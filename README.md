# steg

# Custom Image Steganography Tool

A secure command-line steganography tool written in Python that allows users to **hide encrypted messages inside images** using **Least Significant Bit (LSB) steganography** combined with **AES-256 encryption**.

This project demonstrates how **cryptography and steganography** can be combined to securely conceal information inside digital images while maintaining minimal visual distortion.

---

# Overview

This tool allows you to:

* Hide secret messages inside images
* Encrypt messages before embedding them
* Extract hidden messages using the correct password
* Analyze image capacity and embedding density

Unlike simple steganography tools, this implementation **encrypts the data before hiding it**, providing an additional security layer.

Even if someone detects hidden data, they **cannot read the message without the password**.

---

# How It Works

The system works in **two main stages**:

## 1. Encryption

Before embedding the message, the script encrypts it using:

* **AES-256 GCM encryption**
* **PBKDF2 password-based key derivation**
* Random **salt** and **nonce**

Process:

1. User enters a secret message and password
2. A cryptographic key is derived from the password
3. The message is encrypted
4. The encrypted blob is prepared for embedding

---

## 2. Steganography (Randomized LSB Encoding)

The encrypted data is hidden using a **Password-Seeded PRNG (Pseudo-Random Number Generator)**.

Instead of hiding data in a predictable line from top-to-bottom, the script:
1.  **Hashes your password** to create a unique mathematical seed.
2.  **Shuffles the pixel coordinates** of the entire image based on that seed.
3.  **Scatters the message bits** across the image in a random-looking pattern.

This makes the hidden data look like natural "sensor noise" to forensic tools, making it much harder to detect with visual or statistical attacks.

---

### Why Randomized LSB?
Sequential LSB (hiding bits in a row) creates a "signature" in the image's bit-planes. An attacker using a tool like **StegSolve** can easily see a horizontal bar of noise at the top of the image.

By using a **Password-Seeded PRNG Shuffle**, this tool:
* Destroys the spatial correlation of the hidden data.
* Spreads the "entropy" across the entire image.
* Ensures that even a Chi-square statistical attack cannot easily distinguish the hidden bits from natural camera sensor noise.

---

#### 3. Mathematical Integrity
The pixel path is generated using:
$Path = Shuffle(Coordinates, Seed(Hash(Password)))$  
Without the 256-bit hash of the password, the coordinate map is mathematically impossible to reconstruct, adding a layer of **Security through Obscurity** on top of our **AES-GCM encryption**.

---

### Visual Integrity
| Original Image | Stego Image (Encoded) |
| :---: | :---: |
| ![Original](./examples/cover.png) | ![Encoded](./examples/stego.png) |
| 0% Change | 0.0164% LSB Change |
*Note: Even at high magnification, the LSB modification remains invisible to the human eye.*

---

## Message Structure Inside Image

The embedded data contains:

```
[32-bit header][salt][nonce][encrypted message]
```

The **32-bit header** stores the length of the encrypted payload so the decoder knows how many bits to extract.

---

# Image Capacity & Density Analysis

Before encoding, the tool analyzes the image:

* Image dimensions
* Total available LSB slots
* Required bits for the message
* Steganographic density percentage

Example output:

```
[*] Image Analysis:
- Dimensions:      1920x1080
- Total LSB Slots: 6220800
- Required Bits:   1024
- Stego Density:   0.0164%
```

If density becomes too high (>10%), the tool warns that **steganalysis may detect the hidden data**.

---

# Technologies Used

| Technology           | Purpose                              |
| -------------------- | ------------------------------------ |
| Python 3             | Core programming language            |
| Pillow (PIL)         | Image processing                     |
| cryptography library | AES encryption and key derivation    |
| AES-256-GCM          | Authenticated encryption             |
| PBKDF2HMAC           | Secure password-based key derivation |
| LSB Steganography    | Hiding data inside image pixels      |

---

## ⚠️ Disclaimer
This tool is for **educational and research purposes only**. The author is not responsible for any misuse of this software. Always ensure you have explicit permission before performing any security testing or data hiding on systems you do not own.

---

# Installation

## 1. Clone the repository

```
git clone https://github.com/roodra-afk/steg
cd steg
```

## 2. Install dependencies

```
pip install pillow cryptography
```

Or using requirements:

```
pip install -r requirements.txt
```

Example `requirements.txt`:

```
pillow
cryptography
```

---

# Usage

Run the script using Python:

```
python steg.py
```

You will be prompted to choose a mode.

---

# Encode a Secret Message

Choose:

```
encode
```

Then enter:

* Input image path
* Secret message
* Password
* Output image name

Example:

```
Choose mode (encode/decode): encode
Enter path to your custom image: photo.png
Enter the secret message: This is classified
Enter a password: myStrongPassword
Enter name for the output image: hidden.png
```

Output:

```
Success! 'hidden.png' now contains your secret.
```

---

# Decode a Hidden Message

Choose:

```
decode
```

Then enter:

* Encoded image
* Password

Example:

```
Choose mode (encode/decode): decode
Enter path to the image you want to decode: hidden.png
Enter the password: myStrongPassword
```

Output:

```
[+] DECODED MESSAGE: This is classified
```

If the password is incorrect or the image is corrupted:

```
[-] Error: Decryption failed. Wrong password or damaged image.
```

---

# Security Features

* PRNG-Based Bit Shuffling: Uses a password-seeded shuffle to scatter data, bypassing first-order statistical steganalysis.
* AES-256-GCM authenticated encryption
* PBKDF2 key derivation with 100,000 iterations
* Random cryptographic salt
* Random nonce generation
* Message length header validation
* Density warning to reduce detectability

---

# Limitations

* Works best with **PNG images**
* Image compression (like JPEG recompression) may destroy hidden data
* Extremely large messages may increase detection risk

---

# Possible Improvements

Future enhancements could include:

* Support for multiple image formats
* GUI interface
* File embedding instead of text only
* Advanced steganalysis resistance

---
