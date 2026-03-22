import numpy as np
import random
import sys
from PIL import ImageOps
import os
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# --- ENCRYPTION HELPERS ---
def derive_key(password: str, salt: bytes):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(password.encode())

def encrypt_data(data: bytes, password: str):
    salt, nonce = os.urandom(16), os.urandom(12)
    key = derive_key(password, salt)
    return salt + nonce + AESGCM(key).encrypt(nonce, data, None)

def decrypt_data(combined: bytes, password: str):
    salt, nonce, ciphertext = combined[:16], combined[16:28], combined[28:]
    key = derive_key(password, salt)
    return AESGCM(key).decrypt(nonce, ciphertext, None)

def get_shuffled_coords(width, height, password):
    # Create a list of all possible (x, y) coordinates
    coords = [(x, y) for y in range(height) for x in range(width)]
    
    # Use a hash of the password as the seed for the PRNG
    seed_hash = hashes.Hash(hashes.SHA256())
    seed_hash.update(password.encode())
    seed = int.from_bytes(seed_hash.finalize(), 'big')
    
    random.seed(seed)
    random.shuffle(coords)
    return coords

# --- STEGANOGRAPHY CORE ---
def encode(input_img_path, message, password, output_img_path):
    img = Image.open(input_img_path).convert('RGB')
    img = ImageOps.exif_transpose(img) # Fixes orientation
    data = np.array(img).flatten().tolist()
    img = Image.new(img.mode, img.size) # This creates a "clean" copy without metadata
    img.putdata(data)
    pixels = img.load()
    width, height = img.size
    
    # --- VISIBLE CAPACITY & DENSITY BLOCK ---
    total_slots = width * height * 3 
    overhead_bits = 384
    message_bits = len(message.encode()) * 8
    required_bits = overhead_bits + message_bits
    
    # Calculate density (How much of the total image are we changing?)
    density = (required_bits / total_slots) * 100
    
    print(f"\n[*] Image Analysis:")
    print(f"    - Dimensions:      {width}x{height}")
    print(f"    - Total LSB Slots: {total_slots}")
    print(f"    - Required Bits:   {required_bits}")
    print(f"    - Stego Density:   {density:.4f}%") # Shows 4 decimal places
    print(f"[*] OpSec: EXIF Metadata stripped successfully.")

    
    if required_bits > total_slots:
        max_chars = (total_slots - 384) // 8
        print(f"[!] ERROR: Image too small! Max: {max_chars} chars.")
        return False
    
    # Warning for high density
    if density > 10.0:
        print(f"[!] WARNING: High density ({density:.2f}%). This may be detectable by steganalysis.")
    else:
        print(f"    - Status: Optimal density. Highly covert.")
    # --- END VISIBLE CAPACITY BLOCK ---
    
    encrypted_blob = encrypt_data(message.encode(), password)
    header = format(len(encrypted_blob), '032b') 
    
    bit_stream = [int(b) for b in header]
    for byte in encrypted_blob:
        for bit in format(byte, '08b'):
            bit_stream.append(int(bit))

    if len(bit_stream) > width * height * 3:
        print(f"Error: Message too long! Max capacity is {((width*height*3)-416)//8} bytes.")
        return False

    coords = get_shuffled_coords(width, height, password)
    bit_idx = 0
    
    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        for i in range(3):
            if bit_idx < len(bit_stream):
                channels[i] = (channels[i] & ~1) | bit_stream[bit_idx]
                bit_idx += 1
            
        pixels[x, y] = tuple(channels)
        if bit_idx >= len(bit_stream):
            img.save(output_img_path, format="PNG")
            return True

def decode(img_path, password):
    img = Image.open(img_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    
    # Get the exact same shuffled path using the password
    coords = get_shuffled_coords(width, height, password)
    
    # 1. Extract length header (32 bits)
    all_extracted_bits = []
    bit_limit = 32  # Start by getting the header
    bit_idx = 0
    
    for x, y in coords:
        r, g, b = pixels[x, y]
        for c in [r, g, b]:
            if bit_idx < bit_limit:
                all_extracted_bits.append(c & 1)
                bit_idx += 1
        if bit_idx >= bit_limit: break

    blob_len = int("".join(map(str, all_extracted_bits[:32])), 2)
    
    # 2. Extract encrypted blob (reset and get the full stream)
    bit_limit = 32 + (blob_len * 8)
    all_extracted_bits = []
    bit_idx = 0
    
    for x, y in coords:
        r, g, b = pixels[x, y]
        for c in [r, g, b]:
            if bit_idx < bit_limit:
                all_extracted_bits.append(c & 1)
                bit_idx += 1
        if bit_idx >= bit_limit: break

    blob_bytes = bytearray()
    for i in range(32, len(all_extracted_bits), 8):
        blob_bytes.append(int("".join(map(str, all_extracted_bits[i:i+8])), 2))
    
    return decrypt_data(bytes(blob_bytes), password).decode() 

# --- INTERACTIVE CLI ---
if __name__ == "__main__":
    print("--- Custom Image Steganography Tool ---")
    mode = input("Choose mode (encode/decode): ").strip().lower()

    if mode == "encode":
        in_file = input("Enter path to your custom image (e.g., my_photo.png): ")
        if not img_path.lower().endswith('.png'):
            print("[!] Warning: Steganography is most reliable with PNG. JPEG may lose data.")
        if not os.path.exists(in_file):
            print("Error: File not found.")
            sys.exit()
            
        secret = input("Enter the secret message: ")
        pwd = input("Enter a password to encrypt the message: ")
        out_file = input("Enter name for the output image (e.g., hidden.png): ")
        
        if encode(in_file, secret, pwd, out_file):
            print(f"Success! '{out_file}' now contains your secret.")

    elif mode == "decode":
        target = input("Enter path to the image you want to decode: ")
        if not os.path.exists(target):
            print("Error: File not found.")
            sys.exit()
            
        pwd = input("Enter the password: ")
        try:
            result = decode(target, pwd)
            print(f"\n[+] DECODED MESSAGE: {result}")
        except Exception:
            print("\n[-] Error: Decryption failed. Wrong password or damaged image.")
    else:
        print("Invalid mode selection.")
