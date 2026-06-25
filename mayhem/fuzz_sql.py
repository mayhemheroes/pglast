#!/usr/bin/env python3
"""fuzz_sql.py — Atheris harness for pglast (lelit/pglast).

pglast is a thin Python wrapper around libpg_query, the actual PostgreSQL parser
exported as a CPython C extension (pglast.parser). Each input is split into a bool
selector + a string: half the inputs are fed to parse_sql (build the raw parse tree),
the other half to prettify (parse + reformat via the RawStream serializer). This drives
the C parser, the AST-node Python layer, and the SQL pretty-printer.

Expected, well-defined failures for arbitrary/garbage SQL — a parse error (pglast.Error,
raised by libpg_query on invalid syntax), a ValueError from the prettifier on an
unrepresentable node, or a CPython recursion-limit hit on pathologically nested SQL —
are caught and ignored: they are NOT defects. Anything else propagates so Atheris reports
it as a genuine crash.
"""
import sys

import atheris

import fuzz_helpers

with atheris.instrument_imports(include=["pglast"]):
    from pglast import parse_sql, prettify

from pglast import Error

# Normal outcomes of feeding arbitrary text as SQL — not bugs.
EXPECTED = (
    Error,            # pglast.Error / ParseError — libpg_query rejected the input
    ValueError,       # prettifier / RawStream on an unrepresentable construct
    RecursionError,   # CPython recursion limit on pathologically nested SQL
)


def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)
    try:
        if fdp.ConsumeBool():
            parse_sql(fdp.ConsumeRemainingString())
        else:
            prettify(fdp.ConsumeRemainingString())
    except EXPECTED:
        return -1


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
