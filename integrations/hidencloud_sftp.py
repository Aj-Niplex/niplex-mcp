import os
import re
import socket
import stat
import time

import paramiko

# All SFTP operations are confined to this base directory.
# Callers cannot escape it via path traversal (e.g. ../../etc).
#
# NOTE: HidenCloud's SFTP is Pterodactyl-based, which already chroots each
# session to that server's own data directory — so from the client's view,
# "/" IS the confined root. There is no separate "/home" to descend into;
# prepending one caused every lookup to resolve to a non-existent nested
# directory. Path-traversal safety still holds: _safe_path normalizes with
# a leading "/" before joining, so a ".." can never resolve above this root.
SFTP_BASE_DIR = "/"

# Read cap: files larger than this are refused whole-read with a clear
# message instead of being loaded fully into memory (a giant log or binary
# used to hang/oom the tool call).
MAX_READ_BYTES = 2 * 1024 * 1024  # 2 MiB

# Depth cap for recursive search so one tool call can't walk the whole server.
SEARCH_MAX_DEPTH = 4

# Max search results returned before truncating.
SEARCH_MAX_RESULTS = 200


class HidenCloudSFTPBridge:
    """
    File-only bridge to a HidenCloud (Pterodactyl) server via SFTP.
    No shell/terminal access — this only reads, writes, lists, and deletes
    files. All paths are confined to SFTP_BASE_DIR to prevent traversal.
    Code should be proven working in the Daytona sandbox first, then
    pushed here for actual deployment.
    """

    def __init__(self):
        self.host = os.environ.get("HIDENCLOUD_SFTP_HOST")
        self.port = int(os.environ.get("HIDENCLOUD_SFTP_PORT", 2022))
        self.user = os.environ.get("HIDENCLOUD_SFTP_USER")
        self.password = os.environ.get("HIDENCLOUD_SFTP_PASSWORD")
        # One timeout for every network phase (TCP connect, banner, auth).
        # Before this, a dead/unreachable server could hang a tool call for
        # minutes (TCP-level default timeouts) — same hang class we already
        # fixed in the bot's MCP bridge with BOT_TOOL_TIMEOUT.
        self.timeout = float(os.environ.get("HIDENCLOUD_SFTP_TIMEOUT", "15"))

    def _safe_path(self, path: str) -> tuple:
        """
        Resolve path relative to SFTP_BASE_DIR and ensure it stays inside.
        Returns (resolved_path, error_string_or_None).
        """
        # Normalise: strip leading slash so os.path.join works predictably
        clean = os.path.normpath("/" + str(path or "").lstrip("/"))
        full = os.path.normpath(os.path.join(SFTP_BASE_DIR, clean.lstrip("/")))
        if not full.startswith(SFTP_BASE_DIR):
            return None, f"Access denied: path '{path}' escapes the allowed base directory."
        return full, None

    def _sftp_path(self, safe: str) -> str:
        """
        This server's SFTP implementation fails to resolve a literal '/'
        root for directory listing (confirmed: listdir_attr('/') returns
        a generic SSH_FX_FAILURE, while absolute paths to actual files
        resolve correctly). '.' — the session's own starting directory,
        which for a chrooted SFTP session IS that root — works reliably
        instead, so translate only that one case.
        """
        return "." if safe == "/" else safe

    def _connect(self):
        if not all([self.host, self.user, self.password]):
            return None, "HidenCloud SFTP env vars not fully configured (HIDENCLOUD_SFTP_HOST/USER/PASSWORD)."
        try:
            # Explicit socket timeout so a dead host fails in `self.timeout`
            # seconds instead of hanging on the OS's default TCP timeout.
            sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            transport = paramiko.Transport(sock)
            # banner_timeout / auth_timeout are Transport ATTRIBUTES (set
            # before connecting), not accepted keyword args on connect()
            # itself — paramiko 5.0.0's Transport.connect() signature is
            # just (hostkey, username, password, pkey). Passing them as
            # kwargs raises TypeError and breaks every SFTP call.
            transport.banner_timeout = self.timeout
            transport.auth_timeout = self.timeout
            transport.connect(username=self.user, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            return (sftp, transport), None
        except Exception as e:
            return None, f"SFTP connection failed (timeout {self.timeout:.0f}s): {str(e)}"

    def list_files(self, path: str = "/") -> str:
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            entries = sftp.listdir_attr(self._sftp_path(safe))
            lines = []
            for entry in sorted(entries, key=lambda e: (not stat.S_ISDIR(e.st_mode), e.filename.lower())):
                kind = "DIR " if stat.S_ISDIR(entry.st_mode) else "FILE"
                lines.append(f"{kind}  {entry.filename}  ({entry.st_size} bytes)")
            return "\n".join(lines) if lines else "No files found."
        except FileNotFoundError:
            return f"List error: '{safe}' does not exist."
        except Exception as e:
            return f"List error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def read_file(self, path: str) -> str:
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            with sftp.open(safe, "rb") as f:
                data = f.read(MAX_READ_BYTES + 1)
            if len(data) > MAX_READ_BYTES:
                return (
                    f"Error: '{safe}' is larger than the {MAX_READ_BYTES // (1024 * 1024)} MiB "
                    f"read cap — use stat_hidencloud_file or search_hidencloud_files instead of "
                    f"reading it whole."
                )
            if isinstance(data, bytes):
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return "Error: file is binary and cannot be decoded as text."
            return data
        except FileNotFoundError:
            return f"Read error: '{safe}' does not exist."
        except Exception as e:
            return f"Read error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def write_file(self, path: str, content: str) -> str:
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            parent = os.path.dirname(safe)
            if parent and parent != SFTP_BASE_DIR:
                self._ensure_dir(sftp, parent)
            with sftp.open(safe, "w") as f:
                f.write(content)
            return f"Successfully wrote {safe} to HidenCloud."
        except Exception as e:
            return f"Write error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def delete_file(self, path: str) -> str:
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            sftp.remove(safe)
            return f"Successfully deleted {safe} from HidenCloud."
        except FileNotFoundError:
            return f"Delete error: '{safe}' does not exist."
        except Exception as e:
            return f"Delete error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def stat(self, path: str) -> str:
        """Check existence + type/size/mtime of a file or directory."""
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            st = sftp.stat(safe)
            kind = "DIR " if stat.S_ISDIR(st.st_mode) else "FILE"
            mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime))
            return f"{kind}  {safe}  ({st.st_size} bytes, modified {mtime})"
        except FileNotFoundError:
            return f"'{safe}' does not exist."
        except Exception as e:
            return f"Stat error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def mkdir(self, path: str) -> str:
        """Create a directory, including any missing parents."""
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            self._ensure_dir(sftp, safe)
            st = sftp.stat(safe)
            if stat.S_ISDIR(st.st_mode):
                return f"Directory ready: {safe}"
            return f"Error: '{safe}' exists and is not a directory."
        except Exception as e:
            return f"Mkdir error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def rename(self, path: str, new_path: str) -> str:
        """Rename or move a file/dir. Destinations inside the confined root only."""
        safe, err = self._safe_path(path)
        if err:
            return err
        new_safe, err2 = self._safe_path(new_path)
        if err2:
            return err2
        if safe == new_safe:
            return "Rename error: source and destination are the same path."
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            parent = os.path.dirname(new_safe)
            if parent and parent != SFTP_BASE_DIR:
                self._ensure_dir(sftp, parent)
            sftp.rename(safe, new_safe)
            return f"Renamed/moved {safe} -> {new_safe}"
        except FileNotFoundError:
            return f"Rename error: '{safe}' does not exist."
        except Exception as e:
            return f"Rename error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def search(self, path: str = "/", pattern: str = "", max_depth: int = None) -> str:
        """
        Recursively find files/dirs whose name contains `pattern`
        (case-insensitive substring). Bounded by max_depth and a result cap.
        """
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        depth_limit = int(max_depth) if max_depth is not None else SEARCH_MAX_DEPTH
        needle = (pattern or "").lower()
        try:
            results = []
            seen = set()

            def walk(sftp_path: str, display: str, depth: int):
                if depth > depth_limit or sftp_path in seen:
                    return
                seen.add(sftp_path)
                try:
                    entries = sftp.listdir_attr(sftp_path)
                except Exception:
                    return
                for e in sorted(entries, key=lambda x: x.filename.lower()):
                    child_display = f"/{e.filename}" if display in ("/", "") else f"{display.rstrip('/')}/{e.filename}"
                    if needle in e.filename.lower():
                        kind = "DIR " if stat.S_ISDIR(e.st_mode) else "FILE"
                        results.append(f"{kind}  {child_display}  ({e.st_size} bytes)")
                    if stat.S_ISDIR(e.st_mode) and len(results) < SEARCH_MAX_RESULTS:
                        child_sftp = f"./{e.filename}" if sftp_path == "." else f"{sftp_path.rstrip('/')}/{e.filename}"
                        walk(child_sftp, child_display, depth + 1)

            walk(self._sftp_path(safe), safe, 0)
            if not results:
                return f"No files matching '{pattern or '(any)'}' found under {safe} (max depth {depth_limit})."
            out = "\n".join(results[:SEARCH_MAX_RESULTS])
            if len(results) > SEARCH_MAX_RESULTS:
                out += f"\n… ({len(results) - SEARCH_MAX_RESULTS} more — refine pattern or path)"
            return out
        except Exception as e:
            return f"Search error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def _ensure_dir(self, sftp, path: str):
        """Recursively create directories, confined to SFTP_BASE_DIR."""
        parts = [p for p in str(path).strip("/").split("/") if p]
        current = SFTP_BASE_DIR
        for part in parts:
            # rstrip prevents '//foo' — this server's SFTP already chokes on
            # the bare '/' root; a doubled slash is the same failure class.
            current = f"{current.rstrip('/')}/{part}"
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)
