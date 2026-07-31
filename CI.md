# Continuous Integration

[![EDK Stress and Scaling Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-stress-scaling-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-stress-scaling-validation.yml)
[![EDK Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml)
[![EDK Module Execution](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml)
[![EDK Artifact Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml)
[![EDK Python Compatibility](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-python-compatibility.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-python-compatibility.yml)

The Endogenous Dynamics of the Continuum (EDK) repository uses five independent GitHub Actions validation layers.

## EDK Stress and Scaling Validation

Workflow:

`.github/workflows/edk-stress-scaling-validation.yml`

Validates:

- eight sustained numerical stress configurations;
- domain counts from 32 to 1024;
- `float32` and `float64` execution;
- finite metrics and finite field arrays;
- wrapped phase bounds;
- amplitude bounds;
- tact and simulation-time continuity;
- linear state-memory scaling from 32 to 2048 domains.

## EDK Validation

Workflow:

`.github/workflows/edk-validation.yml`

Validates:

- Python source compilation;
- full pytest execution;
- GPU mean-field phase engine smoke test;
- hierarchical orchestrator smoke test;
- Marnov retention-collapse protocol smoke test;
- spatiotemporal phase-delay smoke test;
- vortex phase-field smoke test.

## EDK Module Execution

Workflow:

`.github/workflows/edk-module-execution.yml`

Independently executes:

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

Each module is executed as an independent GitHub Actions matrix job.

## EDK Artifact Validation

Workflow:

`.github/workflows/edk-artifact-validation.yml`

Validates:

- core CLI interfaces;
- generated JSON artifacts;
- generated NPZ artifacts;
- required JSON fields;
- required NPZ arrays;
- empty artifact detection;
- finite numeric values;
- NPZ loading with `allow_pickle=False`;
- object-dtype rejection;
- temporary-file residue detection;
- deterministic seeded replay equivalence;
- repository integrity through `git diff --exit-code`.

## EDK Python Compatibility

Workflow:

`.github/workflows/edk-python-compatibility.yml`

Validates:

- supported Python-version matrix execution;
- Python source compilation;
- full pytest execution;
- smoke-test execution across the compatibility matrix;
- dependency installation and package consistency.

## Validation Environment

- GitHub Actions;
- Ubuntu runner;
- Python version matrix defined by the compatibility workflow;
- Python 3.11 for the primary validation workflows;
- NumPy;
- Matplotlib;
- pytest.

## CI Structure

EDK Stress and Scaling Validation
→ sustained numerical stress
→ state-memory scaling

EDK Validation
→ compilation
→ pytest
→ smoke tests

EDK Module Execution
→ independent executable-module validation

EDK Artifact Validation
→ artifact generation
→ structure validation
→ numeric validation
→ deterministic replay
→ repository integrity

EDK Python Compatibility
→ Python-version matrix
→ compilation
→ pytest
→ smoke tests
