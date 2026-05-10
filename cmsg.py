#!/usr/bin/env python3
# Written by AI, just for fun.
# Sometimes we don't need a commit message, so, just a random one is fine.
import requests
import sys
import string

URL = "https://whatthecommit.com/index.txt"

def is_ascii(s):
    try:
        s.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False

def main():
    try:
        resp = requests.get(URL, timeout=5)
        resp.raise_for_status()
        content = resp.text.strip()
    except Exception as e:
        print(f"Error fetching content: {e}", file=sys.stderr)
        sys.exit(1)

    # Check ASCII
    if not is_ascii(content):
        print("Error: Content is not pure ASCII.", file=sys.stderr)
        sys.exit(2)

    # Check for forbidden characters
    forbidden = {'$', '`','\\'}
    if any(c in content for c in forbidden):
        print("Error: Content contains forbidden characters ($ or `).", file=sys.stderr)
        sys.exit(3)

    # Additional shell safety: check for newlines and control chars
    if any(ord(c) < 32 and c not in '\t\n\r' for c in content):
        print("Error: Content contains control characters.", file=sys.stderr)
        sys.exit(4)

    print(content)

if __name__ == "__main__":
    main()