import asyncio
import fcntl
import os
import signal
import struct
import subprocess
import termios
import weakref
from pathlib import Path

# Global registry of active sessions so lifespan can kill them on shutdown
_active_sessions: weakref.WeakSet = weakref.WeakSet()


def shutdown_all_sessions() -> None:
    """Kill every active PTY session. Called on backend shutdown."""
    for session in list(_active_sessions):
        session.kill()


def _resolve_cli(provider: str) -> list[str]:
    """Return argv to launch the interactive CLI for the given provider."""
    if provider == "claude":
        return ["claude"]
    elif provider == "gemini":
        return ["gemini"]
    else:
        raise ValueError(f"Unknown CLI provider: {provider!r}")


class AgentSession:
    def __init__(self, master_fd: int, proc: subprocess.Popen):
        self.master_fd = master_fd
        self.proc = proc

    def resize(self, rows: int, cols: int) -> None:
        winsize = struct.pack("HHHH", rows, cols, 0, 0)
        try:
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, winsize)
            if self.proc.pid:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGWINCH)
        except (OSError, ProcessLookupError):
            pass

    def kill(self) -> None:
        try:
            if self.proc.pid:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGTERM)
        except (OSError, ProcessLookupError):
            pass
        try:
            self.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(self.proc.pid), signal.SIGKILL)
            except (OSError, ProcessLookupError):
                pass
        try:
            os.close(self.master_fd)
        except OSError:
            pass


def start_session(cli: str, cwd: Path) -> AgentSession:
    import pty

    argv = _resolve_cli(cli)
    master_fd, slave_fd = pty.openpty()

    env = os.environ.copy()
    env["TERM"] = "xterm-256color"
    env["CV_PROJECT_ROOT"] = str(cwd)

    proc = subprocess.Popen(
        argv,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        close_fds=True,
        cwd=str(cwd),
        env=env,
        preexec_fn=os.setsid,
    )
    os.close(slave_fd)
    session = AgentSession(master_fd=master_fd, proc=proc)
    _active_sessions.add(session)
    return session


async def pty_reader(session: AgentSession, ws) -> None:
    loop = asyncio.get_event_loop()
    try:
        while True:
            data = await loop.run_in_executor(None, _read_fd, session.master_fd)
            if not data:
                break
            await ws.send_bytes(data)
    except Exception:
        pass


def _read_fd(fd: int, size: int = 4096) -> bytes:
    try:
        return os.read(fd, size)
    except OSError:
        return b""


async def ws_reader(ws, session: AgentSession) -> None:
    import json

    try:
        while True:
            msg = await ws.receive()
            if msg["type"] == "websocket.disconnect":
                break
            # Text frame (resize control) or binary keystrokes
            text: str | None = msg.get("text")
            data: bytes | None = msg.get("bytes")
            if text:
                try:
                    frame = json.loads(text)
                    if isinstance(frame, dict) and frame.get("type") == "resize":
                        session.resize(int(frame["rows"]), int(frame["cols"]))
                        continue
                except (json.JSONDecodeError, KeyError, ValueError):
                    pass
                data = text.encode("utf-8")
            if data:
                try:
                    os.write(session.master_fd, data)
                except OSError:
                    break
    except Exception:
        pass
