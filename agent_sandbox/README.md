# agent-sandbox

OpenAI API で生成した Python コードを [microsandbox](https://microsandbox.dev/) の microVM 上で安全に実行するためのサンドボックス環境です。

## 構成

```
agent_sandbox/
├── main.py                         # エントリポイント (Hello world)
├── pyproject.toml                  # uv プロジェクト定義
├── data/
│   └── sample.csv                  # describe_dataframe 用サンプルデータ
└── scripts/
    ├── sandbox.py                  # microsandbox の最小サンプル
    ├── openai_sandbox.py           # OpenAI が生成したコードを sandbox で実行
    ├── jinja_template.py           # Jinja2 テンプレートの動作確認
    ├── describe_dataframe.py       # CSV を要約するプロンプト生成サンプル
    └── describe_dataframe.jinja    # describe_dataframe.py が読み込む Jinja2 テンプレート
```

## 前提

- Python 3.12 以上
- [uv](https://docs.astral.sh/uv/) (パッケージ管理)
- [microsandbox](https://microsandbox.dev/) (ローカルで microVM を提供するサーバ)
- OpenAI API キー

## セットアップ

### 1. microsandbox CLI のインストール

microsandbox 本体 (CLI) は別途インストールが必要です。Python SDK は内部でこの `msb` バイナリを直接呼び出すため、**常駐サーバの起動は不要** です (v0.5.x 系で挙動が変わっています)。

```bash
curl -sSL https://get.microsandbox.dev | sh

# インストーラがシェル設定 (~/.bashrc など) に PATH を追記するため、再ログインまたは:
source ~/.bashrc

# 動作確認
msb --version
```

初回 `msb run` / Python SDK 初回実行時に Python の microVM イメージが自動でプルされます (数百MB、数分かかることがあります)。事前にプルしておく場合は:

```bash
msb pull python
```

> ダウンロードが `Failed to download ...tar.gz` で落ちる場合は GitHub Releases CDN への一時的な接続エラーです。リトライするか、リリースページから tarball を手動取得して `~/.microsandbox` に展開してください。

### 2. Python 依存関係のインストール

```bash
cd agent_sandbox
uv sync
```

開発用ツール (mypy / ruff / pytest など) も入れる場合:

```bash
uv sync --extra dev
```

### 3. 環境変数

`agent_sandbox/.env` に OpenAI API キーを記載します。

```env
OPENAI_API_KEY=sk-...
```

## 動かし方

すべて `agent_sandbox` ディレクトリ直下から実行します。

### microsandbox の疎通確認

microVM 上で `print('Hello from microVM')` を実行する最小サンプル。

```bash
uv run python scripts/sandbox.py
```

### OpenAI + microsandbox の連携

OpenAI (`gpt-4o-mini`) にフィボナッチ数列を出力するコードを生成させ、microVM 上で実行して結果を表示します。

```bash
uv run python scripts/openai_sandbox.py
```

実行されると以下のような出力になります。

- `生成されたコード:` … LLM が返した Python コード
- `実行結果:` … サンドボックスでの標準出力

### Jinja2 テンプレートの動作確認

```bash
uv run python scripts/jinja_template.py
```

### CSV を要約するプロンプト生成

`data/sample.csv` を `pandas` で読み込み、`scripts/describe_dataframe.jinja` を使ってデータ要約プロンプトを構築します。

```bash
uv run python scripts/describe_dataframe.py
```

## サンドボックスの管理

`msb` v0.5.x には常駐サーバ/デーモンは存在せず、「msb 自体の再起動」は不要です。`stop` / `start` などは個別の sandbox に対する操作になります。

### 一覧 / 状態確認

```bash
msb list             # 全 sandbox を一覧 (alias: msb ls)
msb list --running   # 起動中のみ
msb list --stopped   # 停止中のみ
msb status           # 起動中の状態 (alias: msb ps)
msb status -a        # 停止中も含めて表示
```

### 停止 / 起動 / 再起動

`restart` サブコマンドは存在しないため、停止→起動を順に実行します。

```bash
msb stop <name> [<name> ...]   # 通常停止 (graceful)
msb stop -f <name>             # 即時 kill
msb start <name>               # 停止中の sandbox を起動

# 「再起動」したい場合
msb stop <name> && msb start <name>
```

スクリプト経由 (Python SDK) の場合は、`Sandbox.create(..., replace=True)` が「既存があれば置き換える」挙動になっており、`scripts/sandbox.py` / `scripts/openai_sandbox.py` ではこの形を採用しています。

### 削除

`stop_and_wait()` 後も sandbox の登録は残ります。ディスクや一覧をクリーンに保ちたい場合は `remove` で消します。

```bash
msb remove <name>              # 停止中の sandbox を削除 (alias: msb rm)
msb remove -f <name>           # 起動中でも強制停止して削除
msb remove $(msb list -q)      # 全件削除 (--all は無いので list と組み合わせる)
```

### 一括操作のヒント

`stop` / `remove` には `--all` フラグはありませんが、以下で代替できます。

- 名前を列挙: `msb stop name1 name2 name3`
- ラベルでフィルタ: `msb stop --label key=value` (sandbox 作成時にラベルを付けている場合)
- 一覧から流し込み: `msb stop $(msb list --running -q)`

## トラブルシュート

- **`MicrosandboxError: ... Migration file of version 'mYYYYMMDD_*' is missing`**: 過去に新しめの `msb` ビルドが作成した state DB を、いま入っている `msb` がマイグレーション不一致で読めない状態です。`msb` には reset コマンドが無いため、state DB を退避して再生成させます (永続 sandbox は失われますが、本リポジトリのスクリプトは毎回 `replace=True` で作り直すため影響なし)。キャッシュ済みイメージのメタデータも消えるため、次回 `Sandbox.create()` で `python` イメージが再プルされる可能性があります。
  ```bash
  mv ~/.microsandbox/db/msb.db ~/.microsandbox/db/msb.db.bak.$(date +%Y%m%d%H%M%S)
  ```
- **`msb: command not found`**: インストーラが書き込んだ `export PATH="$HOME/.microsandbox/bin:$PATH"` が読み込まれていません。新しいターミナルを開くか `source ~/.bashrc` してください。
- **`msb server start` で `unrecognized subcommand`**: v0.5.x にサーバサブコマンドはありません (常駐不要)。そのまま Python SDK / `msb run` を実行してください。
- **初回実行が異常に遅い / 進まない**: Python の microVM イメージ (数百MB) を初回プル中です。`msb pull python` を先に実行して状況を確認してください。
- **`OPENAI_API_KEY` が未設定エラー**: `agent_sandbox/.env` が存在し、`uv run` を `agent_sandbox` ディレクトリで実行しているか確認してください。
- **`ModuleNotFoundError: src...`**: `scripts/` 配下のスクリプトは `agent_sandbox` をカレントディレクトリにして実行する前提です。`uv run python scripts/xxx.py` のように実行してください。
