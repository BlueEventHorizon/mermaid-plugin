# GitHub レンダリング実地検証用フィクスチャ

`mermaid-lint` の btoa 系ルールのうち、根拠が推測ベースだったものを実地検証するための資料。

**使い方**: このファイルを GitHub.com 上で直接開き（`https://github.com/<org>/<repo>/blob/<branch>/plugins/mermaid/skills/mermaid-lint/fixtures/github_render_verification.md`）、各セクションの図が「Unable to render rich display」エラーなく描画されるかを目視確認する。

**確認済み（ラウンド1、2026-07）**: いずれも未クォートで問題なし。

- flowchart の素の非 ASCII ノード ID（`未読 --> 既読`）
- flowchart の素の非 ASCII subgraph ID（`subgraph App層`）
- stateDiagram-v2 の素の非 ASCII 状態 ID
- stateDiagram-v2 の非 ASCII 遷移ラベル
- flowchart のドット付きリンクの未クォート CJK ラベル（`-. text .->`）
- flowchart の未クォート CJK ノードラベル（`[...]` 内）・パイプラベル（`|...|`）
- クォート済みの数学記号ラベル（mermaid-js issue #4050 の再現、`∘` は Latin-1 範囲外）

**確認済み・唯一の実在問題（ラウンド1、2026-07）**: 絵文字（サロゲートペア文字）を素のノード ID に使うと `Lexical error` になる（`btoa` エラーではない）。`lint_mermaid.py` の `lexical` チェックはこれに対応する。

**今回検証する項目（ラウンド2）**: ラウンド1で未検証だった、絵文字関連の他パターンと、CJK/絵文字以外の Unicode 記号を検証する。

## 1. flowchart: 絵文字を含む素の subgraph ID

```mermaid
flowchart TD
    subgraph 🎉Party
        Foo --> Bar
    end
```

## 2. stateDiagram-v2: 絵文字を含む遷移ラベル

```mermaid
stateDiagram-v2
    state "A" as S1
    state "B" as S2
    S1 --> S2 : 🎉開封する
```

## 3. flowchart: 素の識別子に使った矢印記号（CJK でも絵文字でもない Unicode 記号、BMP 内）

```mermaid
flowchart TD
    A→B --> C
```

## 4. flowchart: 素の識別子に使った数学記号（issue #4050 のトリガー文字、BMP 内・未クォート）

```mermaid
flowchart TD
    f∘g --> C
```

## 5. 比較用: 絵文字を含む subgraph タイトルをクォートした場合（問題ない想定）

```mermaid
flowchart TD
    subgraph SG["🎉Party"]
        Foo --> Bar
    end
```
