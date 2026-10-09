# Wire this repo into a skills directory, and keep it inside its budgets.
#
# The repo is the single source of truth: each quality-* directory is symlinked
# individually into every installed CLI's skills directory (claude, codex,
# agy), so each of those directories keeps whatever else it already carries.

REPO       := $(CURDIR)
CLAUDE_DIR ?= $(HOME)/.claude/skills
CODEX_DIR  ?= $(HOME)/.codex/skills
AGY_DIR    ?= $(HOME)/.gemini/antigravity-cli/skills

# Every CLI reading a SKILL.md gets the same working tree. A host is only
# written to when it is installed here, and its own home — the parent of the
# skills directory — is what says so: judging by the skills directory itself
# would skip a host that has one but has never been given a skill.
HOST_DIRS  := $(CLAUDE_DIR) $(CODEX_DIR) $(AGY_DIR)

.DEFAULT_GOAL := help
.PHONY: help check validate test routes figures drift engines refute render hooks link unlink status

help:
	@echo "make check     validate + test + routes + figures + drift (CI and the pre-commit hook run the same)"
	@echo "make validate  static rules over the corpus"
	@echo "make test      prove every rule still fires"
	@echo "make routes    the acquisition-ownership regression test"
	@echo "make figures   re-derive the reference pages' figures and git behaviours"
	@echo "make drift     fail if any SKILL.md delivery block is stale (writes nothing)"
	@echo "make refute CLAIMS=f.json RUNNING=<engine>   put each claim to the engines that did not make it"
	@echo "make engines   ask each checker engine for one object; reports what is unreachable"
	@echo "make render    write the delivered blocks back into every SKILL.md"
	@echo "make hooks     install the pre-commit hook (checks the staged content)"
	@echo "make link      symlink the skills into claude / codex / agy"
	@echo "make unlink    remove those symlinks"
	@echo "make status    show what is linked"

check: validate test routes figures drift

validate:
	@python3 quality-tools/validate.py

test:
	@python3 quality-tools/test_validate.py

routes:
	@python3 quality-tools/test_acquisition_routes.py

figures:
	@python3 quality-tools/figures_check.py

drift:
	@python3 quality-tools/render.py --check

engines:
	@python3 quality-tools/engine.py --selftest

# No default for RUNNING: the running engine is stated, never assumed (engine.py).
refute:
	@test -n "$(CLAIMS)" && test -n "$(RUNNING)" || { echo "usage: make refute CLAIMS=claims.json RUNNING=<claude|codex|agy>"; exit 2; }
	@python3 quality-tools/refute.py --running "$(RUNNING)" "$(CLAIMS)"

render:
	@python3 quality-tools/render.py

# git says where the hook goes: in a worktree or submodule .git is a file.
hooks:
	@hook=$$(git rev-parse --git-path hooks/pre-commit) && \
		mkdir -p "$$(dirname "$$hook")" && \
		cp quality-tools/githooks/pre-commit "$$hook" && \
		chmod +x "$$hook" && \
		echo "pre-commit installed at $$hook"

# A skill is a directory holding a SKILL.md, under skills/ where the plugin
# format expects it. The prefix alone is not the test: quality-registry/ and
# quality-tools/ share it and must never be installed.
SKILL_DIRS := $(patsubst %/SKILL.md,%,$(wildcard skills/quality-*/SKILL.md))

link:
	@for dir in $(HOST_DIRS); do \
		if [ ! -d "$$(dirname "$$dir")" ]; then echo "skip $$dir (host not installed here)"; continue; fi; \
		mkdir -p "$$dir"; \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; \
			if [ -e "$$target" ] && [ ! -L "$$target" ]; then \
				echo "  skip $$name (a real path is already there)"; \
			else \
				ln -sfn "$(REPO)/$$path" "$$target"; echo "  link $$name"; \
			fi; \
		done; \
	done

# A symlink is ours only if it points into this repo; another checkout or set
# may have installed one under the same name.
unlink:
	@for dir in $(HOST_DIRS); do \
		[ -d "$$dir" ] || continue; \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; \
			[ -L "$$target" ] || continue; \
			case "$$(readlink "$$target")" in \
				"$(REPO)"/*) rm "$$target"; echo "  unlink $$name";; \
				*) echo "  skip $$name (links elsewhere: $$(readlink "$$target"))";; \
			esac; \
		done; \
	done

status:
	@for dir in $(HOST_DIRS); do \
		echo "$$dir"; \
		for path in $(SKILL_DIRS); do \
			name=$$(basename "$$path"); target="$$dir/$$name"; \
			if [ -L "$$target" ]; then \
				case "$$(readlink "$$target")" in \
					"$(REPO)"/*) echo "  linked   $$name";; \
					*) echo "  foreign  $$name -> $$(readlink "$$target")";; \
				esac; \
			else echo "  unlinked $$name"; fi; \
		done; \
	done
