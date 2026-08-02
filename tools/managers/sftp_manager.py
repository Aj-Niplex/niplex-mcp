from integrations.hidencloud_sftp import HidenCloudSFTPBridge


class SftpManager:
    """Owns HidenCloud SFTP file operations (no shell access, file-only)."""

    def __init__(self):
        self.hidencloud = HidenCloudSFTPBridge()

    def describe(self):
        return {
            "namespace": "sftp",
            "description": "HidenCloud server file operations via SFTP (list/read/write/delete). No terminal access.",
            "tools": {
                "list_files": "List files/dirs at a path. Args: path (default '/').",
                "read_file": "Read a file's content. Args: path.",
                "write_file": "Write/overwrite a file. Args: path, content.",
                "delete_file": "Delete a file. Args: path.",
            }
        }

    def call(self, tool: str, **kwargs):
        if tool == "list_files":
            return self.hidencloud.list_files(kwargs.get("path", "/"))
        if tool == "read_file":
            return self.hidencloud.read_file(kwargs.get("path"))
        if tool == "write_file":
            return self.hidencloud.write_file(kwargs.get("path"), kwargs.get("content"))
        if tool == "delete_file":
            return self.hidencloud.delete_file(kwargs.get("path"))
        return f"Unknown sftp tool: {tool}"
