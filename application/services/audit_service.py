from sqlalchemy.orm import Session
from domain.entities.audit import AuditLog
from application.services.auth_service import AuthService
import json

class AuditService:
    def __init__(self, session: Session):
        self.session = session
        
    def log_action(self, module: str, action: str, entity_type: str = None, 
                   entity_id: int = None, old_values: dict = None, new_values: dict = None):
        """
        Record a system action to the database audit log.
        """
        current_user = AuthService.get_current_user()
        user_id = current_user.id if current_user else None
        
        old_val_str = json.dumps(old_values, ensure_ascii=False) if old_values else None
        new_val_str = json.dumps(new_values, ensure_ascii=False) if new_values else None
        
        log_entry = AuditLog(
            user_id=user_id,
            module=module,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            old_values=old_val_str,
            new_values=new_val_str
        )
        
        self.session.add(log_entry)
        self.session.commit()

    def get_all_logs(self):
        """
        Return all audit logs ordered by timestamp descending.
        """
        from domain.entities.user import User
        # Return logs joined with user to easily display username
        return self.session.query(
            AuditLog, User.username
        ).outerjoin(User, AuditLog.user_id == User.id).order_by(AuditLog.timestamp.desc()).all()
