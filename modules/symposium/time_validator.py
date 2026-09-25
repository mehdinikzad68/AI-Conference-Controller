"""
Time Validation and Utility Module

Provides comprehensive time validation, parsing, and manipulation for symposium scheduling.

Features:
- Time format validation (HH:MM)
- Duration validation and bounds checking
- Overlap detection between sessions
- End time calculation with midnight crossing support
- Timezone-aware operations (future extension)
- Chronological sorting

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

from datetime import datetime, timedelta, time as dt_time
from typing import Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


class TimeValidationError(Exception):
    """Exception raised for time validation errors."""
    
    def __init__(self, message: str, field: str = "", value: any = None):
        """
        Initialize time validation error.
        
        Args:
            message: Error message
            field: Field name that caused error
            value: Invalid value
        """
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)
    
    def __str__(self):
        if self.field and self.value is not None:
            return f"{self.message} (Field: {self.field}, Value: {self.value})"
        return self.message


@dataclass
class TimeRange:
    """Represents a time range with start and end times."""
    start_time: str  # HH:MM format
    end_time: str    # HH:MM format
    crosses_midnight: bool = False
    
    def __str__(self):
        if self.crosses_midnight:
            return f"{self.start_time} - {self.end_time} (+1 day)"
        return f"{self.start_time} - {self.end_time}"


class TimeValidator:
    """
    Comprehensive time validator for symposium scheduling.
    
    Validates time formats, durations, and detects scheduling conflicts.
    Provides utility methods for time manipulation and comparison.
    """
    
    # Constants
    TIME_FORMAT = "%H:%M"
    TIME_FORMAT_12H = "%I:%M %p"
    
    # Validation bounds
    MIN_DURATION_MINUTES = 1
    MAX_DURATION_MINUTES = 1440  # 24 hours
    RECOMMENDED_MAX_DURATION = 480  # 8 hours
    
    # Warning thresholds
    SHORT_SESSION_WARNING = 5  # Less than 5 minutes
    LONG_SESSION_WARNING = 240  # More than 4 hours
    
    @staticmethod
    def validate_time_format(time_str: str, allow_24_hour: bool = True) -> Tuple[bool, Optional[str]]:
        """
        Validate time format.
        
        Args:
            time_str: Time string to validate
            allow_24_hour: Allow 24:00 format (converts to 00:00)
        
        Returns:
            Tuple of (is_valid, error_message)
        
        Examples:
            >>> TimeValidator.validate_time_format("09:30")
            (True, None)
            >>> TimeValidator.validate_time_format("25:00")
            (False, "Invalid hour: 25. Must be 0-23")
        """
        if not time_str:
            return (False, "Time is required")
        
        # Strip whitespace
        time_str = time_str.strip()
        
        # Check basic format
        if ':' not in time_str:
            return (False, f"Invalid format: '{time_str}'. Expected 'HH:MM'")
        
        parts = time_str.split(':')
        if len(parts) != 2:
            return (False, f"Invalid format: '{time_str}'. Expected 'HH:MM'")
        
        try:
            hour_str, minute_str = parts
            
            # Remove leading zeros for parsing
            hour = int(hour_str)
            minute = int(minute_str)
            
            # Special case: 24:00 converts to 00:00
            if allow_24_hour and hour == 24 and minute == 0:
                return (True, None)
            
            # Validate hour range
            if hour < 0 or hour > 23:
                return (False, f"Invalid hour: {hour}. Must be 0-23")
            
            # Validate minute range
            if minute < 0 or minute > 59:
                return (False, f"Invalid minute: {minute}. Must be 0-59")
            
            # Try to create datetime object to ensure validity
            datetime.strptime(f"{hour:02d}:{minute:02d}", TimeValidator.TIME_FORMAT)
            
            return (True, None)
            
        except ValueError as e:
            return (False, f"Invalid time: '{time_str}'. {str(e)}")
        except Exception as e:
            return (False, f"Unexpected error parsing time '{time_str}': {str(e)}")
    
    @staticmethod
    def validate_duration(duration_minutes: int, 
                         strict: bool = True) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate session duration.
        
        Args:
            duration_minutes: Duration in minutes
            strict: If True, enforce hard limits; if False, return warnings
        
        Returns:
            Tuple of (is_valid, error_message, warning_message)
        
        Examples:
            >>> TimeValidator.validate_duration(30)
            (True, None, None)
            >>> TimeValidator.validate_duration(-5)
            (False, "Duration must be positive", None)
            >>> TimeValidator.validate_duration(300, strict=False)
            (True, None, "Duration is very long (300 min). Recommended max: 480 min")
        """
        error_msg = None
        warning_msg = None
        
        # Check if positive
        if duration_minutes < TimeValidator.MIN_DURATION_MINUTES:
            error_msg = f"Duration must be at least {TimeValidator.MIN_DURATION_MINUTES} minute"
            return (False, error_msg, None)
        
        # Check maximum in strict mode
        if strict and duration_minutes > TimeValidator.MAX_DURATION_MINUTES:
            error_msg = (f"Duration exceeds maximum: {duration_minutes} min. "
                        f"Maximum allowed: {TimeValidator.MAX_DURATION_MINUTES} min (24 hours)")
            return (False, error_msg, None)
        
        # Generate warnings
        if duration_minutes < TimeValidator.SHORT_SESSION_WARNING:
            warning_msg = (f"⚠️ Very short session: {duration_minutes} min. "
                          f"Consider allowing at least {TimeValidator.SHORT_SESSION_WARNING} minutes")
        
        elif duration_minutes > TimeValidator.LONG_SESSION_WARNING:
            if duration_minutes > TimeValidator.MAX_DURATION_MINUTES:
                warning_msg = (f"⚠️ Extremely long session: {duration_minutes} min ({duration_minutes/60:.1f} hours). "
                             f"This exceeds 24 hours and may cause issues!")
            else:
                warning_msg = (f"⚠️ Long session: {duration_minutes} min ({duration_minutes/60:.1f} hours). "
                             f"Consider breaking into multiple sessions")
        
        return (True, None, warning_msg)
    
    @staticmethod
    def normalize_time(time_str: str) -> str:
        """
        Normalize time to HH:MM format (zero-padded).
        
        Args:
            time_str: Time string (e.g., "9:00" or "09:00")
        
        Returns:
            Normalized time string (e.g., "09:00")
        
        Raises:
            TimeValidationError: If time format is invalid
        
        Examples:
            >>> TimeValidator.normalize_time("9:5")
            "09:05"
            >>> TimeValidator.normalize_time("24:00")
            "00:00"
        """
        # Validate first
        valid, error = TimeValidator.validate_time_format(time_str, allow_24_hour=True)
        if not valid:
            raise TimeValidationError(error, field="time", value=time_str)
        
        # Parse and reformat
        parts = time_str.strip().split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        
        # Convert 24:00 to 00:00
        if hour == 24:
            hour = 0
        
        return f"{hour:02d}:{minute:02d}"
    
    @staticmethod
    def calculate_end_time(start_time: str, 
                          duration_minutes: int) -> TimeRange:
        """
        Calculate end time from start time and duration.
        
        Args:
            start_time: Start time in HH:MM format
            duration_minutes: Duration in minutes
        
        Returns:
            TimeRange object with start, end, and midnight crossing flag
        
        Examples:
            >>> result = TimeValidator.calculate_end_time("09:30", 90)
            >>> print(result)
            "09:30 - 11:00"
            >>> result = TimeValidator.calculate_end_time("23:30", 90)
            >>> print(result)
            "23:30 - 01:00 (+1 day)"
        """
        # Normalize and parse start time
        start_normalized = TimeValidator.normalize_time(start_time)
        start_dt = datetime.strptime(start_normalized, TimeValidator.TIME_FORMAT)
        
        # Add duration
        end_dt = start_dt + timedelta(minutes=duration_minutes)
        
        # Check if crossed midnight
        crosses_midnight = end_dt.day != start_dt.day
        
        # Format end time
        end_time_str = end_dt.strftime(TimeValidator.TIME_FORMAT)
        
        return TimeRange(
            start_time=start_normalized,
            end_time=end_time_str,
            crosses_midnight=crosses_midnight
        )
    
    @staticmethod
    def parse_time_to_minutes(time_str: str) -> int:
        """
        Parse time string to minutes since midnight.
        
        Args:
            time_str: Time in HH:MM format
        
        Returns:
            Minutes since midnight (0-1439)
        
        Examples:
            >>> TimeValidator.parse_time_to_minutes("09:30")
            570
            >>> TimeValidator.parse_time_to_minutes("00:00")
            0
        """
        normalized = TimeValidator.normalize_time(time_str)
        dt = datetime.strptime(normalized, TimeValidator.TIME_FORMAT)
        return dt.hour * 60 + dt.minute
    
    @staticmethod
    def minutes_to_time_string(minutes: int) -> str:
        """
        Convert minutes since midnight to time string.
        
        Args:
            minutes: Minutes since midnight
        
        Returns:
            Time string in HH:MM format
        
        Examples:
            >>> TimeValidator.minutes_to_time_string(570)
            "09:30"
        """
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
    
    @staticmethod
    def detect_overlap(session1_start: str, session1_duration: int,
                      session2_start: str, session2_duration: int,
                      buffer_minutes: int = 0) -> bool:
        """
        Detect if two sessions overlap.
        
        Args:
            session1_start: Session 1 start time (HH:MM)
            session1_duration: Session 1 duration (minutes)
            session2_start: Session 2 start time (HH:MM)
            session2_duration: Session 2 duration (minutes)
            buffer_minutes: Required buffer time between sessions (default: 0)
        
        Returns:
            True if sessions overlap (including buffer)
        
        Examples:
            >>> TimeValidator.detect_overlap("09:00", 60, "10:00", 60)
            False
            >>> TimeValidator.detect_overlap("09:00", 60, "09:30", 60)
            True
            >>> TimeValidator.detect_overlap("09:00", 60, "10:00", 60, buffer_minutes=15)
            True  # With 15-min buffer, 10:00 is too soon
        """
        # Parse times to minutes since midnight
        s1_start_min = TimeValidator.parse_time_to_minutes(session1_start)
        s1_end_min = s1_start_min + session1_duration
        
        s2_start_min = TimeValidator.parse_time_to_minutes(session2_start)
        s2_end_min = s2_start_min + session2_duration
        
        # Apply buffer
        s1_end_min += buffer_minutes
        s2_end_min += buffer_minutes
        
        # Handle midnight crossing
        # If end time > 1440 (24 hours), it crosses midnight
        # For simplicity, we check overlap in the same day
        # More complex logic needed for multi-day events
        
        # Check overlap: s1_start < s2_end AND s2_start < s1_end
        return s1_start_min < s2_end_min and s2_start_min < s1_end_min
    
    @staticmethod
    def calculate_gap(session1_start: str, session1_duration: int,
                     session2_start: str) -> int:
        """
        Calculate gap in minutes between end of session1 and start of session2.
        
        Args:
            session1_start: Session 1 start time
            session1_duration: Session 1 duration in minutes
            session2_start: Session 2 start time
        
        Returns:
            Gap in minutes (negative if overlap)
        
        Examples:
            >>> TimeValidator.calculate_gap("09:00", 60, "10:30")
            30  # 30 minute gap
            >>> TimeValidator.calculate_gap("09:00", 90, "10:00")
            -30  # 30 minute overlap
        """
        s1_start_min = TimeValidator.parse_time_to_minutes(session1_start)
        s1_end_min = s1_start_min + session1_duration
        s2_start_min = TimeValidator.parse_time_to_minutes(session2_start)
        
        return s2_start_min - s1_end_min
    
    @staticmethod
    def sort_times(times: List[str]) -> List[str]:
        """
        Sort time strings chronologically.
        
        This fixes the string sort bug where "10:00" < "9:00" (lexicographic).
        
        Args:
            times: List of time strings in HH:MM format
        
        Returns:
            Sorted list of time strings
        
        Examples:
            >>> TimeValidator.sort_times(["10:00", "9:00", "14:30", "9:15"])
            ["09:00", "09:15", "10:00", "14:30"]
        """
        # Normalize all times first
        normalized = [TimeValidator.normalize_time(t) for t in times]
        
        # Sort by parsing to datetime
        sorted_times = sorted(normalized, 
                            key=lambda t: datetime.strptime(t, TimeValidator.TIME_FORMAT))
        
        return sorted_times
    
    @staticmethod
    def format_duration(minutes: int, verbose: bool = False) -> str:
        """
        Format duration for display.
        
        Args:
            minutes: Duration in minutes
            verbose: If True, use verbose format (e.g., "1 hour 30 minutes")
        
        Returns:
            Formatted duration string
        
        Examples:
            >>> TimeValidator.format_duration(90)
            "1h 30m"
            >>> TimeValidator.format_duration(90, verbose=True)
            "1 hour 30 minutes"
        """
        if minutes < 60:
            return f"{minutes} minutes" if verbose else f"{minutes}m"
        
        hours = minutes // 60
        mins = minutes % 60
        
        if verbose:
            hour_str = f"{hours} hour{'s' if hours != 1 else ''}"
            if mins > 0:
                min_str = f"{mins} minute{'s' if mins != 1 else ''}"
                return f"{hour_str} {min_str}"
            return hour_str
        else:
            if mins > 0:
                return f"{hours}h {mins}m"
            return f"{hours}h"
    
    @staticmethod
    def validate_time_sequence(sessions: List[Tuple[str, int]], 
                              allow_overlap: bool = False,
                              min_gap_minutes: int = 0) -> Tuple[bool, List[str]]:
        """
        Validate a sequence of sessions for overlaps and proper ordering.
        
        Args:
            sessions: List of (start_time, duration) tuples
            allow_overlap: If False, detect and report overlaps
            min_gap_minutes: Minimum required gap between sessions
        
        Returns:
            Tuple of (is_valid, error_messages)
        
        Examples:
            >>> sessions = [("09:00", 60), ("10:30", 45), ("11:30", 60)]
            >>> TimeValidator.validate_time_sequence(sessions)
            (True, [])
        """
        errors = []
        
        if len(sessions) < 2:
            return (True, [])
        
        # Sort sessions by start time
        sorted_sessions = sorted(sessions, 
                                key=lambda s: TimeValidator.parse_time_to_minutes(s[0]))
        
        # Check each consecutive pair
        for i in range(len(sorted_sessions) - 1):
            s1_start, s1_duration = sorted_sessions[i]
            s2_start, s2_duration = sorted_sessions[i + 1]
            
            # Check for overlap
            if not allow_overlap:
                if TimeValidator.detect_overlap(s1_start, s1_duration, s2_start, s2_duration):
                    s1_range = TimeValidator.calculate_end_time(s1_start, s1_duration)
                    s2_range = TimeValidator.calculate_end_time(s2_start, s2_duration)
                    errors.append(
                        f"⚠️ Overlap detected: Session {i+1} ({s1_range}) "
                        f"overlaps with Session {i+2} ({s2_range})"
                    )
            
            # Check gap requirement
            if min_gap_minutes > 0:
                gap = TimeValidator.calculate_gap(s1_start, s1_duration, s2_start)
                if gap < min_gap_minutes:
                    errors.append(
                        f"⚠️ Insufficient gap: {gap} minutes between sessions {i+1} and {i+2}. "
                        f"Required: {min_gap_minutes} minutes"
                    )
        
        return (len(errors) == 0, errors)


# Convenience functions for common operations

def validate_and_normalize_time(time_str: str) -> str:
    """
    Validate and normalize time string.
    
    Args:
        time_str: Time string to validate
    
    Returns:
        Normalized time string
    
    Raises:
        TimeValidationError: If validation fails
    """
    valid, error = TimeValidator.validate_time_format(time_str)
    if not valid:
        raise TimeValidationError(error, field="time", value=time_str)
    return TimeValidator.normalize_time(time_str)


def validate_session_duration(duration_minutes: int, strict: bool = True) -> None:
    """
    Validate session duration or raise error.
    
    Args:
        duration_minutes: Duration to validate
        strict: Enforce strict limits
    
    Raises:
        TimeValidationError: If validation fails
    """
    valid, error, warning = TimeValidator.validate_duration(duration_minutes, strict=strict)
    
    if not valid:
        raise TimeValidationError(error, field="duration", value=duration_minutes)
    
    if warning:
        logger.warning(warning)


# Example usage
if __name__ == "__main__":
    # Test validation
    print("=== Time Validation Tests ===")
    
    test_cases = [
        "09:30",  # Valid
        "9:30",   # Valid but needs normalization
        "25:00",  # Invalid hour
        "12:60",  # Invalid minute
        "24:00",  # Valid (converts to 00:00)
        "abc",    # Invalid format
    ]
    
    for time_str in test_cases:
        valid, error = TimeValidator.validate_time_format(time_str)
        if valid:
            normalized = TimeValidator.normalize_time(time_str)
            print(f"✅ '{time_str}' → '{normalized}'")
        else:
            print(f"❌ '{time_str}' → {error}")
    
    print("\n=== Duration Validation Tests ===")
    durations = [-5, 0, 1, 30, 300, 1440, 2000]
    for dur in durations:
        valid, error, warning = TimeValidator.validate_duration(dur, strict=False)
        status = "✅" if valid else "❌"
        print(f"{status} {dur} min: error={error}, warning={warning}")
    
    print("\n=== Overlap Detection Tests ===")
    overlaps = [
        (("09:00", 60), ("10:00", 60), False),  # No overlap
        (("09:00", 90), ("10:00", 60), True),   # Overlap
        (("09:00", 60), ("10:00", 60), True),   # With buffer (default 0)
    ]
    
    for (s1, s2, expected) in overlaps:
        result = TimeValidator.detect_overlap(s1[0], s1[1], s2[0], s2[1])
        status = "✅" if result == expected else "❌"
        print(f"{status} {s1} vs {s2}: overlap={result}")
    
    print("\n=== End Time Calculation ===")
    test_sessions = [
        ("09:30", 90),   # Normal
        ("23:30", 90),   # Crosses midnight
        ("14:00", 240),  # Long session
    ]
    
    for start, duration in test_sessions:
        time_range = TimeValidator.calculate_end_time(start, duration)
        print(f"📅 {start} + {duration}min = {time_range}")

