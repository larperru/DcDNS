# DcDNS

A lightweight desktop tool that enhances privacy in Discord's Electron client by injecting a JavaScript payload into its main process before Discord loads.

## What it does

DcDNS modifies Discord's internal `index.js` file to apply three privacy rules at the application level.

**DNS-over-HTTPS via Mullvad**
All DNS queries made by Discord are routed through Mullvad's encrypted DoH resolver at `dns.mullvad.net`. Mullvad keeps zero logs and blocks ads, trackers, and malware domains by default. Fallback to unencrypted plain DNS is disabled entirely.

**WebRTC IP leak prevention**
WebRTC is forced to use only your public network interface. Your local LAN IP addresses are never exposed to Discord's voice servers or other users in calls. Voice and video functionality continues to work normally.

**Spellcheck disabled**
Discord's built-in spellchecker silently transmits typed words to third-party cloud APIs. DcDNS disables this feature to prevent unintended data leaving your machine.

## Supported clients

- Discord
- Discord PTB
- Discord Canary

## Supported platforms

- Windows
- Linux
- macOS

## How it works

Before making any changes, DcDNS creates a backup of the original `index.js` file alongside it as `index.js.dcdns.bak`. If you uninstall, the original file is fully restored and the backup is removed. If no backup exists, DcDNS strips the payload manually without the backup.

Detection is automatic. DcDNS scans all standard Discord installation paths for your platform and shows the version and current injection status for each client it finds. You can also provide a custom path manually if your installation is in a non-standard location.

## Download

Get the latest build from the [Releases](../../releases) page.

## Requirements

- Windows 10 or later
- Discord, Discord PTB or Discord Canary installed
- WebView2 runtime (included with Windows 11, otherwise download from [microsoft.com/edge/webview2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/))

## License

This project is closed source. The binary is provided as-is for personal use under CC BY-NC-ND 4.0.
Reverse engineering, redistribution, or modification of the binary is not permitted.

Copyright (c) 2025 [Your Name]

---

<img width="760" height="511" alt="image1" src="https://github.com/user-attachments/assets/00519624-018c-413f-9edd-53a3f39c9d6a" />
