# File Shredder - Python

Overwrites a file multiple times with random/pattern data before
deleting it, making recovery significantly harder than a standard
delete operation.

Inspired by the DoD 5220.22-M and Gutmann erasure standards.

Author : Raymundo B.
Python : 3.14+
License : MIT
Usage : Open source tool for Windows, Linux, MacOS for safe deletion

**What I Learned:**

- Learned File Processing via Python
- Learned how to manipulate and randomize bytes to scramble.
- Learned how to perform several passes to a file
- Learned how to use argparse for terminal utilities

Usage:
`python shredder.py <filepath> [--passes N] [--force]`

Examples:

```bash
    python shredder.py secret.txt
    python shredder.py secret.txt --passes 7
    python shredder.py secret.txt --force
```
