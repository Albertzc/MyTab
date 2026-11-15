# .iconfont — 分组图标工具链

本目录**不属于扩展运行时**，只放图标下载 / 生成 / 打包 / 回归脚本。

分组图标来自 iconfont **「Ant Design 官方图标库」**（[cid=9402](https://www.iconfont.cn/collections/detail?cid=9402)，官方 / 免费，共 599 个图标）。其中大量是品牌 Logo、箭头和填充变体，因此从里面精选 **134 个**适合做分组 / 分类的图形（见 `curated-9402.json`），并补上中文名。

## 文件

| 文件 | 作用 |
|---|---|
| `collections/9402.json` | Ant Design 集合接口的原始响应（可离线复用） |
| `collections/42993.json` | 上一版「天猫好房」集合的原始响应（留档，用于旧图标 id 迁移对照） |
| `curated-9402.json` | 精选清单：英文图标名 + 中文显示名 |
| `build-group-icons.py` | 生成 `icons/groups/ad-*.svg` + `manifest.json`，并重写 `app.js` 的 `GROUP_ICONS` 段 |
| `build-xpi.py` | 打包 `mytab-<version>.xpi`（只含运行时文件），并**按改动内容自动判断版本号**（major / minor / patch） |
| `test/test.mjs` | jsdom 回归（181 项：图标渲染、中英文搜索、迁移、页面右键菜单、编辑态、点击空白退出、磁贴 / 分组 / 卡片拖拽排序、配置导入导出、搜索引擎的编辑增删、默认分组图标、24 小时制、默认背景 ocean、全部恢复默认） |
| `test/test-zip.mjs` | 备份压缩包回归（23 项：ZIP 结构、往返一致、图片字节保真、脏数据清洗） |
| `test/test-e2e.mjs` | 端到端演练（14 项：导出 → 落盘 → 新环境 → 导入还原） |
| `test/test-semver.py` | 版本判定单元测试（15 种典型改动的 SemVer 分级断言） |
| `test/render-preview.mjs` | 生成 `.preview/group-icons.png` 图标总览图（resvg-js） |

## 重新生成 / 调整图标

```bash
python .iconfont/build-group-icons.py
```

- 想增删图标：编辑 `curated-9402.json` 里的 `{ en, zh }`（`en` 必须是 iconfont 集合里的英文名）；
- 脚本会重写 `app.js` 中 `/* === GROUP_ICONS:START === */` 到 `/* === GROUP_ICONS:END === */` 之间的内容，**不要手改这一段**；
- 同时刷新 `icons/groups/` 下的 SVG、`manifest.json`，并删除上一套遗留的 SVG。

## 打包

```bash
python .iconfont/build-xpi.py
```

运行时文件清单写死在脚本里；新增运行时文件（例如新的 JS/CSS）需要同步加进去。

**版本号按语义化版本（SemVer）判定**：脚本把工作区的运行时文件与最近一个 `mytab-*.xpi` 逐个对比，再按**改动的性质**分级（不是按「新增了几个函数」这类代理信号）：

| 级别 | 语义 | 触发条件 |
|---|---|---|
| **major** | 破坏性变更 —— 旧数据 / 旧环境不再兼容 | manifest 的 `permissions` / `host_permissions` / `browser_specific_settings` 变化；localStorage 键名（`STORE_KEY` / `FAV_KEY`）变化；**移除**某个设置项或存储字段；删掉 JS 仍在引用的 DOM id（运行时会直接报错）；移除后台消息类型但页面仍在调用 |
| **minor** | 向后兼容的新功能 —— 老数据照常能用 | **新增**设置项 / 存储字段；index.html **新增** DOM id；**新增**后台消息类型 |
| **patch** | 向后兼容的修复 —— 不加功能、不动兼容面 | 样式、类名、文案、manifest 描述、修复类改动；纯内部重构（app.js 有改动但没有新增任何能力） |

- **运行时文件与上一个包完全一致 → 不升版本、也不打包**（不产生空版本）。
- 版本号取「自动升号」与「manifest 已预置版本」的较大者，保证永远大于已发布的包且不重复占用；打包后自动同步 `manifest.json`、`index.html`「关于」、`README.md` 里的包名与版本号。
- 判定逻辑有独立的单元测试：`python .iconfont/test/test-semver.py`（15 种典型改动的分级断言）。

常用参数：

```bash
python .iconfont/build-xpi.py --dry-run       # 只看改动与版本判断，不写文件、不打包
python .iconfont/build-xpi.py --bump minor     # 人工判断后强制指定升哪一级（覆盖自动判定）
python .iconfont/build-xpi.py --version 2.0.0  # 直接指定版本号
python .iconfont/build-xpi.py --no-bump        # 沿用 manifest 里的版本号，不自动升
```

每次打包的报告同时写入 `.preview/build-report.txt`（UTF-8）。

## 回归测试

```bash
cd .iconfont/test
pnpm install
node test.mjs
```

测试会启动一个本地静态服务器，用 jsdom 加载 `index.html`，覆盖首次运行、新建分组、图标搜索 / 选择、旧 emoji / 旧图标 id 迁移、页面右键菜单、编辑态切换、点击空白退出编辑、磁贴 / 分组 / 文件夹卡片拖拽排序、磁贴右键菜单、配置导出 / 导入（含脏数据清洗）、搜索引擎的编辑增删、默认分组图标、24 小时制、默认背景 ocean、全部恢复默认等 181 项检查。

备份压缩包另有独立回归（`node test-zip.mjs`，23 项），验证 ZIP 结构、往返一致与图片字节保真；`node test-e2e.mjs`（14 项）做「导出 → 落盘 → 全新环境 → 把压缩包喂回导入路径」的端到端演练。

被测项目根目录默认取仓库自身；也可以用环境变量 `MYTAB_ROOT` 指定（例如把测试脚本复制到别处运行时）：

```bash
MYTAB_ROOT=/path/to/MyTab node test.mjs
```

### 版本判定单元测试

```bash
python .iconfont/test/test-semver.py
```

用 15 种典型改动验证语义化版本的分级是否符合预期（纯样式 → patch、新增设置项 → minor、移除设置项 → major、删掉仍在引用的 DOM id → major 等）。

## 预览图

```bash
cd .iconfont/test
node render-preview.mjs   # 需要 resvg-js（已在 package.json）
```
