"""
Middleware for TTB Label Verifier.

Implements host checking to restrict access to authorized domains only.
"""

import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse

logger = logging.getLogger(__name__)


class HostCheckMiddleware(BaseHTTPMiddleware):
    """
    Middleware to restrict access based on Host header.
    
    Only allows requests from authorized hostnames.
    Always allows /health endpoint for ALB health checks.
    """
    
    def __init__(self, app, allowed_hosts: list[str]):
        super().__init__(app)
        self.allowed_hosts = allowed_hosts
        logger.info(f"HostCheckMiddleware initialized with allowed hosts: {allowed_hosts}")
    
    async def dispatch(self, request: Request, call_next):
        """Process request and check Host header."""
        
        # Always allow health checks (needed for ALB health checks from any IP)
        if request.url.path == "/health":
            return await call_next(request)
        
        # Get host from header
        host = request.headers.get("host", "")
        
        # Remove port if present (e.g., "example.com:443" -> "example.com")
        host_without_port = host.split(":")[0]
        
        # Check if host is allowed
        if host_without_port in self.allowed_hosts:
            logger.debug(f"Allowed access from host: {host_without_port}")
            return await call_next(request)
        
        # Reject with 403
        logger.warning(f"Blocked access from unauthorized host: {host_without_port}")
        
        return HTMLResponse(
            content="""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>403 Forbidden</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }
        .error-container {
            text-align: center;
            padding: 40px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            max-width: 500px;
        }
        h1 {
            color: #dc3545;
            margin-bottom: 20px;
        }
        p {
            color: #666;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="error-container">
        <h1>403 Forbidden</h1>
        <p>Access denied. This service is only accessible via the authorized domain.</p>
        <p>Please use the official domain to access this service.</p>
    </div>
</body>
</html>
            """,
            status_code=403
        )
