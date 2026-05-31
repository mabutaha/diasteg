#!/usr/bin/env python3
"""
Diasteg: Arabic Diacritic Steganography — Carrier Sentence Validator

Generates the constraint map for a secret message and validates candidate
Arabic sentences against it. The first N Arabic letters of the sentence
must each come from a position-specific set of allowed letters so that
M1[i] ⊕ secret[i] always produces a valid, commonly-diacritized Arabic letter.

Usage:
  python validate_carrier.py                          # show constraint map + prompt
  python validate_carrier.py "arabic sentence"        # validate a sentence
  python validate_carrier.py -s "newsecret"           # use a different secret
  python validate_carrier.py -s "newsecret" "sentence"
  
This implementation was prepared with the help of Claude Opus.
"""

import sys
import argparse

# Codepoints to skip in the carrier: tatweel and unassigned slots.
EXCLUDED = {0x0640} | set(range(0x063B, 0x0640))

# Key values must also avoid letters that are rarely/never diacritized
# in standard Arabic text, since they won't appear in the diacritized pool.
#   U+0627 ا  alef          — never carries harakat
#   U+0649 ى  alef maksura  — never carries harakat
#   U+0622 آ  alef madda    — never diacritized
#   U+0624 ؤ  hamza on waw  — extremely rare in diacritized text
EXCLUDED_KEY = EXCLUDED | {0x0627, 0x0649, 0x0622, 0x0624}

DEFAULT_SECRET = "exampledashserverdashsecretdotcom"


def is_arabic_letter(ch):
    cp = ord(ch)
    return 0x0621 <= cp <= 0x064A and cp not in EXCLUDED


def compute_constraints(secret):
    """For each secret character, compute which Arabic letters are valid M1 choices.

    A letter is valid at position i if M1[i] ⊕ secret[i] produces a codepoint
    that is both a valid Arabic letter and commonly diacritized (not in EXCLUDED_KEY).
    """
    constraints = []
    for fch in secret:
        valid = set()
        for a in range(0x0621, 0x064B):
            if a in EXCLUDED:
                continue
            k = a ^ ord(fch)
            if 0x0621 <= k <= 0x064A and k not in EXCLUDED_KEY:
                valid.add(chr(a))
        constraints.append(valid)
    return constraints


def validate(sentence, secret):
    """Check if a sentence satisfies all constraints.

    Returns (success: bool, message: str).
    """
    letters = [ch for ch in sentence if is_arabic_letter(ch)]
    constraints = compute_constraints(secret)

    if len(letters) < len(secret):
        return False, f"Not enough Arabic letters: {len(letters)} < {len(secret)}"

    violations = []
    for i in range(len(secret)):
        if letters[i] not in constraints[i]:
            violations.append((i, letters[i], secret[i], constraints[i]))

    if violations:
        msg = f"{len(violations)} violation(s):\n"
        for pos, got, need_for, allowed in violations:
            msg += f"  Position {pos} (for '{need_for}'): got '{got}', need one of: {''.join(sorted(allowed, key=ord))}\n"
        return False, msg

    # Verify ⊕
    m1 = letters[:len(secret)]
    key = [chr(ord(m1[i]) ^ ord(secret[i])) for i in range(len(secret))]
    decoded = ''.join(chr(ord(m1[i]) ^ ord(key[i])) for i in range(len(key)))

    return True, f"VALID — decoded: {decoded}"


def format_constraint_map(secret):
    """Return the constraint map as a formatted string."""
    constraints = compute_constraints(secret)
    lines = [f"Constraint map for: {secret}", f"Length: {len(secret)} letters", ""]
    for i, (fch, valid) in enumerate(zip(secret, constraints)):
        sorted_valid = ''.join(sorted(valid, key=ord))
        lines.append(f"  Position {i:>2} ({fch}): {sorted_valid}  [{len(valid)} options]")
    return '\n'.join(lines)


def generate_prompt(secret):
    """Generate an LLM prompt that asks for a valid carrier sentence."""
    constraints = compute_constraints(secret)
    prompt = f"Write a single Arabic sentence that is exactly {len(secret)} Arabic letters long.\n"
    prompt += "Letters only — spaces, diacritics, and punctuation do NOT count.\n\n"
    prompt += "Each letter position must use one of the allowed letters below.\n"
    prompt += "The sentence must be natural, grammatical Modern Standard Arabic.\n\n"
    prompt += "CONSTRAINT MAP:\n"
    for i, (fch, valid) in enumerate(zip(secret, constraints)):
        sorted_valid = ''.join(sorted(valid, key=ord))
        prompt += f"  Position {i:>2}: {sorted_valid}\n"
    prompt += "\nRULES:\n"
    prompt += f"- Exactly {len(secret)} Arabic letters (no more, no less)\n"
    prompt += "- Each letter from the allowed set for its position\n"
    prompt += "- Spaces, commas, periods, diacritics are free\n"
    prompt += "- Natural Arabic — should read like a real sentence\n"
    prompt += "- No non-Arabic characters\n\n"
    prompt += "Return ONLY the Arabic sentence, nothing else.\n"
    return prompt


def main():
    parser = argparse.ArgumentParser(
        description='Arabic Diacritic Steganography — Carrier Validator'
    )
    parser.add_argument('sentence', nargs='?', help='Arabic sentence to validate')
    parser.add_argument('-s', '--secret', default=DEFAULT_SECRET,
                        help=f'Secret message (default: {DEFAULT_SECRET})')
    parser.add_argument('--prompt', action='store_true',
                        help='Print the LLM prompt for generating a valid sentence')
    args = parser.parse_args()

    if args.sentence:
        success, msg = validate(args.sentence, args.secret)
        print(f"{'✓' if success else '✗'} {msg}")
        sys.exit(0 if success else 1)

    # Info mode
    print("=" * 60)
    print("ARABIC DIACRITIC STEGANOGRAPHY — CARRIER VALIDATOR")
    print("=" * 60)
    print()
    print(format_constraint_map(args.secret))

    if args.prompt:
        print("\n" + "=" * 60)
        print("LLM PROMPT")
        print("=" * 60)
        print(generate_prompt(args.secret))

    print(f"\nTo validate:  python {sys.argv[0]} \"your arabic sentence\"")
    print(f"To see prompt: python {sys.argv[0]} --prompt")
    if args.secret == DEFAULT_SECRET:
        print(f"Custom secret: python {sys.argv[0]} -s \"yoursecret\" \"sentence\"")


if __name__ == '__main__':
    main()
