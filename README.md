# I2P Browser
## A web browser for accessing I2P network anonymously and securely
## Description:
I2P, which stands for "Invisible Internet Project," is an anonymous network layer that allows for secure and private communication over the internet. It is designed to provide strong anonymity and privacy protections for its users. I2P browser is a web browser that is configured to work with the I2P network, allowing users to access websites and services hosted within the I2P network while maintaining a high level of anonymity.

## Features:

- Javascript is blocked by default
- Non-unique fingerprint (Each user looks identical to websites)
- Same security of Tor Browser's [safest level](https://tb-manual.torproject.org/security-settings/) by default
- Built in Python
- No browsing history and cache
- I2P Proxy Killswitch (prevents data leaks)
- Optional Tor SOCKS5 proxy mode

## Installation:

     git clone https://github.com/AnonUsAl/I2P-Browser.git
     cd I2P-Browser/
     python3 -m venv .venv
     source .venv/bin/activate
     #MacOS:
     brew install python3-pyqt5.qtwebengine
     #Linux
     sudo apt-get install python3-pyqt5.qtwebengine
     python3 -m pip install -r requirements.txt
     python3 Browser.py

## Usage:
Step 1: Start the I2P router in the background and make sure the HTTP proxy is available at `127.0.0.1:4444`.

Optional: Start Tor in the background if you want to use Tor mode. The browser expects a SOCKS5 proxy at `127.0.0.1:9050`.

Step 2:

     python3 Browser.py

## Requirements:

- I2P Router ---> https://geti2p.net/en/download

- Tor service ---> https://www.torproject.org/download/tor/

- Python >=3.9




### Disclaimer:

The creator of this project, disclaims no affiliation with the Invisible Internet Project (I2P) or any other third-party organizations, products, or services.
