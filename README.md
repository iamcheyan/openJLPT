# OpenJLPT 📚

**OpenJLPT** 是一个专为 **电子墨水平板 (E-ink Devices)** 量身定制的、高性能、极致离线的 JLPT 全等级模拟考试平台。

本项目致力于提供一个**完全静态、无需后端、不依赖网络**的学习环境，让用户在纯净的墨水平面上专注于日语能力的提升。

---

![App Icon](assets/app_icon.png)

## ✨ 核心特性

- 🌚 **墨水平深度优化**：纯黑白极简 UI，高对比度设计，无动画刷新，适配各种 E-ink 屏（Kindle, Boox, 文石等）。
- 🎯 **全等级支持**：内置 N1 - N5 题库结构，完美对齐官方标准（如 N2 的 75 题配比），涵盖文字、语法、阅读全模块。
- 📱 **原生安卓客户端**：提供基于原生 WebView 封装的安卓壳子，支持全屏沉浸模式与本地文件系统访问。
- 🏮 **智能振假名 (Furigana)**：本地集成 `kuromoji.js` 引擎，离线实现汉字读音实时标注与切换。
- 📦 **极致离线静态架构**：
  - **静态运行**：无数据库、无 API 请求，所有逻辑在浏览器/WebView 端闭环。
  - **动静分离**：UI 引擎（壳子）与词库数据分离，通过拷贝 JSON 即可实现“热更新”，无需频繁重装 App。
- ☁️ **CI/CD 自动化构建**：集成 GitHub Actions，代码推送即在云端自动编译并产出安卓 APK。

---

## ⚠️ 重要声明 (Disclaimer)

- **AI 生成数据**：本项目题库中的所有题目、选项及解析均为 **AI (Large Language Models) 生成**。
- **无侵权风险**：由于题目非直接采集自历年真题或市面教辅，**不涉及任何知识产权纠纷**。
- **准确性提示**：虽然经过算法筛选，但 AI 生成内容可能存在极个别逻辑瑕疵或用法争议，仅供备考练习参考。

---

## 🚀 快速上手

### 1. 网页版/开发版
在根目录下运行简易服务器即可访问：
```bash
python3 server.py --port 8080
```

### 2. 安卓版 (WebView Shell)
- **云端构建**：推送代码到 GitHub 后，在 **Actions** 选项卡下载自动编译的 `openjlpt-debug-apk`。
- **智能同步 (Cloud Sync)**：
    - **自动下载**：App 内内置了云端补位逻辑。如果本地没有题库，它会**自动从 GitHub 加载**。这意味着你无需拷贝文件，开箱即用。
    - **离线部署 (可选)**：为了在完全断网环境下使用，你可以将 `data/` 文件夹拷贝到手机内存中。

```text
📁 手机内部存储 (Internal Storage)
   └── 📁 OpenJLPT
          └── 📁 data
                 ├── 📁 n1
                 ├── 📁 n2
                 └── ...
```
> [!TIP]
> 默认搜索路径为 `/sdcard/OpenJLPT/data`。如果你的设备挂载点不同，可以在 `MainActivity.java` 中修改 `window.DATA_ROOT` 的注入值。

### 3. 多端同步
```bash
python3 tools/sync_data.py user:password
```

---

## 🧠 题库管理与维护

项目内置了一套基于 AI 的题库自动修复与生成流程。

### 智能修复脚本
运行以下命令可以自动从词汇表生成高质量题目（带例句、详细解析及多模型审核）：
```bash
bash fix_vocab_data.sh
```

- **智能去重/同步**：启动时自动同步 JSON 题库与状态文件，跳过已完成词汇。
- **覆盖修复**：若发现旧题目缺少例句、解析过短或未经审核，会自动用 AI 生成的新版进行覆盖。
- **多模型协作**：集成 Gemini, DeepSeek, 智谱, 火山ARK 等模型，实现生成与交叉审核。

---

## 🛠 技术栈

- **Core**: Vanilla HTML5 / Modern JavaScript / CSS3
- **NLP**: [kuromoji.js](https://github.com/takuyaa/kuromoji.js) (Local Dictionary)
- **Android Shell**: Native Java WebView (File Access Enabled)
- **CI/CD**: GitHub Actions Build Pipeline

---

## 📂 项目目录

```text
├── android/            # 安卓原生外壳源码
├── assets/             # 核心引擎 (CSS, JS, 图标, 离线词典)
├── data/               # 题库数据 (N1-N5, JSON格式)
├── .github/workflows/  # GitHub Actions 自动打包脚本
├── index.html          # 动态练习生成引擎
├── full_exam.html      # 标准模拟卷预览
└── tools/              # 数据同步与辅助工具
```

---
*Created by [iamcheyan](https://github.com/iamcheyan)*
