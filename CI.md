# Continuous Integration

The Endogenous Dynamics of the Continuum (EDK) repository uses GitHub Actions for automated Python validation, smoke testing, and executable module verification.

## CI Status

Current CI layers:

- EDK Validation — PASS
- EDK Module Execution — PASS
- Restore C^3 notation in Markdown — PASS

## EDK Validation

Workflow file:

`.github/workflows/edk-validation.yml`

The validation workflow performs:

- Python source compilation;
- full pytest execution;
- GPU mean-field phase engine smoke validation;
- hierarchical orchestrator smoke validation;
- Marnov retention-collapse protocol smoke validation;
- spatiotemporal phase-delay smoke validation;
- vortex phase-field smoke validation.

The workflow validates the repository with Python 3.11 on GitHub Actions.

Current status:

PASS

## EDK Module Execution

Workflow file:

`.github/workflows/edk-module-execution.yml`

The module-execution workflow independently executes the remaining repository modules through a GitHub Actions matrix.

Validated executable modules:

- Continuum Simulation;
- Impulse Transition;
- Poynting Flux Transition;
- Recursive Feedback Loop;
- Visual Protocol;
- Marnov Cubic Potential Visualizer;
- Framework Core;
- Marnov Reverse Decoder;
- Metric Bridge Solver;
- Molecular Phase Chemistry;
- Organic Matrix;
- Planetary Resonance;
- Solar Synthesis;
- Wave Genetics.

Each module is executed independently so that failure in one module does not prevent validation of the remaining matrix entries.

Current status:

PASS

## Retention-Collapse Protocol Correction

The Marnov retention-collapse protocol smoke test validates multi-tact critical exposure accumulation before phase-node unlock.

The validated smoke-test configuration uses:

`critical_exposure_threshold = 0.50`

This preserves the intended test sequence:

positive exposure accumulation → multi-tact persistence → threshold crossing → phase-node unlock

Current status:

PASS

## CI Trigger Conditions

The validation workflows run on:

- manual workflow dispatch;
- pushes to the `main` branch affecting Python files;
- pull requests to the `main` branch affecting Python files;
- changes to the corresponding workflow files.

## Validation Environment

Primary environment:

- GitHub Actions;
- Ubuntu latest runner;
- Python 3.11;
- repository root added to `PYTHONPATH`;
- non-interactive Matplotlib backend through `MPLBACKEND=Agg`.

Validation dependencies:

- NumPy;
- Matplotlib;
- pytest.

## Maintenance Workflow

Workflow file:

`.github/workflows/restore-cpow3.yml`

This workflow preserves the required `C^3` notation in Markdown documentation.

Current status:

PASS

## Final CI Result

The repository currently has two independent executable validation layers:

1. full Python test and smoke-test validation;
2. independent execution of the remaining executable modules.

Combined result:

PASS
