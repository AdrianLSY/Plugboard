#!/bin/sh
# Restore the staging database from the nightly dump.
set -eu

# The line as it was actually committed: the password is in the tree.
psql "postgres://plugboard:7Kq2Vt9Rw4Zx1Bn6@db.internal:5432/plugboard" < dump.sql

# The same command taking the value from the environment. A reference is not a
# disclosure, and a scanner that cannot tell them apart gets switched off.
psql "postgres://plugboard:${PGPASSWORD}@db.internal:5432/plugboard" < dump.sql

# And as a runbook writes it for a reader to fill in.
psql "postgres://plugboard:password@db.internal:5432/plugboard" < dump.sql
