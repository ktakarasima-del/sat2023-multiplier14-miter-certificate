# SAT Competition 2023 乗算器ミターの機械検証済みUNSAT証明

対象は [SAT Competition 2023 Main Track Benchmarks](https://doi.org/10.5281/zenodo.11426992) の `multiplier_14bits__miter_14.cnf.xz` 1件です。DIMACS CNFは4,376変数、13,018節です。[Global Benchmark Database](https://benchmark-database.de/?track=main_2023) の対象行（GBDハッシュ `017ba03ed108f492c9293c7c95e5cae9`）には `result: unknown` と記録されています。

公式XZを無加工で展開したCNFに対し、同じカーネル形式のCutting-Planes証明をVeriPB 3.0.2とCakePB CP2026が独立に受理しました。証明には14,123個の `pol` ステップがあり、`--elaborate` を使わずに検証できます。

## 再検証

Python 3.11以上、VeriPB 3.0.2、CakePB CP2026のDIMACSフロントエンド `cake_pb_cnf` が必要です。公開ファイルのディレクトリで実行します。

```sh
python3 verify_certificates.py --checksums-only
python3 verify_certificates.py --fetch-original
```

`--fetch-original` は公式ZIP内の固定範囲32,684バイトを取得し、ZIP内のXZと無加工展開後のCNFをハッシュで照合します。[公式レコード](https://zenodo.org/records/11426992) のZIP、正確なXZメンバー、または展開したCNFを `--original` で指定することもできます。

```sh
python3 verify_certificates.py --original multiplier_14bits__miter_14.cnf.xz
```

検証器の場所は `--veripb` と `--cakepb` で指定できます。WindowsのPythonからWSLのCakePBを使う場合は `--cakepb-wsl` を指定します。完全再検証時の合格条件は、両検証器が `VERIFIED_UNSAT`、終了コード0を返すことです。チェックサム一覧は公開ファイルのうち一覧自身を除く7ファイルをカバーします。

検証環境はWindows 11 x86-64、Intel Core i7、搭載RAM 64 GiBで、CakePBをWSL2上で実行しました。原本と証明のサイズ・SHA-256、検証器バージョンと設定は [MANIFEST.json](MANIFEST.json) に記載しています。

証明と文書はCC BY 4.0、検証スクリプトはMITです。[ライセンス](LICENSE)・[第三者表記](THIRD_PARTY_NOTICES.md)を参照してください。
