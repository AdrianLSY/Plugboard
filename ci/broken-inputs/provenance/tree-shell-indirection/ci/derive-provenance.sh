#!/bin/sh
# A second derivation, one file sideways from anything the gate used to read.
# It asks for the SHORT hash where the one place asks for the full one, so the
# two disagree about what "the commit" means while each stays self-consistent.
git rev-parse --short HEAD
