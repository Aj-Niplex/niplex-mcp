import os
import base64


class E2BBridge:
    """
    E2B sandbox bridge — two modes matching the architecture diagram:
      - run_code(): short-lived code execution (e2b-code-interpreter)
      - Desktop/computer-use methods: GUI automation via a virtual desktop
        (e2b-desktop) — screenshots, mouse, keyboard, launching apps.
    Complements Daytona (long-running execution) rather than replacing it.
    """

    def __init__(self):
        self.api_key = os.environ.get("E2B_API_KEY")

    # ---------- Short-run code execution ----------

    def run_code(self, code: str, language: str = "python") -> str:
        if not self.api_key:
            return "E2B_API_KEY not configured."
        try:
            from e2b_code_interpreter import Sandbox
            sbx = Sandbox.create(api_key=self.api_key, timeout=120)
            try:
                execution = sbx.run_code(code, language=language)
                if execution.error:
                    return f"E2B Execution Error: {execution.error.name}: {execution.error.value}"
                output = execution.text or ""
                logs = ""
                if execution.logs:
                    stdout = "\n".join(execution.logs.stdout) if execution.logs.stdout else ""
                    stderr = "\n".join(execution.logs.stderr) if execution.logs.stderr else ""
                    logs = (stdout + ("\n" + stderr if stderr else "")).strip()
                return output or logs or "Executed with no output."
            finally:
                sbx.kill()
        except Exception as e:
            return f"E2B Bridge Error: {str(e)}"

    # ---------- Computer use / desktop automation ----------

    def desktop_screenshot(self) -> str:
        """Take a screenshot of a fresh desktop sandbox, return as base64 PNG."""
        if not self.api_key:
            return "E2B_API_KEY not configured."
        try:
            from e2b_desktop import Sandbox
            desktop = Sandbox(api_key=self.api_key, timeout=120)
            try:
                image_bytes = desktop.screenshot()
                return base64.b64encode(image_bytes).decode("utf-8")
            finally:
                desktop.kill()
        except Exception as e:
            return f"E2B Desktop Error: {str(e)}"

    def desktop_run_actions(self, actions: list) -> str:
        """
        Run a sequence of computer-use actions in one desktop sandbox session.
        Each action is a dict, e.g.:
          {"type": "launch", "app": "google-chrome"}
          {"type": "click", "x": 100, "y": 200}
          {"type": "write", "text": "hello"}
          {"type": "hotkey", "keys": ["ctrl", "c"]}
          {"type": "wait", "seconds": 2}
        Returns a base64 PNG of the final screenshot plus a log of actions taken.
        """
        if not self.api_key:
            return "E2B_API_KEY not configured."
        try:
            from e2b_desktop import Sandbox
            import time
            desktop = Sandbox(api_key=self.api_key, timeout=180)
            log = []
            try:
                for action in actions:
                    a_type = action.get("type")
                    if a_type == "launch":
                        desktop.launch(action["app"])
                        log.append(f"launched {action['app']}")
                    elif a_type == "click":
                        desktop.mouse_move(action["x"], action["y"])
                        desktop.left_click()
                        log.append(f"clicked ({action['x']},{action['y']})")
                    elif a_type == "write":
                        desktop.write(action["text"])
                        log.append(f"wrote: {action['text'][:40]}")
                    elif a_type == "hotkey":
                        desktop.hotkey(*action["keys"])
                        log.append(f"hotkey: {'+'.join(action['keys'])}")
                    elif a_type == "wait":
                        time.sleep(action.get("seconds", 1))
                        log.append(f"waited {action.get('seconds', 1)}s")
                    else:
                        log.append(f"unknown action type: {a_type}")

                image_bytes = desktop.screenshot()
                screenshot_b64 = base64.b64encode(image_bytes).decode("utf-8")
                return f"Actions: {'; '.join(log)}\nScreenshot (base64 PNG):\n{screenshot_b64}"
            finally:
                desktop.kill()
        except Exception as e:
            return f"E2B Desktop Error: {str(e)}"
