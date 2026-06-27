from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    from . import edk_gpu_mean_field_phase_engine as engine_module
except ImportError:
    try:
        import edk_gpu_mean_field_phase_engine as engine_module
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_gpu_mean_field_phase_engine import (
            edk_gpu_mean_field_phase_engine as engine_module,
        )


EDKGPUMeanFieldLogger = engine_module.EDKGPUMeanFieldLogger
EDKGPUMeanFieldPhaseEngine = engine_module.EDKGPUMeanFieldPhaseEngine
MeanFieldPhaseConfig = engine_module.MeanFieldPhaseConfig


class MeanFieldPhaseConfigurationTests(unittest.TestCase):
    def test_minimum_valid_configuration(self) -> None:
        engine = EDKGPUMeanFieldPhaseEngine(
            MeanFieldPhaseConfig(
                num_domains=2,
                backend="cpu",
                seed=1,
            )
        )

        self.assertEqual(
            engine.N,
            2,
        )

        self.assertEqual(
            engine.backend_name,
            "cpu",
        )

        self.assertEqual(
            engine.backend_library,
            "numpy",
        )

        self.assertFalse(
            engine.using_gpu
        )

        self.assertIsNone(
            engine.active_device_id
        )

        self.assertEqual(
            engine.tact_index,
            0,
        )

        self.assertEqual(
            engine.step_index,
            0,
        )

        self.assertAlmostEqual(
            engine.simulation_time,
            0.0,
        )

    def test_num_domains_below_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "num_domains must be at least 2",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    num_domains=1,
                    backend="cpu",
                )
            )

    def test_non_finite_coupling_strength_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "coupling_strength_k must be finite",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    coupling_strength_k=float("nan"),
                    backend="cpu",
                )
            )

    def test_non_finite_phase_lag_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sakaguchi_phase_lag_alpha must be finite",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    sakaguchi_phase_lag_alpha=float("inf"),
                    backend="cpu",
                )
            )

    def test_negative_natural_frequency_std_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "natural_frequency_std must be non-negative",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    natural_frequency_std=-0.1,
                    backend="cpu",
                )
            )

    def test_negative_phase_noise_strength_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "phase_noise_strength must be non-negative",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    phase_noise_strength=-0.1,
                    backend="cpu",
                )
            )

    def test_negative_amplitude_noise_strength_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "amplitude_noise_strength must be non-negative",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_noise_strength=-0.1,
                    backend="cpu",
                )
            )

    def test_negative_amplitude_saturation_rate_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "amplitude_saturation_rate must be non-negative",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_saturation_rate=-0.1,
                    backend="cpu",
                )
            )

    def test_non_positive_amplitude_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "amplitude_minimum must be positive",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_minimum=0.0,
                    backend="cpu",
                )
            )

    def test_amplitude_maximum_not_above_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "amplitude_maximum must be greater than amplitude_minimum",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_minimum=1.0,
                    amplitude_maximum=1.0,
                    initial_amplitude_minimum=1.0,
                    initial_amplitude_maximum=1.1,
                    backend="cpu",
                )
            )

    def test_initial_amplitude_minimum_below_bound_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "initial_amplitude_minimum must not be smaller than amplitude_minimum",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_minimum=0.5,
                    initial_amplitude_minimum=0.4,
                    backend="cpu",
                )
            )

    def test_initial_amplitude_maximum_above_bound_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "initial_amplitude_maximum must not exceed amplitude_maximum",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    amplitude_maximum=2.0,
                    initial_amplitude_maximum=2.1,
                    backend="cpu",
                )
            )

    def test_initial_amplitude_interval_must_be_ordered(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "initial_amplitude_maximum must be greater than initial_amplitude_minimum",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    initial_amplitude_minimum=1.0,
                    initial_amplitude_maximum=1.0,
                    backend="cpu",
                )
            )

    def test_unknown_dtype_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "dtype must be 'float32' or 'float64'",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    dtype="float16",
                    backend="cpu",
                )
            )

    def test_unknown_backend_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "backend must be 'auto', 'gpu', or 'cpu'",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    backend="invalid",
                )
            )

    def test_negative_device_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "device_id must be non-negative",
        ):
            EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    backend="cpu",
                    device_id=-1,
                )
            )

    def test_explicit_gpu_without_cupy_is_rejected(self) -> None:
        with mock.patch.object(
            engine_module,
            "_cupy",
            None,
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "GPU backend requested, but CuPy could not be imported",
            ):
                EDKGPUMeanFieldPhaseEngine(
                    MeanFieldPhaseConfig(
                        num_domains=8,
                        backend="gpu",
                    )
                )

    def test_auto_backend_falls_back_to_cpu_without_cupy(self) -> None:
        with mock.patch.object(
            engine_module,
            "_cupy",
            None,
        ):
            engine = EDKGPUMeanFieldPhaseEngine(
                MeanFieldPhaseConfig(
                    num_domains=8,
                    backend="auto",
                )
            )

        self.assertEqual(
            engine.backend_name,
            "cpu",
        )

        self.assertEqual(
            engine.backend_library,
            "numpy",
        )

        self.assertFalse(
            engine.using_gpu
        )

        self.assertIsNone(
            engine.active_device_id
        )


class MeanFieldPhaseRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = MeanFieldPhaseConfig(
            num_domains=128,
            coupling_strength_k=12.0,
            sakaguchi_phase_lag_alpha=0.2,
            natural_frequency_mean=0.0,
            natural_frequency_std=0.08,
            external_forcing_phase=0.35,
            phase_noise_strength=0.02,
            amplitude_growth_rate=1.0,
            amplitude_saturation_rate=1.0,
            amplitude_noise_strength=0.03,
            amplitude_minimum=0.1,
            amplitude_maximum=3.0,
            initial_amplitude_minimum=0.5,
            initial_amplitude_maximum=1.5,
            seed=17,
            dtype="float32",
            backend="cpu",
            device_id=0,
        )

        self.engine = EDKGPUMeanFieldPhaseEngine(
            self.config
        )

    def test_non_finite_external_forcing_density_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_forcing_density must be finite",
        ):
            self.engine.process_micro_interval(
                external_forcing_density=float("nan"),
                external_forcing_phase=0.0,
                dt=0.01,
            )

    def test_non_positive_or_non_finite_dt_is_rejected(self) -> None:
        for invalid_dt in (
            0.0,
            -0.01,
            float("inf"),
            float("nan"),
        ):
            with self.subTest(
                dt=invalid_dt,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "dt must be a positive finite value",
                ):
                    self.engine.process_micro_interval(
                        external_forcing_density=1.0,
                        external_forcing_phase=0.0,
                        dt=invalid_dt,
                    )

    def test_non_finite_external_forcing_phase_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_forcing_phase must be finite",
        ):
            self.engine.process_micro_interval(
                external_forcing_density=1.0,
                external_forcing_phase=float("inf"),
                dt=0.01,
            )

    def test_non_finite_coupling_strength_update_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "coupling_strength_k must be finite",
        ):
            self.engine.set_coupling_strength(
                float("nan")
            )

    def test_non_finite_phase_lag_update_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sakaguchi_phase_lag_alpha must be finite",
        ):
            self.engine.set_phase_lag(
                float("inf")
            )

    def test_runtime_parameter_updates_are_applied(self) -> None:
        self.engine.set_coupling_strength(
            7.5
        )

        self.engine.set_phase_lag(
            0.1
        )

        self.assertEqual(
            self.engine.K,
            7.5,
        )

        self.assertEqual(
            self.engine.alpha,
            0.1,
        )

    def test_default_external_forcing_phase_is_used(self) -> None:
        metrics = self.engine.process_micro_interval(
            external_forcing_density=1.0,
            dt=0.01,
        )

        self.assertEqual(
            metrics["external_forcing_phase"],
            self.config.external_forcing_phase,
        )

    def test_one_interval_produces_finite_bounded_metrics(self) -> None:
        metrics = self.engine.process_micro_interval(
            external_forcing_density=1.75,
            external_forcing_phase=0.35,
            dt=0.01,
        )

        required_metrics = (
            "R_t_phase_order",
            "global_mean_phase",
            "phase_amplitude_order_proxy",
            "mean_phase_velocity",
            "phase_velocity_dispersion",
            "mean_amplitude",
            "amplitude_dispersion",
            "minimum_amplitude",
            "maximum_amplitude",
            "coupling_energy_proxy",
            "external_forcing_density",
            "external_forcing_phase",
            "coupling_strength_k",
            "sakaguchi_phase_lag_alpha",
            "active_domains",
            "backend_name",
            "backend_library",
            "device_id",
            "simulation_time",
            "tact_index",
            "step",
        )

        for key in required_metrics:
            self.assertIn(
                key,
                metrics,
            )

        for key in (
            "R_t_phase_order",
            "global_mean_phase",
            "phase_amplitude_order_proxy",
            "mean_phase_velocity",
            "phase_velocity_dispersion",
            "mean_amplitude",
            "amplitude_dispersion",
            "minimum_amplitude",
            "maximum_amplitude",
            "coupling_energy_proxy",
            "external_forcing_density",
            "external_forcing_phase",
            "coupling_strength_k",
            "sakaguchi_phase_lag_alpha",
            "simulation_time",
        ):
            self.assertTrue(
                math.isfinite(
                    float(
                        metrics[key]
                    )
                ),
                msg=f"Non-finite metric: {key}={metrics[key]}",
            )

        self.assertGreaterEqual(
            metrics["R_t_phase_order"],
            0.0,
        )

        self.assertLessEqual(
            metrics["R_t_phase_order"],
            1.0,
        )

        self.assertGreaterEqual(
            metrics["phase_amplitude_order_proxy"],
            0.0,
        )

        self.assertLessEqual(
            metrics["phase_amplitude_order_proxy"],
            1.0,
        )

        self.assertGreaterEqual(
            metrics["global_mean_phase"],
            -math.pi,
        )

        self.assertLessEqual(
            metrics["global_mean_phase"],
            math.pi,
        )

        self.assertGreaterEqual(
            metrics["coupling_energy_proxy"],
            -1.0,
        )

        self.assertLessEqual(
            metrics["coupling_energy_proxy"],
            1.0,
        )

        self.assertGreaterEqual(
            metrics["phase_velocity_dispersion"],
            0.0,
        )

        self.assertGreaterEqual(
            metrics["amplitude_dispersion"],
            0.0,
        )

        self.assertGreaterEqual(
            metrics["minimum_amplitude"],
            self.config.amplitude_minimum,
        )

        self.assertLessEqual(
            metrics["maximum_amplitude"],
            self.config.amplitude_maximum,
        )

        self.assertEqual(
            metrics["active_domains"],
            self.config.num_domains,
        )

        self.assertEqual(
            metrics["backend_name"],
            "cpu",
        )

        self.assertEqual(
            metrics["backend_library"],
            "numpy",
        )

        self.assertIsNone(
            metrics["device_id"]
        )

        self.assertEqual(
            metrics["tact_index"],
            1,
        )

        self.assertEqual(
            metrics["step"],
            1,
        )

        self.assertEqual(
            self.engine.tact_index,
            1,
        )

        self.assertEqual(
            self.engine.step_index,
            1,
        )

        self.assertAlmostEqual(
            metrics["simulation_time"],
            0.01,
        )

    def test_multiple_intervals_advance_tact_step_and_time(self) -> None:
        for _ in range(
            5
        ):
            self.engine.process_micro_interval(
                external_forcing_density=1.0,
                external_forcing_phase=0.0,
                dt=0.01,
            )

        metrics = self.engine.get_metrics()

        self.assertEqual(
            metrics["tact_index"],
            5,
        )

        self.assertEqual(
            metrics["step"],
            5,
        )

        self.assertEqual(
            self.engine.tact_index,
            5,
        )

        self.assertEqual(
            self.engine.step_index,
            5,
        )

        self.assertAlmostEqual(
            metrics["simulation_time"],
            0.05,
        )

    def test_field_snapshot_shapes_dtypes_and_bounds(self) -> None:
        initial_natural_frequencies = (
            self.engine.export_field_snapshot()[
                "natural_frequencies"
            ].copy()
        )

        for _ in range(
            10
        ):
            self.engine.process_micro_interval(
                external_forcing_density=1.75,
                external_forcing_phase=0.35,
                dt=0.01,
            )

        field = self.engine.export_field_snapshot()

        required_fields = (
            "phases",
            "amplitudes",
            "natural_frequencies",
            "phase_velocity",
            "amplitude_velocity",
            "phase_noise_increment",
            "amplitude_noise_increment",
        )

        for key in required_fields:
            values = np.asarray(
                field[key]
            )

            self.assertEqual(
                values.shape,
                (
                    self.config.num_domains,
                ),
            )

            self.assertEqual(
                values.dtype,
                np.dtype("float32"),
            )

            self.assertTrue(
                np.all(
                    np.isfinite(
                        values
                    )
                ),
                msg=f"Non-finite values in field: {key}",
            )

        phase_tolerance = 1.0e-6

        self.assertTrue(
            np.all(
                field["phases"]
                >= -math.pi
                - phase_tolerance
            )
        )

        self.assertTrue(
            np.all(
                field["phases"]
                < math.pi
                + phase_tolerance
            )
        )

        self.assertTrue(
            np.all(
                field["amplitudes"]
                >= self.config.amplitude_minimum
                - phase_tolerance
            )
        )

        self.assertTrue(
            np.all(
                field["amplitudes"]
                <= self.config.amplitude_maximum
                + phase_tolerance
            )
        )

        np.testing.assert_array_equal(
            field["natural_frequencies"],
            initial_natural_frequencies,
        )

    def test_same_seed_reproduces_initial_state(self) -> None:
        engine_a = EDKGPUMeanFieldPhaseEngine(
            self.config
        )

        engine_b = EDKGPUMeanFieldPhaseEngine(
            self.config
        )

        state_a = engine_a.export_field_snapshot()
        state_b = engine_b.export_field_snapshot()

        for key in (
            "phases",
            "amplitudes",
            "natural_frequencies",
            "phase_velocity",
            "amplitude_velocity",
            "phase_noise_increment",
            "amplitude_noise_increment",
        ):
            np.testing.assert_array_equal(
                state_a[key],
                state_b[key],
            )

    def test_zero_noise_keeps_noise_increments_zero(self) -> None:
        engine = EDKGPUMeanFieldPhaseEngine(
            MeanFieldPhaseConfig(
                num_domains=32,
                phase_noise_strength=0.0,
                amplitude_noise_strength=0.0,
                backend="cpu",
                seed=3,
            )
        )

        engine.process_micro_interval(
            external_forcing_density=0.5,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        field = engine.export_field_snapshot()

        np.testing.assert_array_equal(
            field["phase_noise_increment"],
            np.zeros(
                32,
                dtype=np.float32,
            ),
        )

        np.testing.assert_array_equal(
            field["amplitude_noise_increment"],
            np.zeros(
                32,
                dtype=np.float32,
            ),
        )

    def test_float64_configuration_preserves_float64_fields(self) -> None:
        engine = EDKGPUMeanFieldPhaseEngine(
            MeanFieldPhaseConfig(
                num_domains=16,
                dtype="float64",
                backend="cpu",
                seed=5,
            )
        )

        field = engine.export_field_snapshot()

        for values in field.values():
            self.assertEqual(
                np.asarray(
                    values
                ).dtype,
                np.dtype("float64"),
            )

    def test_engine_does_not_allocate_pairwise_state_matrix(self) -> None:
        for name, value in vars(
            self.engine
        ).items():
            shape = getattr(
                value,
                "shape",
                None,
            )

            self.assertNotEqual(
                shape,
                (
                    self.engine.N,
                    self.engine.N,
                ),
                msg=(
                    f"Unexpected N x N "
                    f"state matrix: {name}"
                ),
            )


class MeanFieldPhaseLoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = EDKGPUMeanFieldPhaseEngine(
            MeanFieldPhaseConfig(
                num_domains=32,
                backend="cpu",
                seed=23,
            )
        )

        self.engine.process_micro_interval(
            external_forcing_density=0.5,
            external_forcing_phase=0.0,
            dt=0.01,
        )

    def test_negative_tact_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            with self.assertRaisesRegex(
                ValueError,
                "tact_id must be non-negative",
            ):
                logger.log_tact(
                    tact_id=-1,
                    engine=self.engine,
                )

    def test_log_step_negative_id_uses_tact_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            with self.assertRaisesRegex(
                ValueError,
                "tact_id must be non-negative",
            ):
                logger.log_step(
                    step_id=-1,
                    engine=self.engine,
                )

    def test_logger_rejects_mismatched_tact_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            with self.assertRaisesRegex(
                ValueError,
                "tact_id must match engine.tact_index",
            ):
                logger.log_tact(
                    tact_id=7,
                    engine=self.engine,
                )

    def test_logger_writes_metric_and_field_snapshots(self) -> None:
        tact = int(
            self.engine.tact_index
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_tact(
                tact_id=tact,
                engine=self.engine,
                include_field=True,
            )

            output_dir = Path(
                temporary_directory
            )

            tact_json_path = (
                output_dir
                / f"gpu_mean_field_tact_{tact:06d}.json"
            )

            step_json_path = (
                output_dir
                / f"gpu_mean_field_step_{tact:06d}.json"
            )

            expected_field_path = (
                output_dir
                / f"gpu_mean_field_field_{tact:06d}.npz"
            )

            self.assertEqual(
                metrics_path,
                tact_json_path,
            )

            self.assertTrue(
                tact_json_path.is_file()
            )

            self.assertTrue(
                step_json_path.is_file()
            )

            self.assertIsNotNone(
                field_path
            )

            self.assertEqual(
                field_path,
                expected_field_path,
            )

            self.assertTrue(
                expected_field_path.is_file()
            )

            with tact_json_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                tact_payload = json.load(
                    stream
                )

            with step_json_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                step_payload = json.load(
                    stream
                )

            self.assertEqual(
                tact_payload,
                step_payload,
            )

            self.assertEqual(
                tact_payload["tact"],
                tact,
            )

            self.assertEqual(
                tact_payload["step"],
                tact,
            )

            self.assertEqual(
                tact_payload["tact_index"],
                tact,
            )

            self.assertAlmostEqual(
                tact_payload["simulation_time"],
                float(
                    self.engine.simulation_time
                ),
            )

            self.assertEqual(
                tact_payload["module"],
                "module_edk_gpu_mean_field_phase_engine",
            )

            self.assertEqual(
                tact_payload["engine_class"],
                "EDKGPUMeanFieldPhaseEngine",
            )

            self.assertEqual(
                tact_payload["backend"]["name"],
                "cpu",
            )

            self.assertEqual(
                tact_payload["backend"]["library"],
                "numpy",
            )

            self.assertFalse(
                tact_payload["backend"]["using_gpu"]
            )

            self.assertIsNone(
                tact_payload["backend"]["device_id"]
            )

            self.assertIn(
                "configuration",
                tact_payload,
            )

            self.assertIn(
                "metrics",
                tact_payload,
            )

            self.assertEqual(
                tact_payload["metrics"]["tact_index"],
                tact,
            )

            self.assertEqual(
                tact_payload["metrics"]["step"],
                tact,
            )

            with np.load(
                expected_field_path,
                allow_pickle=False,
            ) as archive:
                for key in (
                    "phases",
                    "amplitudes",
                    "natural_frequencies",
                    "phase_velocity",
                    "amplitude_velocity",
                    "phase_noise_increment",
                    "amplitude_noise_increment",
                ):
                    self.assertIn(
                        key,
                        archive.files,
                    )

            self.assertEqual(
                list(
                    output_dir.glob(
                        "*.tmp"
                    )
                ),
                [],
            )

    def test_log_step_alias_matches_log_tact(self) -> None:
        tact = int(
            self.engine.tact_index
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_step(
                step_id=tact,
                engine=self.engine,
                include_field=False,
            )

            self.assertEqual(
                metrics_path,
                Path(
                    temporary_directory
                )
                / f"gpu_mean_field_tact_{tact:06d}.json",
            )

            self.assertIsNone(
                field_path
            )

            self.assertTrue(
                (
                    Path(
                        temporary_directory
                    )
                    / f"gpu_mean_field_step_{tact:06d}.json"
                ).is_file()
            )

            self.assertFalse(
                (
                    Path(
                        temporary_directory
                    )
                    / f"gpu_mean_field_field_{tact:06d}.npz"
                ).exists()
            )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
