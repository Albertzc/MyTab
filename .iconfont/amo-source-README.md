# MyTab — 源代码包说明

本包是 MyTab 扩展的**完整源代码**，用于 addons.mozilla.org（AMO）的源代码提交。

## 重要：MyTab 没有构建步骤

**扩展包（xpi）里的文件就是这些源文件本身，一个字节都没经过处理。**

- 没有代码压缩 / 混淆（无 uglify、terser、Closure Compiler 等）
- 没有打包合并（无 webpack、rollup、browserify、vite 等）
- 没有模板预编译（无 handlebars、jinja 等）
- 没有代码生成器参与扩展包的产出

因此 AMO 审阅员**不需要构建**，直接解压 xpi 就能逐行阅读全部逻辑。
扩展包内的文件与本包内的文件**完全一致**（逐字节相同）。

## 包内结构

```
manifest.json     扩展清单（MV3）
background.js     后台脚本：图标抓取、无痕窗口打开、收藏书签
index.html        新标签页页面结构
styles.css        样式
app.js            全部前端逻辑 + 内置分组图标数据（GROUP_ICONS）
icons/            扩展图标
  icon-48.png
  icon-96.png
  icon-128.png
```

`app.js` 顶部的 `GROUP_ICONS` 段是一段**静态数据**（134 个 Ant Design 单色 SVG 字符串），
由仓库里的 `.iconfont/build-group-icons.py` 生成后写回 `app.js`。
生成后的结果是普通的 JS 字面量数组，**审阅员可以直接阅读**，不构成「难以阅读的构建产物」，
也**不需要**为还原扩展包而执行任何构建命令。

## 如果审阅员需要比对

扩展包与本包的差异应当为**零**。比对方法：

1. 解压对应的 `mytab-<版本号>.xpi`（xpi 本质是 zip）
2. 与本包根目录下的同名文件逐个比对

两者应当完全相同。

## 运行环境

本扩展是**纯静态**的：HTML + CSS + 原生 JavaScript，无框架、无 npm 依赖、无运行时依赖。

审阅员不需要安装任何工具，任意文本编辑器打开 `app.js` / `background.js` 即可阅读。
（审阅环境的默认配置：Ubuntu 24.04 LTS、Node 24.14.0、npm 11.9.0 —— 本项目均不依赖。）

## 第三方代码

扩展内**不包含任何第三方 JavaScript 库**。

`app.js` 的 `GROUP_ICONS` 段内联的 SVG 路径来自 [iconfont「Ant Design 官方图标库」](https://www.iconfont.cn/collections/detail?cid=9402)（Ant Design 图标本身为 MIT 许可）。
SVG 路径是**数据**而非可执行代码。

## 许可

MIT，见仓库中的 `LICENSE`。
