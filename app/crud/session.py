from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.models.sessions import Session as UserSession
from app.models.user import User


def get_user_active_sessions(db: Session, user_id: int) -> List[UserSession]:
    """Get all active sessions for a specific user."""
    return (
        db.query(UserSession)
        .filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        .order_by(UserSession.created_at.desc())
        .all()
    )


def get_user_session_by_id(
    db: Session, user_id: int, session_id: int
) -> Optional[UserSession]:
    """Get a specific session by ID for a user."""
    return (
        db.query(UserSession)
        .filter(
            and_(
                UserSession.id == session_id,
                UserSession.user_id == user_id,
                UserSession.is_active == True,
            )
        )
        .first()
    )


def get_session_by_id(db: Session, session_id: int) -> Optional[UserSession]:
    """Get a session by ID (admin function)."""
    return (
        db.query(UserSession)
        .filter(and_(UserSession.id == session_id, UserSession.is_active == True))
        .first()
    )


def get_all_active_sessions(
    db: Session, skip: int = 0, limit: int = 100, company_id: Optional[int] = None
) -> List[UserSession]:
    """Get all active sessions (admin function).
    If company_id provided, filter by company."""
    query = db.query(UserSession).filter(
        and_(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    if company_id is not None:
        query = query.join(User).filter(User.company_id == company_id)

    return query.order_by(UserSession.created_at.desc()).offset(skip).limit(limit).all()


def get_current_user_session(db: Session, user_id: int) -> Optional[UserSession]:
    """Get current session for a user (used to exclude from revoke all)."""
    return (
        db.query(UserSession)
        .filter(and_(UserSession.user_id == user_id, UserSession.is_active == True))
        .first()
    )


def revoke_session(db: Session, session: UserSession) -> None:
    """Revoke a session by marking it as inactive."""
    session.is_active = False
    db.add(session)
    db.commit()


def get_session_statistics(db: Session, company_id: Optional[int] = None) -> dict:
    """
    Get session statistics for admin dashboard.
    If company_id provided, filter by company.
    """
    # Active sessions in last 24 hours
    last_24h = datetime.now(timezone.utc) - timedelta(hours=24)

    query = db.query(UserSession).filter(
        and_(
            UserSession.is_active == True,
            UserSession.created_at >= last_24h,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    if company_id is not None:
        query = query.join(User).filter(User.company_id == company_id)

    active_sessions_24h = query.count()

    # Unique active users in last 24 hours
    query = db.query(func.count(func.distinct(UserSession.user_id))).filter(
        and_(
            UserSession.is_active == True,
            UserSession.created_at >= last_24h,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    if company_id is not None:
        query = query.join(User).filter(User.company_id == company_id)

    active_users_24h = query.scalar()

    # Total active sessions
    query = db.query(UserSession).filter(
        and_(
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
    )

    if company_id is not None:
        query = query.join(User).filter(User.company_id == company_id)

    total_active_sessions = query.count()

    return {
        "active_sessions_24h": active_sessions_24h,
        "active_users_24h": active_users_24h or 0,
        "total_active_sessions": total_active_sessions,
    }


def get_session_by_refresh_token(
    db: Session, user_id: int, refresh_token: str
) -> Optional[UserSession]:
    """Get session by refresh token for token refresh endpoint."""
    return (
        db.query(UserSession)
        .filter(
            UserSession.user_id == user_id,
            UserSession.refresh_token == refresh_token,
            UserSession.is_active == True,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )


def get_user_sessions_for_logout(db: Session, user_id: int) -> Optional[UserSession]:
    """Get user session for logout endpoint."""
    return (
        db.query(UserSession)
        .filter(UserSession.user_id == user_id, UserSession.is_active == True)
        .first()
    )
