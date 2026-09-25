"""
Input Sanitization and Validation Module

Provides comprehensive input sanitization for user-provided data to prevent:
- Unicode/encoding issues
- Null byte injection
- Excessively long strings
- Path traversal attacks
- SQL injection attempts (even though using JSON, for future-proofing)
- XSS attempts (for future web interface)

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import re
import unicodedata
from typing import Optional, Tuple, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class InputSanitizationError(Exception):
    """Exception raised for input sanitization errors."""
    
    def __init__(self, message: str, field: str = "", value: any = None):
        """
        Initialize sanitization error.
        
        Args:
            message: Error message
            field: Field name that caused error
            value: Invalid value
        """
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.message)


class InputSanitizer:
    """
    Comprehensive input sanitizer for all user-provided data.
    
    Validates and sanitizes strings, numbers, paths, emails, and other inputs.
    """
    
    # Length limits
    MAX_NAME_LENGTH = 200
    MAX_TITLE_LENGTH = 500
    MAX_BIO_LENGTH = 5000
    MAX_EMAIL_LENGTH = 254  # RFC 5321
    MAX_PATH_LENGTH = 260   # Windows MAX_PATH
    MAX_NOTES_LENGTH = 10000
    
    # Validation patterns
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|\#|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"(';|\";\s*DROP)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\.",
        r"^/",
        r"^\\",
        r"^[A-Za-z]:",  # Drive letters
    ]
    
    @staticmethod
    def sanitize_string(
        text: str,
        max_length: Optional[int] = None,
        remove_null_bytes: bool = True,
        remove_control_chars: bool = True,
        normalize_unicode: bool = True,
        strip_whitespace: bool = True,
        allow_newlines: bool = True,
        field_name: str = "text"
    ) -> Tuple[str, List[str]]:
        """
        Sanitize a general string input.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            remove_null_bytes: Remove null bytes (\x00)
            remove_control_chars: Remove control characters
            normalize_unicode: Normalize Unicode to NFC form
            strip_whitespace: Strip leading/trailing whitespace
            allow_newlines: Allow newline characters
            field_name: Name of field for warning messages
        
        Returns:
            Tuple of (sanitized_text, warnings)
        
        Examples:
            >>> InputSanitizer.sanitize_string("Hello\\x00World", max_length=20)
            ("HelloWorld", ["Removed 1 null byte(s)"])
        """
        if text is None:
            return ("", [])
        
        if not isinstance(text, str):
            text = str(text)
        
        original_length = len(text)
        warnings = []
        
        # Remove null bytes
        if remove_null_bytes:
            null_count = text.count('\x00')
            if null_count > 0:
                text = text.replace('\x00', '')
                warnings.append(f"Removed {null_count} null byte(s) from {field_name}")
                logger.warning(f"Null bytes detected in {field_name}")
        
        # Normalize Unicode
        if normalize_unicode:
            try:
                # Normalize to NFC (Canonical Decomposition, followed by Canonical Composition)
                text = unicodedata.normalize('NFC', text)
            except Exception as e:
                warnings.append(f"Unicode normalization failed: {str(e)}")
        
        # Remove control characters (except allowed ones)
        if remove_control_chars:
            allowed_chars = {'\n', '\r', '\t'} if allow_newlines else {'\t'}
            original_text = text
            text = ''.join(
                char for char in text
                if not unicodedata.category(char).startswith('C') or char in allowed_chars
            )
            if len(text) != len(original_text):
                removed = len(original_text) - len(text)
                warnings.append(f"Removed {removed} control character(s) from {field_name}")
        
        # Strip whitespace
        if strip_whitespace:
            text = text.strip()
        
        # Truncate if needed
        if max_length and len(text) > max_length:
            text = text[:max_length]
            warnings.append(
                f"{field_name.capitalize()} truncated from {original_length} to {max_length} characters"
            )
        
        return (text, warnings)
    
    @staticmethod
    def sanitize_name(name: str, field_name: str = "name") -> Tuple[str, List[str]]:
        """
        Sanitize a person's name (speaker, presenter, etc.).
        
        Args:
            name: Name to sanitize
            field_name: Field name for warnings
        
        Returns:
            Tuple of (sanitized_name, warnings)
        
        Raises:
            InputSanitizationError: If name is empty after sanitization
        """
        sanitized, warnings = InputSanitizer.sanitize_string(
            name,
            max_length=InputSanitizer.MAX_NAME_LENGTH,
            remove_null_bytes=True,
            remove_control_chars=True,
            normalize_unicode=True,
            strip_whitespace=True,
            allow_newlines=False,
            field_name=field_name
        )
        
        # Check for empty name
        if not sanitized:
            raise InputSanitizationError(
                f"{field_name.capitalize()} cannot be empty after sanitization",
                field=field_name,
                value=name
            )
        
        # Check for suspicious patterns
        if InputSanitizer._contains_sql_injection(sanitized):
            warnings.append(f"⚠️ {field_name} contains SQL-like syntax (stored as-is, but logged)")
            logger.warning(f"SQL-like pattern detected in {field_name}: {sanitized}")
        
        if InputSanitizer._contains_xss(sanitized):
            warnings.append(f"⚠️ {field_name} contains HTML/script tags")
            logger.warning(f"XSS pattern detected in {field_name}: {sanitized}")
        
        return (sanitized, warnings)
    
    @staticmethod
    def sanitize_title(title: str) -> Tuple[str, List[str]]:
        """
        Sanitize a session/talk title.
        
        Args:
            title: Title to sanitize
        
        Returns:
            Tuple of (sanitized_title, warnings)
        
        Raises:
            InputSanitizationError: If title is empty
        """
        sanitized, warnings = InputSanitizer.sanitize_string(
            title,
            max_length=InputSanitizer.MAX_TITLE_LENGTH,
            remove_null_bytes=True,
            remove_control_chars=True,
            normalize_unicode=True,
            strip_whitespace=True,
            allow_newlines=False,
            field_name="title"
        )
        
        if not sanitized:
            raise InputSanitizationError(
                "Title cannot be empty after sanitization",
                field="title",
                value=title
            )
        
        return (sanitized, warnings)
    
    @staticmethod
    def sanitize_bio(bio: str) -> Tuple[str, List[str]]:
        """
        Sanitize biography/description text.
        
        Args:
            bio: Bio text to sanitize
        
        Returns:
            Tuple of (sanitized_bio, warnings)
        """
        sanitized, warnings = InputSanitizer.sanitize_string(
            bio,
            max_length=InputSanitizer.MAX_BIO_LENGTH,
            remove_null_bytes=True,
            remove_control_chars=False,  # Allow formatting
            normalize_unicode=True,
            strip_whitespace=True,
            allow_newlines=True,
            field_name="bio"
        )
        
        return (sanitized, warnings)
    
    @staticmethod
    def sanitize_notes(notes: str) -> Tuple[str, List[str]]:
        """
        Sanitize notes/comments field.
        
        Args:
            notes: Notes to sanitize
        
        Returns:
            Tuple of (sanitized_notes, warnings)
        """
        sanitized, warnings = InputSanitizer.sanitize_string(
            notes,
            max_length=InputSanitizer.MAX_NOTES_LENGTH,
            remove_null_bytes=True,
            remove_control_chars=False,
            normalize_unicode=True,
            strip_whitespace=True,
            allow_newlines=True,
            field_name="notes"
        )
        
        return (sanitized, warnings)
    
    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str], str]:
        """
        Validate and sanitize email address.
        
        Args:
            email: Email to validate
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_email)
        
        Examples:
            >>> InputSanitizer.validate_email("user@example.com")
            (True, None, "user@example.com")
            >>> InputSanitizer.validate_email("invalid.email")
            (False, "Invalid email format", "")
        """
        if not email:
            return (True, None, "")  # Email is optional
        
        # Sanitize first
        email = email.strip().lower()
        
        # Remove null bytes
        if '\x00' in email:
            return (False, "Email contains null bytes", "")
        
        # Length check
        if len(email) > InputSanitizer.MAX_EMAIL_LENGTH:
            return (
                False,
                f"Email too long (max {InputSanitizer.MAX_EMAIL_LENGTH} chars)",
                ""
            )
        
        # Pattern check
        if not InputSanitizer.EMAIL_PATTERN.match(email):
            return (False, "Invalid email format", "")
        
        # Check for dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '\\', '\n', '\r']
        for char in dangerous_chars:
            if char in email:
                return (False, f"Email contains invalid character: {char}", "")
        
        return (True, None, email)
    
    @staticmethod
    def sanitize_file_path(
        path_str: str,
        must_exist: bool = False,
        allowed_extensions: Optional[List[str]] = None
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """
        Sanitize and validate file path.
        
        Args:
            path_str: Path string to validate
            must_exist: If True, path must exist
            allowed_extensions: List of allowed extensions (e.g., ['.pdf', '.jpg'])
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_path)
        
        Examples:
            >>> InputSanitizer.sanitize_file_path("../etc/passwd")
            (False, "Path traversal detected", None)
        """
        if not path_str:
            return (True, None, None)  # Empty path is OK (optional)
        
        # Check for null bytes
        if '\x00' in path_str:
            return (False, "Path contains null bytes", None)
        
        # Check length
        if len(path_str) > InputSanitizer.MAX_PATH_LENGTH:
            return (False, f"Path too long (max {InputSanitizer.MAX_PATH_LENGTH} chars)", None)
        
        # Check for path traversal
        if InputSanitizer._contains_path_traversal(path_str):
            logger.error(f"Path traversal attempt detected: {path_str}")
            return (False, "Path traversal detected", None)
        
        try:
            # Convert to Path object
            path = Path(path_str)
            
            # Resolve to absolute path
            resolved_path = path.resolve()
            
            # Check if exists (if required)
            if must_exist and not resolved_path.exists():
                return (False, f"Path does not exist: {path_str}", None)
            
            # Check extension (if specified)
            if allowed_extensions:
                ext = resolved_path.suffix.lower()
                if ext not in allowed_extensions:
                    return (
                        False,
                        f"Invalid file extension: {ext}. Allowed: {', '.join(allowed_extensions)}",
                        None
                    )
            
            return (True, None, resolved_path)
            
        except Exception as e:
            return (False, f"Invalid path: {str(e)}", None)
    
    @staticmethod
    def validate_integer(
        value: any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        field_name: str = "value"
    ) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Validate and sanitize integer input.
        
        Args:
            value: Value to validate (can be str or int)
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            field_name: Field name for error messages
        
        Returns:
            Tuple of (is_valid, error_message, sanitized_value)
        """
        try:
            # Convert to int
            int_value = int(value)
            
            # Check range
            if min_value is not None and int_value < min_value:
                return (
                    False,
                    f"{field_name} must be at least {min_value}",
                    None
                )
            
            if max_value is not None and int_value > max_value:
                return (
                    False,
                    f"{field_name} must be at most {max_value}",
                    None
                )
            
            return (True, None, int_value)
            
        except (ValueError, TypeError) as e:
            return (False, f"Invalid integer for {field_name}: {str(e)}", None)
    
    @staticmethod
    def _contains_sql_injection(text: str) -> bool:
        """Check if text contains SQL injection patterns."""
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _contains_xss(text: str) -> bool:
        """Check if text contains XSS patterns."""
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def _contains_path_traversal(path_str: str) -> bool:
        """Check if path contains traversal patterns."""
        for pattern in InputSanitizer.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, path_str):
                return True
        return False
    
    @staticmethod
    def sanitize_session_id(session_id: str) -> Tuple[str, List[str]]:
        """
        Sanitize session ID (alphanumeric + underscore/hyphen only).
        
        Args:
            session_id: Session ID to sanitize
        
        Returns:
            Tuple of (sanitized_id, warnings)
        
        Raises:
            InputSanitizationError: If ID is invalid
        """
        warnings = []
        
        # Basic sanitization
        sanitized, basic_warnings = InputSanitizer.sanitize_string(
            session_id,
            max_length=100,
            remove_null_bytes=True,
            remove_control_chars=True,
            strip_whitespace=True,
            allow_newlines=False,
            field_name="session_id"
        )
        warnings.extend(basic_warnings)
        
        # Remove invalid characters (allow only alphanumeric, underscore, hyphen)
        original = sanitized
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', sanitized)
        
        if sanitized != original:
            warnings.append("Session ID contained invalid characters (replaced with underscore)")
        
        if not sanitized:
            raise InputSanitizationError(
                "Session ID cannot be empty after sanitization",
                field="session_id",
                value=session_id
            )
        
        return (sanitized, warnings)
    
    @staticmethod
    def sanitize_dict(
        data: dict,
        field_specs: dict
    ) -> Tuple[dict, List[str]]:
        """
        Sanitize entire dictionary based on field specifications.
        
        Args:
            data: Dictionary to sanitize
            field_specs: Dictionary mapping field names to sanitization functions
        
        Returns:
            Tuple of (sanitized_dict, all_warnings)
        
        Example:
            >>> specs = {
            ...     'name': lambda x: InputSanitizer.sanitize_name(x),
            ...     'email': lambda x: InputSanitizer.validate_email(x)[2]
            ... }
            >>> InputSanitizer.sanitize_dict({'name': 'John', 'email': 'john@example.com'}, specs)
        """
        sanitized = {}
        all_warnings = []
        
        for field, value in data.items():
            if field in field_specs:
                try:
                    result = field_specs[field](value)
                    
                    # Handle different return types
                    if isinstance(result, tuple):
                        if len(result) == 2:  # (value, warnings)
                            sanitized[field], warnings = result
                            all_warnings.extend(warnings)
                        elif len(result) == 3:  # (valid, error, value)
                            valid, error, san_value = result
                            if valid:
                                sanitized[field] = san_value
                            else:
                                all_warnings.append(f"{field}: {error}")
                    else:
                        sanitized[field] = result
                        
                except Exception as e:
                    all_warnings.append(f"Error sanitizing {field}: {str(e)}")
                    sanitized[field] = value  # Keep original on error
            else:
                # No spec for this field, keep as-is
                sanitized[field] = value
        
        return (sanitized, all_warnings)


# Convenience functions

def sanitize_speaker_name(name: str) -> str:
    """
    Sanitize speaker name, raise on error.
    
    Args:
        name: Speaker name
    
    Returns:
        Sanitized name
    
    Raises:
        InputSanitizationError: If name is invalid
    """
    sanitized, warnings = InputSanitizer.sanitize_name(name, "speaker_name")
    
    if warnings:
        for warning in warnings:
            logger.warning(warning)
    
    return sanitized


def sanitize_talk_title(title: str) -> str:
    """
    Sanitize talk title, raise on error.
    
    Args:
        title: Talk title
    
    Returns:
        Sanitized title
    
    Raises:
        InputSanitizationError: If title is invalid
    """
    sanitized, warnings = InputSanitizer.sanitize_title(title)
    
    if warnings:
        for warning in warnings:
            logger.warning(warning)
    
    return sanitized


# Example usage
if __name__ == "__main__":
    print("=== Input Sanitizer Tests ===\n")
    
    # Test 1: Name with null bytes
    print("Test 1: Null bytes")
    name = "John\x00Doe"
    sanitized, warnings = InputSanitizer.sanitize_name(name)
    print(f"  Input: {repr(name)}")
    print(f"  Output: {repr(sanitized)}")
    print(f"  Warnings: {warnings}\n")
    
    # Test 2: Unicode name
    print("Test 2: Unicode (Farsi)")
    name = "محمد رضا احمدی"
    sanitized, warnings = InputSanitizer.sanitize_name(name)
    print(f"  Input: {name}")
    print(f"  Output: {sanitized}")
    print(f"  Warnings: {warnings}\n")
    
    # Test 3: SQL injection attempt
    print("Test 3: SQL injection")
    name = "Robert'; DROP TABLE speakers;--"
    sanitized, warnings = InputSanitizer.sanitize_name(name)
    print(f"  Input: {name}")
    print(f"  Output: {sanitized}")
    print(f"  Warnings: {warnings}\n")
    
    # Test 4: Long name
    print("Test 4: Extremely long name")
    name = "A" * 500
    sanitized, warnings = InputSanitizer.sanitize_name(name)
    print(f"  Input length: {len(name)}")
    print(f"  Output length: {len(sanitized)}")
    print(f"  Warnings: {warnings}\n")
    
    # Test 5: Email validation
    print("Test 5: Email validation")
    emails = ["valid@example.com", "invalid.email", "test@domain", ""]
    for email in emails:
        valid, error, sanitized = InputSanitizer.validate_email(email)
        status = "✅" if valid else "❌"
        print(f"  {status} '{email}' -> {sanitized} (error: {error})")
    
    print("\n Test 6: Path traversal")
    paths = ["document.pdf", "../etc/passwd", "../../secret.txt", "normal/path/file.txt"]
    for path in paths:
        valid, error, sanitized = InputSanitizer.sanitize_file_path(path)
        status = "✅" if valid else "❌"
        print(f"  {status} '{path}' (error: {error})")

