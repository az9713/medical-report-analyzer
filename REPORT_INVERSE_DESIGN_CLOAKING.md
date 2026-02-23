# REPORT_INVERSE_DESIGN_CLOAKING

## Phase 0 — Problem Framing + Seed Generation

Phase 0 defines the deterministic initialization envelope used by downstream inverse-design solvers.

```yaml
phase: 0
seed:
  wavelength_nm: 1550.0
  substrate_index: 1.44
  superstrate_index: 1.0
  period_nm: 620.0
  amplitude_nm: 80.0
  duty_cycle: 0.5
  sample_points: 64
deliverables:
  - validated_seed
  - ripple_profile
  - baseline_fom
  - signed_clocking
```

### Acceptance Criteria
1. Seed parameters validate against physical sanity checks.
2. Ripple profile is deterministic for identical input values.
3. Baseline FOM is bounded to `[0, 1]` and reproducible.
4. Signed clocking metadata includes SHA-256 digest and UTC timestamp.
