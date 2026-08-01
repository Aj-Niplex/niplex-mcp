import os
import io
import stat
import paramiko


class HidenCloudSFTPBridge:
    """
    File-only bridge to a HidenCloud (Pterodactyl) server via SFTP.
    No shell/terminal access — this only reads, writes, lists, and deletes
    files. Code should be proven working in the Daytona sandbox first, then
    pushed here for actual deployment.
    """

    def __init__(self):
        self.host = os.environ.get("HIDENCLOUD_SFTP_HOST")
        self.port = int(os.environ.get("HIDENCLOUD_SFTP_PORT", 2022))
        self.user = os.environ.get("HIDENCLOUD_SFTP_USER")
        self.password = os.environ.get("HIDENCLOUD_SFTP_PASSWORD")

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
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            entries = sftp.listdir_attr(path)
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
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            with sftp.open(path, "r") as f:
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
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            # Ensure parent directories exist
            parent = "/".join(path.split("/")[:-1])
            if parent:
                self._ensure_dir(sftp, parent)
            with sftp.open(path, "w") as f:
                f.write(content)
            return f"Successfully wrote {path} to HidenCloud."
        except Exception as e:
            return f"Write error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def delete_file(self, path: str) -> str:
        conn, err = self._connect()
        if err:
            return err
        sftp, transport = conn
        try:
            sftp.remove(path)
            return f"Successfully deleted {path} from HidenCloud."
        except Exception as e:
            return f"Delete error: {str(e)}"
        finally:
            sftp.close()
            transport.close()

    def _ensure_dir(self, sftp, path: str):
        dirs = path.strip("/").split("/")
        current = ""
        for d in dirs:
            current += f"/{d}"
            try:
                sftp.stat(current)
            except FileNotFoundError:
                sftp.mkdir(current)
