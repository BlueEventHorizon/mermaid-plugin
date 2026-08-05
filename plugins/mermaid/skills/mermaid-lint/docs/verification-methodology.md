# mermaid 実地検証メソドロジー

`lint_mermaid.py` / `mermaid-diagram` のルールを追加・削除・修正するときに使う検証手順。
**想像や伝聞だけでルールを変えない。** 既存ルールは過去に実際のエラーを確認して追加されたものであり、
新しいルールも「実際に壊れる／壊れない」を再現してから反映する。

**mermaid.live 等、GitHub 以外の外部サイトに図を貼って検証しない。** 図の内容が社内情報を
含みうる以上、GitHub 以外への送信は情報漏洩になるため禁止。検証は下記 2 手段
（ローカル実パーサ / 既に push 済みの GitHub 上）だけで完結させる。

## 2 つの検証手段

判定したい対象によって使い分ける。混同すると、GitHub 固有の挙動を mermaid 一般の仕様と誤認したり、
その逆をしたりする。

### 1. 実パーサ（mermaid.render() + jsdom）— 一般的な構文・lexer 挙動の根拠

mermaid 本体は Node.js 上で `mermaid.render()` まで実行できる。DOM 依存（`getBBox()` 等）があるため
jsdom で最小限の DOM を用意する必要がある。バージョンを固定できるため再現性が高く、
文字カテゴリの網羅比較など**総当たりの検証はこちらを主に使う**。

セットアップ例:

```bash
mkdir -p /tmp/mermaid-verify && cd /tmp/mermaid-verify
npm init -y
npm install mermaid@11.16.0 jsdom
```

実行スクリプト例（`verify.mjs`）:

```javascript
import { JSDOM } from "jsdom";

const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
globalThis.window = dom.window;
globalThis.document = dom.window.document;
// mermaid の内部処理が getBBox 等を呼ぶため、jsdom 側にない実装を最低限埋める
SVGElement.prototype.getBBox = () => ({ x: 0, y: 0, width: 100, height: 20 });
SVGElement.prototype.getComputedTextLength = () => 50;

const { default: mermaid } = await import("mermaid");
mermaid.initialize({ startOnLoad: false });

const cases = [
  { name: "flowchart 素の ID に句読点", code: "flowchart TD\n    未読・既読 --> C" },
  // 検証したいパターンをここに列挙する
];

for (const c of cases) {
  try {
    await mermaid.render(`id-${c.name}`, c.code);
    console.log(`OK    ${c.name}`);
  } catch (e) {
    console.log(`ERROR ${c.name}: ${e.message}`);
  }
}
```

```bash
node verify.mjs
```

`mermaid.parse()` だけでなく `render()` まで通すのは、lexer/parser を通過してもレイアウト処理で
落ちるケースがあるため（例: 全角空白は `Lexical error` とは別のエラーになる）。

### 2. GitHub レンダラー（claude-in-chrome）— GitHub 固有挙動の確認

GitHub.com の Markdown プレビュー（Viewscreen）は mermaid 本体とは別に、GitHub 固有の前処理
（過去に btoa Latin-1 エラーが報告された等）を持つ可能性がある。**「mermaid では OK でも GitHub では
NG」または「その逆」を切り分けたいときだけ**この手段を使う。実パーサで再現できる一般的な構文エラーを
わざわざこちらで確認する必要はない。

手順:

1. 検証したいケースを Markdown + mermaid コードブロックとしてフィクスチャファイルに書き、GitHub へ push する
2. `claude-in-chrome` の deferred tools をロードする

   ```
   ToolSearch query: "select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,mcp__claude-in-chrome__computer,mcp__claude-in-chrome__tabs_create_mcp"
   ```

3. 複数ブラウザが接続されている場合は `AskUserQuestion` で対象を確認してから `switch_browser` / `select_browser` する（省略不可）
4. `navigate` でフィクスチャファイルの GitHub 上の URL（`https://github.com/<org>/<repo>/blob/<branch>/<path>`）を開く
5. `computer`（スクリーンショット）で各セクションが「Unable to render rich display」にならず描画されているかを目視確認する

GitHub の mermaid バージョンは固定・公開されていないため、この手段で得た結果は**その時点の GitHub の
挙動**であることに注意する。将来 GitHub 側が mermaid を更新すれば結果が変わりうる（実際、旧版の
btoa エラーはこの検証で再現しなかった——バグが直った可能性がある）。

## 全体の手順

1. **仮説を列挙する**: 「これも壊れるかもしれない」と思うパターンをすべて洗い出す。1 つ確認して
   満足せず、関連するパターン（識別子の位置違い・diagram 種別違い・クォート有無等）を横展開する
2. **パターンごとに独立したテストケースを書く**: 1 ケース = 1 セクション。複数の懸念を 1 つの図に
   混ぜない（どの文字が原因か切り分けられなくなる）
3. **実パーサで検証する**: 上記スクリプトで全ケースを一括実行し、OK/ERROR を記録する
4. **GitHub 固有の懸念があるケースだけ Chrome で確認する**: 実パーサと結果が食い違う可能性がある
   場合（GitHub 側の前処理・レンダラーバージョン差）に限る
5. **結果を照合してからルールに反映する**: 実パーサ・GitHub 双方の結果を突き合わせ、
   `lint_mermaid.py` の実装と `mermaid-diagram`/`mermaid-lint` の SKILL.md へ反映する。
   一部のケースだけを根拠に他のルールまで拡大解釈しない
6. **フィクスチャは消さずに残す**: `fixtures/github_render_verification.md` のように、検証に使った
   ケースと結果の対応表をそのまま残す。将来同種の疑問が出たときの一次資料になる

## この手順を使うとき

- 新しい文字種別・記法が lint で NG/WARN になるべきか判断に迷うとき
- ユーザーから「これは実際には動いている」等、既存ルールと矛盾する報告があったとき
- lint のルールを削除・緩和する前（削除は追加よりも影響が大きい。実証なしに緩めない）

## 関連

- `../fixtures/github_render_verification.md` — 本メソドロジーを使った実際の検証結果
- `../fixtures/fixture.md` — `lint_mermaid.py` 自身の検出ロジックの回帰テスト（本メソドロジーとは別。
  こちらは「lint が仕様通りに発火するか」、本メソドロジーは「仕様・実挙動が何であるか」を扱う）
