#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 AMO 签名后的 MyTab 包是否可以安装 / 是否就是你要装的那个。

用法：
    python verify-signed-xpi.py <路径>.xpi

检查四件事：
  1. 有没有 Mozilla 签名（META-INF/mozilla.rsa + cose.*）—— 没有就是本地未签名包，
     官方版 Firefox 会拒绝安装（MOZ_REQUIRE_SIGNING=true）。
  2. 扩展 ID、版本号是不是预期的那个（mytab@local.mytab）。
  3. update_url / data_collection_permissions 有没有带上。
  4. 算一下 sha256 —— 发布到 GitHub Release 时要写进 updates.json 的 update_hash。
"""
import hashlib
import json
import os
import sys
import zipfile

EXPECTED_ID = "mytab@local.mytab"

# Mozilla 签名相关的文件
SIGNATURE_FILES = (
    "META-INF/mozilla.rsa",
    "META-INF/mozilla.sf",
    "META-INF/manifest.mf",
)
# 新版签名（cose）—— 有它在说明是新版签名流程
COSE_FILES = ("META-INF/cose.manifest", "META-INF/cose.sig")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    if not os.path.exists(path):
        print("找不到文件: %s" % path)
        return 1

    print("=" * 62)
    print("文件: %s" % path)
    print("大小: %.1f KB" % (os.path.getsize(path) / 1024))

    with open(path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    print("sha256: %s" % digest)
    print("=" * 62)

    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        print("✗ 这不是有效的 zip/xpi 文件")
        return 1

    names = set(z.namelist())

    # --- 1. 签名检查 ---
    print("\n[1] Mozilla 签名")
    missing = [f for f in SIGNATURE_FILES if f not in names]
    has_cose = all(f in names for f in COSE_FILES)
    if missing:
        print("  ✗ 缺少签名文件: %s" % ", ".join(missing))
        print("    → 这是**未签名**的本地构建包，官方版 Firefox 装不了。")
        print("    → 请到 AMO 下载签名后的那份再试。")
    else:
        print("  ✓ 签名文件齐全")
        if has_cose:
            print("  ✓ 含新版 cose 签名（META-INF/cose.manifest + cose.sig）")
    for n in sorted(n for n in names if n.startswith("META-INF/")):
        print("      %s" % n)

    # --- 2. manifest 检查 ---
    print("\n[2] manifest")
    if "manifest.json" not in names:
        print("  ✗ 包里没有 manifest.json，不是有效的扩展包")
        return 1
    mf = json.loads(z.read("manifest.json").decode("utf-8"))

    gecko = (mf.get("browser_specific_settings") or {}).get("gecko") or {}
    if not gecko:
        # MV2 的扩展用 applications.gecko
        gecko = (mf.get("applications") or {}).get("gecko") or {}
    addon_id = gecko.get("id")
    version = mf.get("version")

    print("  id      : %s" % addon_id)
    print("  version : %s" % version)
    print("  mv      : %s" % mf.get("manifest_version"))

    ok = True
    if addon_id != EXPECTED_ID:
        print("  ✗ 扩展 ID 不是 %s —— 装上会变成另一个扩展，老数据读不到" % EXPECTED_ID)
        ok = False
    else:
        print("  ✓ 扩展 ID 正确")

    # --- 3. 关键字段 ---
    print("\n[3] 关键字段")
    update_url = gecko.get("update_url")
    if update_url:
        print("  ✓ update_url = %s" % update_url)
    else:
        print("  ✗ 没有 update_url —— 装了以后不会自动更新")
        ok = False

    dcp = gecko.get("data_collection_permissions")
    if dcp:
        print("  ✓ data_collection_permissions = %s" % json.dumps(dcp, ensure_ascii=False))
    else:
        print("  ⚠ 没有 data_collection_permissions")

    if mf.get("chrome_url_overrides"):
        print("  ✓ chrome_url_overrides = %s" % json.dumps(mf["chrome_url_overrides"]))
    else:
        print("  ⚠ 没有 chrome_url_overrides —— 不会接管新标签页")
    if mf.get("chrome_settings_overrides"):
        print("  ✓ chrome_settings_overrides = %s" % json.dumps(mf["chrome_settings_overrides"]))

    print("\n  permissions          : %s" % mf.get("permissions"))
    print("  optional_host_perms  : %s" % mf.get("optional_host_permissions"))

    # --- 4. 包内容 ---
    print("\n[4] 包内文件")
    for n in sorted(names):
        print("      %s" % n)

    print("\n" + "=" * 62)
    if ok and not missing:
        print("结论：✓ 这是可以安装的 AMO 签名包")
        print("\n安装步骤：")
        print("  1. Firefox 里打开 about:addons")
        print("  2. 右上角齿轮 →「从文件安装附加组件…」")
        print("  3. 选中这个 %s" % os.path.basename(path))
        print("  4. 弹窗点「添加」")
        print("\n装完后：")
        print("  · Ctrl+T 新标签页应该变成 MyTab")
        print("  · 工具栏「主页」按钮和 Ctrl+N 新窗口也应该是 MyTab")
        print("  · Firefox 会弹一次提示「An extension, MyTab, changed the page...」")
        print("    —— 点「保留更改」即可，这是正常提示")
        print("\n发布时把 sha256 写进 updates.json 的 update_hash：")
        print("  python .iconfont/build-xpi.py --signed-xpi \"%s\"" % path)
        print("  （update_hash 要用**签名包**算，不是本地构建包）")
    else:
        print("结论：✗ 有问题，先别装")
    print("=" * 62)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
