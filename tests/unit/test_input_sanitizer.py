"""
Unit Tests for InputSanitizer

Tests input validation and sanitization for:
- Name sanitization
- Unicode handling
- Null byte removal
- Length limits
- Email validation
- Path validation
- SQL injection detection
- XSS detection
"""

import pytest
from pathlib import Path
from modules.utils.input_sanitizer import (
    InputSanitizer,
    InputSanitizationError,
    sanitize_speaker_name,
    sanitize_talk_title
)


class TestBasicSanitization:
    """Test basic string sanitization."""
    
    def test_simple_string(self):
        """Test sanitization of simple clean string."""
        text, warnings = InputSanitizer.sanitize_string("Hello World")
        assert text == "Hello World"
        assert len(warnings) == 0
    
    def test_null_byte_removal(self):
        """Test that null bytes are removed."""
        text, warnings = InputSanitizer.sanitize_string("Hello\x00World")
        assert text == "HelloWorld"
        assert len(warnings) > 0
        assert "null byte" in warnings[0].lower()
    
    def test_multiple_null_bytes(self):
        """Test removal of multiple null bytes."""
        text, warnings = InputSanitizer.sanitize_string("A\x00B\x00C\x00")
        assert text == "ABC"
        assert "3 null byte" in warnings[0]
    
    def test_whitespace_stripping(self):
        """Test that leading/trailing whitespace is stripped."""
        text, warnings = InputSanitizer.sanitize_string("  Hello  ")
        assert text == "Hello"
    
    def test_length_truncation(self):
        """Test that long strings are truncated."""
        long_text = "A" * 100
        text, warnings = InputSanitizer.sanitize_string(long_text, max_length=50)
        assert len(text) == 50
        assert len(warnings) > 0
        assert "truncated" in warnings[0].lower()
    
    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        # Combining characters
        text = "café"  # May be represented as c+a+f+é or c+a+f+e+´
        sanitized, warnings = InputSanitizer.sanitize_string(text, normalize_unicode=True)
        # Should be normalized to consistent form
        assert len(sanitized) <= len(text)
    
    def test_control_character_removal(self):
        """Test removal of control characters."""
        text = "Hello\x01\x02World\x03"
        sanitized, warnings = InputSanitizer.sanitize_string(
            text,
            remove_control_chars=True,
            allow_newlines=False
        )
        assert sanitized == "HelloWorld"
        assert len(warnings) > 0


class TestNameSanitization:
    """Test name-specific sanitization."""
    
    def test_simple_name(self):
        """Test sanitization of simple name."""
        name, warnings = InputSanitizer.sanitize_name("John Doe")
        assert name == "John Doe"
        assert len(warnings) == 0
    
    def test_unicode_name_farsi(self):
        """Test Farsi/Persian name."""
        name, warnings = InputSanitizer.sanitize_name("محمد رضا احمدی")
        assert name == "محمد رضا احمدی"
        assert len(warnings) == 0
    
    def test_unicode_name_chinese(self):
        """Test Chinese name."""
        name, warnings = InputSanitizer.sanitize_name("张伟")
        assert name == "张伟"
        assert len(warnings) == 0
    
    def test_unicode_name_russian(self):
        """Test Russian name."""
        name, warnings = InputSanitizer.sanitize_name("Владимир Петров")
        assert name == "Владимир Петров"
        assert len(warnings) == 0
    
    def test_name_with_accents(self):
        """Test name with accented characters."""
        name, warnings = InputSanitizer.sanitize_name("José García")
        assert name == "José García"
        assert len(warnings) == 0
    
    def test_name_with_apostrophe(self):
        """Test name with apostrophe."""
        name, warnings = InputSanitizer.sanitize_name("O'Brien")
        assert name == "O'Brien"
        assert len(warnings) == 0
    
    def test_name_with_hyphen(self):
        """Test hyphenated name."""
        name, warnings = InputSanitizer.sanitize_name("Jean-Claude")
        assert name == "Jean-Claude"
        assert len(warnings) == 0
    
    def test_empty_name_raises_error(self):
        """Test that empty name raises error."""
        with pytest.raises(InputSanitizationError):
            InputSanitizer.sanitize_name("")
    
    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only name raises error."""
        with pytest.raises(InputSanitizationError):
            InputSanitizer.sanitize_name("   ")
    
    def test_extremely_long_name(self):
        """Test that extremely long names are truncated."""
        long_name = "A" * 500
        name, warnings = InputSanitizer.sanitize_name(long_name)
        assert len(name) == InputSanitizer.MAX_NAME_LENGTH
        assert len(warnings) > 0
    
    def test_sql_injection_in_name(self):
        """Test detection of SQL injection patterns."""
        name = "Robert'; DROP TABLE speakers;--"
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        # Should sanitize but warn
        assert sanitized == name  # Keeps as-is for desktop app
        assert len(warnings) > 0
        assert any("SQL" in w for w in warnings)
    
    def test_xss_in_name(self):
        """Test detection of XSS patterns."""
        name = "<script>alert('xss')</script>"
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        assert len(warnings) > 0
        assert any("script" in w.lower() for w in warnings)


class TestTitleSanitization:
    """Test title sanitization."""
    
    def test_simple_title(self):
        """Test simple title."""
        title, warnings = InputSanitizer.sanitize_title("Introduction to AI")
        assert title == "Introduction to AI"
        assert len(warnings) == 0
    
    def test_title_with_unicode(self):
        """Test title with Unicode."""
        title, warnings = InputSanitizer.sanitize_title("تحلیل داده با هوش مصنوعی")
        assert title == "تحلیل داده با هوش مصنوعی"
        assert len(warnings) == 0
    
    def test_empty_title_raises_error(self):
        """Test that empty title raises error."""
        with pytest.raises(InputSanitizationError):
            InputSanitizer.sanitize_title("")
    
    def test_title_length_limit(self):
        """Test title length limit."""
        long_title = "A" * 1000
        title, warnings = InputSanitizer.sanitize_title(long_title)
        assert len(title) == InputSanitizer.MAX_TITLE_LENGTH
        assert len(warnings) > 0


class TestBioSanitization:
    """Test biography sanitization."""
    
    def test_simple_bio(self):
        """Test simple bio."""
        bio = "Professor of Computer Science"
        sanitized, warnings = InputSanitizer.sanitize_bio(bio)
        assert sanitized == bio
        assert len(warnings) == 0
    
    def test_bio_with_newlines(self):
        """Test bio with newlines (should be preserved)."""
        bio = "Line 1\nLine 2\nLine 3"
        sanitized, warnings = InputSanitizer.sanitize_bio(bio)
        assert "\n" in sanitized
        assert len(warnings) == 0
    
    def test_empty_bio(self):
        """Test that empty bio is OK."""
        bio, warnings = InputSanitizer.sanitize_bio("")
        assert bio == ""
        assert len(warnings) == 0
    
    def test_bio_length_limit(self):
        """Test bio length limit."""
        long_bio = "A" * 10000
        bio, warnings = InputSanitizer.sanitize_bio(long_bio)
        assert len(bio) == InputSanitizer.MAX_BIO_LENGTH
        assert len(warnings) > 0


class TestEmailValidation:
    """Test email validation."""
    
    def test_valid_emails(self):
        """Test valid email addresses."""
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+filter@domain.org",
            "user123@test-domain.com",
        ]
        
        for email in valid_emails:
            valid, error, sanitized = InputSanitizer.validate_email(email)
            assert valid, f"Expected '{email}' to be valid, got error: {error}"
            assert error is None
            assert sanitized == email.lower()
    
    def test_invalid_emails(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid.email",
            "@example.com",
            "user@",
            "user name@example.com",  # Space
            "user@domain",  # No TLD
        ]
        
        for email in invalid_emails:
            valid, error, sanitized = InputSanitizer.validate_email(email)
            assert not valid, f"Expected '{email}' to be invalid"
            assert error is not None
    
    def test_empty_email(self):
        """Test that empty email is valid (optional field)."""
        valid, error, sanitized = InputSanitizer.validate_email("")
        assert valid
        assert error is None
        assert sanitized == ""
    
    def test_email_with_dangerous_chars(self):
        """Test email with dangerous characters."""
        dangerous_emails = [
            "user<script>@example.com",
            "user@example.com\n",
            "user'@example.com",
        ]
        
        for email in dangerous_emails:
            valid, error, sanitized = InputSanitizer.validate_email(email)
            assert not valid
    
    def test_email_length_limit(self):
        """Test email length limit."""
        long_email = "a" * 300 + "@example.com"
        valid, error, sanitized = InputSanitizer.validate_email(long_email)
        assert not valid
        assert "too long" in error.lower()
    
    def test_email_normalization(self):
        """Test that emails are lowercased."""
        valid, error, sanitized = InputSanitizer.validate_email("User@EXAMPLE.COM")
        assert valid
        assert sanitized == "user@example.com"


class TestPathValidation:
    """Test file path validation."""
    
    def test_valid_path(self):
        """Test valid file path."""
        valid, error, path = InputSanitizer.sanitize_file_path("document.pdf")
        assert valid
        assert error is None
        assert path is not None
    
    def test_path_traversal_dotdot(self):
        """Test path traversal with .."""
        valid, error, path = InputSanitizer.sanitize_file_path("../etc/passwd")
        assert not valid
        assert "traversal" in error.lower()
        assert path is None
    
    def test_path_traversal_absolute(self):
        """Test absolute path (potential traversal)."""
        valid, error, path = InputSanitizer.sanitize_file_path("/etc/passwd")
        assert not valid
        assert "traversal" in error.lower()
    
    def test_path_with_null_byte(self):
        """Test path with null byte."""
        valid, error, path = InputSanitizer.sanitize_file_path("file\x00.pdf")
        assert not valid
        assert "null byte" in error.lower()
    
    def test_path_too_long(self):
        """Test excessively long path."""
        long_path = "a" * 500 + ".pdf"
        valid, error, path = InputSanitizer.sanitize_file_path(long_path)
        assert not valid
        assert "too long" in error.lower()
    
    def test_empty_path(self):
        """Test that empty path is OK (optional)."""
        valid, error, path = InputSanitizer.sanitize_file_path("")
        assert valid
        assert path is None
    
    def test_path_with_allowed_extensions(self):
        """Test path validation with extension whitelist."""
        valid, error, path = InputSanitizer.sanitize_file_path(
            "document.pdf",
            allowed_extensions=['.pdf', '.docx']
        )
        assert valid
        
        valid, error, path = InputSanitizer.sanitize_file_path(
            "document.exe",
            allowed_extensions=['.pdf', '.docx']
        )
        assert not valid
        assert "extension" in error.lower()


class TestIntegerValidation:
    """Test integer validation."""
    
    def test_valid_integer(self):
        """Test valid integer."""
        valid, error, value = InputSanitizer.validate_integer(42)
        assert valid
        assert error is None
        assert value == 42
    
    def test_integer_from_string(self):
        """Test parsing integer from string."""
        valid, error, value = InputSanitizer.validate_integer("123")
        assert valid
        assert value == 123
    
    def test_integer_min_value(self):
        """Test minimum value validation."""
        valid, error, value = InputSanitizer.validate_integer(5, min_value=10)
        assert not valid
        assert "at least" in error.lower()
    
    def test_integer_max_value(self):
        """Test maximum value validation."""
        valid, error, value = InputSanitizer.validate_integer(100, max_value=50)
        assert not valid
        assert "at most" in error.lower()
    
    def test_integer_in_range(self):
        """Test integer within range."""
        valid, error, value = InputSanitizer.validate_integer(
            25,
            min_value=0,
            max_value=100
        )
        assert valid
        assert value == 25
    
    def test_invalid_integer(self):
        """Test invalid integer."""
        valid, error, value = InputSanitizer.validate_integer("not_a_number")
        assert not valid
        assert "invalid" in error.lower()


class TestSessionIdSanitization:
    """Test session ID sanitization."""
    
    def test_simple_session_id(self):
        """Test simple alphanumeric session ID."""
        session_id, warnings = InputSanitizer.sanitize_session_id("session_123")
        assert session_id == "session_123"
        assert len(warnings) == 0
    
    def test_session_id_with_hyphen(self):
        """Test session ID with hyphens."""
        session_id, warnings = InputSanitizer.sanitize_session_id("session-01-2025")
        assert session_id == "session-01-2025"
        assert len(warnings) == 0
    
    def test_session_id_with_invalid_chars(self):
        """Test that invalid characters are replaced."""
        session_id, warnings = InputSanitizer.sanitize_session_id("session@#$123")
        assert session_id == "session___123"
        assert len(warnings) > 0
    
    def test_empty_session_id_raises_error(self):
        """Test that empty session ID raises error."""
        with pytest.raises(InputSanitizationError):
            InputSanitizer.sanitize_session_id("")


class TestPatternDetection:
    """Test malicious pattern detection."""
    
    def test_sql_injection_detection(self):
        """Test SQL injection pattern detection."""
        patterns = [
            "SELECT * FROM users",
            "'; DROP TABLE speakers;--",
            "1=1 OR 1=1",
            "admin'--",
        ]
        
        for pattern in patterns:
            assert InputSanitizer._contains_sql_injection(pattern), \
                f"Failed to detect SQL injection: {pattern}"
    
    def test_xss_detection(self):
        """Test XSS pattern detection."""
        patterns = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "<img onerror='alert(1)'>",
            "<iframe src='evil.com'>",
        ]
        
        for pattern in patterns:
            assert InputSanitizer._contains_xss(pattern), \
                f"Failed to detect XSS: {pattern}"
    
    def test_path_traversal_detection(self):
        """Test path traversal pattern detection."""
        patterns = [
            "../etc/passwd",
            "..\\windows\\system32",
            "/etc/shadow",
            "C:\\Windows\\System32",
        ]
        
        for pattern in patterns:
            assert InputSanitizer._contains_path_traversal(pattern), \
                f"Failed to detect path traversal: {pattern}"


class TestConvenienceFunctions:
    """Test convenience wrapper functions."""
    
    def test_sanitize_speaker_name_success(self):
        """Test successful speaker name sanitization."""
        name = sanitize_speaker_name("John Doe")
        assert name == "John Doe"
    
    def test_sanitize_speaker_name_failure(self):
        """Test that invalid speaker name raises error."""
        with pytest.raises(InputSanitizationError):
            sanitize_speaker_name("")
    
    def test_sanitize_talk_title_success(self):
        """Test successful talk title sanitization."""
        title = sanitize_talk_title("Introduction to AI")
        assert title == "Introduction to AI"
    
    def test_sanitize_talk_title_failure(self):
        """Test that invalid title raises error."""
        with pytest.raises(InputSanitizationError):
            sanitize_talk_title("")


class TestDictionarySanitization:
    """Test dictionary sanitization."""
    
    def test_sanitize_dict(self):
        """Test sanitizing entire dictionary."""
        data = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'age': '30'
        }
        
        specs = {
            'name': lambda x: InputSanitizer.sanitize_name(x),
            'email': lambda x: InputSanitizer.validate_email(x),
            'age': lambda x: InputSanitizer.validate_integer(x, min_value=0, max_value=150)
        }
        
        sanitized, warnings = InputSanitizer.sanitize_dict(data, specs)
        
        assert 'name' in sanitized
        assert 'email' in sanitized
        assert 'age' in sanitized


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_emoji_in_name(self):
        """Test emoji in name (should be preserved)."""
        name = "🎉 John Doe 🚀"
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        # Emojis should be preserved (valid Unicode)
        assert "John Doe" in sanitized
    
    def test_mixed_scripts(self):
        """Test name with mixed scripts."""
        name = "John المحمد 张"  # English + Arabic + Chinese
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        assert len(sanitized) > 0
        assert len(warnings) == 0
    
    def test_zero_width_characters(self):
        """Test removal of zero-width characters."""
        # Zero-width space (U+200B)
        name = "John\u200bDoe"
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        # Should be removed by control char filtering
        assert sanitized in ["JohnDoe", "John Doe"]  # May or may not have space
    
    def test_rtl_text(self):
        """Test right-to-left text (Arabic, Hebrew)."""
        name = "محمد علي"  # Arabic (RTL)
        sanitized, warnings = InputSanitizer.sanitize_name(name)
        assert sanitized == name
        assert len(warnings) == 0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

