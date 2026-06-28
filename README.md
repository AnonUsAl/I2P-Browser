# I2P Browser

A lightweight PyQt browser for accessing I2P sites with privacy-focused defaults.

## 描述

I2P, the Invisible Internet Project, is an anonymous network layer for private communication over the internet. I2P Browser is configured to access websites and services hosted inside the I2P network while keeping JavaScript, storage, and proxy behavior conservative by default.

## Features

- JavaScript is enabled by default and can be toggled from the toolbar.
- Browser storage, cache, and persistent cookies are disabled.
- Third-party cookies are blocked.
- I2P HTTP proxy mode is enabled by default at `127.0.0.1:4444`。
- Optional Tor SOCKS5 proxy mode is available at `127.0.0.1:9050`。
- I2P and Tor proxy modes are mutually exclusive.
- The interface supports English, Simplified Chinese, and Traditional Chinese.
- The browser clears history and visited links on exit.

## Requirements

- Python 3.9 or newer
- [I2P Router](https://geti2p.net/en/download)
- Optional: [Tor service](https://www.torproject.org/download/tor/) for Tor proxy mode

## 安裝

Clone the repository:

```bash
git clone https://github.com/AnonUsAl/I2P-Browser.git
cd I2P-Browser
```

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install Qt 6 WebEngine dependencies for your platform.

macOS:

``bash
python3 -m pip install -r requirements.txt
```
Newest version may not support MacOS

Debian/Ubuntu:

```bash
sudo apt-get install libnss3 libxcomposite1 libxdamage1 libxrandr2 libxtst6 libxkbcommon-x11-0
```

Install Python dependencies:

```bash
python3 -m pip install -r requirements.txt
```

## Usage

Start the I2P router and make sure its HTTP proxy is available at `127.0.0.1:4444`。

To use Tor mode, start Tor and make sure its SOCKS5 proxy is available at `127.0.0.1:9050`。

Run the browser:

```bash
python3 Browser.py
```

## Disclaimer

This project is not affiliated with the Invisible Internet Project, the Tor Project, or any other third-party organization, product, or service.
