from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import numpy as np

try:
    from .edk_vortex_phase_field import (
        EDKVortexLogger,
        EDKVortexPhaseFieldEngine,
        VortexEngineConfig,
    )
except ImportError:
    from edk_vortex_phase_field import (
        EDKVortexLogger,
        EDKVortexPhaseFieldEngine,
        VortexEngineConfig,
    )


class VortexPhaseFieldConfigurationTests(unittest.TestCase):
    def test_minimum_valid_configuration(self) -> None:
        engine = EDKVortexPhaseFieldEngine(
            VortexEngineConfig(
                num_domains=8,
                neighbor_count=3,
                backend="cpu",
                knn_chunk_size=4,
                seed=1,
            )
        )

        self.assertEqual(engine.N, 8)
        self.assertEqual(engine.backend_name, "cpu")
        self.assertEqual(engine.neighbor_indices.shape, (8, 3))

    def test_num_domains_below_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "num_domains must be at least 8",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=7,
                    neighbor_count=3,
                    backend="cpu",
                )
            )

    def test_neighbor_count_below_minimum_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "neighbor_count must be at least 3",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=8,
                    neighbor_count=2,
                    backend="cpu",
                )
            )

    def test_neighbor_count_equal_to_num_domains_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "neighbor_count must be at least 3 and smaller than num_domains",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=8,
                    neighbor_count=8,
                    backend="cpu",
                )
            )

    def test_non_positive_wave_velocity_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "wave_velocity_c must be positive",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=8,
                    neighbor_count=3,
                    wave_velocity_c=0.0,
                    backend="cpu",
                )
            )

    def test_non_positive_knn_chunk_size_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "knn_chunk_size must be positive",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=8,
                    neighbor_count=3,
                    knn_chunk_size=0,
                    backend="cpu",
                )
            )

    def test_unknown_backend_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "backend must be 'auto', 'cpu', or 'gpu'",
        ):
            EDKVortexPhaseFieldEngine(
                VortexEngineConfig(
                    num_domains=8,
                    neighbor_count=3,
                    backend="invalid",
                )
            )


class VortexPhaseFieldRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = VortexEngineConfig(
            num_domains=32,
            neighbor_count=6,
            coupling_strength_k=20.0,
            backend="cpu",
            knn_chunk_size=8,
            seed=11,
        )

        self.engine = EDKVortexPhaseFieldEngine(
            self.config
        )

    def test_negative_external_pressure_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_pressure must be non-negative",
        ):
            self.engine.process_vortex_delayed_interval(
                external_forcing_density=1.0,
                external_pressure=-0.1,
                dt=0.01,
            )

    def test_non_finite_external_pressure_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_pressure must be finite",
        ):
            self.engine.process_vortex_delayed_interval(
                external_forcing_density=1.0,
                external_pressure=math.nan,
                dt=0.01,
            )

    def test_non_finite_external_forcing_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_forcing_density must be finite",
        ):
            self.engine.process_vortex_delayed_interval(
                external_forcing_density=math.inf,
                external_pressure=0.1,
                dt=0.01,
            )

    def test_non_positive_dt_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "dt must be positive",
        ):
            self.engine.process_vortex_delayed_interval(
                external_forcing_density=1.0,
                external_pressure=0.1,
                dt=0.0,
            )

    def test_dt_change_after_history_initialization_is_rejected(self) -> None:
        self.engine.process_vortex_delayed_interval(
            external_forcing_density=1.0,
            external_pressure=0.1,
            dt=0.01,
        )

        with self.assertRaisesRegex(
            ValueError,
            "dt changed after delay history initialization",
        ):
            self.engine.process_vortex_delayed_interval(
                external_forcing_density=1.0,
                external_pressure=0.1,
                dt=0.02,
            )

    def test_negative_pressure_is_rejected_by_appearance_calculation(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_pressure must be non-negative",
        ):
            self.engine.calculate_vortex_appearance(
                -0.1
            )

    def test_non_finite_pressure_is_rejected_by_appearance_calculation(
        self,
    ) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "external_pressure must be finite",
        ):
            self.engine.calculate_vortex_appearance(
                math.nan
            )

    def test_one_interval_produces_finite_bounded_metrics(
        self,
    ) -> None:
        metrics = self.engine.process_vortex_delayed_interval(
            external_forcing_density=1.0,
            external_pressure=0.1,
            dt=0.01,
        )

        required_metrics = (
            "R_t_phase_order",
            "phase_amplitude_coherence",
            "local_phase_coherence",
            "amplitude_retention",
            "C_proxy_t",
            "interface_retention_proxy",
            "M_proxy_t",
            "mean_vorticity_abs",
            "mean_vorticity_signed",
            "vortex_alignment",
            "positive_vortex_support",
            "negative_vortex_penalty",
            "continuum_appearance_index",
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
                msg=(
                    f"Non-finite metric: "
                    f"{key}={metrics[key]}"
                ),
            )

        for key in (
            "R_t_phase_order",
            "phase_amplitude_coherence",
            "local_phase_coherence",
            "amplitude_retention",
            "C_proxy_t",
            "interface_retention_proxy",
            "positive_vortex_support",
            "negative_vortex_penalty",
        ):
            self.assertGreaterEqual(
                metrics[key],
                0.0,
            )

            self.assertLessEqual(
                metrics[key],
                1.0,
            )

        self.assertGreaterEqual(
            metrics["vortex_alignment"],
            -1.0,
        )

        self.assertLessEqual(
            metrics["vortex_alignment"],
            1.0,
        )

        self.assertGreaterEqual(
            metrics["M_proxy_t"],
            0.0,
        )

        self.assertGreaterEqual(
            metrics["continuum_appearance_index"],
            0.0,
        )

        self.assertGreater(
            metrics["mean_vorticity_abs"],
            0.0,
        )

    def test_positive_and_negative_vortex_terms_are_separate_metrics(
        self,
    ) -> None:
        metrics = self.engine.process_vortex_delayed_interval(
            external_forcing_density=1.0,
            external_pressure=0.1,
            dt=0.01,
        )

        self.assertIn(
            "positive_vortex_support",
            metrics,
        )

        self.assertIn(
            "negative_vortex_penalty",
            metrics,
        )

        self.assertGreaterEqual(
            metrics["positive_vortex_support"],
            0.0,
        )

        self.assertGreaterEqual(
            metrics["negative_vortex_penalty"],
            0.0,
        )

    def test_exported_field_shapes_and_values(
        self,
    ) -> None:
        self.engine.process_vortex_delayed_interval(
            external_forcing_density=1.0,
            external_pressure=0.1,
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
            "amplitudes": (
                self.config.num_domains,
            ),
            "node_exchange_current": (
                self.config.num_domains,
                3,
            ),
            "curl_J": (
                self.config.num_domains,
                3,
            ),
            "signed_vorticity": (
                self.config.num_domains,
            ),
            "local_axes": (
                self.config.num_domains,
                3,
            ),
        }

        for key, expected_shape in expected_shapes.items():
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
                msg=(
                    f"Non-finite values "
                    f"in field: {key}"
                ),
            )

        self.assertFalse(
            np.allclose(
                field["curl_J"],
                0.0,
            )
        )

    def test_logger_writes_tact_and_step_compatibility_fields(
        self,
    ) -> None:
        self.engine.process_vortex_delayed_interval(
            external_forcing_density=1.0,
            external_pressure=0.1,
            dt=0.01,
        )

        with tempfile.TemporaryDirectory() as temporary_dir:
            logger = EDKVortexLogger(
                temporary_dir
            )

            logger.log_tact(
                tact_index=1,
                engine=self.engine,
                include_field=True,
            )

            snapshot_path = (
                Path(temporary_dir)
                / "vortex_step_000001.json"
            )

            field_path = (
                Path(temporary_dir)
                / "vortex_field_000001.npz"
            )

            self.assertTrue(
                snapshot_path.exists()
            )

            self.assertTrue(
                field_path.exists()
            )

            with snapshot_path.open(
                "r",
                encoding="utf-8",
            ) as stream:
                record = json.load(stream)

            self.assertEqual(
                record["tact"],
                1,
            )

            self.assertEqual(
                record["step"],
                1,
            )

            self.assertIn(
                "positive_vortex_support",
                record["metrics"],
            )

            self.assertIn(
                "negative_vortex_penalty",
                record["metrics"],
            )

    def test_same_seed_reproduces_initial_state(
        self,
    ) -> None:
        engine_a = EDKVortexPhaseFieldEngine(
            self.config
        )

        engine_b = EDKVortexPhaseFieldEngine(
            self.config
        )

        state_a = engine_a.export_field_snapshot()
        state_b = engine_b.export_field_snapshot()

        for key in (
            "coords_3d",
            "phases",
            "amplitudes",
            "local_axes",
        ):
            np.testing.assert_allclose(
                state_a[key],
                state_b[key],
                rtol=0.0,
                atol=0.0,
            )


if __name__ == "__main__":
    unittest.main(
        verbosity=2
    )
