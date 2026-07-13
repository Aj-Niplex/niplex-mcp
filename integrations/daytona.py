import os
from daytona import Daytona, CreateSandboxFromSnapshotParams

class DaytonaBridge:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def execute_command(self, command: str, ttl_minutes: int = 0) -> str:
        try:
            os.environ["DAYTONA_API_KEY"] = self.api_key
            daytona = Daytona()
        
            stop_int = ttl_minutes if ttl_minutes > 0 else 5
            del_int = ttl_minutes if ttl_minutes > 0 else 0
        
            params = CreateSandboxFromSnapshotParams(
                auto_stop_interval=stop_int,
                auto_archive_interval=stop_int,
                auto_delete_interval=del_int,
            )
        
            sandbox = daytona.create(params)
            result = sandbox.execute(command)
        
            if ttl_minutes == 0:
                sandbox.delete()
                status = "Destroyed instantly (TTL=0)"
            else:
                status = f"Kept alive for {ttl_minutes}m (Auto-delete active)"
        
            return f"[Sandbox {sandbox.id}] - {status}:\n{result}"
        except Exception as e:
            return f"Daytona Execution Error: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        try:
            os.environ["DAYTONA_API_KEY"] = self.api_key
            daytona = Daytona()
            params = CreateSandboxFromSnapshotParams(auto_delete_interval=0)
            sandbox = daytona.create(params)
        
            import base64
            encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
            cmd = f"echo '{encoded_content}' | base64 -d > {file_path}"
            result = sandbox.execute(cmd)
        
            sandbox.delete()
            return f"Successfully wrote {file_path} to Daytona sandbox."
        except Exception as e:
            return f"Daytona Write Error: {str(e)}"

    def delete_sandbox(self, sandbox_id: str) -> str:
        try:
            os.environ["DAYTONA_API_KEY"] = self.api_key
            daytona = Daytona()
            sandbox = daytona.get_sandbox(sandbox_id)
            sandbox.delete()
            return f"Sandbox {sandbox_id} has been successfully destroyed."
        except Exception as e:
            return f"Error deleting sandbox {sandbox_id}: {str(e)}"
