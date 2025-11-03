from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.core.security import get_password_hash, verify_password, create_access_token, verify_token
from app.services.audit_service import AuditService
from typing import Optional
from datetime import datetime, timezone


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_user(self, user: UserCreate) -> User:
        hashed_password = get_password_hash(user.password)
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user

    def authenticate_user(self, username: str, password: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Optional[User]:
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        
        # Logger la connexion (seulement si authentification réussie)
        login_time = datetime.now(timezone.utc)
        self.audit_service.log_action(
            action="USER_LOGIN",
            entity_type="user",
            user_id=user.id,
            entity_id=user.id,
            description=f"Connexion de l'utilisateur '{username}'",
            metadata={
                "username": username,
                "login_time": login_time.isoformat()
            },
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def create_access_token_for_user(self, user: User) -> str:
        return create_access_token(data={"sub": user.username})

    def verify_token_and_get_user(self, token: str) -> Optional[User]:
        payload = verify_token(token)
        if payload is None:
            return None
        username = payload.get("sub")
        if username is None:
            return None
        return self.get_user_by_username(username)

