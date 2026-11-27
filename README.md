# Machine-Checked Unsatisfiability Certificate for SAT Competition 2023 multiplier_14bits__miter_14

VeriPB 3.0.2 and CakePB CP2026 accepted the same 14,123-step cutting-planes proof on the original CNF for `multiplier_14bits__miter_14.cnf.xz`. This SAT Competition 2023 instance has 4,376 variables and 13,018 clauses.

The [Zenodo dataset](https://zenodo.org/records/24500045) is the canonical release. Cite [DOI 10.5281/zenodo.24500045](https://doi.org/10.5281/zenodo.24500045).

[Dataset documentation](zenodo/README.md) · [日本語の説明](zenodo/README.ja.md) · [Manifest](zenodo/MANIFEST.json)

## Files hosted on Zenodo

- [multiplier_14bits_miter_14.pbp.gz](https://zenodo.org/records/24500045/files/multiplier_14bits_miter_14.pbp.gz?download=1)

## Verify the release

Download every file linked above into the `zenodo/` directory of this repository. From the repository root, use Python 3.11 or later to check the complete release.

```sh
python zenodo/verify_certificates.py --bundle zenodo --checksums-only
```

For replay against the official benchmark inputs, follow the [verification instructions](zenodo/README.md).

## License and citation

Generated data and documentation are licensed under CC BY 4.0. The public verifier is MIT-licensed. See the [license](zenodo/LICENSE), [third-party notices](zenodo/THIRD_PARTY_NOTICES.md) and [citation file](CITATION.cff).
