"""
Authentication & Authorization System

Secure authentication and role-based access control.

Features:
- Password hashing (bcrypt)
- Role-based access control (RBAC)
- Session management
- Login attempts tracking
- PIN/Password support

Author: AI-Symp-Controller Team
Date: November 2025
Version: 1.0
"""

import hashlib
import secrets
import time
import logging
from typing import Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class UserRole(Enum):
    """User roles with permissions."""
    ADMIN = "admin"  # Full access
    OPERATOR = "operator"  # Normal operations
    VIEWER = "viewer"  # Read-only


@dataclass
class User:
    """User data."""
    username: str
    password_hash: str
    role: UserRole
    created_at: float
    last_login: Optional[float] = None
    is_active: bool = True


@dataclass
class Session:
    """User session."""
    session_id: str
    username: str
    role: UserRole
    created_at: float
    last_activity: float
    ip_address: Optional[str] = None


class PasswordHasher:
    """
    Password hashing utilities using PBKDF2.
    """
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> str:
        """
        Hash password with salt.
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
        
        Returns:
            Hash in format: salt$hash
        """
        if salt is None:
            salt = secrets.token_bytes(32)
        
        # PBKDF2 with 100,000 iterations
        hash_bytes = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        # Store as: salt$hash (hex encoded)
        return f"{salt.hex()}${hash_bytes.hex()}"
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            password: Plain text password
            password_hash: Stored hash (salt$hash)
        
        Returns:
            True if password matches
        """
        try:
            salt_hex, hash_hex = password_hash.split('$')
            salt = bytes.fromhex(salt_hex)
            
            # Hash provided password with same salt
            new_hash = PasswordHasher.hash_password(password, salt)
            
            # Compare
            return secrets.compare_digest(new_hash, password_hash)
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False


class LoginAttemptTracker:
    """
    Tracks failed login attempts to prevent brute force.
    """
    
    def __init__(self, max_attempts: int = 5, lockout_duration: float = 300.0):
        """
        Initialize tracker.
        
        Args:
            max_attempts: Max failed attempts before lockout
            lockout_duration: Lockout duration in seconds
        """
        self._attempts: Dict[str, List[float]] = {}
        self._max_attempts = max_attempts
        self._lockout_duration = lockout_duration
    
    def record_attempt(self, username: str, success: bool):
        """
        Record login attempt.
        
        Args:
            username: Username
            success: True if successful
        """
        if success:
            # Clear attempts on success
            if username in self._attempts:
                del self._attempts[username]
        else:
            # Record failed attempt
            if username not in self._attempts:
                self._attempts[username] = []
            
            self._attempts[username].append(time.time())
            
            # Clean old attempts
            cutoff = time.time() - self._lockout_duration
            self._attempts[username] = [
                t for t in self._attempts[username] if t > cutoff
            ]
    
    def is_locked_out(self, username: str) -> bool:
        """
        Check if user is locked out.
        
        Args:
            username: Username
        
        Returns:
            True if locked out
        """
        if username not in self._attempts:
            return False
        
        # Clean old attempts
        cutoff = time.time() - self._lockout_duration
        self._attempts[username] = [
            t for t in self._attempts[username] if t > cutoff
        ]
        
        return len(self._attempts[username]) >= self._max_attempts
    
    def get_remaining_attempts(self, username: str) -> int:
        """Get remaining login attempts."""
        if username not in self._attempts:
            return self._max_attempts
        
        return max(0, self._max_attempts - len(self._attempts[username]))


class AuthenticationManager:
    """
    Main authentication manager.
    """
    
    def __init__(self, users_file: str = "users.json"):
        """
        Initialize authentication manager.
        
        Args:
            users_file: Path to users database file
        """
        self._users_file = Path(users_file)
        self._users: Dict[str, User] = {}
        self._sessions: Dict[str, Session] = {}
        self._attempt_tracker = LoginAttemptTracker()
        
        # Load users
        self._load_users()
        
        # Create default admin if no users exist
        if not self._users:
            self._create_default_admin()
        
        logger.info(f"AuthenticationManager initialized ({len(self._users)} users)")
    
    def _load_users(self):
        """Load users from file."""
        if not self._users_file.exists():
            logger.info("No users file found, starting fresh")
            return
        
        try:
            with open(self._users_file, 'r') as f:
                data = json.load(f)
            
            for username, user_data in data.items():
                self._users[username] = User(
                    username=username,
                    password_hash=user_data['password_hash'],
                    role=UserRole(user_data['role']),
                    created_at=user_data['created_at'],
                    last_login=user_data.get('last_login'),
                    is_active=user_data.get('is_active', True)
                )
            
            logger.info(f"Loaded {len(self._users)} users")
        except Exception as e:
            logger.error(f"Error loading users: {e}")
    
    def _save_users(self):
        """Save users to file."""
        try:
            data = {}
            for username, user in self._users.items():
                data[username] = {
                    'password_hash': user.password_hash,
                    'role': user.role.value,
                    'created_at': user.created_at,
                    'last_login': user.last_login,
                    'is_active': user.is_active
                }
            
            with open(self._users_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Users saved")
        except Exception as e:
            logger.error(f"Error saving users: {e}")
    
    def _create_default_admin(self):
        """Create default admin user."""
        logger.warning("Creating default admin user")
        
        self.create_user(
            username="admin",
            password="admin123",  # CHANGE IN PRODUCTION!
            role=UserRole.ADMIN
        )
        
        logger.warning("⚠️ DEFAULT ADMIN CREATED - CHANGE PASSWORD IMMEDIATELY!")
    
    def create_user(
        self,
        username: str,
        password: str,
        role: UserRole
    ) -> bool:
        """
        Create new user.
        
        Args:
            username: Username
            password: Password
            role: User role
        
        Returns:
            True if created successfully
        """
        if username in self._users:
            logger.error(f"User already exists: {username}")
            return False
        
        # Hash password
        password_hash = PasswordHasher.hash_password(password)
        
        # Create user
        user = User(
            username=username,
            password_hash=password_hash,
            role=role,
            created_at=time.time()
        )
        
        self._users[username] = user
        self._save_users()
        
        logger.info(f"User created: {username} (role: {role.value})")
        return True
    
    def login(self, username: str, password: str) -> Optional[str]:
        """
        Login user.
        
        Args:
            username: Username
            password: Password
        
        Returns:
            Session ID if successful, None otherwise
        """
        # Check lockout
        if self._attempt_tracker.is_locked_out(username):
            remaining = self._attempt_tracker.get_remaining_attempts(username)
            logger.warning(f"Login blocked (locked out): {username}")
            return None
        
        # Check user exists
        if username not in self._users:
            self._attempt_tracker.record_attempt(username, False)
            logger.warning(f"Login failed (user not found): {username}")
            return None
        
        user = self._users[username]
        
        # Check active
        if not user.is_active:
            logger.warning(f"Login failed (user inactive): {username}")
            return None
        
        # Verify password
        if not PasswordHasher.verify_password(password, user.password_hash):
            self._attempt_tracker.record_attempt(username, False)
            remaining = self._attempt_tracker.get_remaining_attempts(username)
            logger.warning(f"Login failed (wrong password): {username} ({remaining} attempts left)")
            return None
        
        # Success!
        self._attempt_tracker.record_attempt(username, True)
        
        # Update last login
        user.last_login = time.time()
        self._save_users()
        
        # Create session
        session_id = secrets.token_urlsafe(32)
        session = Session(
            session_id=session_id,
            username=username,
            role=user.role,
            created_at=time.time(),
            last_activity=time.time()
        )
        
        self._sessions[session_id] = session
        
        logger.info(f"✅ Login successful: {username} (role: {user.role.value})")
        return session_id
    
    def logout(self, session_id: str):
        """Logout (invalidate session)."""
        if session_id in self._sessions:
            username = self._sessions[session_id].username
            del self._sessions[session_id]
            logger.info(f"Logout: {username}")
    
    def validate_session(self, session_id: str, max_idle: float = 3600.0) -> Optional[Session]:
        """
        Validate session.
        
        Args:
            session_id: Session ID
            max_idle: Max idle time (seconds)
        
        Returns:
            Session if valid, None otherwise
        """
        if session_id not in self._sessions:
            return None
        
        session = self._sessions[session_id]
        
        # Check idle time
        idle_time = time.time() - session.last_activity
        if idle_time > max_idle:
            logger.info(f"Session expired (idle): {session.username}")
            del self._sessions[session_id]
            return None
        
        # Update activity
        session.last_activity = time.time()
        
        return session
    
    def has_permission(self, session_id: str, required_role: UserRole) -> bool:
        """
        Check if session has required permission.
        
        Args:
            session_id: Session ID
            required_role: Required role
        
        Returns:
            True if has permission
        """
        session = self.validate_session(session_id)
        if not session:
            return False
        
        # Admin has all permissions
        if session.role == UserRole.ADMIN:
            return True
        
        # Check role
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.OPERATOR: 2,
            UserRole.VIEWER: 1
        }
        
        return role_hierarchy.get(session.role, 0) >= role_hierarchy.get(required_role, 999)
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password."""
        if username not in self._users:
            return False
        
        user = self._users[username]
        
        # Verify old password
        if not PasswordHasher.verify_password(old_password, user.password_hash):
            logger.warning(f"Password change failed (wrong old password): {username}")
            return False
        
        # Set new password
        user.password_hash = PasswordHasher.hash_password(new_password)
        self._save_users()
        
        logger.info(f"Password changed: {username}")
        return True


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    print("=== Authentication System Test ===\n")
    
    # Create manager
    auth = AuthenticationManager("test_users.json")
    
    # Create users
    auth.create_user("operator1", "pass123", UserRole.OPERATOR)
    auth.create_user("viewer1", "view123", UserRole.VIEWER)
    
    # Login
    print("\n1. Login as admin")
    session = auth.login("admin", "admin123")
    print(f"Session: {session}")
    
    print("\n2. Validate session")
    valid_session = auth.validate_session(session)
    print(f"Valid: {valid_session is not None}")
    
    print("\n3. Check permissions")
    print(f"Has OPERATOR permission: {auth.has_permission(session, UserRole.OPERATOR)}")
    
    print("\n4. Wrong password")
    bad_session = auth.login("admin", "wrong")
    print(f"Session: {bad_session}")
    
    print("\n5. Change password")
    success = auth.change_password("admin", "admin123", "new_password")
    print(f"Success: {success}")
    
    # Cleanup
    Path("test_users.json").unlink(missing_ok=True)

