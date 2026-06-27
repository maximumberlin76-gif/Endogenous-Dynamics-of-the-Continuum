from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

try:
    from .marnov_retention_collapse_protocol import (
        EDKMarnovProtocolLogger,
        EDKMarnovRetentionCollapseProtocol,
        MarnovRetentionCollapseConfig,
    )
except ImportError:
    from marnov_retention_collapse_protocol import (
        EDKMarnovProtocolLogger,
        EDKMarnovRetentionCollapseProtocol,
        MarnovRetentionCollapseConfig,
    )

try:
    from module_edk_gpu_mean_field_phase_engine import (
        EDKGPUMeanFieldPhaseEngine,
        MeanFieldPhaseConfig,
    )
except ImportError:
    try:
        from edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_gpu_mean_field_phase_engine import (
            EDKGPUMeanFieldPhaseEngine,
            MeanFieldPhaseConfig,
        )


def build_engine(
    seed: int = 31,
    num_domains: int = 64,
) -> EDKGPUMeanFieldPhaseEngine:
    return EDKGPUMeanFieldPhaseEngine(
        MeanFieldPhaseConfig(
            num_domains=num_domains,
            coupling_strength_k=18.0,
            sakaguchi_phase_lag_alpha=0.0,
            natural_frequency_mean=0.0,
            natural_frequency_std=0.05,
            external_forcing_phase=0.0,
            phase_noise_strength=0.02,
            amplitude_growth_rate=1.0,
            amplitude_saturation_rate=1.0,
            amplitude_noise_strength=0.01,
            amplitude_minimum=0.1,
            amplitude_maximum=3.0,
            initial_amplitude_minimum=0.8,
            initial_amplitude_maximum=1.2,
            seed=seed,
            dtype="float32",
            backend="cpu",
            device_id=0,
        )
    )


def build_config(
    **changes: object,
) -> MarnovRetentionCollapseConfig:
    base = MarnovRetentionCollapseConfig(
        formation_maximum_tacts=500,
        formation_confirmation_tacts=3,
        retained_verification_tacts=2,
        critical_loading_maximum_tacts=500,
        maximum_post_unlock_tacts=300,
        minimum_post_unlock_tacts=2,
        R_form_min=0.70,
        phase_amplitude_form_min=0.70,
        phase_velocity_dispersion_form_max=3.0,
        amplitude_dispersion_form_max=0.20,
        coherence_weight_R=0.40,
        coherence_weight_phase_amplitude=0.40,
        coherence_weight_phase_velocity=0.10,
        coherence_weight_amplitude=0.10,
        phase_velocity_reference=2.0,
        amplitude_dispersion_reference=0.20,
        retained_boundary_tolerance=0.02,
        pressure_schedule="step",
        pressure_hold=0.05,
        pressure_collapse=1.0,
        pressure_ramp_rate=1.0,
        delay_base_tau_0=0.02,
        pressure_velocity_coefficient_mu=5.0,
        delay_regularization_epsilon=1.0e-9,
        minimum_delay_tau=1.0e-6,
        critical_exposure_threshold=0.25,
        exposure_recovery_mode="decaying",
        exposure_recovery_rate=0.25,
        coupling_quench_mode="exponential",
        coupling_floor=0.0,
        coupling_quench_tau=0.01,
        post_unlock_phase_noise_multiplier=100.0,
        post_unlock_frequency_dispersion_multiplier=100.0,
        post_unlock_amplitude_decay_scale=2.0,
        phase_order_collapse_threshold=0.05,
        phase_order_collapse_fraction=0.50,
        phase_amplitude_collapse_threshold=0.0,
        phase_velocity_dispersion_collapse_threshold=1.0e9,
        collapse_logic="any",
        log_every=0,
        field_every=0,
    )

    return replace(
        base,
        **changes,
    )


def build_protocol(
    seed: int = 31,
    num_domains: int = 64,
    **config_changes: object,
) -> EDKMarnovRetentionCollapseProtocol:
    return EDKMarnovRetentionCollapseProtocol(
        build_engine(
            seed,
            num_domains,
        ),
        build_config(
            **config_changes
        ),
    )


class ConfigurationTests(
    unittest.TestCase
):
    def test_valid_configuration(
        self,
    ) -> None:
        build_config().validate(
            18.0
        )

    def test_invalid_configuration_values(
        self,
    ) -> None:
        cases = (
            (
                {
                    "formation_maximum_tacts": 0,
                },
                (
                    "formation_maximum_tacts "
                    "must be at least 1"
                ),
            ),
            (
                {
                    "formation_maximum_tacts": 2,
                    "formation_confirmation_tacts": 3,
                },
                (
                    "formation_confirmation_tacts "
                    "exceeds formation_maximum_tacts"
                ),
            ),
            (
                {
                    "pressure_collapse": 1.1,
                },
                "pressure_collapse must be within",
            ),
            (
                {
                    "retained_boundary_tolerance": -0.01,
                },
                (
                    "retained_boundary_tolerance "
                    "must be finite and non-negative"
                ),
            ),
            (
                {
                    "delay_base_tau_0": 0.0,
                },
                (
                    "delay_base_tau_0 must be "
                    "a positive finite value"
                ),
            ),
            (
                {
                    "coherence_weight_R": -0.10,
                    "coherence_weight_phase_amplitude": 0.50,
                },
                (
                    "Coherence-proxy weights "
                    "must be non-negative"
                ),
            ),
            (
                {
                    "coherence_weight_R": 0.25,
                    "coherence_weight_phase_amplitude": 0.25,
                    "coherence_weight_phase_velocity": 0.25,
                    "coherence_weight_amplitude": 0.20,
                },
                (
                    "Coherence-proxy weights "
                    "must sum to 1"
                ),
            ),
            (
                {
                    "coupling_floor": 18.1,
                },
                (
                    "coupling_floor exceeds the initial "
                    "coupling strength"
                ),
            ),
            (
                {
                    "pressure_schedule": "invalid",
                },
                "Unsupported pressure_schedule",
            ),
            (
                {
                    "exposure_recovery_mode": "invalid",
                },
                "Unsupported exposure_recovery_mode",
            ),
            (
                {
                    "coupling_quench_mode": "invalid",
                },
                "Unsupported coupling_quench_mode",
            ),
            (
                {
                    "collapse_logic": "invalid",
                },
                (
                    "collapse_logic must be "
                    "'any' or 'all'"
                ),
            ),
            (
                {
                    "log_every": -1,
                },
                "log_every must be non-negative",
            ),
            (
                {
                    "field_every": -1,
                },
                "field_every must be non-negative",
            ),
        )

        for changes, message in cases:
            with self.subTest(
                changes=changes
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    message,
                ):
                    build_config(
                        **changes
                    ).validate(
                        18.0
                    )


class RuntimeTests(
    unittest.TestCase
):
    def setUp(
        self,
    ) -> None:
        self.protocol = build_protocol()

    def test_initial_metrics(
        self,
    ) -> None:
        metrics = self.protocol.get_metrics()

        self.assertEqual(
            metrics[
                "protocol_state"
            ],
            self.protocol.INITIALIZED,
        )

        self.assertEqual(
            metrics[
                "final_status"
            ],
            self.protocol.INITIALIZED,
        )

        self.assertFalse(
            metrics[
                "attractor_formed"
            ]
        )

        self.assertFalse(
            metrics[
                "phase_node_unlocked"
            ]
        )

        self.assertFalse(
            metrics[
                "collapse_detected"
            ]
        )

        self.assertGreaterEqual(
            metrics[
                "C_proxy_t"
            ],
            0.0,
        )

        self.assertLessEqual(
            metrics[
                "C_proxy_t"
            ],
            1.0,
        )

        self.assertAlmostEqual(
            metrics[
                "retention_margin"
            ],
            (
                metrics[
                    "C_proxy_t"
                ]
                - metrics[
                    "external_pressure_P_ext"
                ]
            ),
        )

    def test_invalid_runtime_inputs(
        self,
    ) -> None:
        for dt in (
            0.0,
            -0.01,
            float("inf"),
            float("nan"),
        ):
            with self.subTest(
                dt=dt
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    (
                        "dt must be a positive "
                        "finite value"
                    ),
                ):
                    self.protocol.run_protocol(
                        dt,
                        1.0,
                        0.0,
                    )

        forcing_cases = (
            (
                float("nan"),
                0.0,
                "Forcing density must be finite",
            ),
            (
                1.0,
                float("inf"),
                "Forcing phase must be finite",
            ),
        )

        for density, phase, message in forcing_cases:
            with self.subTest(
                density=density,
                phase=phase,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    message,
                ):
                    self.protocol.run_protocol(
                        0.01,
                        density,
                        phase,
                    )

        for pressure in (
            -0.01,
            1.01,
        ):
            with self.subTest(
                pressure=pressure
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    (
                        "external_pressure "
                        "must be within"
                    ),
                ):
                    self.protocol._validate_pressure(
                        pressure
                    )

        with self.assertRaisesRegex(
            ValueError,
            "external_pressure must be finite",
        ):
            self.protocol._validate_pressure(
                float("nan")
            )

    def test_retention_regime_classification(
        self,
    ) -> None:
        tolerance = (
            self.protocol
            .config
            .retained_boundary_tolerance
        )

        self.assertEqual(
            self.protocol._classify_retention_regime(
                tolerance
                + 0.01
            ),
            self.protocol.EDS_RETAINED,
        )

        self.assertEqual(
            self.protocol._classify_retention_regime(
                tolerance
            ),
            self.protocol.EDC_CRITICAL,
        )

        self.assertEqual(
            self.protocol._classify_retention_regime(
                -tolerance
                - 0.01
            ),
            self.protocol.DEGRADATION,
        )

    def test_delay_and_critical_exposure(
        self,
    ) -> None:
        tau_low = (
            self.protocol._calculate_delay_tau(
                0.01
            )
        )

        tau_high = (
            self.protocol._calculate_delay_tau(
                0.50
            )
        )

        self.assertGreater(
            tau_low,
            tau_high,
        )

        self.assertGreaterEqual(
            tau_high,
            (
                self.protocol
                .config
                .minimum_delay_tau
            ),
        )

        self.protocol.pressure_excess = 0.5
        self.protocol.instantaneous_delay_tau = 0.25

        self.protocol._accumulate_critical_exposure(
            0.1
        )

        self.assertAlmostEqual(
            self.protocol.critical_exposure,
            0.4,
        )

        self.protocol.pressure_excess = 0.0

        self.protocol._accumulate_critical_exposure(
            0.2
        )

        self.assertAlmostEqual(
            self.protocol.critical_exposure,
            0.35,
        )

    def test_pressure_schedules(
        self,
    ) -> None:
        step = build_protocol(
            pressure_schedule="step"
        )

        self.assertEqual(
            step._pressure_for_loading_tact(
                1,
                0.1,
                None,
            ),
            step.config.pressure_collapse,
        )

        linear = build_protocol(
            pressure_schedule="linear_ramp",
            pressure_hold=0.1,
            pressure_collapse=0.9,
            pressure_ramp_rate=0.5,
        )

        self.assertAlmostEqual(
            linear._pressure_for_loading_tact(
                2,
                0.1,
                None,
            ),
            0.2,
        )

        smooth = build_protocol(
            pressure_schedule="smooth_ramp",
            pressure_hold=0.1,
            pressure_collapse=0.9,
            pressure_ramp_rate=1.0,
        )

        smooth_value = (
            smooth._pressure_for_loading_tact(
                3,
                0.1,
                None,
            )
        )

        self.assertGreater(
            smooth_value,
            0.1,
        )

        self.assertLess(
            smooth_value,
            0.9,
        )

        external = build_protocol(
            pressure_schedule="external_sequence"
        )

        self.assertEqual(
            external._pressure_for_loading_tact(
                5,
                0.1,
                (
                    0.2,
                    0.4,
                ),
            ),
            0.4,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                "A non-empty external pressure "
                "sequence is required"
            ),
        ):
            external._pressure_for_loading_tact(
                1,
                0.1,
                (),
            )

    def test_field_snapshot(
        self,
    ) -> None:
        initial_base = (
            self
            .protocol
            .base_natural_frequencies
            .copy()
        )

        snapshot = (
            self.protocol.export_field_snapshot()
        )

        fields = (
            "phases",
            "amplitudes",
            "natural_frequencies",
            "effective_natural_frequencies",
            "phase_velocity",
            "amplitude_velocity",
            "phase_noise_increment",
            "amplitude_noise_increment",
        )

        for key in fields:
            values = np.asarray(
                snapshot[
                    key
                ]
            )

            self.assertEqual(
                values.shape,
                (
                    self.protocol.engine.N,
                ),
            )

            self.assertTrue(
                np.all(
                    np.isfinite(
                        values
                    )
                ),
                msg=(
                    f"Non-finite values in {key}"
                ),
            )

        np.testing.assert_array_equal(
            self.protocol.base_natural_frequencies,
            initial_base,
        )

    def test_full_protocol(
        self,
    ) -> None:
        summary = (
            self.protocol.run_protocol(
                dt=0.01,
                hold_forcing_density=1.5,
                hold_forcing_phase=0.0,
                collapse_forcing_density=0.0,
                collapse_forcing_phase=0.0,
            )
        )

        self.assertEqual(
            summary[
                "final_status"
            ],
            self.protocol.COLLAPSE_COMPLETED,
        )

        self.assertTrue(
            summary[
                "attractor_formed"
            ]
        )

        self.assertTrue(
            summary[
                "attractor_verified"
            ]
        )

        self.assertTrue(
            summary[
                "phase_node_unlocked"
            ]
        )

        self.assertTrue(
            summary[
                "collapse_detected"
            ]
        )

        self.assertGreater(
            summary[
                "history_length"
            ],
            0,
        )

        events = [
            item[
                "event"
            ]
            for item in summary[
                "transition_events"
            ]
        ]

        for event in (
            "ATTRACTOR_FORMED",
            "ATTRACTOR_VERIFIED",
            "PHASE_NODE_UNLOCKED",
            self.protocol.COLLAPSE_COMPLETED,
        ):
            self.assertIn(
                event,
                events,
            )

        self.assertLess(
            summary[
                "formation_tact"
            ],
            summary[
                "unlock_tact"
            ],
        )

        self.assertLess(
            summary[
                "unlock_tact"
            ],
            summary[
                "collapse_tact"
            ],
        )

        for key in (
            "C_proxy_t",
            "external_pressure_P_ext",
            "retention_margin",
            "pressure_excess",
            "instantaneous_delay_tau",
            "critical_exposure",
            "effective_coupling_K",
        ):
            self.assertTrue(
                math.isfinite(
                    float(
                        summary[
                            "final_metrics"
                        ][
                            key
                        ]
                    )
                ),
                msg=(
                    f"Non-finite metric: {key}"
                ),
            )

        np.testing.assert_array_equal(
            self.protocol.engine._to_host(
                self.protocol.base_natural_frequencies
            ),
            self.protocol.engine._to_host(
                (
                    self.protocol
                    .engine
                    .natural_frequencies
                )
            ),
        )

    def test_same_seed_reproduces_transition_sequence(
        self,
    ) -> None:
        protocol_a = build_protocol(
            seed=7
        )

        protocol_b = build_protocol(
            seed=7
        )

        summary_a = (
            protocol_a.run_protocol(
                0.01,
                1.5,
                0.0,
            )
        )

        summary_b = (
            protocol_b.run_protocol(
                0.01,
                1.5,
                0.0,
            )
        )

        for key in (
            "final_status",
            "formation_tact",
            "unlock_tact",
            "collapse_tact",
            "transition_events",
        ):
            self.assertEqual(
                summary_a[
                    key
                ],
                summary_b[
                    key
                ],
            )


class LoggerTests(
    unittest.TestCase
):
    def test_logger_outputs(
        self,
    ) -> None:
        protocol = build_protocol(
            seed=13
        )

        protocol._advance_engine(
            1.0,
            0.0,
            0.01,
        )

        protocol._refresh_protocol_observables(
            protocol.config.pressure_hold
        )

        with tempfile.TemporaryDirectory() as directory:
            logger = EDKMarnovProtocolLogger(
                directory
            )

            metrics_path, field_path = (
                logger.log_tact(
                    protocol,
                    include_field=True,
                )
            )

            summary_path = (
                logger.log_summary(
                    protocol
                )
            )

            self.assertTrue(
                metrics_path.is_file()
            )

            self.assertIsNotNone(
                field_path
            )

            self.assertTrue(
                field_path.is_file()
            )

            self.assertTrue(
                summary_path.is_file()
            )

            with metrics_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                payload = json.load(
                    stream
                )

            tact = int(
                protocol.engine.tact_index
            )

            self.assertEqual(
                payload[
                    "tact"
                ],
                tact,
            )

            self.assertEqual(
                payload[
                    "step"
                ],
                tact,
            )

            self.assertEqual(
                payload[
                    "tact_index"
                ],
                tact,
            )

            self.assertAlmostEqual(
                payload[
                    "simulation_time"
                ],
                float(
                    protocol.engine.simulation_time
                ),
            )

            self.assertEqual(
                payload[
                    "module"
                ],
                (
                    "module_edk_marnov_"
                    "retention_collapse_protocol"
                ),
            )

            self.assertEqual(
                payload[
                    "protocol_class"
                ],
                (
                    "EDKMarnovRetention"
                    "CollapseProtocol"
                ),
            )

            self.assertIn(
                "metrics",
                payload,
            )

            self.assertIn(
                "protocol_configuration",
                payload,
            )

            self.assertEqual(
                payload[
                    "metrics"
                ][
                    "tact_index"
                ],
                tact,
            )

            self.assertAlmostEqual(
                payload[
                    "metrics"
                ][
                    "simulation_time"
                ],
                float(
                    protocol.engine.simulation_time
                ),
            )

            with np.load(
                field_path,
                allow_pickle=False,
            ) as archive:
                for key in (
                    "phases",
                    "amplitudes",
                    "effective_natural_frequencies",
                ):
                    self.assertIn(
                        key,
                        archive.files,
                    )

            with summary_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                summary = json.load(
                    stream
                )

            self.assertEqual(
                summary[
                    "module"
                ],
                (
                    "module_edk_marnov_"
                    "retention_collapse_protocol"
                ),
            )

            self.assertIn(
                "final_metrics",
                summary,
            )

            self.assertEqual(
                list(
                    Path(
                        directory
                    ).glob(
                        "*.tmp"
                    )
                ),
                [],
            )

    def test_log_step_alias_matches_log_tact(
        self,
    ) -> None:
        protocol = build_protocol(
            seed=17
        )

        protocol._advance_engine(
            1.0,
            0.0,
            0.01,
        )

        protocol._refresh_protocol_observables(
            protocol.config.pressure_hold
        )

        with tempfile.TemporaryDirectory() as directory:
            logger = EDKMarnovProtocolLogger(
                directory
            )

            tact_path, _ = logger.log_tact(
                protocol,
                include_field=False,
            )

            alias_path, _ = logger.log_step(
                protocol,
                include_field=False,
            )

            self.assertEqual(
                tact_path,
                alias_path,
            )

            with alias_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                payload = json.load(
                    stream
                )

            self.assertEqual(
                payload[
                    "tact"
                ],
                payload[
                    "step"
                ],
            )

            self.assertEqual(
                payload[
                    "tact_index"
                ],
                payload[
                    "tact"
                ],
            )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
