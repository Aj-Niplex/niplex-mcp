import os
import stat
import paramiko

# All SFTP operations are confined to this base directory.
# Callers cannot escape it via path traversal (e.g. ../../etc).
#
# NOTE: HidenCloud's SFTP is Pterodactyl-based, which already chroots each
# session to that server's own data directory — so from the client's view,
# "/" IS the confined root. There is no separate "/home" to descend into;
# prepending one caused every lookup (e.g. listing "/") to resolve to a
# non-existent nested directory and fail with a generic SFTP "failure".
# Path-traversal safety still holds: _safe_path normalizes with a leading
# "/" before joining, so a ".." can never resolve above this root.
SFTP_BASE_DIR = "/"


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

    def _safe_path(self, path: str) -> tuple:
        """
        Resolve path relative to SFTP_BASE_DIR and ensure it stays inside.
        Returns (resolved_path, error_string_or_None).
        """
        # Normalise: strip leading slash so os.path.join works predictably
        clean = os.path.normpath("/" + path.lstrip("/"))
        full = os.path.normpath(os.path.join(SFTP_BASE_DIR, clean.lstrip("/")))
        if not full.startswith(SFTP_BASE_DIR):
            return None, f"Access denied: path '{path}' escapes the allowed base directory."
        return full, None

    def _connect(self):
        if not all([self.host, self.user, self.password]):
            return None, "HidenCloud SFTP env vars not fully configured (HIDENCLOUD_SFTP_HOST/USER/PASSWORD)."
        try:
            transport = paramiko.Transport((self.host, self.port))
            transport.connect(username=self.user, password=self.password)
            sftp = paramiko.SFTPClient.from_transport(transport)
            return (sftp, transport), None
        except Exception as e:
            return None, f"SFTP connection failed: {str(e)}"

    def list_files(self, path: str = "/") -> str:
        safe, err = self._safe_path(path)
        if err:
            return err
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            entries = sftp.listdir_attr(safe)
            lines = []
            for entry in entries:
                kind = "DIR " if stat.S_ISDIR(entry.st_mode) else "FILE"
                lines.append(f"{kind}  {entry.filename}  ({entry.st_size} bytes)")
            return "\n".join(lines) if lines else "No files found."
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
            with sftp.open(safe, "r") as f:
                content = f.read()
            if isinstance(content, bytes):
                try:
                    return content.decode("utf-8")
                except UnicodeDecodeError:
                    return "Error: file is binary and cannot be decoded as text."
            return content
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
        except Exception as e:
            return f"Delete error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def _ensure_dir(self, sftp, path: str):
        """Recursively create directories, confined to SFTP_BASE_DIR."""
        parts = path.replace(SFTP_BASE_DIR, "").strip("/").split("/")
        current = SFTP_BASE_DIR
        for part in parts:
            if not part:
                continue
            current = f"{current}/{part}"
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)
