#!/usr/bin/python3
"""run_tests.py — behavioral known-answer test (KAT) oracle for pglast.

Invoked via the `/mayhem/pglast-tests` ELF launcher (NOT directly), so the verify-repo
sabotage oracle can neuter the launcher and prove the test oracle is behavioral
(LD_PRELOAD _exit(0) kills the non-system launcher before python runs → no RUNTESTS
line → mayhem/test.sh fails).

These are EXACT-VALUE assertions, not "did it import / exit 0": real SQL is parsed and
pretty-printed and the EXACT serialized output is checked (keyword normalization, target
list / FROM / WHERE layout, operator rendering, JOIN expansion), the raw parse tree's node
types are checked, and invalid SQL is required to raise pglast's Error. A no-op /
behaviour-altering patch to libpg_query, the pglast.parser C extension or the RawStream
pretty-printer cannot pass it. Outputs captured from pglast v7.14.

Prints exactly one machine-readable line:

    RUNTESTS tests=<n> passed=<p> failed=<f> skipped=<s>

Exit 0 iff failed == 0. mayhem/test.sh parses that line into a CTRF report.
"""
from __future__ import annotations

import sys
import traceback

from pglast import parse_sql, prettify, Error


# --- known-answer cases ---------------------------------------------------------------

def t_prettify_select_simple():
    assert prettify("select 1") == "SELECT 1", prettify("select 1")


def t_prettify_select_where():
    # Target list one-per-line, lowercased keywords normalized to upper, `x=1` -> `x = 1`.
    expected = "SELECT a\n     , b\nFROM t\nWHERE x = 1"
    got = prettify("select a,b from t where x=1")
    assert got == expected, repr(got)


def t_prettify_insert():
    expected = "INSERT INTO t (a\n             , b)\nVALUES (1, 2)"
    got = prettify("insert into t(a,b) values (1,2)")
    assert got == expected, repr(got)


def t_prettify_join():
    # A bare `join` must expand to `INNER JOIN`, and the ON clause rendered.
    expected = "SELECT *\nFROM a\n     INNER JOIN b ON a.id = b.id"
    got = prettify("select * from a join b on a.id=b.id")
    assert got == expected, repr(got)


def t_parse_structure():
    # parse_sql returns a tuple of one RawStmt wrapping a SelectStmt.
    r = parse_sql("SELECT 1")
    assert isinstance(r, tuple), type(r)
    assert len(r) == 1, len(r)
    assert r[0].__class__.__name__ == "RawStmt", r[0].__class__.__name__
    assert r[0].stmt.__class__.__name__ == "SelectStmt", r[0].stmt.__class__.__name__


def t_parse_two_statements():
    # Two statements separated by ';' parse into two RawStmt nodes.
    r = parse_sql("SELECT 1; SELECT 2")
    assert len(r) == 2, len(r)


def t_syntax_error_raised():
    # Invalid SQL MUST raise pglast.Error (libpg_query's parser rejects it), not pass.
    try:
        parse_sql("SELEC 1 FORM t")
    except Error:
        return
    raise AssertionError("expected pglast.Error for invalid SQL 'SELEC 1 FORM t'")


TESTS = [
    t_prettify_select_simple,
    t_prettify_select_where,
    t_prettify_insert,
    t_prettify_join,
    t_parse_structure,
    t_parse_two_statements,
    t_syntax_error_raised,
]


def main() -> int:
    passed = failed = 0
    for t in TESTS:
        try:
            t()
            passed += 1
            print(f"PASS {t.__name__}")
        except Exception:
            failed += 1
            print(f"FAIL {t.__name__}")
            traceback.print_exc()
    total = passed + failed
    print(f"RUNTESTS tests={total} passed={passed} failed={failed} skipped=0")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
