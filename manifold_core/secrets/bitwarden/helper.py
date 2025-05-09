import os
import subprocess
import json

class BitwardenHelper:
    def __init__(self, project_id=None, debug=False):
        self.project_id = project_id or os.getenv("BW_PROJECT_ID")
        self.token = os.getenv("BW_ACCESS_TOKEN")
        if not self.token:
            raise RuntimeError("BW_ACCESS_TOKEN environment variable is not set.")
        self.debug = debug

    def _run_bws(self, args):
        cmd = ["bws"] + args + ["-t", self.token]
        if self.debug:
            print(f"[bws debug] Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if self.debug:
            print(f"[bws debug] stdout: {result.stdout}")
            print(f"[bws debug] stderr: {result.stderr}")

        result.check_returncode()
        return result.stdout


    def get_secret(self, name: str) -> str:
        token = os.getenv("BW_ACCESS_TOKEN")

        result = subprocess.run(
            ["bws", "secret", "list", "-t", token],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        secrets = json.loads(result.stdout)
        match = next((s for s in secrets if s.get("key") == name), None)
        if not match:
            raise ValueError(f"Secret '{name}' not found.")

        result = subprocess.run(
            ["bws", "secret", "get", match["id"], "-t", token],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
        return json.loads(result.stdout)["value"]



    def create_secret(self, name: str, value: str) -> None:
        token = os.getenv("BW_ACCESS_TOKEN")

        subprocess.run(
            ["bws", "secret", "create", name, value, "-t", token],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )

    def has_secret(self, key: str) -> bool:
        output = self._run_bws(["secret", "list"])
        secrets = json.loads(output)
        return any(s.get("key") == key for s in secrets)
