import logging
import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()


def validate_api_key_security():
    """Validate API key meets security requirements"""
    api_key = os.getenv("HAPPYROBOT_API_KEY", "happyrobot-api-key-change-in-production")
    min_length = 32
    
    if len(api_key) < min_length:
        logger.warning(f"API key is too short ({len(api_key)} chars). Minimum: {min_length}")
        return False
    
    if api_key in ["happyrobot-api-key-change-in-production", "test-key", "demo-key"]:
        logger.warning("Using default/weak API key. Change for production!")
        return False
    
    return True


def verify_api_key(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify API key authentication"""
    api_key = os.getenv("HAPPYROBOT_API_KEY", "happyrobot-api-key-change-in-production")
    if credentials.credentials != api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


# Check security on startup
def check_security_configuration():
    """Check and warn about security configuration"""
    issues = []
    
    if not validate_api_key_security():
        issues.append("API key security")
    
    require_https = os.getenv("REQUIRE_HTTPS", "false").lower() == "true"
    api_key = os.getenv("HAPPYROBOT_API_KEY", "happyrobot-api-key-change-in-production")
    if not require_https and api_key != "happyrobot-test-key-123456":
        issues.append("HTTPS not required")
    
    if issues:
        logger.warning(f"Security issues detected: {', '.join(issues)}")
    
    logger.info("For production: Use strong API keys (32+ chars) and enable HTTPS") 