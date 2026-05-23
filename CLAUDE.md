# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

このリポジトリは「実行可能なコード」を持たない **配布パッケージ** である。Claude Code の **plugin marketplace** + OpenAI Codex CLI Skill の両規格に同時準拠して、単一スキル `mermaid-diagram` を 1 つの Git リポジトリで配布する。

成果物の実体は 2 ファイル: `plugins/mermaid/skills/mermaid-diagram/SKILL.md`（本体）と `common-errors.md`（リファレンス）。これらが mermaid 図作成時の暗黙ルールと renderer 固有の罠（特に GitHub の `btoa` Latin-1 エラー）をまとめている。

## 3 層構造の意図 (重要)

```
mermaid-plugin/                               # Layer 1: marketplace (リポジトリ)
├── .claude-plugin/
│   └── marketplace.json                      # marketplace catalog
└── plugins/
    └── mermaid/                              # Layer 2: plugin
        ├── .claude-plugin/
        │   └── plugin.json                   # plugin manifest
        ├── skills/                           # Layer 3 (canonical): skill 本体
        │   └── mermaid-diagram/
        │       ├── SKILL.md
        │       └── common-errors.md
        └── .agents/                          # Layer 3 (Codex 用 symlink)
            └── skills/
                └── mermaid-diagram → ../../skills/mermaid-diagram
```

### Layer の責務

| Layer | 役割 | 必須ファイル |
|---|---|---|
| 1: marketplace | catalog として複数 plugin をリスト | `.claude-plugin/marketplace.json` (root) |
| 2: plugin | 個別 plugin の manifest | `plugins/<plugin>/.claude-plugin/plugin.json` |
| 3: skill | skill の実体 | `plugins/<plugin>/skills/<skill>/SKILL.md` |

このリポジトリは plugin が 1 個 (`mermaid`) しかないが、`plugins/` 配下に追加することで marketplace として 2 個目以降を拡張可能。

### 不変条件 (変更時に必ず守る)

1. **`marketplace.json` の `name`/`owner`/`plugins[]` は必須**
2. **`plugins[].source` は plugin ディレクトリへの相対 path** (例: `./plugins/mermaid`)
3. **`plugin.json` の `name` は plugin namespace** になる (`/mermaid:mermaid-diagram` の前半)
4. **skill 実体は `plugins/<plugin>/skills/<skill>/` が canonical**。`.agents/skills/<skill>` は **relative symlink**
5. **`AGENTS.md` を SKILL.md への symlink にしない** (agents.md 規格は plain markdown 要求、frontmatter と衝突)
6. **`plugin.json` に `"skills": "./skills/"` のようなデフォルト位置の冗長指定をしない**

### 命名関係

- **repo 名**: `mermaid-plugin`
- **marketplace.name**: `mermaid-plugin` (repo 名と同じ)
- **plugin.name**: `mermaid` (marketplace.json の `plugins[0].name` と一致)
- **skill ディレクトリ名**: `mermaid-diagram` (SKILL.md frontmatter の `name` と一致)
- **install 後の slash command**: `/mermaid:mermaid-diagram`

## 仕様の出典

仕様変更があると配布形態に直接影響するため、`marketplace.json` / `plugin.json` / レイアウトを大きく変える前にこれらを WebFetch で再確認すること。

| 領域 | 一次情報 URL |
|---|---|
| Claude Code plugin manifest | https://code.claude.com/docs/en/plugins-reference |
| Claude Code plugin marketplaces | https://code.claude.com/docs/en/plugin-marketplaces |
| Discover and install plugins | https://code.claude.com/docs/en/discover-plugins |
| Claude Code plugins overview | https://code.claude.com/docs/en/plugins |
| Codex Skills (.agents/skills/) | https://developers.openai.com/codex/skills |
| AGENTS.md 規格 | https://agents.md/ |
| mermaid 公式 | https://mermaid.js.org/ |

## Validation commands

このリポジトリには test/build はない。代わりに以下:

```bash
# marketplace 全体 (root から)
claude plugin validate . --strict

# 個別 plugin
claude plugin validate ./plugins/mermaid --strict

# ローカルで plugin だけロードして試用
claude --plugin-dir ./plugins/mermaid

# symlink 解決確認
readlink plugins/mermaid/.agents/skills/mermaid-diagram
# 期待: ../../skills/mermaid-diagram

# JSON 構文確認
python3 -c "import json; json.load(open('.claude-plugin/marketplace.json'))"
python3 -c "import json; json.load(open('plugins/mermaid/.claude-plugin/plugin.json'))"
```

## SKILL.md を編集する際の注意

`plugins/mermaid/skills/mermaid-diagram/SKILL.md` 自身が mermaid 図の正しい書き方を扱うので、自己言及の罠がある:

- SKILL.md 内で mermaid サンプルを書くなら、SKILL.md 自身が説いているルール（ダブルクォート escape、`btoa` 対策、`%%` 専用行など）を守る
- **Broken 例は ` ```mermaid ` ではなく ` ```text ` ブロックに入れる**。GitHub renderer で本文書自体が parse error になるのを防ぐ
- 例の改訂時は GitHub レンダラーでの表示も確認する (README は GitHub で表示されるため特に)

## バージョン管理

- `plugin.json` の `version` を上げると Claude Code 側で更新通知される
- `marketplace.json` の `plugins[].version` は plugin.json の値が優先される ("plugin.json wins silently")
- `version` を省略すると git commit SHA が版番として使われる
- 現状 `0.1.0`。SKILL.md の実質改訂時にバンプする運用

## install フロー (動作確認用)

ユーザー視点では:

```bash
/plugin marketplace add k2moons/mermaid-plugin
/plugin install mermaid@mermaid-plugin
/reload-plugins
# 利用: /mermaid:mermaid-diagram
```

`/plugin install <github-url>` のような直接 URL 指定は **存在しない**。必ず marketplace を経由する。

## このリポジトリでよく使う user skills

ユーザー環境 (`~/.claude/skills/`) に登録されており、本リポジトリの保守作業中に発動しうる:

- **plugin-creator**: 「Claude Code + Codex 両対応プラグインを作る」知識ベース。本リポジトリはこの skill が説く手順で構築されている
- **update-plugin-creator**: 実プロジェクトで得た学びを plugin-creator に反映する meta skill
- **skill-creator**: 個別 skill (SKILL.md 単体) の設計を扱う
- **update-skill-creator**: 同上の meta skill

本リポジトリで pitfall や spec 変更に遭遇したら、いずれかの update-* skill 経由でグローバル側に還元する。

## .gitignore に注意

`.claude/` 配下はローカル開発用 (user skills のコピー、settings、temp 等) で `.gitignore` 除外。コミット対象は:

- `.claude-plugin/`
- `plugins/`
- `README.md` / `LICENSE` / `.gitignore` / `CLAUDE.md`

意図せず `.claude/` 配下を `git add` しない。
