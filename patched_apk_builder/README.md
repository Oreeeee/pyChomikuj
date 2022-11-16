# Patched APK builder
This script will patch the APK to see what it is hashing for request tokens

## Building
`./patched_apk_builder.sh [apktool JAR] [input APK]`

## Example
`./patched_apk_builder.sh apktool.jar chomikuj.apk`

## Usage
Uninstall original Chomikuj app, install the patched one, use this command to get what it's outputting

`adb logcat | grep "HASHING MD5"`