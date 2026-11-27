#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Verify the multiplier miter certificate against the exact competition CNF."""
import argparse
import gzip
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
from tempfile import TemporaryDirectory
from time import monotonic
from urllib.request import Request, urlopen
import zipfile
import zlib


PROOF = "multiplier_14bits_miter_14.pbp.gz"
CHECKED_FILES = frozenset({
    PROOF, "verify_certificates.py", "MANIFEST.json", "README.md", "README.ja.md",
    "LICENSE", "THIRD_PARTY_NOTICES.md",
})
SOURCE = {
    "DOI": "10.5281/zenodo.11426992",
    "record": "https://zenodo.org/records/11426992",
    "zip_file": "sat-competition-2023-main-benchmarks.zip",
    "zip_url": "https://zenodo.org/records/11426992/files/sat-competition-2023-main-benchmarks.zip?download=1",
    "zip_bytes": 3367333095,
    "zip_range_first": 1940933786,
    "zip_range_last": 1940966469,
    "zip_range_sha256": "6b952ccb8e2a404d1101944af56b3d272d172e35c8a35a961c91ff0c66eb1b60",
    "zip_member_storage_method": 0,
    "zip_member_data_offset": 92,
    "zip_member_crc32": "96a12c58",
    "member": "multiplier_14bits__miter_14.cnf.xz",
    "member_bytes": 32364,
    "member_sha256": "6893371b0497890275d65117720de7d14bde3aaf7d656cc25b09e78b82f4cf5e",
    "cnf_bytes": 186196,
    "cnf_sha256": "f59c75f6e2950d19b82a6af181555e484ff44882250ef6a07629e5a41de9fc82",
    "variables": 4376,
    "clauses": 13018
}
PROOF_STEPS = 14123


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check_release(bundle):
    entries = {}
    for line in (bundle / "SHA256SUMS.txt").read_text(encoding="ascii").splitlines():
        match = re.fullmatch(r"([a-f0-9]{64})  ([A-Za-z0-9_.-]+)", line)
        require(match, "Malformed checksum line")
        checksum, name = match.groups()
        require(name in CHECKED_FILES and name not in entries, f"Unexpected checksum entry: {name}")
        path = bundle / name
        require(path.is_file() and not path.is_symlink(), f"Missing or nonregular file: {name}")
        require(sha_file(path) == checksum, f"SHA-256 mismatch: {name}")
        entries[name] = checksum
    require(set(entries) == CHECKED_FILES, "Incomplete checksum list")
    manifest = json.loads((bundle / "MANIFEST.json").read_text(encoding="utf-8"))
    require(manifest["source"] == SOURCE, "Manifest source does not match the pinned competition input")
    record = manifest["certificate"]
    archive = bundle / PROOF
    require(record["filename"] == PROOF and record["status"] == "VERIFIED_UNSAT"
            and record["format"] == "Cutting-Planes kernel proof" and record["proof_steps"] == PROOF_STEPS
            and record["sha256"] == entries[PROOF] and archive.stat().st_size == record["bytes"],
            "Manifest certificate record does not match the archive")
    limit = record["uncompressed_bytes"]
    require(type(limit) is int and 0 < limit <= 1024**2, "Unexpected decompressed proof size")
    with gzip.open(archive, "rb") as stream:
        proof = stream.read(limit + 1)
    require(len(proof) == limit and digest(proof) == record["uncompressed_sha256"],
            "Decompressed proof size or SHA-256 mismatch")
    return proof


def check_cnf(data):
    require(len(data) == SOURCE["cnf_bytes"], "Original CNF byte count mismatch")
    require(digest(data) == SOURCE["cnf_sha256"], "Original CNF SHA-256 mismatch")
    return data


def expand_xz(blob):
    require(len(blob) == SOURCE["member_bytes"], "Original XZ byte count mismatch")
    require(digest(blob) == SOURCE["member_sha256"], "Original XZ SHA-256 mismatch")
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=256 * 1024**2)
    data = decoder.decompress(blob, max_length=SOURCE["cnf_bytes"] + 1)
    require(decoder.eof and not decoder.unused_data, "Invalid original XZ stream")
    return check_cnf(data)


def original_from_file(path):
    extension = path.suffix.lower()
    if extension == ".zip":
        with zipfile.ZipFile(path) as archive:
            members = [item for item in archive.infolist() if item.filename == SOURCE["member"]]
            require(len(members) == 1 and members[0].file_size == SOURCE["member_bytes"]
                    and f"{members[0].CRC:08x}" == SOURCE["zip_member_crc32"],
                    "Official member name, size or CRC32 differs")
            with archive.open(members[0]) as member:
                return expand_xz(member.read(SOURCE["member_bytes"] + 1))
    with path.open("rb") as data:
        if extension == ".xz":
            return expand_xz(data.read(SOURCE["member_bytes"] + 1))
        require(extension == ".cnf", "Use a competition ZIP, exact .cnf.xz member, or exact .cnf")
        return check_cnf(data.read(SOURCE["cnf_bytes"] + 1))


def original_from_zenodo():
    first, last = SOURCE["zip_range_first"], SOURCE["zip_range_last"]
    request = Request(SOURCE["zip_url"],
                      headers={"Range": f"bytes={first}-{last}", "Accept-Encoding": "identity"})
    length = last - first + 1
    with urlopen(request, timeout=40) as response:
        content_range = f"bytes {first}-{last}/{SOURCE['zip_bytes']}"
        require(response.status == 206 and response.headers.get("Content-Range") == content_range,
                "The official archive did not return the pinned range. Use --original with the official file.")
        part = response.read(length + 1)
    require(len(part) == length and digest(part) == SOURCE["zip_range_sha256"],
            "Official ZIP range SHA-256 mismatch")
    magic, version, flags, method, mtime, mdate, crc, stored, member_bytes, nlen, extra = struct.unpack_from(
        "<4s5H3I2H", part
    )
    begin = 30 + nlen + extra
    require(magic == b"PK\x03\x04" and flags == 0 and method == SOURCE["zip_member_storage_method"]
            and begin == SOURCE["zip_member_data_offset"]
            and part[30:30 + nlen] == SOURCE["member"].encode("ascii")
            and stored == member_bytes == SOURCE["member_bytes"] and f"{crc:08x}" == SOURCE["zip_member_crc32"],
            "Unexpected official ZIP member header")
    member = part[begin:begin + stored]
    require(zlib.crc32(member) == crc, "Official ZIP member CRC32 mismatch")
    return expand_xz(member)


def wsl_path(path):
    result = subprocess.run(["wsl.exe", "--exec", "wslpath", "-a", "-u", str(path.resolve())],
                            check=True, capture_output=True, text=True, timeout=20)
    translated = result.stdout.strip()
    require(translated.startswith("/"), "Could not translate the checker input path for WSL")
    return translated


def cakepb_command(binary, cnf, proof, use_wsl):
    settings = os.environ.copy()
    settings.setdefault("CML_HEAP_SIZE", "2048")
    settings.setdefault("CML_STACK_SIZE", "512")
    if not use_wsl:
        return [binary, str(cnf), str(proof)], settings
    return [
        "wsl.exe", "--exec", "env",
        f"CML_HEAP_SIZE={settings['CML_HEAP_SIZE']}", f"CML_STACK_SIZE={settings['CML_STACK_SIZE']}",
        binary, wsl_path(cnf), wsl_path(proof),
    ], settings


def check_with(cmd, marker, checker, timeout, environment=None):
    start = monotonic()
    outcome = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace",
                             timeout=timeout, env=environment)
    if outcome.returncode != 0 or marker not in outcome.stdout.splitlines():
        detail = (outcome.stderr or outcome.stdout).strip()[-400:]
        raise ValueError(f"{checker} did not verify UNSAT (exit {outcome.returncode}). {detail}")
    return {"status": "VERIFIED_UNSAT", "exit_code": 0, "marker": marker,
            "wall_seconds": round(monotonic() - start, 6)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, default=Path(__file__).resolve().parent)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--checksums-only", action="store_true", help="Check release and proof data hashes")
    source.add_argument("--original", type=Path, help="Original ZIP, .cnf.xz member, or unmodified .cnf")
    source.add_argument("--fetch-original", action="store_true", help="Read the pinned official Zenodo ZIP range")
    parser.add_argument("--veripb", default="veripb", help="VeriPB 3.0.2 executable")
    parser.add_argument("--cakepb", default="cake_pb_cnf", help="CakePB CP2026 DIMACS checker executable")
    parser.add_argument("--cakepb-wsl", action="store_true", help="Run CakePB with WSL when Python runs on Windows")
    parser.add_argument("--timeout", default=180, type=int, help="Seconds per external checker")
    opt = parser.parse_args()
    if opt.timeout <= 0 or (opt.cakepb_wsl and os.name != "nt"):
        parser.error("--timeout must be positive and --cakepb-wsl is available on Windows")
    try:
        proof = check_release(opt.bundle)
        result = {"checksums_passed": len(CHECKED_FILES), "certificates": 1, "proof_sha256": digest(proof),
                  "proof_steps": PROOF_STEPS, "original_cnf_checked": False}
        if not opt.checksums_only:
            data = original_from_zenodo() if opt.fetch_original else original_from_file(opt.original)
            with TemporaryDirectory(prefix="multiplier14-verify-") as work:
                cnf = Path(work) / "original.cnf"
                pbp = Path(work) / "certificate.pbp"
                cnf.write_bytes(data)
                pbp.write_bytes(proof)
                result["original_cnf_checked"] = True
                result["original_cnf_sha256"] = digest(data)
                result["VeriPB"] = check_with(
                    [opt.veripb, "--cnf", str(cnf), str(pbp)], "s VERIFIED UNSATISFIABLE", "VeriPB", opt.timeout
                )
                command, environment = cakepb_command(opt.cakepb, cnf, pbp, opt.cakepb_wsl)
                result["CakePB"] = check_with(command, "s VERIFIED UNSAT", "CakePB", opt.timeout, environment)
                require(sha_file(cnf) == SOURCE["cnf_sha256"] and sha_file(pbp) == digest(proof),
                        "The checker input bytes changed during verification")
    except (OSError, EOFError, ValueError, KeyError, TypeError, zipfile.BadZipFile, lzma.LZMAError,
            subprocess.TimeoutExpired, subprocess.CalledProcessError) as error:
        print(f"Verification failed: {error}", file=sys.stderr)
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
