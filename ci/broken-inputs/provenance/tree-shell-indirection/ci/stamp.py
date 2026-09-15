"""A correct one place, so the defect here is unambiguously the indirection."""
import subprocess

FIELDS = ("version", "commit", "tree", "built_at")


def values():
    out = subprocess.run(["git", "describe", "--tags"], capture_output=True)
    return {"version": out.stdout, "commit": "", "tree": "", "built_at": ""}
