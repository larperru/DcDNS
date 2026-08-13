# DcDNS

DcDNS is a small Windows tool that patches Discord to block tracking and leaks before the app even connects.

## What it does

DcDNS modifies Discord's internal `index.js` file to apply comprehensive privacy rules at the application level before network modules initialize.

**DNS-over-HTTPS via Mullvad (Strict DoH)**
All DNS queries made by Discord are strictly routed through Mullvad's encrypted DoH resolver (`https://dns.mullvad.net/dns-query`). Unencrypted plain DNS and fallback resolvers (such as Cloudflare or Quad9) are completely removed—DNS queries fail hard instead of silently downgrading to another provider. Chromium-level `DnsOverHttps` feature flags are injected before the app `ready` event, and host resolver cache is flushed on startup.

**Privacy & Fingerprinting Protection**
- **User-Agent Cleaning:** Electron and Discord-specific strings (`Electron/x.x.x`, `DiscordApp/x.x.x`) are stripped from the User-Agent header to prevent web servers from fingerprinting your exact version.
- **TLS Hardening:** Minimum TLS version is enforced at 1.2 via `setSSLConfig`, blocking outdated and insecure TLS protocols.
- **`X-Client-Data` Removal:** Google's Chromium identification header is stripped from every outgoing request.
- **Geolocation Blocked:** All geolocation permission requests are explicitly denied at the Electron layer.
- **Spellcheck Disabled:** Chromium's built-in spellchecker (which can send typed text to remote cloud APIs) is disabled for Discord's session.
- **Leak Prevention:** Prevention of HTTPS/SVCB record queries leaking over insecure channels (`enableAdditionalDnsQueryTypes: false`).

**WebRTC IP Leak Prevention**
WebRTC is forced to block non-proxied UDP connections (`disable_non_proxied_udp`). Local LAN IP addresses are never exposed to Discord's voice servers or other users in calls. Hardware WebRTC decoding is disabled, and strict IP permission checks are enforced.

**Anti-Telemetry and Tracker Blocking**
Disables built-in crash reporting and metrics collection (`--disable-breakpad`, `--disable-metrics`, `--disable-metrics-repo`).

**Auto-Update Engine**
Integrated GitHub API client checks for application updates automatically upon startup and notifies you of new releases.

## Supported clients

- Discord
- Discord PTB
- Discord Canary
- Discord Development

## Supported platforms

- Windows (Windows 11 or later)

## How it works

Before making any changes, DcDNS automatically closes active Discord processes to prevent file lock conflicts. It creates a backup of the original `index.js` file as `index.js.dcdns.bak`. If you uninstall, the original file is fully restored and the backup is removed. If no backup exists, DcDNS safely strips the payload manually without corrupting the file.

Detection is automatic. DcDNS scans all standard Discord installation paths across Windows, showing the current injection status for each client found.

## Download

Get the latest build from the [Releases](../../releases) page.

## Requirements

- **Windows:** Windows 11 or later with WebView2 runtime (included with Windows 11, or download from [microsoft.com/edge/webview2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/))
- Discord, Discord PTB, Discord Canary, or Discord Development installed

## Notes

- On Windows, run `DcDNS.exe` as Administrator if you encounter permission errors during injection.
- After updating Discord, run Install again — Discord updates overwrite the patched `index.js`.

## License

This project is now **open source**. The software and its source code are provided for personal, non-commercial use. 

You are free to read, inspect, and share the original software, but **modification, reverse engineering, creating derivative works, or commercial use are not permitted**.

Copyright (c) 2025-2026 [Larper.ru]

See the [LICENSE](LICENSE) file for full license details.

---

<img width="758" height="512" alt="image" src="https://github.com/user-attachments/assets/b843c23a-b7c6-4e52-a07f-1ba950afd30f" />
