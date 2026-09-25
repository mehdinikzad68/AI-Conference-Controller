"""
Resource Warning Dialog

Shows warning dialogs for high resource usage with optimization recommendations.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont
import logging

logger = logging.getLogger(__name__)


class ResourceWarningDialog(QDialog):
    """
    Dialog for displaying resource warnings.
    
    Shows RAM/CPU usage warnings with optimization recommendations.
    """
    
    def __init__(self, parent=None):
        """Initialize resource warning dialog."""
        super().__init__(parent)
        self.setWindowTitle("Resource Warning")
        self.setMinimumWidth(500)
        self.setModal(True)
        
    def show_ram_warning(self, ram_percent: float, used_gb: float, total_gb: float):
        """
        Show RAM usage warning.
        
        Args:
            ram_percent: RAM usage percentage
            used_gb: Used RAM in GB
            total_gb: Total RAM in GB
        """
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Warning icon and title
        title_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(self.style().standardIcon(
            self.style().StandardPixmap.SP_MessageBoxWarning
        ).pixmap(48, 48))
        title_layout.addWidget(icon_label)
        
        title = QLabel("Resource Warning:")
        title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)
        
        # RAM usage details
        ram_info = QLabel(
            f"High RAM usage: {ram_percent:.1f}% ({used_gb:.1f}GB / {total_gb:.1f}GB)"
        )
        ram_info.setFont(QFont("Arial", 10))
        layout.addWidget(ram_info)
        
        # Recommendations
        recommendations = QTextEdit()
        recommendations.setReadOnly(True)
        recommendations.setMaximumHeight(100)
        recommendations.setPlainText(
            "Consider closing heavy files or reducing Face AI processing rate."
        )
        layout.addWidget(QLabel("Recommendations:"))
        layout.addWidget(recommendations)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        self.exec()
    
    @staticmethod
    def show_quick_warning(parent, message: str, recommendations: list = None):
        """
        Show a quick warning message box.
        
        Args:
            parent: Parent widget
            message: Warning message
            recommendations: List of recommendation strings
        """
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Resource Warning")
        msg.setText(message)
        
        if recommendations:
            detailed_text = "\n".join([f"• {rec}" for rec in recommendations])
            msg.setDetailedText(detailed_text)
        
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

