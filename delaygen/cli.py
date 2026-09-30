"""CLI : delaygen prepare | fit | eda | validate | allocate | sensitivity | tables"""
from __future__ import annotations

import argparse
import logging
import runpy
import sys


def main():
    ap = argparse.ArgumentParser(prog="delaygen")
    ap.add_argument("command", choices=["prepare", "fit", "eda", "validate", "allocate", "sensitivity", "tables", "literature"])
    ap.add_argument("rest", nargs=argparse.REMAINDER)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    mod = {"prepare": "delaygen.prepare", "fit": "delaygen.fit", "eda": "delaygen.analysis.eda",
           "validate": "delaygen.experiments.run_validation", "allocate": "delaygen.experiments.run_allocation",
           "sensitivity": "delaygen.experiments.run_sensitivity", "tables": "delaygen.experiments.make_tables",
           "literature": "delaygen.experiments.literature_table"}[a.command]
    sys.argv = [mod] + a.rest
    runpy.run_module(mod, run_name="__main__")


if __name__ == "__main__":
    main()
