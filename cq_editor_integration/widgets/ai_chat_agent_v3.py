"""
AI Agent v3 Chat Panel for CQ-Editor  (LangGraph edition)

Two agent modes selectable via Preferences:
  sequential   — fixed Plan→Skill→Code→Execute→Repair pipeline  (graph.py)
  tool-calling — LLM autonomously calls tools mid-generation     (agent_graph.py)

Drop this file into cq_editor/widgets/ as ai_chat_agent_v3.py, then register
it in main_window.py (see instructions at the bottom of this file).
"""

import os
import sys
import threading

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QScrollArea, QFileDialog, QSizePolicy,
)
from PyQt5.QtGui import QFont, QPixmap

from pyqtgraph.parametertree import Parameter
from ..mixins import ComponentMixin


# ---------------------------------------------------------------------------
# Signals bridge — crosses thread boundary safely
# ---------------------------------------------------------------------------

class _Bridge(QObject):
    code_ready    = pyqtSignal(str)
    status_update = pyqtSignal(str)
    step_signal   = pyqtSignal(int)
    error_signal  = pyqtSignal(str)


# ---------------------------------------------------------------------------
# Step map — sequential mode (node name → step index)
# ---------------------------------------------------------------------------

_SEQ_NODE_STEPS = {
    "plan":         (0, "Planning..."),
    "skill_select": (1, "Selecting skill..."),
    "codegen":      (2, "Generating code..."),
    "execute":      (3, "Executing..."),
    "repair":       (4, "Repairing..."),
}

# Tool-calling mode: which tool call maps to which step
_TOOL_STEPS = {
    "plan_shape":       (0, "Planning features..."),
    "list_skills":      (1, "Checking skill library..."),
    "search_skills":    (1, "Searching skills..."),
    "use_skill":        (2, "Loading skill template..."),
    "execute_cadquery": (3, "Executing code..."),
}


# ---------------------------------------------------------------------------
# Sequential agent runner (original graph.py pipeline)
# ---------------------------------------------------------------------------

def _run_sequential(api_key, model, user_request, image_path, agent_dir, bridge):
    try:
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)

        from graph import graph

        initial = {
            "user_request":      user_request,
            "image_path":        image_path or "",
            "api_key":           api_key,
            "model":             model,
            "plan":              "",
            "selected_skill":    "",
            "extracted_params":  {},
            "generated_code":    "",
            "execution_success": False,
            "execution_error":   "",
            "repair_attempts":   0,
            "repair_history":    [],
            "final_message":     "",
        }

        accumulated = dict(initial)

        for chunk in graph.stream(initial, stream_mode="updates"):
            node_name, updates = next(iter(chunk.items()))
            accumulated.update(updates)
            if node_name in _SEQ_NODE_STEPS:
                step_idx, msg = _SEQ_NODE_STEPS[node_name]
                bridge.step_signal.emit(step_idx)
                bridge.status_update.emit(msg)

        if accumulated["execution_success"]:
            bridge.code_ready.emit(accumulated["generated_code"])
        else:
            bridge.error_signal.emit(
                accumulated.get("final_message") or "Agent failed — no output."
            )

    except Exception as e:
        import traceback
        bridge.error_signal.emit(f"{e}\n\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Tool-calling agent runner (agent_graph.py ReAct agent)
# ---------------------------------------------------------------------------

def _run_tool_agent(api_key, model, user_request, image_path, agent_dir, bridge):
    try:
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)

        from agent_graph import build_agent, _build_human_message, extract_final_code
        from langchain_core.messages import AIMessage, ToolMessage

        agent = build_agent(api_key, model)
        human_msg = _build_human_message(user_request, image_path)

        all_messages = []

        for chunk in agent.stream(
            {"messages": [human_msg]}, stream_mode="updates"
        ):
            node_name, data = next(iter(chunk.items()))
            msgs = data.get("messages", [])
            all_messages.extend(msgs)

            if node_name == "agent":
                for msg in msgs:
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        # Emit step for FIRST tool about to be called
                        tc = msg.tool_calls[0]
                        step, status = _TOOL_STEPS.get(
                            tc.get("name", ""), (0, "Thinking...")
                        )
                        bridge.step_signal.emit(step)
                        bridge.status_update.emit(status)
                    else:
                        bridge.step_signal.emit(0)
                        bridge.status_update.emit("Reading request...")

            elif node_name == "tools":
                for msg in msgs:
                    if isinstance(msg, ToolMessage):
                        content = str(msg.content)
                        if "SUCCESS" in content:
                            bridge.step_signal.emit(3)
                            bridge.status_update.emit("Code validated ✓")
                        elif "FAILED" in content:
                            bridge.step_signal.emit(4)
                            bridge.status_update.emit("Fixing error...")

        code = extract_final_code(all_messages)
        if code:
            bridge.code_ready.emit(code)
        else:
            last = next(
                (m for m in reversed(all_messages) if isinstance(m, AIMessage)), None
            )
            msg_txt = ""
            if last:
                c = last.content
                msg_txt = c if isinstance(c, str) else str(c)
            bridge.error_signal.emit(
                f"No validated code produced.\n\n{msg_txt[:600]}"
            )

    except Exception as e:
        import traceback
        bridge.error_signal.emit(f"{e}\n\n{traceback.format_exc()}")


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def _dispatch(api_key, model, user_request, image_path, agent_dir, mode, bridge):
    if mode == "tool-calling":
        _run_tool_agent(api_key, model, user_request, image_path, agent_dir, bridge)
    else:
        _run_sequential(api_key, model, user_request, image_path, agent_dir, bridge)


# ---------------------------------------------------------------------------
# Chat bubble widgets
# ---------------------------------------------------------------------------

class _ChatBubble(QLabel):
    def __init__(self, text: str, is_user: bool, parent=None):
        super().__init__(parent)
        self.setWordWrap(True)
        self.setText(text)
        self.setMargin(8)
        if is_user:
            self.setStyleSheet(
                "background-color: #DCF8C6; border-radius: 8px; padding: 6px; color: #000;"
            )
            self.setAlignment(Qt.AlignRight)
        else:
            self.setStyleSheet(
                "background-color: #ECECEC; border-radius: 8px; padding: 6px; color: #000;"
            )
            self.setAlignment(Qt.AlignLeft)


class _ImageBubble(QLabel):
    def __init__(self, image_path: str, parent=None):
        super().__init__(parent)
        pix = QPixmap(image_path).scaledToWidth(180, Qt.SmoothTransformation)
        self.setPixmap(pix)
        self.setAlignment(Qt.AlignRight)
        self.setStyleSheet("padding: 4px;")


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class AIChatWidget(QWidget, ComponentMixin):

    name = "AI Agent v3"

    preferences = Parameter.create(
        name="Preferences",
        children=[
            {"name": "Google API Key", "type": "str",  "value": ""},
            {"name": "Model",          "type": "str",  "value": "gemini-2.0-flash"},
            {"name": "Agent Dir",      "type": "str",
             "value": r"C:\Users\vbu7\Desktop\cadquery\test\CQ-editor\cq_agent_v3_langgraph"},
            {"name": "Agent Mode",     "type": "list",
             "values": ["tool-calling", "sequential"], "value": "tool-calling"},
        ],
    )

    _STEPS = ["Plan", "Skills", "Code", "Exec", "Fix"]

    def __init__(self, parent=None):
        super().__init__(parent)
        ComponentMixin.__init__(self)

        self._editor     = None
        self._image_path = None

        self._bridge = _Bridge()
        self._bridge.code_ready.connect(self._on_code_ready)
        self._bridge.status_update.connect(self._on_status)
        self._bridge.step_signal.connect(self._highlight_step)
        self._bridge.error_signal.connect(self._on_error)

        self._build_ui()
        self._auto_load_api_key()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self._title = QLabel("AI Agent v3  (tool-calling)")
        self._title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(self._title)

        # Pipeline step indicators
        pipeline_layout = QHBoxLayout()
        self._step_labels = []
        for step in self._STEPS:
            lbl = QLabel(step)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(20)
            lbl.setStyleSheet(
                "background: #ddd; border-radius: 4px; font-size: 10px; padding: 2px 4px;"
            )
            pipeline_layout.addWidget(lbl)
            self._step_labels.append(lbl)
        layout.addLayout(pipeline_layout)

        # Chat history
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setMinimumHeight(80)
        self._scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._chat_layout.setSpacing(6)
        self._scroll.setWidget(self._chat_container)
        layout.addWidget(self._scroll, stretch=1)

        # Image preview
        self._img_preview = QLabel("")
        self._img_preview.setFixedHeight(0)
        self._img_preview.setAlignment(Qt.AlignCenter)
        self._img_preview.setStyleSheet(
            "background: #f0f0f0; border: 1px solid #ccc; border-radius: 4px;"
        )
        layout.addWidget(self._img_preview)

        # Status bar
        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self._status_label)

        # Input row
        input_layout = QHBoxLayout()

        self._attach_btn = QPushButton("📎")
        self._attach_btn.setFixedWidth(32)
        self._attach_btn.setToolTip("Attach image")
        self._attach_btn.clicked.connect(self._attach_image)
        input_layout.addWidget(self._attach_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Describe your 3D object...")
        self._input.returnPressed.connect(self._send)
        input_layout.addWidget(self._input)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(60)
        self._send_btn.clicked.connect(self._send)
        input_layout.addWidget(self._send_btn)

        layout.addLayout(input_layout)

        clear_btn = QPushButton("Clear chat")
        clear_btn.setFixedHeight(24)
        clear_btn.setStyleSheet("font-size: 10px;")
        clear_btn.clicked.connect(self._clear_chat)
        layout.addWidget(clear_btn)

    # ------------------------------------------------------------------
    def _auto_load_api_key(self):
        key = os.environ.get("GOOGLE_API_KEY", "")
        model = os.environ.get("MODEL", "")
        if not key:
            candidates = [
                os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
                os.path.join(os.path.dirname(__file__), "..", "..", "env"),
                os.path.expanduser("~/.cq_agent.env"),
            ]
            for env_path in candidates:
                env_path = os.path.normpath(env_path)
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GOOGLE_API_KEY="):
                                key = key or line.split("=", 1)[1].strip()
                            elif line.startswith("MODEL="):
                                model = model or line.split("=", 1)[1].strip()
                if key:
                    break
        if key:
            self.preferences["Google API Key"] = key
        if model:
            self.preferences["Model"] = model

    def set_editor(self, editor):
        self._editor = editor

    # ------------------------------------------------------------------
    def _attach_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._image_path = path
            pix = QPixmap(path).scaledToWidth(160, Qt.SmoothTransformation)
            self._img_preview.setPixmap(pix)
            self._img_preview.setFixedHeight(pix.height() + 8)
            self._status_label.setText(f"Image: {os.path.basename(path)}")

    # ------------------------------------------------------------------
    def _highlight_step(self, active: int):
        for i, lbl in enumerate(self._step_labels):
            if i == active:
                lbl.setStyleSheet(
                    "background: #4CAF50; border-radius: 4px; "
                    "font-size: 10px; padding: 2px 4px; color: white;"
                )
            elif i < active:
                lbl.setStyleSheet(
                    "background: #81C784; border-radius: 4px; "
                    "font-size: 10px; padding: 2px 4px; color: white;"
                )
            else:
                lbl.setStyleSheet(
                    "background: #ddd; border-radius: 4px; "
                    "font-size: 10px; padding: 2px 4px;"
                )

    def _reset_steps(self):
        for lbl in self._step_labels:
            lbl.setStyleSheet(
                "background: #ddd; border-radius: 4px; font-size: 10px; padding: 2px 4px;"
            )

    # ------------------------------------------------------------------
    def _send(self):
        text = self._input.text().strip()
        if not text and not self._image_path:
            return

        api_key = self.preferences["Google API Key"]
        if not api_key:
            self._add_bubble(
                "No API key set. Add it in Preferences → AI Agent v3 → Google API Key.",
                is_user=False,
            )
            return

        if text:
            self._add_bubble(text, is_user=True)
        if self._image_path:
            self._add_image_bubble(self._image_path)

        self._input.clear()
        self._send_btn.setEnabled(False)
        self._reset_steps()
        self._highlight_step(0)

        mode      = self.preferences["Agent Mode"]
        model     = self.preferences["Model"]
        agent_dir = self.preferences["Agent Dir"]
        image_path = self._image_path

        # Update title to reflect active mode
        self._title.setText(f"AI Agent v3  ({mode})")
        self._status_label.setText(f"Starting [{mode}]...")

        self._image_path = None
        self._img_preview.clear()
        self._img_preview.setFixedHeight(0)

        threading.Thread(
            target=_dispatch,
            args=(api_key, model, text, image_path, agent_dir, mode, self._bridge),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    def _on_code_ready(self, code: str):
        self._send_btn.setEnabled(True)
        self._highlight_step(len(self._STEPS) - 1)
        self._status_label.setText("✓ Done. Code loaded into editor.")

        preview = "\n".join(code.splitlines()[:4])
        if len(code.splitlines()) > 4:
            preview += "\n..."
        self._add_bubble(f"Generated:\n{preview}", is_user=False)

        if self._editor:
            self._editor.set_text(code)

    def _on_status(self, msg: str):
        self._status_label.setText(msg)

    def _on_error(self, msg: str):
        self._send_btn.setEnabled(True)
        self._reset_steps()
        self._status_label.setText("Error.")
        self._add_bubble(f"Error: {msg}", is_user=False)

    # ------------------------------------------------------------------
    def _add_bubble(self, text: str, is_user: bool):
        bubble = _ChatBubble(text, is_user)
        self._chat_layout.addWidget(bubble)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _add_image_bubble(self, image_path: str):
        bubble = _ImageBubble(image_path)
        self._chat_layout.addWidget(bubble)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _clear_chat(self):
        while self._chat_layout.count():
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status_label.setText("")
        self._reset_steps()

    def toolbarActions(self):
        return []

    def menuActions(self):
        return {}


# ---------------------------------------------------------------------------
# Installation instructions
# ---------------------------------------------------------------------------
#
# 1. Copy this file to:
#       CQ-editor/cq_editor/widgets/ai_chat_agent_v3.py
#
# 2. In main_window.py (already done if you followed v3 setup):
#
#    from .widgets.ai_chat_agent_v3 import AIChatWidget as AIAgentV3Widget
#
#    self.registerComponent(
#        "ai_agent_v3", AIAgentV3Widget(self),
#        lambda c: dock(c, "AI Agent v3", self, defaultArea="right"),
#    )
#
#    self.components["ai_agent_v3"].set_editor(self.components["editor"])
#
# 3. pip install langchain-google-genai   (for tool-calling mode)
