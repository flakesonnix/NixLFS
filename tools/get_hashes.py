#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Optional

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"


def print_header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'=' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 60}{RESET}\n")


def print_success(text: str) -> None:
    print(f"  {GREEN}✓{RESET} {GREEN}{text}{RESET}")


def print_error(text: str) -> None:
    print(f"  {RED}✗{RESET} {RED}{text}{RESET}")


def print_warning(text: str) -> None:
    print(f"  {YELLOW}⚠{RESET} {YELLOW}{text}{RESET}")


def print_info(text: str) -> None:
    print(f"  {BLUE}ℹ{RESET} {BLUE}{text}{RESET}")


def print_progress(current: int, total: int, name: str) -> None:
    percent: float = (current / total) * 100
    bar_len: int = 40
    filled: int = int(bar_len * current / total)
    bar: str = "█" * filled + "░" * (bar_len - filled)
    emoji: str = "🔄" if current < total else "✅"
    print(
        f"\n  {CYAN}┌{bar}┐{RESET} {percent:5.1f}%  {emoji} {BOLD}{name}{RESET}",
        end="\r",
        flush=True,
    )
    if current == total:
        print()


def get_hash(url: str, name: str) -> Optional[str]:
    try:
        print_info(f"Downloading {CYAN}{name}{RESET}...")

        result = subprocess.run(
            ["nix-prefetch-url", "--print-path", url],
            capture_output=True,
            text=True,
            check=True,
            stderr=subprocess.DEVNULL,
        )

        path: str = result.stdout.strip().split("\n")[-1]

        if not os.path.exists(path):
            print_warning(f"File not found locally, waiting...")
            time.sleep(2)
            if not os.path.exists(path):
                print_error(f"File still not found: {path}")
                return None

        print_info(f"Calculating SHA256 hash...")

        hash_result = subprocess.run(
            ["sha256sum", path], capture_output=True, text=True, check=True
        )

        sha256: str = hash_result.stdout.split()[0]

        size_mb: float = os.path.getsize(path) / (1024 * 1024)
        print_success(
            f"{GREEN}{name}{RESET} → {GREEN}{sha256[:16]}...{RESET} ({size_mb:.1f} MB)"
        )

        return sha256

    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e.cmd}")
        return None
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        return None


def main() -> None:
    print_header(f"📦  NixLFS Hash Fetcher  🔐")

    print_info(f"Reading sources from {CYAN}lfs_sources.json{RESET}...\n")

    with open("lfs_sources.json") as f:
        sources: dict[str, str] = json.load(f)

    total: int = len(sources)
    hashes: dict[str, str] = {}
    successful: int = 0
    failed: list[str] = []

    print(f"{BOLD}Total packages to fetch: {WHITE}{total}{RESET}\n")

    for i, (name, url) in enumerate(sources.items(), 1):
        print_progress(i, total, name)

        h: Optional[str] = get_hash(url, name)

        if h:
            hashes[name] = h
            successful += 1
        else:
            failed.append(name)
            hashes[name] = "0" * 64

        print()

    print_header(f"💾  Writing Results  📝")

    with open("lfs_hashes_new.json", "w") as f:
        json.dump(hashes, f, indent=2)

    print(f"  {BOLD}Output file:{RESET} {GREEN}lfs_hashes_new.json{RESET}")
    print(f"  {BOLD}Successful:{RESET} {GREEN}{successful}{RESET}/{total}")

    if failed:
        print(f"\n  {YELLOW}⚠  Failed packages:{RESET}")
        for name in failed:
            print(f"    {RED}•{RESET} {name}")

    print(f"\n{GREEN}🎉  Done!{RESET}\n")
    print(f"  To use the new hashes:")
    print(f"  {CYAN}mv lfs_hashes_new.json lfs_hashes.json{RESET}")
    print(f"  {CYAN}git add lfs_hashes.json && git commit -m 'Update hashes'{RESET}\n")


if __name__ == "__main__":
    main()
