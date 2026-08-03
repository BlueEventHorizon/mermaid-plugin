#!/usr/bin/env python3
"""Mermaid 図の静的検査。

`mermaid-diagram` Skill が説くルールのうち、機械判定できるものだけを検査する。
標準ライブラリのみで動く。mermaid パーサーは使わないため、構文エラーを網羅はしない。
描画の最終確認は https://mermaid.live/ で行うこと。

使い方:
    lint_mermaid.py <FILE>...        Markdown なら ```mermaid ブロックを抽出して検査
    cat part.md | lint_mermaid.py -  標準入力を検査（文書の一部だけを見たいとき）

判定は 2 段階。
    NG    構文が壊れる。終了コード 1
    WARN  意図次第で正しい場合がある。終了コード 0

日本語・CJK ラベル/識別子の未クォートは検査しない。fixtures/github_render_verification.md
での実地検証 (2026-07) の結果、GitHub 上で問題が再現しなかったため。flowchart では
Unicode Letter 以外の非 ASCII 文字を素の識別子に使うとエラーになるため検査する。
stateDiagram-v2 は同じ文字を状態 ID に使用できるため検査しない。
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

FENCE_RE = re.compile(r"```mermaid[ \t]*\n(.*?)```", re.S)
# フェンスの数え上げは行頭のものだけを見る。mermaid を解説する文書は
# インラインコード内に ``` を書くことがあり、素朴に数えると誤検出する。
FENCE_LINE_RE = re.compile(r"^[ \t]*```", re.M)

FLOWCHART_KINDS = {"flowchart", "graph"}

EDGE_LABEL_RE = re.compile(r'--\s*([^-|>\n"]+?)\s*--[->]')
PIPE_LABEL_RE = re.compile(r'\|([^"|\n]+)\|')
# ドット付きリンクのラベル記法 `A -. text .-> B`。EDGE_LABEL_RE は `--` 形式専用のため別枠で扱う。
DOTTED_EDGE_LABEL_RE = re.compile(r'-\.\s*([^.\n]+?)\s*\.-')

QUOTED_RE = re.compile(r'"[^"\n]*"')
BRACKETED_RE = re.compile(r"\[[^\[\]\n]*\]|\([^()\n]*\)|\{[^{}\n]*\}")

# `A---oBar` は circle edge、`A---xBar` は cross edge と解釈される。
OX_EDGE_RE = re.compile(r"-{2,3}[ox][A-Za-z_]")

# flowchart / classDiagram では Note キーワードが使えない。
NOTE_RE = re.compile(r"^\s*[Nn]ote\s+(right|left|over)\b")


@dataclass
class Finding:
    level: str
    check: str
    line: int
    message: str


def has_unsafe_bare_char(text: str) -> bool:
    """mermaid の lexer が素の識別子で認識できない文字を含むか。

    github_render_verification.md での実地検証 (2026-07) の結果:
    - Unicode の Letter カテゴリ (Lo/Lm/Lu/Ll/Lt。CJK 統合漢字・ひらがな・カタカナ等) は
      未クォートの識別子でも問題なく描画された
    - Letter 以外の非 ASCII 文字 (記号・句読点・全角数字・全角括弧等) は素の識別子で
      `Lexical error` 等のエラーになる
    このチェックでは ASCII 文字は対象外。
    """
    for c in text:
        if ord(c) <= 0x7F:
            continue
        if unicodedata.category(c).startswith("L"):
            continue
        return True
    return False


def clip(text: str, width: int = 40) -> str:
    stripped = text.strip()
    return stripped if len(stripped) <= width else stripped[:width] + "…"


def diagram_kind(block: str) -> str:
    for line in block.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue
        match = re.match(r"(\w[\w-]*)", stripped)
        return match.group(1) if match else ""
    return ""


def strip_labels(line: str) -> str:
    """クォート・パイプラベル・エッジラベル・括弧ラベルを落とし、素の識別子だけ残す。"""
    text = QUOTED_RE.sub(" ", line)
    text = PIPE_LABEL_RE.sub(" ", text)
    text = EDGE_LABEL_RE.sub(" --> ", text)
    text = DOTTED_EDGE_LABEL_RE.sub(" -.-  ", text)
    previous = None
    while previous != text:
        previous = text
        text = BRACKETED_RE.sub(" ", text)
    return text


def lint_flowchart(block: str, offset: int, findings: list[Finding]) -> None:
    for index, line in enumerate(block.split("\n")):
        lineno = offset + index
        stripped = line.strip()
        if not stripped or stripped.startswith("%%"):
            continue

        if "%%" in line:
            findings.append(
                Finding("NG", "comment", lineno, f"行末 %% コメントは parse error: {clip(line)}")
            )
        if re.search(r"(-->|---|\bsubgraph\b)\s+end\b", line) or re.match(
            r"^\s*end\s*(\[|\(|\{)", line
        ):
            findings.append(
                Finding("NG", "end", lineno, f"ノード ID に lowercase end: {clip(line)}")
            )
        if NOTE_RE.match(line):
            findings.append(
                Finding("NG", "note", lineno, f"flowchart は Note を持たない: {clip(line)}")
            )
        # 行末コメントは上で報告済み。以降の検査ではコメント本文を対象から外す。
        code_part = line.split("%%")[0]
        if has_unsafe_bare_char(strip_labels(code_part)):
            findings.append(
                Finding(
                    "NG",
                    "lexical",
                    lineno,
                    "Letter 以外の非 ASCII 文字を素の識別子に使うとエラーになる。"
                    f"ラベルとしてクォートする: {clip(line)}",
                )
            )
        if OX_EDGE_RE.search(line):
            findings.append(
                Finding(
                    "WARN",
                    "ox-edge",
                    lineno,
                    f"circle/cross edge と解釈される。ノード名ならスペースを挟む: {clip(line)}",
                )
            )


def lint_class_diagram(block: str, offset: int, findings: list[Finding]) -> None:
    for index, line in enumerate(block.split("\n")):
        if NOTE_RE.match(line):
            findings.append(
                Finding(
                    "NG",
                    "note",
                    offset + index,
                    f"classDiagram は Note を持たない: {clip(line)}",
                )
            )


def lint_block(block: str, offset: int, findings: list[Finding]) -> None:
    kind = diagram_kind(block)
    if kind in FLOWCHART_KINDS:
        lint_flowchart(block, offset, findings)
    elif kind == "classDiagram":
        lint_class_diagram(block, offset, findings)


def blocks_of(text: str, as_markdown: bool) -> list[tuple[str, int]]:
    """(ブロック本文, 開始行番号) の一覧を返す。行番号は 1 始まり。"""
    if not as_markdown:
        return [(text, 1)]
    return [
        (match.group(1), text[: match.start(1)].count("\n") + 1)
        for match in FENCE_RE.finditer(text)
    ]


def lint_text(text: str, as_markdown: bool) -> list[Finding]:
    findings: list[Finding] = []
    if as_markdown and len(FENCE_LINE_RE.findall(text)) % 2 != 0:
        findings.append(Finding("NG", "fence", 0, "コードフェンスが閉じていない"))
    for block, offset in blocks_of(text, as_markdown):
        lint_block(block, offset, findings)
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", metavar="FILE", help="検査対象。`-` で標準入力")
    parser.add_argument(
        "--format",
        choices=("auto", "markdown", "mermaid"),
        default="auto",
        help="auto は ```mermaid の有無で判定する",
    )
    args = parser.parse_args()

    total = 0
    blocks = 0
    for path in args.paths:
        if path == "-":
            text, label = sys.stdin.read(), "(stdin)"
        else:
            target = Path(path)
            if not target.is_file():
                print(f"ファイルが見つかりません: {target}", file=sys.stderr)
                return 1
            text, label = target.read_text(encoding="utf-8"), str(target)

        as_markdown = "```mermaid" in text if args.format == "auto" else args.format == "markdown"
        blocks += len(blocks_of(text, as_markdown))

        for finding in lint_text(text, as_markdown):
            where = f"{label}:{finding.line}" if finding.line else label
            print(f"{finding.level:<4} [{finding.check}] {where}  {finding.message}")
            total += finding.level == "NG"

    if total:
        print(f"\nNG {total} 件。修正してください。")
        return 1

    print(f"OK  mermaid ブロック {blocks} 個に NG はありません。")
    print("静的検査はパーサーの代わりにはなりません。https://mermaid.live/ で描画も確認してください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
