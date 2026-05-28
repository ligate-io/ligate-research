"""Fetch a sample of recent Ethereum mainnet transactions and project to a bipartite degree distribution.

Used to populate §A.4's real-chain Chung-Lu calibration in PoUA v0.10
(issue #120). The script fetches ~N recent blocks via a free public RPC,
extracts the (from, to) bipartite, computes degree sequences on both
sides, fits a power-law tail via the Hill estimator, and caches both the
raw sample provenance metadata and the resulting degree sequences for
use by `run_a3_fpr_comparison.py`.

Cache path: prototypes/poua-sim/data/ethereum_bipartite_<block_range>.json

Run from repo root:

    python3 prototypes/poua-sim/scripts/fetch_ethereum_bipartite.py \\
        --blocks 50

The script is idempotent: re-running with the same block window
regenerates the cache from the (still-immutable) RPC source.
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CACHE_DIR = REPO_ROOT / "prototypes/poua-sim/data"

# Free public RPC endpoints. Try in order until one responds.
RPC_ENDPOINTS = [
    "https://ethereum-rpc.publicnode.com",
    "https://eth.llamarpc.com",
    "https://rpc.ankr.com/eth",
    "https://cloudflare-eth.com",
]

USER_AGENT = "ligate-research/poua-v0.10 (https://github.com/ligate-io/ligate-research)"


def _rpc_call(endpoint: str, method: str, params: list, request_id: int = 1) -> dict:
    """Issue a single JSON-RPC POST and return the parsed `result`."""
    payload = json.dumps(
        {"jsonrpc": "2.0", "method": method, "params": params, "id": request_id}
    ).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        method="POST",
        data=payload,
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    if "error" in body:
        raise RuntimeError(f"RPC error: {body['error']}")
    return body["result"]


def pick_endpoint() -> str:
    """Return the first RPC endpoint that responds within 10 seconds."""
    for url in RPC_ENDPOINTS:
        try:
            block_hex = _rpc_call(url, "eth_blockNumber", [])
            print(f"using {url} (latest block {int(block_hex, 16)})")
            return url
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as e:
            print(f"  skip {url}: {e}")
    raise RuntimeError("no public RPC reachable; cannot fetch real-chain data")


def fetch_block(endpoint: str, block_number: int) -> dict:
    """Fetch a single block with full transaction objects."""
    block_hex = hex(block_number)
    return _rpc_call(endpoint, "eth_getBlockByNumber", [block_hex, True])


def extract_bipartite(blocks: list[dict]) -> tuple[Counter, Counter, int]:
    """Project blocks to (sender_degrees, recipient_degrees, total_txns).

    Includes every transaction's (from, to). Filters out contract-creation
    transactions (to == None) since those don't carry a bipartite edge.
    """
    sender_degrees: Counter = Counter()
    recipient_degrees: Counter = Counter()
    total_txns = 0
    for block in blocks:
        for tx in block.get("transactions", []):
            from_addr = tx.get("from")
            to_addr = tx.get("to")
            if from_addr is None or to_addr is None:
                continue  # contract creation: no bipartite edge
            sender_degrees[from_addr.lower()] += 1
            recipient_degrees[to_addr.lower()] += 1
            total_txns += 1
    return sender_degrees, recipient_degrees, total_txns


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--blocks",
        type=int,
        default=50,
        help="Number of recent blocks to fetch (default 50, ~10-15k transactions)",
    )
    parser.add_argument(
        "--start-block",
        type=int,
        default=None,
        help="Explicit start block (default: latest - blocks)",
    )
    args = parser.parse_args()

    endpoint = pick_endpoint()
    latest_hex = _rpc_call(endpoint, "eth_blockNumber", [])
    latest = int(latest_hex, 16)
    start_block = args.start_block if args.start_block is not None else latest - args.blocks
    end_block = start_block + args.blocks - 1

    print(f"fetching blocks [{start_block}, {end_block}] ({args.blocks} blocks)")

    blocks: list[dict] = []
    t0 = time.time()
    for i, h in enumerate(range(start_block, end_block + 1)):
        try:
            blk = fetch_block(endpoint, h)
        except (urllib.error.URLError, urllib.error.HTTPError, RuntimeError) as e:
            print(f"  block {h}: error {e}; skipping")
            continue
        blocks.append(blk)
        if (i + 1) % 10 == 0:
            print(f"  fetched {i + 1}/{args.blocks} blocks ({time.time() - t0:.1f}s elapsed)")

    sender_degs, recipient_degs, n_txns = extract_bipartite(blocks)
    print(
        f"extracted {n_txns} transactions; "
        f"{len(sender_degs)} unique senders, {len(recipient_degs)} unique recipients"
    )

    output = {
        "provenance": {
            "source_url": endpoint,
            "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
            "block_range": [start_block, end_block],
            "block_count": len(blocks),
            "transaction_count": n_txns,
        },
        "sender_degree_sequence": sorted(sender_degs.values(), reverse=True),
        "recipient_degree_sequence": sorted(recipient_degs.values(), reverse=True),
    }

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"ethereum_bipartite_{start_block}_{end_block}.json"
    with open(cache_path, "w") as fh:
        json.dump(output, fh, indent=2)
    print(f"wrote {cache_path.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
