"""
Firebase Authentication for VENDORA FastAPI Application
Implements JWT token verification and user management
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json

import firebase_admin
from firebase_admin import credentials, auth as firebase_auth
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import requests
from jose import jwt, JWTError
from pydantic import BaseModel

# Configure logging
logger = logging.getLogger(__name__)

# Security scheme for FastAPI documentation
security = HTTPBearer()


class FirebaseUser(BaseModel):
    """Represents a verified Firebase user"""
    uid: str
    email: Optional[str] = None
    email_verified: bool = False
    display_name: Optional[str] = None
    phone_number: Optional[str] = None
    custom_claims: Dict[str, Any] = {}
    dealership_id: Optional[str] = None  # Extract from custom claims


class FirebaseAuthHandler:
    """Handles Firebase authentication and token verification"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Firebase Admin SDK
        
        Args:
            config: Configuration dictionary containing Firebase settings
        """
        self.config = config
        self.initialized = False
        self._firebase_project_id = None
        self._issuer = None
        self._public_keys_url = "https://www.googleapis.com/robot/v1/metadata/x509/securetoken@system.gserviceaccount.com"
        self._cached_public_keys = {}
        self._keys_expiry = None
        
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                # Check for service account path
                service_account_path = config.get('FIREBASE_SERVICE_ACCOUNT_PATH')
                
                if service_account_path and os.path.exists(service_account_path):
                    # Use service account file
                    cred = credentials.Certificate(service_account_path)
                    firebase_admin.initialize_app(cred)
                    logger.info("Firebase Admin SDK initialized with service account")
                else:
                    # Try default credentials (for Cloud Run)
                    try:
                        firebase_admin.initialize_app()
                        logger.info("Firebase Admin SDK initialized with default credentials")
                    except Exception as e:
                        logger.warning(f"Could not initialize with default credentials: {e}")
                        # Initialize without credentials for token verification only
                        firebase_admin.initialize_app(options={
                            'projectId': config.get('FIREBASE_PROJECT_ID', 'vendora-analytics')
                        })
                        logger.info("Firebase Admin SDK initialized for token verification only")
            
            self._firebase_project_id = config.get('FIREBASE_PROJECT_ID', 'vendora-analytics')
            self._issuer = f"https://securetoken.google.com/{self._firebase_project_id}"
            self.initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {e}")
            raise
    
    async def _get_public_keys(self) -> Dict[str, str]:
        """Fetch and cache Google's public keys for token verification"""
        now = datetime.utcnow()
        
        # Check if we have cached keys that haven't expired
        if self._cached_public_keys and self._keys_expiry and now < self._keys_expiry:
            return self._cached_public_keys
        
        try:
            # Fetch new public keys
            response = requests.get(self._public_keys_url)
            response.raise_for_status()
            
            # Parse cache control header to determine expiry
            cache_control = response.headers.get('Cache-Control', '')
            max_age = 3600  # Default 1 hour
            
            for directive in cache_control.split(','):
                if 'max-age=' in directive:
                    max_age = int(directive.split('=')[1].strip())
                    break
            
            self._cached_public_keys = response.json()
            self._keys_expiry = now + timedelta(seconds=max_age)
            
            return self._cached_public_keys
            
        except Exception as e:
            logger.error(f"Failed to fetch public keys: {e}")
            # Return cached keys if available, even if expired
            if self._cached_public_keys:
                return self._cached_public_keys
            raise
    
    async def verify_token(self, token: str) -> FirebaseUser:
        """
        Verify a Firebase ID token
        
        Args:
            token: The Firebase ID token to verify
            
        Returns:
            FirebaseUser object with verified user information
            
        Raises:
            HTTPException: If token is invalid or verification fails
        """
        try:
            # First try using Firebase Admin SDK (preferred method)
            try:
                decoded_token = firebase_auth.verify_id_token(token)
                
                # Extract user information
                user = FirebaseUser(
                    uid=decoded_token['uid'],
                    email=decoded_token.get('email'),
                    email_verified=decoded_token.get('email_verified', False),
                    display_name=decoded_token.get('name'),
                    phone_number=decoded_token.get('phone_number'),
                    custom_claims=decoded_token.get('custom_claims', {})
                )
                
                # Extract dealership_id from custom claims if present
                if 'dealership_id' in user.custom_claims:
                    user.dealership_id = user.custom_claims['dealership_id']
                
                return user
                
            except Exception as sdk_error:
                logger.warning(f"Firebase Admin SDK verification failed, trying manual verification: {sdk_error}")
                
                # Fallback to manual verification
                # Decode without verification first to get the key ID
                unverified = jwt.get_unverified_header(token)
                kid = unverified.get('kid')
                
                if not kid:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token: No key ID"
                    )
                
                # Get public keys
                public_keys = await self._get_public_keys()
                
                if kid not in public_keys:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token: Unknown key ID"
                    )
                
                # Verify the token
                decoded_token = jwt.decode(
                    token,
                    public_keys[kid],
                    algorithms=['RS256'],
                    audience=self._firebase_project_id,
                    issuer=self._issuer,
                    options={"verify_exp": True}
                )
                
                # Extract user information
                user = FirebaseUser(
                    uid=decoded_token.get('user_id', decoded_token.get('sub')),
                    email=decoded_token.get('email'),
                    email_verified=decoded_token.get('email_verified', False),
                    display_name=decoded_token.get('name'),
                    phone_number=decoded_token.get('phone_number')
                )
                
                # Try to get custom claims from Firebase Admin if available
                try:
                    user_record = firebase_auth.get_user(user.uid)
                    if user_record.custom_claims:
                        user.custom_claims = user_record.custom_claims
                        if 'dealership_id' in user.custom_claims:
                            user.dealership_id = user.custom_claims['dealership_id']
                except:
                    pass  # Custom claims not critical
                
                return user
                
        except JWTError as e:
            logger.error(f"JWT verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate authentication token"
            )
    
    async def set_custom_claims(self, uid: str, claims: Dict[str, Any]) -> bool:
        """
        Set custom claims for a user (requires Admin SDK with full permissions)
        
        Args:
            uid: User ID
            claims: Dictionary of custom claims to set
            
        Returns:
            True if successful
        """
        try:
            firebase_auth.set_custom_user_claims(uid, claims)
            logger.info(f"Set custom claims for user {uid}: {claims}")
            return True
        except Exception as e:
            logger.error(f"Failed to set custom claims for user {uid}: {e}")
            return False
    
    async def create_user(self, email: str, password: str, display_name: Optional[str] = None,
                         dealership_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new Firebase user
        
        Args:
            email: User's email address
            password: User's password
            display_name: Optional display name
            dealership_id: Optional dealership association
            
        Returns:
            Dictionary with user information
        """
        try:
            # Create user
            user = firebase_auth.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            # Set custom claims if dealership_id provided
            if dealership_id:
                await self.set_custom_claims(user.uid, {'dealership_id': dealership_id})
            
            return {
                'uid': user.uid,
                'email': user.email,
                'display_name': user.display_name
            }
            
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to create user: {str(e)}"
            )
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """Get user information by UID"""
        try:
            user = firebase_auth.get_user(uid)
            return {
                'uid': user.uid,
                'email': user.email,
                'email_verified': user.email_verified,
                'display_name': user.display_name,
                'phone_number': user.phone_number,
                'custom_claims': user.custom_claims or {},
                'disabled': user.disabled
            }
        except Exception as e:
            logger.error(f"Failed to get user {uid}: {e}")
            return None


# Global Firebase auth handler instance
_firebase_auth_handler: Optional[FirebaseAuthHandler] = None


def get_firebase_auth_handler() -> FirebaseAuthHandler:
    """Get the global Firebase auth handler instance"""
    if _firebase_auth_handler is None:
        raise RuntimeError("Firebase auth handler not initialized")
    return _firebase_auth_handler


def initialize_firebase_auth(config: Dict[str, Any]):
    """Initialize the global Firebase auth handler"""
    global _firebase_auth_handler
    _firebase_auth_handler = FirebaseAuthHandler(config)
    logger.info("Firebase authentication initialized")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> FirebaseUser:
    """
    FastAPI dependency to get the current authenticated user
    
    Args:
        credentials: Bearer token from Authorization header
        
    Returns:
        FirebaseUser object
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authentication required"
        )
    
    auth_handler = get_firebase_auth_handler()
    return await auth_handler.verify_token(credentials.credentials)


async def get_current_verified_user(
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """
    FastAPI dependency to ensure user has verified email
    
    Args:
        current_user: The authenticated user
        
    Returns:
        FirebaseUser object if email is verified
        
    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


async def require_dealership_access(
    dealership_id: str,
    current_user: FirebaseUser = Depends(get_current_user)
) -> FirebaseUser:
    """
    FastAPI dependency to ensure user has access to specific dealership
    
    Args:
        dealership_id: The dealership to check access for
        current_user: The authenticated user
        
    Returns:
        FirebaseUser object if access is granted
        
    Raises:
        HTTPException: If access is denied
    """
    # Admin users (if you have an admin claim) can access all dealerships
    if current_user.custom_claims.get('admin', False):
        return current_user
    
    # Check if user's dealership_id matches
    if current_user.dealership_id != dealership_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied to dealership {dealership_id}"
        )
    
    return current_user


# Optional: Role-based access control
class RequireRole:
    """Dependency class for role-based access control"""
    
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles
    
    async def __call__(self, current_user: FirebaseUser = Depends(get_current_user)) -> FirebaseUser:
        user_roles = current_user.custom_claims.get('roles', [])
        
        # Check if user has any of the allowed roles
        if not any(role in user_roles for role in self.allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of roles: {', '.join(self.allowed_roles)}"
            )
        
        return current_user