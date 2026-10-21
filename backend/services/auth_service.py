"""Authentication business logic and user persistence service."""

import threading
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import HTTPException, status

from backend.core.security import (
    create_access_token,
    get_password_hash,
    validate_institutional_email,
    validate_password_complexity,
    verify_password,
)
from backend.schemas.auth import (
    LoginResponse,
    UserProfileResponse,
    UserRegisterRequest,
)


class UserRecord:
    """Internal user record representation."""

    def __init__(
        self,
        user_id: str,
        email: str,
        full_name: str,
        role: str,
        hashed_password: str,
        created_at: Optional[datetime] = None,
    ):
        self.id = user_id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.hashed_password = hashed_password
        self.created_at = created_at or datetime.now(timezone.utc)

    def to_profile(self) -> UserProfileResponse:
        return UserProfileResponse(
            id=self.id,
            email=self.email,
            full_name=self.full_name,
            role=self.role,
            created_at=self.created_at,
        )


class AuthService:
    """Authentication and user management service."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._users_by_email: Dict[str, UserRecord] = {}
        self._users_by_id: Dict[str, UserRecord] = {}
        self._seed_default_users()

    def _seed_default_users(self) -> None:
        """Seed default institutional users for local development and testing."""
        seed_users = [
            (
                "usr-unsa-001",
                "jariasq@unsa.edu.pe",
                "Jhonatan David Arias Quispe",
                "student",
                "Password123*",
            ),
            (
                "usr-unsa-002",
                "docente@unsa.edu.pe",
                "Dr. Jorge Huarsaya",
                "docent",
                "Password123*",
            ),
        ]
        for uid, email, name, role, raw_pass in seed_users:
            hashed = get_password_hash(raw_pass)
            record = UserRecord(
                user_id=uid,
                email=email,
                full_name=name,
                role=role,
                hashed_password=hashed,
            )
            self._users_by_email[email.lower()] = record
            self._users_by_id[uid] = record

    def register_user(self, payload: UserRegisterRequest) -> UserProfileResponse:
        """Register a new institutional user with domain and complexity checks."""
        email_clean = payload.email.strip().lower()

        # Step 1: Institutional domain check
        if not validate_institutional_email(email_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo institucional debe pertenecer al dominio @unsa.edu.pe",
            )

        # Step 2: Password complexity check
        is_valid_pwd, pwd_error = validate_password_complexity(payload.password)
        if not is_valid_pwd:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=pwd_error,
            )

        # Step 3: Conflict check (duplicate email)
        with self._lock:
            if email_clean in self._users_by_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="El correo institucional ya se encuentra registrado en el sistema.",
                )

            user_id = f"usr-{uuid.uuid4()}"
            hashed_pw = get_password_hash(payload.password)
            new_record = UserRecord(
                user_id=user_id,
                email=email_clean,
                full_name=payload.full_name.strip(),
                role=payload.role.strip().lower(),
                hashed_password=hashed_pw,
            )
            self._users_by_email[email_clean] = new_record
            self._users_by_id[user_id] = new_record

            return new_record.to_profile()

    def authenticate_user(self, email: str, password: str) -> LoginResponse:
        """Verify credentials and issue JWT bearer token."""
        email_clean = email.strip().lower()

        # Domain verification
        if not validate_institutional_email(email_clean):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Acceso restringido: Solo se permiten cuentas institucionales @unsa.edu.pe",
            )

        with self._lock:
            user = self._users_by_email.get(email_clean)

        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciales invalidas o no autorizadas",
            )

        token_claims = {
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
        }
        token = create_access_token(subject=user.id, claims=token_claims)

        return LoginResponse(
            access_token=token,
            token_type="bearer",
            expires_in=3600,
            user=user.to_profile(),
        )

    def get_user_by_id(self, user_id: str) -> Optional[UserProfileResponse]:
        """Retrieve user profile by unique identifier."""
        with self._lock:
            user = self._users_by_id.get(user_id)
            return user.to_profile() if user else None

    def get_user_by_email(self, email: str) -> Optional[UserProfileResponse]:
        """Retrieve user profile by institutional email."""
        with self._lock:
            user = self._users_by_email.get(email.strip().lower())
            return user.to_profile() if user else None


# Global singleton instance for service injection
auth_service = AuthService()
