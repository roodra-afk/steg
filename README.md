# stegx

**Advanced Image Steganography Tool**  
A secure, Python-based CLI to hide encrypted messages in images using *randomized LSB steganography* plus *AES-256* encryption.  
Minimizes visual distortion, maximizes stealth & security.

---

## Features

- Hide secret messages in PNG images
- AES-256-GCM encryption (with PBKDF2 key derivation, 600,000 rounds)
- Randomized, password-seeded LSB embedding to resist detection
- Reed-Solomon error correction for data integrity
- Capacity & density analysis with detectability warnings
- Visual integrity: changes are visually imperceptible
- Returns “honey-pot” data on wrong password (anti-forensics)
- CLI tool for encoding & decoding

---

## Installation

**Requirements:**  
- Python 3.8+  

**One-line install:**    
```bash
curl -sSL https://raw.githubusercontent.com/roodra-afk/stegx/main/install.sh | bash
```

---

## Usage

**Encode a message:**
```bash
stegx encode -i input.png -m "Your secret message" -p <password> -o output.png
```

**Decode a message:**
```bash
stegx decode -i output.png -p <password>
```

**Example:**
```bash
stegx encode -i photo.png -m "This is classified" -p myStrongPassword -o hidden.png
stegx decode -i hidden.png -p myStrongPassword
```

---

## How It Works

1. **Encryption**: Encrypts your message using AES-256-GCM. Keys are derived from your password via PBKDF2 (600,000 iterations), with a random salt & nonce.
2. **Embedding**: Data is scattered into image LSBs using a password-based pseudo-random order. LSB Matching is used for stealth—prevents PoV detection.
3. **Error Correction**: Reed-Solomon ECC enables recovery from minor image corruption.
4. **Obfuscation**: The structure `[32-bit mask][32-bit masked_length][salt][nonce][encrypted payload]` is XOR-masked to inhibit detection.

---

## Image Capacity & Density Analysis

Before embedding, the tool checks:

- Dimensions & available LSBs
- Payload size vs. capacity
- Embedding density percentage

**Sample output:**
```
[*] Image Analysis:
Dimensions: 1920x1080
Total LSB Slots: 6220800
Required Bits: 1024
Stego Density: 0.0164%
```
**Warning shown if capacity is exceeded or detectability risk is high.**

---

## Technologies Used

| Technology           | Purpose                              |
| -------------------- | ------------------------------------ |
| Python 3             | Core language                        |
| Pillow               | Image processing (PNG)               |
| cryptography         | Encryption, key derivation           |
| AES-256-GCM          | Authenticated encryption             |
| PBKDF2HMAC           | Key derivation                       |
| Reed-Solomon         | Error correction                     |
| LSB Steganography    | Data encoding                        |

---

## Limitations

- Optimized for **PNG** images
- Lossy formats (e.g. JPEG) destroy hidden data
- Large payloads increase detection risk
- Correct password required (for both decrypting and mapping)
- Not (yet) a general file-in-image embedder

---

## Integrity Verification

To check image integrity:
```bash
sha256sum output.png
```
Any change likely corrupts the hidden payload.

---

## Possible Improvements

- GUI/web interface
- Multi-format (JPEG, BMP, etc.) support
- File embedding
- Adaptive/edge-based embedding
- Enhanced steganalysis resistance

---

## ⚠️ Disclaimer

**For educational and research use only.  
Do not use for unauthorized data concealment.**

---

## Visual Example

| Original Image | Stego Image (Encoded) |
|:--------------:|:--------------------:|
| ![Original](./examples/cover.png) | ![Encoded](./examples/stego.png) |
| 0% Change      | ~0.01% LSB Change    |

*Pixel-level changes are imperceptible even under magnification.*

---

