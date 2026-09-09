import subprocess
import os
import sys

git_exe = r"C:\Users\Vivek\AppData\Local\MinGit\cmd\git.exe"
repo_url = "https://github.com/VIVEKSRINIVASREDDY/AI-Railway-block-planning.git"

def run_git(args):
    cmd = [git_exe] + args
    print(f">> Running: {' '.join(cmd)}")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout.strip())
    if res.stderr:
        print(res.stderr.strip(), file=sys.stderr)
    return res.returncode == 0

print("1. Checking git version...")
run_git(["--version"])

print("\n2. Initializing git repository if needed...")
run_git(["init"])

print("\n3. Configuring user...")
run_git(["config", "user.name", "Vivek Srinivas Reddy"])
run_git(["config", "user.email", "viveksrinivasreddy@users.noreply.github.com"])

print("\n4. Checking remotes...")
run_git(["remote", "-v"])
# Set or update origin
run_git(["remote", "remove", "origin"])
run_git(["remote", "add", "origin", repo_url])

print("\n5. Checking status...")
run_git(["status", "--short"])

print("\n6. Staging all project files...")
run_git(["add", "."])

print("\n7. Creating commit...")
run_git(["commit", "-m", "Full Stack AI Railway Block Planning & Maintenance Optimization System"])

print("\n8. Setting branch to main...")
run_git(["branch", "-M", "main"])

print("\n9. Pushing to GitHub (origin main)...")
success = run_git(["push", "-u", "origin", "main"])
if not success:
    print("\nAttempting push with force in case remote repo has existing README/init commit...")
    run_git(["push", "-u", "origin", "main", "--force"])
