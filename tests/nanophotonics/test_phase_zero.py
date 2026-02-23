from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.health_report.nanophotonics.phase_zero import (
    PhaseZeroSpec,
    run_phase_zero,
    run_phase_zero_from_report,
)


def test_run_phase_zero_structure():
    result = run_phase_zero(PhaseZeroSpec(), sample_points=16)

    assert result["phase"] == "zero"
    assert len(result["profile"]) == 16
    assert 0.0 <= result["baseline_fom"] <= 1.0
    assert "sha256" in result["signature"]


def test_run_phase_zero_validation():
    bad = PhaseZeroSpec(duty_cycle=1.2)
    try:
        run_phase_zero(bad)
    except ValueError as exc:
        assert "duty_cycle" in str(exc)
    else:
        raise AssertionError("Expected ValueError for invalid duty_cycle")


def test_run_phase_zero_from_report():
    out = run_phase_zero_from_report("REPORT_INVERSE_DESIGN_CLOAKING.md")
    assert out["phase"] == "zero"
    assert len(out["profile"]) == 64
    assert out["spec"]["period_nm"] == 620.0
