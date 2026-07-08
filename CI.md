# Continuous Integration

[![EDK Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-validation.yml)
[![EDK Module Execution](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-module-execution.yml)
[![EDK Artifact Validation](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml/badge.svg)](https://github.com/maximumberlin76-gif/Endogenous-Dynamics-of-the-Continuum/actions/workflows/edk-artifact-validation.yml)

The Endogenous Dynamics of the Continuum (EDK) repository uses three independent GitHub Actions validation layers.

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

## Validation Environment

- GitHub Actions;
- Ubuntu runner;
- Python 3.11;
- NumPy;
- Matplotlib;
- pytest.

## CI Structure

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
