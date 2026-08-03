# mermaid-plugin

Mermaid 図を書くときに AI が見落としがちな**暗黙ルール**と**主要 renderer 固有の制約**（Letter 以外の非 ASCII 文字を flowchart の素の ID に使った際のエラー等）を最小セットでまとめた Skill を、**Claude Code Plugin marketplace** と **OpenAI Codex CLI Skill** の両規格で配布する単独リポジトリ。

Skill は 2 つある。

| Skill             | 役割                                           |
| ----------------- | ---------------------------------------------- |
| `mermaid-diagram` | ルールの知識ベース。書く前に読む               |
| `mermaid-lint`    | 書いた図の静的検査。機械判定できる分だけを見る |

ルールの根拠は `mermaid-diagram` を正とし、`mermaid-lint` は判定だけを担う。二重管理を避けるため。

## 何を解決するか

- ✅ ラベル内特殊文字（`:` `()` `[]` `{}` `#` 等）の正しいエスケープ
- ✅ 予約語 `end` の誤用回避
- ✅ edge 開始位置の `o` / `x` による circle/cross 誤解釈
- ✅ subgraph ID の必要・不要の正しい判別
- ✅ `Note` / `note` が使える diagram 種別の整理
- ✅ classDiagram の前方参照・method 戻り値構文
- ✅ `%%` コメントは専用行のみ (行末コメントは parse error)
- ✅ Letter 以外の非 ASCII 文字（記号・句読点・全角数字・全角括弧等）を flowchart の素の ID に使うとエラーになる問題の回避

詳細は [`plugins/mermaid/skills/mermaid-diagram/SKILL.md`](plugins/mermaid/skills/mermaid-diagram/SKILL.md) と実例ベースのトラブルシュート集 [`common-errors.md`](plugins/mermaid/skills/mermaid-diagram/common-errors.md) を参照。

上のうち機械判定できるものは [`mermaid-lint`](plugins/mermaid/skills/mermaid-lint/SKILL.md) が検査する。
標準ライブラリのみの Python スクリプトで、Markdown 内の `` ```mermaid `` ブロックを抽出して検査する。
mermaid パーサーは使わないため構文エラーを網羅しない。描画の最終確認は <https://mermaid.live/> で行う。

## インストール

### Claude Code (推奨)

このリポジトリは Claude Code の **marketplace** として登録すると利用できる。

```bash
# 1. marketplace としてリポジトリを登録
/plugin marketplace add BlueEventHorizon/mermaid-plugin

# 2. mermaid plugin を install
/plugin install mermaid@mermaid-plugin

# 3. (必要なら) reload
/reload-plugins
```

利用時は plugin 名で namespace される:

```
/mermaid:mermaid-diagram
/mermaid:mermaid-lint
```

> 参考: [Discover and install plugins](https://code.claude.com/docs/en/discover-plugins) — `/plugin install <url>` のような直接 URL 指定はなく、`marketplace add` + `install` の 2 ステップが正規。

### Claude Code (ローカル開発用)

このリポジトリを直接 clone してロードする場合:

```bash
git clone https://github.com/BlueEventHorizon/mermaid-plugin ~/tools/mermaid-plugin
claude --plugin-dir ~/tools/mermaid-plugin/plugins/mermaid
```

### Codex CLI (OpenAI)

Codex CLI には marketplace 機構がない。`.agents/skills/` を proximity scan する仕様のため、symlink で配置する ([Codex Skills 公式 docs](https://developers.openai.com/codex/skills))。

```bash
# 1. リポジトリを任意の場所にクローン
git clone https://github.com/BlueEventHorizon/mermaid-plugin ~/tools/mermaid-plugin

# 2. プロジェクトの .agents/skills/ から symlink
mkdir -p .agents/skills
ln -s ~/tools/mermaid-plugin/plugins/mermaid/skills/mermaid-diagram .agents/skills/mermaid-diagram
ln -s ~/tools/mermaid-plugin/plugins/mermaid/skills/mermaid-lint .agents/skills/mermaid-lint
```

個人全プロジェクト用なら `~/.agents/skills/` 配下に symlink。

## リポジトリ構成

```
mermaid-plugin/                                  # repo = marketplace
├── .claude-plugin/
│   └── marketplace.json                         # marketplace catalog
├── plugins/
│   └── mermaid/                                 # 個別 plugin
│       ├── .claude-plugin/
│       │   └── plugin.json                      # plugin manifest
│       ├── skills/
│       │   ├── mermaid-diagram/                 # canonical skill location
│       │   │   ├── SKILL.md
│       │   │   └── common-errors.md
│       │   └── mermaid-lint/
│       │       ├── SKILL.md
│       │       ├── scripts/
│       │       │   └── lint_mermaid.py          # 標準ライブラリのみ
│       │       └── fixtures/
│       │           ├── fixture.md               # 検出テスト用（保守用）
│       │           └── github_render_verification.md
│       └── .agents/
│           └── skills/
│               ├── mermaid-diagram → ../../skills/mermaid-diagram   # Codex 互換 symlink
│               └── mermaid-lint → ../../skills/mermaid-lint
├── README.md
├── CLAUDE.md
├── LICENSE
└── .gitignore
```

階層意図:

- **リポジトリルート** = marketplace (catalog として `.claude-plugin/marketplace.json` を持つ)
- **`plugins/mermaid/`** = 個別の plugin (`.claude-plugin/plugin.json` を持つ)
- **`plugins/mermaid/skills/<skill>/`** = skill 本体 (実体)
- **`plugins/mermaid/.agents/skills/<skill>`** = 同一スキルへの Codex 用 symlink

skill に同梱したスクリプトは `${CLAUDE_SKILL_DIR}` で参照する。plugin skill では
skill 自身のサブディレクトリに解決され、SKILL.md 本文と `allowed-tools` の Bash ルールの
両方で置換されるため、許可プロンプトなしで実行できる（Claude Code v2.1.129 以降）。
`${CLAUDE_PLUGIN_ROOT}` は本文では展開されるが `allowed-tools` での置換は明記がない。

## 仕様準拠の確認

- ✅ **Claude Code Marketplace**: [Plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) の `.claude-plugin/marketplace.json` 必須フィールド (`name`, `owner`, `plugins[]`) を満たす
- ✅ **Claude Code Plugin**: [Plugins reference](https://code.claude.com/docs/en/plugins-reference) の `name` 必須を満たす
- ✅ **Codex Skill**: [Codex Skills](https://developers.openai.com/codex/skills) の `name` + `description` frontmatter 必須を満たす

ローカル検証:

```bash
# marketplace 全体の検証
claude plugin validate . --strict

# 個別 plugin の検証
claude plugin validate ./plugins/mermaid --strict

# symlink 解決
readlink plugins/mermaid/.agents/skills/mermaid-diagram
# 期待: ../../skills/mermaid-diagram

# lint の検出テスト（NG 8 件 / WARN 1 件、終了コード 1 になること）
plugins/mermaid/skills/mermaid-lint/scripts/lint_mermaid.py \
  plugins/mermaid/skills/mermaid-lint/fixtures/fixture.md

# lint の誤検出テスト（NG 0 件になること）
plugins/mermaid/skills/mermaid-lint/scripts/lint_mermaid.py \
  plugins/mermaid/skills/mermaid-diagram/SKILL.md \
  plugins/mermaid/skills/mermaid-diagram/common-errors.md
```

## 出典

このスキルは [bw-cc-plugins](https://github.com/BlueEventHorizon/bw-cc-plugins) 内で開発された `mermaid-diagram` skill を、単独 marketplace として配布可能な形に切り出したものである。

- 公式 mermaid docs: <https://mermaid.js.org/>
- GitHub の mermaid サポート: <https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams>
- Claude Code plugins: <https://code.claude.com/docs/en/plugins>
- Claude Code plugin marketplaces: <https://code.claude.com/docs/en/plugin-marketplaces>
- Claude Code plugins reference: <https://code.claude.com/docs/en/plugins-reference>
- Discover and install plugins: <https://code.claude.com/docs/en/discover-plugins>
- Codex Skills: <https://developers.openai.com/codex/skills>

## ライセンス

MIT — [LICENSE](LICENSE) を参照。
