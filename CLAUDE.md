# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> リポジトリの目的・3 層構造・install フロー・検証コマンドの**説明**は [README.md](README.md) が正本。本ファイルはそれを重複させず、**編集時に Claude が守る規則**だけを置く。構造や install 手順を知りたいときは README を読むこと。

## 不変条件 (変更時に必ず守る)

1. **`marketplace.json` の `name`/`owner`/`plugins[]` は必須**
2. **`plugins[].source` は plugin ディレクトリへの相対 path** (例: `./plugins/mermaid`)
3. **`plugin.json` の `name` は plugin namespace** になる (`/mermaid:mermaid-diagram` の前半)
4. **skill 実体は `plugins/<plugin>/skills/<skill>/` が canonical**。`.agents/skills/<skill>` は **relative symlink** (`../../skills/<skill>`)
5. **`AGENTS.md` を SKILL.md への symlink にしない** (agents.md 規格は plain markdown 要求、frontmatter と衝突)
6. **`plugin.json` に `"skills": "./skills/"` のようなデフォルト位置の冗長指定をしない**

## 命名関係 (これらは常に一致させる)

- **repo 名**: `mermaid-plugin`
- **marketplace.name**: `mermaid-plugin` (repo 名と同じ)
- **plugin.name**: `mermaid` (marketplace.json の `plugins[0].name` と一致)
- **skill ディレクトリ名**: `mermaid-diagram` / `mermaid-lint` (各 SKILL.md frontmatter の `name` と一致)
- **install 後の slash command**: `/mermaid:mermaid-diagram` / `/mermaid:mermaid-lint`

いずれかを変えるときは連動する全箇所を同時に更新すること。

## 2 つの skill の責務分担

- **`mermaid-diagram`**: ルールの知識ベース。根拠と公式 docs へのリンクを持つ
- **`mermaid-lint`**: 静的検査。ルールの説明は持たず、判定だけを行う

**ルールを両方に書かない。** `mermaid-lint` にルールの解説を足したくなったら、
`mermaid-diagram` 側に書いて lint からは参照に留める。二重管理すると片方が陳腐化する。

逆に、lint が仕様上正しい書き方を落とすなら、それは誤検出として lint 側を直す。
実例: 行末 `%%` コメントは flowchart では parse error だが、state diagram の公式仕様は
文末コメントを許している。`mermaid-diagram` の Rule 8 は「種別問わず専用行が安全」と
助言しているが、`mermaid-lint` は flowchart でのみ NG にしている。

## 同梱スクリプトのパス参照

`${CLAUDE_SKILL_DIR}` を使う。plugin skill では skill 自身のサブディレクトリ (plugin root ではない) に
解決され、**SKILL.md 本文と `allowed-tools` の Bash ルールの両方**で置換される。
同じ文字列を両方に書けば許可プロンプトなしで実行できる (Claude Code v2.1.129 以降)。

`${CLAUDE_PLUGIN_ROOT}` は skill 本文では展開されるが、`allowed-tools` での置換は公式に明記がない。
同梱スクリプトを呼ぶ用途では `${CLAUDE_SKILL_DIR}` を使うこと。
なお `CLAUDE_PLUGIN_DIR` という変数は存在しない。

スクリプトは `chmod +x` して shebang を付ける。依存は標準ライブラリのみに保つ
(利用者の環境に何が入っているか制御できないため)。

## SKILL.md を編集する際の注意

`plugins/mermaid/skills/mermaid-diagram/SKILL.md` 自身が mermaid 図の正しい書き方を扱うので、自己言及の罠がある:

- SKILL.md 内で mermaid サンプルを書くなら、SKILL.md 自身が説いているルール（ダブルクォート escape、flowchart の素の ID に Letter 以外の非 ASCII 文字を使わない、`%%` 専用行など）を守る
- **Broken 例は ` ```mermaid ` ではなく ` ```text ` ブロックに入れる**。GitHub renderer で本文書自体が parse error になるのを防ぐ
- 例の改訂時は GitHub レンダラーでの表示も確認する (README は GitHub で表示されるため特に)

## バージョン管理

- `plugin.json` の `version` を上げると Claude Code 側で更新通知される
- `marketplace.json` の `plugins[].version` は plugin.json の値が優先される ("plugin.json wins silently")
- `version` を省略すると git commit SHA が版番として使われる
- 現状 `0.2.2`。SKILL.md の実質改訂時にバンプする運用

## 仕様変更前の再確認

仕様変更があると配布形態に直接影響する。`marketplace.json` / `plugin.json` / レイアウトを大きく変える前に、該当する一次情報を WebFetch で再確認すること。

| 領域 | 一次情報 URL |
|---|---|
| Claude Code plugin manifest | https://code.claude.com/docs/en/plugins-reference |
| Claude Code plugin marketplaces | https://code.claude.com/docs/en/plugin-marketplaces |
| Discover and install plugins | https://code.claude.com/docs/en/discover-plugins |
| Claude Code plugins overview | https://code.claude.com/docs/en/plugins |
| Codex Skills (.agents/skills/) | https://developers.openai.com/codex/skills |
| AGENTS.md 規格 | https://agents.md/ |
| mermaid 公式 | https://mermaid.js.org/ |

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
