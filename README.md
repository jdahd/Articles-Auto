# Article with Auto and comfortable

一款优雅的微信公众号文章提取与转换工具。

Text Purifier 是一个基于 Python 和 CustomTkinter 构建的桌面应用程序，旨在帮助用户批量下载微信公众号文章（及知乎链接），并将其转换为 Markdown、HTML、Word 或思维导图格式，同时自动下载图片到本地，提供纯净的离线阅读体验。

## ✨ 主要功能

*   **批量提取**：支持多行链接批量处理，自动跳过重复链接。
*   **多格式导出**：
    *   **Markdown (.md)**：带有 YAML Frontmatter，适合导入 Obsidian、Notion 等笔记软件。
    *   **HTML (.html)**：包含排版样式的离线网页，图片本地化，物理移除隐藏样式。
    *   **Word (.docx)**：生成可编辑的文档（需安装对应库）。
    *   **MindMap (.mm)**：根据文章标题结构自动生成思维导图（支持 XMind/FreeMind）。
*   **纯净阅读**：智能去除广告、二维码、小程序卡片、推广文本等干扰元素。
*   **资源本地化**：自动下载文章中的图片到本地 `assets` 文件夹，防止防盗链失效。
*   **历史记录**：内置历史记录面板，支持搜索、预览、重新提取。
*   **剪贴板监控**：可选开启监控，复制链接即自动识别并下载。
*   **现代化 UI**：
    *   支持亮色/暗色（Dark Mode）主题切换。
    *   启动动画（Splash Screen）。
    *   支持拖拽 `.txt` 文件导入链接。
    *   自定义字体大小和代理设置。

## 🛠️ 安装与运行

### 1. 环境要求

请确保已安装 Python 3.8 或更高版本。

### 2. 安装依赖库

在项目根目录下运行以下命令安装所需的第三方库：

```bash
pip install customtkinter requests beautifulsoup4 html2text Pillow python-docx htmldocx pyperclip windnd
```

> **注意**：
> *   `windnd`：用于支持文件拖拽功能（Windows）。
> *   `pyperclip`：用于剪贴板监控功能。
> *   `htmldocx` / `python-docx`：用于 Word 导出功能。

### 3. 运行程序

```bash
python app.py
```

## 📖 使用指南

1.  **输入链接**：
    *   在主界面的输入框中粘贴文章链接（每行一个）。
    *   或者直接将包含链接的 `.txt` 文件拖入输入框。
    *   或者开启右上角的“监控”开关，复制链接自动填入。
2.  **选择保存位置**：点击“更改”按钮选择文件保存目录（默认为桌面）。
3.  **配置选项**：
    *   输入自定义标签（可选）。
    *   勾选需要的导出格式（Markdown, HTML, Word, MindMap）。
4.  **开始提取**：点击“开始提取并保存”按钮（或按 `Ctrl+S`）。
5.  **查看结果**：完成后可直接打开文件夹，或在“历史”面板中预览。

## ⚙️ 高级设置

点击主界面右上角的齿轮图标 ⚙️ 进入设置：
*   **代理设置**：支持 HTTP/SOCKS5 代理（例如 `http://127.0.0.1:7890`），解决部分网络访问问题。
*   **字体大小**：调整界面字体大小以适应不同分辨率屏幕。

## 📂 输出目录结构

```text
保存目录/
├── 2023-10/                  # 按月份归档
│   ├── assets/               # 图片资源文件夹
│   │   ├── 文章标题_img1.jpg
│   │   └── ...
│   ├── 文章标题.md           # Markdown 文件
│   ├── 文章标题.html         # HTML 文件
│   ├── 文章标题.docx         # Word 文件
│   └── 文章标题.mm           # 思维导图文件
└── ...
```

## ⚠️ 免责声明

本项目仅供学习和个人存档使用。请勿用于批量爬取、商业用途或侵犯版权的行为。使用者需自行承担使用本工具产生的所有责任。


# Article Purifier

[![GitHub stars](https://img.shields.io/github/stars/jdahd/Article-Purifier?style=social)](https://github.com/jdahd/Article-Purifier/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/jdahd/Article-Purifier?style=social)](https://github.com/jdahd/Article-Purifier/network/members)
[![GitHub license](https://img.shields.io/github/license/jdahd/Article-Purifier)](https://github.com/jdahd/Article-Purifier/blob/main/LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)

A clean, cross-platform desktop tool for **downloading, purifying, and converting WeChat Official Account articles** into structured formats (Markdown, HTML, Word, MindMap), with optional **local AI integration (Ollama)** for auto-summarization and keyword extraction.

> 🚧 **Future Roadmap**: This tool will evolve into a full-featured **Personal Local Knowledge Library** with bidirectional links, knowledge graph visualization, note-taking, and offline RAG. Stay tuned!

---

## ✨ Core Features
- 📥 **Single/Batch Download**: Download WeChat articles via URL, auto-skip duplicates
- 🧹 **Auto-Purification**: Remove ads, comments, irrelevant widgets, and preserve original content structure
- 📝 **Multi-Format Export**:
  - Markdown (with YAML Frontmatter, perfect for Obsidian/Notion)
  - HTML (with local images, offline viewable)
  - Word (.docx)
  - MindMap (OPML format, compatible with XMind/MindManager)
- 🖼️ **Local Image Download**: Auto-download and embed all images in articles
- 🤖 **Optional Local AI (Ollama)**:
  - Auto-generate 200-word summaries
  - Extract 3-5 core keywords
  - No internet required, no data leakage
- 🎨 **Clean GUI**: Built with CustomTkinter, supports light/dark mode
- 📦 **Portable EXE**: Packaged with PyInstaller, no Python installation needed for end-users

---

## 🛠️ Tech Stack
- **Core Language**: Python 3.8+
- **GUI**: CustomTkinter
- **Web Scraping**: BeautifulSoup4, Requests
- **Markdown Conversion**: html2text
- **PDF/Word Export**: WeasyPrint (PDF), python-docx (Word)
- **MindMap Generation**: xml.etree.ElementTree
- **Local AI**: Ollama API
- **Packaging**: PyInstaller

---

## 🚀 Quick Start

### Option 1: Use Portable EXE (Windows Only)
1. Go to the [Releases](https://github.com/jdahd/Article-Purifier/releases) page
2. Download the latest `Article-Purifier.exe`
3. Double-click to run (no installation required)

### Option 2: Run from Source Code (All Platforms)
#### Prerequisites
- Python 3.8 or higher
- (Optional) Ollama installed and running for local AI features

#### Steps
1. Clone the repository:
   ```bash
   git clone https://github.com/jdahd/Article-Purifier.git
   cd Article-Purifier

