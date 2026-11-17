# MyTab —— AMO（addons.mozilla.org）提交材料

本文件是提交到 addons.mozilla.org 时**逐个字段复制粘贴**用的清单。
分发方式：**Unlisted / 自托管**（On your own），不公开上架。

---

## 1. 提交方式

addons.mozilla.org → [Submit a New Add-on](https://addons.mozilla.org/developers/addon/submit/) → 选 **On your own**（自托管）。

选「On this site」会走公开上架，需要人工审核（1–7 天），且商店页会公开。
选「On your own」只做自动签名（几分钟到几小时），拿到的签名包自己分发。

> ⚠️ **一旦提交，`mytab@local.mytab` 这个扩展 ID 就永久占用了**，发布出去的 ID 不能改。
> 改 ID 会导致 Firefox 重新分配 `moz-extension://` 的 origin UUID，**老用户的数据全部读不到**。
> 本项目的 ID 保持不变。

---

## 2. 版本信息

| 字段 | 值 |
|---|---|
| 上传文件 | `mytab-3.0.1.xpi`（**必须是 AMO 签名后的那份**，见第 5 节） |
| 版本号 | `3.0.1` |
| 源文件包 | 不需要 —— 代码未压缩、未混淆、未经过打包器，审阅员能直接读 `app.js` / `background.js` |

---

## 3. Listing 字段

### Name（≤ 50 字符）

```
MyTab for Firefox
```

> 政策要求：名字里带 "Firefox" 时必须是 `<Add-on Name> for Firefox` 的格式。

### Summary（≤ 66 字符）

```
本地、快速、零账号的新标签页：时钟、搜索、网站磁贴与分组图标栏
```

### Description

```markdown
MyTab 是一个完全在本机运行的新标签页：打开一个新标签，看到的是你自己的时钟、搜索框和常用网站磁贴，而不是广告和资讯流。

## 主要功能

- **大时钟与日期**：24 / 12 小时制可切换，点击可放大缩小。
- **搜索框**：内置 Bing / 百度 / Google / 知乎，可编辑名称与网址、删除或新增自定义引擎；第一位是默认引擎。
- **网站磁贴**：把常用网站放到首页，拖动即可排序。
- **分组（文件夹）**：磁贴按分组归档，左侧窄图标栏切换分组，悬停显示「分组名 + 数量」；每组独立分页。
- **内置图标库**：134 个单色 SVG 分组图标，可搜索、可更换。
- **外观**：浅色 / 深色 / 跟随系统；渐变背景、纯色背景，或选择本机图片。
- **右键菜单**：新标签页 / 新窗口 / 无痕窗口打开、复制链接、收藏到书签、编辑、移动到分组、删除。
- **配置导入导出**：导出一个 ZIP（含配置 JSON 和背景图片），可备份或换机迁移。

## 关于数据与网络

- **所有配置只保存在本机的浏览器 localStorage 里**，不上传、不同步、不需要账号。
- **没有统计、没有广告、没有后台遥测**，扩展本身没有任何第三方脚本。
- 唯一的对外请求是你自己添加的网站：为了抓取该网站的图标，浏览器会向**那个站点本身**请求 `/favicon.ico`。
  这个请求由你添加的网址直接决定，扩展不会把任何信息发送到别处。
- 搜索时，搜索词会直接发送给**你选定的那个搜索引擎**（Bing / 百度 / Google / 知乎或你自定义的），这是搜索引擎的常规用法。

## 权限说明

| 权限 | 为什么需要 |
|---|---|
| `bookmarks` | 右键菜单里的「收藏到书签」 |
| `clipboardWrite` | 右键菜单里的「复制链接地址」 |
| 可选主机权限 `*://*/*` | 只有你添加了某个网站的磁贴时，才会就**那一个站点**向你申请访问权，用来读取它的图标声明（`<link rel="icon">`）。你可以在 Firefox 的「附加组件权限」里随时撤销，撤销后图标回退为首字母色块，**其余功能不受影响**。 |

扩展**不会**读取你的浏览历史、书签内容、Cookie 或任何其他标签页。

## 隐私

完整说明见项目仓库里的 [PRIVACY.md](https://github.com/Albertzc/MyTab/blob/main/PRIVACY.md)。
一句话：数据只在本机，既不出售也不共享。

## 许可

MIT
```

### Categories（最多 2 个）

```
Themes
Productivity
```

### Icons

| 尺寸 | 文件 |
|---|---|
| 48×48 | `icons/icon-48.png` |
| 96×96 | `icons/icon-96.png` |
| 128×128 | `icons/icon-128.png` |

### Screenshots

上传 `1366×768` 或 `1280×800` 的截图。可直接用仓库 `.preview/` 里的成片：

- `v2.0.0-default.png` —— 默认主页（时钟 + 搜索 + 文件夹墙）
- `v2.0.0-panel.png` —— 设置面板

> ⚠️ `.preview/` 是 gitignore 的，不会进仓库。**提交前需要自己截两张图**，或者把选中的图拷到仓库里再上传。

### 「Do you need to provide source code?」（第 7 步）→ 选 **No**

AMO 提交流程的第 7 步会问：

> **Indicate whether you need to provide your source code.**
> （你是否需要提供源代码？）

**MyTab 选 `No`，不需要上传任何源文件。**

AMO 官方文档（[Source code submission](https://extension-workshop.mozilla.org/documentation/publish/source-code-submission/)）规定，
只有在扩展代码是用下列工具生成、**导致审阅员读不懂代码**时才必须上传源代码：

| 需要上传 | MyTab |
|---|---|
| 代码压缩器（uglifyJS、Closure Compiler…） | ❌ 没有 |
| 打包合并（webpack、browserify、rollup…） | ❌ 没有 |
| 模板引擎（handlebars、css2js…） | ❌ 没有 |
| 其它「预处理后生成文件」的自定义工具 | ❌ 没有 |

**扩展包里的文件就是源文件本身，一个字节都没经过处理。**
审阅员解压 xpi 就能逐行读 `app.js`（2900+ 行、带中文注释）、`background.js`、`index.html`、`styles.css`，
根本不需要构建，也不需要比对产物。

> `app.js` 顶部的 `GROUP_ICONS` 段由 `.iconfont/build-group-icons.py` 生成后写回 `app.js`，
> 但它生成出来的是一段**普通 JS 字面量数组**（SVG 字符串），不是难以阅读的产物 ——
> 审阅员能直接读，**不需要**为还原扩展包执行任何命令。

#### 万一你还是想上传（可选，非必需）

我已经准备好了一份现成的源文件包：

```
.preview\mytab-3.0.1-source.zip
```

内容 = 扩展包里的 8 个文件**逐字节完全相同** + 一个 `README.md`（说明「无构建步骤」）。

上传它之前注意两点：

1. **如果之后还要再发新版本，AMO 要求每个版本都重新附上匹配的源代码**
   （官方文档原文：「matching source code must be attached to every extension version」）。
   所以每发一版都要重新生成这个 zip。
2. 源文件包里的 `README.md` **不包含在扩展包中** —— 审阅员比对时应当只比对那 8 个同名文件。

生成命令（`.preview/` 已被 gitignore，不进仓库）：

```bash
python .iconfont/build-xpi.py --source-zip
```

输出 `.preview\mytab-<版本号>-source.zip`：扩展包里的 8 个文件**逐字节完全相同** + 一个 `README.md`。

### License

```
MIT License  (仓库里的 LICENSE 文件)
```

### Support Information

| 字段 | 值 |
|---|---|
| Support email | `你的邮箱` |
| Support URL | `https://github.com/Albertzc/MyTab/issues` |
| Homepage URL | `https://github.com/Albertzc/MyTab` |

---

## 4. Notes for Reviewers（**必填，别跳过**）

这一栏是审阅员唯一的上下文，务必写清楚「为什么需要这些权限」和「哪些行为是用户主动触发的」。

```
MyTab is a purely local new tab page. The reviewer may load the xpi directly.

How to test:
1. Open a new tab — MyTab's page loads (it is registered via
   chrome_url_overrides.newtab, the standard Firefox new tab mechanism).
2. Right-click the page background to add a tile; right-click a tile for the
   context menu (open in new tab / new window / private window / copy link /
   bookmark / edit / move to group / delete).
3. Click the gear icon at the bottom of the left icon bar to open settings.

About the new tab / homepage override:
- The add-on's PRIMARY FUNCTION is to be the new tab page, so it declares
  "chrome_url_overrides": { "newtab": "index.html" }.
- It also declares "chrome_settings_overrides": { "homepage": "index.html" } so
  that the toolbar Home button and new windows (Ctrl+N) show MyTab as well.
  Firefox opens new windows with the homepage rather than the new tab page,
  so without this key the Home button and Ctrl+N would still show Activity
  Stream while Ctrl+T showed MyTab — an inconsistent result.
- This is why the add-on is named "MyTab" and its description says it is a
  new tab page: overriding the new tab page is the add-on's main purpose, not
  an unexpected side feature. The user can revert both at any time in
  Firefox Settings -> Home, or via the doorhanger Firefox shows when the
  extension takes control.

About the permissions:
- "bookmarks" — only for the "收藏到书签" (Bookmark) item in the tile context
  menu. It creates one bookmark the user explicitly asked for. It never reads
  existing bookmarks.
- "clipboardWrite" — only for the "复制链接地址" (Copy link address) item in
  the tile context menu. It writes the URL of the tile the user right-clicked
  to the clipboard. It never reads the clipboard.
- optional_host_permissions "*://*/*" — this is an OPTIONAL permission, not
  granted at install time. When the user adds a tile for a site, MyTab asks for
  access to THAT ONE site's origin only, in order to read its
  <link rel="icon"> declaration so the tile shows the correct icon. If the
  user declines, the tile still works and falls back to a first-letter avatar.
  No host permission is granted at install time.
- The add-on does NOT request the "tabs" permission, and does not read browsing
  history, cookies or any other tab's content.

Network behaviour:
- The extension contains no analytics, no telemetry, no ads and no third-party
  JavaScript.
- The only outbound request is to the host of a site the user added a tile for,
  asking that site for its own favicon.
- Search terms are sent to the search engine the user selected, only when the
  user submits a search.
- Configuration data never leaves the browser; it is stored in localStorage.

data_collection_permissions is declared as {"required": ["none"]}: the add-on
does not collect or transmit personal data.

Source code:
The add-on is plain, unminified JavaScript with no build step. app.js,
background.js, index.html and styles.css are directly readable in the xpi.
Please see the source repository: https://github.com/Albertzc/MyTab
```

---

## 5. 下载签名包并安装到浏览器

### 5.1 从 AMO 下载签名后的 xpi

签名是**自动**的（Unlisted 不需要人工审核），AMO 签好后你会收到一封邮件。

#### 方式 A：邮件（最快）

邮件标题类似 "Your add-on has been signed" / "Your add-on has been signed and is ready to be shared"，
正文里有个下载链接。点它就是签名包。

#### 方式 B：Developer Hub 界面

```
addons.mozilla.org/developers/addon/<你的slug>/versions
   │
   ├─ 左侧菜单「管理状态与版本」(Manage Status & Versions)
   │
   └─ 版本列表里点版本号（比如 3.0.1）
        ↓
      版本详情页 → 「Files / 文件」表格
        ↓
      第一列的文件名（带 .xpi 后缀）就是下载链接 ← 点它
```

> 源码依据（addons-server）：
> - 版本列表页 = `devhub/versions/list.html`，版本号链接到 `devhub.versions.edit`
> - 版本详情页 = `devhub/versions/edit.html`，含 `devhub/includes/version_file.html`
>   → `<a href="{{ file.get_absolute_url() }}">{{ file.pretty_filename }}</a>`
>   → 文件名本身就是下载链接

#### 方式 C：直接用 URL（不想点界面）

把你的 slug 填进去，浏览器会直接下载：

```
https://addons.mozilla.org/firefox/downloads/latest/<你的slug>/
```

例如 slug 是 `mytab-for-firefox`：

```
https://addons.mozilla.org/firefox/downloads/latest/mytab-for-firefox/
```

> 这个地址会 302 跳到真正带签名的 xpi 文件（`/firefox/downloads/file/<file_id>/<文件名>`）。
> **对 Unlisted 扩展同样有效**（已实测：某个 Unlisted 扩展的该地址返回 200 并正确跳转）。
>
> 想知道 slug 是什么？看 Developer Hub 里你的扩展页面 URL 末尾那一段，
> 或者扩展详情页的「Add-on URL」字段。

下载下来的文件名通常长这样（**名字不重要，有 `.xpi` 后缀就行**）：

```
mytab_local_mytab-3.0.1-signed.xpi
```

> ⚠️ **别解压它、别重新打包它。** AMO 的签名在 `META-INF/` 目录里，
> 一旦重新压缩，签名就失效，Firefox 会拒绝安装。

### 5.2 先验一下包对不对

```bash
python .iconfont/verify-signed-xpi.py "<下载路径>.xpi"
```

它会检查：有没有 Mozilla 签名、扩展 ID 对不对、`update_url` 在不在，并顺便算出
**发布时要写进 `updates.json` 的 sha256**。

期望输出：

```
[1] Mozilla 签名
  ✓ 签名文件齐全
  ✓ 含新版 cose 签名
[2] manifest
  id      : mytab@local.mytab
  version : 3.0.1
  ✓ 扩展 ID 正确
[3] 关键字段
  ✓ update_url = https://github.com/Albertzc/MyTab/releases/latest/download/updates.json
结论：✓ 这是可以安装的 AMO 签名包
```

> 如果第 [1] 步报「缺少签名文件」，说明下到的是本地构建包 —— **官方版 Firefox 装不了**
> （`MOZ_REQUIRE_SIGNING=true` 是编译进 `omni.ja` 的，改 `about:config` 无效）。

### 5.3 安装（官方版 Firefox 即可）

官方版 Firefox 装**签名过的**扩展没有任何障碍 —— 这正是走 AMO 签名的意义。

1. Firefox 地址栏输入 `about:addons` 回车
2. 点右上角**齿轮** ⚙ → **「从文件安装附加组件…」**
3. 选中刚才下载的 `.xpi` 文件
4. 弹窗点 **「添加」**

装完就生效，不用重启。

> **命令行等价写法**（可选）：
> ```powershell
> & "C:\Program Files\Mozilla Firefox\firefox.exe" -install-addon "C:\path\to\mytab-3.0.1-signed.xpi"
> ```

### 5.4 装完应该看到什么

| 操作 | 期望结果 |
|---|---|
| `Ctrl+T` | MyTab 页面（时钟 + 搜索 + 磁贴墙） |
| `Ctrl+N` 新窗口 | 也是 MyTab（靠 `chrome_settings_overrides.homepage` 生效） |
| 工具栏 🏠 主页按钮 | 也是 MyTab |
| 第一次开新标签页 | Firefox 弹一次提示：**「An extension, MyTab, changed the page you see when you open a new tab.」** —— 点「保留更改 / Keep changes」即可，这是**正常的告知**，不是错误 |
| `about:addons` 里 | 显示 **MyTab**，有齿轮可进设置 |

想改回去：Firefox 设置 → 主页 → 「新标签页」/「主页和新建窗口」改成「Firefox 主页」。

### 5.5 无痕窗口

想用 `Ctrl+Shift+P` 打开无痕窗口里的 MyTab，需要在
`about:addons` → MyTab → 齿轮 → **「允许在隐私窗口中运行」** 打开。

不打勾的话，无痕窗口的新标签页仍是 Firefox 自带的（这是 Firefox 的安全设计，不是 bug）。

---

## 6. 自托管更新（自动更新）

`manifest.json` 里已经写好：

```json
"update_url": "https://github.com/Albertzc/MyTab/releases/latest/download/updates.json"
```

所以每次发版要放两个文件到 GitHub Release：

| 文件 | 说明 |
|---|---|
| `mytab-3.0.1.xpi` | **AMO 签名后的**那份（不是本地 build 出来的未签名包） |
| `updates.json` | 更新清单，内容形如 |

```json
{
  "addons": {
    "mytab@local.mytab": {
      "updates": [
        {
          "version": "3.0.1",
          "update_link": "https://github.com/Albertzc/MyTab/releases/download/v3.0.1/mytab-3.0.1.xpi",
          "update_hash": "sha256:..."
        }
      ]
    }
  }
}
```

生成方式（先拿到 AMO 签名的 xpi，再算哈希）：

```bash
python .iconfont/build-xpi.py --signed-xpi /path/to/mytab-3.0.1.signed.xpi
```

> ⚠️ **`update_url` 一旦发出去就固定在已装版本里，改不动。**
> 所以第一版就要指向最终地址（现在指向 `releases/latest/download/updates.json`，
> 这个地址本身不用改，`latest` 会自动指向新 release）。

---

## 7. 提交后的发布流程

```
1. 打包（本地，未签名）
     python .iconfont/build-xpi.py
   → 得到 mytab-3.0.1.xpi（未签名）

2. 上传到 AMO「On your own」，等签名
   → 收到邮件，下载 signed xpi

3. 用签名包重算更新清单
     python .iconfont/build-xpi.py --signed-xpi mytab-3.0.1.signed.xpi

4. 创建 GitHub Release v3.0.1，挂上两个资产
     mytab-3.0.1.signed.xpi   （改名成 mytab-3.0.1.xpi）
     updates.json

5. 已装的用户在 24 小时内自动更新（Firefox 默认检查间隔）
```

> **为什么必须用签名包**：用户装的是 AMO 签名版，Firefox 对已签名扩展的更新
> 同样要求新文件带合法 Mozilla 签名，未签名包会被拒。

---

## 8. 容易踩的坑

| 坑 | 说明 |
|---|---|
| 别传未签名的 xpi | 本地 build 出来的包在官方版 Firefox 上装不上（`MOZ_REQUIRE_SIGNING` 是编译进 omni.ja 的，改 `about:config` 无效） |
| **别解压/重打包签名包** | AMO 签名在 `META-INF/` 里，重新 zip 会破坏签名，Firefox 直接拒绝安装 |
| 别把 `updates.json` 的哈希算在本地包上 | `update_hash` 必须用**签名包**算 —— 用户装的是签名版，Firefox 校验的也是签名包 |
| 别改扩展 ID | `mytab@local.mytab` 改了会丢用户数据 |
| 别删 `update_url` | 删了以后 Firefox 会去 AMO 找 Listed 版本，自托管用户就收不到更新了 |
| 别传 `prototype*.html` | 打包脚本的 `RUNTIME_FILES` 白名单只有 8 个文件，原型文件不该进包 |
| 别在 xpi 里放 `.preview/` | 截图属于 listing 素材，不属于运行时文件 |
