# ==============================================================================
# DcDNS
# ==============================================================================
# Author:      Larper.ru
# Version:     v1.0.4
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
import hashlib
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
APP_VERSION = "1.0.4"

PAYLOAD_MARKER = "/* === [DcDNS Policy Framework"
HEADER_TAG = "/* === [DcDNS Policy Framework v" + APP_VERSION + "] === */"
FOOTER_TAG = "/* === [End DcDNS Policy Framework] === */"

DISCORD_TELEMETRY_PATTERNS = [
    r"/api/v\d+/science",
    r"/api/v\d+/track",
    r"/api/v\d+/metrics",
    r"/api/v\d+/events/stats",
    r"/api/v\d+/analytics",
    r"sentry\.io",
    r"\.sentry\.io",
    r"ingest\.sentry\.io",
    r"o\d+\.ingest\.sentry\.io",
    r"crash\.discord\.com",
    r"crash-reports\.discord\.com",
    r"remote-auth-gateway\.discord\.gg",
    r"discord\.gg/track",
    r"discord\.com/api/v\d+/science",
    r"discord\.com/api/v\d+/track",
    r"reporter\.discord\.com",
    r"discordapp\.com/api/v\d+/science",
    r"discordapp\.com/api/v\d+/track",
    r"api\.mixpanel\.com",
    r"api\.segment\.io",
    r"api\.amplitude\.com",
    r"click\.discord\.com",
]

# ---------------------------------------------------------------------------
# PAYLOAD  (injected into Discord's index.js)
# ---------------------------------------------------------------------------
DCDNS_PAYLOAD = r"""/* === [DcDNS Policy Framework v""" + APP_VERSION + r"""] === */
(function() {
    'use strict';
    try {
        var electron;
        try { electron = require('electron'); } catch(e) { return; }
        var app     = (electron && electron.app)     || (electron && electron.default && electron.default.app);
        var session = (electron && electron.session)  || (electron && electron.default && electron.default.session);
        var shell   = (electron && electron.shell)    || (electron && electron.default && electron.default.shell);
        if (!app) return;

        /* ── Read persisted config from main-process storage ── */
        function readConf() {
            try {
                /* Electron main process has no localStorage – read from a temp file */
                var fs = require('fs');
                var path = require('path');
                var cfgFile = path.join(app.getPath('userData'), 'dcdns_conf.json');
                if (fs.existsSync(cfgFile)) {
                    var raw = fs.readFileSync(cfgFile, 'utf8');
                    return JSON.parse(raw);
                }
            } catch(e) {}
            return {};
        }
        var __conf = readConf();

        /* ── Feature flags (overridable via config) ── */
        var DCDNS_LABEL_ENABLED       = __conf.showLabel       !== false;
        var BLOCK_TELEMETRY_ENABLED   = __conf.blockTelemetry  !== false;
        var BLOCK_WEBRTC_LEAK         = __conf.blockWebrtc     !== false;
        var BLOCK_GEOLOCATION         = __conf.blockGeolocation !== false;
        var DISABLE_SPELLCHECK        = __conf.disableSpellcheck !== false;
        var HARDEN_TLS                = __conf.hardenTls        !== false;
        var CLEAN_USERAGENT           = __conf.cleanUserAgent   !== false;
        var BLOCK_CRASH_REPORTS       = __conf.blockCrashReports !== false;
        var DISABLE_UPDATE_CHECK      = __conf.disableUpdateCheck === true;
        var CUSTOM_DNS_PRIMARY        = (__conf.customDnsPrimary   && __conf.customDnsPrimary.trim())   || 'https://dns.mullvad.net/dns-query';
        var CUSTOM_DNS_FALLBACK       = (__conf.customDnsFallback  && __conf.customDnsFallback.trim())  || 'https://adblock.dns.mullvad.net/dns-query';
        var CUSTOM_USERAGENT          = (__conf.customUserAgent && __conf.customUserAgent.trim()) || '';
        var LABEL_POSITION            = __conf.labelPosition || 'bottom-right';

        /* ── Telemetry URL patterns ── */
        var TELEMETRY_PATTERNS = [
            /\/api\/v\d+\/science/,
            /\/api\/v\d+\/track/,
            /\/api\/v\d+\/metrics/,
            /\/api\/v\d+\/events\/stats/,
            /\/api\/v\d+\/analytics/,
            /sentry\.io/,
            /\.sentry\.io/,
            /ingest\.sentry\.io/,
            /crash\.discord\.com/,
            /crash-reports\.discord\.com/,
            /reporter\.discord\.com/,
            /discordapp\.com\/api\/v\d+\/science/,
            /discordapp\.com\/api\/v\d+\/track/,
            /api\.mixpanel\.com/,
            /api\.segment\.io/,
            /api\.amplitude\.com/,
            /click\.discord\.com/
        ];

        function isTelemetryUrl(url) {
            if (!url || !BLOCK_TELEMETRY_ENABLED) return false;
            for (var i = 0; i < TELEMETRY_PATTERNS.length; i++) {
                if (TELEMETRY_PATTERNS[i].test(url)) return true;
            }
            return false;
        }

        function isCrashUrl(url) {
            if (!url || !BLOCK_CRASH_REPORTS) return false;
            return /crash|sentry|breakpad/i.test(url);
        }

        /* ── Chromium switches ── */
        function safeSwitch(name, value) {
            try {
                if (app.commandLine && typeof app.commandLine.appendSwitch === 'function') {
                    app.commandLine.appendSwitch(name, value !== undefined ? String(value) : undefined);
                }
            } catch (e) {}
        }

        if (typeof app.commandLine !== 'undefined') {
            if (BLOCK_WEBRTC_LEAK) {
                safeSwitch('force-webrtc-ip-handling-policy', 'default_public_interface_only');
                safeSwitch('webrtc-ip-handling-policy',       'default_public_interface_only');
            }
            safeSwitch('disable-background-networking',         '1');
            safeSwitch('disable-client-side-phishing-detection','1');
            safeSwitch('disable-component-update',              '1');
            safeSwitch('disable-default-apps',                  '1');
            safeSwitch('disable-sync',                          '1');
            safeSwitch('metrics-recording-only',                '1');
            safeSwitch('no-pings',                              '1');
            if (BLOCK_CRASH_REPORTS) {
                safeSwitch('disable-breakpad',      '1');
                safeSwitch('no-crash-upload',       '1');
                safeSwitch('disable-crash-reporter','1');
            }
            safeSwitch('disable-domain-reliability', '1');
            safeSwitch('disable-features',
                'ReportingObserver,NetworkTimeServiceQuerying,SafeBrowsingExtendedReporting,HyperlinkAuditing,AutofillServerCommunication');
            /* DoH via Chromium flag */
            var dohTemplate = encodeURIComponent(CUSTOM_DNS_PRIMARY) + ' ' + encodeURIComponent(CUSTOM_DNS_FALLBACK);
            safeSwitch('enable-features',
                'DnsOverHttps:Fallback/false/Templates/' + dohTemplate);
        }

        /* ── DNS policy (Electron API) ── */
        function applyDnsPolicy() {
            try {
                if (typeof app.configureHostResolver === 'function') {
                    app.configureHostResolver({
                        secureDnsMode:              'secure',
                        secureDnsServers:           [CUSTOM_DNS_PRIMARY, CUSTOM_DNS_FALLBACK],
                        enableAdditionalDnsQueryTypes: false
                    });
                }
            } catch (e) {}
        }

        /* ── Per-session policy ── */
        function applySessionPolicy(sess) {
            if (!sess) return;

            /* Spellcheck */
            if (DISABLE_SPELLCHECK) {
                try {
                    if (typeof sess.setSpellCheckerEnabled === 'function') {
                        sess.setSpellCheckerEnabled(false);
                    }
                } catch (e) {}
            }

            /* Permission handler – block geolocation (and optionally others) */
            try {
                if (typeof sess.setPermissionRequestHandler === 'function') {
                    sess.setPermissionRequestHandler(function(webContents, permission, callback) {
                        try {
                            if (BLOCK_GEOLOCATION && permission === 'geolocation') {
                                callback(false);
                                return;
                            }
                            /* Allow everything else (notifications, microphone, camera, etc.) */
                            callback(true);
                        } catch (e) { try { callback(true); } catch (e2) {} }
                    });
                }
            } catch (e) {}

            /* Permission check handler (for already-granted permissions) */
            try {
                if (typeof sess.setPermissionCheckHandler === 'function') {
                    sess.setPermissionCheckHandler(function(webContents, permission, requestingOrigin) {
                        if (BLOCK_GEOLOCATION && permission === 'geolocation') return false;
                        return true;
                    });
                }
            } catch (e) {}

            /* Strip tracking / fingerprinting request headers */
            try {
                if (sess.webRequest && typeof sess.webRequest.onBeforeSendHeaders === 'function') {
                    sess.webRequest.onBeforeSendHeaders(function(details, callback) {
                        try {
                            var headers = details.requestHeaders || {};
                            delete headers['X-Client-Data'];
                            delete headers['X-Goog-Visitor-Id'];
                            delete headers['X-Firebase-Client'];
                            callback({ requestHeaders: headers });
                        } catch (e) { try { callback({}); } catch (e2) {} }
                    });
                }
            } catch (e) {}

            /* Block telemetry + crash requests */
            try {
                if (sess.webRequest && typeof sess.webRequest.onBeforeRequest === 'function') {
                    sess.webRequest.onBeforeRequest(function(details, callback) {
                        try {
                            if (isTelemetryUrl(details.url) || isCrashUrl(details.url)) {
                                callback({ cancel: true });
                                return;
                            }
                        } catch (e) {}
                        try { callback({}); } catch (e) {}
                    });
                }
            } catch (e) {}

            /* User-Agent sanitisation */
            try {
                if (CLEAN_USERAGENT && typeof sess.getUserAgent === 'function' && typeof sess.setUserAgent === 'function') {
                    if (CUSTOM_USERAGENT) {
                        sess.setUserAgent(CUSTOM_USERAGENT);
                    } else {
                        var ua = sess.getUserAgent();
                        if (ua) {
                            ua = ua.replace(/Electron\/[^\s]+\s?/g,   '');
                            ua = ua.replace(/DiscordApp\/[^\s]+\s?/g, '');
                            ua = ua.replace(/discord\/[^\s]+\s?/gi,   '');
                            ua = ua.trim();
                            sess.setUserAgent(ua);
                        }
                    }
                }
            } catch (e) {}

            /* Clear stale DNS cache */
            try {
                if (typeof sess.clearHostResolverCache === 'function') {
                    sess.clearHostResolverCache();
                }
            } catch (e) {}

            /* TLS hardening */
            if (HARDEN_TLS) {
                try {
                    if (typeof sess.setSSLConfig === 'function') {
                        sess.setSSLConfig({ minVersion: 'tls1.2', disabledCipherSuites: [] });
                    }
                } catch (e) {}
            }
        }

        /* ── Version helpers ── */
        function getElectronVersion() {
            try { return (process && process.versions && process.versions.electron) || ''; }
            catch (e) { return ''; }
        }
        function getChromeVersion() {
            try { return (process && process.versions && process.versions.chrome) || ''; }
            catch (e) { return ''; }
        }

        /* ── Update checker ── */
        var DCDNS_CURRENT_VERSION = '""" + APP_VERSION + r"""';
        var DCDNS_REPO_SLUG       = '""" + GITHUB_REPO_SLUG + r"""';
        var dcdnsUpdateInfo       = null;
        var dcdnsKnownContents    = [];

        function dcdnsCompareVersions(a, b) {
            try {
                var pa = a.split('.').map(function(n) { return parseInt(n, 10) || 0; });
                var pb = b.split('.').map(function(n) { return parseInt(n, 10) || 0; });
                var len = Math.max(pa.length, pb.length);
                for (var i = 0; i < len; i++) {
                    var x = pa[i] !== undefined ? pa[i] : 0;
                    var y = pb[i] !== undefined ? pb[i] : 0;
                    if (x > y) return 1;
                    if (x < y) return -1;
                }
                return 0;
            } catch (e) { return 0; }
        }

        function dcdnsPushUpdateInfo() {
            if (!dcdnsUpdateInfo) return;
            var script = 'try{window.__dcdnsUpdateInfo=' + JSON.stringify(dcdnsUpdateInfo) +
                ';if(typeof window.__dcdnsShowUpdateBanner==="function"){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}}catch(e){}';
            for (var i = 0; i < dcdnsKnownContents.length; i++) {
                try {
                    var c = dcdnsKnownContents[i];
                    if (c && !c.isDestroyed()) {
                        c.executeJavaScript(script, true).catch(function() {});
                    }
                } catch (e) {}
            }
        }

        function dcdnsCheckForUpdate() {
            if (DISABLE_UPDATE_CHECK) return;
            try {
                var https;
                try { https = require('https'); } catch(e) { return; }
                var options = {
                    hostname: 'api.github.com',
                    path: '/repos/' + DCDNS_REPO_SLUG + '/releases/latest',
                    method: 'GET',
                    headers: {
                        'User-Agent': 'DcDNS-Update-Check/' + DCDNS_CURRENT_VERSION,
                        'Accept': 'application/vnd.github+json'
                    }
                };
                var req = https.request(options, function(res) {
                    var body = '';
                    res.on('data', function(chunk) { body += chunk; });
                    res.on('end', function() {
                        try {
                            var data = JSON.parse(body);
                            var tag = (data.tag_name || '').replace(/^v/i, '');
                            var url = data.html_url || ('https://github.com/' + DCDNS_REPO_SLUG + '/releases/latest');
                            if (tag && dcdnsCompareVersions(tag, DCDNS_CURRENT_VERSION) > 0) {
                                dcdnsUpdateInfo = { version: tag, url: url };
                                dcdnsPushUpdateInfo();
                            }
                        } catch (e) {}
                    });
                });
                req.setTimeout(10000, function() { try { req.destroy(); } catch (e) {} });
                req.on('error', function() {});
                req.end();
            } catch (e) {}
        }

        /* ── Label script injected into each renderer ──
         *
         * Changes vs original:
         *  • Chrome version string REMOVED from label text
         *  • Label uses position:fixed (not position:absolute inside title bar)
         *    so it survives fullscreen, layout changes, and Discord's own CSS
         *  • Position offset chosen to avoid Discord's native window-title text
         *    (Discord's title is centred; we anchor to bottom-right corner)
         *  • Persistent interval + MutationObserver re-inject after any removal
         */
        var DCDNS_LABEL_POS_STYLE = {
            'bottom-right': 'bottom:6px;right:10px;top:auto;left:auto;',
            'bottom-left':  'bottom:6px;left:10px;top:auto;right:auto;',
            'top-right':    'top:6px;right:120px;bottom:auto;left:auto;',
            'top-left':     'top:6px;left:120px;bottom:auto;right:auto;'
        };
        var posStyle = DCDNS_LABEL_POS_STYLE[LABEL_POSITION] || DCDNS_LABEL_POS_STYLE['bottom-right'];

        var DCDNS_LABEL_SCRIPT = '(function(){\n' +
'  try{\n' +
'    if(window.__dcdnsLabelActive)return;\n' +
'    window.__dcdnsLabelActive=true;\n' +
'    var LABEL_ID="dcdns-encrypted-label";\n' +
'    var POS_STYLE="' + posStyle.replace(/"/g, '\\"') + '";\n' +
'    var BASE_STYLE=[\n' +
'      "position:fixed",\n' +
'      POS_STYLE,\n' +
'      "font-size:11px",\n' +
'      "font-weight:600",\n' +
'      "letter-spacing:.03em",\n' +
'      "color:rgba(255,255,255,0.55)",\n' +
'      "pointer-events:none",\n' +
'      "white-space:nowrap",\n' +
'      "z-index:2147483647",\n' +
'      "background:rgba(0,0,0,0.35)",\n' +
'      "padding:2px 7px",\n' +
'      "border-radius:5px",\n' +
'      "backdrop-filter:blur(4px)",\n' +
'      "user-select:none",\n' +
'      "transition:opacity 0.3s"\n' +
'    ].join(";");\n' +
'    function isInDOM(el){try{return document.body&&document.body.contains(el);}catch(e){return false;}}\n' +
'    function makeLabel(){\n' +
'      var label=document.createElement("div");\n' +
'      label.id=LABEL_ID;\n' +
'      label.textContent="Encrypted by DcDNS";\n' +
'      label.setAttribute("style",BASE_STYLE);\n' +
'      return label;\n' +
'    }\n' +
'    var _currentLabel=null;\n' +
'    function inject(){\n' +
'      try{\n' +
'        if(_currentLabel&&isInDOM(_currentLabel))return;\n' +
'        var stale=document.getElementById(LABEL_ID);\n' +
'        if(stale&&stale.parentNode)stale.parentNode.removeChild(stale);\n' +
'        var label=makeLabel();\n' +
'        document.documentElement.appendChild(label);\n' +
'        _currentLabel=label;\n' +
'      }catch(e){}\n' +
'    }\n' +
'    /* Re-inject if removed */\n' +
'    var _obs=new MutationObserver(function(){\n' +
'      if(!_currentLabel||!isInDOM(_currentLabel)){setTimeout(inject,30);}\n' +
'    });\n' +
'    if(document.documentElement){\n' +
'      _obs.observe(document.documentElement,{childList:true,subtree:true});\n' +
'    }\n' +
'    /* Fullscreen change — re-inject */\n' +
'    document.addEventListener("fullscreenchange",function(){setTimeout(inject,60);},true);\n' +
'    document.addEventListener("webkitfullscreenchange",function(){setTimeout(inject,60);},true);\n' +
'    /* Periodic safety net */\n' +
'    setInterval(function(){try{inject();}catch(e){}},2000);\n' +
'    if(document.readyState==="complete"||document.readyState==="interactive"){inject();}\n' +
'    else{document.addEventListener("DOMContentLoaded",inject);}\n' +
'  }catch(e){}\n' +
'  /* Update banner */\n' +
'  window.__dcdnsShowUpdateBanner=function(info){\n' +
'    try{\n' +
'      if(!info||!info.version)return;\n' +
'      if(document.getElementById("dcdns-update-banner"))return;\n' +
'      var banner=document.createElement("div");\n' +
'      banner.id="dcdns-update-banner";\n' +
'      banner.textContent="DcDNS v"+info.version+" available \u2014 click to update";\n' +
'      banner.setAttribute("style","position:fixed;bottom:28px;right:10px;background:#111118;color:#ffffff;font-size:11px;font-weight:600;padding:7px 14px;border-radius:8px;border:1px solid #7c3aed;cursor:pointer;z-index:2147483646;box-shadow:0 4px 14px rgba(0,0,0,.4);");\n' +
'      banner.onclick=function(){try{window.open(info.url,"_blank");}catch(e){}try{banner.remove();}catch(e){}};\n' +
'      document.documentElement.appendChild(banner);\n' +
'    }catch(e){}\n' +
'  };\n' +
'  if(window.__dcdnsUpdateInfo){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}\n' +
'})();';

        function attachLabelInjector(contents) {
            try {
                if (!contents || typeof contents.isDestroyed === 'function' && contents.isDestroyed()) return;
                dcdnsKnownContents.push(contents);
                contents.on('dom-ready', function() {
                    try { if (contents.isDestroyed()) return; } catch(e) { return; }
                    if (DCDNS_LABEL_ENABLED) {
                        try {
                            contents.executeJavaScript(DCDNS_LABEL_SCRIPT, true).catch(function() {});
                        } catch (e) {}
                    }
                    if (dcdnsUpdateInfo) {
                        try {
                            var script = 'try{window.__dcdnsUpdateInfo=' + JSON.stringify(dcdnsUpdateInfo) +
                                ';if(typeof window.__dcdnsShowUpdateBanner==="function"){window.__dcdnsShowUpdateBanner(window.__dcdnsUpdateInfo);}}catch(e){}';
                            if (!contents.isDestroyed()) {
                                contents.executeJavaScript(script, true).catch(function() {});
                            }
                        } catch (e) {}
                    }
                });
                /* Prevent opening telemetry-adjacent URLs in new windows */
                try {
                    if (typeof contents.setWindowOpenHandler === 'function') {
                        contents.setWindowOpenHandler(function(details) {
                            try {
                                if (details && details.url && details.url.indexOf('github.com') !== -1 && shell) {
                                    shell.openExternal(details.url);
                                }
                            } catch (e) {}
                            return { action: 'deny' };
                        });
                    }
                } catch (e) {}
            } catch (e) {}
        }

        if (typeof app.on === 'function') {
            app.on('web-contents-created', function(event, contents) {
                try { attachLabelInjector(contents); } catch (e) {}
            });
        }

        if (typeof app.whenReady === 'function') {
            app.whenReady().then(function() {
                try { applyDnsPolicy(); } catch (e) {}
                try {
                    if (session && session.defaultSession) {
                        applySessionPolicy(session.defaultSession);
                    }
                } catch (e) {}
                try {
                    if (session && typeof session.fromPartition === 'function') {
                        var persist = session.fromPartition('persist:discord');
                        if (persist) applySessionPolicy(persist);
                    }
                } catch (e) {}
                try { dcdnsCheckForUpdate(); } catch (e) {}
                try { setInterval(dcdnsCheckForUpdate, 3 * 60 * 60 * 1000); } catch (e) {}
            }).catch(function() {});
        }
    } catch (err) {}
})();
/* === [End DcDNS Policy Framework] === */

"""

POLICY_TEXT = """\
DcDNS Policy Framework v{version}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT DcDNS IS
  DcDNS is an open-source privacy tool that patches Discord's
  Electron main process (index.js) and injects a small script
  that runs before Discord's own code starts.

  The script only modifies low-level Electron and Chromium
  networking/privacy settings. It does not read, log, store,
  modify, or transmit anything you type, say, or send inside
  Discord. It does not touch your Discord account, session
  token, messages, or files.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PRIVACY PROTECTIONS

  RULE 1 — Encrypted DNS (DNS-over-HTTPS)
    All DNS lookups made by the Discord client are routed
    through a user-configurable DoH resolver (default: Mullvad).
      Default Primary:  https://dns.mullvad.net/dns-query
      Default Fallback: https://adblock.dns.mullvad.net/dns-query
    Mullvad publishes a strict no-logs policy and filters known
    ad, tracker, and malware domains. Fallback to plaintext DNS
    is disabled — lookups cannot silently downgrade.
    You can set your own DoH server in Settings.

  RULE 2 — WebRTC IP Leak Prevention (toggleable)
    WebRTC is locked to "public interface only" mode.
    Your local/LAN IP address is never exposed to voice/video
    servers or call participants. Voice and video calls continue
    to work normally.

  RULE 3 — Geolocation Blocked (toggleable)
    Any geolocation request from Discord is automatically denied
    at the Electron permission layer before Discord can ask.
    This also applies to already-granted-permission checks.

  RULE 4 — Spellcheck Disabled (toggleable)
    Chromium's built-in spellchecker can send typed words to a
    remote Google API endpoint. DcDNS disables this for Discord's
    session so nothing you type is sent for spellcheck purposes.

  RULE 5 — Discord Telemetry Blocked (toggleable)
    Requests to Discord's analytics, event-tracking, and science
    endpoints (/api/*/science, /api/*/track, /api/*/metrics,
    /api/*/analytics, reporter.discord.com, click.discord.com)
    are cancelled at the network layer before they reach servers.
    Also blocks third-party analytics (Mixpanel, Segment, Amplitude).

  RULE 6 — Crash Report Blocking (toggleable)
    Sentry crash reporting and Discord crash upload endpoints are
    blocked, and the Chromium crash reporter (Breakpad) is disabled.

  RULE 7 — Chromium Telemetry Disabled
    Chromium background networking, component updater pings, domain
    reliability reporting, sync, HyperlinkAuditing, and AutofillServer
    communication are all disabled. The X-Client-Data and
    X-Goog-Visitor-Id headers are stripped from every request.

  RULE 8 — TLS Hardening (toggleable)
    Minimum TLS version is enforced at 1.2, preventing connections
    to servers using older, insecure TLS versions.

  RULE 9 — User-Agent Cleaning (toggleable)
    Electron and Discord-specific strings are removed from the
    User-Agent header so the Chromium engine version isn't leaked.
    You can also set a fully custom User-Agent string in Settings.

  RULE 10 — Title Bar Label (toggleable, position configurable)
    An "Encrypted by DcDNS" label is injected into Discord's
    renderer. It uses a fixed position so it persists through
    fullscreen, screen-sharing, layout changes, and Discord
    window events. The Chrome/Electron version is NOT shown.

  RULE 11 — Update Notice (toggleable)
    DcDNS periodically checks GitHub's public release API to see
    if a newer DcDNS version exists. Only a version lookup is sent;
    nothing about you or your Discord account is uploaded.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BACKUP & RESTORE
  Before writing anything, DcDNS copies the untouched file to
  index.js.dcdns.bak next to the original. On reinstall you will
  be asked whether to overwrite the existing backup or keep it.
  Uninstalling restores that exact backup and deletes it.
  If the backup is missing, DcDNS falls back to manually stripping
  its own payload from index.js.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT DcDNS DOES NOT DO
  • Does not collect, store, or transmit any personal data.
  • Does not read or modify your messages, calls, or files.
  • Does not touch your Discord account, token, or settings.
  • Does not survive a Discord auto-update (expected behaviour).
  • Does not install persistent background services or daemons.
  • Does not require admin rights for settings changes (only for
    writing to Discord's program directory).

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RISKS & LIMITATIONS
  • Discord's Terms of Service do not officially support third-party
    client modifications. Use is at your own discretion and risk.
  • Any Discord update overwrites index.js and removes DcDNS;
    this is expected behaviour, not a malfunction.
  • Some Discord-specific features (e.g. crash reporting that helps
    Discord improve the client) will be disabled.
  • DcDNS is provided "as is" with no warranty of any kind.
    See the MIT licence for full terms.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SCOPE
  Only the Discord desktop Electron client is affected.
  The Discord web app and official mobile apps are never touched.
  Supported: Discord (Stable), Discord PTB, Discord Canary on Windows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OPEN SOURCE & LICENCE
  DcDNS is free and open-source software released under the MIT Licence.
  Source: https://github.com/{repo}
  Contributions and audits are welcome.
  Provided "as is", with no warranty of any kind.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
By clicking "I Agree & Continue" you confirm that you have
read and understood this policy and accept full responsibility
for any changes made to your local Discord client.
""".format(version=APP_VERSION, repo=GITHUB_REPO_SLUG)


DISCORD_SVG  = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 127.14 96.36"><path fill="currentColor" d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.26a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>"""
DOWNLOAD_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12"/><path d="m7 11 5 5 5-5"/><path d="M5 21h14"/></svg>"""
TRASH_SVG    = """<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M4 7h16"/><path d="M6 7v13a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>"""
RESTART_SVG  = """<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12a9 9 0 1 1 2.64 6.36"/><path d="M3 21v-6h6"/></svg>"""
WARN_SVG     = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>"""
SETTINGS_SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>"""
SHIELD_SVG   = """<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>"""

FLAVORS = ["DISCORD", "DISCORDPTB", "DISCORDCANARY"]
FLAVOR_DISPLAY = {
    "DISCORD":       ("Discord",        "stable"),
    "DISCORDPTB":    ("Discord PTB",    "ptb"),
    "DISCORDCANARY": ("Discord Canary", "canary"),
}
WINDOWS_EXE_NAMES = {
    "DISCORD":       "Discord.exe",
    "DISCORDPTB":    "DiscordPTB.exe",
    "DISCORDCANARY": "DiscordCanary.exe",
    "MANUAL":        "Discord.exe",
}
PROCESS_NAMES = {
    "DISCORD":       ["Discord.exe"],
    "DISCORDPTB":    ["DiscordPTB.exe"],
    "DISCORDCANARY": ["DiscordCanary.exe"],
    "MANUAL":        ["Discord.exe"],
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


# ---------------------------------------------------------------------------
# HTML UI
# ---------------------------------------------------------------------------
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
.header-right{margin-left:auto;display:flex;align-items:center;gap:6px}
.icon-btn{background:none;border:1px solid #1a1a26;border-radius:8px;color:#71717a;cursor:pointer;display:flex;align-items:center;justify-content:center;width:28px;height:28px;transition:color .2s,border-color .2s,background .2s}
.icon-btn:hover{color:#e8e8ef;border-color:#3f3f46;background:rgba(255,255,255,.04)}
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
.discord-invite-btn{display:inline-flex;align-items:center;gap:5px;background:rgba(88,101,242,.12);border:1px solid rgba(88,101,242,.35);border-radius:8px;color:#7983f5;font-family:inherit;font-size:10px;font-weight:600;padding:4px 10px;cursor:pointer;transition:background .18s ease,border-color .18s ease,color .18s ease;flex-shrink:0;white-space:nowrap}
.discord-invite-btn:hover{background:rgba(88,101,242,.22);border-color:rgba(88,101,242,.6);color:#9fa8fa}
.discord-invite-btn svg{flex-shrink:0}
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
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:9000;display:flex;align-items:center;justify-content:center;animation:fadeSlideIn .2s ease;backdrop-filter:blur(4px)}
.modal{background:#0e0e1a;border:1px solid #2e2e46;border-radius:20px;padding:28px 28px 24px;width:360px;max-width:92vw;box-shadow:0 24px 70px rgba(0,0,0,.7),0 0 0 1px rgba(168,85,247,.08);display:flex;flex-direction:column;gap:0}
.modal-icon{width:44px;height:44px;border-radius:14px;background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.25);display:flex;align-items:center;justify-content:center;margin-bottom:16px;flex-shrink:0}
.modal-title{font-size:15px;font-weight:700;color:#e8e8ef;margin-bottom:7px;line-height:1.3}
.modal-sub{font-size:11.5px;color:#71717a;margin-bottom:22px;line-height:1.6}
.modal-btns{display:flex;gap:10px;width:100%}
.modal-btn{flex:1;height:38px;border-radius:12px;font-family:inherit;font-size:12px;font-weight:700;cursor:pointer;transition:transform .15s ease,box-shadow .2s ease,background .2s ease,opacity .2s ease;display:flex;align-items:center;justify-content:center;border:1px solid transparent}
.modal-btn.secondary{background:#18181f;border-color:#2e2e46;color:#a1a1aa}
.modal-btn.secondary:hover{background:#1e1e2a;border-color:#3f3f5a;color:#e8e8ef;transform:translateY(-1px)}
.modal-btn.secondary:active{transform:translateY(0) scale(.97)}
.modal-btn.primary{background:linear-gradient(135deg,#a855f7,#7c3aed);color:#fff;box-shadow:0 4px 14px -4px rgba(168,85,247,.5)}
.modal-btn.primary:hover{background:linear-gradient(135deg,#b968ff,#8b3ff0);box-shadow:0 8px 20px -6px rgba(168,85,247,.65);transform:translateY(-1px)}
.modal-btn.primary:active{transform:translateY(0) scale(.97)}

/* Settings */
.settings-row{display:flex;align-items:flex-start;justify-content:space-between;padding:10px 0;border-bottom:1px solid #1a1a26;gap:8px}
.settings-row:last-child{border-bottom:none}
.settings-label{font-size:12px;font-weight:600}
.settings-desc{font-size:10px;color:#71717a;margin-top:2px}
.settings-group-title{font-size:10px;font-weight:700;color:#a855f7;letter-spacing:.08em;text-transform:uppercase;padding:10px 0 4px;margin-top:4px}
.toggle{position:relative;width:36px;height:20px;flex-shrink:0;margin-top:2px}
.toggle input{opacity:0;width:0;height:0}
.toggle-slider{position:absolute;inset:0;background:#27272a;border-radius:20px;cursor:pointer;transition:background .2s}
.toggle-slider:before{content:'';position:absolute;height:14px;width:14px;left:3px;bottom:3px;background:#71717a;border-radius:50%;transition:transform .2s,background .2s}
.toggle input:checked+.toggle-slider{background:rgba(168,85,247,.25)}
.toggle input:checked+.toggle-slider:before{transform:translateX(16px);background:#a855f7}
.settings-input{width:100%;background:#11111a;color:#e8e8ef;border:1px solid #1a1a26;border-radius:8px;padding:6px 10px;font-family:'Consolas',monospace;font-size:10px;outline:none;margin-top:4px;transition:border-color .2s}
.settings-input:focus{border-color:#6d28d9}
.settings-input::placeholder{color:#3f3f46}
.settings-select{width:100%;background:#11111a;color:#e8e8ef;border:1px solid #1a1a26;border-radius:8px;padding:5px 10px;font-family:inherit;font-size:11px;outline:none;margin-top:4px;cursor:pointer;transition:border-color .2s}
.settings-select:focus{border-color:#6d28d9}
.dns-preset-row{display:flex;gap:6px;margin-top:4px;flex-wrap:wrap}
.dns-preset-btn{background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.25);border-radius:6px;color:#c4b5fd;font-family:inherit;font-size:9px;font-weight:600;padding:3px 8px;cursor:pointer;transition:background .15s,border-color .15s;white-space:nowrap}
.dns-preset-btn:hover{background:rgba(168,85,247,.22);border-color:rgba(168,85,247,.5)}
.verify-row{display:flex;align-items:center;gap:8px;padding:10px 0;border-top:1px solid #1a1a26;margin-top:4px}
.verify-hash{font-family:monospace;font-size:9px;color:#71717a;word-break:break-all;flex:1;line-height:1.4}
.verify-badge{font-size:9px;font-weight:700;padding:2px 8px;border-radius:6px;flex-shrink:0}
.verify-badge.ok{background:rgba(34,197,94,.12);color:#22c55e}
.verify-badge.fail{background:rgba(239,68,68,.12);color:#ef4444}
.verify-badge.none{background:rgba(113,113,122,.12);color:#71717a}
</style>
</head>
<body>
<div class="bg" id="bg"></div>
<div class="app">
  <div class="header">
    <div class="logo-wrap">""" + LOGO_HTML + """</div>
    <span class="title">DcDNS</span>
    <span class="version">v""" + APP_VERSION + """</span>
    <div class="header-right">
      <button class="icon-btn" id="btn-open-settings" title="Settings">""" + SETTINGS_SVG + """</button>
    </div>
  </div>
  <div class="steps" id="steps"></div>

  <!-- POLICY PAGE -->
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
      <button class="discord-invite-btn" id="btn-discord-invite" title="Join our Discord server">
        <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 127.14 96.36" fill="currentColor"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.26a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>
        Join Our Discord
      </button>
    </div>
    <button class="btn primary" id="btn-next" disabled>Continue &rarr;</button>
  </div>

  <!-- INSTALL PAGE -->
  <div class="page" id="page-install">
    <div class="page-title">Select Discord Client</div>
    <div class="page-sub">Select your Discord client below to install or remove DcDNS.</div>
    <div class="card">
      <div class="card-inner">
        <div class="discord-grid" id="discord-grid">
""" + _build_discord_grid() + """
        </div>
        <div class="status" id="install-status"></div>
        <div class="verify-row" id="verify-row" style="display:none">
          <span class="verify-hash" id="verify-hash"></span>
          <span class="verify-badge none" id="verify-badge">Not verified</span>
        </div>
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

  <!-- LOG PAGE -->
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

  <!-- SETTINGS PAGE -->
  <div class="page" id="page-settings">
    <div class="page-title">Settings</div>
    <div class="card">
      <div class="card-inner" style="padding:14px 18px">

        <div class="settings-group-title">&#x1F4E1; Label</div>

        <div class="settings-row">
          <div>
            <div class="settings-label">Title Bar Label</div>
            <div class="settings-desc">Show "Encrypted by DcDNS" badge in Discord</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-label" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row" id="row-label-position">
          <div style="flex:1">
            <div class="settings-label">Label Position</div>
            <div class="settings-desc">Where the badge appears in Discord's window</div>
            <select class="settings-select" id="select-label-position">
              <option value="bottom-right">Bottom Right (default)</option>
              <option value="bottom-left">Bottom Left</option>
              <option value="top-right">Top Right</option>
              <option value="top-left">Top Left</option>
            </select>
          </div>
        </div>

        <div class="settings-group-title">&#x1F6E1; Privacy</div>

        <div class="settings-row">
          <div>
            <div class="settings-label">Block Discord Telemetry</div>
            <div class="settings-desc">Block science, track, analytics, Sentry, Mixpanel, Segment, Amplitude</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-telemetry" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Block Crash Reports</div>
            <div class="settings-desc">Disable Breakpad crash reporter and crash upload endpoints</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-crash" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">WebRTC IP Leak Protection</div>
            <div class="settings-desc">Prevent your local/LAN IP from being exposed in calls</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-webrtc" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Block Geolocation</div>
            <div class="settings-desc">Deny all location permission requests from Discord</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-geo" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Disable Spellcheck</div>
            <div class="settings-desc">Stop Chromium from sending typed words to remote spell-check APIs</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-spell" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">TLS 1.2+ Hardening</div>
            <div class="settings-desc">Enforce minimum TLS 1.2 — reject older insecure connections</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-tls" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Clean User-Agent</div>
            <div class="settings-desc">Strip Electron/Discord strings from the User-Agent header</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-ua" checked><span class="toggle-slider"></span></label>
        </div>

        <div class="settings-group-title">&#x1F310; DNS</div>

        <div class="settings-row" style="flex-direction:column;align-items:flex-start">
          <div>
            <div class="settings-label">Custom DoH Server — Primary</div>
            <div class="settings-desc">DNS-over-HTTPS URL (must start with https://)</div>
          </div>
          <input class="settings-input" id="input-dns-primary" type="text" placeholder="https://dns.mullvad.net/dns-query" spellcheck="false">
          <div class="dns-preset-row">
            <button class="dns-preset-btn" data-p="https://dns.mullvad.net/dns-query" data-f="https://adblock.dns.mullvad.net/dns-query">Mullvad</button>
            <button class="dns-preset-btn" data-p="https://cloudflare-dns.com/dns-query" data-f="https://1.1.1.1/dns-query">Cloudflare</button>
            <button class="dns-preset-btn" data-p="https://dns.google/dns-query" data-f="https://8.8.4.4/dns-query">Google</button>
            <button class="dns-preset-btn" data-p="https://dns.quad9.net/dns-query" data-f="https://9.9.9.9/dns-query">Quad9</button>
            <button class="dns-preset-btn" data-p="https://doh.opendns.com/dns-query" data-f="https://208.67.222.222/dns-query">OpenDNS</button>
            <button class="dns-preset-btn" data-p="https://adblock.dns.mullvad.net/dns-query" data-f="https://dns.mullvad.net/dns-query">Mullvad AdBlock</button>
          </div>
        </div>
        <div class="settings-row" style="flex-direction:column;align-items:flex-start">
          <div>
            <div class="settings-label">Custom DoH Server — Fallback</div>
            <div class="settings-desc">Used if primary DoH server is unreachable</div>
          </div>
          <input class="settings-input" id="input-dns-fallback" type="text" placeholder="https://adblock.dns.mullvad.net/dns-query" spellcheck="false">
        </div>

        <div class="settings-group-title">&#x1F9BE; User-Agent</div>

        <div class="settings-row" style="flex-direction:column;align-items:flex-start">
          <div>
            <div class="settings-label">Custom User-Agent String</div>
            <div class="settings-desc">Override with a specific UA. Leave blank to auto-clean.</div>
          </div>
          <input class="settings-input" id="input-custom-ua" type="text" placeholder="e.g. Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..." spellcheck="false">
        </div>

        <div class="settings-group-title">&#x2699;&#xFE0F; Misc</div>

        <div class="settings-row">
          <div>
            <div class="settings-label">Disable Update Check</div>
            <div class="settings-desc">Don't contact GitHub to check for DcDNS updates</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-no-update"><span class="toggle-slider"></span></label>
        </div>

      </div>
    </div>
    <div class="foot">
      <button class="btn nav-back" id="btn-settings-back">&larr; Back</button>
      <button class="btn primary" id="btn-settings-save">Save &amp; Close</button>
    </div>
  </div>
</div>

<!-- Backup modal -->
<div id="modal-backup" style="display:none" class="modal-overlay">
  <div class="modal">
    <div class="modal-icon">
      <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    </div>
    <div class="modal-title">Backup already exists</div>
    <div class="modal-sub">A backup file already exists from a previous install. Choose what DcDNS should do with it before proceeding.</div>
    <div class="modal-btns">
      <button class="modal-btn secondary" id="modal-backup-keep">Keep old backup</button>
      <button class="modal-btn primary" id="modal-backup-overwrite">Overwrite backup</button>
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

var _settings = {
  showLabel:         true,
  labelPosition:     'bottom-right',
  blockTelemetry:    true,
  blockCrashReports: true,
  blockWebrtc:       true,
  blockGeolocation:  true,
  disableSpellcheck: true,
  hardenTls:         true,
  cleanUserAgent:    true,
  disableUpdateCheck: false,
  customDnsPrimary:  '',
  customDnsFallback: '',
  customUserAgent:   ''
};
try {
  var _raw = localStorage.getItem('dcdns_conf');
  if (_raw) { var _parsed = JSON.parse(_raw); if (_parsed) _settings = Object.assign(_settings, _parsed); }
} catch(e) {}

function saveSettings() {
  try { localStorage.setItem('dcdns_conf', JSON.stringify(_settings)); } catch(e) {}
}

function applySettingsToUI() {
  function setChk(id, val) { var el = safeEl(id); if (el) el.checked = val; }
  function setVal(id, val) { var el = safeEl(id); if (el) el.value = val || ''; }
  setChk('toggle-label',    _settings.showLabel         !== false);
  setChk('toggle-telemetry',_settings.blockTelemetry    !== false);
  setChk('toggle-crash',    _settings.blockCrashReports !== false);
  setChk('toggle-webrtc',   _settings.blockWebrtc       !== false);
  setChk('toggle-geo',      _settings.blockGeolocation  !== false);
  setChk('toggle-spell',    _settings.disableSpellcheck !== false);
  setChk('toggle-tls',      _settings.hardenTls         !== false);
  setChk('toggle-ua',       _settings.cleanUserAgent    !== false);
  setChk('toggle-no-update',_settings.disableUpdateCheck === false);
  setVal('input-dns-primary',  _settings.customDnsPrimary);
  setVal('input-dns-fallback', _settings.customDnsFallback);
  setVal('input-custom-ua',    _settings.customUserAgent);
  var selPos = safeEl('select-label-position');
  if (selPos) selPos.value = _settings.labelPosition || 'bottom-right';
}

function safeBind(id, eventName, handler) {
  try {
    var el = document.getElementById(id);
    if (el) {
      el.addEventListener(eventName, function(evt) {
        try { handler(evt); } catch (err) { console.error('[DcDNS] Handler error in ' + id + ':', err); }
      });
    }
  } catch (err) {}
}

function safeEl(id) { try { return document.getElementById(id); } catch(e) { return null; } }

/* Orbs */
try {
  var bg = document.getElementById('bg');
  var orbColors = ['#a855f7','#ec4899','#3b82f6','#06b6d4','#6366f1','#8b5cf6'];
  if (bg) {
    for (var _i = 0; _i < 24; _i++) {
      var orb = document.createElement('div');
      orb.className = 'orb';
      var size = 55 + Math.random() * 130;
      orb.style.width  = size + 'px';
      orb.style.height = size + 'px';
      orb.style.left   = Math.random() * 100 + '%';
      orb.style.top    = Math.random() * 100 + '%';
      orb.style.background = orbColors[Math.floor(Math.random() * orbColors.length)];
      orb.style.animationDuration = (13 + Math.random() * 17) + 's';
      orb.style.animationDelay   = (-Math.random() * 26) + 's';
      bg.appendChild(orb);
    }
  }
} catch (err) {}

function showPage(name) {
  try {
    document.querySelectorAll('.page').forEach(function(p) { p.classList.remove('active'); });
    var target = document.getElementById('page-' + name);
    if (target) target.classList.add('active');
    if (name !== 'settings') updateSteps(name);
  } catch(err) {}
}

function updateSteps(active) {
  try {
    var steps = ['policy','install','log'];
    var names = ['Policy','Install','Log'];
    var html = '';
    var activeIdx = steps.indexOf(active);
    steps.forEach(function(s, i) {
      var done = activeIdx > i;
      var isActive = activeIdx === i;
      html += '<div class="step ' + (isActive ? 'active ' : '') + (done ? 'done' : '') + '">' +
        '<span class="step-dot" style="color:' + ((done||isActive) ? '#a855f7' : '#3f3f46') + '">&#9679;</span>' +
        '<span class="step-text" style="color:' + ((done||isActive) ? '#e8e8ef' : '#71717a') + '">' + names[i] + '</span></div>';
      if (i < 2) html += '<span class="step-line">&mdash;</span>';
    });
    var stepsEl = document.getElementById('steps');
    if (stepsEl) stepsEl.innerHTML = html;
  } catch(err) {}
}

try { updateSteps('policy'); } catch (err) {}

window.selectedInstall = null;
window.discordInstalls = [];
window._backupResolve  = null;

safeBind('agree-check', 'change', function(e) {
  var nextBtn = safeEl('btn-next');
  if (nextBtn) nextBtn.disabled = !e.target.checked;
});
safeBind('btn-discord-invite', 'click', function() {
  try { if (window.pywebview && window.pywebview.api && typeof window.pywebview.api.open_discord === 'function') { window.pywebview.api.open_discord(); } } catch (err) {}
});
safeBind('btn-next', 'click', function() { showPage('install'); scanAll(); });
safeBind('btn-back1', 'click', function() {
  showPage('policy');
  var warnEl = safeEl('update-warning');
  if (warnEl) warnEl.style.display = 'none';
});
safeBind('btn-done', 'click', function() {
  try { if (window.pywebview && window.pywebview.api) { window.pywebview.api.close_app(); } } catch (err) {}
});
safeBind('btn-open-settings', 'click', function() { applySettingsToUI(); showPage('settings'); });
safeBind('btn-settings-back', 'click', function() { showPage('install'); });

/* DNS preset buttons */
try {
  document.querySelectorAll('.dns-preset-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var p = btn.dataset.p, f = btn.dataset.f;
      var ip = safeEl('input-dns-primary'),   fi = safeEl('input-dns-fallback');
      if (ip) ip.value = p || '';
      if (fi) fi.value = f || '';
    });
  });
} catch(e) {}

safeBind('btn-settings-save', 'click', function() {
  function chk(id) { var el = safeEl(id); return el ? el.checked : true; }
  function val(id) { var el = safeEl(id); return el ? el.value.trim() : ''; }
  var selPos = safeEl('select-label-position');
  _settings.showLabel          = chk('toggle-label');
  _settings.labelPosition      = selPos ? selPos.value : 'bottom-right';
  _settings.blockTelemetry     = chk('toggle-telemetry');
  _settings.blockCrashReports  = chk('toggle-crash');
  _settings.blockWebrtc        = chk('toggle-webrtc');
  _settings.blockGeolocation   = chk('toggle-geo');
  _settings.disableSpellcheck  = chk('toggle-spell');
  _settings.hardenTls          = chk('toggle-tls');
  _settings.cleanUserAgent     = chk('toggle-ua');
  _settings.disableUpdateCheck = chk('toggle-no-update');
  _settings.customDnsPrimary   = val('input-dns-primary');
  _settings.customDnsFallback  = val('input-dns-fallback');
  _settings.customUserAgent    = val('input-custom-ua');
  saveSettings();
  showPage('install');
});

safeBind('modal-backup-keep', 'click', function() {
  var m = safeEl('modal-backup'); if (m) m.style.display = 'none';
  if (window._backupResolve) { window._backupResolve('keep'); window._backupResolve = null; }
});
safeBind('modal-backup-overwrite', 'click', function() {
  var m = safeEl('modal-backup'); if (m) m.style.display = 'none';
  if (window._backupResolve) { window._backupResolve('overwrite'); window._backupResolve = null; }
});

window.__dcdnsAskBackup = function() {
  return new Promise(function(resolve) {
    window._backupResolve = resolve;
    var m = safeEl('modal-backup');
    if (m) m.style.display = 'flex';
  });
};

var APP_VERSION_JS = '""" + APP_VERSION + """';
var FLAVOR_MAP = """ + _build_flavor_map_js() + """;

function badgeInfo(inst) {
  try {
    if (!inst || !inst.injected) return { text: 'Stock', cls: 'dc-badge stock' };
    if (inst.up_to_date === false) return { text: 'Outdated', cls: 'dc-badge outdated' };
    return { text: 'DcDNS \u2022 v' + (inst.dcdns_version || '?'), cls: 'dc-badge injected' };
  } catch(e) { return { text: 'Stock', cls: 'dc-badge stock' }; }
}

function waitForApi(callback, retries) {
  retries = retries === undefined ? 30 : retries;
  try { if (window.pywebview && window.pywebview.api) { callback(); return; } } catch(e) {}
  if (retries <= 0) return;
  setTimeout(function() { waitForApi(callback, retries - 1); }, 200);
}

async function scanAll() {
  try {
    var cards = document.querySelectorAll('.discord-card');
    cards.forEach(function(card, i) {
      card.style.animation = 'none'; void card.offsetWidth;
      card.style.animationDelay = (i * 0.05) + 's'; card.style.animation = '';
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
          for (var j = 0; j < data.length; j++) { if (data[j].flavor === flavor) { inst = data[j]; break; } }
          var verEl   = safeEl('dc-ver-'   + suffix);
          var badgeEl = safeEl('dc-badge-' + suffix);
          var card    = document.querySelector('.discord-card[data-flavor="' + flavor + '"]');
          if (!verEl || !badgeEl || !card) continue;
          if (inst && inst.path) {
            verEl.textContent = 'v' + (inst.version || 'unknown');
            var badge = badgeInfo(inst);
            badgeEl.textContent = badge.text; badgeEl.className = badge.cls;
            card.dataset.path         = inst.path;
            card.dataset.injected     = inst.injected ? '1' : '0';
            card.dataset.version      = inst.version      || '';
            card.dataset.dcdnsVersion = inst.dcdns_version || '';
            card.dataset.upToDate     = inst.up_to_date === true ? '1' : (inst.up_to_date === false ? '0' : '');
            card.dataset.chromeVersion= inst.chrome_version || '';
            card.dataset.sha256       = inst.sha256 || '';
          } else {
            verEl.textContent = 'Not installed'; badgeEl.textContent = 'Not found'; badgeEl.className = 'dc-badge missing';
            card.dataset.path = ''; card.dataset.injected = '0';
          }
        } catch(innerErr) {}
      }
    } catch (err) {}
  });
}

function selectFlavor(flavor) {
  try {
    document.querySelectorAll('.discord-card').forEach(function(c) { c.classList.remove('selected'); });
    var card        = document.querySelector('.discord-card[data-flavor="' + flavor + '"]');
    var statusEl    = safeEl('install-status');
    var warnEl      = safeEl('update-warning');
    var installBtn  = safeEl('btn-install');
    var uninstallBtn= safeEl('btn-uninstall');
    var verifyRow   = safeEl('verify-row');
    var verifyHash  = safeEl('verify-hash');
    var verifyBadge = safeEl('verify-badge');
    if (!card || !card.dataset.path) {
      if (statusEl) { statusEl.textContent = 'This client is not installed.'; statusEl.className = 'status err'; }
      if (warnEl) warnEl.style.display = 'none';
      if (verifyRow) verifyRow.style.display = 'none';
      window.selectedInstall = null;
      if (installBtn)   installBtn.disabled   = true;
      if (uninstallBtn) uninstallBtn.disabled = true;
      return;
    }
    card.classList.add('selected');
    var isInjected  = card.dataset.injected   === '1';
    var isUpToDate  = card.dataset.upToDate   === '1';
    var dcdnsVersion= card.dataset.dcdnsVersion || '?';
    var sha256      = card.dataset.sha256 || '';
    window.selectedInstall = { flavor: flavor, path: card.dataset.path, version: card.dataset.version, injected: isInjected };
    var displayName = card.querySelector('.dc-name') ? card.querySelector('.dc-name').textContent : flavor;
    if (statusEl) {
      if (isInjected && isUpToDate) {
        statusEl.textContent = displayName + ' v' + card.dataset.version + ' \u2014 DcDNS v' + dcdnsVersion + ' installed.';
        statusEl.className = 'status warn';
        if (installBtn)   installBtn.disabled   = true;
        if (uninstallBtn) uninstallBtn.disabled = false;
      } else if (isInjected && !isUpToDate) {
        statusEl.textContent = displayName + ' v' + card.dataset.version + ' \u2014 outdated DcDNS v' + dcdnsVersion + '. Reinstall to upgrade.';
        statusEl.className = 'status warn';
        if (installBtn)   installBtn.disabled   = false;
        if (uninstallBtn) uninstallBtn.disabled = false;
      } else {
        statusEl.textContent = displayName + ' v' + card.dataset.version + ' selected.';
        statusEl.className = 'status ok';
        if (installBtn)   installBtn.disabled   = false;
        if (uninstallBtn) uninstallBtn.disabled = true;
      }
    }
    if (verifyRow && verifyHash && verifyBadge) {
      if (sha256) {
        verifyRow.style.display = 'flex';
        verifyHash.textContent  = 'SHA-256: ' + sha256;
        if (isInjected) { verifyBadge.textContent = 'DcDNS active'; verifyBadge.className = 'verify-badge ok'; }
        else            { verifyBadge.textContent = 'Stock file';   verifyBadge.className = 'verify-badge none'; }
      } else { verifyRow.style.display = 'none'; }
    }
    if (warnEl) warnEl.style.display = 'flex';
  } catch(err) {}
}

function handleOpResult(res) {
  try {
    if (res === 'ok') return;
    var back2 = safeEl('btn-back2'), done = safeEl('btn-done'), restart = safeEl('btn-restart');
    if (back2)   back2.disabled   = false;
    if (done)    done.disabled    = false;
    if (restart) restart.disabled = !window.selectedInstall;
    var titleEl = safeEl('log-title');
    if (titleEl) { titleEl.textContent = 'Error'; titleEl.style.color = '#ef4444'; }
    if (res === 'busy')  addLog('[X] Another operation is already running.');
    else addLog('[X] Invalid request.');
  } catch(err) {}
}

safeBind('btn-install', 'click', async function() {
  if (!window.selectedInstall) return;
  var inst = Object.assign({}, window.selectedInstall, { settings: _settings });
  showPage('log');
  var logTitle = safeEl('log-title'), logBox = safeEl('log-box');
  var back2 = safeEl('btn-back2'), restart = safeEl('btn-restart'), done = safeEl('btn-done');
  if (logTitle) { logTitle.textContent = 'Installing DcDNS...'; logTitle.style.color = '#e8e8ef'; }
  if (logBox)   logBox.innerHTML = '';
  if (back2)    back2.disabled   = true;
  if (restart)  restart.disabled = true;
  if (done)     done.disabled    = true;
  try {
    var res = await window.pywebview.api.install(JSON.stringify(inst));
    if (res === 'ask_backup') {
      var choice = await window.__dcdnsAskBackup();
      res = await window.pywebview.api.install_confirm_backup(choice);
    }
    handleOpResult(res);
  } catch (err) { handleOpResult('error'); }
});

safeBind('btn-uninstall', 'click', async function() {
  if (!window.selectedInstall) return;
  showPage('log');
  var logTitle = safeEl('log-title'), logBox = safeEl('log-box');
  var back2 = safeEl('btn-back2'), restart = safeEl('btn-restart'), done = safeEl('btn-done');
  if (logTitle) { logTitle.textContent = 'Uninstalling DcDNS & Restoring Backup...'; logTitle.style.color = '#e8e8ef'; }
  if (logBox)   logBox.innerHTML = '';
  if (back2)    back2.disabled   = true;
  if (restart)  restart.disabled = true;
  if (done)     done.disabled    = true;
  try {
    var res = await window.pywebview.api.uninstall(JSON.stringify(window.selectedInstall));
    handleOpResult(res);
  } catch (err) { handleOpResult('error'); }
});

safeBind('btn-restart', 'click', async function() {
  if (!window.selectedInstall) return;
  var back2 = safeEl('btn-back2'), restart = safeEl('btn-restart'), done = safeEl('btn-done'), logTitle = safeEl('log-title');
  if (back2)    back2.disabled   = true;
  if (restart)  restart.disabled = true;
  if (done)     done.disabled    = true;
  if (logTitle) { logTitle.textContent = 'Restarting Discord...'; logTitle.style.color = '#e8e8ef'; }
  try {
    var res = await window.pywebview.api.restart_discord(JSON.stringify(window.selectedInstall));
    handleOpResult(res);
  } catch (err) { handleOpResult('error'); }
});

function addLog(msg) {
  try {
    var box = safeEl('log-box');
    if (!box) return;
    var text = String(msg || '');
    var line = document.createElement('div');
    line.className = 'log-line';
    if (text.startsWith('[+]'))           line.classList.add('ok');
    else if (text.startsWith('[X]') || text.startsWith('[x]')) line.classList.add('err');
    else if (text.startsWith('[!]'))      line.classList.add('warn');
    else if (text.indexOf('===') === 0)   line.classList.add('head');
    line.textContent = text;
    box.appendChild(line);
    box.scrollTop = box.scrollHeight;
  } catch(err) {}
}

function finishLog(ok) {
  try {
    var back2 = safeEl('btn-back2'), done = safeEl('btn-done'), restart = safeEl('btn-restart');
    if (back2)   back2.disabled   = false;
    if (done)    done.disabled    = false;
    if (restart) restart.disabled = !window.selectedInstall;
    var titleEl = safeEl('log-title');
    if (titleEl) {
      if (ok) { titleEl.textContent = 'Done';  titleEl.style.color = '#22c55e'; }
      else    { titleEl.textContent = 'Error'; titleEl.style.color = '#ef4444'; }
    }
    window._needRescan = true;
  } catch(err) {}
}

safeBind('btn-back2', 'click', function() {
  showPage('install');
  if (window._needRescan) {
    window._needRescan = false;
    window.selectedInstall = null;
    var installBtn  = safeEl('btn-install'),   uninstallBtn = safeEl('btn-uninstall');
    var statusEl    = safeEl('install-status'), warnEl = safeEl('update-warning'), verifyRow = safeEl('verify-row');
    if (installBtn)   installBtn.disabled   = true;
    if (uninstallBtn) uninstallBtn.disabled = true;
    if (statusEl) { statusEl.textContent = ''; statusEl.className = 'status'; }
    if (warnEl)   warnEl.style.display   = 'none';
    if (verifyRow) verifyRow.style.display = 'none';
    scanAll();
  }
});
</script>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Discord scanner & patcher
# ---------------------------------------------------------------------------
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
            version      = DiscordDetector._get_version(norm)
            vkey         = DiscordDetector._version_key(version)
            status       = DiscordDetector.get_injection_status(norm)
            chrome_ver   = DiscordDetector._get_chrome_version(norm)
            sha256       = DiscordDetector.hash_file(norm)
            candidate = {
                "flavor": flavor, "version": version, "path": norm,
                "injected": status["injected"], "dcdns_version": status["dcdns_version"],
                "up_to_date": status["up_to_date"], "chrome_version": chrome_ver,
                "sha256": sha256, "_mtime": mtime, "_vkey": vkey,
            }
            current = best.get(flavor)
            if current is None:
                best[flavor] = candidate; return
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
            ("discord",       "Discord",       "DISCORD"),
            ("discordptb",    "DiscordPTB",    "DISCORDPTB"),
            ("discordcanary", "DiscordCanary", "DISCORDCANARY"),
        ]
        local       = os.getenv("LOCALAPPDATA", "")
        roaming     = os.getenv("APPDATA", "")
        pf          = os.getenv("ProgramFiles",        r"C:\Program Files")
        pf86        = os.getenv("ProgramFiles(x86)",   r"C:\Program Files (x86)")
        userprofile = os.getenv("USERPROFILE", os.path.expanduser("~"))

        raw_bases = [
            local, roaming,
            os.path.join(userprofile, "AppData", "Local"),
            os.path.join(userprofile, "AppData", "Roaming"),
        ]
        seen_bases, bases = set(), []
        for b in raw_bases:
            if not b: continue
            norm = os.path.normcase(os.path.normpath(b))
            if norm in seen_bases: continue
            seen_bases.add(norm); bases.append(b)

        for base in bases:
            for lower, title, flavor in WIN_DIRS:
                scan_core(os.path.join(base, lower), flavor)
                scan_core(os.path.join(base, title), flavor)
                scan_core(os.path.join(base, lower.capitalize()), flavor)

        for prog in [pf, pf86]:
            if not prog: continue
            for lower, title, flavor in WIN_DIRS:
                scan_core(os.path.join(prog, title), flavor)

        results = []
        for flavor in FLAVORS:
            cand = best.get(flavor)
            if cand:
                results.append({
                    "flavor": cand["flavor"], "version": cand["version"], "path": cand["path"],
                    "injected": cand["injected"], "dcdns_version": cand["dcdns_version"],
                    "up_to_date": cand["up_to_date"], "chrome_version": cand["chrome_version"],
                    "sha256": cand["sha256"],
                })
        return results

    @staticmethod
    def hash_file(path):
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    h.update(chunk)
            return h.hexdigest()
        except Exception:
            return ""

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
                for cc in glob.glob(os.path.join(base, "chrome-*")):
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
        start = content.find(PAYLOAD_MARKER)
        end   = content.find(FOOTER_TAG)
        if start != -1 and end != -1:
            end += len(FOOTER_TAG)
            stripped = content[:start] + content[end:]
            return stripped.lstrip("\n")
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
                    dirs[:] = []; continue
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
            exe_name   = WINDOWS_EXE_NAMES.get(flavor, "Discord.exe")
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


def _build_payload(settings):
    """Build the JS payload with settings baked in as defaults."""
    if not settings:
        return DCDNS_PAYLOAD

    payload = DCDNS_PAYLOAD

    # Boolean flags
    bool_map = {
        "blockTelemetry":    "BLOCK_TELEMETRY_ENABLED",
        "showLabel":         "DCDNS_LABEL_ENABLED",
        "blockWebrtc":       "BLOCK_WEBRTC_LEAK",
        "blockGeolocation":  "BLOCK_GEOLOCATION",
        "disableSpellcheck": "DISABLE_SPELLCHECK",
        "hardenTls":         "HARDEN_TLS",
        "cleanUserAgent":    "CLEAN_USERAGENT",
        "blockCrashReports": "BLOCK_CRASH_REPORTS",
        "disableUpdateCheck":"DISABLE_UPDATE_CHECK",
    }
    for key, js_var in bool_map.items():
        val = settings.get(key)
        if val is False:
            payload = re.sub(
                r"var " + js_var + r" = (true|false);",
                "var " + js_var + " = false;",
                payload,
            )
        elif val is True:
            payload = re.sub(
                r"var " + js_var + r" = (true|false);",
                "var " + js_var + " = true;",
                payload,
            )

    # Custom DNS
    primary  = str(settings.get("customDnsPrimary",  "") or "").strip()
    fallback = str(settings.get("customDnsFallback", "") or "").strip()
    if primary:
        payload = re.sub(
            r"var CUSTOM_DNS_PRIMARY\s*=\s*\([^;]+\);",
            "var CUSTOM_DNS_PRIMARY = '" + primary.replace("'", "\\'") + "';",
            payload,
        )
    if fallback:
        payload = re.sub(
            r"var CUSTOM_DNS_FALLBACK\s*=\s*\([^;]+\);",
            "var CUSTOM_DNS_FALLBACK = '" + fallback.replace("'", "\\'") + "';",
            payload,
        )

    # Custom User-Agent
    custom_ua = str(settings.get("customUserAgent", "") or "").strip()
    if custom_ua:
        payload = re.sub(
            r"var CUSTOM_USERAGENT\s*=\s*\([^;]+\);",
            "var CUSTOM_USERAGENT = '" + custom_ua.replace("'", "\\'") + "';",
            payload,
        )

    # Label position
    label_pos = str(settings.get("labelPosition", "") or "").strip()
    if label_pos:
        payload = re.sub(
            r"var LABEL_POSITION\s*=\s*[^;]+;",
            "var LABEL_POSITION = '" + label_pos.replace("'", "\\'") + "';",
            payload,
        )

    return payload


# ---------------------------------------------------------------------------
# API exposed to the WebView UI
# ---------------------------------------------------------------------------
class Api:
    def __init__(self):
        self.window       = None
        self.installations= []
        self._queue       = queue.Queue()
        self._running     = True
        self._js_lock     = threading.Lock()
        self._op_lock     = threading.Lock()
        self._pending_install = None
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
        except Exception:
            return json.dumps([])

    def browse_for_client(self):
        try:
            start_dir = DiscordDetector.guess_browse_dir()
            try:
                dialog_type = webview.FileDialog.OPEN
            except AttributeError:
                dialog_type = webview.OPEN_DIALOG
            result = self.window.create_file_dialog(
                dialog_type, directory=start_dir, allow_multiple=False,
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
            flavor       = DiscordDetector.guess_flavor(resolved)
            version      = DiscordDetector._get_version(resolved)
            status       = DiscordDetector.get_injection_status(resolved)
            chrome_ver   = DiscordDetector._get_chrome_version(resolved)
            sha256       = DiscordDetector.hash_file(resolved)
            return json.dumps({
                "flavor": flavor, "version": version, "path": resolved,
                "injected": status["injected"], "dcdns_version": status["dcdns_version"],
                "up_to_date": status["up_to_date"], "chrome_version": chrome_ver, "sha256": sha256,
            })
        except Exception as ex:
            return json.dumps({"error": str(ex)})

    def open_discord(self):
        try:
            open_discord_invite()
        except Exception:
            pass

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
        lock_held = True
        try:
            try:
                inst = json.loads(inst_json)
            except Exception:
                self._op_lock.release()
                return "invalid"
            target = inst.get("path", "")
            if not target or not os.path.isfile(target):
                self._op_lock.release()
                return "invalid"
            backup = target + ".dcdns.bak"
            if os.path.exists(backup):
                self._pending_install = inst
                self._op_lock.release()
                lock_held = False
                return "ask_backup"
            threading.Thread(target=self._run_install, args=(inst, False), daemon=True).start()
            lock_held = False
            self._op_lock.release()
            return "ok"
        except Exception:
            if lock_held:
                try:
                    self._op_lock.release()
                except RuntimeError:
                    pass
            return "invalid"

    def install_confirm_backup(self, choice):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            inst = self._pending_install
            self._pending_install = None
            if not inst:
                return "invalid"
            overwrite = choice == "overwrite"
            threading.Thread(target=self._run_install, args=(inst, overwrite), daemon=True).start()
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

    def _run_install(self, inst, overwrite_backup):
        target   = inst.get("path", "")
        flavor   = inst.get("flavor", "DISCORD")
        settings = inst.get("settings", {})
        backup   = target + ".dcdns.bak"
        self._log("=" * 40)
        self._log("INSTALL -> " + flavor)
        self._log("=" * 40)
        try:
            self._log("[1/7] Validating target file...")
            if not os.path.isfile(target):
                self._log("[X] Target file not found: " + target)
                self._finish(False); return

            self._log("[2/7] Closing running Discord processes...")
            names  = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
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
            if os.path.exists(backup):
                if overwrite_backup:
                    shutil.copyfile(target, backup)
                    self._log("[+] Backup overwritten: " + os.path.basename(backup))
                else:
                    self._log("[!] Keeping existing backup.")
            else:
                shutil.copyfile(target, backup)
                self._log("[+] Backup created: " + os.path.basename(backup))

            self._log("[6/7] Injecting DcDNS payload...")
            payload     = _build_payload(settings)
            new_content = payload + content
            DiscordDetector.write_text(target, new_content)

            self._log("[7/7] Verifying injection...")
            if DiscordDetector._is_injected(target):
                self._log("[+] Payload verified in file.")
            else:
                self._log("[X] Verification failed — payload not found after write.")
                self._finish(False); return

            sha256 = DiscordDetector.hash_file(target)
            if sha256:
                self._log("[+] SHA-256: " + sha256)

            self._log("[+] Launching Discord...")
            if DiscordDetector.launch_client(target, flavor):
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
            names  = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
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
                try:
                    os.remove(backup)
                    self._log("[+] Backup removed.")
                except Exception as rem_ex:
                    self._log("[!] Could not remove backup: " + str(rem_ex))
            else:
                self._log("[!] No backup — stripping payload manually...")
                if not os.path.isfile(target):
                    self._log("[X] Target file not found.")
                    self._finish(False); return
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
                if DiscordDetector.launch_client(target, flavor):
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
            launched = False
            if target and os.path.isfile(target):
                launched = DiscordDetector.launch_client(target, flavor)
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


def open_discord_invite():
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
    try:
        api    = Api()
        window = webview.create_window(
            "DcDNS",
            html=HTML_TEMPLATE,
            width=780,
            height=560,
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
