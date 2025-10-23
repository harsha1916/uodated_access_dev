#!/usr/bin/env python3
"""
Quick Upload Test Script

This script tests different field names to find what your S3 API expects.
Solves: MulterError: Unexpected field

Usage:
    python test_upload.py
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv(".env" if os.path.exists(".env") else "config.example.env")

# Get configuration
UPLOAD_ENDPOINT = os.getenv("UPLOAD_ENDPOINT", "")
UPLOAD_AUTH_BEARER = os.getenv("UPLOAD_AUTH_BEARER", "")

# Field names to test (in order of likelihood)
FIELD_NAMES_TO_TEST = [
    "file",         # Most common
    "singleFile",   # From uploader1.py
    "image",        # Common alternative
    "upload",       # Another common one
    "photo",        # Sometimes used
    "anpr",         # Based on module name
    "document",     # Generic
]

print("=" * 70)
print("🧪 Upload Field Name Test")
print("=" * 70)
print()
print(f"Endpoint: {UPLOAD_ENDPOINT}")
print()

if not UPLOAD_ENDPOINT:
    print("❌ Error: UPLOAD_ENDPOINT not set in .env file")
    print("Please set UPLOAD_ENDPOINT in your .env file")
    exit(1)

# Create a test image (1x1 pixel JPEG)
TEST_IMAGE = "test_upload.jpg"
print("Creating test image...")

# Create minimal JPEG using PIL (more reliable)
try:
    from PIL import Image
    # Create 1x1 pixel image
    img = Image.new('RGB', (1, 1), color='red')
    img.save(TEST_IMAGE, 'JPEG', quality=95)
    print(f"✓ Test image created using PIL: {TEST_IMAGE}")
except ImportError:
    # Fallback: create minimal JPEG manually
    print("PIL not available, creating minimal JPEG manually...")
    # Minimal JPEG header + 1x1 pixel data
    minimal_jpeg = (
        b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00'
        b'\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xff\xc4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xaa\xff\xd9'
    )
    with open(TEST_IMAGE, "wb") as f:
        f.write(minimal_jpeg)
    print(f"✓ Test image created manually: {TEST_IMAGE}")

print()

# Test each field name
print("=" * 70)
print("Testing different field names...")
print("=" * 70)
print()

results = []

for field_name in FIELD_NAMES_TO_TEST:
    print(f"Testing field name: '{field_name}'...")
    
    try:
        headers = {"User-Agent": "camcap-test/1.0"}
        if UPLOAD_AUTH_BEARER:
            headers["Authorization"] = f"Bearer {UPLOAD_AUTH_BEARER}"
        
        with open(TEST_IMAGE, "rb") as f:
            files = {
                field_name: ("test.jpg", f, "image/jpeg")
            }
            
            response = requests.post(
                UPLOAD_ENDPOINT,
                files=files,
                headers=headers,
                timeout=30
            )
        
        status = response.status_code
        
        if status == 200:
            print(f"  ✅ SUCCESS! HTTP {status}")
            print(f"  ✓ Response: {response.text[:200]}")
            results.append((field_name, status, "SUCCESS"))
        else:
            print(f"  ❌ Failed: HTTP {status}")
            print(f"  ✗ Response: {response.text[:200]}")
            results.append((field_name, status, "FAILED"))
    
    except Exception as e:
        print(f"  ❌ Error: {type(e).__name__}: {str(e)[:100]}")
        results.append((field_name, 0, "ERROR"))
    
    print()

# Cleanup
try:
    os.remove(TEST_IMAGE)
except:
    pass

# Summary
print("=" * 70)
print("📊 TEST RESULTS")
print("=" * 70)
print()

success_found = False
for field_name, status, result in results:
    symbol = "✅" if result == "SUCCESS" else "❌"
    print(f"{symbol} Field: '{field_name:15s}' → HTTP {status:3d} ({result})")
    if result == "SUCCESS":
        success_found = True

print()
print("=" * 70)

if success_found:
    print("✅ SOLUTION FOUND!")
    print("=" * 70)
    print()
    for field_name, status, result in results:
        if result == "SUCCESS":
            print(f"✓ Use this field name in your .env file:")
            print(f"  UPLOAD_FIELD_NAME={field_name}")
            print()
            print("Update your .env file:")
            print(f"  nano .env")
            print(f"  # Change UPLOAD_FIELD_NAME to: {field_name}")
            print()
            print("Then restart:")
            print("  python app.py")
            print()
            break
else:
    print("❌ NO WORKING FIELD NAME FOUND")
    print("=" * 70)
    print()
    print("Possible issues:")
    print("  1. Wrong endpoint URL")
    print("  2. Authentication required (set UPLOAD_AUTH_BEARER)")
    print("  3. API configuration issue")
    print("  4. Network/firewall blocking requests")
    print()
    print("Try:")
    print("  1. Check UPLOAD_ENDPOINT is correct")
    print("  2. Contact API provider for field name")
    print("  3. Test with curl manually")
    print()

print("Done!")
print()

