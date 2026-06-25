from __future__ import annotations

import json
import math
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
    from edk_spatiotemporal_phase_delay import (
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

        self.assertEqual(engine.N, 4)
        self.assertEqual(engine.k, 1)
        self.assertEqual(engine.backend_name, "cpu")
        self.assertEqual(engine.neighbor_indices.shape, (4, 1))

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
            "dt must be positive",
        ):
            self.engine.process_delayed_interval(
                external_forcing_density=1.0,
                external_forcing_phase=0.0,
                dt=0.0,
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
            self.assertIn(key, metrics)
            self.assertTrue(
                math.isfinite(metrics[key]),
                msg=f"Non-finite metric: {key}={metrics[key]}",
            )

        self.assertGreaterEqual(metrics["R_t_phase_order"], 0.0)
        self.assertLessEqual(metrics["R_t_phase_order"], 1.0)
        self.assertGreaterEqual(metrics["delayed_local_phase_order"], 0.0)
        self.assertLessEqual(metrics["delayed_local_phase_order"], 1.0)
        self.assertGreaterEqual(metrics["global_mean_phase"], -math.pi)
        self.assertLessEqual(metrics["global_mean_phase"], math.pi)
        self.assertGreaterEqual(
            metrics["delayed_coupling_energy_proxy"],
            -1.0,
        )
        self.assertLessEqual(
            metrics["delayed_coupling_energy_proxy"],
            1.0,
        )
        self.assertGreaterEqual(metrics["phase_velocity_dispersion"], 0.0)
        self.assertGreater(metrics["mean_delay"], 0.0)
        self.assertGreaterEqual(
            metrics["maximum_delay"],
            metrics["mean_delay"],
        )
        self.assertGreaterEqual(metrics["delay_dispersion"], 0.0)

        expected_minimum_history_depth = (
            math.ceil(self.engine.maximum_delay / 0.01)
            + self.config.delay_safety_margin
        )

        self.assertGreaterEqual(
            int(round(metrics["history_buffer_depth"])),
            expected_minimum_history_depth,
        )

    def test_exported_field_shapes_weights_and_values(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.5,
            external_forcing_phase=0.25,
            dt=0.01,
        )

        field = self.engine.export_field_snapshot()

        expected_shapes = {
            "coords_3d": (self.config.num_domains, 3),
            "phases": (self.config.num_domains,),
            "natural_frequencies": (self.config.num_domains,),
            "neighbor_indices": (
                self.config.num_domains,
                self.config.neighbor_count,
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
            "phase_velocity": (self.config.num_domains,),
        }

        for key, expected_shape in expected_shapes.items():
            values = np.asarray(field[key])
            self.assertEqual(values.shape, expected_shape)
            self.assertTrue(
                np.all(np.isfinite(values)),
                msg=f"Non-finite values in field: {key}",
            )

        np.testing.assert_allclose(
            np.sum(field["neighbor_weights"], axis=1),
            np.ones(self.config.num_domains),
            rtol=1e-6,
            atol=1e-6,
        )

        self.assertTrue(np.all(field["edge_distances"] > 0.0))
        self.assertTrue(np.all(field["tau_ij"] > 0.0))
        self.assertTrue(np.all(field["neighbor_indices"] >= 0))
        self.assertTrue(
            np.all(
                field["neighbor_indices"]
                < self.config.num_domains
            )
        )

    def test_same_seed_reproduces_initial_state(self) -> None:
        engine_a = EDKSpatiotemporalPhaseDelayEngine(self.config)
        engine_b = EDKSpatiotemporalPhaseDelayEngine(self.config)

        state_a = engine_a.export_field_snapshot()
        state_b = engine_b.export_field_snapshot()

        for key in (
            "coords_3d",
            "phases",
            "natural_frequencies",
            "neighbor_indices",
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

    def test_logger_writes_metric_and_field_snapshots(self) -> None:
        self.engine.process_delayed_interval(
            external_forcing_density=1.0,
            external_forcing_phase=0.0,
            dt=0.01,
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            logger = EDKDelayLogger(temporary_directory)

            logger.log_step(
                step_id=7,
                engine=self.engine,
                include_field=True,
            )

            json_path = (
                Path(temporary_directory)
                / "delay_step_000007.json"
            )

            field_path = (
                Path(temporary_directory)
                / "delay_field_000007.npz"
            )

            self.assertTrue(json_path.is_file())
            self.assertTrue(field_path.is_file())

            with json_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                record = json.load(stream)

            self.assertEqual(record["step"], 7)
            self.assertEqual(record["backend"], "cpu")
            self.assertIn("metrics", record)
            self.assertIn("config", record)

            with np.load(
                field_path,
                allow_pickle=False,
            ) as archive:
                self.assertIn("coords_3d", archive.files)
                self.assertIn("phases", archive.files)
                self.assertIn("tau_ij", archive.files)


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
