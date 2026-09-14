"""The one place, with the derivation moved out of it.

The shape still looks right -- the fields are all here, the function is still
called values() -- and every component still compiles. They just all report
`unknown`. This is the case the first version of this gate could not detect at
all, because it only ever looked for a SECOND derivation.
"""

FIELDS = ("version", "commit", "tree", "built_at")


def values():
    return {f: "unknown" for f in FIELDS}
