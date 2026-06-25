"""Windows Firewall helper: request an inbound allow rule for the LAN peer port.

Adding a firewall rule needs administrator rights, so this launches an elevated
`netsh` via ShellExecute's "runas" verb — Windows shows a UAC prompt. It is a
best-effort, fire-and-forget request: we can tell whether the elevated process
was launched, not whether the rule was ultimately created."""
import ctypes
import sys

from loguru import logger

RULE_NAME = "CSCN Portal"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def allow_ports(ports) -> bool:
    """Request a Windows Firewall inbound TCP allow rule covering `ports` (one
    elevated UAC prompt for all of them). Replaces any stale rule of the same
    name. Returns True if the elevated request was launched."""
    if not is_windows():
        logger.warning("Firewall rule requested on a non-Windows platform; ignored.")
        return False
    portlist = ",".join(str(int(p)) for p in ports)
    inner = (
        f'netsh advfirewall firewall delete rule name="{RULE_NAME}" >nul 2>&1 & '
        f'netsh advfirewall firewall add rule name="{RULE_NAME}" '
        f'dir=in action=allow protocol=TCP localport={portlist}'
    )
    params = f'/c {inner}'
    try:
        # SW_HIDE (0): no visible console window; the UAC dialog still appears.
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 0)
        launched = int(rc) > 32  # >32 means ShellExecute succeeded
        if launched:
            logger.info(f"Requested firewall allow rule for TCP port(s) {portlist}.")
        else:
            logger.warning(f"Firewall elevation not granted (ShellExecute rc={rc}).")
        return launched
    except Exception as e:  # pragma: no cover - OS/runtime dependent
        logger.error(f"Firewall rule request failed: {e}")
        return False


def allow_port(port: int) -> bool:
    """Allow a single inbound TCP port (see allow_ports)."""
    return allow_ports([port])


def try_add_rule_silent(ports) -> bool:
    """Best-effort: add the firewall rule WITHOUT a UAC prompt (works only when
    the process is already elevated). Never raises; returns True on success."""
    if not is_windows():
        return False
    import subprocess
    portlist = ",".join(str(int(p)) for p in ports)
    create_no_window = 0x08000000
    try:
        subprocess.run(
            ["netsh", "advfirewall", "firewall", "delete", "rule", f"name={RULE_NAME}"],
            capture_output=True, creationflags=create_no_window)
        r = subprocess.run(
            ["netsh", "advfirewall", "firewall", "add", "rule", f"name={RULE_NAME}",
             "dir=in", "action=allow", "protocol=TCP", f"localport={portlist}"],
            capture_output=True, creationflags=create_no_window)
        ok = r.returncode == 0
        if ok:
            logger.info(f"Added firewall rule (silent) for TCP port(s) {portlist}.")
        return ok
    except Exception as e:
        logger.debug(f"Silent firewall rule add failed: {e}")
        return False
