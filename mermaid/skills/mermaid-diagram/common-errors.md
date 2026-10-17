# mermaid: 実例ベースのエラーパターン集

[SKILL.md](SKILL.md) を読んだうえで、症状から逆引きしたいときに使う。本書のすべての例は汎用プレースホルダ (`Foo` / `Bar` / `Hoge`) を使い、特定プロジェクト固有の用語は使わない。

> **MUST**: 各エラーを直す前に [SKILL.md](SKILL.md) の Critical Rules と公式 docs (`mermaid.js.org`) を確認すること。本書は補助資料であり、公式仕様の代替ではない。

---

## 1. ラベル内特殊文字

### 1.1 コロン `:` を含むラベル

**症状**: `Parse error on line X`

**Broken**:

```text
flowchart LR
    A[Method: process]
```

**Fixed (Option A: ダブルクォート)**:

```mermaid
flowchart LR
    A["Method: process"]
```

**Fixed (Option B: HTML entity)**:

```mermaid
flowchart LR
    A[Method&#58; process]
```

公式: https://mermaid.js.org/syntax/flowchart.html#entity-codes-to-escape-characters

### 1.2 角括弧 `[]` を含むラベル

**Broken**:

```text
flowchart LR
    A[Array [1, 2, 3]]
```

シェイプ delimiter と衝突する。

**Fixed**:

```mermaid
flowchart LR
    A["Array [1, 2, 3]"]
```

### 1.3 丸括弧 `()` を含むラベル

**Broken**:

```text
flowchart LR
    A[method(arg)]
```

**Fixed**:

```mermaid
flowchart LR
    A["method(arg)"]
```

### 1.4 ダブルクォート内のダブルクォート

**Broken**:

```text
flowchart LR
    A["Say "Hi""]
```

**Fixed**:

```mermaid
flowchart LR
    A["Say &quot;Hi&quot;"]
    B[Say &#34;Hi&#34;]
```

---

## 2. 予約語

### 2.1 lowercase `end` の使用

**Broken**:

```text
flowchart TD
    Start --> end
```

`end` は subgraph 終端と衝突。

**Fixed**:

```mermaid
flowchart TD
    Start --> End
```

公式: https://mermaid.js.org/syntax/flowchart.html#word-end

---

## 3. edge 開始位置の `o` / `x`

**Broken**:

```text
flowchart LR
    A---oBar
```

`A o-- Bar` (circle edge) と誤解釈される。

**Fixed (スペースを挟む)**:

```mermaid
flowchart LR
    A--- oBar
```

**Fixed (別頭文字)**:

```mermaid
flowchart LR
    A--- Item
```

公式: https://mermaid.js.org/syntax/flowchart.html#unexpected-circle-or-cross-arrows

---

## 4. subgraph

### 4.1 ID は必須ではない (注意: 過去の誤解説の訂正)

`subgraph "Title"` は **valid な構文** (公式: https://mermaid.js.org/syntax/flowchart.html#subgraphs)。

```mermaid
flowchart TD
    subgraph "Group A"
        Foo
        Bar
    end
```

これは問題ない。「subgraph には必ず ID を付けろ」は古い誤った言説。

### 4.2 subgraph に edge を引く場合は ID が必要

**Broken** (subgraph に edge を引きたいのに ID なし):

```text
flowchart TD
    subgraph "Group A"
        Foo
    end

    OtherNode --> Group A    %% スペースを含むため認識されない
```

**Fixed**:

```mermaid
flowchart TD
    subgraph GRP_A["Group A"]
        Foo
    end

    OtherNode --> GRP_A
```

---

## 5. `Note` keyword の誤用

### 5.1 flowchart での Note は不可

**Broken**:

```text
flowchart TD
    A[Foo]
    Note right of A: bad
```

**Fixed (通常ノード化)**:

```mermaid
flowchart TD
    A[Foo]
    N["Note: A は ..."]
    A -.-> N
```

### 5.2 sequenceDiagram / stateDiagram-v2 では可

```mermaid
sequenceDiagram
    participant A as Foo
    participant B as Bar
    A->>B: request
    Note right of B: handle here
```

```mermaid
stateDiagram-v2
    [*] --> S1
    note right of S1: 起動直後の状態
```

公式:

- sequenceDiagram: https://mermaid.js.org/syntax/sequenceDiagram.html#notes
- stateDiagram: https://mermaid.js.org/syntax/stateDiagram.html#comments

---

## 6. classDiagram

### 6.1 前方参照

**Broken** (関係を書く時点で class 未定義):

```text
classDiagram
    Foo <|-- Bar

    class Foo {
        +name
    }
```

**Fixed**:

```mermaid
classDiagram
    class Foo {
        +name
    }
    class Bar
    Foo <|-- Bar
```

### 6.2 method 戻り値の前のコロン

**Broken**:

```text
classDiagram
    class Foo {
        run(arg): Result
    }
```

**Fixed**:

```mermaid
classDiagram
    class Foo {
        run(arg) Result
    }
```

戻り値の前にコロンを書かない。属性は `name: Type` でコロン可。

公式: https://mermaid.js.org/syntax/classDiagram.html#defining-a-class

---

## 7. edge label の特殊文字

**Broken**:

```text
flowchart LR
    A -->|process()| B
```

**Fixed**:

```mermaid
flowchart LR
    A -->|"process()"| B
```

パイプ形 edge label `|...|` 内もダブルクォート可。

---

## 8. GitHub レンダラー: 非 ASCII 文字関連

### 8.1 CJK ラベル・識別子は基本的に問題ない [検証済み 2026-07]

過去のバージョンでは、日本語・中国語等の非 ASCII 文字を含むラベルで GitHub 上の mermaid 描画が `btoa()` の Latin-1 範囲エラーで失敗するという既知の問題が報告されていた:

```
Unable to render rich display
Failed to execute 'btoa' on 'Window': The string to be encoded contains characters outside of the Latin1 range.
```

`../mermaid-lint/fixtures/github_render_verification.md` を使って github.com 上で実地検証した結果 (2026-07)、ノードラベル・パイプラベル・ドット付きリンクラベル・素のノード ID・subgraph ID・stateDiagram の状態 ID / 遷移ラベルのいずれも、未クォートの CJK テキストでエラーは再現しなかった。GitHub 側か mermaid.js 側の改善で解消されている可能性が高い。ダブルクォートで囲む対処は無害だが必須ではない。

将来的にこのエラーを実際に見かけたら、`github_render_verification.md` で再現・切り分けたうえで本ドキュメントを更新すること。renderer のバージョンアップで再発しうる。

### 8.2 flowchart の素の識別子では非 ASCII の Letter 以外がエラー [検証済み 2026-08]

こちらは flowchart の実地検証で確認された実在の問題。**非 ASCII 文字のうち Unicode Letter
カテゴリ以外をクォートなしで node / subgraph ID に使うとエラーになる**。Symbol
(絵文字・矢印・数学記号) だけでなく、Punctuation (中黒・句読点・全角括弧)、Number
(全角数字)、Separator (全角空白) 等も対象。CJK や全角英字などの Letter カテゴリは問題ない:

**Broken** (絵文字):

```text
flowchart TD
    🎉Party --> End2
```

**Broken** (記号・句読点・全角数字):

```text
flowchart TD
    A→B --> C
    f∘g --> C
    未読・既読 --> C
    状態０ --> C
```

**エラー例**:

```
Unable to render rich display
Lexical error on line 2. Unrecognized text.
flowchart TD 🎉Party --> End2
```

**Fixed** (ラベルとしてクォートする、または ASCII ID にする):

```mermaid
flowchart TD
    A["🎉Party"] --> End2
```

判別は Python `unicodedata.category()` で確認できる。flowchart では Letter カテゴリ
(`Lo`/`Lm`/`Lu`/`Ll`/`Lt`。CJK・ひらがな・カタカナ・全角英字等) は素の ID でも安全。
それ以外の非 ASCII 文字はカテゴリを問わずエラーになる。全角空白だけは `Lexical error`
とは別のエラーだが、同様に素の ID には使えない。ラベルとしてクォートすれば問題ない。

**stateDiagram-v2 は別の文法であり、この制約の対象外。** Mermaid 11.16.0 と GitHub 上の
実地検証では、これら Letter 以外の文字を含む素の状態 ID も描画できた。遷移ラベルだけでなく
状態 ID 自体も使用可能。

---

## 9. ありがちな失敗パターン (上位 5 件)

実プロジェクトでの修正履歴ベース:

1. **特殊文字ノーガード**: コロン / 括弧をラベルに直書き → Rule 1 ダブルクォート
2. **Letter 以外の非 ASCII 文字を flowchart の素の ID に使用**: 記号・句読点・全角数字等が lexer で認識されない → §8.2 ラベルとしてクォート
3. **lowercase `end`**: ノード ID に `end` → `End` に rename
4. **subgraph ID 混乱**: 「ID を必ず付けろ」と思って必須化 → 「edge を引くときだけ必要」
5. **flowchart に Note 書く**: 通常ノードで代用

---

## 10. デバッグ戦略

エラー位置が分かりにくいときの定石:

1. **コメントアウトで二分探索**: 怪しいノード/エッジを `%%` でコメント化し、再 render
2. **シンプル化**: 全特殊文字を除き、最小構造で render → 通ったら incrementally に戻す
3. **ローカル実パーサで再現**（`mermaid-lint/docs/verification-methodology.md`、mermaid.live 等の外部サイトは使わない）: GitHub renderer の問題か mermaid 仕様の問題かを切り分け
4. **公式 docs を読む**: バージョンによる挙動差は公式の changelog で確認

---

## 参照

- [SKILL.md](SKILL.md) — Critical Rules と GitHub Caveats の本編
- 公式 docs: https://mermaid.js.org/
- GitHub mermaid サポート: https://docs.github.com/en/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams
