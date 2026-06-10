#!/usr/bin/env python3
"""
JSON to 香色闺阁 XBS converter
Uses XXTEA encryption with the fixed key from xbsrebuild
"""
import struct
import json
import sys

def xxtea_encrypt(data, key):
    """Pure Python XXTEA encryption"""
    if not data:
        return b''

    # Pad to 4-byte boundary
    data_len = len(data)
    pad_len = (4 - data_len % 4) % 4
    if pad_len:
        data = data + b'\x00' * pad_len

    # Pack into 32-bit unsigned integers (little-endian)
    v = list(struct.unpack('<' + 'I' * (len(data) // 4), data))
    k = list(struct.unpack('<' + 'I' * (len(key) // 4), key[:16]))

    n = len(v) - 1
    if n < 1:
        return data

    z = v[n]
    y = v[0]
    q = 6 + 52 // (n + 1)
    p = 0
    delta = 0x9E3779B9

    while q > 0:
        q -= 1
        p = (p + delta) & 0xFFFFFFFF
        e = (p >> 2) & 3
        for i in range(n + 1):
            y = v[(i + 1) % (n + 1)]
            mx = ((((z >> 5) ^ (y << 2)) + ((y >> 3) ^ (z << 4))) ^ ((p ^ y) + (k[(i & 3) ^ e] ^ z)))
            v[i] = (v[i] + mx) & 0xFFFFFFFF
            z = v[i]

    return struct.pack('<' + 'I' * (n + 1), *v)


def json2xbs(json_bytes):
    """
    Convert JSON bytes to XBS format.
    Appends original length as uint32 LE, pads, then XXTEA encrypts.
    """
    # Append original length as 4-byte little-endian
    buffer_len = len(json_bytes)
    # Pad to 4 bytes
    pad_len = (4 - buffer_len % 4) % 4
    if pad_len:
        json_bytes = json_bytes + b'\x00' * pad_len
    # Append length
    json_bytes += struct.pack('<I', buffer_len)
    # Encrypt with XXTEA
    key = bytes([0xe5, 0x87, 0xbc, 0xe8, 0xa4, 0x86, 0xe6, 0xbb, 0xbf, 0xe9, 0x87, 0x91, 0xe6, 0xba, 0xa1, 0xe5])
    encrypted = xxtea_encrypt(json_bytes, key)
    return encrypted


def main():
    if len(sys.argv) < 3:
        print("Usage: python json2xbs.py input.json output.xbs")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, 'r', encoding='utf-8') as f:
        json_content = f.read()

    # Validate JSON
    try:
        json.loads(json_content)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON: {e}")
        sys.exit(1)

    json_bytes = json_content.encode('utf-8')
    xbs_bytes = json2xbs(json_bytes)

    with open(output_path, 'wb') as f:
        f.write(xbs_bytes)

    print(f"Converted {input_path} -> {output_path}")
    print(f"JSON size: {len(json_bytes)} bytes -> XBS size: {len(xbs_bytes)} bytes")


if __name__ == '__main__':
    main()
