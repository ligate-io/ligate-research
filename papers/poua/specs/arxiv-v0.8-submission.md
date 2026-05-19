# arXiv submission package, PoUA v0.8

Closes [ligate-research#9](https://github.com/ligate-io/ligate-research/issues/9). Submission is a Stefan-manual step on arxiv.org with a logged-in account; this document captures the metadata + checklist so the form-fill is mechanical.

## Pre-submission gate

Do NOT submit until:

- [ ] v0.8 PDF is final and merged to `main` (this branch: `paper/poua-v0.8`)
- [ ] At least one endorser has approved the primary category (cs.CR or cs.DC, depending on Yu's eligibility)
- [ ] CHANGELOG entry for v0.8 is committed
- [ ] CONTRIBUTING.md license is reconciled with the chosen arXiv license (we use Apache-2.0 OR MIT for code and CC-BY-4.0 for paper text per `LICENSE-CC-BY-4.0`; arXiv accepts CC-BY-4.0)
- [ ] At least one co-author confirmation if the paper has co-authors (currently single-author: Stefan Stefanović / Ligate Labs)

## arXiv form fill

### Title

```
Proof of Useful Attestation (PoUA): A Consensus Primitive for Attestation-Native Chains
```

### Authors

Stefan Stefanović, Ligate Labs.

(If a co-author is added before submission, update here. arXiv requires full names and affiliations.)

### Abstract

Use the paper's existing abstract verbatim, from `papers/poua/poua.md` §Abstract. Paste into the arXiv abstract field, removing LaTeX math markup where the arXiv form does not accept it (typically a stripped Markdown version is fine).

Abstract length cap on arXiv: 1920 characters. Verify before submitting; if over, condense or split into "abstract + summary."

### Categories

- **Primary**: cs.CR (Cryptography and Security)
- **Cross-list**: cs.DC (Distributed, Parallel, and Cluster Computing)
- **Cross-list, ambitious**: cs.GT (Computer Science and Game Theory) — for §5.5 cost-to-grind and §6 incentive analysis

If Yu's eligibility is cs.DC-only (verify per `v0.8-yu.md` pre-send notes), flip to cs.DC primary + cs.CR cross-list + cs.GT cross-list.

### License

CC-BY-4.0 (matches `papers/poua/LICENSE` and repo's `LICENSE-CC-BY-4.0`).

### Comments field

Suggested text:

```
60 pages, 6 figures. v0.8 of the PoUA working paper. Reference simulator
at https://github.com/ligate-io/ligate-research/tree/main/prototypes/poua-sim
with empirical validation for every load-bearing claim. Changelog:
https://github.com/ligate-io/ligate-research/blob/main/papers/poua/CHANGELOG.md
```

### Source files

Two options:

1. **Upload pre-compiled PDF** (`papers/poua/poua.pdf`). Simpler. arXiv hosts the PDF; no compilation on their side.
2. **Upload LaTeX source** (`papers/poua/poua.tex`, `papers/poua/header-includes.tex`, all figure files under `prototypes/poua-sim/out/`). arXiv compiles. Riskier (their TeX environment can differ from tectonic's). Useful only if we want their canonical compilation badge.

**Recommend option 1.** The figures path conversion from local relative paths (`../../prototypes/poua-sim/out/`) to arXiv source-tree paths is fragile; the pre-compiled PDF avoids the issue. Option 2 can wait until the paper hits a v1.0 / journal-submission milestone.

### Endorsement

If first-time submitter to the chosen primary category (likely), arXiv asks for an endorsement code from a registered endorser. The endorser request flow:

1. Submit the paper draft. arXiv shows "endorsement required" with a unique endorsement URL.
2. Email the URL to the endorser (Yu first per `v0.8-yu.md`; Vukolić as backup per `v0.8-vukolic-followup-endorsement.md`).
3. Endorser approves via the URL.
4. arXiv finalizes the submission.

Endorsement is one-time per category per endorser-endorsee pair. Future submissions to the same category from Stefan do not need re-endorsement.

### After submission

- [ ] arXiv assigns an identifier (typically `arXiv:2026.XXXXX [cs.CR]`)
- [ ] Update `papers/poua/README.md` "Working paper" line with the arXiv link
- [ ] Update `papers/poua/CHANGELOG.md` v0.8 entry with the arXiv identifier
- [ ] Update `~/Desktop/ligate-docs/research/outreach/poua/STATE.md` with submission date + identifier
- [ ] Add `arXiv: 2026.XXXXX` to the Outreach Attio records for both Yu and Vukolić
- [ ] Send Yu the arXiv link as a "thanks again, here is where it lives" follow-up (one short line, no new ask)
- [ ] Marketing-side: update ligate.io landing's PoUA reference (if any) with the arXiv link in addition to the GitHub link
- [ ] Cross-post arXiv link on X / LinkedIn per the distribution playbook

## Out of scope for this submission

- Submitting the five supplementary papers (per-schema fees, native delegation, cross-schema composition, time-locked attestations, native DA). Those are v0.2-draft-tracking issues; not arxiv-ready.
- Conference submission. Per CHANGELOG.md "path forward" in v0.7, conference submission is a mid-2027 target.
- Author identifier (ORCID etc.) registration. Stefan should have ORCID if not already; one-time, free, separate process at orcid.org.
