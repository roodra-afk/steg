import sys
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

# --- STEGANOGRAPHY CORE ---
def encode(input_img_path, message, password, output_img_path):
    img = Image.open(input_img_path).convert('RGB')
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

    bit_idx = 0
    for y in range(height):
        for x in range(width):
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
    
    # 1. Extract length header (32 bits)
    header_bits = []
    bit_count = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for c in [r, g, b]:
                if bit_count < 32:
                    header_bits.append(c & 1)
                    bit_count += 1
            if bit_count >= 32: break
        if bit_count >= 32: break

    blob_len = int("".join(map(str, header_bits)), 2)
    
    # 2. Extract encrypted blob
    all_bits = []
    bit_limit = 32 + (blob_len * 8)
    bit_idx = 0
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            for c in [r, g, b]:
                if bit_idx < bit_limit:
                    all_bits.append(c & 1)
                    bit_idx += 1
            if bit_idx >= bit_limit: break
        if bit_idx >= bit_limit: break

    blob_bytes = bytearray()
    for i in range(32, len(all_bits), 8):
        blob_bytes.append(int("".join(map(str, all_bits[i:i+8])), 2))
    
    return decrypt_data(bytes(blob_bytes), password).decode()

# --- INTERACTIVE CLI ---
if __name__ == "__main__":
    print("--- Custom Image Steganography Tool ---")
    mode = input("Choose mode (encode/decode): ").strip().lower()

    if mode == "encode":
        in_file = input("Enter path to your custom image (e.g., my_photo.png): ")
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
