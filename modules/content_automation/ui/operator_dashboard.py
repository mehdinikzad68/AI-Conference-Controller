"""
Content Automation Operator Dashboard (PyQt6)

Advanced operator panel with:
- Live schedule monitoring
- Queue display
- Manual controls
- Emergency override
- Status indicators
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QGroupBox, QSplitter, QTextEdit, QComboBox,
    QProgressBar, QMessageBox, QFileDialog, QSpinBox, QTimeEdit, QDateTimeEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, QTime, QDateTime
from PyQt6.QtGui import QColor, QFont
from datetime import datetime, timedelta
from typing import Optional
import asyncio

from ..core.engine import ContentAutomationEngine
from ..models import ContentType, ContentMetadata, Priority, PlaybackStatus, ValidationStatus
from ..sync.event_bus import get_event_bus, EventType


class ContentAutomationDashboard(QWidget):
    """
    Operator Dashboard for Content Automation.
    
    Features:
    - Live schedule view
    - Content library management
    - Manual playback controls
    - Emergency override
    - Status monitoring
    - Event log
    """
    
    # Signals
    content_added = pyqtSignal(str)  # content_id
    playback_triggered = pyqtSignal(str)  # schedule_id
    emergency_triggered = pyqtSignal()
    
    def __init__(self, engine: ContentAutomationEngine, parent=None):
        super().__init__(parent)
        self.engine = engine
        self.event_bus = get_event_bus()
        
        self._init_ui()
        self._connect_events()
        self._start_monitoring()
    
    def _run_async(self, coro):
        """
        Safely run async coroutine from sync context.
        
        Args:
            coro: Coroutine to run
        """
        try:
            loop = asyncio.get_running_loop()
            # Event loop is running, create task
            asyncio.create_task(coro)
        except RuntimeError:
            # No running loop, try to get event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(coro)
                else:
                    # Run synchronously if no loop
                    asyncio.run(coro)
            except RuntimeError:
                # Fallback: create new event loop
                asyncio.run(coro)
    
    def _init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("📋 Content Automation Dashboard")
        self.setMinimumSize(1200, 800)
        
        layout = QVBoxLayout(self)
        
        # Header
        header = self._create_header()
        layout.addWidget(header)
        
        # Main splitter
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Top section: Schedule + Queue
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        
        # Upcoming schedules
        schedule_group = self._create_schedule_section()
        top_layout.addWidget(schedule_group, 2)
        
        # Content library
        library_group = self._create_library_section()
        top_layout.addWidget(library_group, 1)
        
        splitter.addWidget(top_widget)
        
        # Bottom section: Controls + Logs
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # Controls
        controls_group = self._create_controls_section()
        bottom_layout.addWidget(controls_group, 1)
        
        # Event log
        log_group = self._create_log_section()
        bottom_layout.addWidget(log_group, 2)
        
        splitter.addWidget(bottom_widget)
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_bar = QLabel("🟢 System Ready")
        self.status_bar.setStyleSheet("padding: 5px; background: #e8f5e9; border-radius: 3px;")
        layout.addWidget(self.status_bar)
    
    def _create_header(self) -> QWidget:
        """Create header with stats."""
        header = QGroupBox("📊 System Status")
        layout = QHBoxLayout(header)
        
        # Stats labels
        self.stat_content = QLabel("Content: 0")
        self.stat_scheduled = QLabel("Scheduled: 0")
        self.stat_playing = QLabel("Playing: 0")
        self.stat_failed = QLabel("Failed: 0")
        
        for label in [self.stat_content, self.stat_scheduled, self.stat_playing, self.stat_failed]:
            label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            layout.addWidget(label)
        
        # Emergency button
        self.btn_emergency = QPushButton("🚨 EMERGENCY STOP")
        self.btn_emergency.setStyleSheet("""
            QPushButton {
                background-color: #d32f2f;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #b71c1c;
            }
        """)
        self.btn_emergency.clicked.connect(self._on_emergency_stop)
        layout.addWidget(self.btn_emergency)
        
        return header
    
    def _create_schedule_section(self) -> QWidget:
        """Create schedule monitoring section."""
        group = QGroupBox("📅 Upcoming Schedule")
        layout = QVBoxLayout(group)
        
        # Table
        self.schedule_table = QTableWidget(0, 6)
        self.schedule_table.setHorizontalHeaderLabels([
            "Time", "Content", "Platform", "Priority", "Status", "Actions"
        ])
        self.schedule_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.schedule_table)
        
        # Countdown to next
        self.next_schedule_label = QLabel("⏱️ Next: --:--:--")
        self.next_schedule_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.next_schedule_label.setStyleSheet("padding: 10px; background: #fff3e0; border-radius: 5px;")
        layout.addWidget(self.next_schedule_label)
        
        return group
    
    def _create_library_section(self) -> QWidget:
        """Create content library section."""
        group = QGroupBox("📚 Content Library")
        layout = QVBoxLayout(group)
        
        # Add content button
        btn_add = QPushButton("➕ Add Content")
        btn_add.clicked.connect(self._on_add_content)
        layout.addWidget(btn_add)
        
        # Content list
        self.library_table = QTableWidget(0, 4)
        self.library_table.setHorizontalHeaderLabels([
            "Title", "Type", "Status", "Duration"
        ])
        layout.addWidget(self.library_table)
        
        return group
    
    def _create_controls_section(self) -> QWidget:
        """Create manual controls."""
        group = QGroupBox("Manual Controls")
        layout = QVBoxLayout(group)
        
        # Quick schedule
        layout.addWidget(QLabel("Quick Schedule:"))
        
        self.combo_content = QComboBox()
        layout.addWidget(self.combo_content)
        
        self.combo_platform = QComboBox()
        self.combo_platform.addItems(["hall", "skyroom", "hall+skyroom"])
        layout.addWidget(self.combo_platform)
        
        self.combo_priority = QComboBox()
        self.combo_priority.addItems(["normal", "high", "emergency"])
        layout.addWidget(self.combo_priority)
        
        # Custom Time Selection
        layout.addWidget(QLabel("Schedule Time:"))
        
        time_layout = QHBoxLayout()
        self.time_edit = QDateTimeEdit()
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.time_edit.setDateTime(QDateTime.currentDateTime())
        self.time_edit.setCalendarPopup(True)
        time_layout.addWidget(self.time_edit)
        layout.addLayout(time_layout)
        
        # Time adjustment buttons
        time_adjust_layout = QHBoxLayout()
        
        btn_minus_5 = QPushButton("-5 min")
        btn_minus_5.clicked.connect(lambda: self._adjust_time(-5))
        btn_minus_5.setStyleSheet("padding: 5px;")
        time_adjust_layout.addWidget(btn_minus_5)
        
        btn_minus_1 = QPushButton("-1 min")
        btn_minus_1.clicked.connect(lambda: self._adjust_time(-1))
        btn_minus_1.setStyleSheet("padding: 5px;")
        time_adjust_layout.addWidget(btn_minus_1)
        
        btn_now = QPushButton("Now")
        btn_now.clicked.connect(lambda: self.time_edit.setDateTime(QDateTime.currentDateTime()))
        btn_now.setStyleSheet("padding: 5px; background: #2196F3; color: white;")
        time_adjust_layout.addWidget(btn_now)
        
        btn_plus_1 = QPushButton("+1 min")
        btn_plus_1.clicked.connect(lambda: self._adjust_time(1))
        btn_plus_1.setStyleSheet("padding: 5px;")
        time_adjust_layout.addWidget(btn_plus_1)
        
        btn_plus_5 = QPushButton("+5 min")
        btn_plus_5.clicked.connect(lambda: self._adjust_time(5))
        btn_plus_5.setStyleSheet("padding: 5px;")
        time_adjust_layout.addWidget(btn_plus_5)
        
        layout.addLayout(time_adjust_layout)
        
        # Action buttons
        btn_schedule_now = QPushButton("Play Now")
        btn_schedule_now.clicked.connect(self._on_play_now)
        btn_schedule_now.setStyleSheet("background: #4caf50; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(btn_schedule_now)
        
        btn_schedule_custom = QPushButton("Schedule at Selected Time")
        btn_schedule_custom.clicked.connect(self._on_schedule_custom)
        btn_schedule_custom.setStyleSheet("background: #2196F3; color: white; font-weight: bold; padding: 10px;")
        layout.addWidget(btn_schedule_custom)
        
        layout.addStretch()
        
        return group
    
    def _create_log_section(self) -> QWidget:
        """Create event log."""
        group = QGroupBox("📜 Event Log")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)
        
        btn_clear_log = QPushButton("🗑️ Clear Log")
        btn_clear_log.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(btn_clear_log)
        
        return group
    
    def _connect_events(self):
        """Connect to event bus."""
        self.event_bus.subscribe(EventType.CONTENT_ADDED, self._on_event_content_added)
        self.event_bus.subscribe(EventType.CONTENT_VALIDATION_COMPLETED, self._on_event_validation)
        self.event_bus.subscribe(EventType.SCHEDULE_CREATED, self._on_event_schedule_created)
        self.event_bus.subscribe(EventType.SCHEDULE_TRIGGERED, self._on_event_schedule_triggered)
        self.event_bus.subscribe(EventType.PLAYBACK_STARTED, self._on_event_playback_started)
        self.event_bus.subscribe(EventType.PLAYBACK_FAILED, self._on_event_playback_failed)
        self.event_bus.subscribe(EventType.EMERGENCY_STOP, self._on_event_emergency)
    
    def _start_monitoring(self):
        """Start periodic UI updates."""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_ui)
        self.update_timer.start(1000)  # Update every second
    
    def _update_ui(self):
        """Update UI with current state."""
        # Update stats
        stats = self.engine.get_stats()
        self.stat_content.setText(f"Content: {stats['content'].get('total_content', 0)}")
        
        schedule_stats = stats['schedule']
        by_status = schedule_stats.get('by_status', {})
        self.stat_scheduled.setText(f"Scheduled: {by_status.get('scheduled', 0)}")
        self.stat_playing.setText(f"Playing: {by_status.get('playing', 0)}")
        self.stat_failed.setText(f"Failed: {by_status.get('failed', 0)}")
        
        # Update schedule table
        self._update_schedule_table()
        
        # Update library
        self._update_library_table()
        
        # Update next schedule countdown
        self._update_next_schedule()
    
    def _update_schedule_table(self):
        """Update schedule table."""
        upcoming = self.engine.get_upcoming_schedules(limit=10)
        self.schedule_table.setRowCount(len(upcoming))
        
        for row, schedule in enumerate(upcoming):
            # Time
            time_str = schedule.start_time.strftime("%H:%M:%S")
            self.schedule_table.setItem(row, 0, QTableWidgetItem(time_str))
            
            # Content
            content_id_short = schedule.content_id[:8] + "..."
            self.schedule_table.setItem(row, 1, QTableWidgetItem(content_id_short))
            
            # Platform
            platforms = ", ".join([p.value for p in schedule.platforms])
            self.schedule_table.setItem(row, 2, QTableWidgetItem(platforms))
            
            # Priority
            priority_item = QTableWidgetItem(schedule.priority.value)
            if schedule.priority == Priority.EMERGENCY:
                priority_item.setBackground(QColor("#ffcdd2"))
            self.schedule_table.setItem(row, 3, priority_item)
            
            # Status
            status_item = QTableWidgetItem(schedule.playback_status.value)
            self.schedule_table.setItem(row, 4, status_item)
            
            # Actions
            self.schedule_table.setItem(row, 5, QTableWidgetItem("⋮"))
    
    def _update_library_table(self):
        """Update content library table."""
        all_content = self.engine.search_content()
        self.library_table.setRowCount(len(all_content))
        
        # Update combo
        self.combo_content.clear()
        
        for row, content in enumerate(all_content):
            # Title
            self.library_table.setItem(row, 0, QTableWidgetItem(content.metadata.title))
            
            # Type
            self.library_table.setItem(row, 1, QTableWidgetItem(content.content_type.value))
            
            # Status
            status_item = QTableWidgetItem(content.validation_status.value)
            if content.validation_status == ValidationStatus.VALID:
                status_item.setBackground(QColor("#c8e6c9"))
            elif content.validation_status == ValidationStatus.INVALID:
                status_item.setBackground(QColor("#ffcdd2"))
            self.library_table.setItem(row, 2, status_item)
            
            # Duration
            duration = f"{content.metadata.duration_seconds}s" if content.metadata.duration_seconds else "N/A"
            self.library_table.setItem(row, 3, QTableWidgetItem(duration))
            
            # Add to combo
            self.combo_content.addItem(content.metadata.title, content.content_id)
    
    def _update_next_schedule(self):
        """Update countdown to next schedule."""
        upcoming = self.engine.get_upcoming_schedules(limit=1)
        if upcoming:
            next_schedule = upcoming[0]
            delta = next_schedule.start_time - datetime.now()
            
            if delta.total_seconds() > 0:
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                self.next_schedule_label.setText(f"⏱️ Next in: {hours:02d}:{minutes:02d}:{seconds:02d}")
                
                # Warning color if < 60 seconds
                if delta.total_seconds() < 60:
                    self.next_schedule_label.setStyleSheet("padding: 10px; background: #ffcdd2; border-radius: 5px;")
                else:
                    self.next_schedule_label.setStyleSheet("padding: 10px; background: #fff3e0; border-radius: 5px;")
            else:
                self.next_schedule_label.setText("⏱️ Next: Overdue!")
        else:
            self.next_schedule_label.setText("⏱️ Next: No schedules")
    
    # ========== Event Handlers ==========
    
    def _on_add_content(self):
        """Handle add content button."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Content File",
            "",
            "Media Files (*.mp4 *.avi *.mkv *.png *.jpg *.jpeg *.pdf *.mp3 *.wav);;All Files (*.*)"
        )
        
        if not file_path:
            return
        
        # Determine type
        ext = file_path.split('.')[-1].lower()
        content_type_map = {
            'mp4': ContentType.VIDEO, 'avi': ContentType.VIDEO, 'mkv': ContentType.VIDEO,
            'png': ContentType.IMAGE, 'jpg': ContentType.IMAGE, 'jpeg': ContentType.IMAGE,
            'pdf': ContentType.PDF,
            'mp3': ContentType.AUDIO, 'wav': ContentType.AUDIO
        }
        content_type = content_type_map.get(ext, ContentType.VIDEO)
        
        # Add via async
        self._run_async(self._async_add_content(file_path, content_type))
    
    async def _async_add_content(self, path: str, content_type: ContentType):
        """Add content asynchronously."""
        try:
            content_id = await self.engine.add_content(
                path=path,
                content_type=content_type,
                metadata=ContentMetadata(title=path.split('/')[-1].split('\\')[-1])
            )
            self._log(f"✅ Content added: {path}")
        except Exception as e:
            self._log(f"❌ Error adding content: {e}")
            QMessageBox.critical(self, "Error", f"Failed to add content:\n{e}")
    
    def _on_play_now(self):
        """Play selected content now."""
        content_id = self.combo_content.currentData()
        if not content_id:
            QMessageBox.warning(self, "Warning", "No content selected")
            return
        
        platforms = self.combo_platform.currentText().split('+')
        priority = self.combo_priority.currentText()
        
        self._run_async(self._async_schedule(content_id, datetime.now(), platforms, priority))
    
    def _adjust_time(self, minutes: int):
        """Adjust the time picker by specified minutes."""
        current_time = self.time_edit.dateTime()
        new_time = current_time.addSecs(minutes * 60)
        self.time_edit.setDateTime(new_time)
    
    def _on_schedule_custom(self):
        """Schedule at custom selected time."""
        content_id = self.combo_content.currentData()
        if not content_id:
            QMessageBox.warning(self, "Warning", "No content selected")
            return
        
        platforms = self.combo_platform.currentText().split('+')
        priority = self.combo_priority.currentText()
        
        # Get time from time picker
        qt_datetime = self.time_edit.dateTime()
        start_time = datetime(
            qt_datetime.date().year(),
            qt_datetime.date().month(),
            qt_datetime.date().day(),
            qt_datetime.time().hour(),
            qt_datetime.time().minute(),
            qt_datetime.time().second()
        )
        
        # Check if time is in the past
        if start_time < datetime.now():
            reply = QMessageBox.question(
                self,
                "Past Time",
                "Selected time is in the past. Schedule anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self._run_async(self._async_schedule(content_id, start_time, platforms, priority))
    
    async def _async_schedule(self, content_id: str, start_time: datetime, platforms: list, priority: str):
        """Schedule content asynchronously."""
        try:
            schedule_id = await self.engine.schedule_content(
                content_id=content_id,
                start_time=start_time,
                platforms=platforms,
                priority=priority
            )
            self._log(f"✅ Scheduled: {schedule_id} at {start_time.strftime('%H:%M:%S')}")
        except Exception as e:
            self._log(f"❌ Error scheduling: {e}")
            QMessageBox.critical(self, "Error", f"Failed to schedule:\n{e}")
    
    def _on_emergency_stop(self):
        """Handle emergency stop."""
        reply = QMessageBox.question(
            self,
            "Emergency Stop",
            "🚨 Stop ALL playbacks immediately?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Use helper to safely run async function
            self._run_async(self.engine.emergency_stop())
            
            self._log("🚨 EMERGENCY STOP triggered by operator")
            self.emergency_triggered.emit()
    
    # ========== Event Bus Callbacks ==========
    
    def _on_event_content_added(self, event):
        """Handle content added event."""
        self._log(f"📦 Content added: {event.data.get('content_id', 'N/A')}")
    
    def _on_event_validation(self, event):
        """Handle validation completed."""
        status = event.data.get('status', 'unknown')
        icon = "✅" if status == "valid" else "⚠️"
        self._log(f"{icon} Validation: {status}")
    
    def _on_event_schedule_created(self, event):
        """Handle schedule created."""
        self._log(f"📅 Schedule created: {event.data.get('schedule_id', 'N/A')}")
    
    def _on_event_schedule_triggered(self, event):
        """Handle schedule triggered."""
        self._log(f"▶️ Triggered: {event.data.get('schedule_id', 'N/A')}")
    
    def _on_event_playback_started(self, event):
        """Handle playback started."""
        self._log(f"🎬 Playback started: {event.data.get('schedule_id', 'N/A')}")
    
    def _on_event_playback_failed(self, event):
        """Handle playback failed."""
        self._log(f"❌ Playback FAILED: {event.data.get('error', 'Unknown')}")
        self.status_bar.setText(f"🔴 Playback Failed")
        self.status_bar.setStyleSheet("padding: 5px; background: #ffcdd2; border-radius: 3px;")
    
    def _on_event_emergency(self, event):
        """Handle emergency stop."""
        self._log("🚨 EMERGENCY STOP executed")
        self.status_bar.setText("🔴 Emergency Stop")
        self.status_bar.setStyleSheet("padding: 5px; background: #ffcdd2; border-radius: 3px;")
    
    def _log(self, message: str):
        """Add message to log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

