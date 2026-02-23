from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, UTC
import hashlib
import math


@dataclass(slots=True)
class PhaseZeroSpec:
    """Initial parameter envelope for a ripple inverse-design seed."""

    wavelength_nm: float = 1550.0
    substrate_index: float = 1.44
    superstrate_index: float = 1.0
    period_nm: float = 620.0
    amplitude_nm: float = 80.0
    duty_cycle: float = 0.5

    def validate(self) -> None:
        if self.wavelength_nm <= 0:
            raise ValueError("wavelength_nm must be positive")
        if self.period_nm <= 0:
            raise ValueError("period_nm must be positive")
        if self.amplitude_nm <= 0:
            raise ValueError("amplitude_nm must be positive")
        if not 0 < self.duty_cycle < 1:
            raise ValueError("duty_cycle must be between 0 and 1")
        if self.substrate_index <= 1 or self.superstrate_index <= 0:
            raise ValueError("invalid refractive indices")


def _ripple_height(x_nm: float, spec: PhaseZeroSpec) -> float:
    return spec.amplitude_nm * math.sin(2 * math.pi * x_nm / spec.period_nm)


def _baseline_fom(spec: PhaseZeroSpec) -> float:
    """Simple phase-zero proxy FOM used before full-wave optimization.

    This bounded score rewards index contrast and penalizes aggressive ripple depth.
    """

    contrast = abs(spec.substrate_index - spec.superstrate_index)
    normalized_depth = spec.amplitude_nm / spec.wavelength_nm
    duty_bias = 1 - abs(spec.duty_cycle - 0.5) * 2
    score = (contrast * duty_bias) / (1 + normalized_depth**2)
    return round(max(0.0, min(1.0, score / 2.5)), 6)


def sign_clocking_report(report_text: str) -> dict[str, str]:
    digest = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
    return {
        "signed_at_utc": datetime.now(UTC).isoformat(),
        "sha256": digest,
    }


def run_phase_zero(spec: PhaseZeroSpec, *, sample_points: int = 64) -> dict:
    """Produce a deterministic phase-zero seed artifact for downstream solvers."""

    spec.validate()
    if sample_points < 8:
        raise ValueError("sample_points must be >= 8")

    x_step = spec.period_nm / (sample_points - 1)
    profile = []
    for i in range(sample_points):
        x_nm = i * x_step
        profile.append({"x_nm": round(x_nm, 6), "z_nm": round(_ripple_height(x_nm, spec), 6)})

    summary = (
        "phase_zero_seed|"
        f"wl={spec.wavelength_nm}|period={spec.period_nm}|amp={spec.amplitude_nm}|"
        f"n_sub={spec.substrate_index}|n_sup={spec.superstrate_index}|duty={spec.duty_cycle}"
    )

    return {
        "phase": "zero",
        "spec": {
            "wavelength_nm": spec.wavelength_nm,
            "period_nm": spec.period_nm,
            "amplitude_nm": spec.amplitude_nm,
            "substrate_index": spec.substrate_index,
            "superstrate_index": spec.superstrate_index,
            "duty_cycle": spec.duty_cycle,
        },
        "baseline_fom": _baseline_fom(spec),
        "profile": profile,
        "signature": sign_clocking_report(summary),
    }
