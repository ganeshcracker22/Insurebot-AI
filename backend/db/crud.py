"""
CRUD operations for policy management.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from backend.db.models import Policy


def create_policy(
    db: Session,
    user_name: str,
    policy_type: str,
    premium: float,
    status: str = "active",
) -> Policy:
    """Create a new policy record."""
    policy = Policy(
        user_name=user_name,
        policy_type=policy_type,
        premium=premium,
        status=status,
        created_at=datetime.utcnow(),
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


def list_policies(
    db: Session,
    user_name: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[Policy]:
    """List policies with optional filters."""
    query = db.query(Policy)
    if user_name:
        query = query.filter(Policy.user_name == user_name)
    if status:
        query = query.filter(Policy.status == status)
    return query.offset(skip).limit(limit).all()


def get_policy(db: Session, policy_id: int) -> Optional[Policy]:
    """Get a single policy by ID."""
    return db.query(Policy).filter(Policy.id == policy_id).first()


def cancel_policy(db: Session, policy_id: int) -> Optional[Policy]:
    """Cancel a policy by setting its status to 'cancelled'."""
    policy = get_policy(db, policy_id)
    if policy is None:
        return None
    policy.status = "cancelled"
    db.commit()
    db.refresh(policy)
    return policy


def delete_policy(db: Session, policy_id: int) -> bool:
    """Permanently delete a policy record."""
    policy = get_policy(db, policy_id)
    if policy is None:
        return False
    db.delete(policy)
    db.commit()
    return True
