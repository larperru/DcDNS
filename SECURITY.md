# Security Policy

## Supported versions

Only the latest release of DcDNS is supported.

| Version | Supported |
|---------|-----------|
| Latest release | Yes |
| Older releases | No |

Please always use the newest version from the official GitHub Releases page.

## What DcDNS is

DcDNS is a local Windows tool that patches the Discord desktop client to apply privacy-related settings.

It:
- runs only on your machine
- does not require an account
- does not phone home with personal data
- does not read your Discord messages, token, or files

## Reporting a vulnerability

If you believe you found a security or privacy issue in DcDNS, please report it responsibly.

### Please report
- Remote code execution
- Privilege escalation
- Unexpected network requests made by DcDNS itself
- Data leakage caused by DcDNS
- Installer behavior that could damage the system or Discord install in an unsafe way
- Weak or broken privacy protections that DcDNS claims to provide

### Please do not report
- Discord's own security issues unrelated to DcDNS
- Issues caused by unofficial modified Discord clients
- Feature requests
- General questions about how the tool works

## How to report

Preferred method:
1. Open a GitHub Issue titled `SECURITY: short description`
2. Or contact the maintainer through the official project Discord

Include:
- DcDNS version
- Windows version
- Discord client version (Stable / PTB / Canary)
- Clear steps to reproduce
- Expected vs actual behavior
- Proof of concept if possible
- Impact assessment

Please do **not** publish a full exploit publicly before a fix is available.

## Response process

1. The report will be reviewed as soon as possible
2. If confirmed, a fix will be prepared for the next release when feasible
3. Credit may be given to the reporter unless anonymity is requested

## Scope notes

- DcDNS modifies local Discord files. Any Discord update can remove the patch.
- DcDNS is provided as-is, without warranty.
- Use of third-party client modifications may violate Discord's Terms of Service. Use at your own risk.

## Official source only

Download DcDNS only from the official repository:

https://github.com/larperru/DcDNS

Do not trust reposted binaries from third-party sites.
