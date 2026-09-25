"""
PDF Viewer Test Script

Standalone test script to demonstrate and test PDF rendering functionality.
This script showcases high-quality PDF page rendering with navigation.

Usage:
    python modules/media/test_pdf_viewer.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import Qt
from modules.media.media_display_widget import MediaDisplayWidget


class PDFViewerTestWindow(QMainWindow):
    """Test window for PDF viewer functionality."""
    
    def __init__(self):
        """Initialize test window."""
        super().__init__()
        self.setWindowTitle("PDF Viewer Test")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Instructions
        instructions = QLabel(
            "PDF Viewer Test\n\n"
            "1. Click 'Load PDF' to select a PDF file\n"
            "2. Use Previous/Next buttons to navigate pages\n"
            "3. PDF pages will render at high quality (200 DPI)\n"
            "4. Window is resizable and supports fullscreen (F11)\n"
            "5. Optimized for projector display and OBS Studio capture"
        )
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("padding: 20px; font-size: 14px;")
        layout.addWidget(instructions)
        
        # PDF display widget
        self.pdf_display = MediaDisplayWidget()
        layout.addWidget(self.pdf_display, stretch=1)
        
        # Controls
        controls_layout = QHBoxLayout()
        
        load_btn = QPushButton("Load PDF File...")
        load_btn.clicked.connect(self.load_pdf)
        controls_layout.addWidget(load_btn)
        
        self.prev_btn = QPushButton("◀ Previous Page")
        self.prev_btn.clicked.connect(self.previous_page)
        self.prev_btn.setEnabled(False)
        controls_layout.addWidget(self.prev_btn)
        
        self.page_label = QLabel("No PDF loaded")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_label.setMinimumWidth(150)
        controls_layout.addWidget(self.page_label)
        
        self.next_btn = QPushButton("Next Page ▶")
        self.next_btn.clicked.connect(self.next_page)
        self.next_btn.setEnabled(False)
        controls_layout.addWidget(self.next_btn)
        
        fullscreen_btn = QPushButton("Toggle Fullscreen (F11)")
        fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        controls_layout.addWidget(fullscreen_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Status
        self.status_label = QLabel("Ready - Load a PDF file to begin")
        self.status_label.setStyleSheet("padding: 10px; color: #666666;")
        layout.addWidget(self.status_label)
    
    def load_pdf(self):
        """Load a PDF file."""
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Select PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*.*)"
        )
        
        if file:
            if self.pdf_display.load_media(file, transition=MediaDisplayWidget.TRANSITION_FADE):
                info = self.pdf_display.get_current_media_info()
                total_pages = info.get('total_pages', 0)
                current_page = info.get('page', 1)
                
                self.page_label.setText(f"Page: {current_page} / {total_pages}")
                self.prev_btn.setEnabled(current_page > 1)
                self.next_btn.setEnabled(current_page < total_pages)
                
                self.status_label.setText(f"Loaded: {Path(file).name} ({total_pages} pages)")
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Failed to load PDF file.\n\n"
                    "Please ensure:\n"
                    "- PyMuPDF is installed: pip install PyMuPDF\n"
                    "- File is a valid PDF\n"
                    "- You have read permissions"
                )
    
    def previous_page(self):
        """Navigate to previous page."""
        self.pdf_display.previous_pdf_page()
        self.update_page_info()
    
    def next_page(self):
        """Navigate to next page."""
        self.pdf_display.next_pdf_page()
        self.update_page_info()
    
    def update_page_info(self):
        """Update page information display."""
        info = self.pdf_display.get_current_media_info()
        if info.get('type') == 'pdf':
            current_page = info.get('page', 1)
            total_pages = info.get('total_pages', 1)
            self.page_label.setText(f"Page: {current_page} / {total_pages}")
            self.prev_btn.setEnabled(current_page > 1)
            self.next_btn.setEnabled(current_page < total_pages)
    
    def toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
            self.status_label.setText("Exited fullscreen mode")
        else:
            self.showFullScreen()
            self.status_label.setText("Fullscreen mode - Press F11 to exit")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts."""
        if event.key() == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        elif event.key() == Qt.Key.Key_Left:
            self.previous_page()
        elif event.key() == Qt.Key.Key_Right:
            self.next_page()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close."""
        self.pdf_display.close()
        event.accept()


def main():
    """Run PDF viewer test."""
    print("=" * 60)
    print("PDF Viewer Test - AI-Symp-Controller")
    print("=" * 60)
    print("\nThis test demonstrates:")
    print("  - High-quality PDF page rendering (PyMuPDF)")
    print("  - Page navigation (Previous/Next)")
    print("  - Resizable display with aspect ratio")
    print("  - Fullscreen mode for projector display")
    print("  - OBS Studio compatible window")
    print("\nInstructions:")
    print("  1. Click 'Load PDF File...' to select a PDF")
    print("  2. Use Previous/Next buttons or arrow keys to navigate")
    print("  3. Press F11 for fullscreen mode")
    print("  4. Window is optimized for OBS Studio Window Capture")
    print("\nKeyboard Shortcuts:")
    print("  - Left Arrow: Previous page")
    print("  - Right Arrow: Next page")
    print("  - F11: Toggle fullscreen")
    print("\nPress Ctrl+Q or close window to exit")
    print("=" * 60)
    print()
    
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Viewer Test")
    
    window = PDFViewerTestWindow()
    window.show()
    
    print("PDF viewer test window opened!")
    print("Load a PDF file to test rendering.\n")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")


if __name__ == "__main__":
    main()

