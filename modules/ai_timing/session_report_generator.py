"""
Session Report Generator Module

Generates AI-powered post-session reports with engagement metrics,
presenter performance, and adaptive timing adjustments.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class SessionReportGenerator:
    """
    Generates comprehensive post-session reports.
    
    Features:
    - Presenter effective time calculation
    - Audience engagement timeline
    - Key moments tracking (focus drops, extensions, overrides)
    - Statistical summaries
    - Export to JSON/HTML
    """
    
    def __init__(self):
        """Initialize report generator."""
        self._session_data = {
            'start_time': None,
            'end_time': None,
            'total_duration': 0,
            'effective_duration': 0,
            'presenter_states': [],
            'engagement_timeline': [],
            'adaptation_events': [],
            'extension_events': [],
            'reduction_events': [],
            'override_events': [],
            'statistics': {}
        }
    
    def start_session(self):
        """Start a new session."""
        self._session_data['start_time'] = datetime.now()
        self._session_data['end_time'] = None
        self._session_data['total_duration'] = 0
        self._session_data['effective_duration'] = 0
        self._session_data['presenter_states'].clear()
        self._session_data['engagement_timeline'].clear()
        self._session_data['adaptation_events'].clear()
        self._session_data['extension_events'].clear()
        self._session_data['reduction_events'].clear()
        self._session_data['override_events'].clear()
    
    def end_session(self):
        """End current session."""
        self._session_data['end_time'] = datetime.now()
        if self._session_data['start_time']:
            duration = (self._session_data['end_time'] - self._session_data['start_time']).total_seconds()
            self._session_data['total_duration'] = int(duration)
    
    def record_presenter_state(self, state: str, timestamp: Optional[datetime] = None):
        """Record presenter state change."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['presenter_states'].append({
            'state': state,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def record_engagement(self, level: str, attention: float, timestamp: Optional[datetime] = None):
        """Record engagement level."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['engagement_timeline'].append({
            'level': level,
            'attention': attention,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def record_adaptation(self, mode: str, reason: str, timestamp: Optional[datetime] = None):
        """Record timer adaptation event."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['adaptation_events'].append({
            'mode': mode,
            'reason': reason,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def record_extension(self, seconds: int, confirmed: bool, timestamp: Optional[datetime] = None):
        """Record timer extension."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['extension_events'].append({
            'seconds': seconds,
            'confirmed': confirmed,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def record_reduction(self, seconds: int, confirmed: bool, timestamp: Optional[datetime] = None):
        """Record timer reduction."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['reduction_events'].append({
            'seconds': seconds,
            'confirmed': confirmed,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def record_override(self, operator_action: str, timestamp: Optional[datetime] = None):
        """Record operator override."""
        if timestamp is None:
            timestamp = datetime.now()
        
        self._session_data['override_events'].append({
            'action': operator_action,
            'timestamp': timestamp.isoformat(),
            'session_time': self._get_session_time(timestamp)
        })
    
    def _get_session_time(self, timestamp: datetime) -> int:
        """Get session time in seconds from start."""
        if not self._session_data['start_time']:
            return 0
        return int((timestamp - self._session_data['start_time']).total_seconds())
    
    def calculate_statistics(self) -> Dict:
        """Calculate session statistics."""
        stats = {}
        
        # Total vs effective time
        stats['total_duration'] = self._session_data['total_duration']
        
        # Calculate effective duration (excluding paused/slowed periods)
        effective = 0
        last_state = None
        last_time = None
        
        for state_record in sorted(self._session_data['presenter_states'], 
                                   key=lambda x: x['session_time']):
            state = state_record['state']
            time = state_record['session_time']
            
            if last_state in ['talking', 'engaged'] and state in ['talking', 'engaged']:
                effective += time - (last_time or 0)
            
            last_state = state
            last_time = time
        
        stats['effective_duration'] = effective
        stats['efficiency_ratio'] = effective / stats['total_duration'] if stats['total_duration'] > 0 else 0
        
        # Engagement statistics
        engagement_levels = [e['level'] for e in self._session_data['engagement_timeline']]
        if engagement_levels:
            stats['engagement_high_percent'] = (engagement_levels.count('high') / len(engagement_levels)) * 100
            stats['engagement_medium_percent'] = (engagement_levels.count('medium') / len(engagement_levels)) * 100
            stats['engagement_low_percent'] = (engagement_levels.count('low') / len(engagement_levels)) * 100
        
        # Average attention
        attentions = [e['attention'] for e in self._session_data['engagement_timeline']]
        if attentions:
            stats['average_attention'] = sum(attentions) / len(attentions)
        
        # Key moments
        stats['focus_drops'] = [e for e in self._session_data['engagement_timeline'] 
                               if e['level'] == 'low']
        stats['extension_count'] = len([e for e in self._session_data['extension_events'] if e['confirmed']])
        stats['reduction_count'] = len([e for e in self._session_data['reduction_events'] if e['confirmed']])
        stats['override_count'] = len(self._session_data['override_events'])
        
        self._session_data['statistics'] = stats
        return stats
    
    def generate_report(self, format: str = 'json') -> Dict:
        """
        Generate session report.
        
        Args:
            format: Report format ('json' or 'dict')
            
        Returns:
            Report dictionary
        """
        # Calculate statistics
        self.calculate_statistics()
        
        report = {
            'session_info': {
                'start_time': self._session_data['start_time'].isoformat() if self._session_data['start_time'] else None,
                'end_time': self._session_data['end_time'].isoformat() if self._session_data['end_time'] else None,
                'total_duration_seconds': self._session_data['total_duration'],
                'effective_duration_seconds': self._session_data['statistics'].get('effective_duration', 0)
            },
            'statistics': self._session_data['statistics'],
            'timeline': {
                'presenter_states': self._session_data['presenter_states'],
                'engagement': self._session_data['engagement_timeline']
            },
            'events': {
                'adaptations': self._session_data['adaptation_events'],
                'extensions': self._session_data['extension_events'],
                'reductions': self._session_data['reduction_events'],
                'overrides': self._session_data['override_events']
            }
        }
        
        return report
    
    def save_report(self, file_path: str) -> bool:
        """
        Save report to JSON file.
        
        Args:
            file_path: Path to save report
            
        Returns:
            True if saved successfully
        """
        try:
            report = self.generate_report()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session report saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return False

