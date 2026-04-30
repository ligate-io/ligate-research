# Contributing to Ligate Research

Thanks for considering a contribution. This repo's primary purpose is to be a venue for substantive technical critique and collaboration on Ligate's protocol-level research direction.

## What contributions look like

### Substantive technical critique on a paper

The most valuable contribution. Open a GitHub issue with the paper name in the title:

> `[poua] question about §5.3 cost-to-attack derivation`

> `[poua] suggested counterexample to A3 detection in §5.5`

Include:
- The specific section or claim you're addressing
- Your critique or proposed alternative
- Any references to prior literature we may have missed

We will respond. If the critique lands, it gets folded into the next paper revision with attribution (and your name in the version history if you'd like). If it doesn't, we'll explain why in writing.

### Typos and small wording fixes

Send a PR directly against the paper's source markdown. We'll merge or comment.

### Larger structural revisions

Open an issue first. Restructuring a paper requires alignment on what we're trying to communicate. A PR that changes a paper's narrative arc without prior discussion is unlikely to land cleanly.

### New paper proposals

For now, the paper roadmap is set by Ligate Labs. If you have a strong proposal for a new paper that fits Ligate's research direction (consensus, attestation primitives, delegation, fee markets, schema composition), open an issue describing the proposal and we'll discuss whether it fits and how to scope it.

## Author requirements (for substantive contributions)

If your contribution rises to the level of co-authorship on a paper:

- You retain copyright on your contribution. By submitting, you license your contribution under [CC-BY-4.0](LICENSE-CC-BY-4.0) (papers) or [Apache-2.0](LICENSE-APACHE-2.0) (code), matching the repository's licenses.
- You agree to be credited by name (or pseudonym) in the paper's author list and version history.
- You confirm you have the right to license the contribution under the above terms.

## Building papers locally

Papers are written in markdown and compiled to PDF via Pandoc + Tectonic. To build a paper locally:

```bash
brew install pandoc tectonic     # macOS
# or apt-get install pandoc; cargo install tectonic   # Linux

cd papers/poua
pandoc poua-v0.md -o poua-v0.pdf \
  --pdf-engine=tectonic \
  --include-in-header=header-includes.tex \
  -V geometry:margin=1in \
  -V documentclass=article \
  -V fontsize=11pt
```

The first build will download LaTeX dependencies (~30 MB); subsequent builds are fast.

On macOS without Xcode, set `RISC0_SKIP_BUILD_KERNELS=1` and `DYLD_FALLBACK_LIBRARY_PATH=/Library/Developer/CommandLineTools/usr/lib` if you encounter library resolution errors during related tooling setup.

## Tone and review norms

- Be specific. "This section is unclear" is less useful than "the formula in §5.3 doesn't hold when $r_{\min} = 0$."
- Be charitable. Working papers have known gaps; we list them in §9 of each paper. Critiquing a known limitation is welcome but please reference the paper's own framing.
- Be patient. We respond within ~1 week to substantive critique. PRs for typos may be merged faster.

## Code of Conduct

This repository follows the [Contributor Covenant 2.1](https://www.contributor-covenant.org/version/2/1/code_of_conduct/) by reference. Be civil. Critique ideas, not people. Reports of misconduct go to hello@ligate.io.
