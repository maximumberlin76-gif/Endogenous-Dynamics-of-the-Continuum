import numpy as np


class MarnovMultidimensionalCoder:
    """
    Marnov Protocol multidimensional encoder and reverse decoder.

    This implementation provides:
    - UTF-8 string encoding into a complex multiplet matrix Q(n),
    - folding into a phase-locked C3 payload,
    - reverse phase-locked decoding back into bytes or text,
    - deterministic spatial-phase addressing with collision protection.
    """

    def __init__(self, grid_size=32, kappa=3.14):
        if grid_size < 4:
            raise ValueError("grid_size must be >= 4")

        self.grid_size = int(grid_size)
        self.kappa = float(kappa)
        self.shape = (self.grid_size, self.grid_size, self.grid_size)
        self.capacity = self.grid_size ** 3

    def _validate_payload_shape(self, payload):
        if payload.shape != self.shape:
            raise ValueError(
                f"Payload shape mismatch. Expected {self.shape}, got {payload.shape}."
            )

    def _ring_candidate_address(self, idx, total_length):
        """
        Generate a primary spatial-phase address on a circular attractor path.

        This preserves the original ring-style addressing idea while allowing
        deterministic collision correction in _address_table().
        """
        cx = self.grid_size // 2
        cy = self.grid_size // 2
        cz = self.grid_size // 2

        angle = (idx / total_length) * 2.0 * np.pi
        radius = max(1, self.grid_size // 4)

        x = int(round(cx + radius * np.cos(angle)))
        y = int(round(cy + radius * np.sin(angle)))
        z = int(cz + (idx % 3 - 1))

        x = min(max(x, 0), self.grid_size - 1)
        y = min(max(y, 0), self.grid_size - 1)
        z = min(max(z, 0), self.grid_size - 1)

        return x, y, z

    def _address_to_flat(self, address):
        x, y, z = address
        return (x * self.grid_size * self.grid_size) + (y * self.grid_size) + z

    def _flat_to_address(self, flat_index):
        x = flat_index // (self.grid_size * self.grid_size)
        remainder = flat_index % (self.grid_size * self.grid_size)
        y = remainder // self.grid_size
        z = remainder % self.grid_size
        return int(x), int(y), int(z)

    def _address_table(self, total_length):
        """
        Build a deterministic collision-free address table.

        Primary addresses follow the ring attractor path. If two bytes map to
        the same coordinate, linear probing assigns the next free voxel.
        """
        if total_length < 0:
            raise ValueError("total_length must be >= 0")

        if total_length > self.capacity:
            raise ValueError(
                f"Input requires {total_length} addresses, but grid capacity is {self.capacity}."
            )

        if total_length == 0:
            return []

        used = set()
        table = []

        for idx in range(total_length):
            primary = self._ring_candidate_address(idx, total_length)
            flat = self._address_to_flat(primary)

            while flat in used:
                flat = (flat + 1) % self.capacity

            used.add(flat)
            table.append(self._flat_to_address(flat))

        return table

    def _byte_to_phase(self, byte_value):
        """
        Map byte values 0..255 to distinct phase bins.

        Division by 256 avoids aliasing between byte 0 and byte 255.
        """
        if not 0 <= int(byte_value) <= 255:
            raise ValueError("byte_value must be in the range 0..255")

        return (int(byte_value) / 256.0) * 2.0 * np.pi

    def _phase_lock(self, phase):
        """
        Apply the phase-lock transformation.
        """
        return phase + self.kappa * np.sin(phase)

    def encode_bytes_to_7d(self, input_bytes):
        """
        Encode a byte sequence into the complex multiplet matrix Q(n).
        """
        if not isinstance(input_bytes, (bytes, bytearray)):
            raise TypeError("input_bytes must be bytes or bytearray")

        data = bytes(input_bytes)
        data_len = len(data)

        q_matrix = np.zeros(self.shape, dtype=np.complex128)

        if data_len == 0:
            return q_matrix

        address_table = self._address_table(data_len)

        for idx, byte_value in enumerate(data):
            phase = self._byte_to_phase(byte_value)
            q_matrix[address_table[idx]] = np.exp(1j * phase)

        return q_matrix

    def encode_string_to_7d(self, input_text):
        """
        Encode a UTF-8 string into the complex multiplet matrix Q(n).
        """
        if not isinstance(input_text, str):
            raise TypeError("input_text must be a string")

        return self.encode_bytes_to_7d(input_text.encode("utf-8"))

    def generate_6d_torus_payload(self, q_matrix):
        """
        Fold the multiplet matrix into the phase-locked C3 payload.
        """
        self._validate_payload_shape(q_matrix)

        phase_q = np.angle(q_matrix)
        magnitude_q = np.abs(q_matrix)

        phase_locked = self._phase_lock(phase_q)

        c3_payload = np.power(magnitude_q, 3) * np.exp(1j * phase_locked)

        return c3_payload

    def _decode_byte_from_locked_complex(self, locked_complex):
        """
        Discretely invert the phase-locked complex trace.

        All 256 possible byte phases are tested. The byte whose phase-locked
        trace is closest to the received complex value is selected.
        """
        if np.abs(locked_complex) < 1e-12:
            return 0

        normalized = locked_complex / np.abs(locked_complex)

        candidates = np.arange(256, dtype=float)
        candidate_phases = (candidates / 256.0) * 2.0 * np.pi
        candidate_locked = np.exp(1j * self._phase_lock(candidate_phases))

        distances = np.abs(candidate_locked - normalized)

        return int(np.argmin(distances))

    def decode_7d_to_bytes(self, c3_payload, original_byte_length):
        """
        Reverse-decode the phase-locked C3 payload into the original byte sequence.
        """
        self._validate_payload_shape(c3_payload)

        if original_byte_length < 0:
            raise ValueError("original_byte_length must be >= 0")

        if original_byte_length == 0:
            return b""

        address_table = self._address_table(original_byte_length)
        decoded = bytearray()

        for address in address_table:
            signal = c3_payload[address]

            if np.abs(signal) < 1e-12:
                decoded.append(0)
                continue

            decoded.append(self._decode_byte_from_locked_complex(signal))

        return bytes(decoded)

    def decode_7d_to_string(self, c3_payload, original_byte_length):
        """
        Reverse-decode the phase-locked C3 payload into a UTF-8 string.
        """
        decoded_bytes = self.decode_7d_to_bytes(c3_payload, original_byte_length)

        try:
            return decoded_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return "[Decoding error: the phase lock was destroyed by environmental noise]"


def verify_text_cycle(coder, source_text):
    """
    Verify a complete text encode-decode cycle.
    """
    source_bytes = source_text.encode("utf-8")

    q_matrix = coder.encode_string_to_7d(source_text)
    c3_payload = coder.generate_6d_torus_payload(q_matrix)
    decoded_text = coder.decode_7d_to_string(c3_payload, len(source_bytes))

    return decoded_text == source_text, decoded_text


def verify_bytes_cycle(coder, source_bytes):
    """
    Verify a complete arbitrary byte encode-decode cycle.
    """
    q_matrix = coder.encode_bytes_to_7d(source_bytes)
    c3_payload = coder.generate_6d_torus_payload(q_matrix)
    decoded_bytes = coder.decode_7d_to_bytes(c3_payload, len(source_bytes))

    return decoded_bytes == source_bytes, decoded_bytes


if __name__ == "__main__":
    coder = MarnovMultidimensionalCoder(grid_size=32, kappa=3.14)

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
        passed, decoded_text = verify_text_cycle(coder, source_text)

        print(f"Source:  {source_text}")
        print(f"Decoded: {decoded_text}")
        print(f"Status:  {'PASSED' if passed else 'FAILED'}")
        print()

        if not passed:
            raise RuntimeError("Text verification failed")

    binary_payload = bytes(range(256))
    passed, decoded_payload = verify_bytes_cycle(coder, binary_payload)

    print("BYTE VERIFICATION")
    print("=================")
    print(f"Payload length: {len(binary_payload)} bytes")
    print(f"Status:         {'PASSED' if passed else 'FAILED'}")

    if not passed:
        raise RuntimeError("Byte verification failed")

    print()
    print("[STATUS]: FULL VERIFICATION PASSED.")
