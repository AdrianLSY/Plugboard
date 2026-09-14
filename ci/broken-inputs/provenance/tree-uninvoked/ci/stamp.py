"""A correct one place that nothing in this tree ever runs."""
import subprocess

FIELDS = ("version", "commit", "tree", "built_at")


def values():
    out = subprocess.run(["git", "describe"], capture_output=True)
    return {"version": out.stdout, "commit": "", "tree": "", "built_at": ""}
