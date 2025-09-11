from __future__ import annotations

import json
from pathlib import Path


def load_catalog() -> dict:
    path = Path("data/metrics_catalog.json")
    assert path.exists(), "metrics_catalog.json is missing"
    return json.loads(path.read_text(encoding="utf-8"))


def test_bun_conversions():
    tests = load_catalog()["tests"]
    bun = tests["BUN"]
    conv = bun["conversions"]
    assert conv.get("mg/dL->mmol/L") == 0.357
    assert conv.get("mmol/L->mg/dL") == 2.8


def test_creatinine_conversions():
    tests = load_catalog()["tests"]
    cr = tests["CREATININE"]
    conv = cr["conversions"]
    assert conv.get("mg/dL->umol/L") == 88.4
    assert round(conv.get("umol/L->mg/dL"), 5) == 0.01131
    aliases = set(cr["unit_aliases"])
    assert {"umol/L", "µmol/L"}.issubset(aliases)


def test_electrolyte_aliases():
    tests = load_catalog()["tests"]
    for code in ["SODIUM", "POTASSIUM", "CHLORIDE", "CARBON_DIOXIDE"]:
        t = tests[code]
        assert "mEq/L" in t["unit_aliases"]
        conv = t["conversions"]
        assert conv.get("mEq/L->mmol/L") == 1.0
        assert conv.get("mmol/L->mEq/L") == 1.0


def test_calcium_conversions():
    tests = load_catalog()["tests"]
    ca = tests["CALCIUM"]
    conv = ca["conversions"]
    assert conv.get("mg/dL->mmol/L") == 0.25
    assert conv.get("mmol/L->mg/dL") == 4.0


def test_protein_conversions():
    tests = load_catalog()["tests"]
    for code in ["PROTEIN_TOTAL", "ALBUMIN", "GLOBULIN"]:
        t = tests[code]
        conv = t["conversions"]
        assert conv.get("g/dL->g/L") == 10.0
        assert conv.get("g/L->g/dL") == 0.1


def test_bilirubin_conversions():
    tests = load_catalog()["tests"]
    for code in ["BILIRUBIN_TOTAL", "BILIRUBIN_DIRECT", "BILIRUBIN_INDIRECT"]:
        t = tests[code]
        conv = t["conversions"]
        assert conv.get("mg/dL->umol/L") == 17.1
        assert round(conv.get("umol/L->mg/dL"), 4) == 0.0585


def test_unitless_alias_arrays():
    tests = load_catalog()["tests"]
    for code in ["CHOL_HDL_RATIO", "LDL_HDL_RATIO", "A_G_RATIO"]:
        assert tests[code]["unit_aliases"] == []

