from __future__ import annotations

import json
import math
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

try:
    from .edk_spatiotemporal_phase_delay import (
        EDKDelayLogger,
        EDKSpatiotemporalPhaseDelayEngine,
        PhaseDelayConfig,
    )
except ImportError:
    try:
        from edk_spatiotemporal_phase_delay import (
            EDKDelayLogger,
            EDKSpatiotemporalPhaseDelayEngine,
            PhaseDelayConfig,
        )
    except ImportError:
        repo_root = Path(__file__).resolve().parents[1]

        if str(repo_root) not in sys.path:
            sys.path.insert(
                0,
                str(repo_root),
            )

        from module_edk_spatiotemporal_phase_delay.edk_spatiotemporal_phase_delay import (
            EDKDelayLogger,
            EDKSpatiotemporalPhaseDelayEngine,
            PhaseDelayConfig,
        )


class SpatiotemporalPhaseDelayConfigurationTests(unittest.TestCase):
    def test_minimum_valid_configuration(self) -> None:
        engine = EDKSpatiotemporalPhaseDelayEngine(
            PhaseDelayConfig(
                num_domains=4,
                neighbor_count=1,
                backend="cpu",
                knn_chunk_size=2,
                delay_safety_margin=2,
                seed=1,
            )
        )

        self.assertEqual(
            engine.N,
            4,
        )

        self.assertEqual(
            engine.k,
            1,
        )

        self.assertEqual(
            engine.backend_name,
            "cpu",
        )

        self.assertEqual(
            engine.neighbor_indices.shape,
            (
                4,
                1,
            ),
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
            "num_domains must be at least 4",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=3,
                    neighbor_count=1,
                    backend="cpu",
                )
            )

    def test_neighbor_count_below_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "neighbor_count must be at least 1",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=0,
                    backend="cpu",
                )
            )

    def test_neighbor_count_equal_to_num_domains_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "neighbor_count must be at least 1 and smaller than num_domains",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=4,
                    backend="cpu",
                )
            )

    def test_non_positive_wave_velocity_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "wave_velocity_c must be positive",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    wave_velocity_c=0.0,
                    backend="cpu",
                )
            )

    def test_non_positive_coordinate_extent_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "coordinate_half_extent must be positive",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    coordinate_half_extent=0.0,
                    backend="cpu",
                )
            )

    def test_negative_natural_frequency_std_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "natural_frequency_std must be non-negative",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    natural_frequency_std=-0.01,
                    backend="cpu",
                )
            )

    def test_non_positive_knn_chunk_size_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "knn_chunk_size must be positive",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    knn_chunk_size=0,
                    backend="cpu",
                )
            )

    def test_delay_safety_margin_below_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "delay_safety_margin must be at least 2",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    delay_safety_margin=1,
                    backend="cpu",
                )
            )

    def test_unknown_dtype_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "dtype must be 'float32' or 'float64'",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    dtype="float16",
                    backend="cpu",
                )
            )

    def test_unknown_backend_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "backend must be 'auto', 'cpu', or 'gpu'",
        ):
            EDKSpatiotemporalPhaseDelayEngine(
                PhaseDelayConfig(
                    num_domains=4,
                    neighbor_count=1,
                    backend="invalid",
                )
            )


class SpatiotemporalPhaseDelayRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PhaseDelayConfig(
            num_domains=32,
            neighbor_count=6,
            coupling_strength_k=25.0,
            sakaguchi_phase_lag_alpha=0.15,
            wave_velocity_c=12.0,
            coordinate_half_extent=2.0,
            natural_frequency_mean=0.0,
            natural_frequency_std=0.05,
            knn_chunk_size=8,
            delay_safety_margin=3,
            seed=11,
            dtype="float32",
            backend="cpu",
        )

        self.engine = EDKSpatiotemporalPhaseDelayEngine(
            self.config
        )

    def test_non_finite_external_forcing_density_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_forcing_density must be finite",
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=float("nan"),
                external_forcing_phase=0.0,
                dt=0.01,
            )

    def test_non_finite_external_forcing_phase_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_forcing_phase must be finite",
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=1.0,
                external_forcing_phase=float("inf"),
                dt=0.01,
            )

    def test_non_positive_dt_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "dt must be a positive finite value",
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=1.0,
                external_forcing_phase=0.0,
                dt=0.0,
            )

    def test_non_finite_dt_is_rejected(self) -> None:
        for dt in (
            float("inf"),
            float("nan"),
        ):
            with self.subTest(
                dt=dt,
            ):
                with self.assertRaisesRegex(
                    ValueError,
                    "dt must be a positive finite value",
                ):
                    self.engine.process_delayed_interval(
                        external_forcing_density=1.0,
                        external_forcing_phase=0.0,
                        dt=dt,
                    )

    def test_dt_change_after_history_initialization_is_rejected(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        with self.assertRaisesRegex(
            ValueError,
            "dt changed after delay-history initialization",
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=1.0,
                external_forcing_phase=0.0,
                dt=0.02,
            )

    def test_one_interval_produces_finite_bounded_metrics(self) -> None:
        metrics = self.engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=0.01,
        )

        required_metrics = (
            "tact_index",
            "step",
            "simulation_time",
            "R_t_phase_order",
            "global_mean_phase",
            "delayed_local_phase_order",
            "mean_phase_velocity",
            "phase_velocity_dispersion",
            "mean_delay",
            "maximum_delay",
            "delay_dispersion",
            "delayed_coupling_energy_proxy",
            "history_buffer_depth",
        )

        for key in required_metrics:
            self.assertIn(
                key,
                metrics,
            )

            self.assertTrue(
                math.isfinite(
                    metrics[key]
                ),
                msg=f"Non-finite metric: {key}={metrics[key]}",
            )

        self.assertEqual(
            int(
                metrics["tact_index"]
            ),
            1,
        )

        self.assertEqual(
            int(
                metrics["step"]
            ),
            1,
        )

        self.assertAlmostEqual(
            metrics["simulation_time"],
            0.01,
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
            self.engine.simulation_time,
            0.01,
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
            metrics["delayed_local_phase_order"],
            0.0,
        )

        self.assertLessEqual(
            metrics["delayed_local_phase_order"],
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
            metrics["delayed_coupling_energy_proxy"],
            -1.0,
        )

        self.assertLessEqual(
            metrics["delayed_coupling_energy_proxy"],
            1.0,
        )

        self.assertGreaterEqual(
            metrics["phase_velocity_dispersion"],
            0.0,
        )

        self.assertGreater(
            metrics["mean_delay"],
            0.0,
        )

        self.assertGreaterEqual(
            metrics["maximum_delay"],
            metrics["mean_delay"],
        )

        self.assertGreaterEqual(
            metrics["delay_dispersion"],
            0.0,
        )

        expected_minimum_history_depth = (
            math.ceil(
                self.engine.maximum_delay
                / 0.01
            )
            + self.config.delay_safety_margin
        )

        self.assertGreaterEqual(
            int(
                round(
                    metrics["history_buffer_depth"]
                )
            ),
            expected_minimum_history_depth,
        )

    def test_multiple_intervals_advance_tact_and_time(self) -> None:
        for _ in range(
            5
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=1.0,
                external_forcing_phase=None,
                dt=0.01,
            )

        metrics = self.engine.metrics()

        self.assertEqual(
            int(
                metrics["tact_index"]
            ),
            5,
        )

        self.assertEqual(
            int(
                metrics["step"]
            ),
            5,
        )

        self.assertAlmostEqual(
            metrics["simulation_time"],
            0.05,
        )

    def test_exported_field_shapes_weights_and_values(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=0.01,
        )

        field = self.engine.export_field_snapshot()

        expected_shapes = {
            "coords_3d": (
                self.config.num_domains,
                3,
            ),
            "phases": (
                self.config.num_domains,
            ),
            "natural_frequencies": (
                self.config.num_domains,
            ),
            "neighbor_indices": (
                self.config.num_domains,
                self.config.neighbor_count,
            ),
            "edge_vectors": (
                self.config.num_domains,
                self.config.neighbor_count,
                3,
            ),
            "edge_distances": (
                self.config.num_domains,
                self.config.neighbor_count,
            ),
            "tau_ij": (
                self.config.num_domains,
                self.config.neighbor_count,
            ),
            "neighbor_weights": (
                self.config.num_domains,
                self.config.neighbor_count,
            ),
            "delayed_neighbor_phases": (
                self.config.num_domains,
                self.config.neighbor_count,
            ),
            "phase_velocity": (
                self.config.num_domains,
            ),
        }

        for key, expected_shape in expected_shapes.items():
            self.assertIn(
                key,
                field,
            )

            values = np.asarray(
                field[key]
            )

            self.assertEqual(
                values.shape,
                expected_shape,
            )

            self.assertTrue(
                np.all(
                    np.isfinite(
                        values
                    )
                ),
                msg=f"Non-finite values in field: {key}",
            )

        np.testing.assert_allclose(
            np.sum(
                field["neighbor_weights"],
                axis=1,
            ),
            np.ones(
                self.config.num_domains
            ),
            rtol=1e-6,
            atol=1e-6,
        )

        self.assertTrue(
            np.all(
                field["edge_distances"]
                > 0.0
            )
        )

        self.assertTrue(
            np.all(
                field["tau_ij"]
                > 0.0
            )
        )

        self.assertTrue(
            np.all(
                field["neighbor_indices"]
                >= 0
            )
        )

        self.assertTrue(
            np.all(
                field["neighbor_indices"]
                < self.config.num_domains
            )
        )

        self.assertGreaterEqual(
            np.min(
                field["phases"]
            ),
            -math.pi
            - 1.0e-6,
        )

        self.assertLess(
            np.max(
                field["phases"]
            ),
            math.pi
            + 1.0e-6,
        )

    def test_same_seed_reproduces_initial_state(self) -> None:
        engine_a = EDKSpatiotemporalPhaseDelayEngine(
            self.config
        )

        engine_b = EDKSpatiotemporalPhaseDelayEngine(
            self.config
        )

        state_a = engine_a.export_field_snapshot()
        state_b = engine_b.export_field_snapshot()

        for key in (
            "coords_3d",
            "phases",
            "natural_frequencies",
            "neighbor_indices",
            "edge_vectors",
            "edge_distances",
            "tau_ij",
            "neighbor_weights",
        ):
            np.testing.assert_allclose(
                state_a[key],
                state_b[key],
                rtol=0.0,
                atol=0.0,
            )


class SpatiotemporalPhaseDelayLoggerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PhaseDelayConfig(
            num_domains=32,
            neighbor_count=6,
            coupling_strength_k=25.0,
            sakaguchi_phase_lag_alpha=0.15,
            wave_velocity_c=12.0,
            coordinate_half_extent=2.0,
            natural_frequency_mean=0.0,
            natural_frequency_std=0.05,
            knn_chunk_size=8,
            delay_safety_margin=3,
            seed=17,
            dtype="float32",
            backend="cpu",
        )

        self.engine = EDKSpatiotemporalPhaseDelayEngine(
            self.config
        )

    def test_logger_writes_metric_and_field_snapshots(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        tact = int(
            self.engine.tact_index
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKDelayLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_tact(
                tact_id=tact,
                engine=self.engine,
                include_field=True,
            )

            tact_json_path = (
                Path(
                    temporary_directory
                )
                / f"delay_tact_{tact:06d}.json"
            )

            step_json_path = (
                Path(
                    temporary_directory
                )
                / f"delay_step_{tact:06d}.json"
            )

            expected_field_path = (
                Path(
                    temporary_directory
                )
                / f"delay_field_{tact:06d}.npz"
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
                tact_record = json.load(
                    stream
                )

            with step_json_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                step_record = json.load(
                    stream
                )

            self.assertEqual(
                tact_record,
                step_record,
            )

            self.assertEqual(
                tact_record["tact"],
                tact,
            )

            self.assertEqual(
                tact_record["step"],
                tact,
            )

            self.assertEqual(
                tact_record["tact_index"],
                tact,
            )

            self.assertAlmostEqual(
                tact_record["simulation_time"],
                float(
                    self.engine.simulation_time
                ),
            )

            self.assertEqual(
                tact_record["backend"],
                "cpu",
            )

            self.assertEqual(
                tact_record["engine_class"],
                "EDKSpatiotemporalPhaseDelayEngine",
            )

            self.assertIn(
                "metrics",
                tact_record,
            )

            self.assertIn(
                "config",
                tact_record,
            )

            self.assertEqual(
                int(
                    tact_record["metrics"]["tact_index"]
                ),
                tact,
            )

            self.assertEqual(
                int(
                    tact_record["metrics"]["step"]
                ),
                tact,
            )

            self.assertAlmostEqual(
                tact_record["metrics"]["simulation_time"],
                float(
                    self.engine.simulation_time
                ),
            )

            with np.load(
                expected_field_path,
                allow_pickle=False,
            ) as archive:
                for key in (
                    "coords_3d",
                    "phases",
                    "natural_frequencies",
                    "neighbor_indices",
                    "edge_vectors",
                    "edge_distances",
                    "tau_ij",
                    "neighbor_weights",
                    "delayed_neighbor_phases",
                    "phase_velocity",
                ):
                    self.assertIn(
                        key,
                        archive.files,
                    )

            self.assertEqual(
                list(
                    Path(
                        temporary_directory
                    ).glob(
                        "*.tmp"
                    )
                ),
                [],
            )

    def test_log_step_alias_matches_log_tact_metadata(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        tact = int(
            self.engine.tact_index
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKDelayLogger(
                temporary_directory
            )

            metrics_path, field_path = logger.log_step(
                step_id=tact,
                engine=self.engine,
                include_field=False,
            )

            self.assertIsNone(
                field_path
            )

            self.assertEqual(
                metrics_path,
                Path(
                    temporary_directory
                )
                / f"delay_tact_{tact:06d}.json",
            )

            with metrics_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                payload = json.load(
                    stream
                )

            self.assertEqual(
                payload["tact"],
                payload["step"],
            )

            self.assertEqual(
                payload["tact_index"],
                payload["tact"],
            )

    def test_logger_rejects_mismatched_tact_id(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKDelayLogger(
                temporary_directory
            )

            with self.assertRaisesRegex(
                ValueError,
                "tact_id must match engine.tact_index",
            ):
                logger.log_tact(
                    tact_id=7,
                    engine=self.engine,
                    include_field=False,
                )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
