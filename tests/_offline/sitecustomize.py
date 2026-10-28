"""Test-only socket guard inherited by Python subprocesses through PYTHONPATH."""

import os
import socket


def deny_network(*args, **kwargs):
    raise RuntimeError("Network access is disabled during IntakeLedger tests")


TARGETS = [
    (socket, name)
    for name in (
        "create_connection",
        "getaddrinfo",
        "gethostbyname",
        "gethostbyname_ex",
        "gethostbyaddr",
    )
] + [(socket.socket, name) for name in ("connect", "connect_ex", "sendto", "send", "sendall")]
if hasattr(socket.socket, "sendmsg"):
    TARGETS.append((socket.socket, "sendmsg"))

if os.environ.get("INTAKELEDGER_TEST_OFFLINE") == "1":
    for target, name in TARGETS:
        setattr(target, name, deny_network)
