from __future__ import annotations

from typing import Any

import numpy as np


class MarnovMultidimensionalCoder:
    """
    Deterministic phase encoder and reverse decoder for the Marnov Protocol.

    The module implements:

    - collision-free sparse 3D address generation;
    - byte-to-phase mapping;
    - sparse complex payload construction;
    - nonlinear phase-lock transformation;
    - reverse reconstruction through 256-candidate phase matching;
    - UTF-8 reconstruction as an optional layer above exact byte recovery.
    """

    def __init__(
        self,
        grid_size: int = 32,
        kappa: float = 3.14,
        zero_tolerance: float = 1.0e-12,
    ) -> None:
        if isinstance(grid_size, bool):
            raise ValueError("grid_size must be an integer.")

        try:
            converted_grid_size = int(grid_size)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError("grid_size must be an integer.") from exc

        if converted_grid_size != grid_size:
            raise ValueError("grid_size must be an integer.")

        if converted_grid_size < 4:
            raise ValueError("grid_size must be at least 4.")

        self.grid_size = converted_grid_size
        self.kappa = self._finite_scalar("kappa", kappa)
        self.zero_tolerance = self._positive_finite(
            "zero_tolerance",
            zero_tolerance,
        )

        self.shape = (
            self.grid_size,
            self.grid_size,
            self.grid_size,
        )
        self.capacity = self.grid_size ** 3

        self._candidate_byte_values = np.arange(
            256,
            dtype=np.uint16,
        )
        self._candidate_phases = (
            self._candidate_byte_values.astype(np.float64)
            / 256.0
            * 2.0
            * np.pi
        )
        self._candidate_locked_values = np.exp(
            1j
            * self._phase_lock(self._candidate_phases)
        )

        self._validate_candidate_table()

    @staticmethod
    def _finite_scalar(
        name: str,
        value: float,
    ) -> float:
        try:
            scalar = float(value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(f"{name} must be a finite scalar.") from exc

        if not np.isfinite(scalar):
            raise ValueError(f"{name} must be finite.")

        return scalar

    @classmethod
    def _positive_finite(
        cls,
        name: str,
        value: float,
    ) -> float:
        scalar = cls._finite_scalar(name, value)

        if scalar <= 0.0:
            raise ValueError(f"{name} must be positive.")

        return scalar

    def _validate_candidate_table(self) -> None:
        if self._candidate_locked_values.shape != (256,):
            raise RuntimeError("candidate table has an invalid shape.")

        if not np.all(np.isfinite(self._candidate_locked_values)):
            raise FloatingPointError(
                "candidate locked values contain non-finite values."
            )

    def _validate_payload_shape(
        self,
        payload: np.ndarray,
        name: str = "payload",
    ) -> np.ndarray:
        array = np.asarray(
            payload,
            dtype=np.complex128,
        )

        if array.shape != self.shape:
            raise ValueError(
                f"{name} shape mismatch. Expected {self.shape}, "
                f"received {array.shape}."
            )

        if not np.all(np.isfinite(array)):
            raise ValueError(f"{name} contains non-finite values.")

        return array

    def _validate_original_byte_length(
        self,
        original_byte_length: int,
    ) -> int:
        if isinstance(original_byte_length, bool):
            raise ValueError("original_byte_length must be an integer.")

        try:
            length = int(original_byte_length)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "original_byte_length must be an integer."
            ) from exc

        if length != original_byte_length:
            raise ValueError("original_byte_length must be an integer.")

        if length < 0:
            raise ValueError("original_byte_length must be non-negative.")

        if length > self.capacity:
            raise ValueError(
                f"original_byte_length requires {length} addresses, "
                f"but grid capacity is {self.capacity}."
            )

        return length

    def _ring_candidate_address(
        self,
        index: int,
        total_length: int,
    ) -> tuple[int, int, int]:
        center_x = self.grid_size // 2
        center_y = self.grid_size // 2
        center_z = self.grid_size // 2

        angle = (
            index
            / total_length
            * 2.0
            * np.pi
        )
        radius = max(
            1,
            self.grid_size // 4,
        )

        x = int(
            round(
                center_x
                + radius
                * np.cos(angle)
            )
        )
        y = int(
            round(
                center_y
                + radius
                * np.sin(angle)
            )
        )
        z = int(
            center_z
            + (
                index
                % 3
                - 1
            )
        )

        x = min(max(x, 0), self.grid_size - 1)
        y = min(max(y, 0), self.grid_size - 1)
        z = min(max(z, 0), self.grid_size - 1)

        return x, y, z

    def _address_to_flat(
        self,
        address: tuple[int, int, int],
    ) -> int:
        x, y, z = address

        return int(
            x
            * self.grid_size
            * self.grid_size
            + y
            * self.grid_size
            + z
        )

    def _flat_to_address(
        self,
        flat_index: int,
    ) -> tuple[int, int, int]:
        x = flat_index // (self.grid_size * self.grid_size)
        remainder = flat_index % (self.grid_size * self.grid_size)
        y = remainder // self.grid_size
        z = remainder % self.grid_size

        return int(x), int(y), int(z)

    def _address_table(
        self,
        total_length: int,
    ) -> list[tuple[int, int, int]]:
        length = self._validate_original_byte_length(total_length)

        if length == 0:
            return []

        used: set[int] = set()
        table: list[tuple[int, int, int]] = []

        for index in range(length):
            primary_address = self._ring_candidate_address(
                index,
                length,
            )
            flat_index = self._address_to_flat(primary_address)

            probe_count = 0

            while flat_index in used:
                flat_index = (
                    flat_index
                    + 1
                ) % self.capacity
                probe_count += 1

                if probe_count > self.capacity:
                    raise RuntimeError(
                        "address table generation exceeded grid capacity."
                    )

            used.add(flat_index)
            table.append(self._flat_to_address(flat_index))

        return table

    @staticmethod
    def _byte_to_phase(
        byte_value: int,
    ) -> float:
        try:
            converted = int(byte_value)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "byte_value must be an integer in the range 0..255."
            ) from exc

        if not 0 <= converted <= 255:
            raise ValueError(
                "byte_value must be in the range 0..255."
            )

        return float(
            converted
            / 256.0
            * 2.0
            * np.pi
        )

    def _phase_lock(
        self,
        phase: float | np.ndarray,
    ) -> float | np.ndarray:
        return phase + self.kappa * np.sin(phase)

    def encode_bytes_to_grid(
        self,
        input_bytes: bytes | bytearray | memoryview,
    ) -> np.ndarray:
        """
        Encode a byte sequence into a sparse 3D complex grid.
        """
        if not isinstance(input_bytes, (bytes, bytearray, memoryview)):
            raise TypeError(
                "input_bytes must be bytes, bytearray, or memoryview."
            )

        data = bytes(input_bytes)
        data_length = len(data)

        q_grid = np.zeros(
            self.shape,
            dtype=np.complex128,
        )

        if data_length == 0:
            return q_grid

        address_table = self._address_table(data_length)

        for index, byte_value in enumerate(data):
            phase = self._byte_to_phase(byte_value)
            q_grid[address_table[index]] = np.exp(
                1j
                * phase
            )

        return q_grid

    def encode_text_to_grid(
        self,
        input_text: str,
        encoding: str = "utf-8",
    ) -> np.ndarray:
        """
        Encode a text string into a sparse 3D complex grid.
        """
        if not isinstance(input_text, str):
            raise TypeError("input_text must be a string.")

        return self.encode_bytes_to_grid(
            input_text.encode(encoding)
        )

    def generate_locked_payload(
        self,
        q_grid: np.ndarray,
    ) -> np.ndarray:
        """
        Apply the nonlinear phase-lock transformation to Q_grid.
        """
        grid = self._validate_payload_shape(
            q_grid,
            name="q_grid",
        )

        magnitude = np.abs(grid)
        phase = np.angle(grid)
        phase_locked = self._phase_lock(phase)

        locked_payload = (
            magnitude ** 3
            * np.exp(
                1j
                * phase_locked
            )
        )

        return self._validate_payload_shape(
            locked_payload,
            name="locked_payload",
        )

    def _decode_byte_from_locked_complex(
        self,
        locked_complex: complex,
    ) -> int:
        signal = complex(locked_complex)

        if not (
            np.isfinite(signal.real)
            and np.isfinite(signal.imag)
        ):
            raise ValueError(
                "locked_complex contains non-finite values."
            )

        magnitude = abs(signal)

        if magnitude < self.zero_tolerance:
            return 0

        normalized = signal / magnitude

        distances = np.abs(
            self._candidate_locked_values
            - normalized
        )

        return int(
            self._candidate_byte_values[
                int(np.argmin(distances))
            ]
        )

    def decode_locked_payload_to_bytes(
        self,
        locked_payload: np.ndarray,
        original_byte_length: int,
    ) -> bytes:
        """
        Reconstruct the original byte sequence by phase-candidate matching.
        """
        payload = self._validate_payload_shape(
            locked_payload,
            name="locked_payload",
        )
        length = self._validate_original_byte_length(original_byte_length)

        if length == 0:
            return b""

        address_table = self._address_table(length)
        decoded = bytearray()

        for address in address_table:
            decoded.append(
                self._decode_byte_from_locked_complex(
                    payload[address]
                )
            )

        return bytes(decoded)

    def decode_locked_payload_to_text(
        self,
        locked_payload: np.ndarray,
        original_byte_length: int,
        encoding: str = "utf-8",
    ) -> dict[str, Any]:
        """
        Reconstruct UTF-8 text from decoded bytes and return status data.
        """
        decoded_bytes = self.decode_locked_payload_to_bytes(
            locked_payload,
            original_byte_length,
        )

        try:
            decoded_text = decoded_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            return {
                "ok": False,
                "text": "",
                "bytes": decoded_bytes,
                "encoding": encoding,
                "error": str(exc),
            }

        return {
            "ok": True,
            "text": decoded_text,
            "bytes": decoded_bytes,
            "encoding": encoding,
            "error": "",
        }

    def verify_text_cycle(
        self,
        source_text: str,
        encoding: str = "utf-8",
    ) -> tuple[bool, str]:
        """
        Verify a complete text encode-decode cycle.
        """
        if not isinstance(source_text, str):
            raise TypeError("source_text must be a string.")

        source_bytes = source_text.encode(encoding)
        q_grid = self.encode_text_to_grid(source_text, encoding=encoding)
        locked_payload = self.generate_locked_payload(q_grid)
        decoded_status = self.decode_locked_payload_to_text(
            locked_payload,
            len(source_bytes),
            encoding=encoding,
        )

        decoded_text = str(decoded_status["text"])

        return (
            bool(decoded_status["ok"] and decoded_text == source_text),
            decoded_text,
        )

    def verify_bytes_cycle(
        self,
        source_bytes: bytes | bytearray | memoryview,
    ) -> tuple[bool, bytes]:
        """
        Verify a complete arbitrary byte encode-decode cycle.
        """
        data = bytes(source_bytes)
        q_grid = self.encode_bytes_to_grid(data)
        locked_payload = self.generate_locked_payload(q_grid)
        decoded_bytes = self.decode_locked_payload_to_bytes(
            locked_payload,
            len(data),
        )

        return decoded_bytes == data, decoded_bytes

    def encode_bytes_to_7d(
        self,
        input_bytes: bytes | bytearray | memoryview,
    ) -> np.ndarray:
        """
        Backward-compatible alias for encode_bytes_to_grid.
        """
        return self.encode_bytes_to_grid(input_bytes)

    def encode_string_to_7d(
        self,
        input_text: str,
    ) -> np.ndarray:
        """
        Backward-compatible alias for encode_text_to_grid.
        """
        return self.encode_text_to_grid(input_text)

    def generate_6d_torus_payload(
        self,
        q_matrix: np.ndarray,
    ) -> np.ndarray:
        """
        Backward-compatible alias for generate_locked_payload.
        """
        return self.generate_locked_payload(q_matrix)

    def decode_7d_to_bytes(
        self,
        c3_payload: np.ndarray,
        original_byte_length: int,
    ) -> bytes:
        """
        Backward-compatible alias for decode_locked_payload_to_bytes.
        """
        return self.decode_locked_payload_to_bytes(
            c3_payload,
            original_byte_length,
        )

    def decode_7d_to_string(
        self,
        c3_payload: np.ndarray,
        original_byte_length: int,
    ) -> str:
        """
        Backward-compatible text decoder returning only the text string.
        """
        decoded_status = self.decode_locked_payload_to_text(
            c3_payload,
            original_byte_length,
        )

        if decoded_status["ok"]:
            return str(decoded_status["text"])

        return str(decoded_status["error"])


def verify_text_cycle(
    coder: MarnovMultidimensionalCoder,
    source_text: str,
) -> tuple[bool, str]:
    """
    Verify a complete text encode-decode cycle.
    """
    return coder.verify_text_cycle(source_text)


def verify_bytes_cycle(
    coder: MarnovMultidimensionalCoder,
    source_bytes: bytes | bytearray | memoryview,
) -> tuple[bool, bytes]:
    """
    Verify a complete arbitrary byte encode-decode cycle.
    """
    return coder.verify_bytes_cycle(source_bytes)


if __name__ == "__main__":
    coder = MarnovMultidimensionalCoder(
        grid_size=32,
        kappa=3.14,
    )

    text_messages = [
        "Marnov_Protocol_7D_Success",
        "hello",
        "Privet",
        "EDK Continuum",
        "Привет",
        "EDK Континуум",
        "Reverse Decoding of the Marnov Protocol",
    ]

    print("TEXT VERIFICATION")
    print("=================")

    for source_text in text_messages:
        passed, decoded_text = verify_text_cycle(
            coder,
            source_text,
        )

        print(f"Source:  {source_text}")
        print(f"Decoded: {decoded_text}")
        print(f"Status:  {'PASSED' if passed else 'FAILED'}")
        print()

        if not passed:
            raise RuntimeError("Text verification failed.")

    binary_payload = bytes(range(256))
    passed, decoded_payload = verify_bytes_cycle(
        coder,
        binary_payload,
    )

    print("BYTE VERIFICATION")
    print("=================")
    print(f"Payload length: {len(binary_payload)} bytes")
    print(f"Status:         {'PASSED' if passed else 'FAILED'}")

    if not passed:
        raise RuntimeError("Byte verification failed.")

    print()
    print("[STATUS]: FULL VERIFICATION PASSED.")
