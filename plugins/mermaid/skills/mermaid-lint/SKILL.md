---
name: mermaid-lint
description: |
  Mermaid 図を静的検査する。lowercase `end`、flowchart の行末 `%%` コメント、circle/cross edge の誤解釈、flowchart / classDiagram での Note 使用、flowchart の素の識別子に絵文字・矢印・数学記号等の Unicode 記号を使うことによる lexical error を機械判定する。Markdown 内の ```mermaid ブロックを抽出して検査でき、標準入力にも対応する。Use when mermaid 図を書き終えて検証したいとき、CI やスクリプトから mermaid をチェックしたいとき。
allowed-tools: Bash(${CLAUDE_SKILL_DIR}/scripts/lint_mermaid.py *)
---

# Mermaid Lint

`mermaid-diagram` Skill が説くルールのうち、**機械判定できるものだけ**を検査する。
ルールの根拠・書き方・公式 docs へのリンクは `mermaid-diagram` 側を正とする。
本 Skill は判定だけを担い、ルールを二重に持たない。

## 実行

```bash
${CLAUDE_SKILL_DIR}/scripts/lint_mermaid.py <FILE>...
```

Markdown なら ` ```mermaid ` ブロックを抽出して検査する。`.mmd` などはファイル全体を 1 つの図として扱う。

文書の一部だけを検査したいときは標準入力を使う。

```bash
sed -n '40,80p' design.md | ${CLAUDE_SKILL_DIR}/scripts/lint_mermaid.py -
```

既存の図に手を入れられない文書で、**自分が書き足した箇所だけ**を検査したい場合にこれを使う。
ファイル全体を渡すと既存分の NG まで拾ってしまう。

`--format markdown|mermaid` で判定を固定できる。既定の `auto` は ` ```mermaid ` の有無で決める。

## 判定

NG が 1 件でもあれば終了コード 1。WARN だけなら 0。

| 判定 | 意味 |
| ---- | ---- |
| NG | 構文が壊れる |
| WARN | 意図次第で正しい場合がある |

### 検査項目

| check | 判定 | 内容 |
| ---- | ---- | ---- |
| `lexical` | NG | flowchart の素のノード ID に絵文字・矢印・数学記号等 (Unicode Symbol カテゴリ) の文字。ID ではなくラベルにする |
| `end` | NG | ノード ID に lowercase `end`。`subgraph` 終端と衝突する |
| `comment` | NG | flowchart の行末 `%%` コメント |
| `note` | NG | flowchart / classDiagram での `Note` キーワード |
| `fence` | NG | Markdown のコードフェンスが閉じていない |
| `ox-edge` | WARN | `A---oBar` が circle/cross edge と解釈される |

**日本語・CJK ラベル/識別子の未クォートは検査しない。** GitHub 上での btoa Latin-1
エラーという既知の問題があったが、`fixtures/github_render_verification.md` での
実地検証 (2026-07) の結果、いずれの位置（ノードラベル・subgraph タイトル・エッジ/
パイプラベル・素のノード ID・stateDiagram の状態 ID/遷移ラベル）でも再現しなかった。

flowchart の `lexical` チェックは Unicode の一般カテゴリで判定する。**Letter カテゴリ
(Lo/Lm/Lu/Ll/Lt。CJK 統合漢字・ひらがな・カタカナ等) は素の識別子でも安全**、
**Symbol カテゴリ (Sm/So/Sc/Sk。絵文字・矢印・数学記号等) は素の識別子で lexical error
になる**ことを同じ検証で確認済み。絵文字（サロゲートペア文字）に限らず Symbol
カテゴリ全般が対象。

**この制約を stateDiagram-v2 に適用してはいけない。** mermaid 11.16.0 の
`mermaid.render()` と GitHub 上の実地検証 (2026-08) では、Symbol・句読点・数字・全角空白を
含む素の状態 ID も描画できる。diagram 種別で lexer が異なるため、flowchart から
stateDiagram-v2 へ一般化すると誤検出になる。

### 図種別で判定を変えている箇所

**行末 `%%` コメントは flowchart でのみ NG。** state diagram の公式仕様は
「コメントは専用行でも文末でもよい」と明記しているため、そちらでは咎めない。
`mermaid-diagram` Skill の Rule 8 は「種別問わず専用行に倒すのが安全」と助言しているが、
lint が仕様上正しい書き方を落とすのは誤検出なので、判定は仕様に合わせている。

## この検査の限界

**mermaid パーサーを使っていない。** 標準ライブラリだけの正規表現検査なので、
構文エラーを網羅しない。通っても壊れている図はありうる。

**描画の最終確認は https://mermaid.live/ で行う。** GitHub に貼る図は
PR プレビューでも rich display エラーが出ないか確認する。

検査を通すことは必要条件であって十分条件ではない。

## 関連

- `mermaid-diagram` — ルールの根拠、公式 docs へのリンク、Broken / Fixed の実例
- `fixtures/fixture.md` — 各検査が発火することを確認するためのフィクスチャ。保守用
- `fixtures/github_render_verification.md` — GitHub 上での実地レンダリング検証用フィクスチャ。
  btoa 系の疑わしい挙動を見かけたら、ここにケースを足して github.com 上で再現・切り分ける
