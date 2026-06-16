"""UI permission helper. Gates actions against the PermissionService; if no
service is wired (e.g. in isolated tests), everything is allowed."""


def can(permission_service, module: str, action: str) -> bool:
    if permission_service is None:
        return True
    return permission_service.has_permission(module, action)
