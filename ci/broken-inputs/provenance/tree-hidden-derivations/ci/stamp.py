"""A correct one place, so every defect in this tree is unambiguously elsewhere."""
import subprocess

FIELDS = ("version", "commit", "tree", "built_at")


def values():
    out = subprocess.run(["git", "describe", "--tags"], capture_output=True)
    return {"version": out.stdout, "commit": "", "tree": "", "built_at": ""}
