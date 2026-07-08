# Continuous Integration

[![EDK Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml)
[![EDK Module Execution](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml)
[![EDK Artifact Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml)

The Endogenous Dynamics of the Continuum (EDK) repository uses GitHub Actions for automated Python validation, executable module verification, structured artifact validation, and deterministic replay checks.

## CI Validation Architecture

The repository currently uses three independent executable validation layers:

1. EDK Validation;
2. EDK Module Execution;
3. EDK Artifact Validation.

These layers validate different parts of the repository and are kept separate so that test-suite validation, independent module execution, and generated-artifact validation remain individually observable.

## 1. EDK Validation

Workflow file:

`.github/workflows/edk-validation.yml`

The EDK Validation workflow performs:

- Python source compilation;
- full pytest execution;
- GPU mean-field phase engine smoke validation;
- hierarchical orchestrator smoke validation;
- Marnov retention-collapse protocol smoke validation;
- spatiotemporal phase-delay smoke validation;
- vortex phase-field smoke validation.

The workflow runs in a clean GitHub-hosted Ubuntu environment with Python 3.11.

### Retention-Collapse Protocol Correction

The Marnov retention-collapse protocol smoke test validates multi-tact critical exposure accumulation before phase-node unlock.

The validated smoke-test configuration uses:

`critical_exposure_threshold = 0.50`

This preserves the intended validation sequence:

positive exposure accumulation → multi-tact persistence → threshold crossing → phase-node unlock

## 2. EDK Module Execution

Workflow file:

`.github/workflows/edk-module-execution.yml`

The EDK Module Execution workflow independently executes repository modules through a GitHub Actions matrix.

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

Each module is executed as an independent matrix job.

The matrix uses:

`fail-fast: false`

This allows all module jobs to complete even if an individual matrix entry fails.

## 3. EDK Artifact Validation

Workflow file:

`.github/workflows/edk-artifact-validation.yml`

The EDK Artifact Validation workflow validates generated machine-readable outputs rather than only checking whether executable scripts terminate successfully.

The workflow performs:

- dependency installation validation through `pip check`;
- core CLI interface validation;
- deterministic GPU mean-field artifact generation;
- repeated seeded execution;
- spatiotemporal phase-delay artifact generation;
- vortex phase-field artifact generation;
- JSON artifact validation;
- NPZ artifact validation;
- required field validation;
- required array validation;
- empty artifact detection;
- non-finite numeric value detection;
- object-dtype rejection in NPZ arrays;
- temporary-file residue detection;
- exact deterministic replay comparison;
- repository mutation detection.

### Deterministic Replay Validation

The GPU mean-field reference execution is run twice with the same configuration and seed.

Validated seed:

`76`

The two generated artifact directories are compared directly.

The validation requires exact replay equivalence.

### Structured Artifact Validation

Generated JSON artifacts are checked for:

- valid JSON decoding;
- object root structure;
- required top-level keys;
- non-empty files;
- finite numeric values.

Generated NPZ artifacts are checked for:

- successful loading with `allow_pickle=False`;
- required array presence;
- non-empty arrays;
- prohibited object dtype;
- finite numeric values.

### Repository Integrity Validation

After all artifact-generation and validation stages, the workflow executes:

`git diff --exit-code`

This verifies that validation does not modify tracked repository content.

## Validation Environment

Primary CI environment:

- GitHub Actions;
- GitHub-hosted Ubuntu runner;
- Python 3.11;
- repository root available through `PYTHONPATH`;
- non-interactive Matplotlib backend through `MPLBACKEND=Agg`.

Primary validation dependencies:

- NumPy;
- Matplotlib;
- pytest.

## Trigger Conditions

The executable validation workflows support:

- manual workflow dispatch;
- pushes to the `main` branch affecting Python files;
- pull requests to the `main` branch affecting Python files;
- changes to the corresponding workflow file.

## Documentation Maintenance Workflow

Workflow file:

`.github/workflows/restore-cpow3.yml`

This workflow preserves the required `C^3` notation in Markdown documentation.

It is a documentation-maintenance workflow and is not part of the three executable test badges.

## Validation Coverage

The current CI architecture confirms:

- Python source compilation;
- pytest execution;
- five dedicated smoke-test paths;
- independent execution of fourteen repository modules;
- real JSON artifact generation;
- real NPZ artifact generation;
- artifact structure and numeric-integrity validation;
- deterministic seeded replay equivalence;
- absence of validation-generated repository changes.

## Final CI Structure

EDK Validation  
→ source compilation  
→ pytest  
→ smoke tests

EDK Module Execution  
→ independent executable-module matrix

EDK Artifact Validation  
→ generated artifacts  
→ structural validation  
→ numeric validation  
→ deterministic replay  
→ repository integrity

The three executable CI layers are independently visible through GitHub Actions and their status badges.
