/**
 * MyTab —— Firefox 新标签页后台。
 *
 * 1) 新标签页接管：manifest.json 用 chrome_url_overrides.newtab 声明，
 *    Firefox 自己把 about:newtab 指向扩展内置的 index.html（Firefox 54+ 支持）。
 *    这里不再监听 tabs.onCreated / tabs.onUpdated 做重定向 —— 那种做法会让
 *    浏览器先闪一下默认新标签页再跳走，而且需要额外的 "tabs" 权限。
 * 2) 网站图标抓取：可选主机权限（optional_host_permissions）拿到授权后，
 *    读取目标网页 HTML，解析 <link rel="icon"> 找到真实图标地址并转成 dataURL 返回给页面缓存。
 * 3) 无痕窗口打开、收藏到书签。
 */
(function () {
  'use strict';

  /* ---------- 1. 新标签页接管 ---------- */
  /* chrome_url_overrides.newtab 已在 manifest.json 中声明，这里无需任何代码。
   * 需要在扩展里打开设置页时，用 browser.runtime.getURL('index.html') 即可。 */

  /* ---------- 2. 网站图标抓取 ---------- */
  var iconCache = new Map();

  function arrayBufferToBase64(buffer) {
    var bytes = new Uint8Array(buffer);
    var binary = '';
    var chunk = 0x8000;
    for (var i = 0; i < bytes.length; i += chunk) {
      binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(binary);
  }

  function guessMime(url) {
    if (/\.svg(\?|#|$)/i.test(url)) return 'image/svg+xml';
    if (/\.png(\?|#|$)/i.test(url)) return 'image/png';
    if (/\.gif(\?|#|$)/i.test(url)) return 'image/gif';
    if (/\.webp(\?|#|$)/i.test(url)) return 'image/webp';
    if (/\.jpe?g(\?|#|$)/i.test(url)) return 'image/jpeg';
    return 'image/x-icon';
  }

  function fetchWithTimeout(url, ms) {
    return new Promise(function (resolve, reject) {
      var timer = setTimeout(function () { reject(new Error('timeout')); }, ms);
      fetch(url, { credentials: 'omit' }).then(function (res) {
        clearTimeout(timer);
        resolve(res);
      }, function (err) {
        clearTimeout(timer);
        reject(err);
      });
    });
  }

  /* 解析网页里的图标链接：<link rel="icon|shortcut icon|apple-touch-icon"> */
  function parseIconLinks(html, base) {
    var out = [];
    var seen = {};
    var re = /<link\b[^>]*>/gi;
    var m;
    while ((m = re.exec(html)) && out.length < 10) {
      var tag = m[0];
      var relMatch = /rel\s*=\s*["']([^"']+)["']/i.exec(tag);
      if (!relMatch) continue;
      var rel = relMatch[1].toLowerCase();
      if (rel.indexOf('icon') === -1) continue;
      var hrefMatch = /href\s*=\s*["']([^"']+)["']/i.exec(tag);
      if (!hrefMatch) continue;
      try {
        var abs = new URL(hrefMatch[1], base).href;
        if (seen[abs]) continue;
        seen[abs] = true;
        out.push(abs);
      } catch (e) { /* 忽略非法 href */ }
    }
    return out;
  }

  /* 抓图标需要主机权限（manifest 里是 optional_host_permissions，按需申请）。
   * 没授权就直接返回 null，让页面走 <img> 直连 /favicon.ico 的回退路径。 */
  function hasHostPermission(pageUrl) {
    try {
      var u = new URL(pageUrl);
      var pattern = '*://' + u.host + '/*';
      return browser.permissions.contains({ origins: [pattern] }).then(function (ok) {
        return !!ok;
      }).catch(function () { return false; });
    } catch (e) { return Promise.resolve(false); }
  }

  async function loadIcon(pageUrl) {
    var allowed = await hasHostPermission(pageUrl);
    if (!allowed) return null;

    var base = pageUrl;
    var candidates = [];
    try {
      var res = await fetchWithTimeout(pageUrl, 7000);
      if (res.ok) {
        base = res.url || pageUrl;
        var html = await res.text();
        if (html && html.length < 500000) {
          candidates = parseIconLinks(html, base);
        }
      }
    } catch (e) { /* 页面取不到也继续尝试常见路径 */ }
    try {
      var u = new URL(pageUrl);
      candidates.push(u.origin + '/favicon.ico');
      candidates.push(u.origin + '/favicon.png');
      candidates.push(u.origin + '/apple-touch-icon.png');
    } catch (e2) { return null; }

    for (var i = 0; i < candidates.length; i++) {
      try {
        var r = await fetchWithTimeout(candidates[i], 6000);
        if (!r.ok) continue;
        var buf = await r.arrayBuffer();
        if (!buf || buf.byteLength < 32 || buf.byteLength > 300000) continue;
        var mime = (r.headers.get('content-type') || '').split(';')[0].trim();
        if (!/^image\//i.test(mime)) mime = guessMime(candidates[i]);
        return 'data:' + mime + ';base64,' + arrayBufferToBase64(buf);
      } catch (e3) { /* 尝试下一个候选地址 */ }
    }
    return null;
  }

  /* ---------- 3. 消息处理 ---------- */
  browser.runtime.onMessage.addListener(function (msg) {
    if (!msg || typeof msg !== 'object') return undefined;

    if (msg.type === 'favicon' && typeof msg.pageUrl === 'string') {
      var key = msg.pageUrl;
      if (iconCache.has(key)) {
        return Promise.resolve({ ok: true, dataUrl: iconCache.get(key) });
      }
      return loadIcon(key).then(function (dataUrl) {
        if (dataUrl) iconCache.set(key, dataUrl);
        return dataUrl ? { ok: true, dataUrl: dataUrl } : { ok: false };
      }).catch(function () { return { ok: false }; });
    }

    if (msg.type === 'openPrivate' && typeof msg.url === 'string') {
      return browser.windows.create({ url: msg.url, incognito: true }).then(function () {
        return { ok: true };
      }).catch(function (e) {
        return { ok: false, error: String((e && e.message) || e) };
      });
    }

    if (msg.type === 'bookmark' && typeof msg.url === 'string') {
      return browser.bookmarks.create({
        title: String(msg.title || msg.url),
        url: msg.url
      }).then(function () {
        return { ok: true };
      }).catch(function (e) {
        return { ok: false, error: String((e && e.message) || e) };
      });
    }

    return undefined;
  });
})();
