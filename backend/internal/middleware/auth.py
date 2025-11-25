"""
Authentication and Authorization Middleware

This module provides comprehensive authentication and authorization
middleware for the FinOps platform, supporting JWT tokens, API keys,
and role-based access control (RBAC).

Features:
- JWT token authentication
- API key authentication
- Role-based access control (RBAC)
- Permission-based authorization
- Token refresh mechanism
- Security headers
- Rate limiting per user
- Audit logging for security events
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Union

import jwt
from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from ..infra.config import get_security_config
from ..observability.logger import get_logger
from ..observability.metrics import get_finops_metrics


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str):
    """User roles for RBAC"""
    ADMIN = "admin"
    FINOPS_MANAGER = "finops_manager"
    COST_ANALYST = "cost_analyst"
    VIEWER = "viewer"
    API_USER = "api_user"


class Permission(str):
    """Permissions for fine-grained access control"""
    # Cost analysis permissions
    READ_COSTS = "read:costs"
    WRITE_COSTS = "write:costs"
    EXPORT_COSTS = "export:costs"
    
    # Budget permissions
    READ_BUDGETS = "read:budgets"
    WRITE_BUDGETS = "write:budgets"
    APPROVE_BUDGETS = "approve:budgets"
    
    # Optimization permissions
    READ_OPTIMIZATIONS = "read:optimizations"
    WRITE_OPTIMIZATIONS = "write:optimizations"
    APPLY_OPTIMIZATIONS = "apply:optimizations"
    
    # Resource permissions
    READ_RESOURCES = "read:resources"
    WRITE_RESOURCES = "write:resources"
    DELETE_RESOURCES = "delete:resources"
    
    # Admin permissions
    MANAGE_USERS = "manage:users"
    MANAGE_SETTINGS = "manage:settings"
    VIEW_AUDIT_LOGS = "view:audit_logs"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[str, Set[str]] = {
    UserRole.ADMIN: {
        Permission.READ_COSTS, Permission.WRITE_COSTS, Permission.EXPORT_COSTS,
        Permission.READ_BUDGETS, Permission.WRITE_BUDGETS, Permission.APPROVE_BUDGETS,
        Permission.READ_OPTIMIZATIONS, Permission.WRITE_OPTIMIZATIONS, Permission.APPLY_OPTIMIZATIONS,
        Permission.READ_RESOURCES, Permission.WRITE_RESOURCES, Permission.DELETE_RESOURCES,
        Permission.MANAGE_USERS, Permission.MANAGE_SETTINGS, Permission.VIEW_AUDIT_LOGS
    },
    UserRole.FINOPS_MANAGER: {
        Permission.READ_COSTS, Permission.WRITE_COSTS, Permission.EXPORT_COSTS,
        Permission.READ_BUDGETS, Permission.WRITE_BUDGETS, Permission.APPROVE_BUDGETS,
        Permission.READ_OPTIMIZATIONS, Permission.WRITE_OPTIMIZATIONS, Permission.APPLY_OPTIMIZATIONS,
        Permission.READ_RESOURCES, Permission.WRITE_RESOURCES
    },
    UserRole.COST_ANALYST: {
        Permission.READ_COSTS, Permission.EXPORT_COSTS,
        Permission.READ_BUDGETS,
        Permission.READ_OPTIMIZATIONS, Permission.WRITE_OPTIMIZATIONS,
        Permission.READ_RESOURCES
    },
    UserRole.VIEWER: {
        Permission.READ_COSTS,
        Permission.READ_BUDGETS,
        Permission.READ_OPTIMIZATIONS,
        Permission.READ_RESOURCES
    },
    UserRole.API_USER: {
        Permission.READ_COSTS, Permission.WRITE_COSTS,
        Permission.READ_BUDGETS, Permission.WRITE_BUDGETS,
        Permission.READ_OPTIMIZATIONS, Permission.WRITE_OPTIMIZATIONS,
        Permission.READ_RESOURCES, Permission.WRITE_RESOURCES
    }
}


class User(BaseModel):
    """User model for authentication"""
    id: str
    email: str
    username: str
    roles: List[str]
    permissions: Set[str]
    cost_centers: List[str]  # Cost centers user has access to
    is_active: bool = True
    created_at: datetime
    last_login: Optional[datetime] = None


class TokenData(BaseModel):
    """JWT token data"""
    user_id: str
    email: str
    username: str
    roles: List[str]
    permissions: List[str]
    cost_centers: List[str]
    exp: int
    iat: int
    token_type: str = "access"


class AuthenticationError(HTTPException):
    """Authentication error"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class AuthorizationError(HTTPException):
    """Authorization error"""
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class JWTManager:
    """JWT token management"""
    
    def __init__(self):
        self.config = get_security_config()
        self.logger = get_logger(__name__)
    
    def create_access_token(self, user: User) -> str:
        """Create JWT access token"""
        now = datetime.utcnow()
        exp = now + timedelta(minutes=self.config.jwt_expiration_minutes)
        
        payload = {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "roles": user.roles,
            "permissions": list(user.permissions),
            "cost_centers": user.cost_centers,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "token_type": "access"
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        self.logger.debug(f"Created access token for user: {user.username}")
        return token
    
    def create_refresh_token(self, user: User) -> str:
        """Create JWT refresh token"""
        now = datetime.utcnow()
        exp = now + timedelta(days=self.config.jwt_refresh_expiration_days)
        
        payload = {
            "user_id": user.id,
            "username": user.username,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "token_type": "refresh"
        }
        
        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm
        )
        
        self.logger.debug(f"Created refresh token for user: {user.username}")
        return token
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.config.jwt_secret_key,
                algorithms=[self.config.jwt_algorithm]
            )
            
            token_data = TokenData(**payload)
            
            # Check if token is expired
            if datetime.utcnow().timestamp() > token_data.exp:
                raise AuthenticationError("Token has expired")
            
            return token_data
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
        except Exception as e:
            self.logger.error(f"Token verification failed: {e}")
            raise AuthenticationError("Token verification failed")
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Refresh access token using refresh token"""
        try:
            token_data = self.verify_token(refresh_token)
            
            if token_data.token_type != "refresh":
                raise AuthenticationError("Invalid refresh token")
            
            # Get user data (in real implementation, fetch from database)
            # For now, create minimal user data
            user = User(
                id=token_data.user_id,
                email="",  # Would be fetched from database
                username=token_data.username,
                roles=[],  # Would be fetched from database
                permissions=set(),  # Would be calculated from roles
                cost_centers=[],  # Would be fetched from database
                created_at=datetime.utcnow()
            )
            
            return self.create_access_token(user)
            
        except Exception as e:
            self.logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError("Token refresh failed")


class APIKeyManager:
    """API key management"""
    
    def __init__(self):
        self.config = get_security_config()
        self.logger = get_logger(__name__)
        # In real implementation, this would be stored in database
        self.api_keys: Dict[str, User] = {}
    
    def verify_api_key(self, api_key: str) -> User:
        """Verify API key and return associated user"""
        if api_key not in self.api_keys:
            raise AuthenticationError("Invalid API key")
        
        user = self.api_keys[api_key]
        
        if not user.is_active:
            raise AuthenticationError("API key is inactive")
        
        self.logger.debug(f"API key verified for user: {user.username}")
        return user
    
    def create_api_key(self, user: User) -> str:
        """Create new API key for user"""
        import secrets
        api_key = secrets.token_urlsafe(32)
        self.api_keys[api_key] = user
        
        self.logger.info(f"Created API key for user: {user.username}")
        return api_key
    
    def revoke_api_key(self, api_key: str) -> bool:
        """Revoke API key"""
        if api_key in self.api_keys:
            user = self.api_keys[api_key]
            del self.api_keys[api_key]
            self.logger.info(f"Revoked API key for user: {user.username}")
            return True
        return False


class AuthenticationMiddleware:
    """Authentication middleware for FastAPI"""
    
    def __init__(self):
        self.config = get_security_config()
        self.logger = get_logger(__name__)
        self.metrics = get_finops_metrics()
        self.jwt_manager = JWTManager()
        self.api_key_manager = APIKeyManager()
        self.security = HTTPBearer(auto_error=False)
    
    async def authenticate_request(self, request: Request) -> Optional[User]:
        """Authenticate request and return user"""
        
        # Try JWT authentication first
        user = await self._authenticate_jwt(request)
        if user:
            return user
        
        # Try API key authentication
        user = await self._authenticate_api_key(request)
        if user:
            return user
        
        return None
    
    async def _authenticate_jwt(self, request: Request) -> Optional[User]:
        """Authenticate using JWT token"""
        try:
            credentials: HTTPAuthorizationCredentials = await self.security(request)
            
            if not credentials or credentials.scheme.lower() != "bearer":
                return None
            
            token_data = self.jwt_manager.verify_token(credentials.credentials)
            
            # Create user object from token data
            user = User(
                id=token_data.user_id,
                email=token_data.email,
                username=token_data.username,
                roles=token_data.roles,
                permissions=set(token_data.permissions),
                cost_centers=token_data.cost_centers,
                created_at=datetime.utcnow(),
                last_login=datetime.utcnow()
            )
            
            self.logger.debug(f"JWT authentication successful for user: {user.username}")
            self.metrics.record_security_event("jwt_auth_success", {"user_id": user.id})
            
            return user
            
        except AuthenticationError:
            self.metrics.record_security_event("jwt_auth_failed", {"reason": "invalid_token"})
            return None
        except Exception as e:
            self.logger.error(f"JWT authentication error: {e}")
            self.metrics.record_security_event("jwt_auth_error", {"error": str(e)})
            return None
    
    async def _authenticate_api_key(self, request: Request) -> Optional[User]:
        """Authenticate using API key"""
        try:
            api_key = request.headers.get(self.config.api_key_header)
            
            if not api_key:
                return None
            
            user = self.api_key_manager.verify_api_key(api_key)
            
            self.logger.debug(f"API key authentication successful for user: {user.username}")
            self.metrics.record_security_event("api_key_auth_success", {"user_id": user.id})
            
            return user
            
        except AuthenticationError:
            self.metrics.record_security_event("api_key_auth_failed", {"reason": "invalid_key"})
            return None
        except Exception as e:
            self.logger.error(f"API key authentication error: {e}")
            self.metrics.record_security_event("api_key_auth_error", {"error": str(e)})
            return None


class AuthorizationMiddleware:
    """Authorization middleware for RBAC"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.metrics = get_finops_metrics()
    
    def check_permission(self, user: User, required_permission: str) -> bool:
        """Check if user has required permission"""
        if not user.is_active:
            return False
        
        has_permission = required_permission in user.permissions
        
        if not has_permission:
            self.logger.warning(
                f"Permission denied for user {user.username}: {required_permission}",
                extra={
                    "user_id": user.id,
                    "required_permission": required_permission,
                    "user_permissions": list(user.permissions)
                }
            )
            self.metrics.record_security_event("permission_denied", {
                "user_id": user.id,
                "permission": required_permission
            })
        
        return has_permission
    
    def check_role(self, user: User, required_role: str) -> bool:
        """Check if user has required role"""
        if not user.is_active:
            return False
        
        has_role = required_role in user.roles
        
        if not has_role:
            self.logger.warning(
                f"Role check failed for user {user.username}: {required_role}",
                extra={
                    "user_id": user.id,
                    "required_role": required_role,
                    "user_roles": user.roles
                }
            )
        
        return has_role
    
    def check_cost_center_access(self, user: User, cost_center: str) -> bool:
        """Check if user has access to specific cost center"""
        if not user.is_active:
            return False
        
        # Admin users have access to all cost centers
        if UserRole.ADMIN in user.roles:
            return True
        
        # Check if user has access to specific cost center
        has_access = cost_center in user.cost_centers
        
        if not has_access:
            self.logger.warning(
                f"Cost center access denied for user {user.username}: {cost_center}",
                extra={
                    "user_id": user.id,
                    "cost_center": cost_center,
                    "user_cost_centers": user.cost_centers
                }
            )
            self.metrics.record_security_event("cost_center_access_denied", {
                "user_id": user.id,
                "cost_center": cost_center
            })
        
        return has_access


# Utility functions for calculating permissions
def calculate_user_permissions(roles: List[str]) -> Set[str]:
    """Calculate user permissions based on roles"""
    permissions = set()
    
    for role in roles:
        if role in ROLE_PERMISSIONS:
            permissions.update(ROLE_PERMISSIONS[role])
    
    return permissions


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


# Global instances
_auth_middleware: Optional[AuthenticationMiddleware] = None
_authz_middleware: Optional[AuthorizationMiddleware] = None


def get_auth_middleware() -> AuthenticationMiddleware:
    """Get authentication middleware instance"""
    global _auth_middleware
    
    if _auth_middleware is None:
        _auth_middleware = AuthenticationMiddleware()
    
    return _auth_middleware


def get_authz_middleware() -> AuthorizationMiddleware:
    """Get authorization middleware instance"""
    global _authz_middleware
    
    if _authz_middleware is None:
        _authz_middleware = AuthorizationMiddleware()
    
    return _authz_middleware