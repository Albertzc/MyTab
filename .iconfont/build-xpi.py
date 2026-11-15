# -*- coding: utf-8 -*-
"""Package MyTab as mytab-<version>.xpi，并**按语义化版本（SemVer）决定版本号**。

用法:
    python .iconfont/build-xpi.py                  # 自动按语义判定升版本（major/minor/patch）
    python .iconfont/build-xpi.py --bump minor     # 强制指定升哪一级（覆盖自动判定）
    python .iconfont/build-xpi.py --version 1.6.0  # 直接指定版本号
    python .iconfont/build-xpi.py --no-bump        # 沿用 manifest 里的版本号（不升）
    python .iconfont/build-xpi.py --dry-run        # 只报告，不写文件、不打包

判定方式：把工作区的运行时文件与**最近一个 mytab-*.xpi** 里的同名文件逐个对比，
再按语义化版本的定义分级（而不是按「新增了几个函数」这类代理信号）：

    major  破坏性变更 —— 旧数据 / 旧环境不再兼容
           · manifest 的 permissions / host_permissions / browser_specific_settings 变了
           · app.js 里的 localStorage 键名（STORE_KEY / FAV_KEY）变了
           · 移除了某个设置项或存储字段（旧数据里这些值不再被读取）
           · 删掉了 JS 仍在引用的 DOM id（运行时会直接报错）
           · 移除了后台消息类型，但页面仍在调用它
    minor  向后兼容的新功能 —— 老数据照常能用
           · 新增设置项 / 新增存储字段
           · 新增界面元素（index.html 新增 DOM id）
           · 新增后台消息类型
    patch  向后兼容的修复 —— 不加功能、不动兼容面
           · 样式、类名、文案、描述、修复类改动
           · 纯内部重构（app.js 有改动但没有新增任何能力）

**运行时文件与上一个包完全一致时，不升版本、也不打包**（避免空版本）。

打包后会自动同步：manifest.json 的 version、index.html「关于」里的版本号、
README 里的 xpi 文件名与「功能（vX.Y.Z）」标题。
"""
import argparse
import difflib
import glob
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNTIME_FILES = [
    "manifest.json",
    "background.js",
    "index.html",
    "styles.css",
    "app.js",
    "icons/icon-48.png",
    "icons/icon-96.png",
    "icons/icon-128.png",
]
TEXT_FILES = {"manifest.json", "background.js", "index.html", "styles.css", "app.js"}


# ---------------------------------------------------------------- 版本号工具
def parse_version(v):
    m = re.match(r"^(\d+)\.(\d+)\.(\d+)$", str(v).strip())
    if not m:
        raise SystemExit("版本号格式不对: %r（应为 x.y.z）" % v)
    return tuple(int(x) for x in m.groups())


def bump(version, kind):
    major, minor, patch = version
    if kind == "major":
        return (major + 1, 0, 0)
    if kind == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def latest_xpi():
    """返回 (版本元组, 路径) —— 版本号最大的历史包"""
    best = None
    for p in glob.glob(os.path.join(ROOT, "mytab-*.xpi")):
        m = re.match(r"^mytab-(\d+)\.(\d+)\.(\d+)\.xpi$", os.path.basename(p))
        if not m:
            continue
        v = tuple(int(x) for x in m.groups())
        if best is None or v > best[0]:
            best = (v, p)
    return best


def read_package(path):
    out = {}
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            out[n] = z.read(n)
    return out


# ---------------------------------------------------------------- 改动信号
def ids_in_html(text):
    return set(re.findall(r'id="([^"]+)"', text))


def css_classes(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    names = set(re.findall(r"\.([A-Za-z_][\w-]*)", text))
    return {n for n in names if not n.isdigit()}


def js_message_types(text):
    """后台消息类型：兼容 msg.type === 'x' / msg.type == 'x' / { type: 'x' }"""
    return set(re.findall(r"type\s*(?:===|==|:)\s*'([\w-]+)'", text))


def js_storage_keys(text):
    return set(re.findall(r"(?:STORE_KEY|FAV_KEY)\s*=\s*'([^']+)'", text))


def js_used_ids(text):
    """JS 里通过 $('id') / getElementById('id') 引用到的元素 id"""
    ids = set(re.findall(r"\$\(\s*'([^']+)'\s*\)", text))
    ids |= set(re.findall(r"getElementById\(\s*'([^']+)'\s*\)", text))
    return ids


def _object_body(text, brace_index):
    """从 '{' 开始按花括号配对取出对象字面量的内容"""
    depth = 0
    for i in range(brace_index, len(text)):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[brace_index + 1:i]
    return ''


def _object_keys(body):
    """取对象字面量第一层的键名（按最小缩进判断第一层）"""
    lines = [l for l in body.splitlines() if l.strip()]
    if not lines:
        return set()
    indent = min(len(l) - len(l.lstrip()) for l in lines)
    keys = set()
    for l in lines:
        if len(l) - len(l.lstrip()) == indent:
            m = re.match(r"([A-Za-z_$][\w$]*)\s*:", l.strip())
            if m:
                keys.add(m.group(1))
    return keys


def js_settings_fields(text):
    """defaultSettings() 里定义的设置字段名 —— 存储结构的兼容性边界"""
    m = re.search(r"function\s+defaultSettings\s*\(\s*\)\s*\{", text)
    if not m:
        return set()
    body = _object_body(text, m.end() - 1)
    r = re.search(r"return\s*\{", body)
    if not r:
        return set()
    return _object_keys(_object_body(body, r.end() - 1))


def js_store_payload_keys(text):
    """save() 里写进 localStorage 的顶层字段名"""
    m = re.search(r"localStorage\.setItem\(\s*STORE_KEY\s*,\s*JSON\.stringify\(\s*\{", text)
    if not m:
        return set()
    brace = text.index("{", m.end() - 1)
    return _object_keys(_object_body(text, brace))


def manifest_signals(text):
    try:
        m = json.loads(text)
    except Exception:
        return {}
    return {
        "permissions": m.get("permissions"),
        "host_permissions": m.get("host_permissions"),
        "browser_specific_settings": m.get("browser_specific_settings"),
        "name": m.get("name"),
        "description": m.get("description"),
    }


def classify(old, new):
    """按语义化版本判定改动级别，返回 (kind, 原因列表)。

    kind 为 None 表示运行时文件与上一个包完全一致 —— 不该产生空版本。
    """
    major, minor, patch = [], [], []

    om = manifest_signals(old.get("manifest.json", b"").decode("utf-8", "ignore"))
    nm = manifest_signals(new.get("manifest.json", b"").decode("utf-8", "ignore"))
    for key, label in (
        ("permissions", "权限 permissions"),
        ("host_permissions", "主机权限 host_permissions"),
        ("browser_specific_settings", "扩展身份 browser_specific_settings"),
    ):
        if om.get(key) != nm.get(key):
            major.append("manifest 的%s变了（破坏性：影响权限 / 扩展身份）" % label)
    if om.get("name") != nm.get("name"):
        patch.append("manifest 的 name 变了（仅展示文案）")
    if om.get("description") != nm.get("description"):
        patch.append("manifest 的 description 变了（仅展示文案）")

    o_app = old.get("app.js", b"").decode("utf-8", "ignore")
    n_app = new.get("app.js", b"").decode("utf-8", "ignore")
    if js_storage_keys(o_app) != js_storage_keys(n_app):
        major.append("app.js 的 localStorage 键名变了（旧数据读不到）")

    o_set = js_settings_fields(o_app)
    n_set = js_settings_fields(n_app)
    added_set = n_set - o_set
    removed_set = o_set - n_set
    if added_set:
        minor.append("新增设置项：%s（老数据缺省时走默认值，向后兼容）" % ", ".join(sorted(added_set)))
    if removed_set:
        major.append("移除设置项：%s（旧数据里这些值不再被读取）" % ", ".join(sorted(removed_set)))

    o_store = js_store_payload_keys(o_app)
    n_store = js_store_payload_keys(n_app)
    added_store = n_store - o_store
    removed_store = o_store - n_store
    if added_store:
        minor.append("新增存储字段：%s" % ", ".join(sorted(added_store)))
    if removed_store:
        major.append("移除存储字段：%s" % ", ".join(sorted(removed_store)))

    o_bg = old.get("background.js", b"").decode("utf-8", "ignore")
    n_bg = new.get("background.js", b"").decode("utf-8", "ignore")
    o_types = js_message_types(o_bg)
    n_types = js_message_types(n_bg)
    added_types = n_types - o_types
    removed_types = o_types - n_types
    if added_types:
        minor.append("新增后台消息类型：%s" % ", ".join(sorted(added_types)))
    if removed_types:
        still = sorted(t for t in removed_types if ("'%s'" % t) in o_app)
        if still:
            major.append("移除后台消息类型但页面仍在调用：%s" % ", ".join(still))
        else:
            patch.append("移除后台消息类型：%s" % ", ".join(sorted(removed_types)))

    o_html = old.get("index.html", b"").decode("utf-8", "ignore")
    n_html = new.get("index.html", b"").decode("utf-8", "ignore")
    o_ids = ids_in_html(o_html)
    n_ids = ids_in_html(n_html)
    added_ids = n_ids - o_ids
    removed_ids = o_ids - n_ids
    if added_ids:
        minor.append("新增界面元素：%s" % ", ".join(sorted(added_ids)))
    used_now = js_used_ids(n_app)
    still_used = sorted(removed_ids & used_now)
    if still_used:
        major.append("删掉了页面仍在引用的 DOM id：%s（运行时会直接报错）" % ", ".join(still_used))
    elif removed_ids:
        patch.append("移除界面元素：%s" % ", ".join(sorted(removed_ids)))

    o_css = old.get("styles.css", b"").decode("utf-8", "ignore")
    n_css = new.get("styles.css", b"").decode("utf-8", "ignore")
    added_cls = css_classes(n_css) - css_classes(o_css)
    if added_cls:
        patch.append("新增样式类：%s" % ", ".join(sorted(added_cls)))

    # 兜底：没有任何「新增能力」信号，但运行时文件确有字节差异
    # （改样式数值、修 bug、内部重构、换图标）——一律算 patch
    changed_files = [n for n in RUNTIME_FILES if old.get(n) != new.get(n)]
    if not major and not minor and not patch and changed_files:
        patch.append("改动文件（无新增能力，属修复 / 样式 / 重构）：%s" % ", ".join(changed_files))

    if major:
        return "major", major + minor + patch
    if minor:
        return "minor", minor + patch
    if patch:
        return "patch", patch
    return None, ["运行时文件与上一个包完全一致"]


def summarize_diff(old, new):
    lines = []
    for name in RUNTIME_FILES:
        o = old.get(name)
        n = new.get(name)
        if o is None:
            lines.append("  %-20s 新增文件" % name)
            continue
        if n is None:
            lines.append("  %-20s 删除文件" % name)
            continue
        if o == n:
            continue
        if name not in TEXT_FILES:
            lines.append("  %-20s 二进制变更（%d → %d 字节）" % (name, len(o), len(n)))
            continue
        ol = o.decode("utf-8", "ignore").splitlines()
        nl = n.decode("utf-8", "ignore").splitlines()
        d = list(difflib.unified_diff(ol, nl, lineterm="", n=0))
        adds = sum(1 for x in d if x.startswith("+") and not x.startswith("+++"))
        dels = sum(1 for x in d if x.startswith("-") and not x.startswith("---"))
        lines.append("  %-20s +%d / -%d 行" % (name, adds, dels))
    return lines or ["  （与上一个包内容完全一致）"]


# ---------------------------------------------------------------- 写版本号
def write_version(new_version, old_version):
    """把新版本号写回 manifest.json / index.html / README.md（只动版本号，不重排文件）"""
    vp = os.path.join(ROOT, "manifest.json")
    with open(vp, encoding="utf-8") as f:
        mf = f.read()
    mf = re.sub(r'("version"\s*:\s*")\d+\.\d+\.\d+(")', r"\g<1>%s\g<2>" % new_version, mf, count=1)
    with open(vp, "w", encoding="utf-8") as f:
        f.write(mf)

    ip = os.path.join(ROOT, "index.html")
    with open(ip, encoding="utf-8") as f:
        html = f.read()
    html = re.sub(r"MyTab v\d+\.\d+\.\d+", "MyTab v" + new_version, html)
    with open(ip, "w", encoding="utf-8") as f:
        f.write(html)

    rp = os.path.join(ROOT, "README.md")
    if os.path.exists(rp):
        with open(rp, encoding="utf-8") as f:
            rd = f.read()
        # README 里的「当前包」引用统一指向新版本（历史 xpi 文件名不动）
        rd = re.sub(r"mytab-\d+\.\d+\.\d+\.xpi", "mytab-%s.xpi" % new_version, rd)
        rd = re.sub(r"## 功能（v\d+\.\d+\.\d+）", "## 功能（v%s）" % new_version, rd)
        # 文件结构那一行：mytab-x.y.z.xpi   打包好的 Firefox 扩展（vX.Y.Z）
        rd = re.sub(r"(mytab-\d+\.\d+\.\d+\.xpi[^\n]*?（v)\d+\.\d+\.\d+(）)",
                    lambda m: m.group(1) + new_version + m.group(2), rd)
        with open(rp, "w", encoding="utf-8") as f:
            f.write(rd)


# ---------------------------------------------------------------- 主流程
def main():
    ap = argparse.ArgumentParser(description="打包 MyTab 扩展并自动升版本号")
    ap.add_argument("--version", help="指定版本号（x.y.z），跳过自动判断")
    ap.add_argument("--bump", choices=["major", "minor", "patch"],
                    help="强制指定升哪一级（覆盖自动判定）")
    ap.add_argument("--no-bump", action="store_true", help="沿用 manifest 里的版本号，不自动升")
    ap.add_argument("--dry-run", action="store_true", help="只报告改动与版本判断，不写文件")
    args = ap.parse_args()

    missing = [f for f in RUNTIME_FILES if not os.path.exists(os.path.join(ROOT, f))]
    if missing:
        raise SystemExit("缺少运行时文件: %s" % ", ".join(missing))

    with open(os.path.join(ROOT, "manifest.json"), encoding="utf-8") as f:
        cur_version = json.load(f)["version"]

    new_files = {}
    for rel in RUNTIME_FILES:
        with open(os.path.join(ROOT, rel), "rb") as f:
            new_files[rel] = f.read()

    old_pack = latest_xpi()
    old_files = read_package(old_pack[1]) if old_pack else {}
    manifest_version = parse_version(cur_version)
    # 基准 = 最近一个已打包的版本（manifest 里的版本只是上次打包的产物，不作为基准）
    base_version = old_pack[0] if old_pack else manifest_version
    old_version = "%d.%d.%d" % base_version

    # 对比时把版本号字符串抹平，避免版本号本身被算成"改动"
    old_cmp = dict(old_files)
    new_cmp = dict(new_files)
    for key in ("index.html", "manifest.json"):
        if key in old_cmp:
            old_cmp[key] = re.sub(rb"(mytab-|MyTab v)\d+\.\d+\.\d+", rb"\1X.Y.Z", old_cmp[key])
        new_cmp[key] = re.sub(rb"(mytab-|MyTab v)\d+\.\d+\.\d+", rb"\1X.Y.Z", new_cmp[key])
    if "manifest.json" in old_cmp:
        old_cmp["manifest.json"] = re.sub(rb'("version"\s*:\s*")\d+\.\d+\.\d+(")', rb"\1X.Y.Z\2", old_cmp["manifest.json"])
    if "manifest.json" in new_cmp:
        new_cmp["manifest.json"] = re.sub(rb'("version"\s*:\s*")\d+\.\d+\.\d+(")', rb"\1X.Y.Z\2", new_cmp["manifest.json"])

    kind, reasons = classify(old_cmp, new_cmp)

    if args.version:
        target = parse_version(args.version)
        kind = "指定"
    elif args.no_bump:
        target = manifest_version
        kind = "不升版本"
    elif args.bump:
        # 人工按语义化版本判断指定级别（覆盖自动判定）
        target = bump(base_version, args.bump)
        kind = "手动指定 " + args.bump
    elif kind is None:
        # 运行时文件与上一个包完全一致：不该产生空版本
        target = manifest_version
        kind = "无改动"
    else:
        # 自动升号，并与 manifest 里已预置的版本取大者：
        # 保证版本号永远大于最近一个已发布的包，且不重复占用同一个版本号
        target = max(bump(base_version, kind), manifest_version)
        if target == manifest_version and target != bump(base_version, kind):
            kind = "沿用 manifest 预置版本"

    new_version = "%d.%d.%d" % target
    out = os.path.join(ROOT, "mytab-%s.xpi" % new_version)

    print("=" * 62)
    print("对比基准 : %s" % (old_pack[1] if old_pack else "（无历史包）"))
    print("当前版本 : %s" % cur_version)
    print("改动明细 :")
    for line in summarize_diff(old_cmp, new_cmp):
        print(line)
    print("判断依据 :")
    for r in reasons:
        print("  · %s" % r)
    print("版本决策 : %s → %s（%s）" % (old_version, new_version, kind))
    print("=" * 62)

    if kind == "无改动":
        print("运行时文件与最近一个包完全一致 → 不升版本、不打包。")
        print("（如需强制产出一个版本，用 --bump patch / --version x.y.z）")
        return

    report = "\n".join([
        "MyTab 打包报告",
        "对比基准 : %s" % (old_pack[1] if old_pack else "（无历史包）"),
        "当前版本 : %s" % cur_version,
        "改动明细 :", *summarize_diff(old_cmp, new_cmp),
        "判断依据 :", *["  · %s" % r for r in reasons],
        "版本决策 : %s → %s（%s）" % (old_version, new_version, kind),
    ])
    os.makedirs(os.path.join(ROOT, ".preview"), exist_ok=True)
    with open(os.path.join(ROOT, ".preview", "build-report.txt"), "w", encoding="utf-8") as f:
        f.write(report + "\n")

    if args.dry_run:
        print("dry-run：未写文件、未打包")
        return

    write_version(new_version, old_version)

    tmp = out + ".tmp"
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in RUNTIME_FILES:
            z.write(os.path.join(ROOT, rel), rel)
    os.replace(tmp, out)

    with zipfile.ZipFile(out) as z:
        entries = z.namelist()
    print("wrote %s (%d bytes, %d files)" % (out, os.path.getsize(out), len(entries)))
    for e in entries:
        print("  " + e)
    print("已同步版本号：manifest.json / index.html / README.md")
    print("提醒：原型设计-分组.md 的落盘清单与 README 的回归记录需手动补一行。")


if __name__ == "__main__":
    main()
