# time-locked-attestations-sim

Reference simulator for the **Time-Locked / Commit-Reveal Attestations** paper. Mirrors paper §3 (system model), §4 (mechanism), §5 (cryptographic security), and §8 (failure modes). M1 milestone of the paper's [Appendix A simulator-validation plan](../../papers/time-locked-attestations/time-locked-attestations.md).

## What this simulator validates

| Paper section | Module | What it exercises |
|---|---|---|
| §3.1 + §3.4 | `commitment.py` | Commitment tuple + 128-bit nonce floor + SHA-256 / BLAKE3 hash dispatch |
| §3.3 | `lifecycle.py` | Four-state machine: COMMITTED → REVEALED / EXPIRED → CLEANED_UP |
| §4.1 - §4.5 | `transactions.py` | `MsgCommit` / `MsgReveal` / `MsgCleanup` admission + batched-reveal sequencing |
| §5.1 - §5.4 | (via tests) | Binding, hiding, nonce-entropy bound, time-lock-by-chain-height |
| §8.1 - §8.6 | `failure_modes.py` | Six attack-scenario harnesses with quantitative bounds |

## Quick start

```bash
cd prototypes/time-locked-attestations-sim
pip install -e .
pytest tests/                                      # 41 tests
python scripts/run_failure_mode_panel.py           # writes out/failure_modes_panel.png
```

## Layout

```
time-locked-attestations-sim/
├── pyproject.toml                # package metadata
├── README.md                     # this file
├── src/time_locked_attestations_sim/
│   ├── commitment.py             # §3.1 + §3.4
│   ├── lifecycle.py              # §3.3
│   ├── transactions.py           # §4
│   └── failure_modes.py          # §8 harnesses
├── tests/
│   ├── test_commitment.py
│   ├── test_lifecycle.py
│   ├── test_transactions.py
│   └── test_failure_modes.py
├── test_vectors/
│   └── commitment_canonical_encoding.json   # cross-language reference
├── scripts/
│   └── run_failure_mode_panel.py            # §8 panel-figure generator
└── out/
    └── failure_modes_panel.png              # generated figure
```

## Out of scope at M1

The simulator deliberately stops short of §6's use-case-validated work (strategic-bidder sealed-bid auction game, embargo-leak game). Per the paper's §6.1 gate, that work begins when at least one design partner per use-case category (auction, embargo, regulatory) submits a concrete spec. The cryptographic and mechanism layers shipped here are partner-independent and exercise the security claims the paper makes.

## Discipline

- **Every paper claim that the simulator covers has a test.** Failing claims would surface as test failures; tests link back to the paper subsection by docstring.
- **Cross-language test vectors** live under `test_vectors/`. Future Rust or TypeScript implementations on Ligate Chain MUST reproduce these byte-for-byte; mismatches are a chain-versus-simulator drift.
- **Failure modes are quantitative.** §8.5 reports effective bit-security under nonce reuse rather than just "secure / insecure"; §8.6 reports adversary cost as a function of deposit floor.
- **The simulator follows the same code conventions as `poua-sim`, `native-delegation-sim`, and `per-schema-fees-sim`** (frozen dataclasses, structured `AdmissionResult` rejection reasons, deterministic test fixtures).

## Limitations and follow-ups

- **No simulator-level cryptographic stress test.** Hash-collision robustness is asserted at the theoretical 2^128 bound, not exercised by attempting to find collisions (which is computationally infeasible by construction). Production cryptographic vetting belongs in the underlying primitive (Python's `hashlib`, downstream Rust's `sha2`), not here.
- **BLAKE3 falls back to SHA-256** if the optional `blake3` Python package is not installed; production runtimes targeting a BLAKE3-declared schema must ship native BLAKE3.
- **Poseidon raises `NotImplementedError`.** Reserved for the §9.1 ZK-friendly variant; v0.2.1 covers the cleartext-reveal mechanism only.
- **No multi-block lifecycle simulation.** The state machine is exercised at the single-block-height level. A full chain-time simulator (multiple commits interleaved with reveals and cleanups across a horizon of blocks) is a natural M2 extension.

## Related papers and simulators

- [`papers/time-locked-attestations/`](../../papers/time-locked-attestations/): the paper this simulator backs.
- [`papers/poua/`](../../papers/poua/): slashing and proposer-ordering rules referenced by §4.5.
- [`papers/cross-schema-composition/`](../../papers/cross-schema-composition/): typed references that consume revealed commitments.
- [`prototypes/poua-sim/`](../poua-sim/), [`prototypes/native-delegation-sim/`](../native-delegation-sim/), [`prototypes/per-schema-fees-sim/`](../per-schema-fees-sim/): sibling simulators with matching code conventions.

## License

- Code: Apache-2.0 OR MIT (`LICENSE-APACHE-2.0` at repo root).
- Test vectors: same.
- Figures generated under `out/`: CC-BY-4.0 (`LICENSE-CC-BY-4.0`), matching paper text.
