# NEVER `DIR ?= .` — a default silently defeats the `[ -n "$(DIR)" ]` guard below:
# every recipe would see DIR as non-empty even when the user forgot to pass it,
# and `make install-claude-project-symlink` (no DIR=) would install into whatever
# directory `make` happens to run from instead of erroring as the message promises.
PLUGIN := mermaid

# .DEFAULT_GOAL は必ず help に固定する（MANDATORY）。
# Makefile 内で最初に定義されたターゲットが GNU make の既定ゴールになるため、
# これを明示しないと引数なし `make` が help ではなく最初の install-* を実行してしまう。
# これは DIR の未定義ガード (下記) とは別の保護であり、両方が必要 — DEFAULT_GOAL は
# 「引数なし make」を、DIR 未定義ガードは「target 名だけ渡して DIR= を忘れた make」を防ぐ。
.DEFAULT_GOAL := help

.PHONY: help install-claude-project-copy
help:
	@echo "Usage: make <target> DIR=/path/to/project"
	@echo ""
	@echo "Targets:"
	@grep -E '^[a-zA-Z_-]+:.*$$' $(MAKEFILE_LIST) | grep -v '^help:' | sed 's/:.*//' | sort -u | sed 's/^/  /'

# 種別 A × copy (renewal): plugin-wide commit-safe placement、install_copy.sh を呼ぶ。
# 自動 uninstall は提供しない (renewal §3.10)。設置物は commit 対象であり、削除は
# `git rm -r .claude/skills/<...> .claude/.{plugin}/` 等のユーザー操作で完結する。
# install_copy.sh の print_summary が完了時に削除手順を案内するため、Makefile に
# uninstall-claude-project-copy ターゲットは **生成しない** (.PHONY からも除外)。
install-claude-project-copy:
	@[ -n "$(DIR)" ] || { echo "Error: DIR is required: make $@ DIR=/path/to/project" >&2; exit 1; }
	@bash scripts/plugin-installer/install_copy.sh $(PLUGIN) "$(DIR)"
