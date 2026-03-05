#!/usr/bin/env python3
import json
import subprocess
import sys


def get_hash(url):
    try:
        result = subprocess.run(
            ["nix-prefetch-url", "--print-path", url],
            capture_output=True,
            text=True,
            check=True,
        )
        lines = result.stdout.strip().split("\n")
        path = lines[-1]
        hash_result = subprocess.run(
            ["sha256sum", path], capture_output=True, text=True, check=True
        )
        return hash_result.stdout.split()[0]
    except Exception as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def main():
    with open("lfs_sources.json") as f:
        sources = json.load(f)

    hashes = {}
    for name, url in sources.items():
        print(f"Fetching hash for {name}...")
        h = get_hash(url)
        if h:
            hashes[name] = h
            print(f"  {name}: {h}")
        else:
            print(f"  Failed: {name}")

    with open("lfs_hashes_new.json", "w") as f:
        json.dump(hashes, f, indent=2)

    print("\nHashes written to lfs_hashes_new.json")


if __name__ == "__main__":
    main()
