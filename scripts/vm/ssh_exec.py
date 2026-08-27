"""SSH execution helper for connecting to the VM.
Usage: python ssh_exec.py <command>
   or: python ssh_exec.py -f <script_file>
"""
import subprocess
import os
import sys

# 敏感配置优先环境变量，其次 config/local_config.py（不入库），默认 localhost
_REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)
try:
    from config import local_config
except Exception:
    local_config = None

def _cfg(name, default):
    value = os.environ.get(name)
    if value:
        return value
    return getattr(local_config, name, None) if local_config else None or default

HOST = _cfg("VM_HOST", "localhost")
USER = _cfg("VM_USER", "root")
VM_PASSWORD = _cfg("VM_PASSWORD", "")
ASKPASS_SCRIPT = os.path.join(os.environ.get("TEMP", "/tmp"), "ssh_passwd.bat")

# Ensure askpass script exists
if not os.path.exists(ASKPASS_SCRIPT):
    with open(ASKPASS_SCRIPT, "w") as f:
        f.write("@echo off\necho " + VM_PASSWORD + "\n")

def ssh_exec(command: str, timeout: int = 300) -> tuple:
    """Execute a command on the remote VM via SSH."""
    env = os.environ.copy()
    env["DISPLAY"] = "dummy:0"
    env["SSH_ASKPASS"] = ASKPASS_SCRIPT
    env["SSH_ASKPASS_REQUIRE"] = "force"
    
    proc = subprocess.Popen(
        ["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
         f"{USER}@{HOST}", command],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        env=env, text=True, encoding="utf-8", errors="replace"
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        return stdout, stderr, proc.returncode
    except subprocess.TimeoutExpired:
        proc.kill()
        return "", "TIMEOUT", -1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ssh_exec.py <command>  OR  python ssh_exec.py -f <file>")
        sys.exit(1)
    
    if sys.argv[1] == "-f":
        # Read command from file
        if len(sys.argv) < 3:
            print("Usage: python ssh_exec.py -f <file>")
            sys.exit(1)
        with open(sys.argv[2], "r", encoding="utf-8") as f:
            cmd = f.read().strip()
    else:
        cmd = " ".join(sys.argv[1:])
    
    stdout, stderr, rc = ssh_exec(cmd)
    if stdout:
        print(stdout)
    if stderr:
        print(stderr, file=sys.stderr)
    sys.exit(rc)
