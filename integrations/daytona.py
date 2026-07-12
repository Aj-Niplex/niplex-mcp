import os
from daytona import Daytona, CreateSandboxFromSnapshotParams

class DaytonaBridge:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def execute_command(self, command: str) -> str:
        try:
            os.environ["DAYTONA_API_KEY"] = self.api_key
            daytona = Daytona()
            
            params = CreateSandboxFromSnapshotParams(
                auto_stop_interval=5,
                auto_archive_interval=5,
                auto_delete_interval=0,
            )
            
            sandbox = daytona.create(params)
            result = sandbox.execute(command)
            sandbox.delete()
            
            return f"[Disposable Sandbox {sandbox.id}]:\n{result}"
        except Exception as e:
            return f"Daytona Execution Error: {str(e)}"
