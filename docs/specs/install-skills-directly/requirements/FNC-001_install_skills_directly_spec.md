---
type: temporary-feature-requirement
notes:
  - この文書が正。旧仕様（ソースコード・設計書・計画書）と矛盾する場合はこの文書を優先して判断・実装すること。
  - 旧仕様ファイルは本 feature 実装完了まで書き換えない。新規ファイル / 新規ディレクトリとして切り出すこと。
  - 本 feature 実装完了後、この文書は旧仕様書へ merge され削除される予定。
---

# FNC-001 install-skills-directly 要件定義書

## メタデータ

| 項目     | 値      |
| -------- | ------- |
| 要件 ID  | FNC-001 |
| 関連要件 | (なし)  |
| 優先度   | 60      |

## 概要

**動機**: security policy で Claude Code の plugin install (`/plugin marketplace add` + `/plugin install`) が禁止された project でも、本リポジトリで配布する `mermaid-diagram` skill を vendoring 形式で利用したい。Codex CLI には汎用 install CLI がそもそも存在しないため、Codex 側も skill ファイル配置の手動操作を自動化する手段が欲しい。

**対象ユーザー**: security-restricted environment で本 plugin を使いたい開発者・チーム。

## 前提条件

- bash 互換 shell が動作する環境 (macOS / Linux / WSL)
- 本リポジトリが clone 済みで script を実行できる
- target project (または `~/`) に書き込み権限がある
- network 接続は不要

## 要件一覧

### 達成手段

skill を `.claude/skills/<name>/` (Claude Code 用) または `.agents/skills/<name>/` (Codex CLI 用) に直接配置する 2 つの bash script を提供する。配置先は target project (project-local) または user の home (user-global) の 2 種類から選択できる。

### 提供物

リポジトリルートに 2 つの script を追加する:

| script            | 配置先 path                                 |
| ----------------- | ------------------------------------------- |
| `setup-claude.sh` | `<project>/.claude/skills/mermaid-diagram/` |
| `setup-codex.sh`  | `<project>/.agents/skills/mermaid-diagram/` |

それぞれ `--global` 指定で user-global location (`~/.claude/skills/` / `~/.agents/skills/`) にも配置できる。

### 操作要件: `setup-claude.sh`

```
setup-claude.sh PROJECT_DIR [--force] [--dry-run] [--uninstall]
setup-claude.sh --global    [--force] [--dry-run] [--uninstall]
```

| 引数          | 動作                                                                                                |
| ------------- | --------------------------------------------------------------------------------------------------- |
| `PROJECT_DIR` | `PROJECT_DIR/.claude/skills/mermaid-diagram/` に本リポジトリの skill ファイル一式を **copy** で配置 |
| `--global`    | `~/.claude/skills/mermaid-diagram/` に copy で配置 (`PROJECT_DIR` と排他)                           |
| `--force`     | 既存ファイルがあれば上書き                                                                          |
| `--dry-run`   | 実際の変更なし。操作内容を `DRY-RUN:` プレフィックス付きで stdout に出力                            |
| `--uninstall` | 既存 install を削除 (`--force` 不要)                                                                |

### 操作要件: `setup-codex.sh`

```
setup-codex.sh PROJECT_DIR [--force] [--dry-run] [--uninstall]
setup-codex.sh --global    [--force] [--dry-run] [--uninstall]
```

`setup-claude.sh` と同形式。配置先のみ `.agents/skills/mermaid-diagram/` (project) または `~/.agents/skills/mermaid-diagram/` (global)。

### 出力要件

- 操作 1 件につき 1 行を stdout に出力 (`copied: <src> -> <dst>`、`skipped: <path>`、`removed: <path>` など)
- error は stderr に出力、終了 status は非ゼロ
- `--dry-run` 時は全アクション行に `DRY-RUN:` プレフィックスを付け、実ファイルは触らない
- 正常終了時、最後に配置済みの絶対パスを 1 行表示する (ユーザーが install 先を確認できる)

### エラーケース

| 条件                                                  | exit code | メッセージ                                                              |
| ----------------------------------------------------- | --------- | ----------------------------------------------------------------------- |
| `PROJECT_DIR` が存在しない                            | 1         | `error: PROJECT_DIR does not exist: <path>`                             |
| 配置先に書き込み権限がない                            | 1         | `error: cannot write to <path>`                                         |
| `PROJECT_DIR` と `--global` を同時指定                | 2         | `error: PROJECT_DIR and --global are mutually exclusive`                |
| 既存 install があり `--force` も `--uninstall` もない | 1         | `error: <path> already exists. Use --force to overwrite or --uninstall` |
| `--uninstall` 指定で対象が存在しない                  | 0         | `warning: nothing to uninstall at <path>`                               |
| 未知のフラグ / 引数組合せ不正                         | 2         | usage を stderr に表示                                                  |

### 非機能要件

| カテゴリ     | 要件                                                                                                                                     |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 通信         | network 通信を一切行わない (offline / air-gapped 環境対応)                                                                               |
| 副作用範囲   | `<PROJECT_DIR>/.claude/`, `<PROJECT_DIR>/.agents/`, `~/.claude/skills/`, `~/.agents/skills/` の **配置先サブツリー以外は mutate しない** |
| 冪等性       | `--force` 付きで複数回実行しても同じ結果になる                                                                                           |
| OS 対応      | macOS / Linux / WSL を正式サポート。Windows ネイティブ (PowerShell) は非対応 (README で WSL / Git Bash 推奨を明記する)                   |
| 依存最小化   | bash と POSIX 互換ユーティリティのみに依存。ruby / python / node 等の追加 runtime を要求しない                                           |
| セキュリティ | sudo / root 権限を要求しない。target 外のファイルを読み書きしない                                                                        |

### 用語

| 用語                  | 定義                                                                                                                                                     |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| project-local install | target project の `.claude/skills/<name>/` または `.agents/skills/<name>/` に skill を配置すること。project に commit され、project 単位で利用可能になる |
| user-global install   | `~/.claude/skills/<name>/` または `~/.agents/skills/<name>/` に skill を配置すること。当該 OS user のすべての project で利用可能になる                   |
| vendor (動詞)         | 外部から取得した資産を自プロジェクト内に取り込み、自前管理下に置くこと。本要件では「skill ファイルを target project にコピーする」ことを指す             |

## 未確定事項

| ID      | 内容                                                                                                                                             | 期限       |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------ | ---------- |
| TBD-001 | 配置先に既存ファイル / symlink が存在する状態で `--force` 上書きを実行したあと、最終状態はユーザーから見てどうあるべきか (新規 install と同等か) | 設計開始前 |

## 変更履歴

| 日付       | 変更者  | 内容                                                                                                                                                       |
| ---------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-23 | k2moons | 初版作成                                                                                                                                                   |
| 2026-05-23 | k2moons | /forge:review 由来の minor 指摘 4 件を反映 (メタデータ「機能名」削除 / TBD-001 を What 表現に / 依存最小化のコマンド列挙簡略化 / 概要と達成手段の重複削減) |
