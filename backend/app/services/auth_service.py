"""
User authentication database service
Handles user registration, login, session management
"""
import sqlite3
import logging
import secrets
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from hashlib import sha256
import bcrypt

logger = logging.getLogger(__name__)

# Database path - same directory as contracts.db
DB_PATH = os.path.join(os.path.dirname(__file__), "../../data/contracts.db")


def _get_connection() -> sqlite3.Connection:
    """Get database connection with row factory"""
    db_file = Path(DB_PATH)
    db_file.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_file))
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_legacy_sha256(password: str, password_hash: str) -> bool:
    """Verify against legacy SHA-256+salt format (salt:hash)"""
    try:
        salt, stored_hash = password_hash.split(":")
        return sha256(f"{salt}{password}".encode()).hexdigest() == stored_hash
    except (ValueError, AttributeError):
        return False


def _is_bcrypt_hash(password_hash: str) -> bool:
    return password_hash.startswith("$2b$") or password_hash.startswith("$2a$")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt or legacy SHA-256 hash"""
    if _is_bcrypt_hash(password_hash):
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    return _verify_legacy_sha256(password, password_hash)


def init_auth_tables():
    """Create auth-related tables if they don't exist"""
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        # First, ensure the users table exists at all
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                name TEXT DEFAULT '',
                password_hash TEXT DEFAULT '',
                full_name TEXT DEFAULT '',
                organization TEXT DEFAULT '',
                role TEXT DEFAULT 'user',
                last_login TEXT DEFAULT NULL,
                is_active INTEGER DEFAULT 1,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Upgrade existing users table: add columns if missing
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {row["name"] for row in cursor.fetchall()}

        new_columns = {
            "password_hash": "TEXT DEFAULT ''",
            "full_name": "TEXT DEFAULT ''",
            "organization": "TEXT DEFAULT ''",
            "role": "TEXT DEFAULT 'user'",
            "last_login": "TEXT DEFAULT NULL",
            "is_active": "INTEGER DEFAULT 1",
        }

        for col_name, col_def in new_columns.items():
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    logger.info(f"Added {col_name} column to users table")
                except Exception:
                    pass  # Column might already exist via CREATE TABLE above

        # Create sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_token
            ON sessions(token)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sessions_user_id
            ON sessions(user_id)
        """)

        conn.commit()

        # Create demo user if no users with passwords exist
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE password_hash != '' AND password_hash IS NOT NULL")
        if cursor.fetchone()["count"] == 0:
            _create_demo_user(conn)

        logger.info("Auth tables initialized successfully")

    except Exception as e:
        logger.error(f"Error initializing auth tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def _create_demo_user(conn: sqlite3.Connection):
    """Create a demo user for testing"""
    cursor = conn.cursor()
    demo_id = "demo_user"
    now = datetime.utcnow().isoformat()

    # Check if demo user already exists
    cursor.execute("SELECT id FROM users WHERE id = ? OR email = ?", (demo_id, "demo@lexra.ai"))
    existing = cursor.fetchone()

    if existing:
        # Update existing demo user with password
        cursor.execute("""
            UPDATE users SET 
                password_hash = ?,
                full_name = ?,
                organization = ?,
                role = ?
            WHERE id = ? OR email = ?
        """, (
            hash_password("demo123"),
            "Demo User",
            "Lexra Demo",
            "admin",
            demo_id,
            "demo@lexra.ai"
        ))
    else:
        # Insert new demo user
        cursor.execute("""
            INSERT INTO users (id, email, name, created_date, password_hash, full_name, organization, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            demo_id,
            "demo@lexra.ai",
            "Demo User",
            now,
            hash_password("demo123"),
            "Demo User",
            "Lexra Demo",
            "admin",
            1
        ))

    conn.commit()
    logger.info("Demo user created/updated: demo@lexra.ai / demo123")


def create_user(email: str, password: str, full_name: str, organization: str = "") -> Optional[Dict[str, Any]]:
    """
    Register a new user.
    Returns user dict on success, None if email already exists.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        user_id = secrets.token_hex(12)
        now = datetime.utcnow().isoformat()

        cursor.execute("""
            INSERT INTO users (id, email, name, created_date, password_hash, full_name, organization, role, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            email.lower().strip(),
            full_name.strip(),
            now,
            hash_password(password),
            full_name.strip(),
            organization.strip(),
            "user",
            1
        ))
        conn.commit()

        logger.info(f"New user registered: {email}")
        return {
            "id": user_id,
            "email": email.lower().strip(),
            "full_name": full_name.strip(),
            "name": full_name.strip(),
            "organization": organization.strip(),
            "role": "user"
        }
    except sqlite3.IntegrityError:
        logger.warning(f"Registration failed - email already exists: {email}")
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate user by email and password.
    Returns user dict on success, None on failure.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM users WHERE email = ? AND is_active = 1",
            (email.lower().strip(),)
        )
        user = cursor.fetchone()

        if user and user["password_hash"] and verify_password(password, user["password_hash"]):
            # Migrate legacy SHA-256 hash to bcrypt transparently on login
            if not _is_bcrypt_hash(user["password_hash"]):
                cursor.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (hash_password(password), user["id"])
                )
                logger.info(f"Migrated password hash to bcrypt for user: {user['email']}")
            # Update last login timestamp
            cursor.execute(
                "UPDATE users SET last_login = ? WHERE id = ?",
                (datetime.utcnow().isoformat(), user["id"])
            )
            conn.commit()

            return {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"] or user["name"] or "",
                "name": user["full_name"] or user["name"] or "",
                "organization": user["organization"] or "",
                "role": user["role"] or "user"
            }

        return None
    finally:
        conn.close()


def create_session(user_id: str, hours: int = 24) -> str:
    """Create a session token for the user. Returns token string."""
    conn = _get_connection()
    cursor = conn.cursor()

    token = secrets.token_urlsafe(48)
    expires_at = (datetime.utcnow() + timedelta(hours=hours)).isoformat()

    cursor.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at)
    )
    conn.commit()
    conn.close()

    return token


def validate_session(token: str) -> Optional[Dict[str, Any]]:
    """
    Validate a session token.
    Returns user dict if valid, None if expired/invalid.
    """
    conn = _get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.name, u.organization, u.role, s.expires_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ? AND u.is_active = 1
        """, (token,))

        result = cursor.fetchone()

        if result:
            expires_at = datetime.fromisoformat(result["expires_at"])
            if expires_at > datetime.utcnow():
                return {
                    "id": result["id"],
                    "email": result["email"],
                    "full_name": result["full_name"] or result["name"] or "",
                    "name": result["full_name"] or result["name"] or "",
                    "organization": result["organization"] or "",
                    "role": result["role"] or "user"
                }
            else:
                # Clean up expired session
                cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()

        return None
    finally:
        conn.close()


def delete_session(token: str):
    """Delete a session (logout)"""
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def update_user(user_id: str, full_name: str = None, organization: str = None) -> Optional[Dict[str, Any]]:
    """Update user profile fields. Returns updated user dict or None."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        updates = []
        params = []
        if full_name is not None:
            updates.append("full_name = ?")
            updates.append("name = ?")
            params.extend([full_name.strip(), full_name.strip()])
        if organization is not None:
            updates.append("organization = ?")
            params.append(organization.strip())
        if not updates:
            return None
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "email": row["email"],
            "full_name": row["full_name"] or row["name"] or "",
            "name": row["full_name"] or row["name"] or "",
            "organization": row["organization"] or "",
            "role": row["role"] or "user",
        }
    finally:
        conn.close()


def change_user_password(user_id: str, current_password: str, new_password: str) -> bool:
    """Change user password. Returns True on success."""
    conn = _get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row or not verify_password(current_password, row["password_hash"]):
            return False
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(new_password), user_id))
        conn.commit()
        return True
    finally:
        conn.close()


def cleanup_expired_sessions():
    """Remove all expired sessions"""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()
    cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted > 0:
        logger.info(f"Cleaned up {deleted} expired sessions")
