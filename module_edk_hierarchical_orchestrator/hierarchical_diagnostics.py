from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence
import argparse
import json
import math
import re

import matplotlib.pyplot as plt
import numpy as np


STEP_PATTERN = re.compile(
    r"^hierarchical_step_(?P<tact>\d{6})\.json$"
)

FIELD_PATTERN = re.compile(
    r"^hierarchical_field_(?P<tact>\d{6})\.npz$"
)

EXPECTED_STAGE_ORDER: tuple[str, ...] = (
    "solar",
    "planetary",
    "bio_planetary",
    "continuum_core",
    "interface_tensor",
    "massless_exchange_channel",
    "wave_genetics",
    "molecular_phase_chemistry",
    "feedback",
)

DEFAULT_REQUIRED_FIELDS: tuple[str, ...] = (
    "Q_n",
    "D_n",
    "A_n",
    "P_t",
    "T_int",
    "J_flux",
)

SCALAR_DIAGNOSTIC_FIELDS: tuple[str, ...] = (
    "Q_n",
    "D_n",
    "A_n",
    "C_t",
    "C_proxy_t",
    "P_t",
    "retention_margin",
    "R_t_phase_order",
    "T_int",
    "J_flux",
    "M_t",
)


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass(frozen=True)
class DiagnosticIssue:
    severity: str
    code: str
    message: str
    tact_index: int | None = None
    field_name: str | None = None
    details: Mapping[str, Any] = field(
        default_factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "tact_index": self.tact_index,
            "field_name": self.field_name,
            "details": _json_safe(
                self.details
            ),
        }


@dataclass
class DiagnosticRecord:
    tact_index: int
    simulation_time: float
    status: str
    dynamic_regime: str

    state: dict[str, Any]
    feedback: dict[str, Any]
    module_states: dict[str, Any]

    transition_events: list[
        dict[str, Any]
    ]

    field_provenance: dict[
        str,
        Any,
    ]

    arrays: dict[
        str,
        np.ndarray,
    ]

    scalar_fields: dict[
        str,
        float | None,
    ]

    json_path: Path
    npz_path: Path | None

    def scalar(
        self,
        field_name: str,
    ) -> float | None:
        return self.scalar_fields.get(
            field_name
        )


@dataclass
class DiagnosticSummary:
    status: str

    record_count: int

    first_tact: int | None
    last_tact: int | None

    first_time: float | None
    last_time: float | None

    regime_counts: dict[
        str,
        int,
    ]

    issue_counts: dict[
        str,
        int,
    ]

    missing_tacts: list[int]

    missing_required_fields: dict[
        str,
        list[int],
    ]

    resonance_window_transition_count: int

    output_directory: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EDKHierarchicalDiagnostics:
    def __init__(
        self,
        input_directory: str | Path = (
            "edk_hierarchical_output"
        ),
        output_directory: (
            str | Path | None
        ) = None,
        *,
        required_fields: Sequence[str] = (
            DEFAULT_REQUIRED_FIELDS
        ),
        expected_stage_order: Sequence[str] = (
            EXPECTED_STAGE_ORDER
        ),
        strict: bool = False,
    ) -> None:
        self.input_directory = Path(
            input_directory
        )

        if output_directory is None:
            self.output_directory = (
                self.input_directory
                / "diagnostics"
            )
        else:
            self.output_directory = Path(
                output_directory
            )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.required_fields = tuple(
            required_fields
        )

        self.expected_stage_order = tuple(
            expected_stage_order
        )

        self.strict = bool(
            strict
        )

        self.records: list[
            DiagnosticRecord
        ] = []

        self.issues: list[
            DiagnosticIssue
        ] = []

    def load(
        self,
    ) -> list[DiagnosticRecord]:
        self.records = []
        self.issues = []

        if not self.input_directory.exists():
            raise FileNotFoundError(
                (
                    "Input directory does not "
                    "exist: "
                    f"{self.input_directory}"
                )
            )

        step_files = sorted(
            path
            for path
            in self.input_directory.iterdir()
            if (
                path.is_file()
                and STEP_PATTERN.match(
                    path.name
                )
            )
        )

        if not step_files:
            raise FileNotFoundError(
                (
                    "No hierarchical_step_*.json "
                    "files were found in "
                    f"{self.input_directory}"
                )
            )

        for step_path in step_files:
            self.records.append(
                self._load_record(
                    step_path
                )
            )

        self.records.sort(
            key=lambda item: (
                item.tact_index,
                item.simulation_time,
            )
        )

        return list(
            self.records
        )

    def run(
        self,
        *,
        create_plots: bool = True,
        create_report: bool = True,
    ) -> DiagnosticSummary:
        if not self.records:
            self.load()

        self._validate_sequence()

        self._validate_required_fields()

        self._validate_finite_values()

        self._validate_stage_continuity()

        self._validate_feedback_continuity()

        self._validate_provenance()

        self._validate_resonance_window_transitions()

        self._validate_inherited_qualitative_characteristics()

        if create_plots:
            self.create_all_plots()

        summary = self.build_summary()

        if create_report:
            self.write_report(
                summary
            )

        if self.strict:
            errors = [
                issue
                for issue
                in self.issues
                if (
                    issue.severity
                    == DiagnosticSeverity.ERROR.value
                )
            ]

            if errors:
                raise RuntimeError(
                    (
                        "Strict diagnostic mode "
                        f"detected {len(errors)} "
                        "error-level issues."
                    )
                )

        return summary

    def build_summary(
        self,
    ) -> DiagnosticSummary:
        regime_counts: dict[
            str,
            int,
        ] = {}

        for record in self.records:
            regime = (
                record.dynamic_regime
                or "UNDETERMINED"
            )

            regime_counts[
                regime
            ] = (
                regime_counts.get(
                    regime,
                    0,
                )
                + 1
            )

        issue_counts = {
            severity.value: sum(
                (
                    issue.severity
                    == severity.value
                )
                for issue
                in self.issues
            )
            for severity
            in DiagnosticSeverity
        }

        missing_required_fields: dict[
            str,
            list[int],
        ] = {}

        for field_name in self.required_fields:
            missing = [
                record.tact_index
                for record
                in self.records
                if not self._field_exists(
                    record,
                    field_name,
                )
            ]

            if missing:
                missing_required_fields[
                    field_name
                ] = missing

        transitions = sum(
            (
                issue.code
                == "RESONANCE_WINDOW_TRANSITION"
            )
            for issue
            in self.issues
        )

        if self.records:
            first = self.records[0]
            last = self.records[-1]

            first_tact = (
                first.tact_index
            )

            last_tact = (
                last.tact_index
            )

            first_time = (
                first.simulation_time
            )

            last_time = (
                last.simulation_time
            )

        else:
            first_tact = None
            last_tact = None
            first_time = None
            last_time = None

        status = "COMPLETED"

        if (
            issue_counts[
                DiagnosticSeverity.ERROR.value
            ]
            > 0
        ):
            status = "DIAGNOSTIC_ERRORS"

        elif (
            issue_counts[
                DiagnosticSeverity.WARNING.value
            ]
            > 0
        ):
            status = "DIAGNOSTIC_WARNINGS"

        return DiagnosticSummary(
            status=status,
            record_count=len(
                self.records
            ),
            first_tact=first_tact,
            last_tact=last_tact,
            first_time=first_time,
            last_time=last_time,
            regime_counts=regime_counts,
            issue_counts=issue_counts,
            missing_tacts=(
                self._missing_tacts()
            ),
            missing_required_fields=(
                missing_required_fields
            ),
            resonance_window_transition_count=(
                transitions
            ),
            output_directory=str(
                self.output_directory
            ),
        )

    def create_all_plots(
        self,
    ) -> list[Path]:
        if not self.records:
            raise RuntimeError(
                (
                    "No diagnostic records "
                    "are loaded."
                )
            )

        paths: list[Path] = []

        for field_name in (
            "Q_n",
            "D_n",
            "A_n",
        ):
            path = self._plot_single(
                field_name,
                title=field_name,
                ylabel=field_name,
            )

            if path is not None:
                paths.append(
                    path
                )

        path = self._plot_multiple(
            (
                "C_t",
                "C_proxy_t",
                "P_t",
            ),
            title=(
                "C(t), C_proxy(t), P(t)"
            ),
            ylabel=(
                "Operational value"
            ),
            filename=(
                "coherence_and_pressure.png"
            ),
        )

        if path is not None:
            paths.append(
                path
            )

        path = self._plot_single(
            "retention_margin",
            title=(
                "Retention margin"
            ),
            ylabel=(
                "C(t) - P(t)"
            ),
        )

        if path is not None:
            paths.append(
                path
            )

        path = self._plot_single(
            "R_t_phase_order",
            title=(
                "Phase-order parameter"
            ),
            ylabel=(
                "R_t_phase_order"
            ),
        )

        if path is not None:
            paths.append(
                path
            )

        path = self._plot_multiple(
            (
                "T_int",
                "J_flux",
                "M_t",
            ),
            title=(
                "T_int, J_flux, M(t)"
            ),
            ylabel=(
                "Scalar diagnostic reduction"
            ),
            filename=(
                "interface_flux_mass.png"
            ),
        )

        if path is not None:
            paths.append(
                path
            )

        paths.append(
            self.plot_dynamic_regime()
        )

        paths.append(
            self.plot_stage_continuity()
        )

        paths.append(
            self.plot_resonance_window_transitions()
        )

        return paths

    def plot_dynamic_regime(
        self,
    ) -> Path:
        mapping = {
            "DEGRADATION_DRIFT": -1.0,
            "ENDOGENOUS_DYNAMIC_CRITICALITY": 0.0,
            "ENDOGENOUS_DYNAMIC_STABILITY": 1.0,
            "UNDETERMINED": np.nan,
        }

        x_values = [
            record.simulation_time
            for record
            in self.records
        ]

        y_values = [
            mapping.get(
                record.dynamic_regime,
                np.nan,
            )
            for record
            in self.records
        ]

        path = (
            self.output_directory
            / "dynamic_regime.png"
        )

        figure, axis = plt.subplots(
            figsize=(10, 5)
        )

        axis.step(
            x_values,
            y_values,
            where="post",
        )

        axis.set_xlabel(
            "Simulation time"
        )

        axis.set_ylabel(
            "Dynamic regime"
        )

        axis.set_yticks(
            [
                -1.0,
                0.0,
                1.0,
            ]
        )

        axis.set_yticklabels(
            [
                "DEGRADATION_DRIFT",
                "ENDOGENOUS_DYNAMIC_CRITICALITY",
                "ENDOGENOUS_DYNAMIC_STABILITY",
            ]
        )

        axis.set_title(
            "Dynamic-regime transitions"
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        figure.tight_layout()

        figure.savefig(
            path,
            dpi=160,
        )

        plt.close(
            figure
        )

        return path

    def plot_stage_continuity(
        self,
    ) -> Path:
        stage_index = {
            stage: index
            for index, stage
            in enumerate(
                self.expected_stage_order
            )
        }

        path = (
            self.output_directory
            / "stage_continuity.png"
        )

        figure, axis = plt.subplots(
            figsize=(12, 6)
        )

        for record in self.records:
            stages = [
                stage
                for stage
                in self._executed_stages(
                    record
                )
                if stage
                in stage_index
            ]

            axis.scatter(
                [
                    record.tact_index
                ]
                * len(stages),
                [
                    stage_index[
                        stage
                    ]
                    for stage
                    in stages
                ],
                s=18,
            )

        axis.set_xlabel(
            "Tact index"
        )

        axis.set_ylabel(
            "Execution stage"
        )

        axis.set_yticks(
            list(
                stage_index.values()
            )
        )

        axis.set_yticklabels(
            list(
                stage_index.keys()
            )
        )

        axis.set_title(
            "Forward-cascade stage continuity"
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        figure.tight_layout()

        figure.savefig(
            path,
            dpi=160,
        )

        plt.close(
            figure
        )

        return path

    def plot_resonance_window_transitions(
        self,
    ) -> Path:
        state_values: dict[
            str,
            float,
        ] = {}

        x_values: list[float] = []
        y_values: list[float] = []

        for record in self.records:
            state_text = _stable_text(
                record.state.get(
                    "resonance_window_state"
                )
            )

            if state_text not in state_values:
                state_values[
                    state_text
                ] = float(
                    len(
                        state_values
                    )
                )

            x_values.append(
                record.simulation_time
            )

            y_values.append(
                state_values[
                    state_text
                ]
            )

        path = (
            self.output_directory
            / "resonance_window_transitions.png"
        )

        figure, axis = plt.subplots(
            figsize=(10, 5)
        )

        axis.step(
            x_values,
            y_values,
            where="post",
        )

        ordered = sorted(
            state_values.items(),
            key=lambda item: item[1],
        )

        axis.set_yticks(
            [
                value
                for _, value
                in ordered
            ]
        )

        axis.set_yticklabels(
            [
                label
                for label, _
                in ordered
            ]
        )

        axis.set_xlabel(
            "Simulation time"
        )

        axis.set_ylabel(
            "Resonance-window state"
        )

        axis.set_title(
            "Resonance-window transitions"
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        figure.tight_layout()

        figure.savefig(
            path,
            dpi=160,
        )

        plt.close(
            figure
        )

        return path

    def write_report(
        self,
        summary: (
            DiagnosticSummary | None
        ) = None,
    ) -> tuple[Path, Path]:
        if summary is None:
            summary = self.build_summary()

        json_path = (
            self.output_directory
            / "hierarchical_diagnostics.json"
        )

        markdown_path = (
            self.output_directory
            / "hierarchical_diagnostics.md"
        )

        payload = {
            "summary": (
                summary.to_dict()
            ),
            "issues": [
                issue.to_dict()
                for issue
                in self.issues
            ],
            "records": [
                {
                    "tact_index": (
                        record.tact_index
                    ),
                    "simulation_time": (
                        record.simulation_time
                    ),
                    "status": (
                        record.status
                    ),
                    "dynamic_regime": (
                        record.dynamic_regime
                    ),
                    "scalar_fields": (
                        record.scalar_fields
                    ),
                    "json_path": str(
                        record.json_path
                    ),
                    "npz_path": (
                        str(
                            record.npz_path
                        )
                        if (
                            record.npz_path
                            is not None
                        )
                        else None
                    ),
                }
                for record
                in self.records
            ],
        }

        with json_path.open(
            "w",
            encoding="utf-8",
        ) as handle:
            json.dump(
                _json_safe(
                    payload
                ),
                handle,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )

            handle.write(
                "\n"
            )

        markdown_path.write_text(
            self._markdown_report(
                summary
            ),
            encoding="utf-8",
        )

        return (
            json_path,
            markdown_path,
        )

    def _load_record(
        self,
        json_path: Path,
    ) -> DiagnosticRecord:
        match = STEP_PATTERN.match(
            json_path.name
        )

        if match is None:
            raise ValueError(
                (
                    "Unexpected step filename: "
                    f"{json_path.name}"
                )
            )

        filename_tact = int(
            match.group(
                "tact"
            )
        )

        with json_path.open(
            "r",
            encoding="utf-8",
        ) as handle:
            metadata = json.load(
                handle
            )

        if not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                (
                    "Step metadata must be "
                    "a JSON object: "
                    f"{json_path}"
                )
            )

        npz_candidate = (
            self.input_directory
            / (
                "hierarchical_field_"
                f"{filename_tact:06d}.npz"
            )
        )

        arrays: dict[
            str,
            np.ndarray,
        ] = {}

        npz_path: Path | None = None

        if npz_candidate.exists():
            npz_path = npz_candidate

            with np.load(
                npz_candidate,
                allow_pickle=False,
            ) as archive:
                arrays = {
                    key: np.asarray(
                        archive[
                            key
                        ]
                    )
                    for key
                    in archive.files
                }

        else:
            self._add_issue(
                DiagnosticSeverity.WARNING,
                "NPZ_SNAPSHOT_MISSING",
                (
                    "The NPZ field snapshot "
                    "is missing."
                ),
                tact_index=(
                    filename_tact
                ),
                details={
                    "json_path": str(
                        json_path
                    ),
                },
            )

        state = _mapping_copy(
            metadata.get(
                "state"
            )
        )

        feedback = _mapping_copy(
            metadata.get(
                "feedback"
            )
        )

        module_states = _mapping_copy(
            metadata.get(
                "module_states"
            )
        )

        transition_events = (
            _list_of_mappings(
                metadata.get(
                    "transition_events"
                )
            )
        )

        field_provenance = _mapping_copy(
            metadata.get(
                "field_provenance"
            )
        )

        tact_index = int(
            state.get(
                "tact_index",
                filename_tact,
            )
        )

        simulation_time = float(
            state.get(
                "simulation_time",
                float(
                    filename_tact
                ),
            )
        )

        status = str(
            metadata.get(
                "status",
                "UNKNOWN",
            )
        )

        dynamic_regime = str(
            state.get(
                "dynamic_regime",
                "UNDETERMINED",
            )
        )

        scalar_fields = {
            field_name: (
                self._extract_scalar(
                    field_name,
                    state=state,
                    feedback=feedback,
                    arrays=arrays,
                )
            )
            for field_name
            in SCALAR_DIAGNOSTIC_FIELDS
        }

        return DiagnosticRecord(
            tact_index=tact_index,
            simulation_time=(
                simulation_time
            ),
            status=status,
            dynamic_regime=(
                dynamic_regime
            ),
            state=state,
            feedback=feedback,
            module_states=(
                module_states
            ),
            transition_events=(
                transition_events
            ),
            field_provenance=(
                field_provenance
            ),
            arrays=arrays,
            scalar_fields=(
                scalar_fields
            ),
            json_path=json_path,
            npz_path=npz_path,
        )

    def _extract_scalar(
        self,
        field_name: str,
        *,
        state: Mapping[
            str,
            Any,
        ],
        feedback: Mapping[
            str,
            Any,
        ],
        arrays: Mapping[
            str,
            np.ndarray,
        ],
    ) -> float | None:
        for container in (
            state,
            feedback,
        ):
            if field_name in container:
                scalar = _scalar_from_value(
                    container[
                        field_name
                    ]
                )

                if scalar is not None:
                    return scalar

        array = self._find_array(
            arrays,
            field_name,
        )

        if array is None:
            return None

        return _scalar_from_array(
            array
        )

    @staticmethod
    def _find_array(
        arrays: Mapping[
            str,
            np.ndarray,
        ],
        field_name: str,
    ) -> np.ndarray | None:
        candidates = (
            f"state__{field_name}",
            f"payload__{field_name}",
            f"feedback__{field_name}",
            field_name,
        )

        for candidate in candidates:
            if candidate in arrays:
                return arrays[
                    candidate
                ]

        for key, value in arrays.items():
            if (
                key.endswith(
                    f"__{field_name}"
                )
                or key == field_name
            ):
                return value

        return None

    def _validate_sequence(
        self,
    ) -> None:
        seen: set[int] = set()

        previous: (
            DiagnosticRecord | None
        ) = None

        for record in self.records:
            if record.tact_index in seen:
                self._add_issue(
                    DiagnosticSeverity.ERROR,
                    "DUPLICATE_TACT_INDEX",
                    (
                        "Duplicate tact index "
                        "detected."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                )

            seen.add(
                record.tact_index
            )

            if previous is not None:
                if (
                    record.tact_index
                    <= previous.tact_index
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        (
                            "NON_MONOTONIC_"
                            "TACT_INDEX"
                        ),
                        (
                            "Tact indices are not "
                            "strictly increasing."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                    )

                if (
                    record.simulation_time
                    <= previous.simulation_time
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        (
                            "NON_MONOTONIC_"
                            "SIMULATION_TIME"
                        ),
                        (
                            "Simulation time is not "
                            "strictly increasing."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                    )

            previous = record

        for tact_index in self._missing_tacts():
            self._add_issue(
                DiagnosticSeverity.WARNING,
                "TACT_GAP",
                (
                    "A tact index is missing "
                    "from the sequence."
                ),
                tact_index=tact_index,
            )

    def _validate_required_fields(
        self,
    ) -> None:
        for record in self.records:
            for field_name in self.required_fields:
                if self._field_exists(
                    record,
                    field_name,
                ):
                    continue

                if field_name == "T_int":
                    code = (
                        "T_INT_MISSING"
                    )

                elif field_name == "J_flux":
                    code = (
                        "J_FLUX_MISSING"
                    )

                else:
                    code = (
                        "MANDATORY_FIELD_MISSING"
                    )

                self._add_issue(
                    DiagnosticSeverity.ERROR,
                    code,
                    (
                        "A mandatory integration "
                        "field is missing."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    field_name=(
                        field_name
                    ),
                )

    def _validate_finite_values(
        self,
    ) -> None:
        for record in self.records:
            for (
                field_name,
                scalar,
            ) in (
                record.scalar_fields.items()
            ):
                if (
                    scalar is not None
                    and not math.isfinite(
                        scalar
                    )
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        "NON_FINITE_SCALAR",
                        (
                            "A scalar diagnostic "
                            "field is non-finite."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                        details={
                            "value": scalar,
                        },
                    )

            for (
                field_name,
                array,
            ) in (
                record.arrays.items()
            ):
                if not np.all(
                    np.isfinite(
                        array
                    )
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        "NON_FINITE_ARRAY",
                        (
                            "A numerical field "
                            "contains non-finite "
                            "values."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                        details={
                            "shape": list(
                                array.shape
                            ),
                            "dtype": str(
                                array.dtype
                            ),
                        },
                    )

    def _validate_stage_continuity(
        self,
    ) -> None:
        stage_index = {
            stage: index
            for index, stage
            in enumerate(
                self.expected_stage_order
            )
        }

        for record in self.records:
            stages = self._executed_stages(
                record
            )

            if not stages:
                self._add_issue(
                    DiagnosticSeverity.WARNING,
                    (
                        "NO_EXECUTED_"
                        "STAGE_EVENTS"
                    ),
                    (
                        "No executed-stage events "
                        "were found for this tact."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                )

                continue

            unknown = [
                stage
                for stage
                in stages
                if stage
                not in stage_index
            ]

            if unknown:
                self._add_issue(
                    DiagnosticSeverity.WARNING,
                    (
                        "UNKNOWN_EXECUTION_STAGE"
                    ),
                    (
                        "Unknown execution stages "
                        "were recorded."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    details={
                        "unknown_stages": unknown,
                    },
                )

            known = [
                stage
                for stage
                in stages
                if stage
                in stage_index
            ]

            indices = [
                stage_index[
                    stage
                ]
                for stage
                in known
            ]

            if indices != sorted(
                indices
            ):
                self._add_issue(
                    DiagnosticSeverity.ERROR,
                    (
                        "STAGE_ORDER_VIOLATION"
                    ),
                    (
                        "Forward-cascade stages "
                        "were executed out of order."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    details={
                        "executed_stages": known,
                    },
                )

    def _validate_feedback_continuity(
        self,
    ) -> None:
        for record in self.records:
            for field_name in (
                "D_n",
                "A_n",
                "T_int",
                "J_flux",
            ):
                if not self._field_exists(
                    record,
                    field_name,
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        (
                            "FEEDBACK_FIELD_MISSING"
                        ),
                        (
                            "A required feedback "
                            "field is missing."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                    )

            module_feedback = (
                record.feedback.get(
                    "module_feedback"
                )
            )

            if (
                module_feedback is not None
                and not isinstance(
                    module_feedback,
                    Mapping,
                )
            ):
                self._add_issue(
                    DiagnosticSeverity.ERROR,
                    (
                        "INVALID_MODULE_FEEDBACK"
                    ),
                    (
                        "module_feedback must "
                        "be a mapping."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                )

    def _validate_provenance(
        self,
    ) -> None:
        for record in self.records:
            for field_name in self.required_fields:
                provenance = (
                    record.field_provenance.get(
                        field_name
                    )
                )

                if provenance is None:
                    self._add_issue(
                        DiagnosticSeverity.WARNING,
                        (
                            "FIELD_PROVENANCE_MISSING"
                        ),
                        (
                            "Field provenance "
                            "is missing."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                    )

                    continue

                if not isinstance(
                    provenance,
                    Mapping,
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        (
                            "INVALID_FIELD_PROVENANCE"
                        ),
                        (
                            "Field provenance "
                            "must be a mapping."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                    )

                    continue

                provenance_tact = (
                    provenance.get(
                        "tact_index"
                    )
                )

                if (
                    provenance_tact is not None
                    and int(
                        provenance_tact
                    )
                    > record.tact_index
                ):
                    self._add_issue(
                        DiagnosticSeverity.ERROR,
                        (
                            "PROVENANCE_FROM_"
                            "FUTURE_TACT"
                        ),
                        (
                            "Field provenance points "
                            "to a future tact."
                        ),
                        tact_index=(
                            record.tact_index
                        ),
                        field_name=(
                            field_name
                        ),
                        details={
                            "provenance_tact": (
                                provenance_tact
                            ),
                        },
                    )

    def _validate_resonance_window_transitions(
        self,
    ) -> None:
        previous_state: Any = None

        previous_tact: (
            int | None
        ) = None

        for record in self.records:
            current_state = (
                record.state.get(
                    "resonance_window_state"
                )
            )

            if (
                previous_tact is not None
                and not _values_equivalent(
                    previous_state,
                    current_state,
                )
            ):
                self._add_issue(
                    DiagnosticSeverity.INFO,
                    (
                        "RESONANCE_WINDOW_"
                        "TRANSITION"
                    ),
                    (
                        "A resonance-window state "
                        "transition was detected."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    field_name=(
                        "resonance_window_state"
                    ),
                    details={
                        "from_tact": (
                            previous_tact
                        ),
                        "from_state": (
                            _json_safe(
                                previous_state
                            )
                        ),
                        "to_state": (
                            _json_safe(
                                current_state
                            )
                        ),
                    },
                )

            previous_state = current_state

            previous_tact = (
                record.tact_index
            )

    def _validate_inherited_qualitative_characteristics(
        self,
    ) -> None:
        previous_value: Any = None

        previous_tact: (
            int | None
        ) = None

        for record in self.records:
            value = record.state.get(
                (
                    "inherited_qualitative_"
                    "characteristics"
                ),
                record.feedback.get(
                    (
                        "inherited_qualitative_"
                        "characteristics"
                    )
                ),
            )

            if value is None:
                self._add_issue(
                    DiagnosticSeverity.WARNING,
                    (
                        "INHERITED_QUALITATIVE_"
                        "CHARACTERISTICS_MISSING"
                    ),
                    (
                        "Inherited qualitative "
                        "characteristics are missing."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    field_name=(
                        "inherited_qualitative_"
                        "characteristics"
                    ),
                )

            if (
                previous_tact is not None
                and previous_value is not None
                and value is not None
                and _values_equivalent(
                    previous_value,
                    value,
                )
            ):
                self._add_issue(
                    DiagnosticSeverity.INFO,
                    (
                        "QUALITATIVE_"
                        "CHARACTERISTICS_RETAINED"
                    ),
                    (
                        "Inherited qualitative "
                        "characteristics were retained "
                        "between consecutive tacts."
                    ),
                    tact_index=(
                        record.tact_index
                    ),
                    details={
                        "from_tact": (
                            previous_tact
                        ),
                    },
                )

            previous_value = value

            previous_tact = (
                record.tact_index
            )

    def _field_exists(
        self,
        record: DiagnosticRecord,
        field_name: str,
    ) -> bool:
        if (
            field_name in record.state
            and record.state[
                field_name
            ]
            is not None
        ):
            return True

        if (
            field_name in record.feedback
            and record.feedback[
                field_name
            ]
            is not None
        ):
            return True

        return (
            self._find_array(
                record.arrays,
                field_name,
            )
            is not None
        )

    @staticmethod
    def _executed_stages(
        record: DiagnosticRecord,
    ) -> list[str]:
        return [
            str(
                event[
                    "stage_name"
                ]
            )
            for event
            in record.transition_events
            if (
                event.get(
                    "event"
                )
                == "MODULE_EXECUTED"
                and event.get(
                    "stage_name"
                )
                is not None
            )
        ]

    def _missing_tacts(
        self,
    ) -> list[int]:
        if not self.records:
            return []

        indices = {
            record.tact_index
            for record
            in self.records
        }

        return [
            tact_index
            for tact_index
            in range(
                min(
                    indices
                ),
                max(
                    indices
                )
                + 1,
            )
            if tact_index
            not in indices
        ]

    def _plot_single(
        self,
        field_name: str,
        *,
        title: str,
        ylabel: str,
    ) -> Path | None:
        points = [
            (
                record.simulation_time,
                record.scalar(
                    field_name
                ),
            )
            for record
            in self.records
            if (
                record.scalar(
                    field_name
                )
                is not None
            )
        ]

        if not points:
            return None

        path = (
            self.output_directory
            / f"{field_name}.png"
        )

        figure, axis = plt.subplots(
            figsize=(10, 5)
        )

        axis.plot(
            [
                point[0]
                for point
                in points
            ],
            [
                point[1]
                for point
                in points
            ],
            marker="o",
            markersize=3,
        )

        axis.set_xlabel(
            "Simulation time"
        )

        axis.set_ylabel(
            ylabel
        )

        axis.set_title(
            title
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        figure.tight_layout()

        figure.savefig(
            path,
            dpi=160,
        )

        plt.close(
            figure
        )

        return path

    def _plot_multiple(
        self,
        field_names: Sequence[str],
        *,
        title: str,
        ylabel: str,
        filename: str,
    ) -> Path | None:
        x_values = [
            record.simulation_time
            for record
            in self.records
        ]

        series: dict[
            str,
            list[float],
        ] = {}

        for field_name in field_names:
            values = [
                (
                    record.scalar(
                        field_name
                    )
                    if (
                        record.scalar(
                            field_name
                        )
                        is not None
                    )
                    else np.nan
                )
                for record
                in self.records
            ]

            if not all(
                np.isnan(
                    value
                )
                for value
                in values
            ):
                series[
                    field_name
                ] = values

        if not series:
            return None

        path = (
            self.output_directory
            / filename
        )

        figure, axis = plt.subplots(
            figsize=(10, 5)
        )

        for (
            field_name,
            values,
        ) in series.items():
            axis.plot(
                x_values,
                values,
                marker="o",
                markersize=3,
                label=field_name,
            )

        axis.set_xlabel(
            "Simulation time"
        )

        axis.set_ylabel(
            ylabel
        )

        axis.set_title(
            title
        )

        axis.grid(
            True,
            alpha=0.3,
        )

        axis.legend()

        figure.tight_layout()

        figure.savefig(
            path,
            dpi=160,
        )

        plt.close(
            figure
        )

        return path

    def _markdown_report(
        self,
        summary: DiagnosticSummary,
    ) -> str:
        lines = [
            "# EDK Hierarchical Diagnostics",
            "",
            "## Summary",
            "",
            (
                f"- Status: `{summary.status}`"
            ),
            (
                "- Records: "
                f"`{summary.record_count}`"
            ),
            (
                "- First tact: "
                f"`{summary.first_tact}`"
            ),
            (
                "- Last tact: "
                f"`{summary.last_tact}`"
            ),
            (
                "- First time: "
                f"`{summary.first_time}`"
            ),
            (
                "- Last time: "
                f"`{summary.last_time}`"
            ),
            (
                "- Resonance-window "
                "transitions: "
                f"`{summary.resonance_window_transition_count}`"
            ),
            "",
            "## Dynamic Regimes",
            "",
        ]

        for (
            regime,
            count,
        ) in sorted(
            summary.regime_counts.items()
        ):
            lines.append(
                f"- `{regime}`: `{count}`"
            )

        lines.extend(
            [
                "",
                "## Diagnostic Issues",
                "",
            ]
        )

        if not self.issues:
            lines.append(
                (
                    "No diagnostic issues "
                    "were recorded."
                )
            )

        else:
            for issue in self.issues:
                location = ""

                if (
                    issue.tact_index
                    is not None
                ):
                    location += (
                        " tact="
                        f"{issue.tact_index}"
                    )

                if (
                    issue.field_name
                    is not None
                ):
                    location += (
                        " field="
                        f"{issue.field_name}"
                    )

                lines.append(
                    (
                        f"- `{issue.severity}` "
                        f"`{issue.code}`"
                        f"{location}: "
                        f"{issue.message}"
                    )
                )

        lines.extend(
            [
                "",
                "## Missing Tacts",
                "",
                (
                    str(
                        summary.missing_tacts
                    )
                    if (
                        summary.missing_tacts
                    )
                    else "None"
                ),
                "",
                (
                    "## Missing Required "
                    "Fields"
                ),
                "",
                (
                    json.dumps(
                        (
                            summary
                            .missing_required_fields
                        ),
                        ensure_ascii=False,
                        indent=2,
                        sort_keys=True,
                    )
                    if (
                        summary
                        .missing_required_fields
                    )
                    else "None"
                ),
                "",
            ]
        )

        return "\n".join(
            lines
        )

    def _add_issue(
        self,
        severity: DiagnosticSeverity,
        code: str,
        message: str,
        *,
        tact_index: int | None = None,
        field_name: str | None = None,
        details: (
            Mapping[str, Any] | None
        ) = None,
    ) -> None:
        self.issues.append(
            DiagnosticIssue(
                severity=severity.value,
                code=code,
                message=message,
                tact_index=tact_index,
                field_name=field_name,
                details=dict(
                    details or {}
                ),
            )
        )


def _mapping_copy(
    value: Any,
) -> dict[str, Any]:
    if not isinstance(
        value,
        Mapping,
    ):
        return {}

    return {
        str(
            key
        ): item
        for key, item
        in value.items()
    }


def _list_of_mappings(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(
        value,
        list,
    ):
        return []

    return [
        {
            str(
                key
            ): nested
            for key, nested
            in item.items()
        }
        for item
        in value
        if isinstance(
            item,
            Mapping,
        )
    ]


def _scalar_from_value(
    value: Any,
) -> float | None:
    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return float(
            value
        )

    if isinstance(
        value,
        (
            int,
            float,
            np.generic,
        ),
    ):
        return float(
            value
        )

    if isinstance(
        value,
        complex,
    ):
        return float(
            abs(
                value
            )
        )

    if isinstance(
        value,
        Mapping,
    ):
        if value.get(
            "__array__"
        ):
            return None

        if (
            "real" in value
            and "imag" in value
        ):
            try:
                return float(
                    abs(
                        complex(
                            float(
                                value[
                                    "real"
                                ]
                            ),
                            float(
                                value[
                                    "imag"
                                ]
                            ),
                        )
                    )
                )

            except (
                TypeError,
                ValueError,
            ):
                return None

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        try:
            return _scalar_from_array(
                np.asarray(
                    value,
                    dtype=float,
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    return None


def _scalar_from_array(
    array: np.ndarray,
) -> float | None:
    if array.size == 0:
        return None

    if np.iscomplexobj(
        array
    ):
        return float(
            np.mean(
                np.abs(
                    array
                )
            )
        )

    return float(
        np.mean(
            array
        )
    )


def _stable_text(
    value: Any,
) -> str:
    if value is None:
        return "UNDEFINED"

    if isinstance(
        value,
        str,
    ):
        return value

    return json.dumps(
        _json_safe(
            value
        ),
        ensure_ascii=False,
        sort_keys=True,
    )


def _values_equivalent(
    left: Any,
    right: Any,
) -> bool:
    if (
        left is None
        and right is None
    ):
        return True

    if (
        left is None
        or right is None
    ):
        return False

    try:
        left_array = np.asarray(
            left
        )

        right_array = np.asarray(
            right
        )

        if (
            left_array.shape
            == right_array.shape
            and left_array.dtype.kind
            in "biufc"
            and right_array.dtype.kind
            in "biufc"
        ):
            return bool(
                np.allclose(
                    left_array,
                    right_array,
                    equal_nan=True,
                )
            )

    except (
        TypeError,
        ValueError,
    ):
        pass

    return (
        _stable_text(
            left
        )
        == _stable_text(
            right
        )
    )


def _json_safe(
    value: Any,
) -> Any:
    if value is None:
        return None

    if isinstance(
        value,
        Enum,
    ):
        return value.value

    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(
                key
            ): _json_safe(
                item
            )
            for key, item
            in value.items()
        }

    if isinstance(
        value,
        (
            list,
            tuple,
            set,
        ),
    ):
        return [
            _json_safe(
                item
            )
            for item
            in value
        ]

    if isinstance(
        value,
        np.ndarray,
    ):
        if value.ndim == 0:
            return _json_safe(
                value.item()
            )

        return {
            "__array__": True,
            "dtype": str(
                value.dtype
            ),
            "shape": list(
                value.shape
            ),
            "mean": (
                _scalar_from_array(
                    value
                )
            ),
        }

    if isinstance(
        value,
        np.generic,
    ):
        return _json_safe(
            value.item()
        )

    if isinstance(
        value,
        complex,
    ):
        return {
            "real": value.real,
            "imag": value.imag,
        }

    if isinstance(
        value,
        Path,
    ):
        return str(
            value
        )

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    return repr(
        value
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run diagnostics for EDK "
            "hierarchical orchestrator output."
        )
    )

    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path(
            "edk_hierarchical_output"
        ),
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--strict",
        action="store_true",
    )

    parser.add_argument(
        "--no-plots",
        action="store_true",
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
    )

    arguments = parser.parse_args()

    diagnostics = (
        EDKHierarchicalDiagnostics(
            input_directory=(
                arguments.input_dir
            ),
            output_directory=(
                arguments.output_dir
            ),
            strict=(
                arguments.strict
            ),
        )
    )

    summary = diagnostics.run(
        create_plots=(
            not arguments.no_plots
        ),
        create_report=(
            not arguments.no_report
        ),
    )

    print(
        json.dumps(
            summary.to_dict(),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
