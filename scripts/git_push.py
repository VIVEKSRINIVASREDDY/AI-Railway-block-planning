import subprocess
import os
import sys
import shutil

git_exe = shutil.which("git") or "git"

def run_git(args, check=False):
    cmd = [git_exe] + args
    print(f">> Running: {' '.join(cmd)}")
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=check)
        if res.stdout:
            print(res.stdout.strip())
        if res.stderr:
            print(res.stderr.strip(), file=sys.stderr)
        return res.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(e.stdout.strip())
        if e.stderr:
            print(e.stderr.strip(), file=sys.stderr)
        return False
    except FileNotFoundError:
        print("Error: Git executable not found. Please ensure Git is installed and in your PATH.", file=sys.stderr)
        sys.exit(1)

def main():
    print("1. Checking git version...")
    if not run_git(["--version"]):
        sys.exit(1)

    print("\n2. Initializing git repository if needed...")
    run_git(["init"])

    print("\n3. Checking status...")
    run_git(["status", "--short"])

    print("\n4. Staging all project files...")
    run_git(["add", "."])

    print("\n5. Creating commit...")
    # Will fail if there are no changes, but that's okay
    run_git(["commit", "-m", "System update: Security cleanup and improvements"])

    print("\n6. Setting branch to main...")
    run_git(["branch", "-M", "main"])

    print("\n7. Pushing to GitHub (origin main)...")
    success = run_git(["push", "-u", "origin", "main"])
    if not success:
        print("\n[ERROR] Push failed. Please check your remote repository settings or resolve conflicts manually.", file=sys.stderr)
        print("Note: Force pushing has been disabled for safety.", file=sys.stderr)

if __name__ == "__main__":
    main()
