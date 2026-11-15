# -*- coding: utf-8 -*-
"""Build MyTab group-icon assets from the iconfont.cn collection 9402.

Source: https://www.iconfont.cn/collections/detail?cid=9402
        「Ant Design 官方图标库」(599 icons, official / free)
Curated: .iconfont/curated-9402.json —— 从 599 个图标里挑出适合做分组/分类的
         图形，并补上中文名（搜索同时支持中英文）。

Outputs:
  icons/groups/ad-<iconId>.svg   单色 SVG（fill=currentColor，可直接用作文件）
  icons/groups/manifest.json     id / 中文名 / 英文名 / 文件名清单
  app.js 的 GROUP_ICONS 段       内联 SVG（离线可用，不额外依赖数据文件）

Run:  python .iconfont/build-group-icons.py
"""
import io
import json
import os
import re
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(ROOT, ".iconfont")
OUT_SVG_DIR = os.path.join(ROOT, "icons", "groups")
COLLECTION_ID = "9402"
COLLECTION_NAME = "Ant Design 官方图标库"
COLLECTION_JSON = os.path.join(SRC_DIR, "collections", "%s.json" % COLLECTION_ID)
CURATION_JSON = os.path.join(SRC_DIR, "curated-%s.json" % COLLECTION_ID)
API = "https://www.iconfont.cn/api/collection/detail.json?id=%s" % COLLECTION_ID


def load_collection():
    if not os.path.exists(COLLECTION_JSON):
        req = urllib.request.Request(
            API,
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://www.iconfont.cn/collections/detail?cid=%s" % COLLECTION_ID,
            },
        )
        raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
        os.makedirs(os.path.dirname(COLLECTION_JSON), exist_ok=True)
        with io.open(COLLECTION_JSON, "w", encoding="utf-8") as f:
            f.write(raw)
    with io.open(COLLECTION_JSON, encoding="utf-8") as f:
        return json.load(f)["data"]


def load_curation():
    with io.open(CURATION_JSON, encoding="utf-8") as f:
        return json.load(f)["icons"]


def normalize_svg(raw):
    """Flatten iconfont's show_svg into a theme-aware mono SVG."""
    m = re.search(r'viewBox="([^"]+)"', raw)
    view_box = m.group(1) if m else "0 0 1024 1024"
    inner = raw[raw.index(">") + 1: raw.rindex("</svg>")]
    # 去掉硬编码颜色，交给 currentColor（Ant Design 里同为 #111111）
    inner = re.sub(r'\s*fill="(?!none)[^"]*"', "", inner)
    inner = inner.replace("\n", "").replace("\r", "").strip()
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s" width="1em" height="1em" '
        'fill="currentColor" aria-hidden="true" focusable="false">%s</svg>' % (view_box, inner)
    )


def main():
    data = load_collection()
    collection = data.get("collection") or {}
    all_icons = data["icons"]
    by_exact = {ic["name"]: ic for ic in all_icons}
    by_lower = {}
    for ic in all_icons:
        by_lower.setdefault(ic["name"].strip().lower(), ic)

    curated = load_curation()
    picked = []
    missing = []
    for item in curated:
        en = item["en"].strip()
        ic = by_exact.get(en) or by_lower.get(en.lower())
        if not ic:
            missing.append(en)
            continue
        picked.append((ic, item["zh"].strip()))
    if missing:
        raise SystemExit("curated-%s.json 里这些图标在集合中找不到: %s" % (COLLECTION_ID, ", ".join(missing)))

    os.makedirs(OUT_SVG_DIR, exist_ok=True)
    manifest = []
    js_items = []
    files = set()
    for ic, zh in picked:
        key = "ad-%s" % ic["id"]
        svg = normalize_svg(ic["show_svg"])
        fname = key + ".svg"
        with io.open(os.path.join(OUT_SVG_DIR, fname), "w", encoding="utf-8") as f:
            f.write(svg)
        files.add(fname)
        manifest.append({
            "id": key,
            "name": zh,
            "en": ic["name"],
            "file": fname,
        })
        js_items.append({"id": key, "name": zh, "key": ic["name"], "svg": svg})

    # 清理上一套图标留下的 SVG，避免目录里混着两套
    removed = []
    for name in os.listdir(OUT_SVG_DIR):
        if name.endswith(".svg") and name not in files:
            os.remove(os.path.join(OUT_SVG_DIR, name))
            removed.append(name)

    meta = {
        "source": "https://www.iconfont.cn/collections/detail?cid=%s" % COLLECTION_ID,
        "collection": collection.get("name") or COLLECTION_NAME,
        "creator": (data.get("creator") or {}).get("nickname"),
        "license": "free",
        "generatedBy": ".iconfont/build-group-icons.py",
        "curatedBy": "curated-%s.json（从 %d 个图标中挑选）" % (COLLECTION_ID, len(all_icons)),
        "count": len(manifest),
        "icons": manifest,
    }
    with io.open(os.path.join(OUT_SVG_DIR, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
        f.write("\n")

    body = ",\n".join(
        '    { "id": %s, "name": %s, "key": %s, "svg": %s }' % (
            json.dumps(item["id"]),
            json.dumps(item["name"], ensure_ascii=False),
            json.dumps(item["key"], ensure_ascii=False),
            json.dumps(item["svg"], ensure_ascii=False),
        )
        for item in js_items
    )
    block = (
        "/* === GROUP_ICONS:START ===\n"
        "   * 分组图标数据：iconfont「%s」（cid=%s）精选 %d 个单色 SVG。\n"
        "   * 图标英文名放在 key 字段，搜索支持中英文；由 .iconfont/build-group-icons.py 生成，勿手改。\n"
        "   */\n"
        "  var GROUP_ICONS = [\n%s\n  ];\n"
        "  /* === GROUP_ICONS:END === */" % (COLLECTION_NAME, COLLECTION_ID, len(js_items), body)
    )
    app_path = os.path.join(ROOT, "app.js")
    app = io.open(app_path, encoding="utf-8").read()
    pattern = re.compile(
        r"/\* === GROUP_ICONS:START ===.*?/\* === GROUP_ICONS:END === \*/",
        re.S,
    )
    if not pattern.search(app):
        raise SystemExit("app.js 里找不到 GROUP_ICONS 标记，无法写入图标数据")
    app = pattern.sub(lambda _m: block, app, count=1)
    with io.open(app_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(app)

    print("collection: %s (%s total)" % (COLLECTION_NAME, len(all_icons)))
    print("curated icons:", len(js_items))
    print("removed old svg:", len(removed))
    print("svg dir:", OUT_SVG_DIR)
    print("app.js size:", os.path.getsize(app_path))


if __name__ == "__main__":
    main()
