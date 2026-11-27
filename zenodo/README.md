# Machine-checked UNSAT certificate for a SAT Competition 2023 multiplier miter

This release covers one benchmark, `multiplier_14bits__miter_14.cnf.xz`, from the [SAT Competition 2023 Main Track Benchmarks](https://doi.org/10.5281/zenodo.11426992). The DIMACS CNF has 4,376 variables and 13,018 clauses. The [Global Benchmark Database entry](https://benchmark-database.de/?track=main_2023) records `result: unknown` for GBD hash `017ba03ed108f492c9293c7c95e5cae9`.

VeriPB 3.0.2 and CakePB CP2026 independently accepted the same kernel-format Cutting-Planes proof against the official CNF after byte-for-byte XZ decompression. The proof has 14,123 `pol` steps and verifies without `--elaborate`.

## Reproduce verification

Use Python 3.11 or later, VeriPB 3.0.2 and the CakePB CP2026 DIMACS frontend `cake_pb_cnf`. With both checker executables on your PATH, run from the release directory.

```sh
python3 verify_certificates.py --checksums-only
python3 verify_certificates.py --fetch-original
```

The second command obtains a pinned 32,684-byte range of the official Zenodo ZIP, verifies the ZIP member and decompresses the original. You can also download `sat-competition-2023-main-benchmarks.zip` from the [source record](https://zenodo.org/records/11426992) and supply the ZIP, its exact XZ member, or that member's unmodified CNF.

```sh
python3 verify_certificates.py --original multiplier_14bits__miter_14.cnf.xz
```

Use `--veripb` and `--cakepb` if the checker executables are outside PATH. Windows Python supports `--cakepb-wsl` with a CakePB executable available in WSL. Full verification reports `VERIFIED_UNSAT` and exit code 0 for both checkers. The checksum-only command checks seven release files and the decompressed proof.

The official XZ SHA-256 is `6893371b0497890275d65117720de7d14bde3aaf7d656cc25b09e78b82f4cf5e`. The original CNF SHA-256 is `f59c75f6e2950d19b82a6af181555e484ff44882250ef6a07629e5a41de9fc82`. Obtain benchmark inputs from the official source. See [MANIFEST.json](MANIFEST.json) for file identities and the checker versions and settings used on a Windows 11 x86-64 host with an Intel Core i7 and 64 GiB of installed RAM.

The proof and documentation are under CC BY 4.0. The verifier is under MIT. See [LICENSE](LICENSE) and [third-party notices](THIRD_PARTY_NOTICES.md).
