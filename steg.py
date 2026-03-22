from reedsolo import RSCodec
import argparse
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

def get_shuffled_coords(width, height, password, verbose=False):
    coords = [(x, y) for y in range(height) for x in range(width)]
    
    seed_hash = hashes.Hash(hashes.SHA256())
    seed_hash.update(password.encode())
    seed = int.from_bytes(seed_hash.finalize(), 'big')
    
    random.seed(seed)
    random.shuffle(coords)
    
    if verbose:
        print(f"[*] Entropy: Shuffled {width*height} pixels with seed {seed % 10000}")
        
    return coords, seed # Return the seed so we can use it for channels

# --- STEGANOGRAPHY CORE ---
def encode(input_img_path, message, password, output_img_path, verbose=False):
    # --- STEP 1: METADATA STRIPPING (OPSEC) ---
    # We open the image and immediately copy only pixel data to a new object.
    # This prevents EXIF/Metadata from leaking into the output file.
    raw_img = Image.open(input_img_path).convert('RGB')
    img = raw_img.copy() 
    pixels = img.load()
    width, height = img.size
    
    # --- STEP 2: PREPARE DATA (ECC + ENCRYPTION) ---
    rs = RSCodec(10) # Reed-Solomon: adds 10 parity bytes
    ecc_data = rs.encode(message.encode())
    
    encrypted_blob = encrypt_data(ecc_data, password)
    header = format(len(encrypted_blob), '032b') 
    
    bit_stream = [int(b) for b in header]
    for byte in encrypted_blob:
        for bit in format(byte, '08b'):
            bit_stream.append(int(bit))
     
    # --- STEP 3: VISIBLE CAPACITY & DENSITY BLOCK ---
    total_slots = width * height * 3 
    required_bits = len(bit_stream)
    density = (required_bits / total_slots) * 100
    
    print(f"\n[*] Image Analysis:")
    print(f"    - Dimensions:      {width}x{height}")
    print(f"    - Total LSB Slots: {total_slots}")
    print(f"    - Required Bits:   {required_bits}")
    print(f"    - Stego Density:   {density:.4f}%")
    print(f"[*] OpSec: EXIF Metadata stripped successfully.")
    
    if required_bits > total_slots:
        print(f"[!] ERROR: Image too small! Required: {required_bits}, Available: {total_slots}")
        return False

    # --- STEP 4: EMBEDDING (SHUFFLED PIXELS + SHUFFLED CHANNELS) ---
    coords, seed = get_shuffled_coords(width, height, password, verbose)
    bit_idx = 0
    
    if verbose:
        print(f"[*] Embedding {len(bit_stream)} bits into pixels...")

    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        
        # CHANNEL SHUFFLE: Randomize RGB order for this specific pixel
        channel_order = [0, 1, 2]
        random.seed(seed + x + y) 
        random.shuffle(channel_order)
        
        for i in channel_order:
            if bit_idx < len(bit_stream):
                # Apply LSB change
                channels[i] = (channels[i] & ~1) | bit_stream[bit_idx]
                bit_idx += 1
                
        pixels[x, y] = tuple(channels)
        
        # Save and exit once all bits are hidden
        if bit_idx >= len(bit_stream):
            img.save(output_img_path, format="PNG", compress_level=0)
            if verbose:
                print(f"[+] Embedding complete. Output saved to {output_img_path}")
            return True
            
def decode(img_path, password, verbose=False):
    img = Image.open(img_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    
    # Get the coordinates and the seed for channel shuffling
    coords, seed = get_shuffled_coords(width, height, password, verbose)
    
    # --- PHASE 1: Extract 32-bit Header ---
    all_extracted_bits = []
    bit_limit = 32 
    bit_idx = 0
    
    if verbose: print("[*] Scanning image for encrypted headers...")

    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        
        # Match the channel shuffle from the encoder
        channel_order = [0, 1, 2]
        random.seed(seed + x + y)
        random.shuffle(channel_order)

        for i in channel_order:
            if bit_idx < bit_limit:
                all_extracted_bits.append(channels[i] & 1)
                bit_idx += 1
        if bit_idx >= bit_limit: break

    blob_len = int("".join(map(str, all_extracted_bits[:32])), 2)
    
    # --- PHASE 2: Extract Encrypted ECC Blob ---
    if verbose: print(f"[*] Found Payload: {blob_len} bytes. Commencing extraction...")

    bit_limit = 32 + (blob_len * 8)
    all_extracted_bits = []
    bit_idx = 0
    
    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        
        channel_order = [0, 1, 2]
        random.seed(seed + x + y)
        random.shuffle(channel_order)

        for i in channel_order:
            if bit_idx < bit_limit:
                all_extracted_bits.append(channels[i] & 1)
                bit_idx += 1
        if bit_idx >= bit_limit: break

    blob_bytes = bytearray()
    for i in range(32, len(all_extracted_bits), 8):
        blob_bytes.append(int("".join(map(str, all_extracted_bits[i:i+8])), 2))
    
    # Return the raw decrypted data (which still has ECC parity)
    return decrypt_data(bytes(blob_bytes), password)
    

def main():
    parser = argparse.ArgumentParser(
        prog="steg-afk",
        description="steg: hide in plain sight!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python3 steg.py encode -i input.png -m 'Secret' -p 'Pass123' -o output.png\n"
               "  python3 steg.py decode -i output.png -p 'Pass123'"
    )

    # Add Global Verbose Flag
    parser.add_argument("-v", "--verbose", action="store_true", help="Display coordinate mapping during process")

    subparsers = parser.add_subparsers(dest="mode", help="Execution Mode")

    # --- ENCODE HELP PAGE ---
    encode_parser = subparsers.add_parser("encode", help="Hide data inside an image")
    
    enc_req = encode_parser.add_argument_group("Required Arguments")
    enc_req.add_argument("-i", "--image", required=True, metavar="PATH", help="Source image (PNG recommended)")
    enc_req.add_argument("-m", "--message", required=True, metavar="TEXT", help="Secret message to hide")
    enc_req.add_argument("-p", "--password", required=True, metavar="PWD", help="Password for AES-GCM encryption")
    
    enc_opt = encode_parser.add_argument_group("Output Settings")
    enc_opt.add_argument("-o", "--output", default="hidden.png", metavar="FILE", help="Output filename (Default: hidden.png)")

    # --- DECODE HELP PAGE ---
    decode_parser = subparsers.add_parser("decode", help="Extract data from an image")
    
    dec_req = decode_parser.add_argument_group("Required Arguments")
    dec_req.add_argument("-i", "--image", required=True, metavar="PATH", help="Stego-image to decode")
    dec_req.add_argument("-p", "--password", required=True, metavar="PWD", help="Password used during encoding")

    # If no arguments are passed, show the help page
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    args = parser.parse_args()

    # --- ROUTING LOGIC ---
    if args.mode == "encode":
        if not os.path.exists(args.image):
            print(f"Error: {args.image} not found.")
            return
            
        # Pass args.verbose here
        if encode(args.image, args.message, args.password, args.output, verbose=args.verbose):
            print(f"Success! '{args.output}' now contains your secret.")
    
    elif args.mode == "decode":
            if not os.path.exists(args.image):
                print(f"Error: {args.image} not found.")
                return
                    
            try:
                # 1. Decrypt the raw blob
                decrypted_ecc_data = decode(args.image, args.password, verbose=args.verbose)
                
                # 2. Reed-Solomon Decode (This also checks integrity)
                rs = RSCodec(10)
                # This line will throw an error if the password was wrong
                final_message = rs.decode(decrypted_ecc_data)[0].decode()
                
                print(f"\n[+] DECODED MESSAGE: {final_message}")
                
            except Exception:
                # THE LOGIC BOMB: Show fake data on failure
                fake_results = [
                    "nice try, bitchh!.",
                    "Target: 192.168.1.108 | Status: Vulnerable",
                    "ERR_INTEGRITY_FAILURE: Auth Token Revoked",
                    "System Hash: 8b2f9a... [Encrypted]"
                ]
                print(f"\n[+] DECODED MESSAGE: {random.choice(fake_results)}")
            
if __name__ == "__main__":
    main()
