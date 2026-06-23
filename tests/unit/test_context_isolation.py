"""The current-user must be isolated per execution context, otherwise concurrent
web requests would cross-attribute audit log entries."""
import threading

from application.context import set_current_user, get_current_user_ctx, clear_current_user
from application.dto.user_dto import UserDTO


def _user(uid, name):
    return UserDTO(id=uid, username=name, full_name=name, role_id=1,
                   role_name="admin", is_active=True)


def test_contextvar_isolated_across_threads():
    clear_current_user()
    seen = {}
    barrier = threading.Barrier(2)

    def worker(uid, name):
        set_current_user(_user(uid, name))
        barrier.wait()  # ensure both have set before either reads
        seen[name] = get_current_user_ctx().username

    t1 = threading.Thread(target=worker, args=(1, "alice"))
    t2 = threading.Thread(target=worker, args=(2, "bob"))
    t1.start(); t2.start()
    t1.join(); t2.join()

    assert seen == {"alice": "alice", "bob": "bob"}
    # The main thread never set a user, so it must still see None.
    assert get_current_user_ctx() is None


def test_audit_service_uses_contextvar_user(db_session):
    from domain.entities.user import Role, User
    from application.services.audit_service import AuditService

    role = Role(name="admin")
    db_session.add(role)
    db_session.commit()
    u = User(username="carol", password_hash="x", full_name="Carol",
             role_id=role.id, is_active=True)
    db_session.add(u)
    db_session.commit()

    set_current_user(_user(u.id, "carol"))
    AuditService(db_session).log_action(module="hr", action="create",
                                        entity_type="Employee", entity_id=1)
    from domain.entities.audit import AuditLog
    log = db_session.query(AuditLog).one()
    assert log.user_id == u.id
    clear_current_user()
