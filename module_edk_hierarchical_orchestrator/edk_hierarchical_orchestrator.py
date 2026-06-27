from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    MutableMapping,
    Protocol,
    Sequence,
    runtime_checkable,
)
import argparse
import copy
import importlib
import inspect
import json
import math
import os
import tempfile

import numpy as np


STAGE_ORDER: tuple[str, ...] = (
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

DEFAULT_REQUIRED_STAGES: tuple[str, ...] = STAGE_ORDER

MANDATORY_INTEGRATION_FIELDS: tuple[str, ...] = (
    "Q_n",
    "D_n",
    "A_n",
    "P_t",
    "T_int",
    "J_flux",
)


class ExecutionMode(str, Enum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    DIAGNOSTIC = "diagnostic"


class RunStatus(str, Enum):
    COMPLETED = "COMPLETED"
    MODULE_REGISTRATION_FAILED = "MODULE_REGISTRATION_FAILED"
    INTERFACE_VALIDATION_FAILED = "INTERFACE_VALIDATION_FAILED"
    MANDATORY_STAGE_MISSING = "MANDATORY_STAGE_MISSING"
    MANDATORY_FIELD_MISSING = "MANDATORY_FIELD_MISSING"
    T_INT_MISSING = "T_INT_MISSING"
    J_FLUX_MISSING = "J_FLUX_MISSING"
    BACKEND_MISMATCH = "BACKEND_MISMATCH"
    NON_FINITE_STATE = "NON_FINITE_STATE"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    RECURSIVE_UPDATE_FAILED = "RECURSIVE_UPDATE_FAILED"
    LOGGING_FAILED = "LOGGING_FAILED"


class DynamicRegime(str, Enum):
    ENDOGENOUS_DYNAMIC_STABILITY = (
        "ENDOGENOUS_DYNAMIC_STABILITY"
    )
    ENDOGENOUS_DYNAMIC_CRITICALITY = (
        "ENDOGENOUS_DYNAMIC_CRITICALITY"
    )
    DEGRADATION_DRIFT = "DEGRADATION_DRIFT"
    UNDETERMINED = "UNDETERMINED"


class EDKOrchestratorError(RuntimeError):
    def __init__(
        self,
        status: RunStatus,
        message: str,
        *,
        details: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.details = dict(details or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "message": str(self),
            "details": _json_safe(self.details),
        }


@dataclass(frozen=True)
class FieldProvenance:
    field_name: str
    source_module: str
    source_stage: str
    tact_index: int
    backend: str
    dtype: str | None
    shape: tuple[int, ...] | None
    transition_history: tuple[dict[str, Any], ...] = ()

    def next(
        self,
        *,
        source_module: str,
        source_stage: str,
        tact_index: int,
        backend: str,
        value: Any,
    ) -> "FieldProvenance":
        history = list(self.transition_history)

        history.append(
            {
                "from_module": self.source_module,
                "from_stage": self.source_stage,
                "to_module": source_module,
                "to_stage": source_stage,
                "tact_index": int(tact_index),
            }
        )

        dtype, shape = _dtype_and_shape(
            value
        )

        return FieldProvenance(
            field_name=self.field_name,
            source_module=source_module,
            source_stage=source_stage,
            tact_index=int(tact_index),
            backend=backend,
            dtype=dtype,
            shape=shape,
            transition_history=tuple(history),
        )


@dataclass(frozen=True)
class EDKForwardCascadePacket:
    source_stage: str
    target_stage: str
    tact_index: int
    simulation_time: float
    payload: Mapping[str, Any]
    field_provenance: Mapping[str, FieldProvenance]
    validation_status: str = "READY"

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "payload",
            MappingProxyType(
                _deep_copy_mapping(
                    self.payload
                )
            ),
        )

        object.__setattr__(
            self,
            "field_provenance",
            MappingProxyType(
                dict(
                    self.field_provenance
                )
            ),
        )


@dataclass(frozen=True)
class EDKFeedbackPacket:
    D_n: Any
    A_n: Any
    J_flux: Any
    T_int: Any
    retained_structural_work: Any
    inherited_qualitative_characteristics: Any
    module_feedback: Mapping[str, Any]

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "module_feedback",
            MappingProxyType(
                _deep_copy_mapping(
                    self.module_feedback
                )
            ),
        )


@dataclass
class EDKHierarchicalState:
    tact_index: int = 0
    simulation_time: float = 0.0

    Q_n: Any = None
    D_n: Any = None
    A_n: Any = None

    C_t: Any = None
    C_proxy_t: Any = None
    P_t: Any = None
    R_t_phase_order: Any = None

    T_int: Any = None
    J_flux: Any = None
    M_t: Any = None

    retention_margin: Any = None

    dynamic_regime: str = (
        DynamicRegime.UNDETERMINED.value
    )

    resonance_window_state: Any = None

    module_states: dict[str, Any] = field(
        default_factory=dict
    )

    transition_events: list[dict[str, Any]] = field(
        default_factory=list
    )

    field_provenance: dict[
        str,
        FieldProvenance,
    ] = field(
        default_factory=dict
    )

    operational_fields: dict[str, Any] = field(
        default_factory=dict
    )

    def clone(self) -> "EDKHierarchicalState":
        return EDKHierarchicalState(
            tact_index=int(
                self.tact_index
            ),
            simulation_time=float(
                self.simulation_time
            ),
            Q_n=_deep_copy_value(
                self.Q_n
            ),
            D_n=_deep_copy_value(
                self.D_n
            ),
            A_n=_deep_copy_value(
                self.A_n
            ),
            C_t=_deep_copy_value(
                self.C_t
            ),
            C_proxy_t=_deep_copy_value(
                self.C_proxy_t
            ),
            P_t=_deep_copy_value(
                self.P_t
            ),
            R_t_phase_order=_deep_copy_value(
                self.R_t_phase_order
            ),
            T_int=_deep_copy_value(
                self.T_int
            ),
            J_flux=_deep_copy_value(
                self.J_flux
            ),
            M_t=_deep_copy_value(
                self.M_t
            ),
            retention_margin=_deep_copy_value(
                self.retention_margin
            ),
            dynamic_regime=str(
                self.dynamic_regime
            ),
            resonance_window_state=(
                _deep_copy_value(
                    self.resonance_window_state
                )
            ),
            module_states=_deep_copy_mapping(
                self.module_states
            ),
            transition_events=copy.deepcopy(
                self.transition_events
            ),
            field_provenance=dict(
                self.field_provenance
            ),
            operational_fields=_deep_copy_mapping(
                self.operational_fields
            ),
        )

    def as_payload(self) -> dict[str, Any]:
        payload = {
            "tact_index": int(
                self.tact_index
            ),
            "simulation_time": float(
                self.simulation_time
            ),
            "Q_n": _deep_copy_value(
                self.Q_n
            ),
            "D_n": _deep_copy_value(
                self.D_n
            ),
            "A_n": _deep_copy_value(
                self.A_n
            ),
            "C_t": _deep_copy_value(
                self.C_t
            ),
            "C_proxy_t": _deep_copy_value(
                self.C_proxy_t
            ),
            "P_t": _deep_copy_value(
                self.P_t
            ),
            "R_t_phase_order": _deep_copy_value(
                self.R_t_phase_order
            ),
            "T_int": _deep_copy_value(
                self.T_int
            ),
            "J_flux": _deep_copy_value(
                self.J_flux
            ),
            "M_t": _deep_copy_value(
                self.M_t
            ),
            "retention_margin": _deep_copy_value(
                self.retention_margin
            ),
            "dynamic_regime": str(
                self.dynamic_regime
            ),
            "resonance_window_state": (
                _deep_copy_value(
                    self.resonance_window_state
                )
            ),
        }

        payload.update(
            _deep_copy_mapping(
                self.operational_fields
            )
        )

        return payload

    def validate_finite(self) -> None:
        bad_paths: list[str] = []

        for name, value in self.as_payload().items():
            _collect_non_finite_paths(
                value,
                name,
                bad_paths,
            )

        if bad_paths:
            raise EDKOrchestratorError(
                RunStatus.NON_FINITE_STATE,
                (
                    "The hierarchical state "
                    "contains non-finite values."
                ),
                details={
                    "paths": bad_paths,
                },
            )


@runtime_checkable
class EDKModuleAdapter(Protocol):
    module_name: str
    stage_name: str

    required_inputs: Sequence[str]
    provided_outputs: Sequence[str]

    mandatory: bool
    backend: str

    def validate_input(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
    ) -> bool | None:
        ...

    def step(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
        dt: float,
    ) -> Mapping[str, Any]:
        ...

    def validate_output(
        self,
        output: Mapping[str, Any],
    ) -> bool | None:
        ...

    def export_state(
        self,
    ) -> Mapping[str, Any]:
        ...


@dataclass
class CallableModuleAdapter:
    module_name: str
    stage_name: str

    step_callable: Callable[
        [
            EDKForwardCascadePacket,
            EDKHierarchicalState,
            float,
        ],
        Mapping[str, Any],
    ]

    required_inputs: tuple[str, ...] = ()
    provided_outputs: tuple[str, ...] = ()

    mandatory: bool = True
    backend: str = "numpy"

    input_validator: Callable[
        [
            EDKForwardCascadePacket,
            EDKHierarchicalState,
        ],
        bool | None,
    ] | None = None

    output_validator: Callable[
        [
            Mapping[str, Any],
        ],
        bool | None,
    ] | None = None

    state_exporter: Callable[
        [],
        Mapping[str, Any],
    ] | None = None

    def validate_input(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
    ) -> bool | None:
        if self.input_validator is None:
            return True

        return self.input_validator(
            packet,
            state,
        )

    def step(
        self,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
        dt: float,
    ) -> Mapping[str, Any]:
        return self.step_callable(
            packet,
            state,
            dt,
        )

    def validate_output(
        self,
        output: Mapping[str, Any],
    ) -> bool | None:
        if self.output_validator is None:
            return True

        return self.output_validator(
            output
        )

    def export_state(
        self,
    ) -> Mapping[str, Any]:
        if self.state_exporter is None:
            return {}

        return self.state_exporter()


class EDKModuleRegistry:
    def __init__(self) -> None:
        self._by_name: dict[
            str,
            EDKModuleAdapter,
        ] = {}

        self._by_stage: dict[
            str,
            list[EDKModuleAdapter],
        ] = {
            stage: []
            for stage in STAGE_ORDER
        }

    def register(
        self,
        adapter: EDKModuleAdapter,
    ) -> None:
        self._validate_contract(
            adapter
        )

        module_name = str(
            adapter.module_name
        )

        if module_name in self._by_name:
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "Duplicate module name: "
                    f"{module_name}"
                ),
            )

        self._by_name[
            module_name
        ] = adapter

        self._by_stage[
            str(
                adapter.stage_name
            )
        ].append(
            adapter
        )

    def unregister(
        self,
        module_name: str,
    ) -> None:
        adapter = self._by_name.pop(
            module_name
        )

        self._by_stage[
            adapter.stage_name
        ] = [
            item
            for item in self._by_stage[
                adapter.stage_name
            ]
            if item.module_name
            != module_name
        ]

    def get(
        self,
        module_name: str,
    ) -> EDKModuleAdapter:
        return self._by_name[
            module_name
        ]

    def adapters_for_stage(
        self,
        stage_name: str,
    ) -> tuple[EDKModuleAdapter, ...]:
        return tuple(
            self._by_stage[
                stage_name
            ]
        )

    def ordered_adapters(
        self,
    ) -> tuple[EDKModuleAdapter, ...]:
        return tuple(
            adapter
            for stage in STAGE_ORDER
            for adapter in self._by_stage[
                stage
            ]
        )

    def registered_stages(
        self,
    ) -> tuple[str, ...]:
        return tuple(
            stage
            for stage in STAGE_ORDER
            if self._by_stage[
                stage
            ]
        )

    def validate_required_stages(
        self,
        required_stages: Iterable[str],
    ) -> None:
        missing = [
            stage
            for stage in required_stages
            if not self._by_stage.get(
                stage
            )
        ]

        if missing:
            raise EDKOrchestratorError(
                RunStatus.MANDATORY_STAGE_MISSING,
                (
                    "Mandatory execution "
                    "stages are missing."
                ),
                details={
                    "missing_stages": missing,
                },
            )

    def describe(
        self,
    ) -> dict[str, Any]:
        return {
            "stage_order": list(
                STAGE_ORDER
            ),
            "modules": [
                {
                    "module_name": (
                        adapter.module_name
                    ),
                    "stage_name": (
                        adapter.stage_name
                    ),
                    "required_inputs": list(
                        adapter.required_inputs
                    ),
                    "provided_outputs": list(
                        adapter.provided_outputs
                    ),
                    "mandatory": bool(
                        adapter.mandatory
                    ),
                    "backend": str(
                        adapter.backend
                    ),
                }
                for adapter
                in self.ordered_adapters()
            ],
        }

    @staticmethod
    def _validate_contract(
        adapter: EDKModuleAdapter,
    ) -> None:
        required_attributes = (
            "module_name",
            "stage_name",
            "required_inputs",
            "provided_outputs",
            "mandatory",
            "backend",
        )

        required_methods = (
            "validate_input",
            "step",
            "validate_output",
            "export_state",
        )

        for attribute_name in required_attributes:
            if not hasattr(
                adapter,
                attribute_name,
            ):
                raise EDKOrchestratorError(
                    RunStatus.MODULE_REGISTRATION_FAILED,
                    (
                        "Adapter is missing "
                        f"attribute: {attribute_name}"
                    ),
                )

        for method_name in required_methods:
            if not callable(
                getattr(
                    adapter,
                    method_name,
                    None,
                )
            ):
                raise EDKOrchestratorError(
                    RunStatus.MODULE_REGISTRATION_FAILED,
                    (
                        "Adapter is missing "
                        f"method: {method_name}()"
                    ),
                )

        if not str(
            adapter.module_name
        ).strip():
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "module_name must "
                    "not be empty."
                ),
            )

        if adapter.stage_name not in STAGE_ORDER:
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "Unknown execution stage: "
                    f"{adapter.stage_name}"
                ),
                details={
                    "allowed_stages": list(
                        STAGE_ORDER
                    ),
                },
            )

        backend = str(
            adapter.backend
        ).lower()

        if backend not in {
            "numpy",
            "cupy",
            "mixed",
            "agnostic",
        }:
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "Unsupported backend: "
                    f"{adapter.backend}"
                ),
            )

        required_inputs = tuple(
            adapter.required_inputs
        )

        provided_outputs = tuple(
            adapter.provided_outputs
        )

        if (
            len(
                set(
                    required_inputs
                )
            )
            != len(
                required_inputs
            )
        ):
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "Duplicate required_inputs "
                    f"in {adapter.module_name}."
                ),
            )

        if (
            len(
                set(
                    provided_outputs
                )
            )
            != len(
                provided_outputs
            )
        ):
            raise EDKOrchestratorError(
                RunStatus.MODULE_REGISTRATION_FAILED,
                (
                    "Duplicate provided_outputs "
                    f"in {adapter.module_name}."
                ),
            )


class EDKHierarchicalLogger:
    def __init__(
        self,
        output_directory: str | Path = (
            "edk_hierarchical_output"
        ),
    ) -> None:
        self.output_directory = Path(
            output_directory
        )

        self.output_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write_tact(
        self,
        *,
        state: EDKHierarchicalState,
        payload: Mapping[str, Any],
        feedback: EDKFeedbackPacket,
        status: RunStatus,
        registry: EDKModuleRegistry,
    ) -> tuple[Path, Path]:
        tact_number = int(
            state.tact_index
        )

        json_path = (
            self.output_directory
            / (
                "hierarchical_step_"
                f"{tact_number:06d}.json"
            )
        )

        npz_path = (
            self.output_directory
            / (
                "hierarchical_field_"
                f"{tact_number:06d}.npz"
            )
        )

        arrays: dict[
            str,
            np.ndarray,
        ] = {}

        _collect_arrays(
            {
                "state": state.as_payload(),
                "module_states": (
                    state.module_states
                ),
                "payload": payload,
                "feedback": (
                    _feedback_to_dict(
                        feedback
                    )
                ),
            },
            "",
            arrays,
        )

        metadata = {
            "status": status.value,
            "tact": tact_number,
            "step": tact_number,
            "tact_index": tact_number,
            "simulation_time": float(
                state.simulation_time
            ),
            "state": _json_safe(
                state.as_payload()
            ),
            "module_states": _json_safe(
                state.module_states
            ),
            "transition_events": _json_safe(
                state.transition_events
            ),
            "field_provenance": {
                key: _json_safe(
                    asdict(
                        value
                    )
                )
                for key, value
                in state.field_provenance.items()
            },
            "feedback": _json_safe(
                _feedback_to_dict(
                    feedback
                )
            ),
            "registry": registry.describe(),
            "array_fields": {
                key: {
                    "dtype": str(
                        value.dtype
                    ),
                    "shape": list(
                        value.shape
                    ),
                }
                for key, value
                in arrays.items()
            },
        }

        try:
            self._atomic_json(
                json_path,
                metadata,
            )

            self._atomic_npz(
                npz_path,
                arrays,
            )

        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.LOGGING_FAILED,
                (
                    "Atomic tact logging "
                    f"failed: {error}"
                ),
                details={
                    "json_path": str(
                        json_path
                    ),
                    "npz_path": str(
                        npz_path
                    ),
                },
            ) from error

        return (
            json_path,
            npz_path,
        )

    def write_step(
        self,
        *,
        state: EDKHierarchicalState,
        payload: Mapping[str, Any],
        feedback: EDKFeedbackPacket,
        status: RunStatus,
        registry: EDKModuleRegistry,
    ) -> tuple[Path, Path]:
        """
        Compatibility alias for older scripts and tests.

        Internally this represents one tact-by-tact hierarchical interval.
        """

        return self.write_tact(
            state=state,
            payload=payload,
            feedback=feedback,
            status=status,
            registry=registry,
        )

    def write_summary(
        self,
        summary: Mapping[str, Any],
    ) -> Path:
        path = (
            self.output_directory
            / "hierarchical_summary.json"
        )

        try:
            self._atomic_json(
                path,
                summary,
            )
        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.LOGGING_FAILED,
                (
                    "Summary logging "
                    f"failed: {error}"
                ),
                details={
                    "path": str(
                        path
                    ),
                },
            ) from error

        return path

    @staticmethod
    def _atomic_json(
        path: Path,
        data: Mapping[str, Any],
    ) -> None:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )

        temporary_path = Path(
            name
        )

        try:
            with os.fdopen(
                descriptor,
                "w",
                encoding="utf-8",
            ) as handle:
                json.dump(
                    _json_safe(
                        data
                    ),
                    handle,
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                )

                handle.write(
                    "\n"
                )

                handle.flush()

                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary_path,
                path,
            )

            _fsync_directory(
                path.parent
            )

        except Exception:
            temporary_path.unlink(
                missing_ok=True
            )
            raise

    @staticmethod
    def _atomic_npz(
        path: Path,
        arrays: Mapping[
            str,
            np.ndarray,
        ],
    ) -> None:
        descriptor, name = tempfile.mkstemp(
            prefix=f".{path.stem}.",
            suffix=".npz",
            dir=path.parent,
        )

        os.close(
            descriptor
        )

        temporary_path = Path(
            name
        )

        try:
            normalized = {
                _sanitize_npz_key(
                    key
                ): np.asarray(
                    value
                )
                for key, value
                in arrays.items()
            }

            np.savez_compressed(
                temporary_path,
                **normalized,
            )

            with temporary_path.open(
                "rb"
            ) as handle:
                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary_path,
                path,
            )

            _fsync_directory(
                path.parent
            )

        except Exception:
            temporary_path.unlink(
                missing_ok=True
            )
            raise


PhiOperator = Callable[
    ...,
    Any,
]


class EDKHierarchicalOrchestrator:
    def __init__(
        self,
        *,
        registry: EDKModuleRegistry | None = None,
        initial_state: (
            EDKHierarchicalState | None
        ) = None,
        phi_operator: PhiOperator | None = None,
        logger: (
            EDKHierarchicalLogger | None
        ) = None,
        dt: float = 0.005,
        execution_mode: (
            ExecutionMode | str
        ) = ExecutionMode.COMPLETE,
        critical_band: float = 0.0,
        required_stages: Sequence[str] = (
            DEFAULT_REQUIRED_STAGES
        ),
        mandatory_fields: Sequence[str] = (
            MANDATORY_INTEGRATION_FIELDS
        ),
        log_every_tact: bool = True,
    ) -> None:
        self.registry = (
            registry
            or EDKModuleRegistry()
        )

        self.state = (
            initial_state
            or EDKHierarchicalState()
        )

        self.phi_operator = phi_operator
        self.logger = logger

        self.dt = float(
            dt
        )

        self.execution_mode = ExecutionMode(
            execution_mode
        )

        self.critical_band = float(
            critical_band
        )

        self.required_stages = tuple(
            required_stages
        )

        self.mandatory_fields = tuple(
            mandatory_fields
        )

        self.log_every_tact = bool(
            log_every_tact
        )

        self._history: list[
            dict[str, Any]
        ] = []

        self._last_payload: dict[
            str,
            Any,
        ] = {}

        self._last_feedback: (
            EDKFeedbackPacket | None
        ) = None

        self._last_status = (
            RunStatus.COMPLETED
        )

        if (
            not math.isfinite(
                self.dt
            )
            or self.dt <= 0.0
        ):
            raise ValueError(
                (
                    "dt must be a finite "
                    "positive value."
                )
            )

        if (
            not math.isfinite(
                self.critical_band
            )
            or self.critical_band < 0.0
        ):
            raise ValueError(
                (
                    "critical_band must be "
                    "finite and non-negative."
                )
            )

        unknown_stages = [
            stage
            for stage in self.required_stages
            if stage not in STAGE_ORDER
        ]

        if unknown_stages:
            raise ValueError(
                (
                    "Unknown required stages: "
                    f"{unknown_stages}"
                )
            )

        self._initialize_provenance()

    def register_module(
        self,
        adapter: EDKModuleAdapter,
    ) -> None:
        self.registry.register(
            adapter
        )

    def run_tact(
        self,
    ) -> EDKHierarchicalState:
        current_state = self.state.clone()

        try:
            self._validate_start(
                current_state
            )

            payload = (
                current_state.as_payload()
            )

            provenance = dict(
                current_state.field_provenance
            )

            module_states = _deep_copy_mapping(
                current_state.module_states
            )

            transition_events = copy.deepcopy(
                current_state.transition_events
            )

            previous_stage = "state"

            for stage_name in STAGE_ORDER:
                adapters = (
                    self.registry.adapters_for_stage(
                        stage_name
                    )
                )

                if not adapters:
                    if (
                        self.execution_mode
                        is ExecutionMode.COMPLETE
                        and stage_name
                        in self.required_stages
                    ):
                        raise EDKOrchestratorError(
                            RunStatus.MANDATORY_STAGE_MISSING,
                            (
                                "Mandatory stage "
                                "is missing: "
                                f"{stage_name}"
                            ),
                            details={
                                "stage_name": stage_name,
                            },
                        )

                    transition_events.append(
                        {
                            "event": (
                                "STAGE_SKIPPED"
                            ),
                            "stage_name": (
                                stage_name
                            ),
                            "tact_index": (
                                current_state.tact_index
                            ),
                            "execution_mode": (
                                self.execution_mode.value
                            ),
                        }
                    )

                    continue

                for adapter in adapters:
                    packet = (
                        EDKForwardCascadePacket(
                            source_stage=(
                                previous_stage
                            ),
                            target_stage=(
                                stage_name
                            ),
                            tact_index=(
                                current_state.tact_index
                            ),
                            simulation_time=(
                                current_state.simulation_time
                            ),
                            payload=payload,
                            field_provenance=(
                                provenance
                            ),
                        )
                    )

                    self._validate_input(
                        adapter,
                        packet,
                        current_state,
                    )

                    output = adapter.step(
                        packet,
                        current_state.clone(),
                        self.dt,
                    )

                    output_mapping = (
                        self._validate_output(
                            adapter,
                            output,
                        )
                    )

                    self._validate_backend(
                        adapter,
                        output_mapping,
                    )

                    self._merge_output(
                        payload,
                        provenance,
                        adapter,
                        output_mapping,
                        current_state.tact_index,
                    )

                    exported_state = (
                        adapter.export_state()
                    )

                    if not isinstance(
                        exported_state,
                        Mapping,
                    ):
                        raise EDKOrchestratorError(
                            RunStatus.INTERFACE_VALIDATION_FAILED,
                            (
                                f"{adapter.module_name}"
                                ".export_state() "
                                "must return a mapping."
                            ),
                        )

                    module_states[
                        adapter.module_name
                    ] = _deep_copy_mapping(
                        exported_state
                    )

                    transition_events.append(
                        {
                            "event": (
                                "MODULE_EXECUTED"
                            ),
                            "module_name": (
                                adapter.module_name
                            ),
                            "stage_name": (
                                stage_name
                            ),
                            "tact_index": (
                                current_state.tact_index
                            ),
                            "provided_outputs": (
                                sorted(
                                    output_mapping.keys()
                                )
                            ),
                        }
                    )

                    previous_stage = stage_name

            self._validate_mandatory_fields(
                payload
            )

            retention_margin = (
                self._retention_margin(
                    payload.get(
                        "C_t"
                    ),
                    payload.get(
                        "P_t"
                    ),
                )
            )

            dynamic_regime = (
                self._dynamic_regime(
                    retention_margin
                )
            )

            if (
                payload.get(
                    "C_proxy_t"
                )
                is not None
                and payload.get(
                    "P_t"
                )
                is not None
            ):
                payload[
                    "C_proxy_retention_margin"
                ] = _subtract(
                    payload[
                        "C_proxy_t"
                    ],
                    payload[
                        "P_t"
                    ],
                )

            payload[
                "retention_margin"
            ] = retention_margin

            payload[
                "dynamic_regime"
            ] = dynamic_regime.value

            feedback = self._feedback(
                payload,
                module_states,
            )

            Q_next = self._phi(
                current_state,
                payload,
                feedback,
            )

            if not _is_finite_value(
                Q_next
            ):
                raise EDKOrchestratorError(
                    RunStatus.NON_FINITE_STATE,
                    (
                        "Phi returned a "
                        "non-finite Q(n+1)."
                    ),
                )

            next_state = self._next_state(
                current=current_state,
                payload=payload,
                provenance=provenance,
                module_states=module_states,
                events=transition_events,
                feedback=feedback,
                Q_next=Q_next,
                retention_margin=(
                    retention_margin
                ),
                dynamic_regime=(
                    dynamic_regime
                ),
            )

            next_state.validate_finite()

            self.state = next_state

            self._last_payload = (
                _deep_copy_mapping(
                    payload
                )
            )

            self._last_feedback = feedback

            self._last_status = (
                RunStatus.COMPLETED
            )

            self._history.append(
                {
                    "status": (
                        RunStatus.COMPLETED.value
                    ),
                    "tact_index": (
                        next_state.tact_index
                    ),
                    "simulation_time": (
                        next_state.simulation_time
                    ),
                    "dynamic_regime": (
                        next_state.dynamic_regime
                    ),
                    "retention_margin": (
                        _json_safe(
                            next_state.retention_margin
                        )
                    ),
                }
            )

            if (
                self.logger is not None
                and self.log_every_tact
            ):
                self.logger.write_tact(
                    state=next_state,
                    payload=payload,
                    feedback=feedback,
                    status=(
                        RunStatus.COMPLETED
                    ),
                    registry=self.registry,
                )

            return next_state.clone()

        except EDKOrchestratorError as error:
            self._last_status = (
                error.status
            )

            self._history.append(
                {
                    "status": (
                        error.status.value
                    ),
                    "tact_index": (
                        current_state.tact_index
                    ),
                    "simulation_time": (
                        current_state.simulation_time
                    ),
                    "error": (
                        error.to_dict()
                    ),
                }
            )

            raise

        except Exception as error:
            wrapped_error = EDKOrchestratorError(
                RunStatus.INVALID_STATE_TRANSITION,
                (
                    "Unhandled hierarchical "
                    "transition error: "
                    f"{error}"
                ),
            )

            self._last_status = (
                wrapped_error.status
            )

            self._history.append(
                {
                    "status": (
                        wrapped_error.status.value
                    ),
                    "tact_index": (
                        current_state.tact_index
                    ),
                    "simulation_time": (
                        current_state.simulation_time
                    ),
                    "error": (
                        wrapped_error.to_dict()
                    ),
                }
            )

            raise wrapped_error from error

    def run(
        self,
        tact_count: int,
    ) -> dict[str, Any]:
        tact_count = int(
            tact_count
        )

        if tact_count < 0:
            raise ValueError(
                (
                    "tact_count must "
                    "be non-negative."
                )
            )

        completed_tacts = 0

        final_error: (
            dict[str, Any] | None
        ) = None

        for _ in range(
            tact_count
        ):
            try:
                self.run_tact()
                completed_tacts += 1

            except EDKOrchestratorError as error:
                final_error = (
                    error.to_dict()
                )
                break

        summary = self.summary(
            requested_tacts=tact_count,
            completed_tacts=completed_tacts,
            final_error=final_error,
        )

        if self.logger is not None:
            self.logger.write_summary(
                summary
            )

        return summary

    def summary(
        self,
        *,
        requested_tacts: int | None = None,
        completed_tacts: int | None = None,
        final_error: (
            Mapping[str, Any] | None
        ) = None,
    ) -> dict[str, Any]:
        if completed_tacts is None:
            completed_tacts = sum(
                (
                    record.get(
                        "status"
                    )
                    == RunStatus.COMPLETED.value
                )
                for record in self._history
            )

        return {
            "status": (
                self._last_status.value
            ),
            "execution_mode": (
                self.execution_mode.value
            ),
            "requested_tacts": (
                requested_tacts
            ),
            "completed_tacts": int(
                completed_tacts
            ),
            "final_state": _json_safe(
                self.state.as_payload()
            ),
            "field_provenance": {
                key: _json_safe(
                    asdict(
                        value
                    )
                )
                for key, value
                in self.state.field_provenance.items()
            },
            "registry": (
                self.registry.describe()
            ),
            "history": _json_safe(
                self._history
            ),
            "final_error": _json_safe(
                final_error
            ),
        }

    def _initialize_provenance(
        self,
    ) -> None:
        for name, value in (
            self.state.as_payload().items()
        ):
            if (
                name
                not in self.state.field_provenance
                and value is not None
            ):
                dtype, shape = (
                    _dtype_and_shape(
                        value
                    )
                )

                self.state.field_provenance[
                    name
                ] = FieldProvenance(
                    field_name=name,
                    source_module=(
                        "initial_state"
                    ),
                    source_stage="state",
                    tact_index=int(
                        self.state.tact_index
                    ),
                    backend=_detect_backend(
                        value
                    ),
                    dtype=dtype,
                    shape=shape,
                )

    def _validate_start(
        self,
        state: EDKHierarchicalState,
    ) -> None:
        if state.tact_index < 0:
            raise EDKOrchestratorError(
                RunStatus.INVALID_STATE_TRANSITION,
                (
                    "tact_index must "
                    "be non-negative."
                ),
            )

        if (
            not math.isfinite(
                state.simulation_time
            )
            or state.simulation_time < 0.0
        ):
            raise EDKOrchestratorError(
                RunStatus.INVALID_STATE_TRANSITION,
                (
                    "simulation_time must "
                    "be finite and non-negative."
                ),
            )

        state.validate_finite()

        if (
            self.execution_mode
            is ExecutionMode.COMPLETE
        ):
            self.registry.validate_required_stages(
                self.required_stages
            )

    def _validate_input(
        self,
        adapter: EDKModuleAdapter,
        packet: EDKForwardCascadePacket,
        state: EDKHierarchicalState,
    ) -> None:
        missing_inputs = [
            name
            for name in adapter.required_inputs
            if (
                name not in packet.payload
                or packet.payload[
                    name
                ] is None
            )
        ]

        if missing_inputs:
            raise EDKOrchestratorError(
                RunStatus.MANDATORY_FIELD_MISSING,
                (
                    f"Module {adapter.module_name} "
                    "is missing required "
                    "input fields."
                ),
                details={
                    "module_name": (
                        adapter.module_name
                    ),
                    "stage_name": (
                        adapter.stage_name
                    ),
                    "missing_inputs": (
                        missing_inputs
                    ),
                },
            )

        try:
            validation_result = (
                adapter.validate_input(
                    packet,
                    state.clone(),
                )
            )

        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.INTERFACE_VALIDATION_FAILED,
                (
                    "Input validation failed "
                    f"in {adapter.module_name}: "
                    f"{error}"
                ),
            ) from error

        if validation_result is False:
            raise EDKOrchestratorError(
                RunStatus.INTERFACE_VALIDATION_FAILED,
                (
                    "Input validation returned "
                    "False in "
                    f"{adapter.module_name}."
                ),
            )

    def _validate_output(
        self,
        adapter: EDKModuleAdapter,
        output: Mapping[str, Any],
    ) -> dict[str, Any]:
        if not isinstance(
            output,
            Mapping,
        ):
            raise EDKOrchestratorError(
                RunStatus.INTERFACE_VALIDATION_FAILED,
                (
                    f"{adapter.module_name}"
                    ".step() must return "
                    "a mapping."
                ),
            )

        output_mapping = (
            _deep_copy_mapping(
                output
            )
        )

        missing_outputs = [
            name
            for name
            in adapter.provided_outputs
            if name not in output_mapping
        ]

        if missing_outputs:
            raise EDKOrchestratorError(
                RunStatus.MANDATORY_FIELD_MISSING,
                (
                    f"Module {adapter.module_name} "
                    "did not provide declared "
                    "output fields."
                ),
                details={
                    "module_name": (
                        adapter.module_name
                    ),
                    "stage_name": (
                        adapter.stage_name
                    ),
                    "missing_outputs": (
                        missing_outputs
                    ),
                },
            )

        bad_paths: list[str] = []

        for name, value in (
            output_mapping.items()
        ):
            _collect_non_finite_paths(
                value,
                (
                    f"{adapter.module_name}."
                    f"{name}"
                ),
                bad_paths,
            )

        if bad_paths:
            raise EDKOrchestratorError(
                RunStatus.NON_FINITE_STATE,
                (
                    f"Module {adapter.module_name} "
                    "returned non-finite values."
                ),
                details={
                    "paths": bad_paths,
                },
            )

        try:
            validation_result = (
                adapter.validate_output(
                    output_mapping
                )
            )

        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.INTERFACE_VALIDATION_FAILED,
                (
                    "Output validation failed "
                    f"in {adapter.module_name}: "
                    f"{error}"
                ),
            ) from error

        if validation_result is False:
            raise EDKOrchestratorError(
                RunStatus.INTERFACE_VALIDATION_FAILED,
                (
                    "Output validation returned "
                    "False in "
                    f"{adapter.module_name}."
                ),
            )

        return output_mapping

    @staticmethod
    def _validate_backend(
        adapter: EDKModuleAdapter,
        output: Mapping[str, Any],
    ) -> None:
        declared_backend = str(
            adapter.backend
        ).lower()

        if declared_backend in {
            "mixed",
            "agnostic",
        }:
            return

        detected_backends: set[str] = set()

        _collect_array_backends(
            output,
            detected_backends,
        )

        if (
            detected_backends
            and detected_backends
            != {
                declared_backend
            }
        ):
            raise EDKOrchestratorError(
                RunStatus.BACKEND_MISMATCH,
                (
                    "Backend mismatch in "
                    f"{adapter.module_name}: "
                    f"declared={declared_backend}, "
                    "detected="
                    f"{sorted(detected_backends)}"
                ),
                details={
                    "module_name": (
                        adapter.module_name
                    ),
                    "declared_backend": (
                        declared_backend
                    ),
                    "detected_backends": (
                        sorted(
                            detected_backends
                        )
                    ),
                },
            )

    @staticmethod
    def _merge_output(
        payload: MutableMapping[str, Any],
        provenance: MutableMapping[
            str,
            FieldProvenance,
        ],
        adapter: EDKModuleAdapter,
        output: Mapping[str, Any],
        tact_index: int,
    ) -> None:
        for name, value in output.items():
            payload[
                name
            ] = _deep_copy_value(
                value
            )

            if name in provenance:
                provenance[
                    name
                ] = provenance[
                    name
                ].next(
                    source_module=(
                        adapter.module_name
                    ),
                    source_stage=(
                        adapter.stage_name
                    ),
                    tact_index=tact_index,
                    backend=str(
                        adapter.backend
                    ),
                    value=value,
                )

            else:
                dtype, shape = (
                    _dtype_and_shape(
                        value
                    )
                )

                provenance[
                    name
                ] = FieldProvenance(
                    field_name=name,
                    source_module=(
                        adapter.module_name
                    ),
                    source_stage=(
                        adapter.stage_name
                    ),
                    tact_index=int(
                        tact_index
                    ),
                    backend=str(
                        adapter.backend
                    ),
                    dtype=dtype,
                    shape=shape,
                )

    def _validate_mandatory_fields(
        self,
        payload: Mapping[str, Any],
    ) -> None:
        if (
            self.execution_mode
            is not ExecutionMode.COMPLETE
        ):
            return

        missing_fields = [
            name
            for name in self.mandatory_fields
            if (
                name not in payload
                or payload[
                    name
                ] is None
            )
        ]

        if "T_int" in missing_fields:
            raise EDKOrchestratorError(
                RunStatus.T_INT_MISSING,
                (
                    "T_int is missing from "
                    "the complete hierarchical "
                    "tact."
                ),
            )

        if "J_flux" in missing_fields:
            raise EDKOrchestratorError(
                RunStatus.J_FLUX_MISSING,
                (
                    "J_flux is missing from "
                    "the complete hierarchical "
                    "tact."
                ),
            )

        if missing_fields:
            raise EDKOrchestratorError(
                RunStatus.MANDATORY_FIELD_MISSING,
                (
                    "Mandatory integration "
                    "fields are missing."
                ),
                details={
                    "missing_fields": (
                        missing_fields
                    ),
                },
            )

    @staticmethod
    def _retention_margin(
        C_t: Any,
        P_t: Any,
    ) -> Any:
        if (
            C_t is None
            or P_t is None
        ):
            return None

        try:
            return _subtract(
                C_t,
                P_t,
            )

        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.INVALID_STATE_TRANSITION,
                (
                    "Cannot calculate "
                    f"C(t) - P(t): {error}"
                ),
            ) from error

    def _dynamic_regime(
        self,
        retention_margin: Any,
    ) -> DynamicRegime:
        if retention_margin is None:
            return DynamicRegime.UNDETERMINED

        scalar_margin = (
            _reduce_to_scalar(
                retention_margin
            )
        )

        if (
            scalar_margin
            > self.critical_band
        ):
            return (
                DynamicRegime
                .ENDOGENOUS_DYNAMIC_STABILITY
            )

        if (
            scalar_margin
            < -self.critical_band
        ):
            return (
                DynamicRegime
                .DEGRADATION_DRIFT
            )

        return (
            DynamicRegime
            .ENDOGENOUS_DYNAMIC_CRITICALITY
        )

    @staticmethod
    def _feedback(
        payload: Mapping[str, Any],
        module_states: Mapping[str, Any],
    ) -> EDKFeedbackPacket:
        module_feedback: dict[
            str,
            Any,
        ] = {}

        for (
            module_name,
            module_state,
        ) in module_states.items():
            if (
                isinstance(
                    module_state,
                    Mapping,
                )
                and "module_feedback"
                in module_state
            ):
                module_feedback[
                    module_name
                ] = _deep_copy_value(
                    module_state[
                        "module_feedback"
                    ]
                )

        payload_feedback = payload.get(
            "module_feedback"
        )

        if isinstance(
            payload_feedback,
            Mapping,
        ):
            module_feedback.update(
                _deep_copy_mapping(
                    payload_feedback
                )
            )

        return EDKFeedbackPacket(
            D_n=_deep_copy_value(
                payload.get(
                    "D_n"
                )
            ),
            A_n=_deep_copy_value(
                payload.get(
                    "A_n"
                )
            ),
            J_flux=_deep_copy_value(
                payload.get(
                    "J_flux"
                )
            ),
            T_int=_deep_copy_value(
                payload.get(
                    "T_int"
                )
            ),
            retained_structural_work=(
                _deep_copy_value(
                    payload.get(
                        "retained_structural_work"
                    )
                )
            ),
            inherited_qualitative_characteristics=(
                _deep_copy_value(
                    payload.get(
                        "inherited_qualitative_characteristics"
                    )
                )
            ),
            module_feedback=module_feedback,
        )

    def _phi(
        self,
        current_state: EDKHierarchicalState,
        payload: Mapping[str, Any],
        feedback: EDKFeedbackPacket,
    ) -> Any:
        if self.phi_operator is None:
            if (
                self.execution_mode
                is ExecutionMode.COMPLETE
            ):
                raise EDKOrchestratorError(
                    RunStatus.RECURSIVE_UPDATE_FAILED,
                    (
                        "Complete execution "
                        "requires an explicit "
                        "Phi operator."
                    ),
                )

            return _deep_copy_value(
                payload.get(
                    "Q_n"
                )
            )

        try:
            return _invoke_phi(
                self.phi_operator,
                Q_n=payload.get(
                    "Q_n"
                ),
                D_n=payload.get(
                    "D_n"
                ),
                A_n=payload.get(
                    "A_n"
                ),
                feedback=feedback,
                state=current_state.clone(),
                dt=self.dt,
            )

        except Exception as error:
            raise EDKOrchestratorError(
                RunStatus.RECURSIVE_UPDATE_FAILED,
                (
                    "Phi operator failed: "
                    f"{error}"
                ),
            ) from error

    def _next_state(
        self,
        *,
        current: EDKHierarchicalState,
        payload: Mapping[str, Any],
        provenance: Mapping[
            str,
            FieldProvenance,
        ],
        module_states: Mapping[str, Any],
        events: Sequence[
            Mapping[str, Any]
        ],
        feedback: EDKFeedbackPacket,
        Q_next: Any,
        retention_margin: Any,
        dynamic_regime: DynamicRegime,
    ) -> EDKHierarchicalState:
        next_tact_index = int(
            current.tact_index
        ) + 1

        next_simulation_time = float(
            current.simulation_time
        ) + self.dt

        reserved_fields = {
            "tact_index",
            "simulation_time",
            "Q_n",
            "D_n",
            "A_n",
            "C_t",
            "C_proxy_t",
            "P_t",
            "R_t_phase_order",
            "T_int",
            "J_flux",
            "M_t",
            "retention_margin",
            "dynamic_regime",
            "resonance_window_state",
        }

        operational_fields = {
            key: _deep_copy_value(
                value
            )
            for key, value in payload.items()
            if key not in reserved_fields
        }

        operational_fields[
            "retained_structural_work"
        ] = _deep_copy_value(
            feedback.retained_structural_work
        )

        operational_fields[
            "inherited_qualitative_characteristics"
        ] = _deep_copy_value(
            feedback
            .inherited_qualitative_characteristics
        )

        next_events = [
            copy.deepcopy(
                dict(
                    item
                )
            )
            for item in events
        ]

        next_events.append(
            {
                "event": "TACT_COMPLETED",
                "from_tact": int(
                    current.tact_index
                ),
                "to_tact": (
                    next_tact_index
                ),
                "from_time": float(
                    current.simulation_time
                ),
                "to_time": (
                    next_simulation_time
                ),
                "dynamic_regime": (
                    dynamic_regime.value
                ),
            }
        )

        next_provenance = dict(
            provenance
        )

        if "Q_n" in next_provenance:
            next_provenance[
                "Q_n"
            ] = next_provenance[
                "Q_n"
            ].next(
                source_module="Phi",
                source_stage="feedback",
                tact_index=(
                    next_tact_index
                ),
                backend=_detect_backend(
                    Q_next
                ),
                value=Q_next,
            )

        else:
            dtype, shape = (
                _dtype_and_shape(
                    Q_next
                )
            )

            next_provenance[
                "Q_n"
            ] = FieldProvenance(
                field_name="Q_n",
                source_module="Phi",
                source_stage="feedback",
                tact_index=(
                    next_tact_index
                ),
                backend=_detect_backend(
                    Q_next
                ),
                dtype=dtype,
                shape=shape,
            )

        return EDKHierarchicalState(
            tact_index=next_tact_index,
            simulation_time=(
                next_simulation_time
            ),
            Q_n=_deep_copy_value(
                Q_next
            ),
            D_n=_deep_copy_value(
                payload.get(
                    "D_n"
                )
            ),
            A_n=_deep_copy_value(
                payload.get(
                    "A_n"
                )
            ),
            C_t=_deep_copy_value(
                payload.get(
                    "C_t"
                )
            ),
            C_proxy_t=_deep_copy_value(
                payload.get(
                    "C_proxy_t"
                )
            ),
            P_t=_deep_copy_value(
                payload.get(
                    "P_t"
                )
            ),
            R_t_phase_order=_deep_copy_value(
                payload.get(
                    "R_t_phase_order"
                )
            ),
            T_int=_deep_copy_value(
                payload.get(
                    "T_int"
                )
            ),
            J_flux=_deep_copy_value(
                payload.get(
                    "J_flux"
                )
            ),
            M_t=_deep_copy_value(
                payload.get(
                    "M_t"
                )
            ),
            retention_margin=_deep_copy_value(
                retention_margin
            ),
            dynamic_regime=(
                dynamic_regime.value
            ),
            resonance_window_state=(
                _deep_copy_value(
                    payload.get(
                        "resonance_window_state",
                        current
                        .resonance_window_state,
                    )
                )
            ),
            module_states=_deep_copy_mapping(
                module_states
            ),
            transition_events=next_events,
            field_provenance=(
                next_provenance
            ),
            operational_fields=(
                operational_fields
            ),
        )


def _feedback_to_dict(
    feedback: EDKFeedbackPacket,
) -> dict[str, Any]:
    return {
        "D_n": _deep_copy_value(
            feedback.D_n
        ),
        "A_n": _deep_copy_value(
            feedback.A_n
        ),
        "J_flux": _deep_copy_value(
            feedback.J_flux
        ),
        "T_int": _deep_copy_value(
            feedback.T_int
        ),
        "retained_structural_work": (
            _deep_copy_value(
                feedback
                .retained_structural_work
            )
        ),
        "inherited_qualitative_characteristics": (
            _deep_copy_value(
                feedback
                .inherited_qualitative_characteristics
            )
        ),
        "module_feedback": (
            _deep_copy_mapping(
                feedback.module_feedback
            )
        ),
    }


def _invoke_phi(
    operator: PhiOperator,
    *,
    Q_n: Any,
    D_n: Any,
    A_n: Any,
    feedback: EDKFeedbackPacket,
    state: EDKHierarchicalState,
    dt: float,
) -> Any:
    signature = inspect.signature(
        operator
    )

    parameters = (
        signature.parameters
    )

    values = {
        "Q_n": Q_n,
        "D_n": D_n,
        "A_n": A_n,
        "feedback": feedback,
        "state": state,
        "dt": dt,
    }

    has_kwargs = any(
        parameter.kind
        is inspect.Parameter.VAR_KEYWORD
        for parameter
        in parameters.values()
    )

    if has_kwargs:
        return operator(
            **values
        )

    accepted_values = {
        name: value
        for name, value in values.items()
        if name in parameters
    }

    missing_parameters = [
        name
        for name, parameter
        in parameters.items()
        if (
            parameter.kind
            in {
                inspect.Parameter
                .POSITIONAL_OR_KEYWORD,
                inspect.Parameter
                .KEYWORD_ONLY,
            }
            and parameter.default
            is inspect.Parameter.empty
            and name
            not in accepted_values
        )
    ]

    if missing_parameters:
        if len(
            parameters
        ) == 3:
            return operator(
                Q_n,
                D_n,
                A_n,
            )

        raise TypeError(
            (
                "Phi operator has "
                "unsupported required "
                "parameters: "
                f"{missing_parameters}"
            )
        )

    return operator(
        **accepted_values
    )


def _import_symbol(
    reference: str,
) -> Any:
    reference = str(
        reference
    ).strip()

    if not reference:
        raise ValueError(
            (
                "Import reference "
                "must not be empty."
            )
        )

    if ":" in reference:
        module_name, symbol_name = (
            reference.split(
                ":",
                1,
            )
        )

    else:
        (
            module_name,
            separator,
            symbol_name,
        ) = reference.rpartition(
            "."
        )

        if not separator:
            raise ValueError(
                (
                    "Import reference must use "
                    "'module:symbol' or "
                    "'module.symbol'."
                )
            )

    module = importlib.import_module(
        module_name
    )

    return getattr(
        module,
        symbol_name,
    )


def load_configuration(
    path: str | Path,
) -> dict[str, Any]:
    configuration_path = Path(
        path
    )

    with configuration_path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        data = json.load(
            handle
        )

    if not isinstance(
        data,
        dict,
    ):
        raise ValueError(
            (
                "Configuration root "
                "must be a JSON object."
            )
        )

    return data


def build_orchestrator_from_configuration(
    configuration: Mapping[str, Any],
    *,
    output_directory_override: (
        str | Path | None
    ) = None,
    dt_override: float | None = None,
    execution_mode_override: (
        str | None
    ) = None,
) -> EDKHierarchicalOrchestrator:
    registry = EDKModuleRegistry()

    for specification in configuration.get(
        "modules",
        [],
    ):
        if not isinstance(
            specification,
            Mapping,
        ):
            raise ValueError(
                (
                    "Each modules entry "
                    "must be a JSON object."
                )
            )

        class_reference = (
            specification.get(
                "adapter_class"
            )
        )

        if not class_reference:
            raise ValueError(
                (
                    "Each module entry "
                    "requires adapter_class."
                )
            )

        adapter_class = _import_symbol(
            str(
                class_reference
            )
        )

        adapter_kwargs = dict(
            specification.get(
                "kwargs",
                {},
            )
        )

        adapter = adapter_class(
            **adapter_kwargs
        )

        registry.register(
            adapter
        )

    initial_state = EDKHierarchicalState(
        **dict(
            configuration.get(
                "initial_state",
                {},
            )
        )
    )

    phi_operator: (
        PhiOperator | None
    ) = None

    phi_reference = configuration.get(
        "phi_operator"
    )

    if phi_reference:
        phi_operator = _import_symbol(
            str(
                phi_reference
            )
        )

    if (
        output_directory_override
        is not None
    ):
        output_directory = (
            output_directory_override
        )
    else:
        output_directory = (
            configuration.get(
                "output_directory",
                "edk_hierarchical_output",
            )
        )

    if dt_override is not None:
        dt = float(
            dt_override
        )
    else:
        dt = float(
            configuration.get(
                "dt",
                0.005,
            )
        )

    if (
        execution_mode_override
        is not None
    ):
        execution_mode = (
            execution_mode_override
        )
    else:
        execution_mode = (
            configuration.get(
                "execution_mode",
                "complete",
            )
        )

    logger = EDKHierarchicalLogger(
        output_directory
    )

    return EDKHierarchicalOrchestrator(
        registry=registry,
        initial_state=initial_state,
        phi_operator=phi_operator,
        logger=logger,
        dt=dt,
        execution_mode=execution_mode,
        critical_band=float(
            configuration.get(
                "critical_band",
                0.0,
            )
        ),
        required_stages=tuple(
            configuration.get(
                "required_stages",
                DEFAULT_REQUIRED_STAGES,
            )
        ),
        mandatory_fields=tuple(
            configuration.get(
                "mandatory_fields",
                MANDATORY_INTEGRATION_FIELDS,
            )
        ),
        log_every_tact=bool(
            configuration.get(
                "log_every_tact",
                True,
            )
        ),
    )


def _deep_copy_mapping(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        str(
            key
        ): _deep_copy_value(
            item
        )
        for key, item in value.items()
    }


def _deep_copy_value(
    value: Any,
) -> Any:
    if isinstance(
        value,
        np.ndarray,
    ):
        return value.copy()

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        copy_method = getattr(
            value,
            "copy",
            None,
        )

        if callable(
            copy_method
        ):
            return copy_method()

    if isinstance(
        value,
        Mapping,
    ):
        return _deep_copy_mapping(
            value
        )

    if isinstance(
        value,
        list,
    ):
        return [
            _deep_copy_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        tuple,
    ):
        return tuple(
            _deep_copy_value(
                item
            )
            for item in value
        )

    if isinstance(
        value,
        set,
    ):
        return {
            _deep_copy_value(
                item
            )
            for item in value
        }

    try:
        return copy.deepcopy(
            value
        )

    except Exception:
        return value


def _detect_backend(
    value: Any,
) -> str:
    if isinstance(
        value,
        np.ndarray,
    ):
        return "numpy"

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        return "cupy"

    return "agnostic"


def _dtype_and_shape(
    value: Any,
) -> tuple[
    str | None,
    tuple[int, ...] | None,
]:
    if isinstance(
        value,
        np.ndarray,
    ):
        return (
            str(
                value.dtype
            ),
            tuple(
                int(
                    item
                )
                for item in value.shape
            ),
        )

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        dtype = getattr(
            value,
            "dtype",
            None,
        )

        shape = getattr(
            value,
            "shape",
            None,
        )

        return (
            (
                str(
                    dtype
                )
                if dtype is not None
                else None
            ),
            (
                tuple(
                    int(
                        item
                    )
                    for item in shape
                )
                if shape is not None
                else None
            ),
        )

    if isinstance(
        value,
        np.generic,
    ):
        return (
            str(
                value.dtype
            ),
            (),
        )

    if isinstance(
        value,
        (
            bool,
            int,
            float,
            complex,
            str,
        ),
    ):
        return (
            type(
                value
            ).__name__,
            (),
        )

    return (
        None,
        None,
    )


def _is_finite_value(
    value: Any,
) -> bool:
    bad_paths: list[str] = []

    _collect_non_finite_paths(
        value,
        "value",
        bad_paths,
    )

    return not bad_paths


def _collect_non_finite_paths(
    value: Any,
    path: str,
    bad_paths: list[str],
) -> None:
    if value is None:
        return

    if isinstance(
        value,
        Mapping,
    ):
        for key, item in value.items():
            _collect_non_finite_paths(
                item,
                f"{path}.{key}",
                bad_paths,
            )

        return

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        for index, item in enumerate(
            value
        ):
            _collect_non_finite_paths(
                item,
                f"{path}[{index}]",
                bad_paths,
            )

        return

    if isinstance(
        value,
        np.ndarray,
    ):
        if not np.all(
            np.isfinite(
                value
            )
        ):
            bad_paths.append(
                path
            )

        return

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        array = _to_numpy(
            value
        )

        if not np.all(
            np.isfinite(
                array
            )
        ):
            bad_paths.append(
                path
            )

        return

    if isinstance(
        value,
        np.generic,
    ):
        if not bool(
            np.isfinite(
                value
            )
        ):
            bad_paths.append(
                path
            )

        return

    if isinstance(
        value,
        float,
    ):
        if not math.isfinite(
            value
        ):
            bad_paths.append(
                path
            )

        return

    if isinstance(
        value,
        complex,
    ):
        if not (
            math.isfinite(
                value.real
            )
            and math.isfinite(
                value.imag
            )
        ):
            bad_paths.append(
                path
            )


def _collect_array_backends(
    value: Any,
    backends: set[str],
) -> None:
    if isinstance(
        value,
        Mapping,
    ):
        for item in value.values():
            _collect_array_backends(
                item,
                backends,
            )

        return

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        for item in value:
            _collect_array_backends(
                item,
                backends,
            )

        return

    if isinstance(
        value,
        np.ndarray,
    ):
        backends.add(
            "numpy"
        )

    elif hasattr(
        value,
        "__cuda_array_interface__",
    ):
        backends.add(
            "cupy"
        )


def _to_numpy(
    value: Any,
) -> np.ndarray:
    if isinstance(
        value,
        np.ndarray,
    ):
        return value.copy()

    get_method = getattr(
        value,
        "get",
        None,
    )

    if callable(
        get_method
    ):
        return np.asarray(
            get_method()
        )

    return np.asarray(
        value
    )


def _subtract(
    left: Any,
    right: Any,
) -> Any:
    if (
        hasattr(
            left,
            "__cuda_array_interface__",
        )
        or hasattr(
            right,
            "__cuda_array_interface__",
        )
    ):
        return (
            left
            - right
        )

    if (
        isinstance(
            left,
            np.ndarray,
        )
        or isinstance(
            right,
            np.ndarray,
        )
    ):
        return (
            np.asarray(
                left
            )
            - np.asarray(
                right
            )
        )

    return (
        left
        - right
    )


def _reduce_to_scalar(
    value: Any,
) -> float:
    if isinstance(
        value,
        np.ndarray,
    ):
        return float(
            np.mean(
                value
            )
        )

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        return float(
            np.mean(
                _to_numpy(
                    value
                )
            )
        )

    if isinstance(
        value,
        np.generic,
    ):
        return float(
            value.item()
        )

    return float(
        value
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
        FieldProvenance,
    ):
        return _json_safe(
            asdict(
                value
            )
        )

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
            for item in value
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
            "backend": "numpy",
            "dtype": str(
                value.dtype
            ),
            "shape": list(
                value.shape
            ),
        }

    if hasattr(
        value,
        "__cuda_array_interface__",
    ):
        array = _to_numpy(
            value
        )

        return {
            "__array__": True,
            "backend": "cupy",
            "dtype": str(
                array.dtype
            ),
            "shape": list(
                array.shape
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
        Path,
    ):
        return str(
            value
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
        (
            str,
            int,
            float,
            bool,
        ),
    ):
        return value

    if hasattr(
        value,
        "__dict__",
    ):
        return _json_safe(
            vars(
                value
            )
        )

    return repr(
        value
    )


def _collect_arrays(
    value: Any,
    path: str,
    arrays: MutableMapping[
        str,
        np.ndarray,
    ],
) -> None:
    if isinstance(
        value,
        Mapping,
    ):
        for key, item in value.items():
            if path:
                next_path = (
                    f"{path}.{key}"
                )
            else:
                next_path = str(
                    key
                )

            _collect_arrays(
                item,
                next_path,
                arrays,
            )

        return

    if isinstance(
        value,
        (
            list,
            tuple,
        ),
    ):
        for index, item in enumerate(
            value
        ):
            _collect_arrays(
                item,
                f"{path}[{index}]",
                arrays,
            )

        return

    if isinstance(
        value,
        np.ndarray,
    ):
        arrays[
            path or "array"
        ] = value.copy()

    elif hasattr(
        value,
        "__cuda_array_interface__",
    ):
        arrays[
            path or "array"
        ] = _to_numpy(
            value
        )


def _sanitize_npz_key(
    key: str,
) -> str:
    sanitized = (
        key
        .replace(
            ".",
            "__",
        )
        .replace(
            "[",
            "_",
        )
        .replace(
            "]",
            "",
        )
        .replace(
            "/",
            "_",
        )
        .replace(
            "\\",
            "_",
        )
        .replace(
            " ",
            "_",
        )
    )

    return (
        sanitized
        or "array"
    )


def _fsync_directory(
    directory: Path,
) -> None:
    if not hasattr(
        os,
        "O_DIRECTORY",
    ):
        return

    descriptor = os.open(
        str(
            directory
        ),
        (
            os.O_RDONLY
            | os.O_DIRECTORY
        ),
    )

    try:
        os.fsync(
            descriptor
        )

    finally:
        os.close(
            descriptor
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Run the EDK hierarchical "
            "tact-by-tact orchestrator."
        )
    )

    parser.add_argument(
        "--config",
        type=Path,
        required=True,
    )

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
    )

    parser.add_argument(
        "--tacts",
        type=int,
        default=None,
        help=(
            "Number of tact-by-tact "
            "hierarchical intervals."
        ),
    )

    parser.add_argument(
        "--steps",
        type=int,
        default=None,
        help=(
            "Compatibility alias for --tacts. "
            "If --tacts is provided, --tacts "
            "takes priority."
        ),
    )

    parser.add_argument(
        "--dt",
        type=float,
        default=None,
    )

    parser.add_argument(
        "--execution-mode",
        choices=[
            mode.value
            for mode in ExecutionMode
        ],
        default=None,
    )

    arguments = parser.parse_args()

    configuration = load_configuration(
        arguments.config
    )

    orchestrator = (
        build_orchestrator_from_configuration(
            configuration,
            output_directory_override=(
                arguments.output_dir
            ),
            dt_override=arguments.dt,
            execution_mode_override=(
                arguments.execution_mode
            ),
        )
    )

    total_tacts = (
        arguments.tacts
        if arguments.tacts is not None
        else arguments.steps
        if arguments.steps is not None
        else 1
    )

    summary = orchestrator.run(
        total_tacts
    )

    print(
        json.dumps(
            _json_safe(
                summary
            ),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
