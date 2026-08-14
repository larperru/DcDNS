<h1 align="center">DcDNS</h1>

<p align="center">
  <a href="https://github.com/larperru/DcDNS/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/larperru/DcDNS?style=for-the-badge&logo=github&logoSize=auto">
  </a>
  <a href="https://github.com/larperru/DcDNS/releases">
    <img alt="GitHub downloads" src="https://img.shields.io/github/downloads/larperru/DcDNS/total?style=for-the-badge&logo=github&logoSize=auto&label=DOWNLOADS">
  </a>
  <a href="https://github.com/larperru/DcDNS/releases/latest">
    <img alt="Latest release" src="https://img.shields.io/github/v/release/larperru/DcDNS?style=for-the-badge&logo=github&logoSize=auto&label=VERSION">
  </a>
  <img alt="Platform" src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows&logoSize=auto">
</p>

<p align="center">
  <b>A lightweight privacy hardening tool for Discord Desktop on Windows.</b><br>
  Enforces strict DNS-over-HTTPS, blocks WebRTC IP leaks, disables telemetry, and strips tracking headers — all before Discord connects to the internet.
</p>

---

## Why DcDNS Exists

Discord's desktop client runs on Electron, which inherits Chromium's default networking behavior. Out of the box, this means:

- DNS queries travel unencrypted to your ISP or default resolver
- WebRTC can expose your real local IP address during voice and video calls
- Chromium sends telemetry, crash reports, and fingerprinting headers
- Spellcheck may transmit typed text to remote cloud APIs
- Google-specific identifiers like `X-Client-Data` are attached to requests

DcDNS patches Discord's core `index.js` file to eliminate these leaks at the application level, before any network connection is established. No VPN required. No proxy setup. One click, immediate protection.

---

## What DcDNS Does

### Strict DNS-over-HTTPS via Mullvad

All DNS queries from Discord are forced through Mullvad's encrypted DoH resolver (`https://dns.mullvad.net/dns-query`). Plain DNS fallback is completely removed. If the DoH resolver is unreachable, queries fail securely rather than silently downgrading to an unencrypted alternative.

- Chromium `DnsOverHttps` feature flags are injected before the `app-ready` event
- Host resolver cache is flushed on startup
- Optional: configure your own custom DoH URL in Settings

### WebRTC IP Leak Protection

WebRTC is configured to block non-proxied UDP connections (`disable_non_proxied_udp`). Your local LAN IP address is never exposed to Discord's voice servers or other users in calls. Hardware WebRTC decoding is disabled and strict IP permission checks are enforced.

### Telemetry and Tracker Blocking

Outgoing requests to known Discord analytics endpoints are blocked at the Electron network layer:

- `/api/v*/science`
- `/api/v*/track`
- `/api/v*/metrics`
- `/api/v*/events/stats`
- `/api/v*/analytics`
- Sentry domains (`sentry.io`, `*.sentry.io`, `ingest.sentry.io`)
- Discord crash reporting (`crash.discord.com`, `crash-reports.discord.com`, `reporter.discord.com`)

This is toggleable in Settings.

### Privacy Hardening

- **User-Agent Cleaning:** Electron and Discord-specific version strings are stripped from outgoing requests
- **TLS 1.2 Minimum:** Outdated TLS protocols are blocked via `setSSLConfig`
- **`X-Client-Data` Removal:** Google's Chromium identification header is stripped from every request
- **Geolocation Blocked:** All geolocation permission requests are denied at the Electron layer
- **Spellcheck Disabled:** Chromium's built-in spellchecker (which may send text to remote APIs) is disabled for Discord's session
- **Background Networking Disabled:** Chromium's background networking and metrics collection are turned off

### Transparent Operation

- Full installation log showing every change made
- SHA-256 hash of patched file displayed after install
- Automatic backup of original `index.js` as `index.js.dcdns.bak`
- One-click uninstall restores the original file completely

---

## Demo

See DcDNS in action:

- **YouTube Showcase (English):** https://youtu.be/Lw19Vt_cEbs
- **YouTube Showcase (Polish):** https://youtu.be/bacK4ibB_Vo

---

## Supported Clients

- Discord (Stable)
- Discord PTB
- Discord Canary
- Discord Development

---

## System Requirements

- Windows 11 or later
- WebView2 runtime (included with Windows 11, or download from [Microsoft](https://developer.microsoft.com/en-us/microsoft-edge/webview2/))
- One of the supported Discord clients installed

---

## Download

Get the latest release from the [Releases](../../releases) page.

No installation required. DcDNS is a portable executable. Run as Administrator for proper file access to Discord's installation directory.

---

## How to Use

1. **Close Discord** completely (DcDNS can do this automatically)
2. **Run DcDNS.exe** as Administrator
3. **Review the Policy** — full transparency, no data collection
4. **Configure Settings** if desired (custom DNS, telemetry blocking, label toggle)
5. **Click Install** and select your Discord client
6. **Restart Discord** — the title bar will show "Encrypted By DcDNS" when active

After Discord updates, run Install again. Discord updates overwrite the patched file.

---

## Uninstall

Click Uninstall in DcDNS. The original `index.js` is restored from backup. If no backup exists, DcDNS safely strips its payload without corrupting the file.

---

## Why Trust DcDNS

- **Fully open source:** Every line of code is visible in this repository
- **No network calls:** The tool itself does not transmit any data. The only external connection is a read-only check to GitHub's public API for update notifications
- **No data collection:** Zero telemetry, zero analytics, zero crash reporting from DcDNS itself
- **Reversible:** One-click uninstall returns Discord to stock
- **Community tested:** Active feedback and issue tracking on GitHub

---

## Limitations

DcDNS improves network-level privacy within Discord. It does not:

- Make you anonymous to Discord (you are still logged into your account)
- Bypass Discord's servers or encryption
- Protect traffic outside of Discord (use a system-wide VPN or DNS for that)
- Persist through Discord client updates (reinstall required after each update)

---

## Support and Community

- **GitHub Issues:** Bug reports and feature requests
- **Discord Server:** https://discord.gg/9cu4Rf2ke2 — support, feedback, and development discussion

If DcDNS helped you, please consider starring the repository. It helps others discover the project and supports continued development.

---

## License

Copyright (c) 2025-2026 Larper.ru

Permission is granted to use, read, and share this software for personal, non-commercial purposes. Modification, reverse engineering, derivative works, and commercial use are not permitted.

See the [LICENSE](LICENSE) file for complete terms.

---

<p align="center">
  <img width="758" height="512" alt="DcDNS Interface" src="https://github.com/user-attachments/assets/b843c23a-b7c6-4e52-a07f-1ba950afd30f" />
</p>
