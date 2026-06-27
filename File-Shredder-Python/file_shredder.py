"""
shredder.py — Secure File Shredder
═══════════════════════════════════════════════════════════════════
Overwrites a file multiple times with random/pattern data before
deleting it, making recovery significantly harder than a standard
delete operation.

Inspired by the DoD 5220.22-M and Gutmann erasure standards.

Author  : Raymundo B.
Python  : 3.14+
License : MIT

Usage:
    python shredder.py <filepath> [--passes N] [--force]

Examples:
    python shredder.py secret.txt
    python shredder.py secret.txt --passes 7
    python shredder.py secret.txt --force
═══════════════════════════════════════════════════════════════════
"""

from __future__ import annotations

# ─── Standard library ────────────────────────────────────────────
import argparse
import os
import sys

# ═══════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════

# Default number of overwrite passes.
# 3–7 is considered sufficient for modern SSDs/HDDs.
# Higher values = slower but marginally more secure.
DEFAULT_PASSES: int = 5

# The three write patterns that cycle each pass:
#   0 → random bytes  (unpredictable, hardest to recover)
#   1 → all zeros     (0x00 pattern)
#   2 → all ones      (0xFF pattern)
PATTERN_RANDOM = 0
PATTERN_ZEROS = 1
PATTERN_ONES = 2


# ═══════════════════════════════════════════════════════════════════
# CORE — overwrite_file
# ═══════════════════════════════════════════════════════════════════


def overwrite_file(filepath: str, passes: int = DEFAULT_PASSES) -> bool:
    """
    Securely erase a file by overwriting its contents multiple times,
    renaming it to a random name, then deleting it.

    Overwrite pattern per pass (cycles every 3):
        pass % 3 == 0  →  random bytes  (os.urandom)
        pass % 3 == 1  →  zeros         (0x00 * size)
        pass % 3 == 2  →  ones          (0xFF * size)
    A final random-byte pass always runs after the main loop.

    Args:
        filepath:  Absolute or relative path to the target file.
        passes:    Number of overwrite passes before deletion.

    Returns:
        True  if the file was successfully shredded.
        False if the file was not found or was empty.
    """

    # ── Pre-flight checks ─────────────────────────────────────────
    if not os.path.exists(filepath):
        print(f"[ERROR] File not found: {filepath}")
        return False

    file_size = os.path.getsize(filepath)

    if file_size == 0:
        print("[WARN]  File is empty — nothing to shred.")
        return False

    # ── Info banner ───────────────────────────────────────────────
    print(f"[INFO]  File   : {filepath}")
    print(f"[INFO]  Size   : {file_size:,} bytes")
    print(f"[INFO]  Passes : {passes}")
    print()

    # ── Overwrite passes ──────────────────────────────────────────
    with open(filepath, "r+b") as f:

        for i in range(passes):
            pattern = i % 3  # cycle through 0 → 1 → 2 → 0 …
            label = _pattern_label(pattern)
            print(f"  Pass {i + 1:02}/{passes:02} — {label}", end="", flush=True)

            f.seek(0)
            f.write(_generate_pattern(pattern, file_size))

            # Flush Python buffer then force OS to commit to disk.
            # os.fsync() is critical — without it the OS may cache
            # the write and never actually touch the storage medium.
            f.flush()
            os.fsync(f.fileno())

            print("  ✓")

        # ── Final pass (always random) ────────────────────────────
        # One last random pass after the cycle so the on-disk state
        # is never a predictable pattern (zeros or ones).
        print(f"  Final  — random bytes (flush + fsync)", end="", flush=True)
        f.seek(0)
        f.write(os.urandom(file_size))
        f.flush()
        os.fsync(f.fileno())
        print("  ✓")

    # ── Rename before delete ──────────────────────────────────────
    # Renaming to a random hex string obscures the original filename
    # in filesystem metadata / journal entries before removal.
    dir_name = os.path.dirname(os.path.abspath(filepath))
    random_name = os.path.join(dir_name, os.urandom(8).hex())
    os.rename(filepath, random_name)

    # ── Final delete ──────────────────────────────────────────────
    os.remove(random_name)

    print()
    print("[DONE]  File securely deleted.")
    return True


# ═══════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════


def _generate_pattern(pattern: int, size: int) -> bytes:
    """
    Return a bytes object of `size` bytes for the given pattern code.

    Args:
        pattern:  PATTERN_RANDOM | PATTERN_ZEROS | PATTERN_ONES
        size:     Number of bytes to generate.

    Returns:
        Bytes of the requested pattern and length.
    """
    if pattern == PATTERN_RANDOM:
        return os.urandom(size)  # cryptographically random
    elif pattern == PATTERN_ZEROS:
        return b"\x00" * size  # all zeros
    else:  # PATTERN_ONES
        return b"\xff" * size  # all ones


def _pattern_label(pattern: int) -> str:
    """Return a human-readable label for a pattern code."""
    labels = {
        PATTERN_RANDOM: "random bytes ",
        PATTERN_ZEROS: "zeros  (0x00)",
        PATTERN_ONES: "ones   (0xFF)",
    }
    return labels.get(pattern, "unknown")


# ═══════════════════════════════════════════════════════════════════
# UI — Confirmation prompt
# ═══════════════════════════════════════════════════════════════════


def warn_user(filepath: str) -> bool:
    """
    Print a warning banner and ask the user to confirm deletion.

    Args:
        filepath:  The path about to be shredded (shown to the user).

    Returns:
        True if the user typed 'yes', False otherwise.
    """
    print("=" * 52)
    print("   SECURE FILE SHREDDER")
    print("=" * 52)
    print(f"   Target  : {filepath}")
    print()
    print("   WARNING : This action is permanent and cannot")
    print("             be undone. The file will be overwritten")
    print("             multiple times and then deleted.")
    print()

    answer = input("   Type 'yes' to continue: ").strip().lower()
    return answer == "yes"


# ═══════════════════════════════════════════════════════════════════
# CLI — Argument parsing & entry point
# ═══════════════════════════════════════════════════════════════════


def _build_parser() -> argparse.ArgumentParser:
    """Configure and return the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="shredder",
        description=(
            "Securely shred a file by overwriting it multiple times\n"
            "with random data, zeros, and ones before deleting it.\n\n"
            "Inspired by DoD 5220.22-M erasure standards."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "examples:\n"
            "  python shredder.py secret.txt\n"
            "  python shredder.py secret.txt --passes 7\n"
            "  python shredder.py secret.txt --force\n"
        ),
    )

    parser.add_argument(
        "filepath",
        help="Path to the file to shred.",
    )
    parser.add_argument(
        "--passes",
        type=int,
        default=DEFAULT_PASSES,
        metavar="N",
        help=f"Number of overwrite passes (default: {DEFAULT_PASSES}).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip the confirmation prompt (use with care).",
    )

    return parser


def main() -> None:
    """Parse CLI arguments and run the shredder."""
    parser = _build_parser()
    args = parser.parse_args()

    # ── Confirmation gate ─────────────────────────────────────────
    if not args.force:
        if not warn_user(args.filepath):
            print()
            print("[CANCELLED] No files were deleted.")
            sys.exit(0)

    print()

    # ── Run shredder ──────────────────────────────────────────────
    success = overwrite_file(args.filepath, passes=args.passes)

    # Exit with a non-zero code on failure so scripts/CI can detect it
    if not success:
        sys.exit(1)


# ═══════════════════════════════════════════════════════════════════
# ENTRY POINT
# ═══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    main()
