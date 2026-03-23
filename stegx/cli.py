#!/usr/bin/env python3

import os
import sys
import random
import argparse
from PIL import Image
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from reedsolo import RSCodec
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(force_terminal=True) if os.name == 'nt' else Console()

def brand():
    banner = """
[bold red]
       ███████ ████████ ███████  ██████  ██   ██ 
      ██          ██    ██      ██        ██ ██  
      ███████     ██    █████   ██   ███   ███   
           ██     ██    ██      ██    ██  ██ ██  
      ███████     ██    ███████  ██████  ██   ██ 
[/bold red]
[bold white]        > Advanced Steganography Suite < [/bold white]
[cyan]          Project Name: stegx | v0.1.2 [/cyan]
    """
    console.print(Panel.fit(banner, border_style="bright_blue", subtitle="[bold white]roodra-afk[/bold white]"))

def derive_key(password: str, salt: bytes):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=600000)
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
    rng = random.Random(seed)
    rng.shuffle(coords)
    
    if verbose:
        console.print(f"[blue][*][/blue] Entropy: Shuffled {width*height} pixels with seed {seed % 10000}")
    return coords, seed

def encode(input_img_path, message, password, output_img_path, verbose=False):
    if not input_img_path.lower().endswith(".png"):
        console.print("[bold red][!] Error: Only PNG is supported to prevent data loss.[/bold red]")
        return False

    raw_img = Image.open(input_img_path).convert('RGB')
    img = raw_img.copy()
    pixels = img.load()
    width, height = img.size

    parity = random.randint(8, 16)
    rs = RSCodec(parity)
    ecc_data = b"STEG" + bytes([parity]) + rs.encode(message.encode())
    encrypted_blob = encrypt_data(ecc_data, password)

    mask = int.from_bytes(os.urandom(4), 'big')
    masked_len = len(encrypted_blob) ^ mask
    header_bits = format(mask, '032b') + format(masked_len, '032b')

    bit_stream = [int(b) for b in header_bits]
    bit_stream.extend([(byte >> i) & 1 for byte in encrypted_blob for i in range(7, -1, -1)])

    total_slots = width * height * 3
    required_bits = len(bit_stream)
    density = (required_bits / total_slots) * 100

    table = Table(title="Image Analysis", border_style="cyan")
    table.add_column("Property", style="bold white")
    table.add_column("Value", style="green")
    table.add_row("Dimensions", f"{width}x{height}")
    table.add_row("LSB Slots", f"{total_slots}")
    table.add_row("Density", f"{density:.4f}%")
    console.print(table)

    if density > 10:
        console.print("[bold red][!] ERROR: Density too high for safe steganography.[/bold red]")
        return False

    coords, seed = get_shuffled_coords(width, height, password, verbose)
    bit_idx = 0

    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        channel_order = [0, 1, 2]
        rng = random.Random(seed + x + y)
        rng.shuffle(channel_order)

        for i in channel_order:
            if bit_idx < len(bit_stream):
                bit = bit_stream[bit_idx]
                if (channels[i] & 1) != bit:
                    if channels[i] == 255: channels[i] -= 1
                    else: channels[i] += 1
                bit_idx += 1
        pixels[x, y] = tuple(channels)
        if bit_idx >= len(bit_stream):
            img.save(output_img_path, format="PNG", compress_level=6)
            return True
    return False

def decode(img_path, password, verbose=False):
    img = Image.open(img_path).convert('RGB')
    pixels = img.load()
    width, height = img.size
    coords, seed = get_shuffled_coords(width, height, password, verbose)
    
    all_extracted_bits = []
    for x, y in coords:
        r, g, b = pixels[x, y]
        channels = [r, g, b]
        channel_order = [0, 1, 2]
        rng = random.Random(seed + x + y)
        rng.shuffle(channel_order)
        for i in channel_order:
            all_extracted_bits.append(channels[i] & 1)

    mask = int("".join(map(str, all_extracted_bits[:32])), 2)
    masked_len = int("".join(map(str, all_extracted_bits[32:64])), 2)
    blob_len = mask ^ masked_len
    
    start, end = 64, 64 + (blob_len * 8)
    payload_bits = all_extracted_bits[start:end]
    blob_bytes = bytearray()
    for i in range(0, len(payload_bits), 8):
        byte = int("".join(map(str, payload_bits[i:i+8])), 2)
        blob_bytes.append(byte)
    
    return decrypt_data(bytes(blob_bytes), password)

def main():
    brand()

    parser = argparse.ArgumentParser(
        prog="stegx",
        description="stegx: Advanced Cross-Platform Steganography",
        usage="stegx [-h] [-v] {encode,decode} ...",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False, 
        epilog="""
Examples:
  stegx encode -i input.png -m 'Secret' -p 'Pass123' -o output.png
  stegx decode -i output.png -p 'Pass123'
        """
    )

    parser.add_argument("-h", "--help", action="store_true", help="show this help message and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Display extra technical details")
    
    subparsers = parser.add_subparsers(dest="mode")

    enc_parser = subparsers.add_parser("encode", help="Hide data")
    enc_parser.add_argument("-i", "--image", required=True, help="Source PNG file")
    enc_parser.add_argument("-m", "--message", required=True, help="Secret message")
    enc_parser.add_argument("-p", "--password", required=True, help="AES Password")
    enc_parser.add_argument("-o", "--output", default="hidden.png", help="Output file")

    dec_parser = subparsers.add_parser("decode", help="Extract data")
    dec_parser.add_argument("-i", "--image", required=True, help="Stego PNG file")
    dec_parser.add_argument("-p", "--password", required=True, help="Password")

    args, unknown = parser.parse_known_args()

    if args.help or len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    if args.mode == "encode":
        if not os.path.exists(args.image):
            console.print(f"[bold red]Error: {args.image} not found.[/bold red]")
            return
        if encode(args.image, args.message, args.password, args.output, verbose=args.verbose):
            console.print(f"\n[bold green][+] Success![/bold green] '{args.output}' generated.")

    elif args.mode == "decode":
        if not os.path.exists(args.image):
            console.print(f"[bold red]Error: {args.image} not found.[/bold red]")
            return
        try:
            decrypted_ecc_data = decode(args.image, args.password, verbose=args.verbose)
            if not decrypted_ecc_data.startswith(b"STEG"):
                raise ValueError()
            
            parity = decrypted_ecc_data[4]
            rs = RSCodec(parity)
            decoded_msg, _, _ = rs.decode(decrypted_ecc_data[5:])
            console.print(f"\n[bold green][+] DECODED:[/bold green] [white]{decoded_msg.decode()}[/white]")
        except Exception:
            fake_results = ["nice try, bitchh!.", "Target: 192.168.1.108 | Status: Vulnerable", "ERR_AUTH_FAIL"]
            console.print(f"\n[bold red][!] DECODED:[/bold red] {random.choice(fake_results)}")

if __name__ == "__main__":
    main()
