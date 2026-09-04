"""
api/auth.py
-----------
Supabase JWT verification for FastAPI.
Extracts and validates the Bearer token from Authorization header,
returns the Supabase user_id (UUID string).
"""

import os
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

load_dotenv()

SUPABASE_JWT_SECRET = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")

_bearer = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(_bearer),
) -> str:
    """
    Dependency that validates the Supabase JWT and returns the user's UUID.
    Raises 401 if token is missing or invalid.
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is required. Include: Authorization: Bearer <supabase_access_token>",
        )

    token = credentials.credentials
    try:
        # Supabase JWTs use HS256 with the JWT secret (not service role key)
        # The JWT secret is at: Supabase Dashboard -> Settings -> API -> JWT Secret
        # We decode using the anon key's secret embedded in the JWT header.
        # For Supabase, we can decode without verification to get the sub (user_id)
        # and then verify via Supabase REST API, OR use the JWT secret directly.
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        return user_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )
