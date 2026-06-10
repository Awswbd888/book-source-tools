"""
test_encrypt_decrypt.py — XXTEA encrypt/decrypt round-trip tests.

Verifies that encrypt(decrypt(data)) == data and decrypt(encrypt(data)) == data.
"""
import json
import os
import sys

import pytest

# Add scripts dir to path so we can import _common
SCRIPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
sys.path.insert(0, SCRIPTS_DIR)

from _common import json_to_xbs, xbs_to_json, xxtea_encrypt, xxtea_decrypt, XXTEA_KEY


def _padded(data: bytes) -> bytes:
    """Return data padded to 4-byte boundary (as xxtea_encrypt does internally)."""
    pad = (4 - len(data) % 4) % 4
    return data + (b'\x00' * pad) if pad else data


class TestXXTEA:
    """XXTEA encryption/decryption primitive tests.

    Note: xxtea_encrypt pads data to 4-byte boundary internally (XXTEA operates
    on uint32 words). xxtea_decrypt returns the padded version. For the full
    XBS container (with length tracking), use json_to_xbs / xbs_to_json.
    """

    def test_encrypt_then_decrypt_returns_padded_original(self):
        data = b"Hello, XXTEA! This is a test message."
        encrypted = xxtea_encrypt(data, XXTEA_KEY)
        assert len(encrypted) > 0
        assert encrypted != data
        decrypted = xxtea_decrypt(encrypted, XXTEA_KEY)
        assert decrypted == _padded(data)

    def test_decrypt_then_encrypt_returns_original(self):
        data = b"Test data for decrypt-then-encrypt round trip."
        encrypted = xxtea_encrypt(data, XXTEA_KEY)
        decrypted = xxtea_decrypt(encrypted, XXTEA_KEY)
        re_encrypted = xxtea_encrypt(decrypted, XXTEA_KEY)
        assert re_encrypted == encrypted

    def test_empty_data(self):
        assert xxtea_encrypt(b"", XXTEA_KEY) == b""
        assert xxtea_decrypt(b"", XXTEA_KEY) == b""

    def test_short_data(self):
        """Test with 1-7 byte inputs (various padding scenarios)."""
        for i in range(1, 8):
            data = b"x" * i
            encrypted = xxtea_encrypt(data, XXTEA_KEY)
            decrypted = xxtea_decrypt(encrypted, XXTEA_KEY)
            assert decrypted == _padded(data), f"Failed for {i} bytes"

    def test_exact_4_byte_alignment(self):
        data = b"abcd" * 10  # 40 bytes, exactly aligned
        encrypted = xxtea_encrypt(data, XXTEA_KEY)
        decrypted = xxtea_decrypt(encrypted, XXTEA_KEY)
        assert decrypted == data  # No padding needed

    def test_custom_key(self):
        data = b"Custom key test"
        key = b"1234567890abcdef"  # 16 bytes
        encrypted = xxtea_encrypt(data, key)
        decrypted = xxtea_decrypt(encrypted, key)
        assert decrypted == _padded(data)

    def test_wrong_key_fails(self):
        data = b"Secret message"
        encrypted = xxtea_encrypt(data, XXTEA_KEY)
        wrong_key = b"\x00" * 16
        decrypted = xxtea_decrypt(encrypted, wrong_key)
        assert decrypted != _padded(data)

    def test_short_unaligned_data(self):
        """Very short unaligned data should raise (can't be valid ciphertext)."""
        with pytest.raises(ValueError, match="multiple of 4"):
            xxtea_decrypt(b"ab", XXTEA_KEY)

    def test_unaligned_raises(self):
        """Data with len > 8 but not multiple of 4 should raise."""
        with pytest.raises(ValueError, match="multiple of 4"):
            xxtea_decrypt(b"123456789", XXTEA_KEY)  # 9 bytes


class TestXBSRoundTrip:
    """XBS container format round-trip tests."""

    def test_json_to_xbs_round_trip(self, xiangse_json):
        """Encrypt JSON then decrypt back should give original bytes."""
        xbs = json_to_xbs(xiangse_json, XXTEA_KEY)
        assert len(xbs) > 0
        result = xbs_to_json(xbs, XXTEA_KEY)
        assert result == xiangse_json

    def test_xbs_decrypt_matches_original(self, xbs_bytes, xiangse_json):
        """Decrypting existing .xbs file should match original JSON."""
        result = xbs_to_json(xbs_bytes, XXTEA_KEY)
        assert result == xiangse_json

    def test_our_encryption_matches_existing(self, xiangse_json, xbs_bytes):
        """Our encryption should produce identical XBS bytes."""
        our_xbs = json_to_xbs(xiangse_json, XXTEA_KEY)
        assert our_xbs == xbs_bytes

    def test_json_content_preserved(self, xiangse_json):
        """JSON structure and values should survive round-trip."""
        xbs = json_to_xbs(xiangse_json, XXTEA_KEY)
        result = xbs_to_json(xbs, XXTEA_KEY)
        orig = json.loads(xiangse_json)
        parsed = json.loads(result)
        assert orig == parsed

    def test_large_json(self, xiangse_json):
        """Test with a larger JSON payload by repeating the source."""
        large = xiangse_json * 100
        xbs = json_to_xbs(large, XXTEA_KEY)
        result = xbs_to_json(xbs, XXTEA_KEY)
        assert result == large
