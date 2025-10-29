"""
Session Token Management
========================
Provides secure session token generation and validation.
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from database import get_connection

logger = logging.getLogger(__name__)

# Session configuration
SESSION_LIFETIME_HOURS = 24
SESSION_INACTIVITY_TIMEOUT_HOURS = 2


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def create_session(user_id: int) -> str:
    """
    Create a new session for a user.

    Args:
        user_id: User ID

    Returns:
        Session token string
    """
    token = generate_session_token()
    now = datetime.now()
    expires_at = now + timedelta(hours=SESSION_LIFETIME_HOURS)

    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Clean up old sessions for this user
            cursor.execute('''
                DELETE FROM session_tokens
                WHERE user_id = ? AND expires_at < ?
            ''', (user_id, now.isoformat()))

            # Create new session
            cursor.execute('''
                INSERT INTO session_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            ''', (user_id, token, expires_at.isoformat()))

            conn.commit()
            logger.info(f"Session created for user {user_id}")
            return token

    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise


def validate_session(token: str) -> Optional[int]:
    """
    Validate a session token and return user_id if valid.

    Args:
        token: Session token to validate

    Returns:
        User ID if valid, None otherwise
    """
    if not token:
        return None

    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                SELECT user_id, last_activity, expires_at
                FROM session_tokens
                WHERE token = ?
            ''', (token,))

            row = cursor.fetchone()

            if not row:
                return None

            user_id = row['user_id']
            last_activity = datetime.fromisoformat(row['last_activity'])
            expires_at = datetime.fromisoformat(row['expires_at'])

            # Check if session expired
            if now > expires_at:
                logger.info(f"Session expired for user {user_id}")
                delete_session(token)
                return None

            # Check if session inactive too long
            inactivity_timeout = timedelta(hours=SESSION_INACTIVITY_TIMEOUT_HOURS)
            if now - last_activity > inactivity_timeout:
                logger.info(f"Session inactive too long for user {user_id}")
                delete_session(token)
                return None

            # Update last activity
            cursor.execute('''
                UPDATE session_tokens
                SET last_activity = ?
                WHERE token = ?
            ''', (now.isoformat(), token))

            conn.commit()
            return user_id

    except Exception as e:
        logger.error(f"Error validating session: {e}")
        return None


def delete_session(token: str):
    """
    Delete a session token (logout).

    Args:
        token: Session token to delete
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM session_tokens
                WHERE token = ?
            ''', (token,))

            conn.commit()
            logger.info("Session deleted")

    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        raise


def delete_user_sessions(user_id: int):
    """
    Delete all sessions for a user.

    Args:
        user_id: User ID
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                DELETE FROM session_tokens
                WHERE user_id = ?
            ''', (user_id,))

            conn.commit()
            logger.info(f"All sessions deleted for user {user_id}")

    except Exception as e:
        logger.error(f"Error deleting user sessions: {e}")
        raise


def cleanup_expired_sessions():
    """
    Clean up all expired sessions from database.
    Should be run periodically.
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()

            cursor.execute('''
                DELETE FROM session_tokens
                WHERE expires_at < ?
            ''', (now.isoformat(),))

            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} expired sessions")

    except Exception as e:
        logger.error(f"Error cleaning up sessions: {e}")
