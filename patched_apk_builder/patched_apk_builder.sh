#!/bin/bash

# Extract the APK
java -jar $1 d $2 -o build_tmp

# Apply the patch
patch build_tmp/smali/com/coreapplication/encryption/MD5Encryption.smali < MD5Encryption.smali.patch

# Build the patched APK
java -jar $1 b build_tmp -o chomikuj_patched.apk

# Sign the patched APK
echo "You need to generate a signature key. What you give here will not be important, just leave it empty, except the password of course."
keytool -genkey -v -keystore patch.keystore -alias alias_name -keyalg RSA -keysize 2048 -validity 10000
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore patch.keystore chomikuj_patched.apk alias_name

# Cleaning up...
rm -r build_tmp/
rm patch.keystore

echo "Generated APK is in chomikuj_patched.apk"