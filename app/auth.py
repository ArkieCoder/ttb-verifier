"""
Session-based authentication for TTB Label Verifier UI.

Uses signed cookies for stateless authentication that works with multiple workers.
For production, consider AWS Cognito or a proper auth service.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException, status, Depends, Response
from fastapi.security import APIKeyHeader
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import os

logger = logging.getLogger(__name__)

# Session configuration
SESSION_DURATION_HOURS = 4
SESSION_COOKIE_NAME = "session_id"

# Secret key for signing cookies (from environment or generate)
# In production, this should come from AWS Secrets Manager
SECRET_KEY = os.getenv("SESSION_SECRET_KEY", "dev-secret-key-change-in-production")
serializer = URLSafeTimedSerializer(SECRET_KEY)

# Optional API key header for API access
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def create_session_cookie(username: str) -> str:
    """
    Create signed session cookie for authenticated user.
    
    Args:
        username: Username to associate with session
        
    Returns:
        Signed cookie value containing username and expiry
    """
    session_data = {
        "username": username,
        "created_at": datetime.now().isoformat()
    }
    
    # Create signed token (expires after SESSION_DURATION_HOURS)
    token = serializer.dumps(session_data)
    
    expires = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    logger.info(f"Created session for user: {username}, expires: {expires}")
    return token


def verify_session_cookie(cookie_value: Optional[str]) -> Optional[str]:
    """
    Verify and decode signed session cookie.
    
    Args:
        cookie_value: Signed cookie value
        
    Returns:
        Username if valid, None if invalid/expired
    """
    if not cookie_value:
        return None
    
    try:
        # Verify signature and check expiry (max_age in seconds)
        max_age = SESSION_DURATION_HOURS * 3600
        session_data = serializer.loads(cookie_value, max_age=max_age)
        return session_data.get("username")
    except SignatureExpired:
        logger.info("Session expired")
        return None
    except BadSignature:
        logger.warning("Invalid session signature")
        return None
    except Exception as e:
        logger.error(f"Error verifying session: {e}")
        return None


def get_current_user(request: Request) -> str:
    """
    Get username from signed session cookie.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Username from session
        
    Raises:
        HTTPException 401: If not authenticated or session expired
    """
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    username = verify_session_cookie(cookie_value)
    
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    return username


class UnauthenticatedError(Exception):
    """Custom exception for unauthenticated UI access that needs redirect."""
    pass


def get_current_user_ui(request: Request) -> str:
    """
    Get username from signed session cookie for UI routes.
    
    Raises UnauthenticatedError if not authenticated (caught by exception handler).
    
    Args:
        request: FastAPI request object
        
    Returns:
        Username from session
        
    Raises:
        UnauthenticatedError: If not authenticated or session expired
    """
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    username = verify_session_cookie(cookie_value)
    
    if not username:
        raise UnauthenticatedError("User not authenticated")
    
    return username


async def get_current_user_optional(request: Request) -> Optional[str]:
    """
    Get username from signed session cookie, return None if not authenticated.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Username from session or None
    """
    cookie_value = request.cookies.get(SESSION_COOKIE_NAME)
    return verify_session_cookie(cookie_value)


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
        from aws_secrets import get_ui_credentials
        
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
    
    NOTE: With signed cookies, this is a no-op since sessions are stateless.
    Kept for backward compatibility.
    
    Returns:
        Always returns 0
    """
    return 0


def get_session_stats() -> dict:
    """
    Get session statistics for monitoring.
    
    NOTE: With signed cookies, we can't track active sessions.
    Returns placeholder data for backward compatibility.
    
    Returns:
        Dict with placeholder stats
    """
    return {
        "active_sessions": 0,
        "session_type": "signed_cookies",
        "note": "Stateless authentication - cannot track active session count"
    }
