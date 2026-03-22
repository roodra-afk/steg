# steg

# Advanced Image Steganography Tool

A secure command-line steganography tool written in Python that allows users to **hide encrypted messages inside images** using **Least Significant Bit (LSB) steganography** combined with **AES-256 encryption**.

Designed with a focus on **stealth, integrity, and cryptographic security**, this project demonstrates how modern cryptography and steganography can be combined to conceal information inside digital images with minimal visual distortion.

---

# Overview

This tool allows you to:

* Hide secret messages inside images
* Encrypt messages before embedding them
* Extract hidden messages using the correct password
* Analyze image capacity and embedding density

Unlike simple steganography tools, this implementation **encrypts the data before hiding it**, adding a strong security layer.

Even if hidden data is detected, it **cannot be decrypted without the correct password**.

---

# How It Works

The system operates in **two main stages**:

---

## 1. Encryption

Before embedding, the message is encrypted using:

* **AES-256 GCM (authenticated encryption)**
* **PBKDF2 key derivation (600,000 iterations)**
* Random **salt** and **nonce**

### Process:
1. User provides message and password
2. A cryptographic key is derived from the password
3. Message is encrypted securely
4. Encrypted data is prepared for embedding

---

## 2. Steganography (Randomized LSB Encoding)

The encrypted data is embedded using a **password-seeded pseudo-random process**:

1. The password is hashed to generate a deterministic seed
2. Pixel coordinates are shuffled based on that seed
3. Data bits are scattered across the image in a non-linear pattern

This ensures the embedded data resembles natural noise and avoids detectable patterns.

---

### Why Randomized LSB?

Sequential LSB encoding creates visible statistical patterns that can be detected using tools like **StegSolve**.

This implementation:

* Breaks spatial patterns in embedded data
* Distributes entropy across the entire image
* Reduces effectiveness of statistical attacks (e.g., Chi-square analysis)

---

## 3. Coordinate Generation

The embedding path is determined by:
```
Path = Shuffle(Coordinates, Seed(Hash(Password)))
```

Without the correct password, reconstructing the embedding path is computationally infeasible.

This adds an additional **obfuscation layer** on top of AES-GCM encryption.

---

## Visual Integrity

| Original Image | Stego Image (Encoded) |
| :---: | :---: |
| ![Original](./examples/cover.png) | ![Encoded](./examples/stego.png) |
| 0% Change | ~0.01% LSB Change |

*Even under magnification, modifications remain imperceptible to the human eye.*

---

# Message Structure Inside Image

The embedded payload structure:
```
[32-bit mask][32-bit masked_length][salt][nonce][encrypted payload]
```


The payload length is XOR-masked to prevent straightforward extraction or pattern detection.

---

# Image Capacity & Density Analysis

Before encoding, the tool evaluates:

* Image dimensions
* Total available LSB slots
* Required bits for payload
* Embedding density percentage

### Example Output:

```
[*] Image Analysis:

Dimensions: 1920x1080
Total LSB Slots: 6220800
Required Bits: 1024
Stego Density: 0.0164%
```


If density exceeds safe thresholds, the tool warns about potential detectability.

---

# Technologies Used

| Technology           | Purpose                              |
| -------------------- | ------------------------------------ |
| Python 3             | Core programming language            |
| Pillow (PIL)         | Image processing                     |
| cryptography library | Encryption and key derivation        |
| AES-256-GCM          | Authenticated encryption             |
| PBKDF2HMAC           | Password-based key derivation        |
| Reed-Solomon         | Error correction and integrity check |
| LSB Steganography    | Data embedding in image pixels       |

---

# Installation

## 1. Clone the repository
```
git clone https://github.com/roodra-afk/steg

cd steg
```


---

## 2. Install dependencies
```
pip install -r requirements.txt
```

---

# Usage

Run the tool via command-line arguments:

---

### Encode a Message
```
python3 steg.py encode -i input.png -m "Secret message" -p "password" -o output.png
```

---

### Decode a Message
```
python3 steg.py decode -i output.png -p "password"
```

---

## Example

### Encode:
```
python3 steg.py encode -i photo.png -m "This is classified" -p "myStrongPassword" -o hidden.png
```

### Decode:
```
python3 steg.py decode -i hidden.png -p "myStrongPassword"
```

---

# Security Features

* AES-256-GCM authenticated encryption
* PBKDF2 key derivation with 600,000 iterations
* Reed-Solomon error correction
* Password-seeded pixel shuffling
* Channel-level randomization
* Obfuscated payload length header
* Density-based detectability warning

---

# Limitations

* Optimized for **PNG images**
* Lossy formats (e.g., JPEG recompression) may destroy hidden data
* Very large payloads increase detection risk
* Requires correct password for both decoding and pixel mapping

---

# Integrity Verification (Optional)

To verify that the stego image has not been altered:
```
sha256sum output.png
```

Any modification will likely corrupt the hidden payload.

---

# Possible Improvements

Future enhancements could include:

* GUI or web interface
* Support for multiple file formats
* File embedding (not just text)
* Adaptive or edge-based embedding
* Advanced steganalysis resistance techniques

---

## ⚠️ Disclaimer

This tool is intended for **educational and research purposes only**.  
The author is not responsible for misuse. Always ensure proper authorization when working with data concealment techniques.
