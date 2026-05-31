#!/usr/bin/env python3
"""
Diasteg: Arabic Diacritic Steganography — Encoder & Solver

Exploits a Unicode range property: Arabic letters (U+0621–U+064A) ⊕ Arabic
letters always produce values in 0x00–0x7F, covering all of lowercase a–z
plus a handful of symbols. This allows hiding English messages inside Arabic
text using diacritics as the covert channel.

Encoding:
  1. The first N letters of a diacritized carrier text are M1.
  2. The key K is computed: K[i] = M1[i] ⊕ secret[i].
  3. K is found as a subsequence among diacritized letters in the carrier.
  4. All diacritics are stripped; only the subsequence positions keep theirs.

Decoding:
  1. Extract all Arabic letters → M1.
  2. Extract diacritized letters (U+064B–U+0652) in order → K.
  3. secret[i] = chr(ord(M1[i]) ⊕ ord(K[i])).

Usage:
  python arabic_stego.py encode carrier.txt "secret" -o stego.txt
  python arabic_stego.py solve stego.txt
  
This implementation was prepared with the help of Claude Opus.
"""

import sys
import argparse
from collections import Counter

# Codepoints to skip: tatweel (U+0640) and unassigned slots (U+063B–U+063F).
EXCLUDED = {0x0640} | set(range(0x063B, 0x0640))

# Arabic diacritics / harakat (U+064B–U+0652): fathatan through sukun.
DIACRITICS = set(chr(c) for c in range(0x064B, 0x0653))



def is_arabic_letter(ch):
    """Return True if ch is an Arabic letter in the Basic Arabic block."""
    cp = ord(ch)
    return 0x0621 <= cp <= 0x064A and cp not in EXCLUDED


def parse(text):
    """Split Arabic text into segments of (type, char, [diacritics]).

    Type is 'L' for a letter (with any trailing diacritics collected)
    or 'O' for any other character (spaces, punctuation, etc.).
    """
    segments = []
    i = 0
    while i < len(text):
        ch = text[i]
        if is_arabic_letter(ch):
            marks = []
            j = i + 1
            while j < len(text) and text[j] in DIACRITICS:
                marks.append(text[j])
                j += 1
            segments.append(('L', ch, marks))
            i = j
        elif ch in DIACRITICS:
            i += 1
        else:
            segments.append(('O', ch, []))
            i += 1
    return segments


def _find_subsequence(diac_pool, key):
    """Find key as a subsequence in the diacritized pool.

    Returns list of pool indices on success, or raises ValueError with
    diagnostic info on failure.
    """
    positions = []
    j = 0
    for ki, target in enumerate(key):
        found = False
        while j < len(diac_pool):
            if diac_pool[j][1] == target:
                positions.append(j)
                j += 1
                found = True
                break
            j += 1
        if not found:
            full_pool = Counter(l for _, l in diac_pool)
            remaining_key = key[ki:]
            needed = Counter(remaining_key)

            msg = f"Subsequence match failed at key position {ki} ('{target}').\n"
            msg += f"  Pool: {j}/{len(diac_pool)} entries consumed finding {ki}/{len(key)} key letters.\n"
            msg += f"  Remaining key ({len(remaining_key)} letters): {''.join(remaining_key)}\n\n"

            scarce = [(l, n, full_pool.get(l, 0))
                      for l, n in needed.most_common()
                      if full_pool.get(l, 0) < n]
            if scarce:
                msg += "  Scarce/missing letters in pool:\n"
                for letter, need, have in scarce:
                    label = "MISSING" if have == 0 else "SCARCE"
                    msg += f"    '{letter}' — need {need}, pool has {have} ({label})\n"

            msg += "\n  Tip: use a longer carrier text with more letter diversity."
            raise ValueError(msg)

    return positions


def encode(carrier_text, secret):
    """Encode a secret message into a diacritized Arabic carrier text.

    Returns (stego_text, key_string, diacritic_count).
    """
    segments = parse(carrier_text)
    letter_segs = [(idx, seg) for idx, seg in enumerate(segments) if seg[0] == 'L']
    all_letters = [seg[1] for _, seg in letter_segs]

    if len(all_letters) < len(secret):
        raise ValueError(f"Carrier too short: {len(all_letters)} letters < {len(secret)}")

    # Compute key: K[i] = M1[i] ⊕ secret[i]
    key = []
    for i, sch in enumerate(secret):
        k_val = ord(all_letters[i]) ^ ord(sch)
        k_ch = chr(k_val)
        if not is_arabic_letter(k_ch):
            raise ValueError(
                f"Position {i}: '{all_letters[i]}' ⊕ '{sch}' = U+{k_val:04X} "
                f"— not a valid Arabic letter. Carrier doesn't satisfy constraints.\n"
                f"  Use validate_carrier.py to generate a valid opening sentence."
            )
        key.append(k_ch)

    # Find key as a subsequence in the diacritized pool
    diac_pool = [(li, seg[1]) for li, (idx, seg) in enumerate(letter_segs) if seg[2]]
    positions = _find_subsequence(diac_pool, key)

    # Build stego: keep diacritics only at matched positions
    keep = set()
    for p in positions:
        li = diac_pool[p][0]
        seg_idx = letter_segs[li][0]
        keep.add(seg_idx)

    result = []
    for idx, seg in enumerate(segments):
        if seg[0] == 'L':
            result.append(seg[1])
            if idx in keep:
                result.extend(seg[2])
        else:
            result.append(seg[1])

    stego = ''.join(result)
    diac_count = sum(1 for ch in stego if ch in DIACRITICS)
    return stego, ''.join(key), diac_count


def solve(stego_text):
    """Extract the hidden message from a stego text.

    Returns the decoded secret string.
    """
    # Only standard harakat (U+064B–U+0652) count as diacritic markers.
    # Other Arabic combining marks (dagger alif U+0670, alef wasla U+0671,
    # etc.) may appear in the text but are ignored — they serve as natural
    # camouflage, not as key carriers.
    letters = []   # all Arabic letters in order (M1)
    key = []       # the subset carrying a harakat diacritic (K)
    for i, ch in enumerate(stego_text):
        if is_arabic_letter(ch):
            has_diac = (i + 1 < len(stego_text) and stego_text[i + 1] in DIACRITICS)
            letters.append(ch)
            if has_diac:
                key.append(ch)

    if not key:
        return "(no diacritized letters found)"

    # Decode: secret[i] = M1[i] ⊕ K[i] for the first len(K) letters.
    # This works because the secret was encoded starting at M1[0], so the
    # first len(K) letters of M1 are the ones that were ⊕-ed with the secret.
    decoded = ''.join(chr(ord(letters[i]) ^ ord(key[i])) for i in range(len(key)))

    if all(0x20 <= ord(c) < 0x7F for c in decoded):
        return decoded
    return f"(non-ASCII result): {decoded}"


def main():
    parser = argparse.ArgumentParser(
        description='Arabic Diacritic Steganography — Encoder & Solver'
    )
    sub = parser.add_subparsers(dest='mode')

    enc = sub.add_parser('encode', help='Hide a message in a carrier text')
    enc.add_argument('carrier', help='Diacritized Arabic text file')
    enc.add_argument('secret', help='Secret message (lowercase a–z, {|}~`)')
    enc.add_argument('-o', '--output', default='stego.txt', help='Output path')

    slv = sub.add_parser('solve', help='Extract hidden message from stego text')
    slv.add_argument('stego', help='Stego text file')

    args = parser.parse_args()

    if args.mode == 'encode':
        with open(args.carrier, encoding='utf-8') as f:
            carrier = f.read()

        try:
            stego, key, diac_count = encode(carrier, args.secret)
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(stego)

        print(f"Secret:     {args.secret}")
        print(f"Key:        {key}")
        print(f"Diacritics: {diac_count}")
        print(f"Output:     {args.output}")

        recovered = solve(stego)
        print(f"Verify:     {recovered}")
        print(f"Match:      {'✓' if recovered == args.secret else '✗'}")

    elif args.mode == 'solve':
        with open(args.stego, encoding='utf-8') as f:
            stego = f.read()
        print(solve(stego))

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
