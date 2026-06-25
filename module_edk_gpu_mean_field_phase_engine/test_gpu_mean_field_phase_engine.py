from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

try:
    from . import edk_gpu_mean_field_phase_engine as engine_module
except ImportError:
    import edk_gpu_mean_field_phase_engine as engine_module


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

        self.assertEqual(engine.N, 2)
        self.assertEqual(engine.backend_name, "numpy")
        self.assertFalse(engine.using_gpu)
        self.assertIsNone(engine.active_device_id)

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
                    initial_amplitude_maximum=1.0,
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

    def test_auto_backend_falls_back_to_numpy_without_cupy(self) -> None:
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

        self.assertEqual(engine.backend_name, "numpy")
        self.assertFalse(engine.using_gpu)
        self.assertIsNone(engine.active_device_id)


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
            with self.subTest(dt=invalid_dt):
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

    def test_non_finite_coupling_strength_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "coupling_strength_k must be finite",
        ):
            self.engine.set_coupling_strength(
                float("nan")
            )

    def test_non_finite_phase_lag_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "sakaguchi_phase_lag_alpha must be finite",
        ):
            self.engine.set_phase_lag(
                float("inf")
            )

    def test_runtime_parameter_updates_are_applied(self) -> None:
        self.engine.set_coupling_strength(7.5)
        self.engine.set_phase_lag(0.1)

        self.assertEqual(self.engine.K, 7.5)
        self.assertEqual(self.engine.alpha, 0.1)

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
            "device_id",
            "simulation_time",
            "tact_index",
        )

        for key in required_metrics:
            self.assertIn(key, metrics)

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
                math.isfinite(float(metrics[key])),
                msg=f"Non-finite metric: {key}={metrics[key]}",
            )

        self.assertGreaterEqual(metrics["R_t_phase_order"], 0.0)
        self.assertLessEqual(metrics["R_t_phase_order"], 1.0)
        self.assertGreaterEqual(
            metrics["phase_amplitude_order_proxy"],
            0.0,
        )
        self.assertLessEqual(
            metrics["phase_amplitude_order_proxy"],
            1.0,
        )
        self.assertGreaterEqual(metrics["global_mean_phase"], -math.pi)
        self.assertLessEqual(metrics["global_mean_phase"], math.pi)
        self.assertGreaterEqual(metrics["coupling_energy_proxy"], -1.0)
        self.assertLessEqual(metrics["coupling_energy_proxy"], 1.0)
        self.assertGreaterEqual(metrics["phase_velocity_dispersion"], 0.0)
        self.assertGreaterEqual(metrics["amplitude_dispersion"], 0.0)
        self.assertGreaterEqual(
            metrics["minimum_amplitude"],
            self.config.amplitude_minimum,
        )
        self.assertLessEqual(
            metrics["maximum_amplitude"],
            self.config.amplitude_maximum,
        )
        self.assertEqual(metrics["active_domains"], self.config.num_domains)
        self.assertEqual(metrics["backend_name"], "numpy")
        self.assertIsNone(metrics["device_id"])
        self.assertEqual(metrics["tact_index"], 1)
        self.assertAlmostEqual(metrics["simulation_time"], 0.01)

    def test_field_snapshot_shapes_dtypes_and_bounds(self) -> None:
        initial_natural_frequencies = (
            self.engine.export_field_snapshot()[
                "natural_frequencies"
            ].copy()
        )

        for _ in range(10):
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
            values = np.asarray(field[key])

            self.assertEqual(
                values.shape,
                (self.config.num_domains,),
            )

            self.assertEqual(
                values.dtype,
                np.dtype("float32"),
            )

            self.assertTrue(
                np.all(np.isfinite(values)),
                msg=f"Non-finite values in field: {key}",
            )

        phase_tolerance = 1e-6

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
                np.asarray(values).dtype,
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

    def test_negative_step_id_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            with self.assertRaisesRegex(
                ValueError,
                "step_id must be non-negative",
            ):
                logger.log_step(
                    step_id=-1,
                    engine=self.engine,
                )

    def test_logger_writes_metric_and_field_snapshots(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_step(
                step_id=7,
                engine=self.engine,
                include_field=True,
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

            with metrics_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                payload = json.load(
                    stream
                )

            self.assertEqual(
                payload["step"],
                7,
            )

            self.assertEqual(
                payload["module"],
                "module_edk_gpu_mean_field_phase_engine",
            )

            self.assertEqual(
                payload["engine_class"],
                "EDKGPUMeanFieldPhaseEngine",
            )

            self.assertEqual(
                payload["backend"]["name"],
                "numpy",
            )

            self.assertFalse(
                payload["backend"]["using_gpu"]
            )

            self.assertIsNone(
                payload["backend"]["device_id"]
            )

            self.assertIn(
                "configuration",
                payload,
            )

            self.assertIn(
                "metrics",
                payload,
            )

            with np.load(
                field_path,
                allow_pickle=False,
            ) as archive:
                self.assertIn(
                    "phases",
                    archive.files,
                )

                self.assertIn(
                    "amplitudes",
                    archive.files,
                )

                self.assertIn(
                    "natural_frequencies",
                    archive.files,
                )

    def test_logger_can_write_metrics_without_field_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKGPUMeanFieldLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_step(
                step_id=3,
                engine=self.engine,
                include_field=False,
            )

            self.assertTrue(
                metrics_path.is_file()
            )

            self.assertIsNone(
                field_path
            )

            self.assertFalse(
                (
                    Path(
                        temporary_directory
                    )
                    / "gpu_mean_field_field_000003.npz"
                ).exists()
            )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
