"""
Reporting & Analytics - Execution Analysis

Tracks and analyzes content automation execution.
"""

import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ExecutionRecord:
    """Single execution record"""
    timestamp: datetime
    event_type: str
    schedule_id: Optional[str]
    content_id: Optional[str]
    platform: Optional[str]
    status: str
    delay_seconds: Optional[float] = None
    error_message: Optional[str] = None
    operator_override: bool = False


class ReportingAnalytics:
    """
    Reporting and analytics system.
    
    Features:
    - Execution logging
    - Delay tracking
    - Success rate analysis
    - Export reports
    """
    
    def __init__(self, log_file: str = "content_automation_log.json"):
        self.log_file = Path(log_file)
        self.records: List[ExecutionRecord] = []
        
        # Load existing log
        self._load_log()
        
        logger.info("ReportingAnalytics initialized")
    
    def log_execution(
        self,
        event_type: str,
        status: str,
        schedule_id: Optional[str] = None,
        content_id: Optional[str] = None,
        platform: Optional[str] = None,
        delay_seconds: Optional[float] = None,
        error_message: Optional[str] = None,
        operator_override: bool = False
    ):
        """Log execution event."""
        record = ExecutionRecord(
            timestamp=datetime.now(),
            event_type=event_type,
            schedule_id=schedule_id,
            content_id=content_id,
            platform=platform,
            status=status,
            delay_seconds=delay_seconds,
            error_message=error_message,
            operator_override=operator_override
        )
        
        self.records.append(record)
        self._save_log()
    
    def get_success_rate(self, time_window: Optional[timedelta] = None) -> float:
        """Calculate success rate."""
        if time_window:
            cutoff = datetime.now() - time_window
            relevant_records = [r for r in self.records if r.timestamp >= cutoff]
        else:
            relevant_records = self.records
        
        if not relevant_records:
            return 0.0
        
        success_count = sum(1 for r in relevant_records if r.status == 'success')
        return (success_count / len(relevant_records)) * 100
    
    def get_average_delay(self, time_window: Optional[timedelta] = None) -> float:
        """Calculate average delay."""
        if time_window:
            cutoff = datetime.now() - time_window
            relevant_records = [r for r in self.records if r.timestamp >= cutoff and r.delay_seconds]
        else:
            relevant_records = [r for r in self.records if r.delay_seconds]
        
        if not relevant_records:
            return 0.0
        
        total_delay = sum(r.delay_seconds for r in relevant_records)
        return total_delay / len(relevant_records)
    
    def get_failure_breakdown(self) -> Dict[str, int]:
        """Get breakdown of failure types."""
        failures = [r for r in self.records if r.status == 'failed']
        breakdown = {}
        
        for record in failures:
            error = record.error_message or 'Unknown'
            breakdown[error] = breakdown.get(error, 0) + 1
        
        return breakdown
    
    def generate_report(self, time_window: Optional[timedelta] = None) -> Dict:
        """Generate comprehensive report."""
        if time_window:
            cutoff = datetime.now() - time_window
            records = [r for r in self.records if r.timestamp >= cutoff]
        else:
            records = self.records
        
        total = len(records)
        success = sum(1 for r in records if r.status == 'success')
        failed = sum(1 for r in records if r.status == 'failed')
        overrides = sum(1 for r in records if r.operator_override)
        
        return {
            'period': f"Last {time_window.days} days" if time_window else "All time",
            'total_executions': total,
            'successful': success,
            'failed': failed,
            'success_rate': (success / total * 100) if total > 0 else 0,
            'operator_overrides': overrides,
            'average_delay': self.get_average_delay(time_window),
            'failure_breakdown': self.get_failure_breakdown(),
            'generated_at': datetime.now().isoformat()
        }
    
    def export_report(self, output_file: str, time_window: Optional[timedelta] = None):
        """Export report to JSON file."""
        report = self.generate_report(time_window)
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Report exported to {output_file}")
    
    def _load_log(self):
        """Load existing log."""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r') as f:
                    data = json.load(f)
                    self.records = [
                        ExecutionRecord(**{**record, 'timestamp': datetime.fromisoformat(record['timestamp'])})
                        for record in data
                    ]
                logger.info(f"Loaded {len(self.records)} records")
            except Exception as e:
                logger.error(f"Failed to load log: {e}")
    
    def _save_log(self):
        """Save log to file."""
        try:
            data = [
                {**asdict(record), 'timestamp': record.timestamp.isoformat()}
                for record in self.records
            ]
            
            with open(self.log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save log: {e}")

