"""
AI Agent Chat Panel for CQ-Editor
Agentic pipeline: Plan → Skill Selection → Code Generation → Repair → Editor
"""

import os
import sys
import threading

from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QScrollArea, QFileDialog,
)
from PyQt5.QtGui import QFont, QPixmap

from pyqtgraph.parametertree import Parameter
from ..mixins import ComponentMixin


# ---------------------------------------------------------------------------
# Signals bridge
# ---------------------------------------------------------------------------

class _Bridge(QObject):
    code_ready    = pyqtSignal(str)
    status_update = pyqtSignal(str)
    error_signal  = pyqtSignal(str)


# ---------------------------------------------------------------------------
# Agent runner (background thread)
# ---------------------------------------------------------------------------

def _run_agent(api_key: str, model: str, user_request: str,
               image_path: str, agent_dir: str, bridge: _Bridge):
    try:
        # Add agent directory to path so imports work
        if agent_dir not in sys.path:
            sys.path.insert(0, agent_dir)

        from graph import run_graph

        bridge.status_update.emit("Planning...")
        state = run_graph(user_request, image_path, api_key, model)

        if state.execution_success:
            bridge.code_ready.emit(state.generated_code)
        else:
            bridge.error_signal.emit(state.final_message)

    except Exception as e:
        bridge.error_signal.emit(str(e))


# ---------------------------------------------------------------------------
# Chat bubbles
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

    name = "AI Agent"

    preferences = Parameter.create(
        name="Preferences",
        children=[
            {"name": "Google API Key", "type": "str",  "value": ""},
            {"name": "Model",          "type": "str",  "value": "gemini-3.1-flash-lite"},
            {"name": "Agent Dir",      "type": "str",
             "value": r"C:\Users\vbu7\Desktop\cadquery\test\CQ-editor\cq_agent_v2"},
        ],
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        ComponentMixin.__init__(self)

        self._editor     = None
        self._image_path = None

        self._bridge = _Bridge()
        self._bridge.code_ready.connect(self._on_code_ready)
        self._bridge.status_update.connect(self._on_status)
        self._bridge.error_signal.connect(self._on_error)

        self._build_ui()
        self._auto_load_api_key()

    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        title = QLabel("AI Agent")
        title.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title)

        # Pipeline status indicators
        pipeline_layout = QHBoxLayout()
        self._step_labels = []
        for step in ["Plan", "Skill", "Code", "Fix"]:
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

        # Status
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
        if not key:
            for env_path in [
                os.path.join(os.path.dirname(__file__), "..", "..", ".env"),
                os.path.expanduser("~/.cq_agent.env"),
            ]:
                env_path = os.path.normpath(env_path)
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        for line in f:
                            line = line.strip()
                            if line.startswith("GOOGLE_API_KEY="):
                                key = line.split("=", 1)[1].strip()
                                break
                if key:
                    break
        if key:
            self.preferences["Google API Key"] = key

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
    def _highlight_step(self, step_index: int):
        for i, lbl in enumerate(self._step_labels):
            if i == step_index:
                lbl.setStyleSheet(
                    "background: #4CAF50; border-radius: 4px; "
                    "font-size: 10px; padding: 2px 4px; color: white;"
                )
            elif i < step_index:
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
                "No API key set. Add it in Preferences → AI Agent → Google API Key.",
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
        self._status_label.setText("Planning...")

        model      = self.preferences["Model"]
        agent_dir  = self.preferences["Agent Dir"]
        image_path = self._image_path

        self._image_path = None
        self._img_preview.clear()
        self._img_preview.setFixedHeight(0)

        thread = threading.Thread(
            target=_run_agent,
            args=(api_key, model, text, image_path, agent_dir, self._bridge),
            daemon=True,
        )
        thread.start()

    # ------------------------------------------------------------------
    def _on_code_ready(self, code: str):
        self._send_btn.setEnabled(True)
        self._highlight_step(3)
        self._status_label.setText("✓ Done. Code loaded into editor.")

        preview = "\n".join(code.splitlines()[:4])
        if len(code.splitlines()) > 4:
            preview += "\n..."
        self._add_bubble(f"Generated:\n{preview}", is_user=False)

        if self._editor:
            self._editor.set_text(code)

    def _on_status(self, msg: str):
        self._status_label.setText(msg)
        msg_lower = msg.lower()
        if "planning" in msg_lower:
            self._highlight_step(0)
        elif "skill" in msg_lower or "select" in msg_lower:
            self._highlight_step(1)
        elif "generat" in msg_lower or "code" in msg_lower:
            self._highlight_step(2)
        elif "repair" in msg_lower or "fix" in msg_lower:
            self._highlight_step(3)

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
