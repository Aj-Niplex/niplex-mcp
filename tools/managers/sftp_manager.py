from integrations.hidencloud_sftp import HidenCloudSFTPBridge


class SftpManager:
    """Owns HidenCloud SFTP file operations (no shell access, file-only)."""

    def __init__(self):
        self.hidencloud = HidenCloudSFTPBridge()

    def describe(self):
        return {
            "namespace": "sftp",
            "description": "HidenCloud server file operations via SFTP (list/read/write/delete/stat/mkdir/rename/search). No terminal access.",
            "tools": {
                "list_files": "List files/dirs at a path. Args: path (default '/').",
                "read_file": "Read a file's text content. Args: path.",
                "write_file": "Write/overwrite a file. Args: path, content.",
                "delete_file": "Delete a file. Args: path.",
                "stat": "Check if a file/dir exists; show type, size, modified time. Args: path.",
                "mkdir": "Create a directory (and any missing parents). Args: path.",
                "rename": "Rename or move a file/dir. Args: path, new_path.",
                "search": "Recursively find files/dirs whose name contains a substring. Args: path (default '/'), pattern, max_depth (default 4).",
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
        if tool == "stat":
            return self.hidencloud.stat(kwargs.get("path"))
        if tool == "mkdir":
            return self.hidencloud.mkdir(kwargs.get("path"))
        if tool == "rename":
            return self.hidencloud.rename(kwargs.get("path"), kwargs.get("new_path"))
        if tool == "search":
            return self.hidencloud.search(
                kwargs.get("path", "/"),
                kwargs.get("pattern", ""),
                kwargs.get("max_depth"),
            )
        return f"Unknown sftp tool: {tool}"
