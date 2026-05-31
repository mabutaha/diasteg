# diasteg
By exploiting a quirk that involves XORing Arabic Unicode codepoints together, you can hide English messages inside Arabic text by using diacritics as a covert channel. `diasteg` is an implementation of this steganographic technique. 

The output is a partially diacritized Arabic text that is fully self-contained. Check the examples folder.
 
📜 Full writeup and explanation on my blog:  
[Unicode XOR Magic: Steganography with Arabic Diacritics](https://mabutaha.me/posts/diasteg/)

<div dir="rtl" align="right">

من خلال استغلال خاصية غير متوقعة تظهر عند تطبيق عملية XOR بين الحروف العربية في Unicode، يمكن إخفاء رسائل باللغة الإنجليزية داخل نص عربي، وذلك باستخدام التشكيل العربي كقناة خفية لنقل الرسالة.
</div>
<div dir="rtl" align="right">
diasteg هو تطبيق عملي لهذه التقنية في مجال إخفاء البيانات (Steganography). ويكون الناتج نصًا عربيًا مستقلاً بذاته مع بعض التشكيل، وتكون الرسالة المخفية مضمَّنة في التشكيل.
</div>
<br>

## Quick Start

**1. Generate a constraint map for your secret:**

This prints which Arabic letters are valid at each position, and optionally generates a prompt you can feed to an LLM.
```bash
python validate_carrier.py -s "mysecretmessage" --prompt
```
 You can  use the constraint map to write the sentence yourself, or find an existing Arabic text whose opening letters happen to satisfy the constraints (see Example 3).

**2. Get a valid opening sentence**: 

write one yourself, use an LLM, or find an existing text that already fits (see Example 3). Validate it by:
```bash
python validate_carrier.py -s "mysecretmessage" "الجملة العربية هنا"
```
From personal experience, Gemini worked best for constrained Arabic writing. Particularly 3.5 Flash and 3.1 Pro.

**3. Build the carrier.txt.** 

Append a longer fully-diacritized Arabic text after the validated sentence (anything relevant, the longer the better). The opening sentence must satisfy the constraints; the rest just needs to be a fully (or mostly) diacritized article.

*Note: For some secrets, existing Arabic texts may already satisfy the constraints at the right positions with the right secret message, so you wouldn't need this whole step. See Example 3.*

**4. Encode:**

```bash
python diasteg.py encode carrier.txt "mysecretmessage" -o stego.txt
```
It should output a success message. The output is a text file containing diacritized text. If there's an error, your article is probably not long enough (i.e. there's not enough diacritized letters to form the key subsequence).

**5. Decode:**

```bash
python diasteg.py solve stego.txt
```
XORing the letters of the Arabic text against the letters marked by the diacritics should retrieve the secret correctly. 
