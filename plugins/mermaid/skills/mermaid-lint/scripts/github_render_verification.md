# GitHub レンダリング実地検証用フィクスチャ

`mermaid-lint` の btoa 系ルールのうち、根拠が推測ベースだったものを実地検証するための資料。

**使い方**: このファイルを GitHub.com 上で直接開き（`https://github.com/<org>/<repo>/blob/<branch>/plugins/mermaid/skills/mermaid-lint/scripts/github_render_verification.md`）、各セクションの図が「Unable to render rich display」エラーなく描画されるかを目視確認する。

**既に確認済み**（削除済みルールの根拠。参考として記録）:
- flowchart の未クォート CJK ノードラベル（`[...]` 内）→ 問題なし
- flowchart の未クォート CJK パイプラベル（`|...|`）→ 問題なし
- flowchart の未クォート CJK ドット付きリンクラベル（`-. text .->`）→ 未クォートラベル一般が問題ないなら同様に問題ないはず（要確認）

**今回検証する項目**:

## 1. flowchart: 素の非 ASCII ノード ID

```mermaid
flowchart TD
    未読 --> 既読
```

## 2. flowchart: 素の非 ASCII subgraph ID

```mermaid
flowchart TD
    subgraph App層
        Foo --> Bar
    end
```

## 3. stateDiagram-v2: 素の非 ASCII 状態 ID

```mermaid
stateDiagram-v2
    未読 --> 既読
```

## 4. stateDiagram-v2: 非 ASCII 遷移ラベル

```mermaid
stateDiagram-v2
    state "未読" as S1
    state "既読" as S2
    S1 --> S2 : 開封する
```

## 5. flowchart: ドット付きリンクの未クォート CJK ラベル（今回追加したルールの根拠確認）

```mermaid
flowchart LR
    A -. 開始確認 .-> B
```

## 6. flowchart: 絵文字を含む素のノード ID

```mermaid
flowchart TD
    🎉Party --> End2
```

## 7. flowchart: クォート済みの数学記号ラベル（mermaid-js issue #4050 の再現、`∘` は Latin-1 範囲外）

```mermaid
flowchart TB
    A["f ∘ g"]
```

## 8. 比較用: すべてクォート済み・delimiter 内ラベル（問題ない想定の対照群）

```mermaid
flowchart TD
    A["未読"] --> B["既読"]
    subgraph SG["App層"]
        C["Foo"]
    end
```
