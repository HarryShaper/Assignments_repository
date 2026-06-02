from PySide2.QtCore import QSize, Qt, Signal
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton


class RuleItemWidget(QWidget):
    """
    Custom list item widget for the rename rules outliner.

    Shows:
    - rule name on the left
    - trash/delete icon button on the right

    Emits:
    - delete_requested: when the trash button is clicked
    """

    delete_requested = Signal()

    def __init__(self, text: str, parent=None):
        super().__init__(parent)

        self._build_ui(text)

    def _build_ui(self, text: str) -> None:
        self.setObjectName("ruleItemWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 8, 0)
        layout.setSpacing(6)

        self.label = QLabel(text, self)
        self.label.setObjectName("label_ruleItem")
        self.label.setAlignment(Qt.AlignVCenter | Qt.AlignLeft)

        self.btn_delete = QPushButton(self)
        self.btn_delete.setObjectName("btn_deleteRule")
        self.btn_delete.setCursor(Qt.PointingHandCursor)
        self.btn_delete.setFlat(True)
        self.btn_delete.setIcon(QIcon(":/icons/delete.png"))
        self.btn_delete.setIconSize(QSize(12, 12))
        self.btn_delete.setToolTip("Delete rule")

        self.btn_delete.setMinimumSize(18, 18)
        self.btn_delete.setMaximumSize(18, 18)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.btn_delete)

        self.btn_delete.clicked.connect(self.delete_requested.emit)

    def text(self) -> str:
        return self.label.text()

    def set_text(self, text: str) -> None:
        self.label.setText(text)