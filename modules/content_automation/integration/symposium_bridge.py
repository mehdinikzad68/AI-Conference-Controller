"""
Symposium Bridge - Integration with Symposium Module

Imports schedule from AgendaManager and auto-creates content schedules.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta

from ..core.engine import ContentAutomationEngine
from ..models import ContentType, ContentMetadata, Priority

logger = logging.getLogger(__name__)


class SymposiumBridge:
    """
    Bridge between Symposium module and Content Automation.
    
    Features:
    - Import agenda from AgendaManager
    - Auto-create content schedules
    - Sync session timing
    - Handle session changes
    """
    
    def __init__(self, content_engine: ContentAutomationEngine, agenda_manager=None):
        self.content_engine = content_engine
        self.agenda_manager = agenda_manager
        
        # Map session_id -> content_schedules
        self.session_content_map: Dict[str, List[str]] = {}
        
        logger.info("SymposiumBridge initialized")
    
    def set_agenda_manager(self, agenda_manager):
        """Set agenda manager reference."""
        self.agenda_manager = agenda_manager
        logger.info("AgendaManager connected")
    
    async def import_full_schedule(self) -> int:
        """
        Import entire symposium schedule.
        
        Returns:
            Number of sessions imported
        """
        if not self.agenda_manager:
            logger.warning("AgendaManager not set")
            return 0
        
        try:
            # Get all sessions from AgendaManager
            sessions = self.agenda_manager.get_all_sessions()
            logger.info(f"Importing {len(sessions)} sessions")
            
            imported_count = 0
            for session in sessions:
                success = await self.import_session(session)
                if success:
                    imported_count += 1
            
            logger.info(f"Successfully imported {imported_count}/{len(sessions)} sessions")
            return imported_count
            
        except Exception as e:
            logger.error(f"Failed to import schedule: {e}", exc_info=True)
            return 0
    
    async def import_session(self, session: Dict) -> bool:
        """
        Import single session and create content schedules.
        
        Args:
            session: Session data from AgendaManager
        
        Returns:
            True if successful
        """
        try:
            session_id = session.get('id')
            speaker_name = session.get('speaker', 'Unknown')
            title = session.get('title', 'Untitled')
            start_time_str = session.get('start_time')
            duration = session.get('duration', 30)  # minutes
            
            if not start_time_str:
                logger.warning(f"Session {session_id} has no start time")
                return False
            
            # Parse time
            start_time = self._parse_time(start_time_str)
            
            # Create content schedules
            schedule_ids = []
            
            # 1. Opening slide (if exists)
            opening_content_id = session.get('opening_slide_id')
            if opening_content_id:
                schedule_id = await self.content_engine.schedule_content(
                    content_id=opening_content_id,
                    start_time=start_time - timedelta(seconds=30),  # 30s before
                    platforms=['hall', 'skyroom'],
                    priority='normal',
                    metadata={'session_id': session_id, 'type': 'opening'}
                )
                schedule_ids.append(schedule_id)
            
            # 2. Presentation slides (if exists)
            presentation_content_id = session.get('presentation_id')
            if presentation_content_id:
                schedule_id = await self.content_engine.schedule_content(
                    content_id=presentation_content_id,
                    start_time=start_time,
                    platforms=['hall', 'skyroom'],
                    priority='high',
                    metadata={'session_id': session_id, 'type': 'main'}
                )
                schedule_ids.append(schedule_id)
            
            # 3. Closing content
            closing_content_id = session.get('closing_content_id')
            if closing_content_id:
                end_time = start_time + timedelta(minutes=duration)
                schedule_id = await self.content_engine.schedule_content(
                    content_id=closing_content_id,
                    start_time=end_time,
                    platforms=['hall'],
                    priority='normal',
                    metadata={'session_id': session_id, 'type': 'closing'}
                )
                schedule_ids.append(schedule_id)
            
            # Store mapping
            self.session_content_map[session_id] = schedule_ids
            
            logger.info(f"Imported session {session_id}: {len(schedule_ids)} schedules created")
            return True
            
        except Exception as e:
            logger.error(f"Failed to import session: {e}", exc_info=True)
            return False
    
    async def update_session_timing(self, session_id: str, new_start_time: datetime):
        """
        Update session timing (reschedule all associated content).
        
        Args:
            session_id: Session ID
            new_start_time: New start time
        """
        if session_id not in self.session_content_map:
            logger.warning(f"Session not found: {session_id}")
            return
        
        schedule_ids = self.session_content_map[session_id]
        logger.info(f"Rescheduling {len(schedule_ids)} items for session {session_id}")
        
        # Reschedule each
        for schedule_id in schedule_ids:
            schedule = self.content_engine._schedule_engine.get_schedule(schedule_id)
            if schedule:
                # Calculate new time based on original offset
                await self.content_engine._schedule_engine.update_schedule(
                    schedule_id=schedule_id,
                    start_time=new_start_time
                )
    
    async def cancel_session(self, session_id: str):
        """Cancel all content for a session."""
        if session_id not in self.session_content_map:
            return
        
        schedule_ids = self.session_content_map[session_id]
        logger.info(f"Cancelling {len(schedule_ids)} schedules for session {session_id}")
        
        for schedule_id in schedule_ids:
            await self.content_engine.cancel_schedule(schedule_id)
        
        del self.session_content_map[session_id]
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime."""
        # Assume today + HH:MM format
        try:
            hour, minute = map(int, time_str.split(':'))
            now = datetime.now()
            return datetime(now.year, now.month, now.day, hour, minute)
        except:
            return datetime.now()
    
    def get_session_schedules(self, session_id: str) -> List[str]:
        """Get all schedule IDs for a session."""
        return self.session_content_map.get(session_id, [])

