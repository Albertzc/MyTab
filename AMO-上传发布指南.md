# MyTab 3.1.1 · 火狐（AMO）上传与发布指南

> 适用版本：**3.1.1**（本次正式包）
> 发布方式：**AMO 自托管渠道（unlisted，即 "On your own"）** —— 由 Mozilla 签名，文件自己分发，自动更新走 manifest 里的 `update_url`。
> 插件管理页：<https://addons.mozilla.org/zh-CN/developers/addon/25481ec30f2d4ac2995f/edit>

---

## 1. 本次产物

| 文件 | 用途 | 说明 |
|---|---|---|
| `mytab-3.1.1.xpi` | **上传给 AMO 的包** | 8 个运行时文件，未签名，版本 3.1.1 |
| `.preview/mytab-3.1.1-source.zip` | 备用源码包 | 项目无构建步骤，一般不需要上传；审阅员索要时再传 |
| `updates.json` | 自托管自动更新清单 | **签名后**需用签名包重算一次再上传 |
| `.preview/build-report.txt` | 打包报告 | 改动明细与版本判定 |

发布前已完成校验（与 AMO 服务端同一套校验器）：

```powershell
npx addons-linter --self-hosted mytab-3.1.1.xpi
# → 0 errors / 0 warnings / 0 notices
```

版本判定：3.1.0 → **3.1.1**（patch，移除界面元素 `bgReset`：背景的「恢复默认」按钮并入「数据管理 → 恢复默认」）。

## 2. 关键前提：渠道必须选「自托管」

`manifest.json` 里带有：

```json
"update_url": "https://github.com/Albertzc/MyTab/releases/latest/download/updates.json"
```

- **自托管（On your own / unlisted）**：允许 `update_url`，AMO 只负责签名，更新由 GitHub 分发。
- **公开上架（On this site / listed）**：**不允许** `update_url`，AMO 会直接报错：

  ```
  MANIFEST_UPDATE_URL "update_url" is not allowed for Mozilla-hosted add-ons.
  ```

  若要做公开上架，必须先删掉 `update_url`（让 AMO 托管更新），并改用普通模式重新校验：

  ```powershell
  npx addons-linter mytab-3.1.1.xpi
  ```

## 3. 上传步骤（自托管签名）

1. 打开你的插件管理页 [MyTab · Developer Hub](https://addons.mozilla.org/zh-CN/developers/addon/25481ec30f2d4ac2995f/edit)，用 Mozilla 账号 **Log in**（没有就 **Register**）。也可以从 [AMO 开发者中心](https://addons.mozilla.org/developers/) 的 **My Add-ons** 进入。
2. 点击 **Submit Your First Add-on** 或 **Submit a New Add-on**。
3. 渠道选择：
   - 选 **On your own**（自己分发、不在商店公开），点 **Continue**。
   - 不要选 **On this site**（会因 `update_url` 校验失败）。
4. 进入 **Upload Version** 页，点 **Select a file**，上传 `mytab-3.1.1.xpi`。
5. 等待自动校验完成：
   - 出现 **无错误** 提示即可继续；
   - 若只有 warning，建议逐条确认后继续（尤其是隐私/安全类）。
6. 选择兼容平台：勾选 **Firefox**（桌面）。需要 Android 时再勾选 Firefox for Android（manifest 要求 142+）。
7. **Provide source code**：选 **No**（本项目没有构建/压缩步骤，包内文件就是源码）。
   若后续审阅员要求，再上传 `.preview/mytab-3.1.1-source.zip`，并在 **Notes for Reviewers** 里说明「无构建步骤」。
8. 点 **Continue**，出现 **Version Signature Pending** 页面，点 **Go to My Submissions**。
9. 等待签名（自动签名通常几分钟，最多 24 小时；被人工抽查会更久），签名完成会收到邮件。

## 4. 下载签名后的包

1. 打开 **My Add-ons** → 对应扩展 → 最新版本处点 **View All**（版本列表直达：<https://addons.mozilla.org/zh-CN/developers/addon/25481ec30f2d4ac2995f/versions>）。
2. 进入刚上传的版本页，**右键**文件链接 → **Save Link As...** 下载签名版 xpi。签名完成后也可以直接用 <https://addons.mozilla.org/firefox/downloads/latest/25481ec30f2d4ac2995f/> 下载最新签名包（会 302 跳到带签名的 xpi；未签名/未发布前该地址返回 404）。
3. 把文件名改成 **`mytab-3.1.1.xpi`**（不带 `mytab@local.mytab-` 前缀）——`updates.json` 里的 `update_link` 按这个文件名生成。

## 5. 重算自动更新清单

用签名包重新生成 `updates.json`（会写入 `update_hash`，并把 update_link 指向签名文件）：

```powershell
python .iconfont/build-xpi.py --no-bump --signed-xpi .\signed\mytab-3.1.1.xpi
```

> 说明：`--no-bump` 表示不升版本；该命令会用源码重新写出同样的 `mytab-3.1.1.xpi`，并覆盖 `updates.json`。
> 生成后检查 `updates.json`：`version` 为 `3.1.1`、`update_link` 指向 GitHub Release、`update_hash` 以 `sha256:` 开头。

## 6. 分发与自动更新

1. 在 GitHub 仓库创建 Release（**不要勾选 prerelease**），标签如 `v3.1.1`。
2. 上传两个资产，**文件名必须精确一致**：
   - `mytab-3.1.1.xpi`（AMO 签名版）
   - `updates.json`
3. `update_url` 是 `.../releases/latest/download/updates.json`，所以必须放在**最新的正式 Release** 里，Firefox 才能拉到。
4. 自动更新规则：Firefox 定期拉取 `updates.json`，发现**更高版本**才更新；已签名扩展的更新文件也必须带 Mozilla 签名，所以 `update_link` 必须指向签名包，不能指向本地未签名包。

## 7. 发布后验证

1. `about:addons` → 齿轮 → **从文件安装附加组件…** → 选签名版 `mytab-3.1.1.xpi`。
2. 打开新标签页确认版本：设置面板「关于」应显示 **MyTab v3.1.1**。
3. 设置 → **网站图标**：点击「授权获取图标」→ 允许后，磁贴图标应逐个换成真实图标（失败站点回退首字母色块）。
4. 升级验证：再发一个 3.1.2（`--bump patch`），上传 Release 后，`about:addons` 手动点「检查更新」应能发现新版本。

## 8. 常见问题

| 现象 | 原因与处理 |
|---|---|
| 上传即报 `MANIFEST_UPDATE_URL` | 选成了公开上架（On this site）。改选 **On your own** 重传；或删掉 manifest 的 `update_url` |
| 提示版本已存在 | AMO 上已有 `mytab@local.mytab` 的 3.1.1。必须用更高版本号重新打包 |
| 签名邮件迟迟不到 | 自动签名排队/人工抽查，最多 24 小时；期间不要重复提交同版本 |
| 用户装不上 | 必须分发**签名版** xpi；未签名的 `mytab-temp-debug.xpi` 只适合 `about:debugging` 临时加载 |
| 自动更新不生效 | 检查三处：`updates.json` 在 latest release、资产名精确、`version` 大于已装版本 |
| 想撤回版本 | 自托管渠道无法从 AMO 撤回已分发文件；直接发一个更高版本号覆盖即可 |

## 9. 发布检查清单

- [ ] 已登录插件管理页 <https://addons.mozilla.org/zh-CN/developers/addon/25481ec30f2d4ac2995f/edit>
- [ ] `mytab-3.1.1.xpi` 已用 `--self-hosted` 模式校验 0 error
- [ ] AMO 渠道选 **On your own**
- [ ] 平台勾选正确（Firefox 桌面；需要时加 Android）
- [ ] 源码包：选 No（被要求时再传 `.preview/mytab-3.1.1-source.zip`）
- [ ] 下载签名包并改名为 `mytab-3.1.1.xpi`
- [ ] 用 `--signed-xpi` 重算 `updates.json` 并确认 `update_hash`
- [ ] GitHub Release 上传两个资产、且 latest 指向该版本
- [ ] 实机安装验证版本号与图标授权流程

## 10. 本次版本变更摘要（可粘贴到 Notes for Reviewers）

- 无构建步骤：包内 8 个文件即源码，无压缩/混淆/远程代码。
- 3.1.1 变更（相对 3.1.0）：设置面板把原「数据备份」与「重置」合并为「数据管理」，内含「恢复默认 / 导出配置 / 导入配置」；移除背景图片区块的「恢复默认」按钮，背景重置统一由「数据管理 → 恢复默认」完成；「关于」移到设置面板底部并更新文案。无权限、存储结构、localStorage 键名变化。
- 3.1.0 变更（背景）：设置面板新增「网站图标」区块与授权按钮；按需申请 `*://*/*` 可选主机权限，授权后由后台读取网页声明的 `<link rel=icon>`，用于显示真实网站图标；不授权时仅尝试根目录 `favicon.ico` 并回退首字母色块。
- 新增磁贴时，若用户授予该站点权限，会立即重试获取图标。
- 默认磁贴更新：GitHub、哔哩哔哩、知乎、豆瓣、掘金；AI 磁贴：DeepSeek、智谱清言、Kimi、MiniMax、豆包、通义千问。
- 所有数据仍只保存在本地 localStorage；不收集、不上报任何用户数据（`data_collection_permissions.required = ["none"]`）。
