#!/bin/bash

# Extract the APK
java -jar $1 d $2 -o build_tmp

# Apply the patch
patch build_tmp/smali/com/coreapplication/encryption/MD5Encryption.smali < MD5Encryption.smali.patch

# Build the patched APK
java -jar $1 b build_tmp -o chomikuj_patched.apk

# Cleaning up...
rm -r build_tmp/

echo "Generated APK is in chomikuj_patched.apk"