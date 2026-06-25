from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("MPLBACKEND", "Agg")

import numpy as np

try:
    from .edk_hierarchical_orchestrator import (
        DEFAULT_REQUIRED_STAGES,
        MANDATORY_INTEGRATION_FIELDS,
        STAGE_ORDER,
        CallableModuleAdapter,
        DynamicRegime,
        EDKForwardCascadePacket,
        EDKHierarchicalOrchestrator,
        EDKModuleRegistry,
        EDKOrchestratorError,
        ExecutionMode,
        FieldProvenance,
        RunStatus,
        load_configuration,
    )
    from .hierarchical_diagnostics import (
        EDKHierarchicalDiagnostics,
    )
    from .smoke_test import (
        build_initial_state,
        build_orchestrator,
        build_registry,
        failing_phi_operator,
    )
except ImportError:
    from edk_hierarchical_orchestrator import (
        DEFAULT_REQUIRED_STAGES,
        MANDATORY_INTEGRATION_FIELDS,
        STAGE_ORDER,
        CallableModuleAdapter,
        DynamicRegime,
        EDKForwardCascadePacket,
        EDKHierarchicalOrchestrator,
        EDKModuleRegistry,
        EDKOrchestratorError,
        ExecutionMode,
        FieldProvenance,
        RunStatus,
        load_configuration,
    )
    from hierarchical_diagnostics import (
        EDKHierarchicalDiagnostics,
    )
    from smoke_test import (
        build_initial_state,
        build_orchestrator,
        build_registry,
        failing_phi_operator,
    )


def make_adapter(
    *,
    module_name: str = "test_adapter",
    stage_name: str = "solar",
    required_inputs: tuple[str, ...] = ("Q_n",),
    provided_outputs: tuple[str, ...] = ("solar_drive",),
    backend: str = "numpy",
    mandatory: bool = True,
) -> CallableModuleAdapter:
    return CallableModuleAdapter(
        module_name=module_name,
        stage_name=stage_name,
        required_inputs=required_inputs,
        provided_outputs=provided_outputs,
        mandatory=mandatory,
        backend=backend,
        step_callable=lambda packet, state, dt: {
            "solar_drive": np.asarray(
                packet.payload["Q_n"],
                dtype=np.float64,
            )
            + dt
        },
        state_exporter=lambda: {
            "module_feedback": {
                "module_name": module_name,
            }
        },
    )


class HierarchicalConstantsTests(unittest.TestCase):
    def test_stage_order_is_fixed_and_complete(self) -> None:
        self.assertEqual(
            STAGE_ORDER,
            (
                "solar",
                "planetary",
                "bio_planetary",
                "continuum_core",
                "interface_tensor",
                "massless_exchange_channel",
                "wave_genetics",
                "molecular_phase_chemistry",
                "feedback",
            ),
        )

        self.assertEqual(
            DEFAULT_REQUIRED_STAGES,
            STAGE_ORDER,
        )

        self.assertEqual(
            MANDATORY_INTEGRATION_FIELDS,
            (
                "Q_n",
                "D_n",
                "A_n",
                "P_t",
                "T_int",
                "J_flux",
            ),
        )


class HierarchicalPacketAndStateTests(unittest.TestCase):
    def test_forward_packet_is_immutable_and_detached(self) -> None:
        source_array = np.asarray(
            [1.0, 2.0],
            dtype=np.float64,
        )

        source_payload = {
            "Q_n": source_array,
            "nested": {
                "value": 3.0,
            },
        }

        packet = EDKForwardCascadePacket(
            source_stage="state",
            target_stage="solar",
            tact_index=0,
            simulation_time=0.0,
            payload=source_payload,
            field_provenance={},
        )

        source_array[0] = 99.0
        source_payload["nested"]["value"] = 77.0

        np.testing.assert_array_equal(
            packet.payload["Q_n"],
            np.asarray(
                [1.0, 2.0],
                dtype=np.float64,
            ),
        )

        self.assertEqual(
            packet.payload["nested"]["value"],
            3.0,
        )

        with self.assertRaises(TypeError):
            packet.payload["new_field"] = 1.0

    def test_state_clone_is_deep_and_independent(self) -> None:
        state = build_initial_state()

        state.module_states["test"] = {
            "array": np.asarray(
                [1.0, 2.0],
            ),
        }

        state.operational_fields["nested"] = {
            "value": [1, 2, 3],
        }

        clone = state.clone()

        clone.Q_n[0] = 100.0
        clone.module_states["test"]["array"][0] = 200.0
        clone.operational_fields["nested"]["value"][0] = 300

        self.assertNotEqual(
            float(state.Q_n[0]),
            100.0,
        )

        self.assertNotEqual(
            float(
                state.module_states[
                    "test"
                ][
                    "array"
                ][
                    0
                ]
            ),
            200.0,
        )

        self.assertEqual(
            state.operational_fields[
                "nested"
            ][
                "value"
            ][
                0
            ],
            1,
        )

    def test_state_rejects_non_finite_values(self) -> None:
        state = build_initial_state()

        state.operational_fields["invalid"] = np.asarray(
            [
                1.0,
                float("nan"),
            ],
            dtype=np.float64,
        )

        with self.assertRaises(
            EDKOrchestratorError
        ) as context:
            state.validate_finite()

        self.assertIs(
            context.exception.status,
            RunStatus.NON_FINITE_STATE,
        )

        self.assertIn(
            "invalid",
            context.exception.details[
                "paths"
            ],
        )

    def test_field_provenance_records_transition_history(
        self,
    ) -> None:
        provenance = FieldProvenance(
            field_name="J_flux",
            source_module="source_module",
            source_stage=(
                "massless_exchange_channel"
            ),
            tact_index=0,
            backend="numpy",
            dtype="float64",
            shape=(),
        )

        updated = provenance.next(
            source_module="feedback_module",
            source_stage="feedback",
            tact_index=1,
            backend="numpy",
            value=np.asarray(
                [1.0, 2.0],
            ),
        )

        self.assertEqual(
            updated.field_name,
            "J_flux",
        )

        self.assertEqual(
            updated.source_module,
            "feedback_module",
        )

        self.assertEqual(
            updated.source_stage,
            "feedback",
        )

        self.assertEqual(
            updated.tact_index,
            1,
        )

        self.assertEqual(
            updated.shape,
            (2,),
        )

        self.assertEqual(
            len(
                updated.transition_history
            ),
            1,
        )

        self.assertEqual(
            updated.transition_history[
                0
            ][
                "from_module"
            ],
            "source_module",
        )

        self.assertEqual(
            updated.transition_history[
                0
            ][
                "to_module"
            ],
            "feedback_module",
        )


class ModuleRegistryTests(unittest.TestCase):
    def test_registration_order_and_description(
        self,
    ) -> None:
        registry = EDKModuleRegistry()

        solar = make_adapter(
            module_name="solar_adapter",
            stage_name="solar",
        )

        feedback = make_adapter(
            module_name="feedback_adapter",
            stage_name="feedback",
            required_inputs=(),
            provided_outputs=(
                "feedback_value",
            ),
        )

        registry.register(
            feedback
        )

        registry.register(
            solar
        )

        self.assertEqual(
            tuple(
                adapter.module_name
                for adapter
                in registry.ordered_adapters()
            ),
            (
                "solar_adapter",
                "feedback_adapter",
            ),
        )

        self.assertEqual(
            registry.registered_stages(),
            (
                "solar",
                "feedback",
            ),
        )

        self.assertIs(
            registry.get(
                "solar_adapter"
            ),
            solar,
        )

        description = (
            registry.describe()
        )

        self.assertEqual(
            description[
                "stage_order"
            ],
            list(
                STAGE_ORDER
            ),
        )

        self.assertEqual(
            [
                item[
                    "module_name"
                ]
                for item
                in description[
                    "modules"
                ]
            ],
            [
                "solar_adapter",
                "feedback_adapter",
            ],
        )

    def test_duplicate_module_name_is_rejected(
        self,
    ) -> None:
        registry = EDKModuleRegistry()

        registry.register(
            make_adapter(
                module_name="duplicate"
            )
        )

        with self.assertRaises(
            EDKOrchestratorError
        ) as context:
            registry.register(
                make_adapter(
                    module_name="duplicate"
                )
            )

        self.assertIs(
            context.exception.status,
            (
                RunStatus
                .MODULE_REGISTRATION_FAILED
            ),
        )

    def test_invalid_stage_backend_and_duplicate_fields_are_rejected(
        self,
    ) -> None:
        cases = (
            make_adapter(
                stage_name="unknown"
            ),
            make_adapter(
                backend="invalid"
            ),
            make_adapter(
                required_inputs=(
                    "Q_n",
                    "Q_n",
                )
            ),
            make_adapter(
                provided_outputs=(
                    "x",
                    "x",
                )
            ),
        )

        for adapter in cases:
            with self.subTest(
                adapter=adapter
            ):
                with self.assertRaises(
                    EDKOrchestratorError
                ) as context:
                    EDKModuleRegistry().register(
                        adapter
                    )

                self.assertIs(
                    context.exception.status,
                    (
                        RunStatus
                        .MODULE_REGISTRATION_FAILED
                    ),
                )

    def test_missing_required_stage_is_rejected(
        self,
    ) -> None:
        registry = EDKModuleRegistry()

        registry.register(
            make_adapter(
                stage_name="solar"
            )
        )

        with self.assertRaises(
            EDKOrchestratorError
        ) as context:
            registry.validate_required_stages(
                (
                    "solar",
                    "feedback",
                )
            )

        self.assertIs(
            context.exception.status,
            RunStatus.MANDATORY_STAGE_MISSING,
        )

        self.assertEqual(
            context.exception.details[
                "missing_stages"
            ],
            [
                "feedback",
            ],
        )


class OrchestratorConfigurationTests(
    unittest.TestCase
):
    def test_invalid_dt_is_rejected(self) -> None:
        for invalid_dt in (
            0.0,
            -0.01,
            float("inf"),
            float("nan"),
        ):
            with self.subTest(
                dt=invalid_dt
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    (
                        "dt must be a finite "
                        "positive value"
                    ),
                ):
                    EDKHierarchicalOrchestrator(
                        dt=invalid_dt
                    )

    def test_invalid_critical_band_is_rejected(
        self,
    ) -> None:
        for invalid_band in (
            -0.01,
            float("inf"),
            float("nan"),
        ):
            with self.subTest(
                critical_band=invalid_band
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    (
                        "critical_band must be "
                        "finite and non-negative"
                    ),
                ):
                    EDKHierarchicalOrchestrator(
                        critical_band=(
                            invalid_band
                        )
                    )

    def test_unknown_required_stage_is_rejected(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "Unknown required stages",
        ):
            EDKHierarchicalOrchestrator(
                required_stages=(
                    "solar",
                    "unknown",
                ),
            )

    def test_negative_tact_count_is_rejected(
        self,
    ) -> None:
        orchestrator = (
            EDKHierarchicalOrchestrator(
                execution_mode=(
                    ExecutionMode.PARTIAL
                ),
                required_stages=(),
                mandatory_fields=(),
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "tact_count must be "
                "non-negative"
            ),
        ):
            orchestrator.run(
                -1
            )

    def test_configuration_loader_accepts_object_and_rejects_non_object(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            valid_path = (
                Path(directory)
                / "valid.json"
            )

            invalid_path = (
                Path(directory)
                / "invalid.json"
            )

            valid_path.write_text(
                json.dumps(
                    {
                        "dt": 0.01,
                    }
                ),
                encoding="utf-8",
            )

            invalid_path.write_text(
                json.dumps(
                    [
                        "not",
                        "an",
                        "object",
                    ]
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                load_configuration(
                    valid_path
                ),
                {
                    "dt": 0.01,
                },
            )

            with self.assertRaisesRegex(
                ValueError,
                (
                    "Configuration root "
                    "must be a JSON object"
                ),
            ):
                load_configuration(
                    invalid_path
                )


class OrchestratorExecutionTests(
    unittest.TestCase
):
    def test_complete_hierarchical_run_preserves_t_int_and_j_flux(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_directory = Path(
                directory
            )

            orchestrator = (
                build_orchestrator(
                    output_directory,
                    dt=0.01,
                )
            )

            initial_q = np.asarray(
                orchestrator.state.Q_n,
                dtype=np.float64,
            ).copy()

            summary = orchestrator.run(
                3
            )

            self.assertEqual(
                summary[
                    "status"
                ],
                RunStatus.COMPLETED.value,
            )

            self.assertEqual(
                summary[
                    "completed_tacts"
                ],
                3,
            )

            self.assertEqual(
                orchestrator.state.tact_index,
                3,
            )

            self.assertAlmostEqual(
                (
                    orchestrator
                    .state
                    .simulation_time
                ),
                0.03,
            )

            self.assertEqual(
                (
                    orchestrator
                    .state
                    .dynamic_regime
                ),
                (
                    DynamicRegime
                    .ENDOGENOUS_DYNAMIC_STABILITY
                    .value
                ),
            )

            self.assertIsNotNone(
                orchestrator.state.T_int
            )

            self.assertIsNotNone(
                orchestrator.state.J_flux
            )

            self.assertIn(
                "T_int",
                (
                    orchestrator
                    .state
                    .field_provenance
                ),
            )

            self.assertIn(
                "J_flux",
                (
                    orchestrator
                    .state
                    .field_provenance
                ),
            )

            self.assertFalse(
                np.allclose(
                    np.asarray(
                        orchestrator.state.Q_n
                    ),
                    initial_q,
                )
            )

            expected_modules = {
                adapter.module_name
                for adapter
                in (
                    orchestrator
                    .registry
                    .ordered_adapters()
                )
            }

            self.assertEqual(
                set(
                    orchestrator
                    .state
                    .module_states
                ),
                expected_modules,
            )

            for tact_index in range(
                1,
                4,
            ):
                json_path = (
                    output_directory
                    / (
                        "hierarchical_step_"
                        f"{tact_index:06d}.json"
                    )
                )

                npz_path = (
                    output_directory
                    / (
                        "hierarchical_field_"
                        f"{tact_index:06d}.npz"
                    )
                )

                self.assertTrue(
                    json_path.is_file()
                )

                self.assertTrue(
                    npz_path.is_file()
                )

                metadata = json.loads(
                    json_path.read_text(
                        encoding="utf-8"
                    )
                )

                self.assertEqual(
                    metadata[
                        "status"
                    ],
                    (
                        RunStatus
                        .COMPLETED
                        .value
                    ),
                )

                self.assertIsNotNone(
                    metadata[
                        "state"
                    ][
                        "T_int"
                    ]
                )

                self.assertIsNotNone(
                    metadata[
                        "state"
                    ][
                        "J_flux"
                    ]
                )

                with np.load(
                    npz_path,
                    allow_pickle=False,
                ) as archive:
                    self.assertGreater(
                        len(
                            archive.files
                        ),
                        0,
                    )

            summary_path = (
                output_directory
                / "hierarchical_summary.json"
            )

            self.assertTrue(
                summary_path.is_file()
            )

    def test_partial_mode_runs_without_registered_modules_or_phi(
        self,
    ) -> None:
        initial_state = (
            build_initial_state()
        )

        initial_q = np.asarray(
            initial_state.Q_n
        ).copy()

        orchestrator = (
            EDKHierarchicalOrchestrator(
                registry=(
                    EDKModuleRegistry()
                ),
                initial_state=(
                    initial_state
                ),
                phi_operator=None,
                logger=None,
                dt=0.01,
                execution_mode=(
                    ExecutionMode.PARTIAL
                ),
                critical_band=0.0,
                required_stages=(),
                mandatory_fields=(),
                log_every_tact=False,
            )
        )

        state = (
            orchestrator.run_tact()
        )

        self.assertEqual(
            state.tact_index,
            1,
        )

        self.assertAlmostEqual(
            state.simulation_time,
            0.01,
        )

        np.testing.assert_array_equal(
            state.Q_n,
            initial_q,
        )

        skipped_events = [
            event
            for event
            in state.transition_events
            if (
                event[
                    "event"
                ]
                == "STAGE_SKIPPED"
            )
        ]

        self.assertEqual(
            len(
                skipped_events
            ),
            len(
                STAGE_ORDER
            ),
        )

    def test_dynamic_regime_classification_uses_c_t_minus_p_t(
        self,
    ) -> None:
        cases = (
            (
                0.90,
                0.20,
                (
                    DynamicRegime
                    .ENDOGENOUS_DYNAMIC_STABILITY
                ),
            ),
            (
                0.50,
                0.50,
                (
                    DynamicRegime
                    .ENDOGENOUS_DYNAMIC_CRITICALITY
                ),
            ),
            (
                0.20,
                0.90,
                (
                    DynamicRegime
                    .DEGRADATION_DRIFT
                ),
            ),
        )

        for C_t, P_t, expected in cases:
            with self.subTest(
                C_t=C_t,
                P_t=P_t,
            ):
                state = (
                    build_initial_state()
                )

                state.C_t = C_t
                state.P_t = P_t

                orchestrator = (
                    EDKHierarchicalOrchestrator(
                        initial_state=state,
                        dt=0.01,
                        execution_mode=(
                            ExecutionMode.PARTIAL
                        ),
                        required_stages=(),
                        mandatory_fields=(),
                        critical_band=0.01,
                        log_every_tact=False,
                    )
                )

                next_state = (
                    orchestrator.run_tact()
                )

                self.assertEqual(
                    (
                        next_state
                        .dynamic_regime
                    ),
                    expected.value,
                )

                self.assertAlmostEqual(
                    float(
                        next_state
                        .retention_margin
                    ),
                    C_t - P_t,
                )

    def test_missing_stage_t_int_j_flux_backend_nonfinite_and_phi_failures(
        self,
    ) -> None:
        cases = []

        with tempfile.TemporaryDirectory() as root:
            root_path = Path(
                root
            )

            cases.append(
                (
                    (
                        RunStatus
                        .MANDATORY_STAGE_MISSING
                    ),
                    build_orchestrator(
                        (
                            root_path
                            / "missing_stage"
                        ),
                        registry=build_registry(
                            omit_stage=(
                                "wave_genetics"
                            )
                        ),
                    ),
                )
            )

            state_without_t_int = (
                build_initial_state()
            )

            state_without_t_int.T_int = None

            state_without_t_int.field_provenance.pop(
                "T_int",
                None,
            )

            cases.append(
                (
                    RunStatus.T_INT_MISSING,
                    build_orchestrator(
                        (
                            root_path
                            / "missing_t_int"
                        ),
                        registry=build_registry(
                            omit_t_int=True
                        ),
                        initial_state=(
                            state_without_t_int
                        ),
                    ),
                )
            )

            state_without_j_flux = (
                build_initial_state()
            )

            state_without_j_flux.J_flux = None

            state_without_j_flux.field_provenance.pop(
                "J_flux",
                None,
            )

            cases.append(
                (
                    RunStatus.J_FLUX_MISSING,
                    build_orchestrator(
                        (
                            root_path
                            / "missing_j_flux"
                        ),
                        registry=build_registry(
                            omit_j_flux=True
                        ),
                        initial_state=(
                            state_without_j_flux
                        ),
                    ),
                )
            )

            cases.append(
                (
                    RunStatus.BACKEND_MISMATCH,
                    build_orchestrator(
                        (
                            root_path
                            / "backend_mismatch"
                        ),
                        registry=build_registry(
                            backend_mismatch=True
                        ),
                    ),
                )
            )

            cases.append(
                (
                    RunStatus.NON_FINITE_STATE,
                    build_orchestrator(
                        (
                            root_path
                            / "non_finite"
                        ),
                        registry=build_registry(
                            non_finite_solar=True
                        ),
                    ),
                )
            )

            cases.append(
                (
                    (
                        RunStatus
                        .RECURSIVE_UPDATE_FAILED
                    ),
                    build_orchestrator(
                        (
                            root_path
                            / "phi_failure"
                        ),
                        phi=(
                            failing_phi_operator
                        ),
                    ),
                )
            )

            for (
                expected_status,
                orchestrator,
            ) in cases:
                with self.subTest(
                    status=(
                        expected_status
                    )
                ):
                    with self.assertRaises(
                        EDKOrchestratorError
                    ) as context:
                        orchestrator.run_tact()

                    self.assertIs(
                        context.exception.status,
                        expected_status,
                    )

    def test_diagnostics_loads_valid_hierarchical_output(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(
                directory
            )

            source = (
                root
                / "source"
            )

            diagnostics_output = (
                root
                / "diagnostics"
            )

            orchestrator = (
                build_orchestrator(
                    source,
                    dt=0.01,
                )
            )

            orchestrator.run(
                1
            )

            diagnostics = (
                EDKHierarchicalDiagnostics(
                    input_directory=source,
                    output_directory=(
                        diagnostics_output
                    ),
                    strict=False,
                )
            )

            summary = diagnostics.run(
                create_plots=False,
                create_report=True,
            )

            self.assertEqual(
                summary.record_count,
                1,
            )

            self.assertEqual(
                summary.first_tact,
                1,
            )

            self.assertEqual(
                summary.last_tact,
                1,
            )

            self.assertEqual(
                summary.issue_counts.get(
                    "ERROR",
                    0,
                ),
                0,
            )

            self.assertTrue(
                (
                    diagnostics_output
                    / (
                        "hierarchical_"
                        "diagnostics.json"
                    )
                ).is_file()
            )

            self.assertTrue(
                (
                    diagnostics_output
                    / (
                        "hierarchical_"
                        "diagnostics.md"
                    )
                ).is_file()
            )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
