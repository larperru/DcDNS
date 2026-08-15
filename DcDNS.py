# ==============================================================================
# DcDNS
# ==============================================================================
# Author:      Larper.ru
# Version:     v1.0.7
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
import socket
import struct

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
WEBSITE_URL = "https://dcdns.pages.dev/"
GITHUB_REPO_SLUG = "larperru/DcDNS"
APP_VERSION = "1.0.7"

PAYLOAD_MARKER = "/* === [DcDNS Policy Framework"
HEADER_TAG = "/* === [DcDNS Policy Framework v" + APP_VERSION + "] === */"
FOOTER_TAG = "/* === [End DcDNS Policy Framework] === */"

DISCORD_TELEMETRY_PATTERNS = [
    r"/api/v\d+/science",
    r"/api/v\d+/track",
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
    r"discord\.com/api/v\d+/events/stats",
    r"discord\.com/api/v\d+/analytics",
    r"datadog-agent",
    r"browser-intake-datadoghq\.com",
]

_DCDNS_PAYLOAD_BODY = r"""(function() {
    'use strict';
    try {
        var electron;
        try { electron = require('electron'); } catch(e) { return; }
        var app     = (electron && electron.app)     || (electron && electron.default && electron.default.app);
        var session = (electron && electron.session)  || (electron && electron.default && electron.default.session);
        var shell   = (electron && electron.shell)    || (electron && electron.default && electron.default.shell);
        if (!app) return;

        function readConf() {
            try {
                var fs = require('fs');
                var path = require('path');
                var execDir = path.dirname(process.execPath || '');
                var portableFile = path.join(execDir, 'dcdns_portable.json');
                if (fs.existsSync(portableFile)) {
                    try {
                        var raw = fs.readFileSync(portableFile, 'utf8');
                        return JSON.parse(raw);
                    } catch(e) {}
                }
                var cfgFile = path.join(app.getPath('userData'), 'dcdns_conf.json');
                if (fs.existsSync(cfgFile)) {
                    var raw2 = fs.readFileSync(cfgFile, 'utf8');
                    return JSON.parse(raw2);
                }
            } catch(e) {}
            return {};
        }
        var __conf = readConf();

        var DCDNS_LABEL_ENABLED       = __conf.showLabel       !== false;
        var BLOCK_TELEMETRY_ENABLED   = __conf.blockTelemetry  !== false;
        var BLOCK_WEBRTC_LEAK         = __conf.blockWebrtc     !== false;
        var BLOCK_GEOLOCATION         = __conf.blockGeolocation !== false;
        var DISABLE_SPELLCHECK        = __conf.disableSpellcheck !== false;
        var HARDEN_TLS                = __conf.hardenTls        !== false;
        var CLEAN_USERAGENT           = __conf.cleanUserAgent   !== false;
        var BLOCK_CRASH_REPORTS       = __conf.blockCrashReports !== false;
        var BLOCK_REMOTE_AUTH         = __conf.blockRemoteAuth  !== false;
        var SPOOF_CANVAS              = __conf.spoofCanvas      !== false;
        var SPOOF_AUDIO               = __conf.spoofAudio       !== false;
        var SPOOF_WEBGL               = __conf.spoofWebgl       !== false;
        var STRIP_REFERRER            = __conf.stripReferrer    !== false;
        var DISABLE_UPDATE_CHECK      = false;
        var CUSTOM_DNS_PRIMARY        = (__conf.customDnsPrimary   && __conf.customDnsPrimary.trim())   || 'https://dns.mullvad.net/dns-query';
        var CUSTOM_DNS_FALLBACK       = (__conf.customDnsFallback  && __conf.customDnsFallback.trim())  || 'https://adblock.dns.mullvad.net/dns-query';
        var CUSTOM_USERAGENT          = (__conf.customUserAgent && __conf.customUserAgent.trim()) || '';
        var LABEL_POSITION            = __conf.labelPosition || 'bottom-right';

        var TELEMETRY_PATTERNS = [
            /\/api\/v\d+\/science/,
            /\/api\/v\d+\/track/,
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
            /click\.discord\.com/,
            /discord\.com\/api\/v\d+\/analytics/,
            /browser-intake-datadoghq\.com/
        ];

        var REMOTE_AUTH_PATTERNS = [
            /remote-auth-gateway\.discord\.gg/
        ];

        function isTelemetryUrl(url) {
            if (!url || !BLOCK_TELEMETRY_ENABLED) return false;
            for (var i = 0; i < TELEMETRY_PATTERNS.length; i++) {
                if (TELEMETRY_PATTERNS[i].test(url)) return true;
            }
            return false;
        }

        function isRemoteAuthUrl(url) {
            if (!url || !BLOCK_REMOTE_AUTH) return false;
            for (var i = 0; i < REMOTE_AUTH_PATTERNS.length; i++) {
                if (REMOTE_AUTH_PATTERNS[i].test(url)) return true;
            }
            return false;
        }

        function isCrashUrl(url) {
            if (!url || !BLOCK_CRASH_REPORTS) return false;
            return /crash-reports|breakpad|crash\.discord\.com/i.test(url);
        }

        function safeSwitch(name, value) {
            try {
                if (app.commandLine && typeof app.commandLine.appendSwitch === 'function') {
                    if (value !== undefined) {
                        app.commandLine.appendSwitch(name, String(value));
                    } else {
                        app.commandLine.appendSwitch(name);
                    }
                }
            } catch (e) {}
        }

        if (typeof app.commandLine !== 'undefined') {
            if (BLOCK_WEBRTC_LEAK) {
                safeSwitch('force-webrtc-ip-handling-policy', 'default_public_interface_only');
                safeSwitch('webrtc-ip-handling-policy',       'default_public_interface_only');
            }
            safeSwitch('disable-client-side-phishing-detection','1');
            safeSwitch('disable-component-update',              '1');
            safeSwitch('metrics-recording-only',                '1');
            safeSwitch('no-pings',                              '1');
            safeSwitch('disable-domain-reliability',            '1');
            safeSwitch('disable-features',
                'ReportingObserver,NetworkTimeServiceQuerying,SafeBrowsingExtendedReporting,HyperlinkAuditing,AutofillServerCommunication,MediaRouter,DialMediaRouteProvider,GamepadPolling');
            if (BLOCK_CRASH_REPORTS) {
                safeSwitch('disable-breakpad',      '1');
                safeSwitch('no-crash-upload',       '1');
                safeSwitch('disable-crash-reporter','1');
            }
            var dohTemplate = encodeURIComponent(CUSTOM_DNS_PRIMARY) + ' ' + encodeURIComponent(CUSTOM_DNS_FALLBACK);
            safeSwitch('enable-features',
                'DnsOverHttps:Fallback/false/Templates/' + dohTemplate);
        }

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

        function applySessionPolicy(sess) {
            if (!sess) return;

            if (DISABLE_SPELLCHECK) {
                try {
                    if (typeof sess.setSpellCheckerEnabled === 'function') {
                        sess.setSpellCheckerEnabled(false);
                    }
                } catch (e) {}
            }

            try {
                if (typeof sess.setPermissionRequestHandler === 'function') {
                    sess.setPermissionRequestHandler(function(webContents, permission, callback) {
                        try {
                            if (BLOCK_GEOLOCATION && permission === 'geolocation') {
                                callback(false);
                                return;
                            }
                            if (permission === 'notifications') {
                                callback(true);
                                return;
                            }
                            if (permission === 'media') {
                                callback(true);
                                return;
                            }
                            callback(true);
                        } catch (e) { try { callback(true); } catch (e2) {} }
                    });
                }
            } catch (e) {}

            try {
                if (typeof sess.setPermissionCheckHandler === 'function') {
                    sess.setPermissionCheckHandler(function(webContents, permission, requestingOrigin) {
                        if (BLOCK_GEOLOCATION && permission === 'geolocation') return false;
                        return true;
                    });
                }
            } catch (e) {}

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

            try {
                if (sess.webRequest && typeof sess.webRequest.onBeforeRequest === 'function') {
                    sess.webRequest.onBeforeRequest(function(details, callback) {
                        try {
                            var url = details.url || '';
                            if (isTelemetryUrl(url) || isCrashUrl(url) || isRemoteAuthUrl(url)) {
                                callback({ cancel: true });
                                return;
                            }
                        } catch (e) {}
                        try { callback({}); } catch (e) {}
                    });
                }
            } catch (e) {}

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

            try {
                if (typeof sess.clearHostResolverCache === 'function') {
                    sess.clearHostResolverCache();
                }
            } catch (e) {}

            if (HARDEN_TLS) {
                try {
                    if (typeof sess.setSSLConfig === 'function') {
                        sess.setSSLConfig({ minVersion: 'tls1.2', disabledCipherSuites: [] });
                    }
                } catch (e) {}
            }

            if (STRIP_REFERRER) {
                try {
                    if (sess.webRequest && typeof sess.webRequest.onBeforeSendHeaders === 'function') {
                        sess.webRequest.onBeforeSendHeaders({ urls: ['*://*/*'] }, function(details, callback) {
                            try {
                                var headers = details.requestHeaders || {};
                                delete headers['X-Client-Data'];
                                delete headers['X-Goog-Visitor-Id'];
                                delete headers['X-Firebase-Client'];
                                var ref = headers['Referer'] || headers['referer'] || '';
                                if (ref) {
                                    try {
                                        var u = new URL(ref);
                                        headers['Referer'] = u.origin + '/';
                                    } catch (e) {
                                        delete headers['Referer'];
                                        delete headers['referer'];
                                    }
                                }
                                callback({ requestHeaders: headers });
                            } catch (e) { try { callback({}); } catch (e2) {} }
                        });
                    }
                } catch (e) {}
            }
        }

        var DCDNS_FINGERPRINT_SCRIPT = (function() {
            var parts = [];
            parts.push('(function(){');
            parts.push('if(window.__dcdnsFPPatched)return;window.__dcdnsFPPatched=true;');
            if (SPOOF_CANVAS) {
                parts.push(
                    'try{' +
                    'var _oc=HTMLCanvasElement.prototype.toDataURL;' +
                    'HTMLCanvasElement.prototype.toDataURL=function(){' +
                    'var d=_oc.apply(this,arguments);' +
                    'if(!d||d.length<100)return d;' +
                    'var n=Math.random()*0.0004-0.0002;' +
                    'return d.slice(0,-4)+(n>0?"1":"0")+"===";' +
                    '};' +
                    'var _ob=HTMLCanvasElement.prototype.toBlob;' +
                    'HTMLCanvasElement.prototype.toBlob=function(cb,t,q){' +
                    'return _ob.call(this,cb,t,q);' +
                    '};' +
                    'var _og=CanvasRenderingContext2D.prototype.getImageData;' +
                    'CanvasRenderingContext2D.prototype.getImageData=function(x,y,w,h){' +
                    'var d=_og.apply(this,arguments);' +
                    'if(d&&d.data&&d.data.length>0){' +
                    'var idx=Math.floor(Math.random()*(d.data.length/4))*4;' +
                    'd.data[idx]=(d.data[idx]+1)%256;' +
                    '}' +
                    'return d;' +
                    '};' +
                    '}catch(e){}'
                );
            }
            if (SPOOF_AUDIO) {
                parts.push(
                    'try{' +
                    'var _AC=window.AudioContext||window.webkitAudioContext;' +
                    'if(_AC){' +
                    'var _orig_createAn=_AC.prototype.createAnalyser;' +
                    '_AC.prototype.createAnalyser=function(){' +
                    'var a=_orig_createAn.apply(this,arguments);' +
                    'var _gf=a.getFloatFrequencyData.bind(a);' +
                    'a.getFloatFrequencyData=function(arr){' +
                    '_gf(arr);' +
                    'if(arr&&arr.length>0)arr[0]+=Math.random()*0.0001-0.00005;' +
                    '};' +
                    'return a;' +
                    '};' +
                    '}' +
                    '}catch(e){}'
                );
            }
            if (SPOOF_WEBGL) {
                parts.push(
                    'try{' +
                    'var _getP=WebGLRenderingContext.prototype.getParameter;' +
                    'WebGLRenderingContext.prototype.getParameter=function(p){' +
                    'if(p===37445)return "DcDNS Graphics";' +
                    'if(p===37446)return "DcDNS Renderer";' +
                    'return _getP.apply(this,arguments);' +
                    '};' +
                    '}catch(e){}' +
                    'try{' +
                    'var _getP2=WebGL2RenderingContext.prototype.getParameter;' +
                    'WebGL2RenderingContext.prototype.getParameter=function(p){' +
                    'if(p===37445)return "DcDNS Graphics";' +
                    'if(p===37446)return "DcDNS Renderer";' +
                    'return _getP2.apply(this,arguments);' +
                    '};' +
                    '}catch(e){}'
                );
            }
            parts.push('})();');
            return parts.join('');
        })();

        function getElectronVersion() {
            try { return (process && process.versions && process.versions.electron) || ''; }
            catch (e) { return ''; }
        }
        function getChromeVersion() {
            try { return (process && process.versions && process.versions.chrome) || ''; }
            catch (e) { return ''; }
        }

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
'    var _obs=new MutationObserver(function(){\n' +
'      if(!_currentLabel||!isInDOM(_currentLabel)){setTimeout(inject,30);}\n' +
'    });\n' +
'    if(document.documentElement){\n' +
'      _obs.observe(document.documentElement,{childList:true,subtree:true});\n' +
'    }\n' +
'    document.addEventListener("fullscreenchange",function(){setTimeout(inject,60);},true);\n' +
'    document.addEventListener("webkitfullscreenchange",function(){setTimeout(inject,60);},true);\n' +
'    setInterval(function(){try{inject();}catch(e){}},2000);\n' +
'    if(document.readyState==="complete"||document.readyState==="interactive"){inject();}\n' +
'    else{document.addEventListener("DOMContentLoaded",inject);}\n' +
'  }catch(e){}\n' +
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

        function patchDiscordCrashHandlers(contents) {
            try {
                if (!contents || typeof contents.isDestroyed === 'function' && contents.isDestroyed()) return;
                var crashPatch = '(function(){\n' +
'  try {\n' +
'    if (window.__dcdnsCrashPatched) return;\n' +
'    window.__dcdnsCrashPatched = true;\n' +
'    window.addEventListener("unhandledrejection", function(e) {\n' +
'      try {\n' +
'        if (e && e.reason && String(e.reason).indexOf("game") !== -1) {\n' +
'          e.preventDefault(); return;\n' +
'        }\n' +
'      } catch(x) {}\n' +
'    }, true);\n' +
'  } catch(e) {}\n' +
'})();';
                contents.executeJavaScript(crashPatch, true).catch(function() {});
            } catch(e) {}
        }

        function attachLabelInjector(contents) {
            try {
                if (!contents || typeof contents.isDestroyed === 'function' && contents.isDestroyed()) return;
                dcdnsKnownContents.push(contents);
                contents.on('dom-ready', function() {
                    try { if (contents.isDestroyed()) return; } catch(e) { return; }
                    patchDiscordCrashHandlers(contents);
                    if (DCDNS_FINGERPRINT_SCRIPT) {
                        try {
                            contents.executeJavaScript(DCDNS_FINGERPRINT_SCRIPT, true).catch(function() {});
                        } catch (e) {}
                    }
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
"""

DCDNS_PAYLOAD = HEADER_TAG + "\n" + _DCDNS_PAYLOAD_BODY + FOOTER_TAG + "\n"

POLICY_TEXT = """\
DcDNS Policy Framework v{version}
\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501

WHAT DcDNS IS

  DcDNS is a free, open-source privacy tool for Discord's Windows
  desktop client. It works by prepending a small JavaScript payload
  to Discord's Electron main-process entry point (index.js). This
  payload executes before Discord's own code and applies a set of
  hardened network and privacy policies at the Electron / Chromium
  engine level.

  DcDNS operates entirely on your local machine. It does not
  communicate with any DcDNS server. It does not have a backend.
  No data about you, your machine, or your Discord usage is ever
  sent anywhere by DcDNS itself.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
PRIVACY PROTECTIONS (ACTIVE BY DEFAULT)

  RULE 1 - Encrypted DNS (DNS-over-HTTPS)
    Every DNS lookup made by the Discord client is forced through a
    DNS-over-HTTPS (DoH) resolver, bypassing your ISP's plaintext
    resolver entirely.

      Default Primary:  https://dns.mullvad.net/dns-query
      Default Fallback: https://adblock.dns.mullvad.net/dns-query

  RULE 2 - WebRTC IP Leak Prevention (toggleable)
    WebRTC is locked to "default_public_interface_only" mode.
    Your local network IP address is never exposed to call participants.

  RULE 3 - Geolocation Blocked (toggleable)
    All geolocation permission requests from Discord are denied.

  RULE 4 - Spellcheck Disabled (toggleable)
    Chromium's spellchecker is disabled so keystrokes are never
    sent to Google's spellcheck endpoint.

  RULE 5 - Discord Telemetry Blocked (toggleable)
    Network requests to Discord's analytics, science, metrics,
    typing indicators, and tracking endpoints are cancelled.
    Mixpanel, Segment, Amplitude also blocked.

  RULE 6 - Crash Report Blocking (toggleable)
    Sentry and Discord crash upload endpoints are blocked.
    Chromium's Breakpad crash reporter is disabled.

  RULE 7 - Chromium Privacy Hardening (always active)
    --disable-background-networking
    --disable-client-side-phishing-detection
    --disable-component-update
    --disable-sync, --metrics-recording-only, --no-pings
    GamepadPolling and MediaRouter are disabled.
    Tracking headers (X-Client-Data, X-Super-Properties) stripped.

  RULE 8 - TLS 1.2+ Hardening (toggleable)
    Minimum TLS version enforced at 1.2.

  RULE 9 - User-Agent Cleaning (toggleable)
    Electron and Discord tokens stripped from the User-Agent header.

  RULE 10 - Title Bar Label (toggleable)
    "Encrypted by DcDNS" badge injected into Discord's renderer.

  RULE 11 - Update Notifications
    Periodic version check to GitHub API only. No personal data sent.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
BACKUP & RESTORE

  Before modifying index.js, DcDNS copies the original file to
  index.js.dcdns.bak. Uninstalling restores the backup exactly.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
WHAT DcDNS DOES NOT DO

  DcDNS explicitly does not:
  - Read, log, store, or transmit anything you type in Discord.
  - Read, modify, or access your messages, calls, or shared files.
  - Access, read, or store your Discord account credentials or token.
  - Persist across a Discord auto-update.
  - Install background services, startup entries, or daemons.
  - Communicate with any DcDNS-operated server or service.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
RISKS & LIMITATIONS

  - Discord's Terms of Service do not permit third-party modifications.
    Use DcDNS at your own discretion and risk.
  - Every Discord auto-update overwrites index.js, removing DcDNS.
    You must reinstall DcDNS after each Discord update.
  - DcDNS does not guarantee anonymity or complete privacy. It reduces
    passive data collection but does not replace a VPN.

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
OPEN SOURCE & LICENCE

  DcDNS is free and open-source software released under the MIT Licence.
  Source: https://github.com/{repo}
  Website: https://dcdns.pages.dev/

\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501
By clicking "I Agree & Continue" you confirm that you have read
and understood this policy in full and accept complete responsibility
for any modifications made to your local Discord client installation.
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
            '<div class="dc-ver" id="dc-ver-' + suffix + '">Waiting...</div>'
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
.discord-invite-btn{display:inline-flex;align-items:center;gap:5px;background:rgba(168,85,247,.1);border:1px solid rgba(168,85,247,.28);border-radius:8px;color:#c4b5fd;font-family:inherit;font-size:10px;font-weight:600;padding:4px 10px;cursor:pointer;transition:background .18s ease,border-color .18s ease,color .18s ease;flex-shrink:0;white-space:nowrap}
.discord-invite-btn:hover{background:rgba(168,85,247,.2);border-color:rgba(168,85,247,.55);color:#ddd6fe}
.discord-invite-btn.discord-btn{background:rgba(88,101,242,.12);border-color:rgba(88,101,242,.35);color:#7983f5}
.discord-invite-btn.discord-btn:hover{background:rgba(88,101,242,.22);border-color:rgba(88,101,242,.6);color:#9fa8fa}
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
    <span id="portable-badge" style="display:none;font-size:9px;font-weight:700;background:rgba(34,197,94,.12);color:#22c55e;border:1px solid rgba(34,197,94,.3);border-radius:5px;padding:2px 7px;margin-left:2px;letter-spacing:.04em">PORTABLE</span>

    <div class="header-right">
      <button class="icon-btn" id="btn-open-settings" title="Settings">""" + SETTINGS_SVG + """</button>
    </div>
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
      <div style="display:flex;gap:6px;margin-left:auto">
        <button class="discord-invite-btn" id="btn-website" title="Official DcDNS website">
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
          Website
        </button>
        <button class="discord-invite-btn discord-btn" id="btn-discord-invite" title="Join our Discord server">
          <svg xmlns="http://www.w3.org/2000/svg" width="11" height="11" viewBox="0 0 127.14 96.36" fill="currentColor"><path d="M107.7,8.07A105.15,105.15,0,0,0,81.47,0a72.06,72.06,0,0,0-3.36,6.83A97.68,97.68,0,0,0,49,6.83,72.37,72.37,0,0,0,45.64,0,105.89,105.89,0,0,0,19.39,8.09C2.79,32.65-1.71,56.6.54,80.21h0A105.73,105.73,0,0,0,32.71,96.36,77.7,77.7,0,0,0,39.6,85.26a68.42,68.42,0,0,1-10.85-5.18c.91-.66,1.8-1.34,2.66-2a75.57,75.57,0,0,0,64.32,0c.87.71,1.76,1.39,2.66,2a68.68,68.68,0,0,1-10.87,5.19,77,77,0,0,0,6.89,11.1A105.25,105.25,0,0,0,126.6,80.22h0C129.24,52.84,122.09,29.11,107.7,8.07ZM42.45,65.69C36.18,65.69,31,60,31,53s5-12.74,11.43-12.74S54,46,53.89,53,48.84,65.69,42.45,65.69Zm42.24,0C78.41,65.69,73.25,60,73.25,53s5-12.74,11.44-12.74S96.23,46,96.12,53,91.08,65.69,84.69,65.69Z"/></svg>
          Discord
        </button>
      </div>
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

  <div class="page" id="page-settings">
    <div class="page-title">Settings</div>
    <div class="card">
      <div class="card-inner" style="padding:14px 18px">

        <div class="settings-group-title">Label</div>

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

        <div class="settings-group-title">Privacy</div>

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
            <div class="settings-desc">Enforce minimum TLS 1.2 - reject older insecure connections</div>
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
        <div class="settings-row">
          <div>
            <div class="settings-label">Block Remote Auth Gateway</div>
            <div class="settings-desc">Block remote authentication sessions (QR code login tracking)</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-remote-auth" checked><span class="toggle-slider"></span></label>
        </div>

        <div class="settings-group-title">Fingerprint Protection</div>

        <div class="settings-row">
          <div>
            <div class="settings-label">Canvas Fingerprint Noise</div>
            <div class="settings-desc">Inject subtle noise into canvas reads to randomize your fingerprint each session</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-canvas" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Audio Fingerprint Noise</div>
            <div class="settings-desc">Add imperceptible noise to AudioContext data used for hardware fingerprinting</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-audio" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">WebGL Vendor Spoofing</div>
            <div class="settings-desc">Hide GPU model and vendor string from WebGL fingerprinting APIs</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-webgl" checked><span class="toggle-slider"></span></label>
        </div>
        <div class="settings-row">
          <div>
            <div class="settings-label">Strip Referrer Headers</div>
            <div class="settings-desc">Trim Referer headers to origin only — prevents cross-site tracking via URL leakage</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-referrer" checked><span class="toggle-slider"></span></label>
        </div>

        <div class="settings-group-title">DNS</div>

        <div class="settings-row" style="flex-direction:column;align-items:flex-start">
          <div>
            <div class="settings-label">Custom DoH Server - Primary</div>
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
            <div class="settings-label">Custom DoH Server - Fallback</div>
            <div class="settings-desc">Used if primary DoH server is unreachable</div>
          </div>
          <input class="settings-input" id="input-dns-fallback" type="text" placeholder="https://adblock.dns.mullvad.net/dns-query" spellcheck="false">
        </div>

        <div class="settings-group-title">User-Agent</div>

        <div class="settings-row" style="flex-direction:column;align-items:flex-start">
          <div>
            <div class="settings-label">Custom User-Agent String</div>
            <div class="settings-desc">Override with a specific UA. Leave blank to auto-clean.</div>
          </div>
          <input class="settings-input" id="input-custom-ua" type="text" placeholder="e.g. Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..." spellcheck="false">
        </div>

        <div class="settings-group-title">Rich Presence</div>

        <div class="settings-row">
          <div>
            <div class="settings-label">Discord Rich Presence</div>
            <div class="settings-desc">Show "Using DcDNS" status in Discord (only when DcDNS.exe is running)</div>
          </div>
          <label class="toggle"><input type="checkbox" id="toggle-rpc" checked><span class="toggle-slider"></span></label>
        </div>

      </div>
    </div>
    <div class="foot">
      <button class="btn nav-back" id="btn-settings-back">&larr; Back</button>
      <button class="btn primary" id="btn-settings-save">Save &amp; Close</button>
    </div>
  </div>
</div>

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
  blockRemoteAuth:   true,
  spoofCanvas:       true,
  spoofAudio:        true,
  spoofWebgl:        true,
  stripReferrer:     true,
  enableRpc:         true,
  customDnsPrimary:  '',
  customDnsFallback: '',
  customUserAgent:   ''
};

function saveSettings() {
  try {
    waitForApi(function() {
      try { window.pywebview.api.save_settings(JSON.stringify(_settings)); } catch(e) {}
    }, 10);
  } catch(e) {}
}

waitForApi(function() {
  try {
    window.pywebview.api.load_settings().then(function(raw) {
      try {
        if (raw) {
          var parsed = JSON.parse(raw);
          if (parsed) _settings = Object.assign(_settings, parsed);
        }
      } catch(e) {}
    }).catch(function() {});
  } catch(e) {}
}, 30);

waitForApi(function() {
  try {
    window.pywebview.api.get_mode().then(function(res) {
      try {
        var mode = JSON.parse(res);
        var badge = safeEl('portable-badge');
        if (badge && mode && mode.portable) {
          badge.style.display = '';
          badge.title = 'Config: ' + (mode.portable_path || 'dcdns_portable.json');
        }
      } catch(e) {}
    }).catch(function() {});
  } catch(e) {}
}, 30);



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

window.selectedInstall = null;
window.discordInstalls = [];
window._backupResolve  = null;

safeBind('agree-check', 'change', function(e) {
  var nextBtn = safeEl('btn-next');
  if (nextBtn) nextBtn.disabled = !e.target.checked;
});
safeBind('btn-discord-invite', 'click', function() {
  waitForApi(function() {
    try { window.pywebview.api.open_discord(); } catch (err) {}
  }, 20);
});
safeBind('btn-website', 'click', function() {
  waitForApi(function() {
    try { window.pywebview.api.open_website(); } catch (err) {}
  }, 20);
});
safeBind('btn-next', 'click', function() {
  var nextBtn = safeEl('btn-next');
  if (nextBtn) nextBtn.disabled = true;
  waitForApi(function() {
    try {
      window.pywebview.api.discord_exists().then(function(res) {
        try {
          var data = res && typeof res === 'string' ? JSON.parse(res) : res;
          if (!data || !data.exists) {
            showPage('install');
            var statusEl = safeEl('install-status');
            if (statusEl) {
              statusEl.textContent = 'Discord is not installed on this computer. Please install Discord first.';
              statusEl.className = 'status err';
            }
            var cards = document.querySelectorAll('.discord-card');
            cards.forEach(function(card) {
              var flavor = card.dataset.flavor;
              var suffix = FLAVOR_MAP[flavor];
              if (suffix) {
                var verEl = safeEl('dc-ver-' + suffix);
                var badgeEl = safeEl('dc-badge-' + suffix);
                if (verEl) verEl.textContent = 'Not installed';
                if (badgeEl) { badgeEl.textContent = 'Not found'; badgeEl.className = 'dc-badge missing'; }
              }
              card.dataset.path = '';
              card.dataset.injected = '0';
            });
            var installBtn = safeEl('btn-install');
            var uninstallBtn = safeEl('btn-uninstall');
            if (installBtn) installBtn.disabled = true;
            if (uninstallBtn) uninstallBtn.disabled = true;
          } else {
            showPage('install');
            scanAll();
          }
        } catch(e) {
          showPage('install');
          scanAll();
        }
      }).catch(function() {
        showPage('install');
        scanAll();
      });
    } catch(e) {
      showPage('install');
      scanAll();
    }
  }, 20);
});
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

try {
  document.querySelectorAll('.dns-preset-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var p = btn.dataset.p, f = btn.dataset.f;
      var ip = safeEl('input-dns-primary'), fi = safeEl('input-dns-fallback');
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
  _settings.blockRemoteAuth    = chk('toggle-remote-auth');
  _settings.spoofCanvas        = chk('toggle-canvas');
  _settings.spoofAudio         = chk('toggle-audio');
  _settings.spoofWebgl         = chk('toggle-webgl');
  _settings.stripReferrer      = chk('toggle-referrer');
  _settings.enableRpc          = chk('toggle-rpc');
  _settings.customDnsPrimary   = val('input-dns-primary');
  _settings.customDnsFallback  = val('input-dns-fallback');
  _settings.customUserAgent    = val('input-custom-ua');
  saveSettings();
  waitForApi(function() {
    try { window.pywebview.api.apply_rpc_setting(_settings.enableRpc); } catch(e) {}
  }, 5);
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
  retries = (retries === undefined || retries === null) ? 30 : retries;
  try {
    if (window.pywebview && window.pywebview.api && typeof window.pywebview.api === 'object') {
      try { callback(); } catch(ce) { console.error('[DcDNS] waitForApi callback error:', ce); }
      return;
    }
  } catch(e) {}
  if (retries <= 0) {
    console.warn('[DcDNS] waitForApi: API not available after max retries');
    return;
  }
  setTimeout(function() { waitForApi(callback, retries - 1); }, 200);
}

function _applyScanResults(data) {
  try {
    window.discordInstalls = Array.isArray(data) ? data : [];
    for (var flavor in FLAVOR_MAP) {
      try {
        var suffix = FLAVOR_MAP[flavor];
        var inst = null;
        for (var j = 0; j < window.discordInstalls.length; j++) {
          if (window.discordInstalls[j].flavor === flavor) { inst = window.discordInstalls[j]; break; }
        }
        var verEl   = safeEl('dc-ver-'   + suffix);
        var badgeEl = safeEl('dc-badge-' + suffix);
        var card    = document.querySelector('.discord-card[data-flavor="' + flavor + '"]');
        if (!verEl || !badgeEl || !card) continue;
        if (inst && inst.path) {
          verEl.textContent = 'v' + (inst.version || 'unknown');
          var badge = badgeInfo(inst);
          badgeEl.textContent = badge.text;
          badgeEl.className   = badge.cls;
          card.dataset.path         = inst.path;
          card.dataset.injected     = inst.injected ? '1' : '0';
          card.dataset.version      = inst.version       || '';
          card.dataset.dcdnsVersion = inst.dcdns_version || '';
          card.dataset.upToDate     = inst.up_to_date === true ? '1' : (inst.up_to_date === false ? '0' : '');
          card.dataset.chromeVersion= inst.chrome_version || '';
          card.dataset.sha256       = inst.sha256 || '';
          card.dataset.stale        = inst.stale ? '1' : '0';
          card.dataset.ageDays      = String(inst.age_days || 0);
        } else {
          verEl.textContent       = 'Not installed';
          badgeEl.textContent     = 'Not found';
          badgeEl.className       = 'dc-badge missing';
          card.dataset.path       = '';
          card.dataset.injected   = '0';
        }
      } catch (innerErr) {}
    }
  } catch (e) {}
}

function scanAll() {
  try {
    var cards = document.querySelectorAll('.discord-card');
    cards.forEach(function(card, i) {
      card.style.animation = 'none';
      void card.offsetWidth;
      card.style.animationDelay = (i * 0.05) + 's';
      card.style.animation = '';
      var suffix = FLAVOR_MAP[card.dataset.flavor];
      if (suffix) {
        var verEl   = safeEl('dc-ver-'   + suffix);
        var badgeEl = safeEl('dc-badge-' + suffix);
        if (verEl)   verEl.innerHTML   = '<span class="spinner"></span>Scanning';
        if (badgeEl) { badgeEl.textContent = 'Scanning'; badgeEl.className = 'dc-badge stock'; }
      }
    });
  } catch (e) {}

  waitForApi(function() {
    try {
      window.pywebview.api.scan_discord().then(function(res) {
        try {
          var data = (res && typeof res === 'string') ? JSON.parse(res) : (Array.isArray(res) ? res : []);
          _applyScanResults(data);
        } catch(parseErr) {
          _applyScanResults([]);
        }
      }).catch(function() {
        _applyScanResults([]);
      });
    } catch(e) {
      _applyScanResults([]);
    }
  }, 40);
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
      if (warnEl)    warnEl.style.display    = 'none';
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
    var dcNameEl = card ? card.querySelector('.dc-name') : null;
    var displayName = (dcNameEl && dcNameEl.textContent) ? dcNameEl.textContent : flavor;
    if (verifyRow) verifyRow.style.display = sha256 ? '' : 'none';
    if (verifyHash) verifyHash.textContent = sha256 ? 'SHA-256: ' + sha256 : '';
    if (verifyBadge) {
      if (sha256) {
        verifyBadge.textContent = 'Verified';
        verifyBadge.className = 'verify-badge ok';
      } else {
        verifyBadge.textContent = 'Not verified';
        verifyBadge.className = 'verify-badge none';
      }
    }
    if (isInjected) {
      var msg = displayName + ': DcDNS v' + dcdnsVersion + ' installed';
      if (!isUpToDate) msg += ' (outdated - reinstall recommended)';
      if (statusEl) { statusEl.textContent = msg; statusEl.className = isUpToDate ? 'status ok' : 'status warn'; }
      if (warnEl) warnEl.style.display = '';
    } else {
      if (statusEl) { statusEl.textContent = displayName + ': Ready to install'; statusEl.className = 'status ok'; }
      if (warnEl) warnEl.style.display = 'none';
    }
    if (installBtn)   installBtn.disabled   = false;
    if (uninstallBtn) uninstallBtn.disabled = !isInjected;
  } catch(e) {}
}

function applySettingsToUI() {
  try {
    function setChk(id, v) { var el = safeEl(id); if (el) el.checked = v; }
    function setVal(id, v) { var el = safeEl(id); if (el) el.value = v || ''; }
    var showLabel = _settings.showLabel !== false;
    setChk('toggle-label',       showLabel);
    setChk('toggle-telemetry',   _settings.blockTelemetry    !== false);
    setChk('toggle-crash',       _settings.blockCrashReports !== false);
    setChk('toggle-webrtc',      _settings.blockWebrtc       !== false);
    setChk('toggle-geo',         _settings.blockGeolocation  !== false);
    setChk('toggle-spell',       _settings.disableSpellcheck !== false);
    setChk('toggle-tls',         _settings.hardenTls         !== false);
    setChk('toggle-ua',          _settings.cleanUserAgent    !== false);
    setChk('toggle-remote-auth', _settings.blockRemoteAuth   !== false);
    setChk('toggle-canvas',      _settings.spoofCanvas       !== false);
    setChk('toggle-audio',       _settings.spoofAudio        !== false);
    setChk('toggle-webgl',       _settings.spoofWebgl        !== false);
    setChk('toggle-referrer',    _settings.stripReferrer     !== false);
    setChk('toggle-rpc',         _settings.enableRpc         !== false);
    setVal('input-dns-primary',  _settings.customDnsPrimary);
    setVal('input-dns-fallback', _settings.customDnsFallback);
    setVal('input-custom-ua',    _settings.customUserAgent);
    var selPos = safeEl('select-label-position');
    if (selPos) selPos.value = _settings.labelPosition || 'bottom-right';
    var posRow = safeEl('row-label-position');
    if (posRow) posRow.style.display = showLabel ? '' : 'none';
  } catch(e) {}
}

safeBind('toggle-label', 'change', function() {
  try {
    var el = safeEl('toggle-label');
    var posRow = safeEl('row-label-position');
    if (el && posRow) posRow.style.display = el.checked ? '' : 'none';
  } catch(e) {}
});

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

safeBind('btn-install', 'click', function() {
  if (!window.selectedInstall) return;
  var inst = Object.assign({}, window.selectedInstall, { settings: _settings });
  var logTitle = safeEl('log-title');
  if (logTitle) logTitle.textContent = 'Installing DcDNS...';
  showPage('log');
  var logBox = safeEl('log-box');
  if (logBox) logBox.innerHTML = '';
  waitForApi(function() {
    try {
      window.pywebview.api.install(JSON.stringify(inst)).then(function(res) {
        try {
          if (res === 'ask_backup') {
            window.__dcdnsAskBackup().then(function(choice) {
              waitForApi(function() {
                try { window.pywebview.api.install_confirm_backup(choice); } catch(e) {}
              }, 10);
            }).catch(function() {});
          } else if (res === 'busy') {
            addLog('[!] Another operation is already running.');
            finishLog(false);
          } else if (res === 'invalid') {
            addLog('[X] Invalid installation target.');
            finishLog(false);
          }
        } catch(re) {}
      }).catch(function(err) {
        try { addLog('[X] Install call failed: ' + (err ? String(err) : 'unknown')); finishLog(false); } catch(e) {}
      });
    } catch(e) {
      try { addLog('[X] Could not contact backend.'); finishLog(false); } catch(ie) {}
    }
  }, 20);
});

safeBind('btn-uninstall', 'click', function() {
  if (!window.selectedInstall) return;
  var logTitle = safeEl('log-title');
  if (logTitle) logTitle.textContent = 'Uninstalling DcDNS...';
  showPage('log');
  var logBox = safeEl('log-box');
  if (logBox) logBox.innerHTML = '';
  waitForApi(function() {
    try {
      window.pywebview.api.uninstall(JSON.stringify(window.selectedInstall)).then(function(res) {
        try {
          if (res === 'busy') { addLog('[!] Another operation is already running.'); finishLog(false); }
          else if (res === 'invalid') { addLog('[X] Invalid installation target.'); finishLog(false); }
        } catch(e) {}
      }).catch(function(err) {
        try { addLog('[X] Uninstall call failed: ' + (err ? String(err) : 'unknown')); finishLog(false); } catch(e) {}
      });
    } catch(e) {
      try { addLog('[X] Could not contact backend.'); finishLog(false); } catch(ie) {}
    }
  }, 20);
});

safeBind('btn-restart', 'click', function() {
  if (!window.selectedInstall) return;
  var restartBtn = safeEl('btn-restart');
  if (restartBtn) { try { restartBtn.disabled = true; } catch(e) {} }
  waitForApi(function() {
    try {
      window.pywebview.api.restart_discord(JSON.stringify(window.selectedInstall)).then(function(res) {
        try {
          if (res === 'busy') { addLog('[!] Another operation is already running.'); finishLog(false); }
          else if (res === 'invalid') { addLog('[X] Invalid target.'); finishLog(false); }
        } catch(e) {}
      }).catch(function(err) {
        try { addLog('[X] Restart call failed: ' + (err ? String(err) : 'unknown')); finishLog(false); } catch(e) {}
      });
    } catch(e) {
      try { addLog('[X] Could not contact backend.'); finishLog(false); } catch(ie) {}
    }
  }, 20);
});

safeBind('btn-back2', 'click', function() {
  showPage('install');
  scanAll();
});

function addLog(msg) {
  try {
    var box = safeEl('log-box');
    if (!box) return;
    var text = (msg === null || msg === undefined) ? '' : String(msg);
    var line = document.createElement('div');
    line.className = 'log-line';
    if (text.indexOf('[+]') === 0) line.className += ' ok';
    else if (text.indexOf('[X]') === 0 || text.indexOf('[!] WARNING') === 0 || text.indexOf('[!] Aborting') === 0) line.className += ' err';
    else if (text.indexOf('[!]') === 0) line.className += ' warn';
    else if (text.indexOf('===') === 0 || text.indexOf('COMPLETE') !== -1 || text.indexOf('->') !== -1) line.className += ' head';
    line.textContent = text;
    box.appendChild(line);
    try { box.scrollTop = box.scrollHeight; } catch(se) {}
  } catch(e) {}
}

function finishLog(ok) {
  try {
    var back2   = safeEl('btn-back2');
    var done    = safeEl('btn-done');
    var restart = safeEl('btn-restart');
    var logTitle= safeEl('log-title');
    if (back2)    { try { back2.disabled   = false; } catch(e) {} }
    if (done)     { try { done.disabled    = false; } catch(e) {} }
    if (restart)  { try { restart.disabled = !ok;   } catch(e) {} }
    if (logTitle) { try { logTitle.textContent = ok ? 'Operation Complete' : 'Operation Failed'; } catch(e) {} }
  } catch(e) {}
}
</script>
</body>
</html>"""


class DiscordRPC:
    CLIENT_ID = "1538182674399760575"
    PIPE_PATH_TEMPLATE = r"\\.\pipe\discord-ipc-{}"

    def __init__(self):
        self._handle = None
        self._active = False
        self._lock = threading.Lock()
        self._thread = None
        self._enabled = True
        self._start_time = int(time.time())

    def _connect(self):
        import ctypes
        import ctypes.wintypes
        GENERIC_READ  = 0x80000000
        GENERIC_WRITE = 0x40000000
        OPEN_EXISTING = 3
        for i in range(10):
            pipe = self.PIPE_PATH_TEMPLATE.format(i)
            try:
                handle = ctypes.windll.kernel32.CreateFileW(
                    pipe, GENERIC_READ | GENERIC_WRITE, 0, None,
                    OPEN_EXISTING, 0, None
                )
                if handle and handle != ctypes.wintypes.HANDLE(-1).value:
                    self._handle = handle
                    return True
            except Exception:
                continue
        return False

    def _send_frame(self, op, payload):
        try:
            import ctypes
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            header = struct.pack("<II", op, len(data))
            full = header + data
            buf = ctypes.create_string_buffer(full)
            written = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.WriteFile(
                self._handle, buf, len(full), ctypes.byref(written), None
            )
            return bool(ok) and written.value == len(full)
        except Exception:
            return False

    def _recv_frame(self):
        try:
            import ctypes
            hdr_buf = ctypes.create_string_buffer(8)
            read = ctypes.c_ulong(0)
            ctypes.windll.kernel32.ReadFile(self._handle, hdr_buf, 8, ctypes.byref(read), None)
            if read.value < 8:
                return None, None
            op, length = struct.unpack("<II", hdr_buf.raw[:8])
            if length == 0:
                return op, {}
            data_buf = ctypes.create_string_buffer(length)
            ctypes.windll.kernel32.ReadFile(self._handle, data_buf, length, ctypes.byref(read), None)
            try:
                return op, json.loads(data_buf.raw[:read.value].decode("utf-8"))
            except Exception:
                return op, {}
        except Exception:
            return None, None

    def _close_handle(self):
        try:
            import ctypes
            if self._handle:
                ctypes.windll.kernel32.CloseHandle(self._handle)
                self._handle = None
        except Exception:
            pass

    def _build_presence(self):
        return {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": {
                    "details": "DcDNS",
                    "state": "Privacy framework for Discord",
                    "timestamps": {"start": self._start_time},
                    "assets": {
                        "large_image": "dcdns_logo",
                        "large_text": "DcDNS v" + APP_VERSION,
                    },
                    "buttons": [
                        {"label": "Website", "url": "https://dcdns.pages.dev/"},
                        {"label": "GitHub", "url": "https://github.com/" + GITHUB_REPO_SLUG},
                    ],
                    "type": 0,
                },
            },
            "nonce": str(int(time.time() * 1000)),
        }

    def _rpc_loop(self):
        _rpc_backoff = 15
        while self._enabled:
            try:
                if not self._connect():
                    self._active = False
                    time.sleep(_rpc_backoff)
                    _rpc_backoff = min(_rpc_backoff * 2, 120)
                    continue

                _rpc_backoff = 15

                if not self._send_frame(0, {"v": 1, "client_id": self.CLIENT_ID}):
                    self._close_handle()
                    self._active = False
                    time.sleep(_rpc_backoff)
                    continue

                op, resp = self._recv_frame()
                if op is None:
                    self._close_handle()
                    self._active = False
                    time.sleep(_rpc_backoff)
                    continue

                presence = self._build_presence()
                if not self._send_frame(1, presence):
                    self._close_handle()
                    self._active = False
                    time.sleep(_rpc_backoff)
                    continue

                self._recv_frame()
                self._active = True

                while self._enabled:
                    time.sleep(15)
                    presence = self._build_presence()
                    if not self._send_frame(1, presence):
                        break
                    self._recv_frame()

                self._close_handle()
                self._active = False

            except Exception:
                self._close_handle()
                self._active = False
                time.sleep(_rpc_backoff)
                _rpc_backoff = min(_rpc_backoff * 2, 120)

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._enabled = True
            self._thread = threading.Thread(target=self._rpc_loop, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            self._enabled = False
            self._active = False
            self._close_handle()

    def is_active(self):
        return self._active and self._enabled


_rpc_instance = None
_rpc_lock = threading.Lock()


def _get_rpc():
    global _rpc_instance
    with _rpc_lock:
        if _rpc_instance is None:
            _rpc_instance = DiscordRPC()
        return _rpc_instance


DEFAULT_PAYLOAD_SETTINGS = {
    "showLabel":         True,
    "labelPosition":     "bottom-right",
    "blockTelemetry":    True,
    "blockCrashReports": True,
    "blockWebrtc":       True,
    "blockGeolocation":  True,
    "disableSpellcheck": True,
    "hardenTls":         True,
    "cleanUserAgent":    True,
    "blockRemoteAuth":   True,
    "spoofCanvas":       True,
    "spoofAudio":        True,
    "spoofWebgl":        True,
    "stripReferrer":     True,
    "enableRpc":         True,
    "customDnsPrimary":  "",
    "customDnsFallback": "",
    "customUserAgent":   "",
}

DISCORD_APPDATA_DIRS = {
    "DISCORD":       "discord",
    "DISCORDPTB":    "discordptb",
    "DISCORDCANARY": "discordcanary",
    "MANUAL":        "discord",
}


def _get_portable_conf_path():
    try:
        base = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else sys.argv[0]))
        candidate = os.path.join(base, "dcdns_portable.json")
        if os.path.isfile(candidate):
            return candidate
    except Exception:
        pass
    return None


def _load_portable_conf():
    path = _get_portable_conf_path()
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _save_portable_conf(settings):
    path = _get_portable_conf_path()
    if not path:
        return False
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(_normalize_payload_settings(settings), f, indent=2)
        return True
    except OSError:
        return False


def _is_portable_mode():
    return _get_portable_conf_path() is not None


def _normalize_payload_settings(settings):
    conf = dict(DEFAULT_PAYLOAD_SETTINGS)
    if settings:
        for key in DEFAULT_PAYLOAD_SETTINGS:
            if key in settings and settings[key] is not None:
                conf[key] = settings[key]
    return conf


def _build_payload(settings):
    conf = _normalize_payload_settings(settings)
    payload = DCDNS_PAYLOAD
    marker = "var __conf = readConf();"
    if marker not in payload:
        raise RuntimeError("Payload marker not found - cannot bake settings into payload")
    conf_json = json.dumps(conf, separators=(",", ":"))
    baked = "var __conf = Object.assign({}, " + conf_json + ", (function(){var r=readConf();return r&&typeof r==='object'?r:{};}()));"
    result = payload.replace(marker, baked, 1)
    if result.count(marker) > 0 or result.count("var __conf = Object.assign") != 1:
        raise RuntimeError("Payload bake produced unexpected output - aborting")
    return result


def _write_discord_conf(flavor, settings):
    if _is_portable_mode():
        return _save_portable_conf(settings)
    folder = DISCORD_APPDATA_DIRS.get(flavor, "discord")
    roaming = os.getenv("APPDATA", "")
    if not roaming:
        return False
    conf_dir = os.path.join(roaming, folder)
    conf_path = os.path.join(conf_dir, "dcdns_conf.json")
    try:
        os.makedirs(conf_dir, exist_ok=True)
        with open(conf_path, "w", encoding="utf-8") as f:
            json.dump(_normalize_payload_settings(settings), f, indent=2)
        return True
    except OSError:
        return False


class DiscordDetector:
    @staticmethod
    def _make_entry(flavor, path):
        status = DiscordDetector.get_injection_status(path)
        return {
            "flavor": flavor,
            "version": DiscordDetector._get_version(path),
            "path": path,
            "injected": status["injected"],
            "dcdns_version": status["dcdns_version"],
            "up_to_date": status["up_to_date"],
            "chrome_version": DiscordDetector._get_chrome_version(path),
            "sha256": DiscordDetector.hash_file(path),
        }

    @staticmethod
    def find_installations():
        NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        best = {}

        def _mtime(p):
            try:
                return os.path.getmtime(p)
            except Exception:
                return 0

        def consider(path, flavor):
            if not path or not os.path.isfile(path):
                return
            try:
                norm = os.path.normcase(os.path.normpath(path))
            except Exception:
                return
            cur = best.get(flavor)
            if cur is None or _mtime(path) > _mtime(cur["path"]):
                try:
                    best[flavor] = DiscordDetector._make_entry(flavor, path)
                except Exception:
                    pass

        seen_paths = set()

        def dedup_consider(path, flavor):
            if not path:
                return
            try:
                key = os.path.normcase(os.path.normpath(path))
            except Exception:
                return
            if key in seen_paths:
                return
            seen_paths.add(key)
            consider(path, flavor)

        WIN_FLAVORS = [
            ("discord",       "Discord",        "DISCORD"),
            ("discordptb",    "DiscordPTB",     "DISCORDPTB"),
            ("discordcanary", "DiscordCanary",  "DISCORDCANARY"),
        ]

        local       = os.getenv("LOCALAPPDATA", "")
        roaming     = os.getenv("APPDATA", "")
        userprofile = os.getenv("USERPROFILE", os.path.expanduser("~"))
        pf          = os.getenv("ProgramFiles",      r"C:\Program Files")
        pf86        = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")

        def _norm_unique(*paths):
            seen = set()
            out = []
            for p in paths:
                if not p:
                    continue
                n = os.path.normcase(os.path.normpath(p))
                if n not in seen:
                    seen.add(n)
                    out.append(p)
            return out

        roaming_bases = _norm_unique(roaming, os.path.join(userprofile, "AppData", "Roaming"))
        local_bases   = _norm_unique(local,   os.path.join(userprofile, "AppData", "Local"))

        def _glob_consider(pattern, flavor, recursive=False):
            try:
                kwargs = {"recursive": True} if recursive else {}
                for p in glob.glob(pattern, **kwargs):
                    if os.path.isfile(p):
                        dedup_consider(p, flavor)
            except Exception:
                pass

        def _scan_dir_for_index(base, flavor):
            if not base or not os.path.isdir(base):
                return
            globs = [
                os.path.join(base, "app-*",  "modules", "discord_desktop_core-*", "discord_desktop_core", "index.js"),
                os.path.join(base, "app-*",  "modules", "discord_desktop_core",   "index.js"),
                os.path.join(base, "app-*",  "resources", "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "modules", "discord_desktop_core-*", "discord_desktop_core", "index.js"),
                os.path.join(base, "modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "resources", "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
                os.path.join(base, "app.asar.unpacked", "node_modules", "discord_desktop_core", "index.js"),
            ]
            for pat in globs:
                _glob_consider(pat, flavor)
            _glob_consider(os.path.join(base, "**", "discord_desktop_core", "index.js"), flavor, recursive=True)

        def _reg_query(hive, key_path, value_name=""):
            try:
                import winreg
                with winreg.OpenKey(hive, key_path) as k:
                    val, _ = winreg.QueryValueEx(k, value_name)
                    return str(val) if val else None
            except Exception:
                return None

        def _reg_scan_all_flavors():
            import winreg
            reg_map = {
                "DISCORD":       r"Software\Discord",
                "DISCORDPTB":    r"Software\DiscordPTB",
                "DISCORDCANARY": r"Software\DiscordCanary",
            }
            uninstall_roots = [
                r"Software\Microsoft\Windows\CurrentVersion\Uninstall",
                r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
            ]
            hives = [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]

            for flavor, rk in reg_map.items():
                for hive in hives:
                    for val_name in ("", "InstallLocation", "Path", "InstallDir", "DisplayIcon"):
                        val = _reg_query(hive, rk, val_name)
                        if val:
                            p = val.split(",")[0].strip().strip('"')
                            if os.path.exists(p):
                                _scan_dir_for_index(p, flavor)
                                r = DiscordDetector.resolve_index_js(p)
                                if r:
                                    dedup_consider(r, flavor)

            discord_app_ids = {
                "DISCORD":       "{846B0CB7-AA2A-4EAF-887A-3B8A8D18FB31}_is1",
                "DISCORDPTB":    "{F3A3F8FF-E1DC-42DB-AADF-F0D1EFFC1337}_is1",
                "DISCORDCANARY": "{3B70B640-C4C1-4FA4-A21B-E3A7A0A0B2F5}_is1",
            }
            for flavor, app_id in discord_app_ids.items():
                for hive in hives:
                    for root in uninstall_roots:
                        key_path = root + "\\" + app_id
                        for val_name in ("InstallLocation", "DisplayIcon", ""):
                            val = _reg_query(hive, key_path, val_name)
                            if val:
                                p = val.split(",")[0].strip().strip('"')
                                if os.path.exists(p):
                                    _scan_dir_for_index(p, flavor)
                                    r = DiscordDetector.resolve_index_js(p)
                                    if r:
                                        dedup_consider(r, flavor)

        def _get_running_discord_exe_paths():
            paths = []
            methods = [
                {
                    "cmd": ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command",
                            "Get-Process -ErrorAction SilentlyContinue | "
                            "Where-Object { $_.ProcessName -match '(?i)^discord' } | "
                            "Select-Object -ExpandProperty Path"],
                    "timeout": 12,
                },
                {
                    "cmd": ["wmic", "process", "where",
                            "name like 'Discord%'",
                            "get", "ExecutablePath", "/format:csv"],
                    "timeout": 8,
                },
            ]
            for m in methods:
                try:
                    r = subprocess.run(
                        m["cmd"], capture_output=True, text=True,
                        timeout=m["timeout"], creationflags=NO_WINDOW,
                    )
                    for line in r.stdout.splitlines():
                        line = line.strip()
                        if not line:
                            continue
                        if "," in line:
                            line = line.split(",")[-1].strip()
                        if line.lower().endswith(".exe") and os.path.isfile(line):
                            paths.append(line)
                except Exception:
                    pass
                if paths:
                    break

            if not paths:
                try:
                    import ctypes
                    import ctypes.wintypes
                    TH32CS_SNAPPROCESS = 0x00000002
                    class PROCESSENTRY32(ctypes.Structure):
                        _fields_ = [
                            ("dwSize",              ctypes.c_ulong),
                            ("cntUsage",            ctypes.c_ulong),
                            ("th32ProcessID",       ctypes.c_ulong),
                            ("th32DefaultHeapID",   ctypes.POINTER(ctypes.c_ulong)),
                            ("th32ModuleID",        ctypes.c_ulong),
                            ("cntThreads",          ctypes.c_ulong),
                            ("th32ParentProcessID", ctypes.c_ulong),
                            ("pcPriClassBase",      ctypes.c_long),
                            ("dwFlags",             ctypes.c_ulong),
                            ("szExeFile",           ctypes.c_char * 260),
                        ]
                    snap = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
                    if snap and snap != ctypes.wintypes.HANDLE(-1).value:
                        entry = PROCESSENTRY32()
                        entry.dwSize = ctypes.sizeof(PROCESSENTRY32)
                        discord_pids = []
                        if ctypes.windll.kernel32.Process32First(snap, ctypes.byref(entry)):
                            while True:
                                name = entry.szExeFile.decode("utf-8", errors="ignore").lower()
                                if name.startswith("discord") and name.endswith(".exe"):
                                    discord_pids.append(entry.th32ProcessID)
                                if not ctypes.windll.kernel32.Process32Next(snap, ctypes.byref(entry)):
                                    break
                        ctypes.windll.kernel32.CloseHandle(snap)
                        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
                        MAX_PATH = 32768
                        for pid in discord_pids:
                            try:
                                h = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
                                if h and h != ctypes.wintypes.HANDLE(-1).value:
                                    buf = ctypes.create_unicode_buffer(MAX_PATH)
                                    size = ctypes.c_ulong(MAX_PATH)
                                    if ctypes.windll.kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
                                        p = buf.value
                                        if p and os.path.isfile(p):
                                            paths.append(p)
                                    ctypes.windll.kernel32.CloseHandle(h)
                            except Exception:
                                pass
                except Exception:
                    pass

            return list(dict.fromkeys(paths))

        for lower, title, flavor in WIN_FLAVORS:
            for base in roaming_bases:
                for name_var in _norm_unique(lower, title, lower.capitalize()):
                    d = os.path.join(base, name_var)
                    _scan_dir_for_index(d, flavor)
            for base in local_bases:
                for name_var in _norm_unique(lower, title, lower.capitalize()):
                    d = os.path.join(base, name_var)
                    _scan_dir_for_index(d, flavor)
                    if os.path.isdir(d):
                        try:
                            for sub in os.listdir(d):
                                sd = os.path.join(d, sub)
                                if os.path.isdir(sd):
                                    _scan_dir_for_index(sd, flavor)
                        except OSError:
                            pass
            for prog in _norm_unique(pf, pf86):
                for name_var in _norm_unique(title, lower, lower.capitalize()):
                    _scan_dir_for_index(os.path.join(prog, name_var), flavor)

        try:
            _reg_scan_all_flavors()
        except Exception:
            pass

        for exe_path in _get_running_discord_exe_paths():
            flavor = DiscordDetector.guess_flavor(exe_path)
            if flavor == "MANUAL":
                continue
            exe_dir = os.path.dirname(exe_path)
            for d in _norm_unique(exe_dir, os.path.dirname(exe_dir)):
                _scan_dir_for_index(d, flavor)
                r = DiscordDetector.resolve_index_js(d)
                if r:
                    dedup_consider(r, flavor)

        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for base_key in (
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\Discord.exe",
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\DiscordPTB.exe",
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\DiscordCanary.exe",
                ):
                    val = _reg_query(hive, base_key, "")
                    if val:
                        p = val.strip().strip('"')
                        if os.path.isfile(p):
                            fl = DiscordDetector.guess_flavor(p)
                            if fl != "MANUAL":
                                d = os.path.dirname(p)
                                _scan_dir_for_index(d, fl)
                                _scan_dir_for_index(os.path.dirname(d), fl)
        except Exception:
            pass

        results = []
        for flavor in FLAVORS:
            cand = best.get(flavor)
            if cand:
                results.append(cand)
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
            if re.match(r"^\d+\.\d+\.\d+$", part):
                return part
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
        if not content:
            return content
        passes = 0
        while PAYLOAD_MARKER in content and passes < 4:
            start = content.find(PAYLOAD_MARKER)
            if start == -1:
                break
            end = content.find(FOOTER_TAG, start)
            if end == -1:
                before = content[:start].rstrip("\r\n")
                content = before if before else ""
                break
            end += len(FOOTER_TAG)
            before = content[:start].rstrip("\r\n")
            after  = content[end:].lstrip("\r\n")
            if before and after:
                content = before + "\n" + after
            elif after:
                content = after
            elif before:
                content = before
            else:
                content = ""
            passes += 1
        return content

    @staticmethod
    def strip_payload_safe(content):
        stripped = DiscordDetector.strip_payload(content)
        if stripped is None:
            return None, "Strip produced None"
        if PAYLOAD_MARKER in stripped:
            return None, "Payload marker still present after strip - possible corruption"
        return stripped, "OK"

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
    def _is_pid_alive(pid):
        import ctypes
        import ctypes.wintypes
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        SYNCHRONIZE = 0x00100000
        STILL_ACTIVE = 259
        try:
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE, False, pid
            )
            if not handle or handle == ctypes.wintypes.HANDLE(-1).value:
                return False
            exit_code = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            if not ok:
                return False
            if exit_code.value != STILL_ACTIVE:
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def is_valid_discord_target(path):
        if not path or not os.path.isfile(path):
            return False, "File does not exist"
        try:
            size = os.path.getsize(path)
        except OSError as e:
            return False, "Cannot stat file: " + str(e)
        if size == 0:
            return False, "File is empty"
        if size < 512:
            return False, "File is too small to be a valid index.js (" + str(size) + " bytes)"
        norm = path.replace("\\", "/").lower()
        if "discord" not in norm:
            return False, "Path does not contain 'discord' - not a Discord installation"
        if not norm.endswith("index.js"):
            return False, "Target must be index.js"
        if "discord_desktop_core" not in norm and "app.asar.unpacked" not in norm:
            return False, "Path does not look like a Discord core module"
        try:
            with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
                head = f.read(4096)
        except OSError as e:
            return False, "Cannot read file: " + str(e)
        if PAYLOAD_MARKER in head:
            return True, "OK"
        discord_signatures = [
            "require(",
            "module.exports",
            "electron",
            "discord",
        ]
        matched = sum(1 for sig in discord_signatures if sig.lower() in head.lower())
        if matched < 2:
            try:
                with open(path, "r", encoding="utf-8", errors="surrogateescape") as f:
                    full = f.read(65536)
                matched = sum(1 for sig in discord_signatures if sig.lower() in full.lower())
            except Exception:
                pass
        if matched < 2:
            return False, "File content does not look like a Discord Electron module"
        return True, "OK"

    @staticmethod
    def _get_pids_by_names(names):
        NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
        collected = {}
        for name in names:
            exe = name if name.lower().endswith(".exe") else name + ".exe"
            exe_lower = exe.lower()
            found = []
            try:
                ps_cmd = (
                    "$name='" + exe + "';"
                    "Get-Process -ErrorAction SilentlyContinue"
                    " | Where-Object {$_.ProcessName -eq [System.IO.Path]::GetFileNameWithoutExtension($name)}"
                    " | Select-Object -ExpandProperty Id"
                )
                result = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive",
                     "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=10,
                    creationflags=NO_WINDOW,
                )
                for line in result.stdout.splitlines():
                    line = line.strip()
                    if line.isdigit():
                        found.append(int(line))
            except Exception:
                pass
            if not found:
                try:
                    result = subprocess.run(
                        ["wmic", "process", "where", "name='" + exe + "'", "get", "ProcessId"],
                        capture_output=True, text=True, timeout=8,
                        creationflags=NO_WINDOW,
                    )
                    for line in result.stdout.splitlines():
                        line = line.strip()
                        if line.isdigit() and line != "0":
                            found.append(int(line))
                except Exception:
                    pass
            for pid in found:
                if pid not in collected:
                    collected[pid] = exe
        alive = []
        for pid, exe in collected.items():
            if DiscordDetector._is_pid_alive(pid):
                alive.append((pid, exe))
        return alive

    @staticmethod
    def kill_processes(names, log_fn=None):
        NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0

        def _log(msg):
            if log_fn:
                log_fn(msg)

        import ctypes
        import ctypes.wintypes

        PROCESS_TERMINATE             = 0x0001
        PROCESS_QUERY_LIMITED_INFO    = 0x1000
        SYNCHRONIZE                   = 0x00100000
        STILL_ACTIVE                  = 259
        INVALID_HANDLE                = ctypes.wintypes.HANDLE(-1).value
        WM_CLOSE                      = 0x0010
        WM_QUIT                       = 0x0012
        CTRL_CLOSE_EVENT              = 2

        EnumWindowsProc = ctypes.WINFUNCTYPE(
            ctypes.c_bool,
            ctypes.POINTER(ctypes.c_int),
            ctypes.POINTER(ctypes.c_int),
        )

        def _open_proc(pid, access):
            h = ctypes.windll.kernel32.OpenProcess(access, False, pid)
            if h and h != INVALID_HANDLE:
                return h
            return None

        def _close_h(h):
            try:
                if h and h != INVALID_HANDLE:
                    ctypes.windll.kernel32.CloseHandle(h)
            except Exception:
                pass

        def _alive(pid):
            h = _open_proc(pid, PROCESS_QUERY_LIMITED_INFO | SYNCHRONIZE)
            if not h:
                return False
            ec = ctypes.c_ulong(0)
            ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(ec))
            _close_h(h)
            return bool(ok) and ec.value == STILL_ACTIVE

        def _wait_dead(pid, ms):
            h = _open_proc(pid, SYNCHRONIZE)
            if not h:
                return True
            ret = ctypes.windll.kernel32.WaitForSingleObject(h, ms)
            _close_h(h)
            return ret == 0 or not _alive(pid)

        def _send_close_messages(pid):
            target_pid = ctypes.c_ulong(pid)
            def _cb(hwnd, _):
                try:
                    owner = ctypes.c_ulong(0)
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(owner))
                    if owner.value == target_pid.value:
                        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
                        ctypes.windll.user32.PostMessageW(hwnd, WM_QUIT,  0, 0)
                except Exception:
                    pass
                return True
            try:
                ctypes.windll.user32.EnumWindows(EnumWindowsProc(_cb), None)
            except Exception:
                pass

        def _try_terminate_via_ctypes(pid):
            h = _open_proc(pid, PROCESS_TERMINATE | SYNCHRONIZE)
            if not h:
                return False
            try:
                ok = ctypes.windll.kernel32.TerminateProcess(h, 1)
                if ok:
                    ctypes.windll.kernel32.WaitForSingleObject(h, 3000)
                    return not _alive(pid)
            except Exception:
                pass
            finally:
                _close_h(h)
            return False

        def _try_taskkill(pid, exe):
            try:
                r = subprocess.run(
                    ["taskkill", "/F", "/PID", str(pid)],
                    capture_output=True, text=True, timeout=8, creationflags=NO_WINDOW,
                )
                return r.returncode == 0
            except Exception:
                return False

        def _try_powershell_stop(pid):
            try:
                r = subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive",
                     "-ExecutionPolicy", "Bypass", "-Command",
                     "Stop-Process -Id " + str(pid) + " -Force -ErrorAction SilentlyContinue"],
                    capture_output=True, text=True, timeout=10, creationflags=NO_WINDOW,
                )
                time.sleep(0.5)
                return not _alive(pid)
            except Exception:
                return False

        pids = DiscordDetector._get_pids_by_names(names)
        if not pids:
            return 0

        killed = 0
        for pid, exe in pids:
            if not _alive(pid):
                killed += 1
                continue

            _log("[~] Closing " + exe + " (PID " + str(pid) + ")...")

            _send_close_messages(pid)
            if _wait_dead(pid, 2500):
                _log("[+] Closed " + exe + " (PID " + str(pid) + ")")
                killed += 1
                continue

            if not _alive(pid):
                _log("[+] Closed " + exe + " (PID " + str(pid) + ")")
                killed += 1
                continue

            _log("[~] Terminating " + exe + " (PID " + str(pid) + ")...")

            if _try_terminate_via_ctypes(pid):
                _log("[+] Terminated " + exe + " (PID " + str(pid) + ")")
                killed += 1
                continue

            if _try_taskkill(pid, exe) and not _alive(pid):
                _log("[+] Force-killed " + exe + " (PID " + str(pid) + ")")
                killed += 1
                continue

            if _try_powershell_stop(pid):
                _log("[+] Stopped " + exe + " (PID " + str(pid) + ")")
                killed += 1
                continue

            if not _alive(pid):
                _log("[+] " + exe + " (PID " + str(pid) + ") exited on its own.")
                killed += 1
            else:
                _log("[!] Could not stop " + exe + " (PID " + str(pid) + ") - may need to be closed manually.")

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
                return proc.pid
            direct_exe = DiscordDetector._find_upwards(target_path, exe_name)
            if direct_exe:
                proc = subprocess.Popen([direct_exe], cwd=os.path.dirname(direct_exe))
                DiscordDetector._detach(proc)
                return proc.pid
            return None
        except Exception:
            return None


class Api:
    def __init__(self):
        self.window        = None
        self.installations = []
        self._queue        = queue.Queue()
        self._running      = True
        self._js_lock      = threading.Lock()
        self._op_lock      = threading.Lock()
        self._pending_install = None
        self._thread = threading.Thread(target=self._process_queue, daemon=True)
        self._thread.start()
        self._rpc = _get_rpc()
        settings = self._load_settings_sync()
        if settings.get("enableRpc", True):
            self._rpc.start()

    def _load_settings_sync(self):
        try:
            portable = _load_portable_conf()
            if portable:
                return portable
            roaming = os.getenv("APPDATA", "")
            if roaming:
                for folder in DISCORD_APPDATA_DIRS.values():
                    conf_path = os.path.join(roaming, folder, "dcdns_conf.json")
                    if os.path.isfile(conf_path):
                        try:
                            with open(conf_path, "r", encoding="utf-8") as f:
                                data = json.load(f)
                            if isinstance(data, dict):
                                return data
                        except Exception:
                            continue
        except Exception:
            pass
        return {}

    def set_window(self, window):
        self.window = window

    def _safe_js(self, js_code):
        if self._running and self.window:
            self._queue.put(js_code)

    def _process_queue(self):
        while self._running:
            try:
                js = self._queue.get(timeout=0.1)
            except queue.Empty:
                continue
            with self._js_lock:
                if not self.window or not self._running:
                    continue
                try:
                    self.window.evaluate_js(js)
                except Exception:
                    pass
        while True:
            try:
                js = self._queue.get_nowait()
            except queue.Empty:
                break
            with self._js_lock:
                if not self.window or not self._running:
                    break
                try:
                    self.window.evaluate_js(js)
                except Exception:
                    pass

    def _log(self, msg):
        safe = (str(msg)
                .replace("\\", "\\\\")
                .replace("`", "\\`")
                .replace("${", "\\${")
                .replace("\r\n", " ")
                .replace("\r", " ")
                .replace("\n", " "))
        self._safe_js("try{addLog(`" + safe + "`)}catch(e){}")

    def _finish(self, ok):
        self._safe_js("try{finishLog(" + ("true" if ok else "false") + ")}catch(e){}")

    @staticmethod
    def _discord_is_present():
        local = os.getenv("LOCALAPPDATA", "")
        roaming = os.getenv("APPDATA", "")
        pf = os.getenv("ProgramFiles", r"C:\Program Files")
        pf86 = os.getenv("ProgramFiles(x86)", r"C:\Program Files (x86)")
        check_names = ["Discord", "discord", "DiscordPTB", "discordptb", "DiscordCanary", "discordcanary"]
        for base in [local, roaming, pf, pf86]:
            if not base:
                continue
            for name in check_names:
                if os.path.isdir(os.path.join(base, name)):
                    return True
        try:
            import winreg
            for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
                for key in (
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\Discord.exe",
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\DiscordPTB.exe",
                    r"Software\Microsoft\Windows\CurrentVersion\App Paths\DiscordCanary.exe",
                ):
                    try:
                        with winreg.OpenKey(hive, key) as k:
                            val, _ = winreg.QueryValueEx(k, "")
                            if val and os.path.isfile(str(val).strip().strip('"')):
                                return True
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            NO_WINDOW = subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            r = subprocess.run(
                ["where", "Discord.exe"],
                capture_output=True, text=True, timeout=4, creationflags=NO_WINDOW,
            )
            if r.returncode == 0 and r.stdout.strip():
                return True
        except Exception:
            pass
        return False

    def discord_exists(self):
        try:
            return json.dumps({"exists": self._discord_is_present()})
        except Exception:
            return json.dumps({"exists": False})

    def scan_discord(self):
        try:
            if not self._discord_is_present():
                self.installations = []
                return json.dumps([])
            installs = DiscordDetector.find_installations()
            for inst in installs:
                try:
                    p = inst.get("path", "")
                    if p and os.path.isfile(p):
                        age_days = (time.time() - os.path.getmtime(p)) / 86400
                        inst["stale"] = age_days > 60
                        inst["age_days"] = int(age_days)
                    else:
                        inst["stale"] = False
                        inst["age_days"] = 0
                except Exception:
                    inst["stale"] = False
                    inst["age_days"] = 0
            self.installations = installs
            return json.dumps(installs)
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
            flavor     = DiscordDetector.guess_flavor(resolved)
            version    = DiscordDetector._get_version(resolved)
            status     = DiscordDetector.get_injection_status(resolved)
            chrome_ver = DiscordDetector._get_chrome_version(resolved)
            sha256     = DiscordDetector.hash_file(resolved)
            return json.dumps({
                "flavor": flavor, "version": version, "path": resolved,
                "injected": status["injected"], "dcdns_version": status["dcdns_version"],
                "up_to_date": status["up_to_date"], "chrome_version": chrome_ver, "sha256": sha256,
            })
        except Exception as ex:
            return json.dumps({"error": str(ex)})

    def get_mode(self):
        return json.dumps({
            "portable": _is_portable_mode(),
            "portable_path": _get_portable_conf_path() or "",
        })

    def get_rpc_status(self):
        return json.dumps({"active": self._rpc.is_active()})

    def apply_rpc_setting(self, enabled):
        try:
            if enabled:
                self._rpc.start()
            else:
                self._rpc.stop()
        except Exception:
            pass

    def load_settings(self):
        try:
            data = self._load_settings_sync()
            if data:
                return json.dumps(data)
        except Exception:
            pass
        return json.dumps({})

    def save_settings(self, settings_json):
        try:
            settings = json.loads(settings_json)
            if _is_portable_mode():
                _save_portable_conf(settings)
                return
            roaming = os.getenv("APPDATA", "")
            if not roaming:
                return
            normalized = _normalize_payload_settings(settings)
            for folder in DISCORD_APPDATA_DIRS.values():
                conf_dir = os.path.join(roaming, folder)
                if os.path.isdir(conf_dir):
                    try:
                        conf_path = os.path.join(conf_dir, "dcdns_conf.json")
                        with open(conf_path, "w", encoding="utf-8") as f:
                            json.dump(normalized, f, indent=2)
                    except OSError:
                        pass
        except Exception:
            pass

    def open_discord(self):
        try:
            open_discord_invite()
        except Exception:
            pass

    def open_website(self):
        try:
            open_website()
        except Exception:
            pass

    def close_app(self):
        try:
            self._running = False
            self._rpc.stop()
            win = self.window
            self.window = None
            if win:
                try:
                    win.destroy()
                except Exception:
                    pass
        except Exception:
            pass

    def install(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
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
            return "ask_backup"
        threading.Thread(target=self._run_install, args=(inst, False), daemon=True).start()
        return "ok"

    def install_confirm_backup(self, choice):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        inst = self._pending_install
        self._pending_install = None
        if not inst:
            self._op_lock.release()
            return "invalid"
        overwrite = choice == "overwrite"
        threading.Thread(target=self._run_install, args=(inst, overwrite), daemon=True).start()
        return "ok"

    def uninstall(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            inst = json.loads(inst_json)
        except Exception:
            self._op_lock.release()
            return "invalid"
        threading.Thread(target=self._run_uninstall, args=(inst,), daemon=True).start()
        return "ok"

    def restart_discord(self, inst_json):
        if not self._op_lock.acquire(blocking=False):
            return "busy"
        try:
            inst = json.loads(inst_json)
        except Exception:
            self._op_lock.release()
            return "invalid"
        threading.Thread(target=self._run_restart, args=(inst,), daemon=True).start()
        return "ok"

    def _run_install(self, inst, overwrite_backup):
        try:
            self._do_install(inst, overwrite_backup)
        finally:
            try:
                self._op_lock.release()
            except RuntimeError:
                pass

    def _do_install(self, inst, overwrite_backup):
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
            valid, reason = DiscordDetector.is_valid_discord_target(target)
            if not valid:
                self._log("[X] Tamper / sanity check failed: " + reason)
                self._finish(False); return
            self._log("[+] Target validated: " + os.path.basename(target))

            self._log("[2/7] Closing running Discord processes...")
            names  = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            killed = DiscordDetector.kill_processes(names, log_fn=self._log)
            if killed:
                self._log("[+] Closed " + str(killed) + " process(es) total.")
                time.sleep(1.5)
            else:
                self._log("[!] No running process detected.")

            self._log("[3/7] Reading target file...")
            content = DiscordDetector.read_text(target)

            self._log("[4/7] Checking for existing payload...")
            if PAYLOAD_MARKER in content:
                injected_ver = DiscordDetector.get_injected_version(target)
                if injected_ver and DiscordDetector._version_key(injected_ver) >= DiscordDetector._version_key(APP_VERSION):
                    self._log("[!] DcDNS v" + injected_ver + " already installed and up to date - reinstalling anyway...")
                elif injected_ver:
                    self._log("[!] Outdated DcDNS v" + injected_ver + " detected - upgrading to v" + APP_VERSION + "...")
                else:
                    self._log("[!] Existing DcDNS payload detected - replacing...")

                bak_try = target + ".dcdns.bak"
                clean_content = None

                if os.path.isfile(bak_try):
                    try:
                        bak_content = DiscordDetector.read_text(bak_try)
                        if PAYLOAD_MARKER not in bak_content and bak_content.strip():
                            clean_content = bak_content
                            self._log("[+] Using backup as clean base.")
                        elif PAYLOAD_MARKER in bak_content:
                            self._log("[!] Backup is also injected - attempting to strip backup...")
                            stripped_bak, strip_bak_reason = DiscordDetector.strip_payload_safe(bak_content)
                            if stripped_bak is not None:
                                clean_content = stripped_bak
                                self._log("[+] Backup stripped successfully - using as clean base.")
                            else:
                                self._log("[!] Could not strip backup (" + strip_bak_reason + ") - will strip from live file.")
                        else:
                            self._log("[!] Backup appears invalid - will strip from file directly.")
                    except Exception as bak_ex:
                        self._log("[!] Could not read backup: " + str(bak_ex))

                if clean_content is None:
                    stripped, strip_reason = DiscordDetector.strip_payload_safe(content)
                    if stripped is not None:
                        clean_content = stripped
                        self._log("[+] Payload stripped from live file successfully.")
                    else:
                        self._log("[X] Strip failed: " + strip_reason)
                        self._log("[X] No clean source available - aborting to protect your installation.")
                        self._finish(False); return

                content = clean_content
                if PAYLOAD_MARKER in content:
                    self._log("[X] Payload marker still present after cleanup - aborting.")
                    self._finish(False); return
                self._log("[+] Base file is clean - ready for injection.")

            self._log("[5/7] Creating backup...")
            bak_sha_file = backup + ".sha256"
            if os.path.exists(backup):
                if overwrite_backup:
                    shutil.copyfile(target, backup)
                    bak_sha = DiscordDetector.hash_file(backup)
                    try:
                        with open(bak_sha_file, "w", encoding="utf-8") as f:
                            f.write(bak_sha)
                    except OSError:
                        pass
                    self._log("[+] Backup overwritten: " + os.path.basename(backup))
                    if bak_sha:
                        self._log("[+] Backup SHA-256: " + bak_sha)
                else:
                    self._log("[!] Keeping existing backup.")
            else:
                shutil.copyfile(target, backup)
                bak_sha = DiscordDetector.hash_file(backup)
                try:
                    with open(bak_sha_file, "w", encoding="utf-8") as f:
                        f.write(bak_sha)
                except OSError:
                    pass
                self._log("[+] Backup created: " + os.path.basename(backup))
                if bak_sha:
                    self._log("[+] Backup SHA-256: " + bak_sha)

            self._log("[5b/7] Writing config to Discord AppData...")
            if _write_discord_conf(flavor, settings):
                self._log("[+] Config written to Discord AppData.")
            else:
                self._log("[!] Could not write config file - payload will use baked defaults.")

            self._log("[6/7] Injecting DcDNS payload...")
            payload     = _build_payload(settings)
            new_content = payload + content
            for attempt in range(5):
                try:
                    DiscordDetector.write_text(target, new_content)
                    break
                except (PermissionError, OSError) as lock_err:
                    if attempt < 4:
                        self._log("[!] File locked, retrying in 1s... (" + str(attempt + 1) + "/5)")
                        time.sleep(1)
                    else:
                        raise lock_err

            self._log("[7/7] Verifying injection...")
            if DiscordDetector._is_injected(target):
                self._log("[+] Payload verified in file.")
            else:
                self._log("[X] Verification failed - payload not found after write.")
                self._finish(False); return

            sha256 = DiscordDetector.hash_file(target)
            if sha256:
                self._log("[+] SHA-256: " + sha256)

            self._log("[+] Launching Discord...")
            launched_pid = DiscordDetector.launch_client(target, flavor)
            if launched_pid:
                self._log("[+] Discord launched (launcher PID " + str(launched_pid) + ").")
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
        try:
            self._do_uninstall(inst)
        finally:
            try:
                self._op_lock.release()
            except RuntimeError:
                pass

    def _do_uninstall(self, inst):
        target = inst.get("path", "")
        flavor = inst.get("flavor", "DISCORD")
        backup = target + ".dcdns.bak"
        self._log("=" * 40)
        self._log("UNINSTALL -> " + flavor)
        self._log("=" * 40)
        try:
            self._log("[1/6] Closing running Discord processes...")
            names  = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            killed = DiscordDetector.kill_processes(names, log_fn=self._log)
            if killed:
                self._log("[+] Closed " + str(killed) + " process(es) total.")
                time.sleep(1.0)
            else:
                self._log("[!] No running process detected.")

            self._log("[2/6] Looking for backup...")
            bak_sha_file = backup + ".sha256"
            if os.path.exists(backup):
                self._log("[2b/6] Verifying backup integrity...")
                expected_sha = ""
                try:
                    with open(bak_sha_file, "r", encoding="utf-8") as f:
                        expected_sha = f.read().strip()
                except OSError:
                    pass
                if expected_sha:
                    actual_sha = DiscordDetector.hash_file(backup)
                    if actual_sha and actual_sha != expected_sha:
                        self._log("[!] WARNING: Backup file SHA-256 mismatch!")
                        self._log("[!] Expected: " + expected_sha)
                        self._log("[!] Got:      " + actual_sha)
                        self._log("[!] Backup may have been modified by another program.")
                        self._log("[!] Aborting restore to protect your installation.")
                        self._finish(False)
                        return
                    else:
                        self._log("[+] Backup integrity verified.")
                else:
                    self._log("[!] No SHA record found - skipping integrity check.")
                self._log("[3/6] Restoring from backup...")
                shutil.copyfile(backup, target)
                self._log("[+] File restored.")
                try:
                    os.remove(backup)
                    self._log("[+] Backup removed.")
                except Exception as rem_ex:
                    self._log("[!] Could not remove backup: " + str(rem_ex))
                try:
                    if os.path.exists(bak_sha_file):
                        os.remove(bak_sha_file)
                except OSError:
                    pass
            else:
                self._log("[!] No backup - stripping payload manually...")
                if not os.path.isfile(target):
                    self._log("[X] Target file not found.")
                    self._finish(False); return
                valid, reason = DiscordDetector.is_valid_discord_target(target)
                if not valid:
                    self._log("[X] Tamper / sanity check failed: " + reason)
                    self._finish(False); return
                content = DiscordDetector.read_text(target)
                if PAYLOAD_MARKER in content:
                    cleaned, strip_reason = DiscordDetector.strip_payload_safe(content)
                    if cleaned is None:
                        self._log("[X] Strip failed: " + strip_reason)
                        self._finish(False); return
                    if PAYLOAD_MARKER in cleaned:
                        self._log("[X] Payload marker still present after strip - aborting.")
                        self._finish(False); return
                    for attempt in range(5):
                        try:
                            DiscordDetector.write_text(target, cleaned)
                            break
                        except (PermissionError, OSError) as lock_err:
                            if attempt < 4:
                                self._log("[!] File locked, retrying in 1s... (" + str(attempt + 1) + "/5)")
                                time.sleep(1)
                            else:
                                raise lock_err
                    self._log("[+] Payload stripped.")
                else:
                    self._log("[!] No DcDNS payload found in file.")

            self._log("[4/6] Verifying...")
            if not DiscordDetector._is_injected(target):
                self._log("[5/6] Launching Discord...")
                launched_pid = DiscordDetector.launch_client(target, flavor)
                if launched_pid:
                    self._log("[+] Discord launched (launcher PID " + str(launched_pid) + ").")
                else:
                    self._log("[!] Could not auto-launch. Start Discord manually.")
                self._log("[6/6] Done.")
                self._log("=" * 40)
                self._log("UNINSTALL COMPLETE!")
                self._log("=" * 40)
                self._finish(True)
            else:
                self._log("[X] Header still present after strip - manual cleanup needed.")
                self._finish(False)
        except PermissionError:
            self._log("[X] Permission denied. Run as Administrator.")
            self._finish(False)
        except Exception as ex:
            self._log("[X] FATAL: " + str(ex))
            self._finish(False)

    def _run_restart(self, inst):
        try:
            self._do_restart(inst)
        finally:
            try:
                self._op_lock.release()
            except RuntimeError:
                pass

    def _do_restart(self, inst):
        target = inst.get("path", "")
        flavor = inst.get("flavor", "DISCORD")
        self._log("=" * 40)
        self._log("RESTART -> " + flavor)
        self._log("=" * 40)
        try:
            names = PROCESS_NAMES.get(flavor, PROCESS_NAMES["DISCORD"])
            self._log("[1/3] Closing running instances...")
            killed = DiscordDetector.kill_processes(names, log_fn=self._log)
            if killed:
                self._log("[+] Closed " + str(killed) + " process(es) total.")
            else:
                self._log("[!] No running process detected (already closed).")
            time.sleep(1.5)
            self._log("[2/3] Launching client...")
            launched_pid = None
            if target and os.path.isfile(target):
                launched_pid = DiscordDetector.launch_client(target, flavor)
            if launched_pid:
                self._log("[+] Discord launched (launcher PID " + str(launched_pid) + ").")
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


def _open_url_bg(url):
    try:
        os.startfile(url)
        return
    except Exception:
        pass
    try:
        subprocess.Popen(
            ["rundll32", "url.dll,FileProtocolHandler", url],
            shell=False,
        )
        return
    except Exception:
        pass
    try:
        webbrowser.open(url, new=2)
    except Exception:
        pass


def open_discord_invite():
    threading.Thread(target=_open_url_bg, args=(DISCORD_INVITE_URL,), daemon=True).start()


def open_website():
    threading.Thread(target=_open_url_bg, args=(WEBSITE_URL,), daemon=True).start()


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
