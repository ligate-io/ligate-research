#!/usr/bin/env python3
# ruff: noqa: D301
r"""Validate that paper citations of simulator/test paths resolve to real files.

Walks ``papers/**/*.md`` looking for citation patterns that point at the
simulator or test infrastructure (currently ``prototypes/poua-sim/``).
For each citation, confirms the cited file exists in the repo. Exits
non-zero if any citation is dangling.

This implements the structural rule from
https://github.com/ligate-io/ligate-research/issues/23: every numerical
claim in a paper that cites a simulator script or test vector must
resolve to a real file. The check is lexical (no Python execution); it
catches typos, renamed scripts, and deleted test vectors. It does NOT
check that the cited test actually validates the cited claim, that is
the author's responsibility.

Patterns matched:

- ``\\texttt{prototypes/poua-sim/...}`` (LaTeX inline file references in paper prose)
- ``\\href{...}{prototypes/poua-sim/...}`` (LaTeX hyperlink targets)
- Markdown code-fenced ``\`prototypes/poua-sim/...\``` (inline code references)
- Markdown link ``[label](prototypes/poua-sim/...)``

LaTeX escapes are unescaped before path resolution: ``\\_`` → ``_``,
``\\&`` → ``&``, etc.

Usage:

    python scripts/check_citations.py            # CI mode: exit 1 on any miss
    python scripts/check_citations.py --verbose  # also report each citation found
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PAPERS_DIR = REPO_ROOT / "papers"

# Match anything that looks like a relative path under prototypes/ or papers/
# referenced from the paper body. We want to catch:
#
#   \texttt{prototypes/poua-sim/scripts/run_capital_scan.py}
#   \href{...}{prototypes/poua-sim/scripts/run_capital_scan.py}
#   `prototypes/poua-sim/scripts/run_capital_scan.py`
#   [text](prototypes/poua-sim/scripts/run_capital_scan.py)
#   prototypes/poua-sim/test_vectors/alpha_eff.json
#
# But NOT trigger on prose mentions like "the prototypes/poua-sim folder"
# without a specific file. So we require a file-extension suffix.
PATH_PATTERN = re.compile(
    r"""(?P<path>
        prototypes/[A-Za-z0-9_./\\-]+\.(?:py|md|json|toml|yml|yaml|txt|tex|png|jpg|svg|pdf)
        |
        papers/[A-Za-z0-9_./\\-]+\.(?:py|md|json|toml|yml|yaml|txt|tex|png|jpg|svg|pdf)
    )""",
    re.VERBOSE,
)


def unescape_latex(s: str) -> str:
    """Drop LaTeX escapes that obscure paths.

    LaTeX escapes ``_`` to ``\\_`` inside ``\\texttt{}`` to avoid math-mode
    interpretation. We strip those for path resolution.
    """
    return (
        s.replace(r"\_", "_")
        .replace(r"\&", "&")
        .replace(r"\#", "#")
        .replace(r"\%", "%")
    )


def find_citations(paper_md: Path) -> list[tuple[int, str]]:
    """Return list of (line_number, raw_path) citations found in the file."""
    citations = []
    text = paper_md.read_text()
    for line_no, line in enumerate(text.splitlines(), start=1):
        for match in PATH_PATTERN.finditer(line):
            citations.append((line_no, match.group("path")))
    return citations


def validate(paper_md: Path, verbose: bool = False) -> list[tuple[int, str, str]]:
    """Return list of (line_number, raw_path, error) for unresolved citations."""
    failures: list[tuple[int, str, str]] = []
    seen: set[tuple[int, str]] = set()
    for line_no, raw_path in find_citations(paper_md):
        # Deduplicate per-(line, path) to avoid double-reporting on lines
        # with multiple matches of the same path.
        key = (line_no, raw_path)
        if key in seen:
            continue
        seen.add(key)

        cleaned = unescape_latex(raw_path)
        target = REPO_ROOT / cleaned
        if not target.exists():
            failures.append((line_no, raw_path, f"file not found: {target}"))
        elif verbose:
            print(f"  ok: {paper_md.name}:{line_no} -> {cleaned}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verbose", action="store_true", help="report each citation found")
    parser.add_argument(
        "--paper",
        type=Path,
        help="check only the specified paper file (default: all papers/**/*.md)",
    )
    args = parser.parse_args()

    if args.paper:
        paper_files = [args.paper]
    else:
        paper_files = sorted(PAPERS_DIR.rglob("*.md"))

    if not paper_files:
        print("No paper markdown files found under papers/", file=sys.stderr)
        return 1

    total_citations = 0
    total_failures: list[tuple[Path, int, str, str]] = []
    for paper in paper_files:
        citations = find_citations(paper)
        total_citations += len(citations)
        if args.verbose:
            print(f"checking {paper.relative_to(REPO_ROOT)} ({len(citations)} citations)")
        failures = validate(paper, verbose=args.verbose)
        for line_no, raw_path, err in failures:
            total_failures.append((paper, line_no, raw_path, err))

    if total_failures:
        print(f"\n{len(total_failures)} citation(s) failed to resolve:", file=sys.stderr)
        for paper, line_no, raw_path, err in total_failures:
            rel = paper.relative_to(REPO_ROOT)
            print(f"  {rel}:{line_no} -> {raw_path}", file=sys.stderr)
            print(f"      {err}", file=sys.stderr)
        return 1

    print(f"checked {len(paper_files)} paper file(s), {total_citations} citation(s) ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
