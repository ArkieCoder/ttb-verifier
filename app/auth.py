"""
Session-based authentication for TTB Label Verifier UI.

Implements simple session management with secure cookies for prototype authentication.
For production, use AWS Cognito or a proper auth service.
"""

import secrets
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional
from fastapi import Request, HTTPException, status, Depends
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# In-memory session store
# Production: Use Redis or DynamoDB for persistence
sessions: Dict[str, Dict[str, any]] = {}

# Session configuration
SESSION_DURATION_HOURS = 4
SESSION_COOKIE_NAME = "session_id"

# Optional API key header for API access
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_session(username: str) -> str:
    """
    Create new session for authenticated user.
    
    Args:
        username: Username to associate with session
        
    Returns:
        Session ID (secure random token)
    """
    session_id = secrets.token_urlsafe(32)
    expires = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    
    sessions[session_id] = {
        "username": username,
        "expires": expires,
        "created_at": datetime.now()
    }
    
    logger.info(f"Created session for user: {username}, expires: {expires}")
    return session_id


def destroy_session(session_id: str) -> None:
    """
    Destroy session by ID.
    
    Args:
        session_id: Session ID to destroy
    """
    if session_id in sessions:
        username = sessions[session_id].get("username", "unknown")
        del sessions[session_id]
        logger.info(f"Destroyed session for user: {username}")


def get_session(session_id: Optional[str]) -> Optional[Dict[str, any]]:
    """
    Get session data by ID.
    
    Args:
        session_id: Session ID from cookie
        
    Returns:
        Session data dict or None if invalid/expired
    """
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    
    # Check expiration
    if datetime.now() > session["expires"]:
        logger.info(f"Session expired for user: {session.get('username')}")
        del sessions[session_id]
        return None
    
    return session


def get_current_user(request: Request) -> str:
    """
    Get username from session cookie.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Username from session
        
    Raises:
        HTTPException 401: If not authenticated or session expired
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = get_session(session_id)
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return session["username"]


async def get_current_user_optional(request: Request) -> Optional[str]:
    """
    Get username from session cookie, return None if not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Username from session or None
    """
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    session = get_session(session_id)
    
    if not session:
        return None
    
    return session["username"]


def verify_credentials(username: str, password: str) -> bool:
    """
    Verify username and password against Secrets Manager.
    
    Args:
        username: Username to verify
        password: Password to verify
        
    Returns:
        True if credentials are valid, False otherwise
    """
    try:
        from app.aws_secrets import get_ui_credentials
        
        valid_user, valid_pass = get_ui_credentials()
        is_valid = username == valid_user and password == valid_pass
        
        if is_valid:
            logger.info(f"Successful authentication for user: {username}")
        else:
            logger.warning(f"Failed authentication attempt for user: {username}")
        
        return is_valid
    
    except Exception as e:
        logger.error(f"Error verifying credentials: {e}")
        return False


def cleanup_expired_sessions() -> int:
    """
    Remove expired sessions from memory.
    
    Returns:
        Number of sessions removed
    """
    now = datetime.now()
    expired_sessions = [
        sid for sid, session in sessions.items()
        if now > session["expires"]
    ]
    
    for sid in expired_sessions:
        del sessions[sid]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    return len(expired_sessions)


def get_session_stats() -> Dict[str, int]:
    """
    Get session statistics for monitoring.
    
    Returns:
        Dict with active session count and other stats
    """
    cleanup_expired_sessions()
    
    return {
        "active_sessions": len(sessions),
        "oldest_session_age_seconds": min(
            [(datetime.now() - s["created_at"]).total_seconds() for s in sessions.values()],
            default=0
        )
    }
