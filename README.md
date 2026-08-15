<h1 align="center">DcDNS</h1>

<p align="center">
  <a href="https://github.com/larperru/DcDNS/stargazers">
    <img alt="GitHub stars" src="https://img.shields.io/github/stars/larperru/DcDNS?style=for-the-badge&logo=github">
  </a>
  <a href="https://github.com/larperru/DcDNS/releases">
    <img alt="GitHub downloads" src="https://img.shields.io/github/downloads/larperru/DcDNS/total?style=for-the-badge&logo=github&label=DOWNLOADS">
  </a>
  <a href="https://github.com/larperru/DcDNS/releases/latest">
    <img alt="Latest release" src="https://img.shields.io/github/v/release/larperru/DcDNS?style=for-the-badge&logo=github&label=VERSION">
  </a>
  <img alt="Platform" src="https://img.shields.io/badge/Windows-0078D6?style=for-the-badge&logo=windows">
</p>

<p align="center">
  <b>A lightweight privacy hardening tool for Discord Desktop on Windows.</b><br>
  Enforces strict DNS-over-HTTPS, blocks WebRTC IP leaks, disables telemetry, and strips tracking headers — before Discord connects to the internet.
</p>

<p align="center">
  <a href="https://dcdns.pages.dev">Website</a> •
  <a href="https://github.com/larperru/DcDNS/releases/latest">Download</a> •
  <a href="https://youtu.be/Lw19Vt_cEbs">Demo</a> •
  <a href="https://discord.gg/9cu4Rf2ke2">Discord</a>
</p>

---

## Why DcDNS Exists

Discord's desktop client runs on Electron and inherits Chromium defaults. That means:

- DNS queries can leave the machine unencrypted
- WebRTC can expose your local/LAN IP during calls
- Chromium may send telemetry, crash reports, and fingerprinting headers
- Spellcheck can send typed text to remote services
- Headers like `X-Client-Data` can leak Chromium build identifiers

DcDNS patches Discord's local `index.js` and injects privacy controls at the Electron layer before Discord starts its normal network activity.

No system-wide VPN required. No proxy setup. Local patch only.

> **Important:** Any Discord update overwrites `index.js` and removes DcDNS. Reinstall after updates. Use at your own risk.

---

## What DcDNS Does

### Strict DNS-over-HTTPS
Forces Discord DNS lookups through encrypted DoH.

- Default: Mullvad (`https://dns.mullvad.net/dns-query`)
- Fallback: Mullvad adblock DoH
- Plain DNS fallback disabled
- Optional custom DoH URL in Settings

### WebRTC IP Protection
Locks WebRTC to public-interface-only mode so your local LAN IP is not exposed during voice/video calls.

### Telemetry / Tracker Blocking
Blocks known Discord analytics and crash endpoints at the Electron network layer, including:

- `/api/v*/science`
- `/api/v*/track`
- `/api/v*/metrics`
- `/api/v*/events/stats`
- `/api/v*/analytics`
- Sentry domains
- `crash.discord.com`, `crash-reports.discord.com`, `reporter.discord.com`

Toggleable in Settings.

### Extra Hardening
- User-Agent cleanup
- TLS 1.2 minimum
- `X-Client-Data` removal
- Geolocation denied
- Spellcheck disabled
- Chromium background networking reduced

### Transparent and reversible
- Full install log
- SHA-256 verification of patched file
- Automatic backup as `index.js.dcdns.bak`
- One-click uninstall restores the original file

---

## Demo

- [YouTube Showcase](https://youtu.be/Lw19Vt_cEbs)
- [Older Showcase](https://youtu.be/bacK4ibB_Vo)

Website: [dcdns.pages.dev](https://dcdns.pages.dev)

---

## Supported Clients

- Discord Stable
- Discord PTB
- Discord Canary
- Discord Development

---

## System Requirements

- Windows 11 or later
- WebView2 Runtime
- One supported Discord desktop client

WebView2 download: [Microsoft Edge WebView2](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)

---

## Download

Get the latest build from the [Releases](../../releases) page.

DcDNS is portable. No installer required.  
Run as Administrator so it can access Discord's installation files.

---

## How to Use

1. Close Discord completely
2. Run `DcDNS.exe` as Administrator
3. Read and accept the policy
4. Optionally configure Settings
5. Select your Discord client
6. Click **Install**
7. Restart Discord

If active, the title bar can show `Encrypted By DcDNS`.

After every Discord update, run Install again.

---

## Uninstall

Click **Uninstall** in DcDNS.

- Restores original `index.js` from `index.js.dcdns.bak`
- If backup is missing, strips the DcDNS payload safely

---

## Why Trust DcDNS

- Source is public and readable
- The tool does not collect personal data
- The only external request is a read-only GitHub release check
- Install creates a backup before patching
- Uninstall is one click and reversible

Still verify the release SHA-256 before running any `.exe`.

---

## Limitations

DcDNS improves Discord client network privacy. It does **not**:

- make you anonymous to Discord while logged in
- bypass Discord servers
- protect traffic outside Discord
- survive Discord auto-updates

For system-wide protection use a VPN or OS-level DNS settings.

---

## Support

- GitHub Issues: bugs and feature requests
- Discord: https://discord.gg/9cu4Rf2ke2

If DcDNS is useful, star the repository. It helps others find the project.

---

## License

Copyright (c) 2025-2026 Larper.ru

Personal non-commercial use only.  
No modification, reverse engineering, derivative works, or commercial use.

See [LICENSE](LICENSE) for full terms.

---

<p align="center">
  <img width="758" height="512" alt="DcDNS Interface" src="https://github.com/user-attachments/assets/b843c23a-b7c6-4e52-a07f-1ba950afd30f" />
</p>
