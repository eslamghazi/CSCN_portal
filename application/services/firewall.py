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


def allow_port(port: int) -> bool:
    """Request a Windows Firewall inbound TCP allow rule for `port` (triggers a
    UAC prompt). Any existing rule with the same name is replaced. Returns True
    if the elevated request was launched (not a guarantee the rule was added)."""
    if not is_windows():
        logger.warning("Firewall rule requested on a non-Windows platform; ignored.")
        return False
    # Replace any stale rule of the same name, then add a fresh one. Run both
    # under one elevated cmd so a single UAC prompt covers the whole operation.
    inner = (
        f'netsh advfirewall firewall delete rule name="{RULE_NAME}" >nul 2>&1 & '
        f'netsh advfirewall firewall add rule name="{RULE_NAME}" '
        f'dir=in action=allow protocol=TCP localport={port}'
    )
    params = f'/c {inner}'
    try:
        # SW_HIDE (0): no visible console window; the UAC dialog still appears.
        rc = ctypes.windll.shell32.ShellExecuteW(None, "runas", "cmd.exe", params, None, 0)
        launched = int(rc) > 32  # >32 means ShellExecute succeeded
        if launched:
            logger.info(f"Requested firewall allow rule for TCP port {port}.")
        else:
            logger.warning(f"Firewall elevation not granted (ShellExecute rc={rc}).")
        return launched
    except Exception as e:  # pragma: no cover - OS/runtime dependent
        logger.error(f"Firewall rule request failed: {e}")
        return False
