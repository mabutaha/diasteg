# Examples

Three encoded texts with different secrets. Decode any of them with:

```bash
python diasteg.py solve examples/encoded_text_example1.txt
```

| File | Secret | Notes |
|------|--------|-------|
| `encoded_text_example1.txt` | `superdashsecretdashlinkdotcom` | LLM-generated carrier sentence |
| `encoded_text_example2.txt` | `exampledashserverdashsecretdotcom` | LLM-generated carrier sentence |
| `encoded_text_example3.txt` | `mooninkstorm` | Uses the Mu'allaqa of Imru' al-Qays as a carrier text |

**Note on Example 3:** The first 12 letters of the Mu'allaqa of Imru' al-Qays happen to satisfy the XOR constraint map for this chosen secret: `mooninkstorm` at offset zero. This means the poem works as a carrier directly. This is a coincidence, and not the general case. Most secrets will need a constrained carrier sentence (see examples 1 and 2). The writeup contains more details.

