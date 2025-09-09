"""
VAPI Webhook Security Module

Provides authentication and verification for VAPI webhook calls.
"""

import hmac
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, Request, Header
from functools import wraps
import structlog

logger = structlog.get_logger(__name__)


class VAPIWebhookSecurity:
    """Security handler for VAPI webhooks."""
    
    def __init__(self, webhook_secret: Optional[str] = None, 
                 api_keys: Optional[list] = None,
                 allowed_ips: Optional[list] = None):
        """
        Initialize security handler.
        
        Args:
            webhook_secret: VAPI webhook secret for signature verification
            api_keys: List of valid API keys
            allowed_ips: List of allowed IP addresses
        """
        self.webhook_secret = webhook_secret
        self.api_keys = set(api_keys) if api_keys else None
        self.allowed_ips = set(allowed_ips) if allowed_ips else None
        self.request_cache = {}  # For replay attack prevention
        self.max_cache_age = timedelta(minutes=5)
    
    def verify_webhook_signature(self, request_body: bytes, signature: str) -> bool:
        """
        Verify VAPI webhook signature.
        
        VAPI signs webhooks using HMAC-SHA256 with your webhook secret.
        """
        if not self.webhook_secret:
            return True  # Skip if no secret configured
        
        try:
            # Calculate expected signature
            expected_sig = hmac.new(
                self.webhook_secret.encode(),
                request_body,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures (constant time comparison)
            return hmac.compare_digest(expected_sig, signature)
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False
    
    def verify_api_key(self, api_key: Optional[str]) -> bool:
        """Verify API key if configured."""
        if not self.api_keys:
            return True  # Skip if no API keys configured
        
        return api_key in self.api_keys
    
    def verify_ip_whitelist(self, client_ip: str) -> bool:
        """Verify client IP against whitelist."""
        if not self.allowed_ips:
            return True  # Skip if no IP whitelist configured
        
        return client_ip in self.allowed_ips
    
    def check_replay_attack(self, request_id: str) -> bool:
        """
        Check for replay attacks using request ID.
        
        Returns True if this is a new request, False if it's a replay.
        """
        # Clean old entries
        now = datetime.now()
        expired = [
            rid for rid, timestamp in self.request_cache.items()
            if now - timestamp > self.max_cache_age
        ]
        for rid in expired:
            del self.request_cache[rid]
        
        # Check if we've seen this request
        if request_id in self.request_cache:
            logger.warning(f"Replay attack detected: {request_id}")
            return False
        
        # Cache this request
        self.request_cache[request_id] = now
        return True
    
    async def verify_webhook_request(self, request: Request, 
                                    signature: Optional[str] = None,
                                    api_key: Optional[str] = None) -> bool:
        """
        Comprehensive webhook request verification.
        
        Checks:
        1. Webhook signature (if configured)
        2. API key (if configured)
        3. IP whitelist (if configured)
        4. Replay attack prevention
        """
        try:
            # Get request body
            body = await request.body()
            
            # 1. Verify signature
            if self.webhook_secret and signature:
                if not self.verify_webhook_signature(body, signature):
                    logger.warning("Invalid webhook signature")
                    raise HTTPException(status_code=401, detail="Invalid signature")
            
            # 2. Verify API key
            if not self.verify_api_key(api_key):
                logger.warning("Invalid API key")
                raise HTTPException(status_code=401, detail="Invalid API key")
            
            # 3. Verify IP
            client_ip = request.client.host
            if not self.verify_ip_whitelist(client_ip):
                logger.warning(f"Unauthorized IP: {client_ip}")
                raise HTTPException(status_code=403, detail="IP not authorized")
            
            # 4. Check for replay attack
            try:
                data = json.loads(body)
                request_id = data.get("call", {}).get("id", "")
                if request_id and not self.check_replay_attack(request_id):
                    raise HTTPException(status_code=409, detail="Duplicate request")
            except json.JSONDecodeError:
                pass  # Can't check replay without valid JSON
            
            return True
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Security verification failed: {e}")
            raise HTTPException(status_code=500, detail="Security verification failed")


class RateLimiter:
    """Simple rate limiter for webhook endpoints."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.request_counts = {}
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if identifier has exceeded rate limit.
        
        Returns True if under limit, False if exceeded.
        """
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        # Clean old entries
        if identifier in self.request_counts:
            self.request_counts[identifier] = [
                timestamp for timestamp in self.request_counts[identifier]
                if timestamp > window_start
            ]
        else:
            self.request_counts[identifier] = []
        
        # Check limit
        if len(self.request_counts[identifier]) >= self.max_requests:
            return False
        
        # Add this request
        self.request_counts[identifier].append(now)
        return True


# Security configuration from environment
def get_security_config() -> Dict[str, Any]:
    """Get security configuration from environment variables."""
    import os
    
    return {
        "webhook_secret": os.getenv("VAPI_WEBHOOK_SECRET"),
        "api_keys": os.getenv("VAPI_API_KEYS", "").split(",") if os.getenv("VAPI_API_KEYS") else None,
        "allowed_ips": os.getenv("VAPI_ALLOWED_IPS", "").split(",") if os.getenv("VAPI_ALLOWED_IPS") else None,
        "rate_limit_enabled": os.getenv("VAPI_RATE_LIMIT", "true").lower() == "true",
        "max_requests_per_minute": int(os.getenv("VAPI_MAX_REQUESTS", "100"))
    }


# Global instances
_security_handler = None
_rate_limiter = None


def init_security():
    """Initialize security components."""
    global _security_handler, _rate_limiter
    
    config = get_security_config()
    
    _security_handler = VAPIWebhookSecurity(
        webhook_secret=config["webhook_secret"],
        api_keys=config["api_keys"],
        allowed_ips=config["allowed_ips"]
    )
    
    if config["rate_limit_enabled"]:
        _rate_limiter = RateLimiter(
            max_requests=config["max_requests_per_minute"],
            window_seconds=60
        )
    
    logger.info("VAPI security initialized", 
               has_secret=bool(config["webhook_secret"]),
               has_api_keys=bool(config["api_keys"]),
               has_ip_whitelist=bool(config["allowed_ips"]),
               rate_limiting=config["rate_limit_enabled"])


async def verify_vapi_request(request: Request,
                             x_vapi_signature: Optional[str] = Header(None),
                             x_api_key: Optional[str] = Header(None)):
    """
    FastAPI dependency for VAPI webhook verification.
    
    Usage:
        @router.post("/webhook", dependencies=[Depends(verify_vapi_request)])
        async def webhook_handler(request: Request):
            ...
    """
    global _security_handler, _rate_limiter
    
    if not _security_handler:
        init_security()
    
    # Rate limiting
    if _rate_limiter:
        client_id = request.client.host
        if not _rate_limiter.check_rate_limit(client_id):
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Security verification
    if _security_handler:
        await _security_handler.verify_webhook_request(
            request=request,
            signature=x_vapi_signature,
            api_key=x_api_key
        )
    
    return True