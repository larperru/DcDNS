# DcDNS

A lightweight desktop tool that enhances privacy in Discord's Electron client by injecting a JavaScript payload into its main process before Discord loads.

## What it does

DcDNS modifies Discord's internal `index.js` file to apply comprehensive privacy rules at the application level before network modules initialize.

**DNS-over-HTTPS via Mullvad**
All DNS queries made by Discord are routed through Mullvad's encrypted DoH resolver at `https://doh.mullvad.net/dns-query`. Fallback to unencrypted plain DNS is disabled entirely.

**WebRTC IP leak prevention**
WebRTC is forced to block non-proxied UDP connections (`disable_non_proxied_udp`). Local LAN IP addresses are never exposed to Discord's voice servers or other users in calls. Hardware WebRTC decoding is disabled, and strict IP permission checks are enforced.

**Anti-Telemetry and Tracker Blocking**
Disables geolocation APIs (`--disable-geolocation`) and strips built-in crash reporting and metrics collection (`--disable-breakpad`, `--disable-metrics`, `--disable-metrics-repo`).

**Spellcheck disabled**
Discord's built-in spellchecker can silently transmit typed words to third-party cloud APIs. DcDNS disables this feature (`--disable-spell-checking`) to prevent unintended data leaving your machine.

**Auto-Update Engine**
Integrated GitHub API client checks for application updates automatically upon startup and notifies you of new releases.

## Supported clients

- Discord
- Discord PTB
- Discord Canary
- Discord Development

## Supported platforms

- Windows
- Linux (System installations, Flatpak, Snap)
- macOS

## How it works

Before making any changes, DcDNS automatically closes active Discord processes to prevent file lock conflicts. It creates a backup of the original `index.js` file as `index.js.dcdns.bak`. If you uninstall, the original file is fully restored and the backup is removed. If no backup exists, DcDNS safely strips the payload manually without corrupting the file.

Detection is automatic. DcDNS scans all standard Discord installation paths across Windows, Linux, and macOS, showing the current injection status for each client found. You can also provide a custom path manually if your installation is in a non-standard location.

## Download

Get the latest build from the [Releases](../../releases) page.

## Requirements

- **Windows:** Windows 10 or later with WebView2 runtime (included with Windows 11, or download from [microsoft.com/edge/webview2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/))
- **Linux:** Any modern distribution with `webkit2gtk` support
- **macOS:** macOS 10.15 or later
- Discord, Discord PTB, Discord Canary, or Discord Development installed

## License

This project is closed source. The binary is provided as-is for personal use under CC BY-NC-ND 4.0.
Reverse engineering, redistribution, or modification of the binary is not permitted.

Copyright (c) 2025-2026 [Larper.ru]

---

<img width="761" height="509" alt="image2" src="https://github.com/user-attachments/assets/3622b245-f803-4d20-b4ba-f8ddc9e773cf" />
