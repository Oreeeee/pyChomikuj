# pyChomikuj
![python](https://img.shields.io/pypi/pyversions/pychomikuj?style=plastic) ![open issues](https://img.shields.io/github/issues-raw/Oreeeee/pychomikuj?style=plastic) ![open pull requests](https://img.shields.io/github/issues-pr/Oreeeee/pychomikuj?style=plastic) ![version](https://img.shields.io/pypi/v/pychomikuj?style=plastic) ![code style](https://img.shields.io/badge/code%20style-black-black?style=plastic) ![star count](https://img.shields.io/github/stars/Oreeeee/pychomikuj?style=social)

(W.I.P) Chomikuj API written in Python

## Features
- Support for Mobile API, which means that you can use infinite transfer from Chomikuj mobile app
- Really thin wrapper over Chomikuj's API, in most cases responses that this package gives are the same as what Chomikuj gives.

## TODO:
- [x] Support for Mobile API (Chomikuj Android) (partially for now)
- [ ] Support for Windows API (ChomikBox)
- [ ] Support for Web API (Chomikuj.pl Website)
- [ ] API documentation for every of them

## Status
This project is in very early development, here is a list of features that work as of the latest commit
1. Mobile API
- [x] Logging in
- [x] Searching for files
- [x] Listing directories, including password protected ones
- [x] Getting download links
- [x] Creating directories
- [x] Private messages
- [x] Listing friends
- [x] Getting a list of copied files
- [ ] Uploading files
- [x] Deleting files
- [ ] Messaging people --- FOR SOME UNKNOWN REASON BROKEN AT THE MOMENT
- [ ] Adding someone as a friend
2. Windows API
- Nothing
3. Web API
- Nothing

## Additional plans
1. Mobile API
- [ ] Recursively get download links
- [ ] Better logging