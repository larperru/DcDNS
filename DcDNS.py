# ==============================================================================
# DcDNS
# ==============================================================================
# Author:      Larper.ru
# Version:     v1.0.2
# License:     Custom Non-Commercial / No-Derivatives (Open Source - Read Only)
# Repository:  https://github.com/larperru/DcDNS
# Discord:     https://discord.gg/RNqC6eEQMR
# Copyright:   (c) 2025-2026 Larper.ru. All rights reserved.
# ==============================================================================

import os
import sys
import re
import glob
import shutil
import time
import json
import queue
import base64
import threading
import subprocess
import multiprocessing
import webbrowser

if sys.platform != "win32":
    print("DcDNS supports Windows only.", file=sys.stderr)
    sys.exit(1)

os.environ["PYWEBVIEW_GUI"] = "edgechromium"

import webview

try:
    import webview.platforms.edgechromium
except Exception:
    pass

DISCORD_INVITE_URL = "https://discord.gg/9cu4Rf2ke2"
GITHUB_REPO_SLUG = "larperru/DcDNS"
APP_VERSION = "1.0.2"

PAYLOAD_MARKER = "/* === [DcDNS Policy Framework"
HEADER_TAG = "/* === [DcDNS Policy Framework v" + APP_VERSION + "] === */"
FOOTER_TAG = "/* === [End DcDNS Policy Framework] === */"

DCDNS_PAYLOAD = (
    HEADER_TAG + "\n"
    "(function() {\n"
    "    'use strict';\n"
    "    try {\n"
    "        var electron;\n"
    "        try { electron = require('electron'); } catch(e) { return; }\n"
    "        var app = (electron && electron.app) || (electron && electron.default && electron.default.app);\n"
    "        var session = (electron && electron.session) || (electron && electron.default && electron.default.session);\n"
    "        var shell = (electron && electron.shell) || (electron && electron.default && electron.default.shell);\n"
    "        if (!app) return;\n"
    "        var MULLVAD_DOH = 'https://dns.mullvad.net/dns-query';\n"
    "        function safeSwitch(name, value) {\n"
    "            try {\n"
    "                if (app.commandLine && typeof app.commandLine.appendSwitch === 'function') {\n"
    "                    app.commandLine.appendSwitch(name, value);\n"
    "                }\n"
    "            } catch (e) {}\n"
    "        }\n"
    "        if (typeof app.commandLine !== 'undefined') {\n"
    "            safeSwitch('force-webrtc-ip-handling-policy', 'default_public_interface_only');\n"
    "            safeSwitch('webrtc-ip-handling-policy', 'default_public_interface_only');\n"
    "            safeSwitch('disable-background-networking', '1');\n"
    "            safeSwitch('disable-client-side-phishing-detection', '1');\n"
    "            safeSwitch('disable-component-update', '1');\n"
    "            safeSwitch('disable-default-apps', '1');\n"
    "            safeSwitch('disable-sync', '1');\n"
    "            safeSwitch('metrics-recording-only', '1');\n"
    "            safeSwitch('no-pings', '1');\n"
    "            safeSwitch('disable-breakpad', '1');\n"
    "            safeSwitch('no-crash-upload', '1');\n"
    "            safeSwitch('enable-features', 'DnsOverHttps:Fallback/false/Templates/https%3A%2F%2Fdns.mullvad.net%2Fdns-query');\n"
    "        }\n"
    "        var DCDNS_DOH_SERVERS = [MULLVAD_DOH];\n"
    "        function applyDnsPolicy() {\n"
    "            try {\n"
    "                if (typeof app.configureHostResolver === 'function') {\n"
    "                    app.configureHostResolver({\n"
    "                        secureDnsMode: 'secure',\n"
    "                        secureDnsServers: DCDNS_DOH_SERVERS,\n"
    "                        enableAdditionalDnsQueryTypes: false\n"
    "                    });\n"
    "                }\n"
    "            } catch (e) {}\n"
    "        }\n"
    "        function applySessionPolicy(sess) {\n"
    "            if (!sess) return;\n"
    "            try {\n"
    "                if (typeof sess.setSpellCheckerEnabled === 'function') {\n"
    "                    sess.setSpellCheckerEnabled(false);\n"
    "                }\n"
    "            } catch (e) {}\n"
    "            try {\n"
    "                if (typeof sess.setPermissionRequestHandler === 'function') {\n"
    "                    sess.setPermissionRequestHandler(function(webContents, permission, callback) {\n"
    "                        try {\n"
    "                            if (permission === 'microphone' || permission === 'camera') {\n"
    "                                callback(true);\n"
    "                            } else if (permission === 'geolocation') {\n"
    "                                callback(false);\n"
    "                            } else {\n"
    "                                callback(true);\n"
    "                            }\n"
    "                        } catch (e) { try { callback(true); } catch (e2) {} }\n"
    "                    });\n"
    "                }\n"
    "            } catch (e) {}\n"
    "            try {\n"
    "                if (sess.webRequest && typeof sess.webRequest.onBeforeSendHeaders === 'function') {\n"
    "                    sess.webRequest.onBeforeSendHeaders(function(details, callback) {\n"
    "                        try {\n"
    "                            var headers = details.requestHeaders || {};\n"
    "                            delete headers['X-Client-Data'];\n"
    "                            callback({ requestHeaders: headers });\n"
    "                        } catch (e) { try { callback({}); } catch (e2) {} }\n"
    "                    });\n"
    "                }\n"
    "            } catch (e) {}\n"
    "            try {\n"
    "                if (typeof sess.getUserAgent === 'function' && typeof sess.setUserAgent === 'function') {\n"
    "                    var ua = sess.getUserAgent();\n"
    "                    if (ua) {\n"
    "                        ua = ua.replace(/Electron\\/[^\\s]+\\s?/g, '');\n"
    "                        ua = ua.replace(/DiscordApp\\/[^\\s]+\\s?/g, '');\n"
    "                        ua = ua.replace(/discord\\/[^\\s]+\\s?/gi, '');\n"
    "                        ua = ua.trim();\n"
    "                        sess.setUserAgent(ua);\n"
    "                    }\n"
    "                }\n"
    "            } catch (e) {}\n"
    "            try {\n"
    "                if (typeof sess.clearHostResolverCache === 'function') {\n"
    "                    sess.clearHostResolverCache();\n"
    "                }\n"
    "            } catch (e) {}\n"
    "            try {\n"
    "                if (typeof sess.setSSLConfig === 'function') {\n"
    "                    sess.setSSLConfig({ minVersion: 'tls1.2' });\n"
    "                }\n"
    "            } catch (e) {}\n"
    "        }\n"
    "        function getElectronVersion() {\n"
    "            try { return (process && process.versions && process.versions.electron) || ''; }\n"
    "            catch (e) { return ''; }\n"
    "        }\n"
    "        function getChromeVersion() {\n"
    "            try { return (process && process.versions && process.versions.chrome) || ''; }\n"
    "            catch (e) { return ''; }\n"
    "        }\n"
    "        var DCDNS_CURRENT_VERSION = '" + APP_VERSION + "';\n"
    "        var DCDNS_REPO_SLUG = '" + GITHUB_REPO_SLUG + "';\n"
    "        var dcdnsUpdateInfo = null;\n"
    "        var dcdnsKnownContents = [];\n"
    "        function dcdnsCompareVersions(a, b) {\n"
    "            try {\n"
    "                var pa = a.split('.').map(function(n) { return parseInt(n, 10) || 0; });\n"
    "                var pb = b.split('.').map(function(n) { return parseInt(n, 10) || 0; });\n"
    "                var len = Math.max(pa.length, pb.length);\n"
    "                for (var i = 0; i < len; i++) {\n"
    "                    var x = (pa[i] !== undefined ? pa[i] : 0);\n"
    "                    var y = (pb[i] !== undefined ? pb[i] : 0);\n"
    "                    if (x > y) return 1;\n"
    "                    if (x < y) return -1;\n"
    "                }\n"
    "                return 0;\n"
    "            } catch (e) { return 0; }\n"
    "        }\n"
    "        function dcdnsPushUpdateInfo() {\n"
    "            if (!dcdnsUpdateInfo) return;\n"
    "            var script = 'try{window.__dcdnsUpdateInfo=' + JSON.stringify(dcdnsUpdateInfo) + ';if(typeof window.__dcdnsShowUpdateBanner===\"function\"){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}}catch(e){}';\n"
    "            for (var i = 0; i < dcdnsKnownContents.length; i++) {\n"
    "                try {\n"
    "                    var c = dcdnsKnownContents[i];\n"
    "                    if (c && !c.isDestroyed()) {\n"
    "                        c.executeJavaScript(script, true).catch(function() {});\n"
    "                    }\n"
    "                } catch (e) {}\n"
    "            }\n"
    "        }\n"
    "        function dcdnsCheckForUpdate() {\n"
    "            try {\n"
    "                var https;\n"
    "                try { https = require('https'); } catch(e) { return; }\n"
    "                var options = {\n"
    "                    hostname: 'api.github.com',\n"
    "                    path: '/repos/' + DCDNS_REPO_SLUG + '/releases/latest',\n"
    "                    method: 'GET',\n"
    "                    headers: { 'User-Agent': 'DcDNS-Update-Check/' + DCDNS_CURRENT_VERSION, 'Accept': 'application/vnd.github+json' }\n"
    "                };\n"
    "                var req = https.request(options, function(res) {\n"
    "                    var body = '';\n"
    "                    res.on('data', function(chunk) { body += chunk; });\n"
    "                    res.on('end', function() {\n"
    "                        try {\n"
    "                            var data = JSON.parse(body);\n"
    "                            var tag = (data.tag_name || '').replace(/^v/i, '');\n"
    "                            var url = data.html_url || ('https://github.com/' + DCDNS_REPO_SLUG + '/releases/latest');\n"
    "                            if (tag && dcdnsCompareVersions(tag, DCDNS_CURRENT_VERSION) > 0) {\n"
    "                                dcdnsUpdateInfo = { version: tag, url: url };\n"
    "                                dcdnsPushUpdateInfo();\n"
    "                            }\n"
    "                        } catch (e) {}\n"
    "                    });\n"
    "                });\n"
    "                req.setTimeout(10000, function() { try { req.destroy(); } catch (e) {} });\n"
    "                req.on('error', function() {});\n"
    "                req.end();\n"
    "            } catch (e) {}\n"
    "        }\n"
    "        var DCDNS_LABEL_SCRIPT = \"(function(){try{if(window.__dcdnsLabelActive)return;window.__dcdnsLabelActive=true;var lastRun=0;function getChromeVer(){try{return window.__dcdnsChromeVersion||'';}catch(e){return '';}}function findTitleBar(){var w=window.innerWidth;var all=document.querySelectorAll('div');var best=null;var bestHeight=999;for(var i=0;i<all.length;i++){var el=all[i];var r=el.getBoundingClientRect();if(r.top<=2&&r.height>15&&r.height<45&&r.width>w*0.85){if(r.height<bestHeight){best=el;bestHeight=r.height;}}}return best;}function inject(){try{if(document.getElementById('dcdns-encrypted-label'))return;var now=Date.now();if(now-lastRun<250)return;lastRun=now;var bar=findTitleBar();if(!bar)return;var computed=window.getComputedStyle(bar);if(computed.position==='static')bar.style.position='relative';var label=document.createElement('div');label.id='dcdns-encrypted-label';var chromever=getChromeVer();var labelText='Encrypted By DcDNS';if(chromever){labelText+=' \\u2014 Chrome/'+chromever;}label.textContent=labelText;label.style.cssText='position:absolute;left:0;right:0;top:0;bottom:0;display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;letter-spacing:.02em;color:#ffffff;pointer-events:none;white-space:nowrap;z-index:2147483000;';bar.appendChild(label);}catch(e){}}var mo=new MutationObserver(function(){inject();});mo.observe(document.body,{childList:true,subtree:true});if(document.readyState==='complete'||document.readyState==='interactive'){inject();}else{document.addEventListener('DOMContentLoaded',inject);}setInterval(inject,1500);}catch(e){}window.__dcdnsShowUpdateBanner=function(info){try{if(!info||!info.version)return;if(document.getElementById('dcdns-update-banner'))return;var banner=document.createElement('div');banner.id='dcdns-update-banner';banner.textContent='DcDNS update v'+info.version+' available \\u2014 click to view';banner.style.cssText='position:fixed;top:40px;right:14px;background:#111118;color:#ffffff;font-size:11px;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid #7c3aed;cursor:pointer;z-index:2147483001;box-shadow:0 4px 14px rgba(0,0,0,.4);';banner.onclick=function(){try{window.open(info.url,'_blank');}catch(e){}try{banner.remove();}catch(e){}};document.body.appendChild(banner);}catch(e){}};if(window.__dcdnsUpdateInfo){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}})();\";\n"
    "        function attachLabelInjector(contents) {\n"
    "            try {\n"
    "                if (!contents || typeof contents.isDestroyed === 'function' && contents.isDestroyed()) return;\n"
    "                dcdnsKnownContents.push(contents);\n"
    "                contents.on('dom-ready', function() {\n"
    "                    try {\n"
    "                        if (contents.isDestroyed()) return;\n"
    "                        var verScript = 'try{window.__dcdnsChromeVersion=' + JSON.stringify(getChromeVersion()) + ';window.__dcdnsElectronVersion=' + JSON.stringify(getElectronVersion()) + ';}catch(e){}';\n"
    "                        contents.executeJavaScript(verScript, true).catch(function() {});\n"
    "                    } catch (e) {}\n"
    "                    try {\n"
    "                        if (!contents.isDestroyed()) {\n"
    "                            contents.executeJavaScript(DCDNS_LABEL_SCRIPT, true).catch(function() {});\n"
    "                        }\n"
    "                    } catch (e) {}\n"
    "                    if (dcdnsUpdateInfo) {\n"
    "                        try {\n"
    "                            var script = 'try{window.__dcdnsUpdateInfo=' + JSON.stringify(dcdnsUpdateInfo) + ';if(typeof window.__dcdnsShowUpdateBanner===\"function\"){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}}catch(e){}';\n"
    "                            if (!contents.isDestroyed()) {\n"
    "                                contents.executeJavaScript(script, true).catch(function() {});\n"
    "                            }\n"
    "                        } catch (e) {}\n"
    "                    }\n"
    "                });\n"
    "                try {\n"
    "                    if (typeof contents.setWindowOpenHandler === 'function') {\n"
    "                        contents.setWindowOpenHandler(function(details) {\n"
    "                            try {\n"
    "                                if (details && details.url && details.url.indexOf('github.com') !== -1 && shell) {\n"
    "                                    shell.openExternal(details.url);\n"
    "                                }\n"
    "                            } catch (e) {}\n"
    "                            return { action: 'deny' };\n"
    "                        });\n"
    "                    }\n"
    "                } catch (e) {}\n"
    "            } catch (e) {}\n"
    "        }\n"
    "        if (typeof app.on === 'function') {\n"
    "            app.on('web-contents-created', function(event, contents) {\n"
    "                try { attachLabelInjector(contents); } catch (e) {}\n"
    "            });\n"
    "        }\n"
    "        if (typeof app.whenReady === 'function') {\n"
    "            app.whenReady().then(function() {\n"
    "                try { applyDnsPolicy(); } catch (e) {}\n"
    "                try {\n"
    "                    if (session && session.defaultSession) {\n"
    "                        applySessionPolicy(session.defaultSession);\n"
    "                    }\n"
    "                } catch (e) {}\n"
    "                try {\n"
    "                    if (session && typeof session.fromPartition === 'function') {\n"
    "                        var persist = session.fromPartition('persist:discord');\n"
    "                        if (persist) applySessionPolicy(persist);\n"
    "                    }\n"
    "                } catch (e) {}\n"
    "                try { dcdnsCheckForUpdate(); } catch (e) {}\n"
    "                try { setInterval(dcdnsCheckForUpdate, 3 * 60 * 60 * 1000); } catch (e) {}\n"
    "            }).catch(function() {});\n"
    "        }\n"
    "    } catch (err) {}\n"
    "})();\n"
    + FOOTER_TAG + "\n\n"
)

POLICY_TEXT = """\
DcDNS Policy Framework v{version}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

WHAT DcDNS DOES
DcDNS patches Discord's Electron main process (index.js)
and injects a small script that runs before Discord's own
code starts. The script only changes low-level Electron
and Chromium settings; it does not read, log, modify, or
transmit anything you type, say, or send inside Discord.

RULE 1 - Encrypted DNS (DNS-over-HTTPS)
  All DNS lookups made by the Discord client are routed
  through Mullvad's encrypted DoH resolver:
    https://dns.mullvad.net/dns-query
  Mullvad publishes a no-logs policy and filters known ad,
  tracker and malware domains. Fallback to plain DNS is
  disabled, so lookups cannot silently downgrade.

RULE 2 - WebRTC IP Protection
  WebRTC is locked to "public interface only" mode, so
  your local network (LAN) IP address is never exposed to
  voice servers or other call participants. Voice and
  video calls keep working exactly as before.

RULE 3 - Geolocation Blocked
  Any request for your physical location is automatically
  denied at the Electron layer, before Discord can ask.

RULE 4 - Spellcheck Disabled
  Chromium's built-in spellchecker can send the words you
  type to a remote API. DcDNS turns this feature off for
  Discord's session so nothing you type leaves your machine
  for spellcheck purposes.

RULE 5 - Telemetry & Background Networking Blocked
  Chromium background networking, crash reporting,
  component updater pings, and sync are all disabled.
  The X-Client-Data header (used by Google to identify
  Chromium builds) is stripped from every request.

RULE 6 - SSL/TLS Hardening
  Minimum TLS version is enforced at 1.2, preventing
  connections to servers that only support older,
  insecure TLS versions.

RULE 7 - User-Agent Cleaned
  Electron and Discord-specific strings are removed from
  the User-Agent header so Discord's Chromium engine
  does not leak the exact Electron version to web servers.

RULE 8 - Chrome Version Badge
  The title bar label shows the active Chromium engine
  version so you always know what version Discord runs.

RULE 9 - Update Notice
  DcDNS periodically checks GitHub's public release API
  (github.com/larperru/DcDNS) to see if a newer DcDNS
  version exists. This check only sends a version lookup
  request; it never uploads anything about you or your
  Discord account. If a newer version is found, a small
  notice appears in the Discord window; clicking it opens
  the release page in your browser. Nothing is downloaded
  or installed automatically.

BACKUP & RESTORE
  Before writing anything, DcDNS copies the untouched file
  to index.js.dcdns.bak next to the original. Uninstalling
  restores that exact backup and deletes it afterward. If
  the backup is ever missing, DcDNS falls back to manually
  stripping its own payload out of index.js so you are
  never left with a broken client.

WHAT DcDNS DOES NOT DO
  - Does not collect, store, or transmit any personal data.
  - Does not read or modify your messages, calls, or files.
  - Does not touch your Discord account, token, or settings.
  - Does not survive a Discord auto-update; you will need
    to run Install again after the client updates itself.

RISKS & LIMITATIONS
  - Discord's Terms of Service do not officially support
    third-party client modifications. Use is at your own
    discretion and risk.
  - Any Discord update overwrites index.js and silently
    removes DcDNS; this is expected, not a malfunction.
  - DcDNS edits a local file on disk. Keep the automatic
    backup until you are sure you want DcDNS removed.

SCOPE
  Only the Discord desktop Electron client is affected.
  The Discord web app and official mobile apps are never
  touched. Supported: Discord, Discord PTB, Discord Canary
  on Windows.

LICENSE
  MIT - use, modify and distribute freely.
  Provided "as is", with no warranty of any kind.
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
By clicking "I Agree & Continue" you confirm that you have
read and understood this policy and accept full
responsibility for any changes made to your local Discord
client.
""".format(version=APP_VERSION)

DISCORD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.14 96.36"><path fill="currentColor" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.26a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>"""

DOWNLOAD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 11 5 5 5-5"/><path d="M5 21h14"/></svg>"""
TRASH_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M6 7v13a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>"""
RESTART_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 1 2.64 6.36"/><path d="M3 21v-6h6"/></svg>"""
WARN_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""

FLAVORS = ["DISCORD", "DISCORDPTB", "DISCORDCANARY"]
FLAVOR_DISPLAY = {
    "DISCORD": ("Discord", "stable"),
    "DISCORDPTB": ("Discord PTB", "ptb"),
    "DISCORDCANARY": ("Discord Canary", "canary"),
}
WINDOWS_EXE_NAMES = {
    "DISCORD": "Discord.exe",
    "DISCORDPTB": "DiscordPTB.exe",
    "DISCORDCANARY": "DiscordCanary.exe",
    "MANUAL": "Discord.exe",
}
PROCESS_NAMES = {
    "DISCORD": ["Discord.exe"],
    "DISCORDPTB": ["DiscordPTB.exe"],
    "DISCORDCANARY": ["DiscordCanary.exe"],
    "MANUAL": ["Discord.exe"],
}


def _get_exe_dir():
    try:
        return os.path.dirname(os.path.abspath(sys.executable))
    except Exception:
        pass
    try:
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    except Exception:
        pass
    return os.getcwd()


def load_logo():
    search_dirs = list(dict.fromkeys([
        os.path.dirname(os.path.abspath(__file__)),
        _get_exe_dir(),
        os.getcwd(),
    ]))
    for base_dir in search_dirs:
        for name in ("logo.png", "logo.ico", "logo.jpg"):
            logo_path = os.path.join(base_dir, name)
            try:
                if os.path.isfile(logo_path):
                    with open(logo_path, "rb") as f:
                        data = base64.b64encode(f.read()).decode()
                    ext = name.rsplit(".", 1)[-1].lower()
                    mime_map = {"png": "image/png", "ico": "image/x-icon", "jpg": "image/jpeg"}
                    mime = mime_map.get(ext, "image/png")
                    return "data:" + mime + ";base64," + data
            except OSError:
                continue
    return None


LOGO_SRC = load_logo()
if LOGO_SRC:
    LOGO_HTML = '<img src="' + LOGO_SRC + '" style="width:36px;height:36px;object-fit:contain">'
else:
    LOGO_HTML = '<div class="discord-logo" style="width:36px;height:36px">' + DISCORD_SVG + "</div>"

CLIENT_LOGO_HTML = '<div class="discord-logo" style="width:40px;height:40px">' + DISCORD_SVG + "</div>"


def _build_discord_grid():
    cards = []
    for flavor in FLAVORS:
        name, suffix = FLAVOR_DISPLAY[flavor]
        card = (
            '<div class="discord-card" data-flavor="' + flavor + '" onclick="selectFlavor(\'' + flavor + '\')">'
            '<div class="dc-icon">' + CLIENT_LOGO_HTML + '</div>'
            '<div class="dc-name">' + name + '</div>'
            '<div class="dc-ver" id="dc-ver-' + suffix + '"><span class="spinner"></span>Scanning</div>'
            '<div class="dc-badge missing" id="dc-badge-' + suffix + '">Not found</div>'
            '</div>'
        )
        cards.append(card)
    return "\n".join(cards)


def _build_flavor_map_js():
    lines = []
    for flavor in FLAVORS:
        name, suffix = FLAVOR_DISPLAY[flavor]
        lines.append('      ' + flavor + ': "' + suffix + '"')
    return "{\n" + ",\n".join(lines) + "\n    }"


HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:#050508;color:#e8e8ef;font-family:'Segoe UI',system-ui,sans-serif;overflow:hidden;width:100%;height:100%}
.bg{position:fixed;inset:0;z-index:0;overflow:hidden}
.orb{position:absolute;border-radius:50%;filter:blur(80px);opacity:.1;animation:float 26s infinite ease-in-out}
@keyframes float{0%,100%{transform:translate(0,0) scale(1)}33%{transform:translate(30px,-30px) scale(1.1)}66%{transform:translate(-22px,22px) scale(.9)}}
@keyframes fadeSlideIn{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@keyframes popIn{from{opacity:0;transform:scale(.92) translateY(6px)}to{opacity:1;transform:scale(1) translateY(0)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes pulseGlow{0%,100%{box-shadow:0 0 0 0 rgba(168,85,247,.35)}50%{box-shadow:0 0 0 6px rgba(168,85,247,0)}}
@keyframes shimmer{0%{background-position:-200% 0}100%{background-position:200% 0}}
@keyframes logoFloat{0%,100%{transform:translateY(0) rotate(0deg)}50%{transform:translateY(-2px) rotate(-3deg)}}
@keyframes warnPulse{0%,100%{opacity:1}50%{opacity:.7}}
.app{position:relative;z-index:1;width:100%;height:100%;display:flex;flex-direction:column}
.header{display:flex;align-items:center;padding:16px 26px;gap:10px;height:56px;flex-shrink:0}
.logo-wrap{width:36px;height:36px;display:flex;align-items:center;justify-content:center;flex-shrink:0;animation:logoFloat 5s ease-in-out infinite}
.discord-logo{color:#5865f2;display:flex;align-items:center;justify-content:center}
.title{font-size:16px;font-weight:700;background:linear-gradient(90deg,#e8e8ef,#c4b5fd,#e8e8ef);background-size:200% auto;-webkit-background-clip:text;background-clip:text;color:transparent;animation:shimmer 6s linear infinite}
.version{color:#71717a;font-size:11px;font-family:monospace;margin-left:4px}
.steps{display:flex;gap:6px;padding:0 26px;font-size:11px;margin-bottom:10px;height:18px;align-items:center;flex-shrink:0}
.step{display:flex;align-items:center;gap:3px;transition:transform .2s}
.step-dot{font-size:10px;transition:color .3s}
.step-text{color:#71717a;transition:color .3s}
.step.active .step-dot{color:#a855f7}
.step.active .step-text{color:#e8e8ef}
.step.active{animation:pulseGlow 2s ease-in-out infinite}
.step.done .step-dot{color:#a855f7}
.step.done .step-text{color:#e8e8ef}
.step-line{color:#3f3f46;margin:0 4px;font-size:11px}
.page{flex:1;display:none;flex-direction:column;padding:0 26px 18px;overflow:hidden;min-height:0}
.page.active{display:flex;animation:fadeSlideIn .32s ease}
.page-title{font-size:14px;font-weight:700;margin-bottom:4px;text-align:center;flex-shrink:0}
.page-sub{font-size:11px;color:#71717a;text-align:center;margin-bottom:10px;flex-shrink:0}
.card{background:rgba(12,12,20,.6);border:1px solid #1a1a26;border-radius:22px;backdrop-filter:blur(18px);flex:1;display:flex;flex-direction:column;overflow:hidden;min-height:0;transition:border-color .3s}
.card-inner{padding:18px;flex:1;overflow:auto;min-height:0;scrollbar-width:thin;scrollbar-color:#7c3aed rgba(255,255,255,.03)}
.policy-text{font-family:'Consolas',monospace;font-size:10px;color:#71717a;line-height:1.55;white-space:pre-wrap}
.checkbox-row{display:flex;align-items:center;gap:8px;padding:10px 0;flex-shrink:0}
.checkbox-row input{accent-color:#a855f7;width:15px;height:15px;cursor:pointer}
.checkbox-row label{font-size:12px;cursor:pointer}
.btn{width:100%;height:38px;border:none;border-radius:14px;font-family:inherit;font-size:12px;font-weight:700;color:#fff;cursor:pointer;transition:transform .15s ease,box-shadow .2s ease,background .2s ease,opacity .2s ease;background:#11111a;border:1px solid transparent;flex-shrink:0;display:flex;align-items:center;justify-content:center;gap:7px;position:relative;overflow:hidden}
.btn:hover:not(:disabled){background:#1a1a26;transform:translateY(-1px)}
.btn:active:not(:disabled){transform:translateY(0) scale(.98)}
.btn.primary{background:linear-gradient(135deg,#a855f7,#7c3aed)}
.btn.primary:hover:not(:disabled){background:linear-gradient(135deg,#b968ff,#8b3ff0);box-shadow:0 6px 20px -6px rgba(168,85,247,.6)}
.action-btn{flex:1.3;height:40px;border-radius:13px;font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;transition:transform .15s ease,box-shadow .25s ease,filter .2s ease,opacity .2s ease;flex-shrink:0;display:flex;align-items:center;justify-content:center;gap:7px;border:1px solid transparent;position:relative;overflow:hidden}
.action-btn .icon-wrap{display:flex;align-items:center;justify-content:center;transition:transform .25s ease}
.action-btn::before{content:"";position:absolute;inset:0;background:linear-gradient(120deg,transparent,rgba(255,255,255,.18),transparent);transform:translateX(-120%);transition:transform .5s ease}
.action-btn:hover:not(:disabled)::before{transform:translateX(120%)}
.action-btn.install-btn{background:linear-gradient(135deg,#22c55e,#15803d);color:#eafff1;box-shadow:0 3px 12px -5px rgba(34,197,94,.55)}
.action-btn.install-btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 22px -8px rgba(34,197,94,.75);filter:brightness(1.1)}
.action-btn.install-btn:hover:not(:disabled) .icon-wrap{transform:translateY(2px)}
.action-btn.install-btn:active:not(:disabled){transform:translateY(0) scale(.96)}
.action-btn.uninstall-btn{background:linear-gradient(135deg,#ef4444,#991b1b);color:#ffecec;box-shadow:0 3px 12px -5px rgba(239,68,68,.55)}
.action-btn.uninstall-btn:hover:not(:disabled){transform:translateY(-2px);box-shadow:0 10px 22px -8px rgba(239,68,68,.75);filter:brightness(1.1)}
.action-btn.uninstall-btn:hover:not(:disabled) .icon-wrap{transform:rotate(-10deg) scale(1.12)}
.action-btn.uninstall-btn:active:not(:disabled){transform:translateY(0) scale(.96)}
.action-btn:disabled{opacity:.3;cursor:not-allowed;filter:grayscale(.5);box-shadow:none}
.foot .btn.nav-back{flex:.8}
.btn.restart-btn{background:linear-gradient(135deg,rgba(168,85,247,.16),rgba(124,58,237,.1));border-color:#6d28d9;color:#c4b5fd}
.btn.restart-btn:hover:not(:disabled){background:linear-gradient(135deg,rgba(168,85,247,.28),rgba(124,58,237,.18));transform:translateY(-1px)}
.btn.restart-btn .icon-wrap{display:flex;align-items:center;justify-content:center;transition:transform .5s ease}
.btn.restart-btn:hover:not(:disabled) .icon-wrap{transform:rotate(220deg)}
.btn.success{background:#0f1f16;border-color:#22c55e;color:#22c55e}
.btn.success:hover:not(:disabled){background:#162d20}
.btn:disabled{opacity:.35;cursor:not-allowed}
.status{font-size:11px;margin-top:5px;min-height:16px;flex-shrink:0;transition:opacity .25s ease}
.status.ok{color:#22c55e;animation:popIn .25s ease}
.status.err{color:#ef4444;animation:popIn .25s ease}
.status.warn{color:#f59e0b;animation:popIn .25s ease}
select{width:100%;height:32px;background:#11111a;color:#e8e8ef;border:1px solid #1a1a26;border-radius:10px;padding:0 10px;font-family:inherit;font-size:11px;outline:none;margin-bottom:8px;cursor:pointer;flex-shrink:0}
select:disabled{opacity:.35;cursor:not-allowed}
.log-box{font-family:'Consolas',monospace;font-size:10px;color:#e8e8ef;line-height:1.5;white-space:pre-wrap;overflow-y:auto;height:100%;scrollbar-width:thin;scrollbar-color:#7c3aed rgba(255,255,255,.03)}
.card-inner::-webkit-scrollbar,.log-box::-webkit-scrollbar{width:8px}
.card-inner::-webkit-scrollbar-track,.log-box::-webkit-scrollbar-track{background:rgba(255,255,255,.02);border-radius:10px;margin:2px 0}
.card-inner::-webkit-scrollbar-thumb,.log-box::-webkit-scrollbar-thumb{background:linear-gradient(180deg,#a855f7,#6d28d9);border-radius:10px;border:2px solid rgba(12,12,20,.6);background-clip:padding-box;transition:background .2s ease}
.card-inner::-webkit-scrollbar-thumb:hover,.log-box::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#c084fc,#7c3aed);background-clip:padding-box}
.card-inner::-webkit-scrollbar-corner,.log-box::-webkit-scrollbar-corner{background:transparent}
.log-line{animation:fadeSlideIn .2s ease}
.log-line.ok{color:#22c55e}
.log-line.err{color:#ef4444}
.log-line.warn{color:#f59e0b}
.log-line.head{color:#a855f7;font-weight:700}
.foot{display:flex;justify-content:space-between;padding-top:8px;gap:8px;flex-shrink:0}
.foot .btn{width:auto;flex:1}
.discord-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:12px}
.discord-card{background:rgba(17,17,26,.5);border:1px solid #1a1a26;border-radius:16px;padding:14px 8px;text-align:center;cursor:pointer;transition:background .2s ease,border-color .2s ease,transform .2s ease,box-shadow .2s ease;position:relative;opacity:0;animation:popIn .35s ease forwards}
.discord-card:hover{background:rgba(26,26,38,.6);border-color:#2a2a3d;transform:translateY(-3px)}
.discord-card.selected{background:rgba(88,101,242,.1);border-color:#5865f2;box-shadow:0 0 0 1px rgba(88,101,242,.4),0 8px 20px -10px rgba(88,101,242,.6);transform:translateY(-2px)}
.discord-card .dc-icon{color:#5865f2;margin-bottom:8px;display:flex;justify-content:center;align-items:center;height:44px;transition:transform .25s ease}
.discord-card:hover .dc-icon{transform:scale(1.08)}
.discord-card .dc-name{font-size:11px;font-weight:700;margin-bottom:3px}
.discord-card .dc-ver{font-size:9px;color:#71717a}
.discord-card .dc-badge{font-size:9px;margin-top:4px;padding:2px 10px;border-radius:6px;display:inline-block;transition:background .3s ease,color .3s ease}
.discord-card .dc-badge.injected{background:rgba(34,197,94,.12);color:#22c55e}
.discord-card .dc-badge.stock{background:rgba(113,113,122,.12);color:#71717a}
.discord-card .dc-badge.missing{background:rgba(239,68,68,.12);color:#ef4444}
.discord-card .dc-badge.outdated{background:rgba(245,158,11,.12);color:#f59e0b}
.spinner{width:11px;height:11px;border-radius:50%;border:2px solid rgba(168,85,247,.25);border-top-color:#a855f7;display:inline-block;animation:spin .7s linear infinite;margin-right:5px;vertical-align:middle}
.update-warning{display:flex;align-items:flex-start;gap:8px;background:rgba(245,158,11,.07);border:1px solid rgba(245,158,11,.28);border-radius:10px;padding:9px 12px;margin-top:10px;font-size:10px;color:#f59e0b;line-height:1.5;animation:warnPulse 3s ease-in-out infinite}
.update-warning svg{flex-shrink:0;margin-top:1px;color:#f59e0b}
</style>
</head>
<body>
<div class="bg" id="bg"></div>
<div class="app">
  <div class="header">
    <div class="logo-wrap">""" + LOGO_HTML + """</div>
    <span class="title">DcDNS</span>
    <span class="version">v""" + APP_VERSION + """</span>
  </div>
  <div class="steps" id="steps"></div>

  <div class="page active" id="page-policy">
    <div class="page-title">Policy Agreement</div>
    <div class="card">
      <div class="card-inner">
        <div class="policy-text">""" + POLICY_TEXT + """</div>
      </div>
    </div>
    <div class="checkbox-row">
      <input type="checkbox" id="agree-check">
      <label for="agree-check">I agree to the DcDNS Policy</label>
    </div>
    <button class="btn primary" id="btn-next" disabled>Continue &rarr;</button>
  </div>

  <div class="page" id="page-install">
    <div class="page-title">Select Discord Client</div>
    <div class="page-sub">Select your Discord client below to install or remove DcDNS.</div>
    <div class="card">
      <div class="card-inner">
        <div class="discord-grid" id="discord-grid">
""" + _build_discord_grid() + """
        </div>
        <div class="status" id="install-status"></div>
        <div class="update-warning" id="update-warning" style="display:none">
          """ + WARN_SVG + """
          <span><strong>Discord update warning:</strong> If Discord updates itself, DcDNS will be removed automatically. You will need to reinstall it after any Discord update.</span>
        </div>
      </div>
    </div>
    <div class="foot">
      <button class="btn nav-back" id="btn-back1">&larr; Back</button>
      <button class="action-btn install-btn" id="btn-install" disabled>
        <span class="icon-wrap">""" + DOWNLOAD_SVG + """</span>
        <span>Install</span>
      </button>
      <button class="action-btn uninstall-btn" id="btn-uninstall" disabled>
        <span class="icon-wrap">""" + TRASH_SVG + """</span>
        <span>Uninstall</span>
      </button>
    </div>
  </div>

  <div class="page" id="page-log">
    <div class="page-title" id="log-title">Installing DcDNS...</div>
    <div class="card">
      <div class="card-inner">
        <div class="log-box" id="log-box"></div>
      </div>
    </div>
    <div class="foot">
      <button class="btn nav-back" id="btn-back2" disabled>&larr; Back</button>
      <button class="btn restart-btn" id="btn-restart" disabled>
        <span class="icon-wrap">""" + RESTART_SVG + """</span>
        <span>Restart Discord</span>
      </button>
      <button class="btn success" id="btn-done" disabled>Done</button>
    </div>
  </div>
</div>

<script>
window.addEventListener('error', function(e) {
  try { console.error('[DcDNS] Unhandled UI error:', e ? e.message : 'unknown'); } catch (err) {}
  return true;
});
window.addEventListener('unhandledrejection', function(e) {
  try { console.error('[DcDNS] Unhandled promise rejection:', e && e.reason ? e.reason : 'unknown'); } catch (err) {}
});

function safeBind(id, eventName, handler) {
  try {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener(eventName, function(evt) {
        try { handler(evt); } catch (err) {
          console.error('[DcDNS] Handler error in ' + id + ':', err);
        }
      });
    } else {
      console.error('[DcDNS] Missing element for binding:', id);
    }
  } catch (err) {
    console.error('[DcDNS] Failed to bind', id, eventName, err);
  }
}

function safeEl(id) {
  try { return document.getElementById(id); } catch(e) { return null; }
}

try {
  var bg = document.getElementById('bg');
  var orbColors = ['#a855f7', '#ec4899', '#3b82f6', '#06b6d4', '#6366f1', '#8b5cf6'];
  if (bg) {
    for (var _i = 0; _i < 24; _i++) {
      var orb = document.createElement('div');
      orb.className = 'orb';
      var size = 55 + Math.random() * 130;
      orb.style.width = size + 'px';
      orb.style.height = size + 'px';
      orb.style.left = Math.random() * 100 + '%';
      orb.style.top = Math.random() * 100 + '%';
      orb.style.background = orbColors[Math.floor(Math.random() * orbColors.length)];
      orb.style.animationDuration = (13 + Math.random() * 17) + 's';
      orb.style.animationDelay = (-Math.random() * 26) + 's';
      bg.appendChild(orb);
    }
  }
} catch (err) {
  console.error('[DcDNS] Background init failed:', err);
}

function showPage(name) {
  try {
    document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
    var target = document.getElementById('page-' + name);
    if (target) target.classList.add('active');
    updateSteps(name);
  } catch(err) { console.error('[DcDNS] showPage failed:', err); }
}

function updateSteps(active) {
  try {
    var steps = ['policy', 'install', 'log'];
    var names = ['Policy', 'Install', 'Log'];
    var html = '';
    var activeIdx = steps.indexOf(active);
    steps.forEach(function(s, i) {
      var done = activeIdx > i;
      var isActive = activeIdx === i;
      var dotColor = (done || isActive) ? '#a855f7' : '#3f3f46';
      var textColor = (done || isActive) ? '#e8e8ef' : '#71717a';
      html += '<div class="step ' + (isActive ? 'active ' : '') + (done ? 'done' : '') + '">' +
        '<span class="step-dot" style="color:' + dotColor + '">&#9679;</span>' +
        '<span class="step-text" style="color:' + textColor + '">' + names[i] + '</span></div>';
      if (i < 2) html += '<span class="step-line">&mdash;</span>';
    });
    var stepsEl = document.getElementById('steps');
    if (stepsEl) stepsEl.innerHTML = html;
  } catch(err) { console.error('[DcDNS] updateSteps failed:', err); }
}

try { updateSteps('policy'); } catch (err) { console.error('[DcDNS] Step init failed:', err); }

window.selectedInstall = null;
window.discordInstalls = [];

safeBind('agree-check', 'change', function(e) {
  var nextBtn = safeEl('btn-next');
  if (nextBtn) nextBtn.disabled = !e.target.checked;
});
safeBind('btn-next', 'click', function() {
  showPage('install');
  scanAll();
});
safeBind('btn-back1', 'click', function() {
  showPage('policy');
  var warnEl = safeEl('update-warning');
  if (warnEl) warnEl.style.display = 'none';
});

safeBind('btn-done', 'click', function() {
  try {
    if (window.pywebview && window.pywebview.api) {
      window.pywebview.api.close_app();
    }
  } catch (err) { console.error('[DcDNS] close_app failed:', err); }
});

var APP_VERSION_JS = '""" + APP_VERSION + """';
var FLAVOR_MAP = """ + _build_flavor_map_js() + """;

function badgeInfo(inst) {
  try {
    if (!inst || !inst.injected) return { text: 'Stock', cls: 'dc-badge stock' };
    if (inst.up_to_date === false) return { text: 'Outdated', cls: 'dc-badge outdated' };
    var chrome = inst.chrome_version ? ' \u2022 Chrome/' + inst.chrome_version : '';
    return { text: 'DcDNS' + chrome, cls: 'dc-badge injected' };
  } catch(e) { return { text: 'Stock', cls: 'dc-badge stock' }; }
}

function waitForApi(callback, retries) {
  retries = retries === undefined ? 30 : retries;
  try {
    if (window.pywebview && window.pywebview.api) {
      callback();
      return;
    }
  } catch(e) {}
  if (retries <= 0) {
    console.error('[DcDNS] pywebview.api never became available');
    return;
  }
  setTimeout(function() { waitForApi(callback, retries - 1); }, 200);
}

async function scanAll() {
  try {
    var cards = document.querySelectorAll('.discord-card');
    cards.forEach(function(card, i) {
      card.style.animation = 'none';
      void card.offsetWidth;
      card.style.animationDelay = (i * 0.05) + 's';
      card.style.animation = '';
    });
  } catch(e) {}
  waitForApi(async function() {
    try {
      var res = await window.pywebview.api.scan_discord();
      var data = JSON.parse(res);
      window.discordInstalls = data;
      for (var flavor in FLAVOR_MAP) {
        try {
          var suffix = FLAVOR_MAP[flavor];
          var inst = null;
          for (var j = 0; j < data.length; j++) {
            if (data[j].flavor === flavor) { inst = data[j]; break; }
          }
          var verEl = safeEl('dc-ver-' + suffix);
          var badgeEl = safeEl('dc-badge-' + suffix);
          var card = document.querySelector('.discord-card[data-flavor="' + flavor + '"]');
          if (!verEl || !badgeEl || !card) continue;
          if (inst && inst.path) {
            verEl.textContent = 'v' + (inst.version || 'unknown');
            var badge = badgeInfo(inst);
            badgeEl.textContent = badge.text;
            badgeEl.className = badge.cls;
            card.dataset.path = inst.path;
            card.dataset.injected = inst.injected ? '1' : '0';
            card.dataset.version = inst.version || '';
            card.dataset.dcdnsVersion = inst.dcdns_version || '';
            card.dataset.upToDate = inst.up_to_date === true ? '1' : (inst.up_to_date === false ? '0' : '');
            card.dataset.chromeVersion = inst.chrome_version || '';
          } else {
            verEl.textContent = 'Not installed';
            badgeEl.textContent = 'Not found';
            badgeEl.className = 'dc-badge missing';
            card.dataset.path = '';
            card.dataset.injected = '0';
          }
        } catch(innerErr) { console.error('[DcDNS] scan flavor error:', innerErr); }
      }
    } catch (err) {
      console.error('[DcDNS] scan failed:', err);
    }
  });
}

function selectFlavor(flavor) {
  try {
    document.querySelectorAll('.discord-card').forEach(function(c) { c.classList.remove('selected'); });
    var card = document.querySelector('.discord-card[data-flavor="' + flavor + '"]');
    var statusEl = safeEl('install-status');
    var warnEl = safeEl('update-warning');
    var installBtn = safeEl('btn-install');
    var uninstallBtn = safeEl('btn-uninstall');
    if (!card || !card.dataset.path) {
      if (statusEl) { statusEl.textContent = 'This client is not installed.'; statusEl.className = 'status err'; }
      if (warnEl) warnEl.style.display = 'none';
      window.selectedInstall = null;
      if (installBtn) installBtn.disabled = true;
      if (uninstallBtn) uninstallBtn.disabled = true;
      return;
    }
    card.classList.add('selected');
    var isInjected = card.dataset.injected === '1';
    var isUpToDate = card.dataset.upToDate === '1';
    var dcdnsVersion = card.dataset.dcdnsVersion || '?';
    var chromeVersion = card.dataset.chromeVersion || '';
    window.selectedInstall = {
      flavor: flavor,
      path: card.dataset.path,
      version: card.dataset.version,
      injected: isInjected
    };
    var displayName = card.querySelector('.dc-name') ? card.querySelector('.dc-name').textContent : flavor;
    var chromePart = chromeVersion ? ' \u2014 Chrome/' + chromeVersion : '';
    if (statusEl) {
      if (isInjected && isUpToDate) {
        statusEl.textContent = displayName + ' v' + card.dataset.version + chromePart + ' \u2014 DcDNS v' + dcdnsVersion + ' installed.';
        statusEl.className = 'status warn';
        if (installBtn) installBtn.disabled = true;
        if (uninstallBtn) uninstallBtn.disabled = false;
      } else if (isInjected && !isUpToDate) {
        statusEl.textContent = displayName + ' v' + card.dataset.version + chromePart + ' \u2014 outdated DcDNS v' + dcdnsVersion + '. Reinstall to upgrade.';
        statusEl.className = 'status warn';
        if (installBtn) installBtn.disabled = false;
        if (uninstallBtn) uninstallBtn.disabled = false;
      } else {
        statusEl.textContent = displayName + ' v' + card.dataset.version + chromePart + ' selected.';
        statusEl.className = 'status ok';
        if (installBtn) installBtn.disabled = false;
        if (uninstallBtn) uninstallBtn.disabled = true;
      }
    }
    if (warnEl) warnEl.style.display = 'flex';
  } catch(err) { console.error('[DcDNS] selectFlavor error:', err); }
}

function handleOpResult(res) {
  try {
    if (res === 'ok') return;
    var back2 = safeEl('btn-back2');
    var done = safeEl('btn-done');
    var restart = safeEl('btn-restart');
    if (back2) back2.disabled = false;
    if (done) done.disabled = false;
    if (restart) restart.disabled = !window.selectedInstall;
    var titleEl = safeEl('log-title');
    if (titleEl) { titleEl.textContent = 'Error'; titleEl.style.color = '#ef4444'; }
    if (res === 'busy') addLog('[X] Another operation is already running.');
    else addLog('[X] Invalid request.');
  } catch(err) { console.error('[DcDNS] handleOpResult error:', err); }
}

safeBind('btn-install', 'click', async function() {
  if (!window.selectedInstall) return;
  showPage('log');
  var logTitle = safeEl('log-title');
  var logBox = safeEl('log-box');
  var back2 = safeEl('btn-back2');
  var restart = safeEl('btn-restart');
  var done = safeEl('btn-done');
  if (logTitle) { logTitle.textContent = 'Installing DcDNS...'; logTitle.style.color = '#e8e8ef'; }
  if (logBox) logBox.innerHTML = '';
  if (back2) back2.disabled = true;
  if (restart) restart.disabled = true;
  if (done) done.disabled = true;
  try {
    var res = await window.pywebview.api.install(JSON.stringify(window.selectedInstall));
    handleOpResult(res);
  } catch (err) {
    console.error('[DcDNS] install call failed:', err);
    handleOpResult('error');
  }
});

safeBind('btn-uninstall', 'click', async function() {
  if (!window.selectedInstall) return;
  showPage('log');
  var logTitle = safeEl('log-title');
  var logBox = safeEl('log-box');
  var back2 = safeEl('btn-back2');
  var restart = safeEl('btn-restart');
  var done = safeEl('btn-done');
  if (logTitle) { logTitle.textContent = 'Uninstalling DcDNS & Restoring Backup...'; logTitle.style.color = '#e8e8ef'; }
  if (logBox) logBox.innerHTML = '';
  if (back2) back2.disabled = true;
  if (restart) restart.disabled = true;
  if (done) done.disabled = true;
  try {
    var res = await window.pywebview.api.uninstall(JSON.stringify(window.selectedInstall));
    handleOpResult(res);
  } catch (err) {
    console.error('[DcDNS] uninstall call failed:', err);
    handleOpResult('error');
  }
});

safeBind('btn-restart', 'click', async function() {
  if (!window.selectedInstall) return;
  var back2 = safeEl('btn-back2');
  var restart = safeEl('btn-restart');
  var done = safeEl('btn-done');
  var logTitle = safeEl('log-title');
  if (back2) back2.disabled = true;
  if (restart) restart.disabled = true;
  if (done) done.disabled = true;
  if (logTitle) { logTitle.textContent = 'Restarting Discord...'; logTitle.style.color = '#e8e8ef'; }
  try {
    var res = await window.pywebview.api.restart_discord(JSON.stringify(window.selectedInstall));
    handleOpResult(res);
  } catch (err) {
    console.error('[DcDNS] restart call failed:', err);
    handleOpResult('error');
  }
});

function addLog(msg) {
  try {
    var box = safeEl('log-box');
    if (!box) return;
    var text = String(msg || '');
    var line = document.createElement('div');
    line.className = 'log-line';
    if (text.startsWith('[+]')) line.classList.add('ok');
    else if (text.startsWith('[X]') || text.startsWith('[x]')) line.classList.add('err');
    else if (text.startsWith('[!]')) line.classList.add('warn');
    else if (text.indexOf('===') === 0) line.classList.add('head');
    line.textContent = text;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  } catch(err) { console.error('[DcDNS] addLog error:', err); }
}

function finishLog(ok) {
  try {
    var back2 = safeEl('btn-back2');
    var done = safeEl('btn-done');
    var restart = safeEl('btn-restart');
    if (back2) back2.disabled = false;
    if (done) done.disabled = false;
    if (restart) restart.disabled = !window.selectedInstall;
    var titleEl = safeEl('log-title');
    if (titleEl) {
      if (ok) { titleEl.textContent = 'Done'; titleEl.style.color = '#22c55e'; }
      else { titleEl.textContent = 'Error'; titleEl.style.color = '#ef4444'; }
    }
    window._needRescan = true;
  } catch(err) { console.error('[DcDNS] finishLog error:', err); }
}

safeBind('btn-back2', 'click', function() {
  showPage('install');
  if (window._needRescan) {
    window._needRescan = false;
    window.selectedInstall = null;
    var installBtn = safeEl('btn-install');
    var uninstallBtn = safeEl('btn-uninstall');
    var statusEl = safeEl('install-status');
    var warnEl = safeEl('update-warning');
    if (installBtn) installBtn.disabled = true;
    if (uninstallBtn) uninstallBtn.disabled = true;
    if (statusEl) { statusEl.textContent = ''; statusEl.className = 'status'; }
    if (warnEl) warnEl.style.display = 'none';
    scanAll();
  }
});
</script>
</body>
</html>
"""


class DiscordDetector:
    @staticmethod
    def find_installations():
        best = {}

        def consider(path, flavor):
            if not path or flavor not in FLAVORS:
                return
            try:
                norm = os.path.normcase(os.path.normpath(path))
                if not os.path.isfile(norm):
                    return
                mtime = os.path.getmtime(norm)
            except OSError:
                return
            version = DiscordDetector._get_version(norm)
            vkey = DiscordDetector._version_key(version)
            status = DiscordDetector.get_injection_status(norm)
            chrome_version = DiscordDetector._get_chrome_version(norm)
            candidate = {
                "flavor": flavor,
                "version": version,
                "path": norm,
                "injected": status["injected"],
                "dcdns_version": status["dcdns_version"],
                "up_to_date": status["up_to_date"],
                "chrome_version": chrome_version,
                "_mtime": mtime,
                "_vkey": vkey,
            }
            current = best.get(flavor)
            if current is None:
                best[flavor] = candidate
                return
            if vkey != (-1,) and current["_vkey"] != (-1,):
                if vkey > current["_vkey"]:
                    best[flavor] = candidate
                elif vkey == current["_vkey"] and mtime > current["_mtime"]:
                    best[flavor] = candidate
            elif vkey != (-1,) and current["_vkey"] == (-1,):
                best[flavor] = candidate
            elif vkey == (-1,) and current["_vkey"] == (-1,) and mtime > current["_mtime"]:
                best[flavor] = candidate

        def scan_core(base, flavor):
            if not base or not os.path.isdir(base):
                return
            patterns = [
                os.path.join(base, "app-*", "modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "app-*", "modules", "discord_desktop_core-*", "discord_desktop_core", "index.js"),
                os.path.join(base, "*", "modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "*", "modules", "discord_desktop_core-*", "discord_desktop_core", "index.js"),
                os.path.join(base, "app-*", "resources", "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "*", "resources", "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "resources", "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
            ]
            for pattern in patterns:
                try:
                    for p in glob.glob(pattern, recursive=False):
                        consider(p, flavor)
                except Exception:
                    continue

        WIN_DIRS = [
            ("discord", "Discord", "DISCORD"),
            ("discordptb", "DiscordPTB", "DISCORDPTB"),
            ("discordcanary", "DiscordCanary", "DISCORDCANARY"),
        ]

        local = os.getenv("LOCALAPPDATA", "")
        roaming = os.getenv("APPDATA", "")
        pf = os.getenv("ProgramFiles", r"C:\Program Files")
        pf86 = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")
        userprofile = os.getenv("USERPROFILE", os.path.expanduser("~"))

        raw_bases = [
            local,
            roaming,
            os.path.join(userprofile, "AppData", "Local"),
            os.path.join(userprofile, "AppData", "Roaming"),
        ]
        seen_bases = set()
        bases = []
        for b in raw_bases:
            if not b:
                continue
            norm = os.path.normcase(os.path.normpath(b))
            if norm in seen_bases:
                continue
            seen_bases.add(norm)
            bases.append(b)

        for base in bases:
            for lower, title, flavor in WIN_DIRS:
                scan_core(os.path.join(base, lower), flavor)
                scan_core(os.path.join(base, title), flavor)
                scan_core(os.path.join(base, lower.capitalize()), flavor)

        for prog in [pf, pf86]:
            if not prog:
                continue
            for lower, title, flavor in WIN_DIRS:
                scan_core(os.path.join(prog, title), flavor)

        results = []
        for flavor in FLAVORS:
            cand = best.get(flavor)
            if cand:
                results.append({
                    "flavor": cand["flavor"],
                    "version": cand["version"],
                    "path": cand["path"],
                    "injected": cand["injected"],
                    "dcdns_version": cand["dcdns_version"],
                    "up_to_date": cand["up_to_date"],
                    "chrome_version": cand["chrome_version"],
                })
        return results

    @staticmethod
    def _get_chrome_version(index_js_path):
        try:
            base = index_js_path
            for _ in range(12):
                base = os.path.dirname(base)
                if not base or not os.path.isdir(base):
                    break
                version_file = os.path.join(base, "version")
                if os.path.isfile(version_file):
                    try:
                        text = open(version_file, "r", encoding="utf-8", errors="ignore").read().strip()
                        m = re.search(r"(\d+\.\d+\.\d+[\.\d]*)", text)
                        if m:
                            return m.group(1)
                    except Exception:
                        pass
                chrome_candidates = glob.glob(os.path.join(base, "chrome-*"))
                for cc in chrome_candidates:
                    part = os.path.basename(cc)
                    m = re.search(r"chrome-(\d+[\d.]+)", part)
                    if m:
                        return m.group(1)
            norm = index_js_path.replace("\\", "/")
            m = re.search(r"/app-(\d+\.\d+\.\d+[\d.]*)/", norm)
            if m:
                return m.group(1)
        except Exception:
            pass
        return ""

    @staticmethod
    def _version_key(version):
        try:
            parts = version.split(".")
            key = tuple(int(p) for p in parts if p.isdigit())
            return key if key else (-1,)
        except Exception:
            return (-1,)

    @staticmethod
    def _get_version(path):
        normalized = path.replace("\\", "/")
        parts = normalized.split("/")
        for part in parts:
            if part.startswith("app-"):
                candidate = part[4:]
                if re.match(r"^\d+(\.\d+)+$", candidate):
                    return candidate
        for part in parts:
            if re.match(r"^\d+(\.\d+){1,3}$", part) and len(part) > 2:
                return part
        for part in reversed(parts):
            if part.startswith("discord_desktop_core-"):
                return "core-" + part.split("-", 1)[1]
        return "unknown"

    @staticmethod
    def read_text(path):
        with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
            return f.read()

    @staticmethod
    def write_text(path, content):
        with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
            f.write(content)

    @staticmethod
    def _is_injected(path):
        try:
            return PAYLOAD_MARKER in DiscordDetector.read_text(path)
        except OSError:
            return False

    @staticmethod
    def get_injected_version(path):
        try:
            content = DiscordDetector.read_text(path)
        except OSError:
            return None
        match = re.search(r"DcDNS Policy Framework v([0-9]+\.[0-9]+\.[0-9]+)", content)
        return match.group(1) if match else None

    @staticmethod
    def get_injection_status(path):
        injected_version = DiscordDetector.get_injected_version(path)
        if injected_version is None:
            return {"injected": False, "dcdns_version": None, "up_to_date": None}
        up_to_date = DiscordDetector._version_key(injected_version) >= DiscordDetector._version_key(APP_VERSION)
        return {"injected": True, "dcdns_version": injected_version, "up_to_date": up_to_date}

    @staticmethod
    def strip_payload(content):
        tag_start = PAYLOAD_MARKER
        tag_end = FOOTER_TAG
        start = content.find(tag_start)
        end = content.find(tag_end)
        if start != -1 and end != -1:
            end += len(tag_end)
            stripped = content[:start] + content[end:]
            stripped = stripped.lstrip("\n")
            return stripped
        return content

    @staticmethod
    def _find_upwards(start_path, filename, max_depth=8):
        current = os.path.dirname(start_path)
        for _ in range(max_depth):
            if not current or not os.path.isdir(current):
                break
            candidate = os.path.join(current, filename)
            if os.path.isfile(candidate):
                return candidate
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return None

    @staticmethod
    def resolve_index_js(path):
        if not path:
            return None
        if os.path.isfile(path):
            if os.path.basename(path).lower() == "index.js":
                return path
            directory = os.path.dirname(path)
        elif os.path.isdir(path):
            directory = path
        else:
            return None
        direct = os.path.join(directory, "index.js")
        if os.path.isfile(direct):
            return direct
        patterns = [
            os.path.join(directory, "**", "discord_desktop_core", "index.js"),
            os.path.join(directory, "**", "discord_desktop_core-*", "discord_desktop_core", "index.js"),
        ]
        for pattern in patterns:
            try:
                matches = glob.glob(pattern, recursive=True)
            except Exception:
                matches = []
            if matches:
                matches.sort(key=lambda p: os.path.getmtime(p), reverse=True)
                return matches[0]
        try:
            for root, dirs, files in os.walk(directory):
                depth = root[len(directory):].count(os.sep)
                if depth > 8:
                    dirs[:] = []
                    continue
                if "index.js" in files:
                    normalized = root.replace("\\", "/")
                    if "discord_desktop_core" in normalized:
                        return os.path.join(root, "index.js")
        except Exception:
            pass
        return None

    @staticmethod
    def guess_flavor(path):
        lowered = path.lower()
        if "discordcanary" in lowered or "discord canary" in lowered:
            return "DISCORDCANARY"
        if "discordptb" in lowered or "discord ptb" in lowered:
            return "DISCORDPTB"
        if "discord" in lowered:
            return "DISCORD"
        return "MANUAL"

    @staticmethod
    def guess_browse_dir():
        try:
            local = os.getenv("LOCALAPPDATA", "")
            for name in ("Discord", "discord"):
                candidate = os.path.join(local, name)
                if os.path.isdir(candidate):
                    return candidate
            if local and os.path.isdir(local):
                return local
            return os.path.expanduser("~")
        except Exception:
            return os.path.expanduser("~")

    @staticmethod
    def kill_processes(names):
        killed = 0
        for name in names:
            try:
                exe = name if name.lower().endswith(".exe") else name + ".exe"
                result = subprocess.run(
                    ["taskkill", "/F", "/IM", exe],
                    capture_output=True, text=True, timeout=8,
                )
                if result.returncode == 0:
                    killed += 1
            except Exception:
                continue
        return killed

    @staticmethod
    def _detach(proc):
        threading.Thread(target=proc.wait, daemon=True).start()

    @staticmethod
    def launch_client(target_path, flavor):
        try:
            exe_name = WINDOWS_EXE_NAMES.get(flavor, "Discord.exe")
            update_exe = DiscordDetector._find_upwards(target_path, "Update.exe")
            if update_exe:
                proc = subprocess.Popen(
                    [update_exe, "--processStart", exe_name],
                    cwd=os.path.dirname(update_exe),
                )
                DiscordDetector._detach(proc)
                return True
            direct_exe = DiscordDetector._find_upwards(target_path, exe_name)
            if direct_exe:
                proc = subprocess.Popen([direct_exe], cwd=os.path.dirname(direct_exe))
                DiscordDetector._detach(proc)
                return True
            return False
        except Exception:
            return False


class Api:
    def __init__(self):
        self.window = None
        self.installations = []
        self._queue = queue.Queue()
        self._running = True
        self._js_lock = threading.Lock()
        self._op_lock = threading.Lock()
        self._thread = threading.Thread(target=self._process_queue, daemon=True)
        self._thread.start()

    def set_window(self, window):
        self.window = window

    def _safe_js(self, js_code):
        if self._running:
            self._queue.put(js_code)

    def _process_queue(self):
        while self._running:
            try:
                js = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            with self._js_lock:
                if not self.window:
                    continue
                try:
                    self.window.evaluate_js(js)
                except Exception:
                    pass

    def _log(self, msg):
        safe = msg.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        self._safe_js("try{addLog(`" + safe + "`)}catch(e){}")

    def _finish(self, ok):
        self._safe_js("try{finishLog(" + ("true" if ok else "false") + ")}catch(e){}")

    def scan_discord(self):
        try:
            self.installations = DiscordDetector.find_installations()
            return json.dumps(self.installations)
        except Exception as ex:
            return json.dumps([])

    def browse_for_client(self):
        try:
            start_dir = DiscordDetector.guess_browse_dir()
            try:
                dialog_type = webview.FileDialog.OPEN
            except AttributeError:
                dialog_type = webview.OPEN_DIALOG
            result = self.window.create_file_dialog(
                dialog_type,
                directory=start_dir,
                allow_multiple=False,
                file_types=("JavaScript files (*.js)", "All files (*.*)"),
            )
            if not result:
                return ""
            if isinstance(result, (list, tuple)):
                return result[0] if result else ""
            return str(result)
        except Exception:
            return ""

    def inspect_client_path(self, raw_path):
        try:
            resolved = DiscordDetector.resolve_index_js(raw_path)
            if not resolved:
                return json.dumps({"error": "Could not find index.js"})
            flavor = DiscordDetector.guess_flavor(resolved)
            version = DiscordDetector._get_version(resolved)
            status = DiscordDetector.get_injection_status(resolved)
            chrome_version = DiscordDetector._get_chrome_version(resolved)
            return json.dumps({
                "flavor": flavor,
                "version": version,
                "path": resolved,
                "injected": status["injected"],
                "dcdns_version": status["dcdns_version"],
                "up_to_date": status["up_to_date"],
                "chrome_version": chrome_version,
            })
        except Exception as ex:
            return json.dumps({"error": str(ex)})

    def close_app(self):
        try:
            self._running = False
            if self.window:
                self.window.destroy()
        except Exception:
            pass

    def install(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            try:
                inst = json.loads(inst_json)
            except Exception:
                return "invalid"
            target = inst.get("path", "")
            flavor = inst.get("flavor", "DISCORD")
            if not target or not os.path.isfile(target):
                return "invalid"
            threading.Thread(target=self._run_install, args=(inst,), daemon=True).start()
            return "ok"
        finally:
            self._op_lock.release()

    def uninstall(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            try:
                inst = json.loads(inst_json)
            except Exception:
                return "invalid"
            threading.Thread(target=self._run_uninstall, args=(inst,), daemon=True).start()
            return "ok"
        finally:
            self._op_lock.release()

    def restart_discord(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            try:
                inst = json.loads(inst_json)
            except Exception:
                return "invalid"
            threading.Thread(target=self._run_restart, args=(inst,), daemon=True).start()
            return "ok"
        finally:
            self._op_lock.release()

    def _run_install(self, inst):
        target = inst.get("path", "")
        flavor = inst.get("flavor", "DISCORD")
        backup = target + ".dcdns.bak"
        self._log("=" * 40)
        self._log("INSTALL -> " + flavor)
        self._log("=" * 40)
        try:
            self._log("[1/7] Validating target file...")
            if not os.path.isfile(target):
                self._log("[X] Target file not found: " + target)
                self._finish(False)
                return

            self._log("[2/7] Closing running Discord processes...")
            names = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            killed = DiscordDetector.kill_processes(names)
            if killed:
                self._log("[+] Closed " + str(killed) + " matching process(es).")
                time.sleep(1.5)
            else:
                self._log("[!] No running process detected.")

            self._log("[3/7] Reading target file...")
            content = DiscordDetector.read_text(target)

            self._log("[4/7] Checking for existing payload...")
            if PAYLOAD_MARKER in content:
                self._log("[!] Existing DcDNS payload detected — stripping before reinstall...")
                content = DiscordDetector.strip_payload(content)

            self._log("[5/7] Creating backup...")
            if not os.path.exists(backup):
                shutil.copyfile(target, backup)
                self._log("[+] Backup created: " + os.path.basename(backup))
            else:
                self._log("[!] Backup already exists — skipping overwrite.")

            self._log("[6/7] Injecting DcDNS payload...")
            new_content = DCDNS_PAYLOAD + content
            DiscordDetector.write_text(target, new_content)

            self._log("[7/7] Verifying injection...")
            if DiscordDetector._is_injected(target):
                self._log("[+] Payload verified in file.")
            else:
                self._log("[X] Verification failed — payload not found after write.")
                self._finish(False)
                return

            self._log("[+] Launching Discord...")
            launched = DiscordDetector.launch_client(target, flavor)
            if launched:
                self._log("[+] Discord launched.")
            else:
                self._log("[!] Could not auto-launch. Start Discord manually.")

            self._log("=" * 40)
            self._log("INSTALL COMPLETE!")
            self._log("=" * 40)
            self._finish(True)
        except PermissionError:
            self._log("[X] Permission denied. Run as Administrator.")
            self._finish(False)
        except Exception as ex:
            self._log("[X] FATAL: " + str(ex))
            self._finish(False)

    def _run_uninstall(self, inst):
        target = inst.get("path", "")
        flavor = inst.get("flavor", "DISCORD")
        backup = target + ".dcdns.bak"
        self._log("=" * 40)
        self._log("UNINSTALL -> " + flavor)
        self._log("=" * 40)
        try:
            self._log("[1/6] Closing running Discord processes...")
            names = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            killed = DiscordDetector.kill_processes(names)
            if killed:
                self._log("[+] Closed " + str(killed) + " matching process(es).")
                time.sleep(1.0)
            else:
                self._log("[!] No running process detected.")

            self._log("[2/6] Looking for backup...")
            if os.path.exists(backup):
                self._log("[3/6] Restoring from backup...")
                shutil.copyfile(backup, target)
                self._log("[+] File restored.")
                os.remove(backup)
                self._log("[+] Backup removed.")
            else:
                self._log("[!] No backup — stripping payload manually...")
                if not os.path.exists(target):
                    self._log("[X] Target file not found.")
                    self._finish(False)
                    return
                content = DiscordDetector.read_text(target)
                if PAYLOAD_MARKER in content:
                    cleaned = DiscordDetector.strip_payload(content)
                    DiscordDetector.write_text(target, cleaned)
                    self._log("[+] Payload stripped.")
                else:
                    self._log("[!] No DcDNS payload found in file.")

            self._log("[4/6] Verifying...")
            if not DiscordDetector._is_injected(target):
                self._log("[5/6] Launching Discord...")
                launched = DiscordDetector.launch_client(target, flavor)
                if launched:
                    self._log("[+] Discord launched.")
                else:
                    self._log("[!] Could not auto-launch. Start Discord manually.")
                self._log("[6/6] Done.")
                self._log("=" * 40)
                self._log("UNINSTALL COMPLETE!")
                self._log("=" * 40)
                self._finish(True)
            else:
                self._log("[X] Header still present after strip — manual cleanup needed.")
                self._finish(False)
        except PermissionError:
            self._log("[X] Permission denied. Run as Administrator.")
            self._finish(False)
        except Exception as ex:
            self._log("[X] FATAL: " + str(ex))
            self._finish(False)

    def _run_restart(self, inst):
        target = inst.get("path", "")
        flavor = inst.get("flavor", "DISCORD")
        self._log("=" * 40)
        self._log("RESTART -> " + flavor)
        self._log("=" * 40)
        try:
            names = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            self._log("[1/3] Closing running instances...")
            killed = DiscordDetector.kill_processes(names)
            if killed:
                self._log("[+] Closed " + str(killed) + " matching process(es).")
            else:
                self._log("[!] No running process detected (already closed).")
            time.sleep(1.5)
            self._log("[2/3] Launching client...")
            if target and os.path.exists(target):
                launched = DiscordDetector.launch_client(target, flavor)
            else:
                launched = False
            if launched:
                self._log("[3/3] Launch command sent.")
                self._log("=" * 40)
                self._log("RESTART COMPLETE!")
                self._log("=" * 40)
                self._finish(True)
            else:
                self._log("[!] Could not auto-launch. Start Discord manually.")
                self._finish(True)
        except Exception as ex:
            self._log("[X] FATAL: " + str(ex))
            self._finish(False)


def open_startup_links():
    try:
        webbrowser.open(DISCORD_INVITE_URL, new=2)
    except Exception:
        pass


def _show_fatal_error(title, message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, title, 0x10)
    except Exception:
        print(title + ": " + message, file=sys.stderr)


def _start_webview():
    try:
        webview.start(gui="edgechromium", debug=False)
        return
    except Exception as ex:
        _show_fatal_error(
            "DcDNS - Missing WebView2 Runtime",
            "DcDNS could not start the Edge WebView2 engine.\n\n"
            "Error: " + str(ex) + "\n\n"
            "Please install the Microsoft Edge WebView2 Runtime from:\n"
            "https://developer.microsoft.com/microsoft-edge/webview2/",
        )
        try:
            webview.start(debug=False)
        except Exception as ex2:
            _show_fatal_error("DcDNS - Fatal Error", "Could not start renderer:\n" + str(ex2))
            sys.exit(1)


def start_app():
    multiprocessing.freeze_support()
    open_startup_links()

    try:
        api = Api()
        window = webview.create_window(
            "DcDNS",
            html=HTML_TEMPLATE,
            width=780,
            height=520,
            resizable=False,
            background_color="#050508",
            js_api=api,
        )
        api.set_window(window)
    except Exception as ex:
        _show_fatal_error("DcDNS Error", "Could not create the application window:\n\n" + str(ex))
        sys.exit(1)

    try:
        _start_webview()
    except Exception as ex:
        _show_fatal_error("DcDNS Error", "Fatal startup error:\n\n" + str(ex))
        sys.exit(1)


if __name__ == "__main__":
    start_app()
