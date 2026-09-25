"""
Unit Tests for TimeValidator

Tests all functionality of the time validation system including:
- Time format validation
- Duration validation
- Overlap detection
- Time calculations
- Edge cases
"""

import pytest
from modules.symposium.time_validator import (
    TimeValidator,
    TimeValidationError,
    TimeRange,
    validate_and_normalize_time,
    validate_session_duration
)


class TestTimeFormatValidation:
    """Test time format validation."""
    
    def test_valid_times(self):
        """Test that valid times pass validation."""
        valid_times = [
            "09:30",
            "00:00",
            "23:59",
            "12:00",
            "01:05",
        ]
        
        for time_str in valid_times:
            valid, error = TimeValidator.validate_time_format(time_str)
            assert valid, f"Expected '{time_str}' to be valid, got error: {error}"
            assert error is None
    
    def test_invalid_hour(self):
        """Test that invalid hours are rejected."""
        invalid_times = [
            "25:00",
            "24:01",
            "-01:00",
            "99:00",
        ]
        
        for time_str in invalid_times:
            valid, error = TimeValidator.validate_time_format(time_str)
            assert not valid, f"Expected '{time_str}' to be invalid"
            assert "hour" in error.lower()
    
    def test_invalid_minute(self):
        """Test that invalid minutes are rejected."""
        invalid_times = [
            "12:60",
            "09:99",
            "10:-5",
        ]
        
        for time_str in invalid_times:
            valid, error = TimeValidator.validate_time_format(time_str)
            assert not valid, f"Expected '{time_str}' to be invalid"
            assert "minute" in error.lower()
    
    def test_invalid_format(self):
        """Test that invalid formats are rejected."""
        invalid_formats = [
            "abc",
            "12-30",
            "9:30:00",  # Seconds not supported
            "930",
            "9",
            "",
            "12:",
            ":30",
        ]
        
        for time_str in invalid_formats:
            valid, error = TimeValidator.validate_time_format(time_str)
            assert not valid, f"Expected '{time_str}' to be invalid"
            assert error is not None
    
    def test_24_hour_format(self):
        """Test 24:00 special case."""
        valid, error = TimeValidator.validate_time_format("24:00", allow_24_hour=True)
        assert valid
        assert error is None
        
        # Should be rejected without allow_24_hour
        valid, error = TimeValidator.validate_time_format("24:00", allow_24_hour=False)
        assert not valid


class TestTimeNormalization:
    """Test time normalization."""
    
    def test_normalize_single_digit(self):
        """Test normalization of single-digit hours/minutes."""
        assert TimeValidator.normalize_time("9:5") == "09:05"
        assert TimeValidator.normalize_time("9:30") == "09:30"
        assert TimeValidator.normalize_time("12:5") == "12:05"
    
    def test_normalize_already_normalized(self):
        """Test that already normalized times remain unchanged."""
        assert TimeValidator.normalize_time("09:30") == "09:30"
        assert TimeValidator.normalize_time("00:00") == "00:00"
        assert TimeValidator.normalize_time("23:59") == "23:59"
    
    def test_normalize_24_hour(self):
        """Test that 24:00 converts to 00:00."""
        assert TimeValidator.normalize_time("24:00") == "00:00"
    
    def test_normalize_invalid_raises_error(self):
        """Test that invalid times raise TimeValidationError."""
        with pytest.raises(TimeValidationError):
            TimeValidator.normalize_time("25:00")
        
        with pytest.raises(TimeValidationError):
            TimeValidator.normalize_time("abc")


class TestDurationValidation:
    """Test duration validation."""
    
    def test_valid_durations(self):
        """Test that valid durations pass."""
        valid_durations = [1, 5, 30, 60, 90, 120, 240, 480, 1440]
        
        for duration in valid_durations:
            valid, error, warning = TimeValidator.validate_duration(duration)
            assert valid, f"Expected {duration} to be valid"
            assert error is None
    
    def test_negative_duration(self):
        """Test that negative durations are rejected."""
        valid, error, warning = TimeValidator.validate_duration(-30)
        assert not valid
        assert "positive" in error.lower() or "at least" in error.lower()
    
    def test_zero_duration(self):
        """Test that zero duration is rejected."""
        valid, error, warning = TimeValidator.validate_duration(0)
        assert not valid
    
    def test_extremely_long_duration_strict(self):
        """Test that extremely long durations are rejected in strict mode."""
        valid, error, warning = TimeValidator.validate_duration(2000, strict=True)
        assert not valid
        assert "maximum" in error.lower()
    
    def test_extremely_long_duration_non_strict(self):
        """Test that extremely long durations generate warnings in non-strict mode."""
        valid, error, warning = TimeValidator.validate_duration(2000, strict=False)
        assert valid  # Valid in non-strict mode
        assert error is None
        assert warning is not None
        assert "long" in warning.lower()
    
    def test_short_duration_warning(self):
        """Test that very short durations generate warnings."""
        valid, error, warning = TimeValidator.validate_duration(3, strict=False)
        assert valid
        assert error is None
        assert warning is not None
        assert "short" in warning.lower()
    
    def test_long_duration_warning(self):
        """Test that long durations generate warnings."""
        valid, error, warning = TimeValidator.validate_duration(300, strict=False)
        assert valid
        assert error is None
        assert warning is not None


class TestEndTimeCalculation:
    """Test end time calculation."""
    
    def test_simple_calculation(self):
        """Test simple end time calculation."""
        result = TimeValidator.calculate_end_time("09:00", 60)
        assert result.start_time == "09:00"
        assert result.end_time == "10:00"
        assert result.crosses_midnight == False
    
    def test_fractional_hours(self):
        """Test calculation with non-hour durations."""
        result = TimeValidator.calculate_end_time("09:30", 45)
        assert result.start_time == "09:30"
        assert result.end_time == "10:15"
        assert result.crosses_midnight == False
    
    def test_midnight_crossing(self):
        """Test that midnight crossing is detected."""
        result = TimeValidator.calculate_end_time("23:30", 90)
        assert result.start_time == "23:30"
        assert result.end_time == "01:00"
        assert result.crosses_midnight == True
    
    def test_midnight_exactly(self):
        """Test session ending exactly at midnight."""
        result = TimeValidator.calculate_end_time("22:00", 120)
        assert result.end_time == "00:00"
        assert result.crosses_midnight == True
    
    def test_long_session(self):
        """Test very long session (multiple hours)."""
        result = TimeValidator.calculate_end_time("09:00", 480)  # 8 hours
        assert result.start_time == "09:00"
        assert result.end_time == "17:00"
        assert result.crosses_midnight == False


class TestOverlapDetection:
    """Test session overlap detection."""
    
    def test_no_overlap_sequential(self):
        """Test sequential sessions with no overlap."""
        assert TimeValidator.detect_overlap("09:00", 60, "10:00", 60) == False
        assert TimeValidator.detect_overlap("09:00", 30, "09:30", 30) == False
    
    def test_overlap_concurrent_start(self):
        """Test sessions starting at same time."""
        assert TimeValidator.detect_overlap("09:00", 60, "09:00", 60) == True
    
    def test_overlap_partial(self):
        """Test partially overlapping sessions."""
        assert TimeValidator.detect_overlap("09:00", 90, "10:00", 60) == True
        assert TimeValidator.detect_overlap("10:00", 60, "09:00", 90) == True
    
    def test_overlap_contained(self):
        """Test one session completely within another."""
        assert TimeValidator.detect_overlap("09:00", 180, "10:00", 30) == True
    
    def test_buffer_time(self):
        """Test overlap detection with buffer time."""
        # Without buffer: no overlap
        assert TimeValidator.detect_overlap("09:00", 60, "10:00", 60, buffer_minutes=0) == False
        
        # With 15-min buffer: overlap detected
        assert TimeValidator.detect_overlap("09:00", 60, "10:00", 60, buffer_minutes=15) == True
    
    def test_gap_exactly_zero(self):
        """Test sessions with exactly zero gap."""
        # 09:00 + 60min = 10:00, next starts at 10:00
        # This should NOT overlap (back-to-back is OK)
        assert TimeValidator.detect_overlap("09:00", 60, "10:00", 30) == False


class TestGapCalculation:
    """Test gap calculation between sessions."""
    
    def test_positive_gap(self):
        """Test calculation of positive gap."""
        gap = TimeValidator.calculate_gap("09:00", 60, "10:30")
        assert gap == 30  # 30 minute gap
    
    def test_zero_gap(self):
        """Test back-to-back sessions (zero gap)."""
        gap = TimeValidator.calculate_gap("09:00", 60, "10:00")
        assert gap == 0
    
    def test_negative_gap_overlap(self):
        """Test negative gap (overlap)."""
        gap = TimeValidator.calculate_gap("09:00", 90, "10:00")
        assert gap == -30  # 30 minute overlap


class TestTimeSorting:
    """Test chronological time sorting."""
    
    def test_sort_already_sorted(self):
        """Test sorting already sorted times."""
        times = ["09:00", "10:00", "11:00"]
        sorted_times = TimeValidator.sort_times(times)
        assert sorted_times == ["09:00", "10:00", "11:00"]
    
    def test_sort_reverse_order(self):
        """Test sorting reverse order times."""
        times = ["14:00", "11:00", "09:00"]
        sorted_times = TimeValidator.sort_times(times)
        assert sorted_times == ["09:00", "11:00", "14:00"]
    
    def test_sort_single_digit_bug(self):
        """Test that single-digit hours sort correctly (fixes string sort bug)."""
        times = ["10:00", "9:00", "14:30", "9:15"]
        sorted_times = TimeValidator.sort_times(times)
        # String sort would give: ["10:00", "14:30", "9:00", "9:15"] - WRONG!
        # Correct sort:
        assert sorted_times == ["09:00", "09:15", "10:00", "14:30"]
    
    def test_sort_normalizes_times(self):
        """Test that sorting also normalizes time format."""
        times = ["9:0", "14:30", "9:15"]
        sorted_times = TimeValidator.sort_times(times)
        assert sorted_times == ["09:00", "09:15", "14:30"]
        # All normalized to HH:MM


class TestTimeSequenceValidation:
    """Test validation of session sequences."""
    
    def test_valid_sequence(self):
        """Test valid session sequence."""
        sessions = [
            ("09:00", 60),
            ("10:30", 45),
            ("11:30", 60),
        ]
        valid, errors = TimeValidator.validate_time_sequence(sessions)
        assert valid
        assert len(errors) == 0
    
    def test_sequence_with_overlap(self):
        """Test sequence with overlaps."""
        sessions = [
            ("09:00", 90),  # Ends at 10:30
            ("10:00", 60),  # Starts at 10:00 - OVERLAP!
        ]
        valid, errors = TimeValidator.validate_time_sequence(sessions, allow_overlap=False)
        assert not valid
        assert len(errors) > 0
        assert "overlap" in errors[0].lower()
    
    def test_sequence_allows_overlap_if_specified(self):
        """Test that overlaps are allowed if specified."""
        sessions = [
            ("09:00", 90),
            ("10:00", 60),
        ]
        valid, errors = TimeValidator.validate_time_sequence(sessions, allow_overlap=True)
        assert valid
        assert len(errors) == 0
    
    def test_sequence_min_gap_requirement(self):
        """Test minimum gap requirement."""
        sessions = [
            ("09:00", 60),  # Ends at 10:00
            ("10:05", 60),  # Starts at 10:05 - only 5 min gap
        ]
        
        # Should pass with 5 min gap requirement
        valid, errors = TimeValidator.validate_time_sequence(sessions, min_gap_minutes=5)
        assert valid
        
        # Should fail with 15 min gap requirement
        valid, errors = TimeValidator.validate_time_sequence(sessions, min_gap_minutes=15)
        assert not valid
        assert "gap" in errors[0].lower()
    
    def test_sequence_sorts_automatically(self):
        """Test that sequence validation sorts sessions first."""
        # Provide in wrong order
        sessions = [
            ("11:00", 60),
            ("09:00", 60),
            ("10:30", 30),
        ]
        valid, errors = TimeValidator.validate_time_sequence(sessions)
        assert valid  # Should sort and validate correctly


class TestTimeParsingConversion:
    """Test time parsing and conversion utilities."""
    
    def test_parse_time_to_minutes(self):
        """Test conversion of time to minutes since midnight."""
        assert TimeValidator.parse_time_to_minutes("00:00") == 0
        assert TimeValidator.parse_time_to_minutes("01:00") == 60
        assert TimeValidator.parse_time_to_minutes("09:30") == 570
        assert TimeValidator.parse_time_to_minutes("23:59") == 1439
    
    def test_minutes_to_time_string(self):
        """Test conversion of minutes to time string."""
        assert TimeValidator.minutes_to_time_string(0) == "00:00"
        assert TimeValidator.minutes_to_time_string(60) == "01:00"
        assert TimeValidator.minutes_to_time_string(570) == "09:30"
        assert TimeValidator.minutes_to_time_string(1439) == "23:59"
    
    def test_round_trip_conversion(self):
        """Test that time -> minutes -> time is consistent."""
        times = ["00:00", "09:30", "12:00", "23:59"]
        for time_str in times:
            minutes = TimeValidator.parse_time_to_minutes(time_str)
            back_to_time = TimeValidator.minutes_to_time_string(minutes)
            assert back_to_time == time_str


class TestDurationFormatting:
    """Test duration formatting for display."""
    
    def test_format_minutes_only(self):
        """Test formatting durations less than 1 hour."""
        assert TimeValidator.format_duration(30) == "30m"
        assert TimeValidator.format_duration(45) == "45m"
        assert TimeValidator.format_duration(30, verbose=True) == "30 minutes"
    
    def test_format_hours_only(self):
        """Test formatting exact hours."""
        assert TimeValidator.format_duration(60) == "1h"
        assert TimeValidator.format_duration(120) == "2h"
        assert TimeValidator.format_duration(60, verbose=True) == "1 hour"
        assert TimeValidator.format_duration(120, verbose=True) == "2 hours"
    
    def test_format_hours_and_minutes(self):
        """Test formatting hours and minutes."""
        assert TimeValidator.format_duration(90) == "1h 30m"
        assert TimeValidator.format_duration(150) == "2h 30m"
        assert TimeValidator.format_duration(90, verbose=True) == "1 hour 30 minutes"
        assert TimeValidator.format_duration(150, verbose=True) == "2 hours 30 minutes"


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""
    
    def test_validate_and_normalize_success(self):
        """Test successful validation and normalization."""
        result = validate_and_normalize_time("9:30")
        assert result == "09:30"
    
    def test_validate_and_normalize_failure(self):
        """Test that invalid time raises exception."""
        with pytest.raises(TimeValidationError) as exc_info:
            validate_and_normalize_time("25:00")
        assert "hour" in str(exc_info.value).lower()
    
    def test_validate_session_duration_success(self):
        """Test successful duration validation."""
        validate_session_duration(30)  # Should not raise
    
    def test_validate_session_duration_failure(self):
        """Test that invalid duration raises exception."""
        with pytest.raises(TimeValidationError):
            validate_session_duration(-30)


class TestTimeRange:
    """Test TimeRange dataclass."""
    
    def test_time_range_string_normal(self):
        """Test TimeRange string representation for normal session."""
        tr = TimeRange("09:00", "10:30", crosses_midnight=False)
        assert str(tr) == "09:00 - 10:30"
    
    def test_time_range_string_midnight_crossing(self):
        """Test TimeRange string representation with midnight crossing."""
        tr = TimeRange("23:30", "01:00", crosses_midnight=True)
        assert str(tr) == "23:30 - 01:00 (+1 day)"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_minute_duration(self):
        """Test minimum valid duration (1 minute)."""
        valid, error, warning = TimeValidator.validate_duration(1)
        assert valid
    
    def test_exactly_24_hours(self):
        """Test exactly 24 hour duration."""
        valid, error, warning = TimeValidator.validate_duration(1440, strict=True)
        assert valid
    
    def test_over_24_hours_strict(self):
        """Test over 24 hours in strict mode."""
        valid, error, warning = TimeValidator.validate_duration(1441, strict=True)
        assert not valid
    
    def test_midnight_to_midnight(self):
        """Test session from midnight to midnight (24 hours)."""
        result = TimeValidator.calculate_end_time("00:00", 1440)
        assert result.end_time == "00:00"
        assert result.crosses_midnight == True
    
    def test_23_59_plus_1_minute(self):
        """Test session at 23:59 + 1 minute."""
        result = TimeValidator.calculate_end_time("23:59", 1)
        assert result.end_time == "00:00"
        assert result.crosses_midnight == True


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

