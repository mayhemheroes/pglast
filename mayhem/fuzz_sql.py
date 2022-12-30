#!/usr/bin/env python3
import atheris
import sys
import fuzz_helpers

with atheris.instrument_imports(include=["pglast"]):
    from pglast import parse_sql, prettify

from pglast import Error

def TestOneInput(data):
    fdp = fuzz_helpers.EnhancedFuzzedDataProvider(data)
    try:
        if fdp.ConsumeBool():
            parse_sql(fdp.ConsumeRemainingString())
        else:
            prettify(fdp.ConsumeRemainingString())
    except (ValueError, Error):
        return -1
def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
