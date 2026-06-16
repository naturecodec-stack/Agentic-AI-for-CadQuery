"""
AI Agent v4 — Full agentic workflow panel for CQ-Editor.

New vs v3:
  - Memory recall (shows past similar shapes)
  - Visual feedback (SVG preview after rendering)
  - Human-in-the-loop approval before loading code
  - Persistent memory (saves accepted shapes)
  - Multi-agent pipeline steps: Memory → Plan → Code → Render → Review → Approve → Save
"""

import os
import sys
import threading
import uuid

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QScrollArea, QFileDialog, QSizePolicy,
    QTextEdit,
)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtSvg import QSvgWidget

from pyqtgraph.parametertree import Parameter
from ..mixins import ComponentMixin


# ---------------------------------------------------------------------------
# Signal bridge
# ---------------------------------------------------------------------------

class _Bridge(QObject):
    step_signal       = pyqtSignal(int)
    status_signal     = pyqtSignal(str)
    code_ready        = pyqtSignal(str)
    error_signal      = pyqtSignal(str)
    approval_needed   = pyqtSignal(dict)   # interrupts — carries svg paths + critique
    memory_recalled   = pyqtSignal(list)   # recalled similar shapes


# ---------------------------------------------------------------------------
# Step definitions
# ---------------------------------------------------------------------------

_STEPS = ["Memory", "Plan", "Code", "Render", "Review", "Approve", "Save"]

_NODE_STEPS = {
    "recall_memory":  (0, "Searching memory..."),
    "plan":           (1, "Planning shape..."),
    "code":           (2, "Writing code..."),
    "render":         (3, "Rendering shape..."),
    "review":         (4, "Reviewing visually..."),
    "human_approval": (5, "Waiting for approval..."),
    "save_memory":    (6, "Saving to memory..."),
}


# ---------------------------------------------------------------------------
# Background runner
# ---------------------------------------------------------------------------

def _run_agent(api_key, model, user_request, image_path, agent_dir,
               thread_id, visual_review, bridge):
    """Run the v4 graph in a background thread, streaming updates."""
    try:
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)

        from cq_agent_v4.graph import graph

        initial = {
            "user_request":      user_request,
            "image_path":        image_path or "",
            "api_key":           api_key,
            "model":             model,
            "visual_review":     visual_review,
            "recalled_shapes":   [],
            "plan":              "",
            "generated_code":    "",
            "execution_success": False,
            "execution_error":   "",
            "repair_attempts":   0,
            "svg_paths":         {},
            "visual_critique":   "",
            "visual_loops":      0,
            "shape_approved":    False,
            "human_approved":    False,
            "human_feedback":    "",
            "final_code":        "",
            "final_message":     "",
            "messages":          [],
        }

        config = {"configurable": {"thread_id": thread_id}}

        for chunk in graph.stream(initial, config=config, stream_mode="updates"):
            # Interrupt from human_approval_node
            if "__interrupt__" in chunk:
                interrupts = chunk["__interrupt__"]
                val = interrupts[0].value if interrupts else {}
                bridge.approval_needed.emit(val)
                return   # widget resumes via _resume_agent()

            node_name, updates = next(iter(chunk.items()))
            if node_name in _NODE_STEPS:
                step_idx, msg = _NODE_STEPS[node_name]
                bridge.step_signal.emit(step_idx)
                bridge.status_signal.emit(msg)
            if node_name == "recall_memory":
                recalled = updates.get("recalled_shapes", [])
                if recalled:
                    bridge.memory_recalled.emit(recalled)

        final = graph.get_state(config).values
        _emit_final(final, bridge)

    except Exception as e:
        import traceback
        bridge.error_signal.emit(f"{e}\n\n{traceback.format_exc()}")


def _resume_agent(api_key, model, agent_dir, thread_id, approved, feedback, bridge,
                  cancel=False):
    """Resume graph after human approval/rejection."""
    try:
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)

        from cq_agent_v4.graph import graph
        from langgraph.types import Command

        config = {"configurable": {"thread_id": thread_id}}
        resume_val = {"approved": approved, "feedback": feedback, "cancel": cancel}

        for chunk in graph.stream(
            Command(resume=resume_val), config=config, stream_mode="updates"
        ):
            # If rejection caused a recode → another approval interrupt
            if "__interrupt__" in chunk:
                interrupts = chunk["__interrupt__"]
                val = interrupts[0].value if interrupts else {}
                bridge.approval_needed.emit(val)
                return  # widget will call _resume_agent again on next approve/reject

            node_name, updates = next(iter(chunk.items()))
            if node_name in _NODE_STEPS:
                step_idx, msg = _NODE_STEPS[node_name]
                bridge.step_signal.emit(step_idx)
                bridge.status_signal.emit(msg)

        final = graph.get_state(config).values
        _emit_final(final, bridge)

    except Exception as e:
        import traceback
        bridge.error_signal.emit(f"{e}\n\n{traceback.format_exc()}")


def _emit_final(state: dict, bridge: _Bridge):
    code = state.get("final_code") or state.get("generated_code", "")
    # human_approved is only False when the user explicitly rejected — never block on it here
    # (rejection re-routes back to code; if we reach _emit_final, the run is truly done)
    if code:
        bridge.code_ready.emit(code)
    else:
        bridge.error_signal.emit(
            state.get("final_message") or "Agent finished without producing code."
        )


# ---------------------------------------------------------------------------
# Main widget
# ---------------------------------------------------------------------------

class AIChatWidget(QWidget, ComponentMixin):

    name = "AI Agent v4"

    preferences = Parameter.create(
        name="Preferences",
        children=[
            {"name": "Google API Key", "type": "str",  "value": ""},
            {"name": "Model",          "type": "str",  "value": "gemini-2.0-flash"},
            {"name": "Agent Dir",      "type": "str",
             "value": r"C:\Users\vbu7\Desktop\cadquery\test\CQ-editor"},
            {"name": "Visual Review",  "type": "bool", "value": True,
             "tip": "ON=full pipeline (slower). OFF=fast mode, skips render/review/approval."},
        ],
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        ComponentMixin.__init__(self)
        self._editor     = None
        self._image_path = None
        self._thread_id  = None

        self._bridge = _Bridge()
        self._bridge.step_signal.connect(self._highlight_step)
        self._bridge.status_signal.connect(self._on_status)
        self._bridge.code_ready.connect(self._on_code_ready)
        self._bridge.error_signal.connect(self._on_error)
        self._bridge.approval_needed.connect(self._on_approval_needed)
        self._bridge.memory_recalled.connect(self._on_memory_recalled)

        self._build_ui()
        self._auto_load_api_key()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel("AI Agent v4  (full agentic)")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)

        # Pipeline steps
        pipeline = QHBoxLayout()
        self._step_labels = []
        for s in _STEPS:
            lbl = QLabel(s)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedHeight(18)
            lbl.setStyleSheet("background:#ddd;border-radius:3px;font-size:9px;padding:1px 3px;")
            pipeline.addWidget(lbl)
            self._step_labels.append(lbl)
        layout.addLayout(pipeline)

        # Memory recall notice
        self._memory_label = QLabel("")
        self._memory_label.setStyleSheet("color:#555;font-size:9px;")
        self._memory_label.setWordWrap(True)
        layout.addWidget(self._memory_label)

        # Chat scroll area
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setMinimumHeight(80)
        self._scroll.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._chat_container = QWidget()
        self._chat_layout = QVBoxLayout(self._chat_container)
        self._chat_layout.setAlignment(Qt.AlignTop)
        self._chat_layout.setSpacing(4)
        self._scroll.setWidget(self._chat_container)
        layout.addWidget(self._scroll, stretch=1)

        # SVG preview (hidden until render)
        self._svg_widget = QLabel("")
        self._svg_widget.setAlignment(Qt.AlignCenter)
        self._svg_widget.setFixedHeight(0)
        self._svg_widget.setStyleSheet(
            "background:#f5f5f5;border:1px solid #ccc;border-radius:4px;"
        )
        layout.addWidget(self._svg_widget)

        # Approval panel (hidden until needed)
        self._approval_panel = QWidget()
        self._approval_panel.setVisible(False)
        ap_layout = QVBoxLayout(self._approval_panel)
        ap_layout.setContentsMargins(0, 0, 0, 0)
        ap_layout.setSpacing(4)

        critique_label = QLabel("Reviewer feedback:")
        critique_label.setStyleSheet("font-weight:bold;font-size:10px;")
        ap_layout.addWidget(critique_label)

        self._critique_text = QLabel("")
        self._critique_text.setWordWrap(True)
        self._critique_text.setStyleSheet(
            "background:#fff8dc;border:1px solid #ddd;border-radius:4px;padding:4px;font-size:10px;"
        )
        ap_layout.addWidget(self._critique_text)

        self._feedback_input = QLineEdit()
        self._feedback_input.setPlaceholderText("Optional: type what to change before rejecting...")
        self._feedback_input.setVisible(False)
        ap_layout.addWidget(self._feedback_input)

        btn_row = QHBoxLayout()
        self._approve_btn = QPushButton("Approve & Load")
        self._approve_btn.setStyleSheet(
            "background:#4CAF50;color:white;border-radius:4px;padding:4px;"
        )
        self._approve_btn.clicked.connect(self._on_approve)
        btn_row.addWidget(self._approve_btn)

        self._reject_btn = QPushButton("Recreate")
        self._reject_btn.setStyleSheet(
            "background:#f44336;color:white;border-radius:4px;padding:4px;"
        )
        self._reject_btn.clicked.connect(self._on_reject)
        btn_row.addWidget(self._reject_btn)

        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setStyleSheet(
            "background:#888;color:white;border-radius:4px;padding:4px;"
        )
        self._cancel_btn.clicked.connect(self._on_cancel)
        btn_row.addWidget(self._cancel_btn)
        ap_layout.addLayout(btn_row)

        layout.addWidget(self._approval_panel)

        # Image preview
        self._img_preview = QLabel("")
        self._img_preview.setFixedHeight(0)
        layout.addWidget(self._img_preview)

        # Status bar
        self._status = QLabel("")
        self._status.setStyleSheet("color:gray;font-size:10px;")
        layout.addWidget(self._status)

        # Input row
        row = QHBoxLayout()
        self._attach_btn = QPushButton("📎")
        self._attach_btn.setFixedWidth(32)
        self._attach_btn.setToolTip("Attach reference image")
        self._attach_btn.clicked.connect(self._attach_image)
        row.addWidget(self._attach_btn)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Describe your shape, or attach an image and press Send...")
        self._input.returnPressed.connect(self._send)
        row.addWidget(self._input)

        self._send_btn = QPushButton("Send")
        self._send_btn.setFixedWidth(55)
        self._send_btn.clicked.connect(self._send)
        row.addWidget(self._send_btn)
        layout.addLayout(row)

        clear_btn = QPushButton("Clear chat")
        clear_btn.setFixedHeight(22)
        clear_btn.setStyleSheet("font-size:9px;")
        clear_btn.clicked.connect(self._clear_chat)
        layout.addWidget(clear_btn)

    # ------------------------------------------------------------------
    def _auto_load_api_key(self):
        key = os.environ.get("GOOGLE_API_KEY", "")
        model = os.environ.get("MODEL", "")
        candidates = [
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
            os.path.join(os.path.dirname(__file__), "..", "..", "env"),
            os.path.expanduser("~/.cq_agent.env"),
        ]
        for p in candidates:
            p = os.path.normpath(p)
            if os.path.exists(p):
                with open(p) as f:
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
            self, "Reference Image", "", "Images (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._image_path = path
            pix = QPixmap(path).scaledToWidth(150, Qt.SmoothTransformation)
            self._img_preview.setPixmap(pix)
            self._img_preview.setFixedHeight(pix.height() + 6)
            self._status.setText(f"Image: {os.path.basename(path)}")

    # ------------------------------------------------------------------
    def _send(self):
        text = self._input.text().strip()

        # Allow image-only: if no text but image attached, model reads the image itself
        if not text and not self._image_path:
            return
        if not text and self._image_path:
            text = "Generate the 3D shape shown in this reference image."

        api_key = self.preferences["Google API Key"]
        if not api_key:
            self._add_bubble("No API key set — add it in Preferences.", is_user=False)
            return

        self._add_bubble(text, is_user=True)
        if self._image_path:
            self._add_image_bubble(self._image_path)

        self._input.clear()
        self._send_btn.setEnabled(False)
        self._approval_panel.setVisible(False)
        self._svg_widget.setFixedHeight(0)
        self._memory_label.setText("")
        self._reset_steps()
        self._highlight_step(0)
        self._status.setText("Starting...")

        self._thread_id = str(uuid.uuid4())
        agent_dir = self.preferences["Agent Dir"]
        model     = self.preferences["Model"]
        image_path = self._image_path
        self._image_path = None
        self._img_preview.clear()
        self._img_preview.setFixedHeight(0)

        visual_review = self.preferences["Visual Review"]
        threading.Thread(
            target=_run_agent,
            args=(api_key, model, text, image_path, agent_dir,
                  self._thread_id, visual_review, self._bridge),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    def _on_approval_needed(self, payload: dict):
        self._highlight_step(5)
        code_failed = payload.get("code_failed", False)

        if code_failed:
            self._status.setText("Code generation failed.")
            self._critique_text.setText(
                "The AI could not generate valid CadQuery code.\n"
                "Click Recreate to try again with different approach, or Cancel to stop."
            )
            self._approve_btn.setEnabled(False)
            self._add_bubble("Code generation failed — no shape was produced.", is_user=False)
        else:
            self._status.setText("Waiting for your approval...")
            critique = payload.get("visual_critique", "")
            self._critique_text.setText(critique or "Reviewer approved the shape.")
            self._approve_btn.setEnabled(True)

            # Show SVG preview (best available view)
            svg_paths = payload.get("svg_paths", {})
            svg_path = svg_paths.get("isometric") or svg_paths.get("front") or \
                       next(iter(svg_paths.values()), None)
            if svg_path and os.path.exists(str(svg_path)):
                self._show_svg(svg_path)
            self._add_bubble("Shape rendered — please review and approve or recreate.", is_user=False)

        self._feedback_input.setVisible(True)
        self._approval_panel.setVisible(True)

    def _show_svg(self, svg_path: str):
        try:
            pix = QPixmap(svg_path)
            if not pix.isNull():
                pix = pix.scaledToWidth(280, Qt.SmoothTransformation)
                self._svg_widget.setPixmap(pix)
                self._svg_widget.setFixedHeight(pix.height() + 8)
                return
        except Exception:
            pass
        # Fallback: just show path
        self._svg_widget.setText(f"SVG: {svg_path}")
        self._svg_widget.setFixedHeight(24)

    # ------------------------------------------------------------------
    def _on_approve(self):
        self._approval_panel.setVisible(False)
        self._status.setText("Approved — continuing...")
        api_key   = self.preferences["Google API Key"]
        model     = self.preferences["Model"]
        agent_dir = self.preferences["Agent Dir"]
        threading.Thread(
            target=_resume_agent,
            args=(api_key, model, agent_dir, self._thread_id, True, "", self._bridge),
            daemon=True,
        ).start()

    def _on_reject(self):
        feedback = self._feedback_input.text().strip()
        self._feedback_input.clear()
        self._approval_panel.setVisible(False)
        self._approve_btn.setEnabled(True)
        self._svg_widget.setFixedHeight(0)
        self._status.setText("Recreating...")
        self._highlight_step(2)
        api_key   = self.preferences["Google API Key"]
        model     = self.preferences["Model"]
        agent_dir = self.preferences["Agent Dir"]
        threading.Thread(
            target=_resume_agent,
            args=(api_key, model, agent_dir, self._thread_id, False, feedback, self._bridge),
            daemon=True,
        ).start()

    def _on_cancel(self):
        self._feedback_input.clear()
        self._approval_panel.setVisible(False)
        self._approve_btn.setEnabled(True)
        self._svg_widget.setFixedHeight(0)
        self._status.setText("Cancelling...")
        self._send_btn.setEnabled(True)
        api_key   = self.preferences["Google API Key"]
        model     = self.preferences["Model"]
        agent_dir = self.preferences["Agent Dir"]
        threading.Thread(
            target=_resume_agent,
            args=(api_key, model, agent_dir, self._thread_id, False, "", self._bridge),
            kwargs={"cancel": True},
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    def _on_code_ready(self, code: str):
        self._send_btn.setEnabled(True)
        self._highlight_step(len(_STEPS) - 1)
        self._status.setText("Done — code loaded and saved to memory.")
        preview = "\n".join(code.splitlines()[:4])
        if len(code.splitlines()) > 4:
            preview += "\n..."
        self._add_bubble(f"Generated & saved:\n{preview}", is_user=False)
        if self._editor:
            self._editor.set_text(code)

    def _on_status(self, msg: str):
        self._status.setText(msg)

    def _on_error(self, msg: str):
        self._send_btn.setEnabled(True)
        self._reset_steps()
        self._status.setText("Error.")
        self._add_bubble(f"Error: {msg}", is_user=False)

    def _on_memory_recalled(self, shapes: list):
        if shapes:
            names = ", ".join(s.get("request", "?")[:40] for s in shapes[:3])
            self._memory_label.setText(f"Memory: found {len(shapes)} similar shape(s) — {names}")

    # ------------------------------------------------------------------
    def _highlight_step(self, active: int):
        for i, lbl in enumerate(self._step_labels):
            if i == active:
                lbl.setStyleSheet(
                    "background:#4CAF50;border-radius:3px;font-size:9px;"
                    "padding:1px 3px;color:white;"
                )
            elif i < active:
                lbl.setStyleSheet(
                    "background:#81C784;border-radius:3px;font-size:9px;"
                    "padding:1px 3px;color:white;"
                )
            else:
                lbl.setStyleSheet(
                    "background:#ddd;border-radius:3px;font-size:9px;padding:1px 3px;"
                )

    def _reset_steps(self):
        for lbl in self._step_labels:
            lbl.setStyleSheet(
                "background:#ddd;border-radius:3px;font-size:9px;padding:1px 3px;"
            )

    def _add_bubble(self, text: str, is_user: bool):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setMargin(6)
        if is_user:
            lbl.setStyleSheet(
                "background:#DCF8C6;border-radius:6px;padding:4px;color:#000;"
            )
            lbl.setAlignment(Qt.AlignRight)
        else:
            lbl.setStyleSheet(
                "background:#ECECEC;border-radius:6px;padding:4px;color:#000;"
            )
            lbl.setAlignment(Qt.AlignLeft)
        self._chat_layout.addWidget(lbl)
        self._scroll.verticalScrollBar().setValue(
            self._scroll.verticalScrollBar().maximum()
        )

    def _add_image_bubble(self, path: str):
        lbl = QLabel()
        pix = QPixmap(path).scaledToWidth(150, Qt.SmoothTransformation)
        lbl.setPixmap(pix)
        lbl.setAlignment(Qt.AlignRight)
        self._chat_layout.addWidget(lbl)

    def _clear_chat(self):
        while self._chat_layout.count():
            item = self._chat_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._status.setText("")
        self._memory_label.setText("")
        self._reset_steps()
        self._svg_widget.setFixedHeight(0)
        self._approval_panel.setVisible(False)

    def toolbarActions(self):
        return []

    def menuActions(self):
        return {}
