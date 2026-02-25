import customtkinter as ctk
import os
import sys
import json # 引入记忆卡模块
from tkinter import filedialog, Menu, messagebox
import requests
import webbrowser
from bs4 import BeautifulSoup
import html2text
import datetime
import threading
import pathlib
from PIL import Image, ImageDraw # 新增：用于加载和绘制启动图
import time
import xml.etree.ElementTree as ET # 新增：用于生成思维导图
try:
    import pyperclip
except ImportError:
    pyperclip = None

try:
    import windnd
except ImportError:
    windnd = None # 如果没安装 windnd，就默默地禁用拖拽功能，不报错

# 资源路径辅助函数：让打包后的 exe 能找到内部的文件 (如图标)
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS # PyInstaller 创建的临时目录
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# 尝试引入 Word 导出库
try:
    from docx import Document
    from htmldocx import HtmlToDocx
except ImportError:
    HtmlToDocx = None

# ==========================================
# 0. 记忆存储系统 (记忆卡 V2.0 扩容版)
# ==========================================

def get_app_data_dir():
    """获取跨平台的应用数据目录，用于存放配置文件"""
    app_name = "TextPurifier"
    if sys.platform == "win32":
        # Windows: %APPDATA%\TextPurifier
        return os.path.join(os.environ["APPDATA"], app_name)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/TextPurifier
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", app_name)
    else:
        # Linux: ~/.config/TextPurifier
        return os.path.join(os.path.expanduser("~"), ".config", app_name)

APP_DATA_DIR = get_app_data_dir()
os.makedirs(APP_DATA_DIR, exist_ok=True) # 启动时确保目录存在
CONFIG_FILE = os.path.join(APP_DATA_DIR, "config.json")

# 用一个全局字典来管理软件所有的记忆
app_config = {
    "save_path": os.path.join(os.path.expanduser("~"), "Desktop"),
    "history": [], # 新增：用来存最近抓取过的文章记录
    "history_window_size": "500x500", # 默认历史窗口尺寸
    "proxy": "", # 新增：代理服务器地址
    "font_size": 13 # 新增：全局基础字体大小
}

def load_config():
    global app_config
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "save_path" in data and os.path.exists(data["save_path"]):
                    app_config["save_path"] = data["save_path"]
                if "history" in data:
                    app_config["history"] = data["history"]
                if "history_window_size" in data:
                    app_config["history_window_size"] = data["history_window_size"]
                if "proxy" in data:
                    app_config["proxy"] = data["proxy"]
                if "font_size" in data:
                    app_config["font_size"] = data["font_size"]
        except:
            pass
    return app_config["save_path"]

def save_config():
    # 每次保存时，把整个 app_config 字典写进 json
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        # indent=4 会让 json 文件排版很漂亮，你可以用记事本打开看看
        json.dump(app_config, f, ensure_ascii=False, indent=4) 

# 启动时读取记忆
current_save_path = load_config()

# ==========================================
# 1.1 全局字体定义 (基于配置)
# ==========================================
FONT_MAIN = "Microsoft YaHei UI"
BASE_FONT_SIZE = app_config.get("font_size", 13)

# 定义各种UI元素的字体大小
FONT_TITLE = (FONT_MAIN, BASE_FONT_SIZE + 19, "bold")
FONT_SUBTITLE = (FONT_MAIN, BASE_FONT_SIZE + 1)
FONT_TEXTBOX = (FONT_MAIN, BASE_FONT_SIZE + 1)
FONT_HISTORY_TITLE = (FONT_MAIN, BASE_FONT_SIZE + 1, "bold")
FONT_NORMAL_BOLD = (FONT_MAIN, BASE_FONT_SIZE, "bold")
FONT_NORMAL = (FONT_MAIN, BASE_FONT_SIZE)
FONT_SMALL_BOLD = (FONT_MAIN, BASE_FONT_SIZE - 1, "bold")
FONT_SMALL = (FONT_MAIN, BASE_FONT_SIZE - 1)
FONT_LARGE_BOLD = (FONT_MAIN, BASE_FONT_SIZE + 3, "bold")
FONT_ICON = (FONT_MAIN, BASE_FONT_SIZE + 3)

# ==========================================
# 1. 视觉设计语言 (双模自动适配)
# ==========================================
ctk.set_appearance_mode("light") # 默认初始为亮色

# 魔法：用元组定义颜色 ("白天模式颜色", "黑夜模式颜色")
BG_COLOR = ("#F8F9FA", "#111827")       # 极简灰白 / 深邃夜空
INPUT_BG = ("#FFFFFF", "#1F2937")       # 纯净白 / 磨砂黑
TEXT_MAIN = ("#1F2937", "#F9FAFB")      # 深灰黑 / 亮白
TEXT_SUB = ("#6B7280", "#9CA3AF")       # 次级灰
BORDER_COLOR = ("#E5E7EB", "#374151")   # 极细边框
ACCENT_COLOR = ("#6366F1", "#818CF8")   # 靛青色 (Indigo) - 更高级的蓝紫色调
HOVER_COLOR = ("#4F46E5", "#6366F1")    # 悬停色
BTN_GRAY = ("#FFFFFF", "#1F2937")       # 次级按钮改为卡片式
BTN_GRAY_HOVER = ("#F3F4F6", "#374151") 

app = ctk.CTk()
app.withdraw() # 1. 启动时先隐藏主窗口，等 Splash 播放完再显示
app.configure(fg_color=BG_COLOR) # 应用大背景
app.geometry("900x750")
app.title("Text Purifier")
app.resizable(True, True)
app.minsize(900, 750)

# 设置窗口图标 (运行时左上角和任务栏显示的图标)
try:
    app.iconbitmap(resource_path("logo.ico"))
except:
    pass # 如果找不到图标文件，就用默认的，不报错

# ==========================================
# 1.5 启动画面 (Splash Screen)
# ==========================================
def show_splash():
    # 创建无边框窗口
    splash = ctk.CTkToplevel(app)
    splash.overrideredirect(True)
    splash.attributes('-topmost', True)
    
    # --- 1. 设置透明背景 (实现圆角窗口的关键) ---
    # 选一个极少用的颜色作为透明色 (比如亮黄色 #FFFF01)
    transparent_color = "#FFFF01"
    splash.configure(fg_color=transparent_color)
    try:
        splash.attributes('-transparentcolor', transparent_color)
    except:
        pass
    
    # 设定尺寸和位置 (居中)
    w, h = 500, 300
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = (screen_w - w) // 2
    y = (screen_h - h) // 2
    splash.geometry(f"{w}x{h}+{x}+{y}")
    
    # --- 2. 创建圆角容器 ---
    # 所有的内容都放在这个 frame 里，而不是直接放在 splash 窗口上
    splash_frame = ctk.CTkFrame(splash, width=w, height=h, corner_radius=20, fg_color="#6366F1")
    splash_frame.pack(fill="both", expand=True)
    
    # 尝试加载 splash.png，如果没有就显示纯色背景+文字
    img_path = resource_path("splash.png")
    image_loaded = False
    
    if os.path.exists(img_path):
        try:
            pil_img = Image.open(img_path)
            # 自动给图片裁切圆角，防止直角图片挡住窗口圆角
            pil_img = pil_img.convert("RGBA")
            mask = Image.new("L", pil_img.size, 0)
            ImageDraw.Draw(mask).rounded_rectangle([(0, 0), pil_img.size], radius=20, fill=255)
            pil_img.putalpha(mask)
            
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(w, h))
            ctk.CTkLabel(splash_frame, text="", image=ctk_img).pack(fill="both", expand=True)
            image_loaded = True
        except:
            pass
            
    if not image_loaded:
        # 默认样式：显示软件名
        ctk.CTkLabel(splash_frame, text="Text Purifier", font=(FONT_MAIN, 32, "bold"), text_color="white").pack(expand=True)

    # --- 3. 状态文本和进度条 ---
    status_text_label = ctk.CTkLabel(splash_frame, text="", font=FONT_SMALL)
    progress = ctk.CTkProgressBar(splash_frame, width=360, height=8, corner_radius=4)
    progress.set(0)
    
    if image_loaded:
        # 有图片时，文字和进度条都悬浮在底部
        status_text_label.place(relx=0.5, rely=0.85, anchor="center")
        status_text_label.configure(text_color="white") # 在图片上用白色文字
        progress.place(relx=0.5, rely=0.9, anchor="center")
        progress.configure(fg_color="#333333", progress_color="#10B981")
    else:
        # 默认样式时，文字和进度条放在底部
        status_text_label.pack(pady=(0, 10))
        status_text_label.configure(text_color="#E0E7FF") # 适配 Indigo 主题的亮色
        progress.pack(pady=(0, 50))
        progress.configure(fg_color="#4F46E5", progress_color="#FFFFFF")
        
    # --- 4. 动画逻辑 (带状态更新) ---
    loading_steps = [
        (0.0, "正在初始化..."),
        (0.3, "加载用户配置..."),
        (0.6, "渲染UI组件..."),
        (0.9, "准备就绪..."),
    ]

    def animate_loading(val=0, step_index=0):
        if val < 1.05: # 稍微多一点确保跑满
            # 检查是否需要更新状态文本
            if step_index < len(loading_steps) and val >= loading_steps[step_index][0]:
                status_text_label.configure(text=loading_steps[step_index][1])
                step_index += 1

            val += 0.02 # 每次增加 2%
            progress.set(min(val, 1.0))
            splash.after(25, lambda: animate_loading(val, step_index)) # 25ms 刷新一次
        else:
            splash.destroy()
            app.deiconify()
            
    # 延迟一点启动动画，确保窗口完全画好
    splash.after(200, lambda: animate_loading())

show_splash()

# ==========================================
# 2. 主题切换器逻辑
# ==========================================
def toggle_theme():
    if theme_switch.get() == 1:
        theme_switch.configure(text="🌙 Dark")
        mode = "dark"
    else:
        theme_switch.configure(text="☀️ Light")
        mode = "light"
        
    # 强制刷新 UI 确保开关动画流畅，并将延迟缩短到 50ms 提升响应速度
    app.update_idletasks()
    
    def apply_theme():
        ctk.set_appearance_mode(mode)
        app.lift() # 关键修复：切换主题后把窗口提上来，防止“下沉”
    app.after(50, apply_theme)

# ==========================================
# 2.1 内置文档内容 (README)
# ==========================================
README_CONTENT = """
# ✨ 微信文章一键永久保存工具 (Text Purifier)

**宝子们！还在手动复制粘贴公众号文章吗？😭**
**文章被删了看不了怎么办？图片过期了裂开怎么办？**

这款 **完全免费** 的神仙软件，帮你 **一键批量下载** 微信公众号文章，自动排版，图片永久保存到本地！再也不怕文章失效啦！💖

---

## 🌟 为什么你需要它？

*   **小白神器**：不需要懂代码，不需要安装环境，**双击 exe 就能用**！
*   **永久收藏**：文章和图片全部下载到你的电脑里，断网也能看，原作者删文也不怕！📂
*   **自动排版**：智能去除广告、二维码、推广卡片，只留最干净的正文，阅读体验满分！✨
*   **格式超全**：
    *   📄 **Word文档**：可以直接编辑修改，打工人必备。
    *   🌐 **HTML网页**：原汁原味还原排版，离线也能看。
    *   🧠 **思维导图**：自动把文章标题生成导图，学习党狂喜！
    *   📝 **Markdown**：笔记软件（Notion/Obsidian）用户最爱。

---

## 🚀 傻瓜式使用教程

### 第一步：打开软件
双击文件夹里的 `Text Purifier.exe` (那个蓝色图标) 启动。
*(注意：请解压整个压缩包后再运行，不要直接在压缩包里点哦！)*

### 第二步：放入链接
有两种超简单的方法：
1.  **复制粘贴**：把文章链接复制，粘贴到软件的大白框里（一行一个，支持批量哦！）。
2.  **自动监控**（推荐🔥）：打开右上角的 **“📋 监控”** 开关，然后你在微信/知乎里 **复制链接**，软件就会自动识别并填入，超级省心！

### 第三步：一键保存
点击大大的 **“开始提取并保存”** 按钮。
等进度条跑完，软件会自动弹窗提示，点击“是”就能直接打开保存的文件夹啦！🎉

---

## ⚙️ 宝藏功能

*   **拖拽导入**：有一个存满链接的 `.txt` 文件？直接拖进软件里就能识别！
*   **夜间模式**：点击右上角的 `☀️ Light` 切换成深色模式，晚上用不刺眼。
*   **历史记录**：点 `📜 历史` 按钮，之前下载过的文章都在这，随时可以找回。

---

## ⚠️ 常见问题 (Q&A)

**Q: 软件打不开怎么办？**
A: 请确保你解压了整个压缩包，不要只把 `.exe` 拖出来，它需要旁边的文件夹支持哦。

**如果觉得好用，记得分享给身边的集美/兄弟们哦！绝绝子！👍**
"""

def show_readme():
    readme_win = ctk.CTkToplevel(app)
    readme_win.geometry("850x650")
    readme_win.title("📖 使用说明")
    readme_win.attributes("-topmost", True)
    
    textbox = ctk.CTkTextbox(readme_win, font=FONT_NORMAL, wrap="word")
    textbox.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 获取当前主题模式，用于适配 Markdown 样式颜色
    is_dark = ctk.get_appearance_mode() == "Dark"
    accent = ACCENT_COLOR[1] if is_dark else ACCENT_COLOR[0]
    code_bg = "#374151" if is_dark else "#E5E7EB"

    # --- 配置 Markdown 样式标签 ---
    textbox._textbox.tag_config("h1", font=(FONT_MAIN, BASE_FONT_SIZE + 8, "bold"), spacing1=20, spacing3=10, foreground=accent)
    textbox._textbox.tag_config("h2", font=(FONT_MAIN, BASE_FONT_SIZE + 4, "bold"), spacing1=15, spacing3=5)
    textbox._textbox.tag_config("h3", font=(FONT_MAIN, BASE_FONT_SIZE + 2, "bold"), spacing1=10, spacing3=2)
    textbox._textbox.tag_config("bold", font=(FONT_MAIN, BASE_FONT_SIZE, "bold")) # 加粗样式
    textbox._textbox.tag_config("code", font=("Consolas", BASE_FONT_SIZE - 1), background=code_bg, lmargin1=20, lmargin2=20)
    textbox._textbox.tag_config("list", lmargin1=20, lmargin2=20, spacing1=5)
    textbox._textbox.tag_config("sep", justify="center", foreground="#9CA3AF", spacing1=10, spacing3=10) # 分割线

    # 直接使用内置的文档内容
    content = README_CONTENT.strip()
            
    # --- 升级版 Markdown 解析渲染 ---
    lines = content.split('\n')
    in_code_block = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # 1. 处理代码块
        if line_stripped.startswith("```"):
            in_code_block = not in_code_block
            continue 
        if in_code_block:
            textbox.insert("end", line + "\n", "code")
            continue
            
        # 2. 处理分割线
        if line_stripped == "---":
            textbox.insert("end", "──────────────────────────\n", "sep")
            continue

        # 3. 处理标题 (移除 # 号)
        current_tags = []
        text_to_show = line + "\n"
        
        if line.startswith("# "):
            current_tags.append("h1")
            text_to_show = line[2:] + "\n"
        elif line.startswith("## "):
            current_tags.append("h2")
            text_to_show = line[3:] + "\n"
        elif line.startswith("### "):
            current_tags.append("h3")
            text_to_show = line[4:] + "\n"
        
        # 4. 处理列表 (移除 * 号，换成圆点)
        elif line_stripped.startswith("* ") or line_stripped.startswith("- "):
            current_tags.append("list")
            # 保持缩进，但把 * 换成 •
            text_to_show = line.replace("* ", "• ", 1).replace("- ", "• ", 1) + "\n"

        # 5. 处理加粗 (**文字**) - 简单的行内解析
        # 将文本按 ** 分割，偶数索引是普通文本，奇数索引是加粗文本
        parts = text_to_show.split("**")
        for i, part in enumerate(parts):
            # 基础标签 + (如果是奇数位则追加 bold 标签)
            final_tags = tuple(current_tags)
            if i % 2 == 1: 
                final_tags = final_tags + ("bold",)
            
            textbox.insert("end", part, final_tags)

    textbox.configure(state="disabled")

def show_about():
    messagebox.showinfo("关于", "Text Purifier v1.0\n\n专注微信文章的工具。\n\n支持多格式导出。Designed by jux")

# 辅助函数：同时更新进度条和百分比文字
def set_progress(val):
    progress_bar.set(val)
    progress_label.configure(text=f"{int(val * 100)}%")

# 辅助函数：安全更新状态栏 (解决 NameError)
def safe_update_status(text, color):
    app.after(0, lambda: status_label.configure(text=text, text_color=color))

# --- 新增：悬浮提示 (Tooltip) 逻辑 ---
# 用一个全局变量来暂存显示悬浮提示前的状态栏信息
previous_status_info = {"text": "", "color": ""}

def add_tooltip(widget, text):
    """为组件绑定悬浮事件，在状态栏显示帮助文字"""
    def on_enter(event):
        global previous_status_info
        current_text = status_label.cget("text")
        # 只有当状态栏不是一个提示时，才保存当前状态
        if not current_text.startswith("💡"):
            previous_status_info["text"] = current_text
            previous_status_info["color"] = status_label.cget("text_color")
        
        safe_update_status(f"💡 {text}", TEXT_SUB)

    def on_leave(event):
        global previous_status_info
        # 恢复之前的状态
        safe_update_status(previous_status_info["text"], previous_status_info["color"])

    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

# ==========================================
# 2.5 设置面板
# ==========================================
def open_settings_panel():
    settings_win = ctk.CTkToplevel(app)
    settings_win.geometry("400x320")
    settings_win.title("⚙️ 设置")
    settings_win.attributes("-topmost", True)
    settings_win.resizable(False, False)

    # 代理设置
    proxy_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
    proxy_frame.pack(fill="x", padx=20, pady=(20, 10))

    ctk.CTkLabel(proxy_frame, text="HTTP/SOCKS5 代理:", font=FONT_NORMAL_BOLD).pack(anchor="w")
    proxy_entry = ctk.CTkEntry(proxy_frame, placeholder_text="例如: http://127.0.0.1:7890 或 socks5://127.0.0.1:1080", font=FONT_SMALL)
    proxy_entry.pack(fill="x", pady=(5, 10))
    proxy_entry.insert(0, app_config.get("proxy", ""))

    # 字体大小设置
    font_settings_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
    font_settings_frame.pack(fill="x", padx=20, pady=10)
    ctk.CTkLabel(font_settings_frame, text="界面字体大小:", font=FONT_NORMAL_BOLD).pack(anchor="w")
    
    font_slider_frame = ctk.CTkFrame(font_settings_frame, fg_color="transparent")
    font_slider_frame.pack(fill="x", pady=(5, 10))

    font_size_label = ctk.CTkLabel(font_slider_frame, text=str(app_config.get("font_size", 13)), font=FONT_NORMAL, width=30)
    font_size_label.pack(side="right")

    def update_font_label(value):
        font_size_label.configure(text=str(int(value)))

    font_size_slider = ctk.CTkSlider(font_slider_frame, from_=11, to=16, number_of_steps=5, command=update_font_label)
    font_size_slider.set(app_config.get("font_size", 13))
    font_size_slider.pack(fill="x", expand=True, side="left")

    # 按钮
    btn_frame = ctk.CTkFrame(settings_win, fg_color="transparent")
    btn_frame.pack(fill="x", padx=20, pady=10, side="bottom")

    def save_settings():
        old_font_size = app_config.get("font_size", 13)
        new_font_size = int(font_size_slider.get())

        app_config["proxy"] = proxy_entry.get().strip()
        app_config["font_size"] = new_font_size
        save_config()
        safe_update_status("⚙️ 设置已保存", TEXT_SUB)
        settings_win.destroy()

        if old_font_size != new_font_size:
            messagebox.showinfo("提示", "字体大小设置已保存。\n需要重启软件才能生效。")

    ctk.CTkButton(btn_frame, text="保存", command=save_settings, fg_color=ACCENT_COLOR, hover_color=HOVER_COLOR).pack(side="right")
    ctk.CTkButton(btn_frame, text="取消", command=settings_win.destroy, fg_color=BTN_GRAY, hover_color=BTN_GRAY_HOVER).pack(side="right", padx=(0, 10))

# ==========================================
# 3. 核心抓取逻辑 (多线程批量升级版)
# ==========================================
def process_downloads_thread(urls, export_md, export_html, export_docx, export_mm, user_tags):
    """这是后台工人的车间，专门负责干苦力，不影响界面"""
    total = len(urls)
    success_count = 0
    
    # --- 新增：加载代理设置 ---
    proxies = None
    proxy_url = app_config.get("proxy", "").strip()
    if proxy_url:
        proxies = {
            "http": proxy_url,
            "https": proxy_url,
        }

    # 开始循环处理每一个链接
    for i, url in enumerate(urls):
        url = url.strip()
        if not url: continue # 如果是空行，跳过
        
        # --- 新增：防重复检测 (如果历史记录里已经有了，就跳过) ---
        if any(item.get("url") == url for item in app_config["history"]):
            status_label.configure(text=f"⚠️ 此链接已添加过，跳过 ({i+1}/{total})", text_color="#E0AF68")
            app.after(0, lambda v=((i + 1) / total): set_progress(v))
            continue
        
        # 让后台工人通知界面更新进度
        status_label.configure(text=f"⏳ 正在提取 ({i+1}/{total})，请稍候...", text_color="#E0AF68")
        app.after(0, lambda v=(i / total): set_progress(v))
        
        try:
            # --- 核心抓取代码（和之前一模一样）---
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            response = requests.get(url, headers=headers, proxies=proxies, timeout=15)
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            title_tag = soup.find('h1', class_='rich_media_title')
            title = title_tag.get_text().strip() if title_tag else "未命名文章"
            author_tag = soup.find('a', id='js_name')
            author_name = author_tag.get_text().strip() if author_tag else "未知公众号"
            save_date = datetime.datetime.now().strftime("%Y-%m-%d")
            safe_title = title.replace('/', '_').replace('\\', '_').replace('|', '_')
            
            content_div = soup.find('div', id='js_content')
            
            if not content_div:
                print(f"[{url}] 未找到正文")
                app.after(0, lambda v=((i + 1) / total): set_progress(v))
                continue # 找不到正文就算了，直接抓下一篇！
            
            content_div = soup.find('div', id='js_content')
            if not content_div:
                print(f"[{url}] 未找到正文")
                continue 
            
            # === 核心破解：扒掉微信正文的“隐身衣” ===
            if content_div.has_attr('style'):
                del content_div['style']  # 物理删除隐藏样式
            # ========================================

            # --- 新增：智能广告与冗余信息清洗 (DOM 树裁剪) ---
            # 1. 物理消灭已知组件：干掉所有微信小程序卡片、视频号名片、语音等多媒体干扰
            for bad_tag in content_div.find_all(['mp-miniprogram', 'mp-common-profile', 'mpvoice']):
                bad_tag.decompose()
                
            # 2. 语义消灭推广文本：定义一个“垃圾词黑名单”
            trash_keywords = ["阅读原文", "喜欢此内容的人还喜欢", "长按扫码", "关注公众号", "点击上方卡片", "扫码关注"]
            
            # 遍历文章里所有的段落 <p> 和区块 <section>
            for tag in content_div.find_all(['p', 'section']):
                # 把里面的文字提取出来，去掉空格
                text = tag.get_text().replace(" ", "").replace("\n", "").strip()
                
                # 如果这句话里包含了黑名单里的词，并且这句话不是很长（防止误杀包含了这些词的正常长篇大论）
                if len(text) < 30:
                    for kw in trash_keywords:
                        if kw in text:
                            tag.decompose() # 毫不留情地从内存中销毁这个段落
                            break # 这个段落已经没了，跳出当前循环，去检查下一个段落
            # --------------------------------------------------

            current_month = datetime.datetime.now().strftime("%Y-%m")
            final_save_dir = os.path.join(current_save_path, current_month)
            os.makedirs(final_save_dir, exist_ok=True) 
            assets_dir = os.path.join(final_save_dir, "assets")
            os.makedirs(assets_dir, exist_ok=True) 
            full_file_path = os.path.join(final_save_dir, f"{safe_title}.md") 
                
            img_counter = 1
            for img in content_div.find_all('img'):
                real_url = img.get('data-src') or img.get('src')
                if real_url:
                    try:
                        img_filename = f"{safe_title}_img{img_counter}.jpg"
                        img_full_path = os.path.join(assets_dir, img_filename)
                        img_response = requests.get(real_url, headers=headers, timeout=10, proxies=proxies)
                        with open(img_full_path, 'wb') as img_file:
                            img_file.write(img_response.content)
                        img['src'] = f"./assets/{img_filename}"
                        img_counter += 1
                    except Exception:
                        img['src'] = real_url
                    
            converter = html2text.HTML2Text()
            converter.ignore_links = False
            converter.body_width = 0
            markdown_content = converter.handle(str(content_div))
            
            # --- 处理标签 ---
            tags_list = ["微信摘录", "待阅读"]
            if user_tags:
                # 支持中文逗号和英文逗号，自动去空格
                extras = [t.strip() for t in user_tags.replace("，", ",").split(",") if t.strip()]
                tags_list.extend(extras)
            tags_str = ", ".join(tags_list)
            
            yaml_frontmatter = f"---\ntitle: \"{title}\"\nauthor: \"{author_name}\"\nsource: \"{url}\"\ndate_saved: \"{save_date}\"\ntags: [{tags_str}]\n---\n\n"
            
            # 1. 保存 Markdown
            if export_md:
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(yaml_frontmatter)
                    f.write(f"# {title}\n\n")
                    f.write(markdown_content)
            
            # 准备 HTML 内容 (用于 HTML 导出和 PDF 生成)
            html_style = "<style>body{max-width:800px;margin:40px auto;padding:0 20px;line-height:1.6;color:#333;font-family:sans-serif;}img{max-width:100%;height:auto;display:block;margin:20px auto;}</style>"
            html_content = f"<html><head><meta charset='utf-8'><title>{title}</title>{html_style}</head><body><h1>{title}</h1>{str(content_div)}</body></html>"

            # === 2. 保存极简 HTML (物理破解微信隐身衣版) ===
            html_file_path = full_file_path.replace(".md", ".html")
            
            # 物理魔法：既然它是对象，我们直接强行修改它的 style 属性！
            if content_div.has_attr('style'):
                content_div['style'] = "visibility: visible; opacity: 1; display: block;"
            else:
                # 就算它没有 style，我们也硬塞一个可见属性进去以防万一
                content_div['style'] = "visibility: visible; opacity: 1; display: block;"

            with open(html_file_path, 'w', encoding='utf-8') as f:
                f.write(f"<html><head><meta charset='utf-8'><title>{title}</title>")
                # 加上排版 CSS
                ultimate_css = """
                <style>
                    body { max-width:800px; margin:40px auto; padding:0 20px; line-height:1.6; color:#333; font-family:sans-serif; }
                    img { max-width:100%; height:auto; display:block; margin:20px auto; border-radius:8px; }
                </style>
                """
                f.write(f"{ultimate_css}</head>")
                # 这时候的 str(content_div) 里的 style 已经被我们彻底改写成 visible 了！
                f.write(f"<body><h1>{title}</h1>{str(content_div)}</body></html>")
            # ==========================================


            # 4. 保存 Word (docx)
            if export_docx and HtmlToDocx:
                docx_file_path = full_file_path.replace(".md", ".docx")
                try:
                    doc = Document()
                    new_parser = HtmlToDocx()
                    # 构造 Word 需要的 HTML (处理图片路径为绝对路径，确保 Word 能找到图片)
                    abs_assets_dir = assets_dir.replace("\\", "/")
                    if not abs_assets_dir.endswith("/"): abs_assets_dir += "/"
                    word_html = str(content_div).replace('src="./assets/', f'src="{abs_assets_dir}')
                    
                    doc.add_heading(title, 0) # 添加大标题
                    new_parser.add_html_to_document(word_html, doc)
                    doc.save(docx_file_path)
                except Exception as e:
                    print(f"Word 导出失败: {e}")

            # 5. 保存思维导图 (.mm)
            if export_mm:
                mm_file_path = full_file_path.replace(".md", ".mm")
                try:
                    # 创建根节点
                    root = ET.Element("map", version="1.0.1")
                    main_node = ET.SubElement(root, "node", TEXT=title)
                    
                    # 简单的层级堆栈算法
                    # 初始堆栈包含根节点，假设它的层级是 0
                    stack = [{"level": 0, "node": main_node}]
                    
                    # 查找正文中的所有标题 (h1-h6)
                    headers = content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    
                    if not headers:
                        ET.SubElement(main_node, "node", TEXT="（此文章未检测到目录结构）")
                    
                    for h in headers:
                        try:
                            current_level = int(h.name[1]) # h1->1, h2->2
                        except:
                            current_level = 2
                            
                        text = h.get_text().strip()
                        if not text: continue
                        if len(text) > 50: text = text[:50] + "..." # 限制节点文字长度
                        
                        # 回溯堆栈：找到当前标题的“父级”
                        while len(stack) > 1 and stack[-1]["level"] >= current_level:
                            stack.pop()
                        
                        parent = stack[-1]["node"]
                        new_node = ET.SubElement(parent, "node", TEXT=text)
                        stack.append({"level": current_level, "node": new_node})
                        
                    tree = ET.ElementTree(root)
                    tree.write(mm_file_path, encoding="utf-8", xml_declaration=True)
                except Exception as e:
                    print(f"MindMap error: {e}")

            success_count += 1 
            
            # === 新增：往记忆卡里写历史记录 ===
            # 把这篇成功抓取的文章信息（标题、链接、时间）插到列表的第 0 个位置（最前面）
            app_config["history"].insert(0, {"title": title, "url": url, "date": save_date})
            # 只保留最近的 20 条，防止日记本太厚拖慢程序
            app_config["history"] = app_config["history"][:20]
            save_config() # 立刻存入硬盘！
            # ==================================
            
        except Exception as e:
            print(f"[{url}] 出错: {e}")
            # 出错了也没关系，后台工人会自动继续处理下一篇！
            
        # 本次循环结束，更新进度条
        app.after(0, lambda v=((i + 1) / total): set_progress(v))
            
    # --- 循环结束：所有链接都处理完了 ---
    # 安全锁 2：把更新界面和清空输入框的工作，交回给主线程（app.after）去执行，绝对不会卡死或静默失败！
    def update_ui_on_finish():
        global is_processing
        is_processing = False 
        if success_count == 0 and total > 0:
            status_label.configure(text="⚠️ 没有新文章被保存 (可能已存在)", text_color="#E0AF68")
        else:
            status_label.configure(text=f"✅ 批量完成！共成功处理 {success_count}/{total} 篇", text_color=("#10B981", "#9ECE6A"))
            
        download_btn.configure(state="normal", text="已完成提取并保存")
        # progress_bar.pack_forget() # 任务完成后不再隐藏进度条
        
        # 只要有一篇抓取成功，就自动清空输入框，从根源上防止你二次误触重复保存！
        if success_count > 0:
            url_textbox.delete("0.0", "end")
            # 弹窗询问 (这是一个非常贴心的产品细节)
            if messagebox.askyesno("任务完成", f"成功提取 {success_count} 篇文章！\n是否立即打开文件夹查看？"):
                os.startfile(os.path.join(current_save_path, datetime.datetime.now().strftime("%Y-%m")))

    # 0 毫秒后，立刻让主线程执行上面的 update_ui_on_finish 函数
    app.after(0, update_ui_on_finish)

def start_download():
    """这是主线程老板，只负责接单，然后分配给工人"""
    # 0. 防止快捷键重复触发 (如果正在处理中，直接无视)
    if download_btn.cget("state") == "disabled":
        return

    # 1. 把文本框里的提示文字先清理掉（如果你忘了删的话）
    raw_text = url_textbox.get("0.0", "end").replace("批量模式：在此处粘贴链接，每行一个...", "")
    
    # 2. 提取出所有包含 "http" 的真实链接，放进一个列表里
    urls = [line.strip() for line in raw_text.split('\n') if "http" in line]
    
    if not urls:
        status_label.configure(text="提示：请先粘贴有效的链接", text_color="#F7768E")
        return
        
    # 获取导出选项
    save_md = chk_md.get()
    save_html = chk_html.get()
    save_docx = chk_docx.get()
    save_mm = chk_mm.get()
    
    # 获取用户输入的标签
    user_tags = tags_entry.get()

    # 老板把按钮变灰，防止你连续狂点
    download_btn.configure(state="disabled", text="流水线运转中...")
    
    # 重置进度条
    set_progress(0)
    
    # 3. 核心魔法：召唤一个后台线程，把 urls 列表扔给它去干活
    thread = threading.Thread(target=process_downloads_thread, args=(urls, save_md, save_html, save_docx, save_mm, user_tags))
    # 设为守护线程（意味着如果你关掉软件，后台下载也会立刻停止，不会在电脑后台变成幽灵）
    thread.daemon = True 
    thread.start()

# ==========================================
# 4. 历史记录独立面板 (悬浮窗口)
# ==========================================
def open_history_panel():
    # 召唤一个独立的子窗口
    history_win = ctk.CTkToplevel(app)
    
    # 读取记忆中的尺寸，如果没有则默认 500x500
    current_size = app_config.get("history_window_size", "500x500")
    history_win.geometry(current_size)
    
    history_win.title("📜 抓取历史")
    history_win.attributes("-topmost", True) # 霸道一点，让这个窗口永远悬浮在最前面
    
    # --- 新增：保存窗口尺寸的函数 ---
    def save_win_size():
        # geometry() 返回 "WxH+X+Y"，我们只需要 "WxH" (尺寸)，不需要位置
        app_config["history_window_size"] = history_win.geometry().split("+")[0]
        save_config()

    # 绑定关闭窗口事件 (点击右上角叉号时触发)
    history_win.protocol("WM_DELETE_WINDOW", lambda: (save_win_size(), history_win.destroy()))
    
    # --- 搜索框区域 ---
    search_frame = ctk.CTkFrame(history_win, fg_color="transparent")
    search_frame.pack(fill="x", padx=20, pady=(20, 0))

    def clear_all_history():
        if not app_config["history"]: return
        if messagebox.askyesno("确认", "确定要清空所有历史记录吗？\n此操作不可恢复。"):
            app_config["history"] = []
            save_config()
            render_history_list([])
            safe_update_status("🗑️ 历史记录已清空", TEXT_SUB)
    
    search_entry = ctk.CTkEntry(search_frame, placeholder_text="🔍 搜索历史文章...", font=FONT_NORMAL)
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
    
    clear_btn = ctk.CTkButton(search_frame, text="🗑️ 清空", width=60, height=28, fg_color=BTN_GRAY, hover_color="#F7768E", text_color=TEXT_MAIN, font=FONT_SMALL, command=clear_all_history)
    clear_btn.pack(side="right")
    add_tooltip(clear_btn, "清空所有历史记录 (此操作不可恢复)")
    
    # 建一个可以滚动的框架
    scroll_frame = ctk.CTkScrollableFrame(history_win, fg_color="transparent")
    scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    def render_history_list(items):
        # 先清空列表
        for widget in scroll_frame.winfo_children():
            widget.destroy()
            
        if not items:
            ctk.CTkLabel(scroll_frame, text="没有找到相关记录", text_color=TEXT_SUB).pack(pady=40)
            return

        # 遍历日记本，把每一条记录画在滚动框架里
        for item in items:
            # 每条记录是一个小卡片
            item_card = ctk.CTkFrame(scroll_frame, fg_color=INPUT_BG, corner_radius=10)
            item_card.pack(fill="x", pady=6)
            
            # 左侧显示标题和日期
            text_frame = ctk.CTkFrame(item_card, fg_color="transparent")
            text_frame.pack(side="left", padx=15, pady=10, fill="x", expand=True)
            
            # 限制标题长度，太长了会破坏排版
            display_title = item["title"][:20] + "..." if len(item["title"]) > 20 else item["title"]
            ctk.CTkLabel(text_frame, text=display_title, font=FONT_HISTORY_TITLE, text_color=TEXT_MAIN, anchor="w").pack(fill="x")
            ctk.CTkLabel(text_frame, text=item["date"], font=FONT_SMALL, text_color=TEXT_SUB, anchor="w").pack(fill="x")
            
            # 魔法函数：点击按钮，把这篇历史文章的链接，重新填进主界面的输入框里
            def reuse_url(u=item["url"]):
                url_textbox.insert("end", u + "\n")
                save_win_size() # 提取时也顺便记住当前尺寸
                history_win.destroy() # 填完之后自动关闭历史窗口
                status_label.configure(text="✨ 链接已提取，可重新抓取", text_color=("#10B981", "#9ECE6A"))
                
            # 右侧操作按钮组
            btn_frame = ctk.CTkFrame(item_card, fg_color="transparent")
            btn_frame.pack(side="right", padx=15)

            # 1. 提取按钮
            reuse_btn = ctk.CTkButton(btn_frame, text="提取", width=45, height=24, fg_color=BTN_GRAY, hover_color=BTN_GRAY_HOVER, text_color=TEXT_MAIN, font=FONT_SMALL, command=reuse_url)
            reuse_btn.grid(row=0, column=0, padx=2, pady=2)
            add_tooltip(reuse_btn, "将此链接重新添加到主界面的输入框")

            # 2. 预览按钮 (新功能：直接用浏览器打开刚抓好的 HTML)
            def preview_article(t=item["title"], d=item["date"]):
                safe_t = t.replace('/', '_').replace('\\', '_').replace('|', '_')
                target_path = os.path.join(app_config["save_path"], d[:7], f"{safe_t}.html")
                if os.path.exists(target_path):
                    # 使用 pathlib 转换路径为 URI，解决中文路径浏览器打不开的问题
                    webbrowser.open(pathlib.Path(target_path).as_uri())
                else:
                    safe_update_status("⚠️ 找不到预览文件", "#F7768E")

            preview_btn = ctk.CTkButton(btn_frame, text="预览", width=45, height=24, fg_color="#4ECDC4", hover_color="#3EBDB4", text_color="#1A1B26", font=FONT_SMALL, command=preview_article)
            preview_btn.grid(row=0, column=1, padx=2, pady=2)
            add_tooltip(preview_btn, "用默认浏览器打开已保存的 HTML 文件")

            # 3. Markdown 源码预览 (新增)
            def preview_markdown(t=item["title"], d=item["date"]):
                safe_t = t.replace('/', '_').replace('\\', '_').replace('|', '_')
                target_path = os.path.join(app_config["save_path"], d[:7], f"{safe_t}.md")
                
                if os.path.exists(target_path):
                    try:
                        with open(target_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # 弹窗显示内容
                        top = ctk.CTkToplevel(app)
                        top.geometry("700x600")
                        top.title(f"Markdown 源码: {t}")
                        top.attributes("-topmost", True)
                        
                        # 使用等宽字体显示源码，方便阅读代码
                        textbox = ctk.CTkTextbox(top, font=("Consolas", BASE_FONT_SIZE), wrap="word")
                        textbox.pack(fill="both", expand=True, padx=10, pady=10)
                        textbox.insert("0.0", content)
                    except Exception as e:
                        safe_update_status(f"❌ 读取错误: {e}", "#F7768E")
                else:
                    safe_update_status("⚠️ 找不到 Markdown 文件", "#F7768E")
            md_btn = ctk.CTkButton(btn_frame, text="MD", width=45, height=24, fg_color="#7289DA", hover_color="#5B6EA5", text_color="#FFFFFF", font=FONT_SMALL, command=preview_markdown)
            md_btn.grid(row=1, column=0, padx=2, pady=2)
            add_tooltip(md_btn, "在新窗口中预览 Markdown 源码")

            # 4. 删除按钮
            def delete_item(i=item, card=item_card):
                if i in app_config["history"]:
                    app_config["history"].remove(i)
                    save_config()
                    card.destroy() # 视觉上移除这个卡片

            del_btn = ctk.CTkButton(btn_frame, text="删除", width=45, height=24, 
                                    fg_color="transparent", hover_color=BTN_GRAY_HOVER, 
                                    text_color=("#EF4444", "#F87171"), font=FONT_SMALL, command=delete_item)
            del_btn.grid(row=1, column=1, padx=2, pady=2)
            add_tooltip(del_btn, "从历史记录中移除此条目")

    # 初始渲染
    render_history_list(app_config["history"])

    # 搜索过滤函数
    def on_search(event):
        query = search_entry.get().strip().lower()
        if not query:
            render_history_list(app_config["history"])
        else:
            filtered_items = [
                item for item in app_config["history"] 
                if query in item["title"].lower() or query in item["date"]
            ]
            render_history_list(filtered_items)

    search_entry.bind("<KeyRelease>", on_search)

# ==========================================
# 4. UI 界面搭建
# ==========================================

main_frame = ctk.CTkFrame(app, fg_color="transparent")
main_frame.pack(fill="both", expand=True, padx=40, pady=30)

# --- 顶部区域：标题 + 功能按钮 (使用弹性布局，不再绝对定位) ---
header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
header_frame.pack(fill="x", pady=(0, 20))

# 左侧：标题组
title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
title_frame.pack(side="left")

title_label = ctk.CTkLabel(title_frame, text="Article Purifier", font=FONT_TITLE, text_color=TEXT_MAIN)
title_label.pack(anchor="w")

subtitle_label = ctk.CTkLabel(title_frame, text="优雅地将微信公众号文章转换为 Markdown", font=FONT_SUBTITLE, text_color=TEXT_SUB)
subtitle_label.pack(anchor="w")

# 右侧：按钮组 (自动靠右对齐)
controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
controls_frame.pack(side="right", anchor="ne")

history_btn = ctk.CTkButton(
    controls_frame, text="📜 历史", width=60, height=28, 
    fg_color="transparent", hover_color=BTN_GRAY_HOVER, text_color=TEXT_MAIN, font=FONT_SMALL_BOLD,
    command=open_history_panel
)
history_btn.pack(side="left", padx=(0, 10))
add_tooltip(history_btn, "查看和管理已抓取的文章记录")

readme_btn = ctk.CTkButton(
    controls_frame, text="📖 说明", width=60, height=28, 
    fg_color="transparent", hover_color=BTN_GRAY_HOVER, text_color=TEXT_MAIN, font=FONT_SMALL_BOLD,
    command=show_readme
)
readme_btn.pack(side="left", padx=(0, 10))
add_tooltip(readme_btn, "查看使用说明")

settings_btn = ctk.CTkButton(
    controls_frame, text="⚙️", width=30, height=28, 
    fg_color="transparent", hover_color=BTN_GRAY_HOVER, text_color=TEXT_MAIN, font=FONT_ICON,
    command=open_settings_panel
)
settings_btn.pack(side="left", padx=(0, 10))
add_tooltip(settings_btn, "配置代理服务器等高级选项")

about_btn = ctk.CTkButton(
    controls_frame, text="ℹ️", width=30, height=28, 
    fg_color="transparent", hover_color=BTN_GRAY_HOVER, text_color=TEXT_MAIN, font=FONT_ICON,
    command=show_about
)
about_btn.pack(side="left", padx=(0, 10))
add_tooltip(about_btn, "查看软件版本和信息")

def toggle_monitor():
    if not pyperclip:
        messagebox.showerror("组件缺失", "需要安装 pyperclip 才能使用监控功能。\n请在终端运行: pip install pyperclip")
        monitor_switch.deselect()
        return
    app_config["clipboard_monitor"] = bool(monitor_switch.get())
    save_config()
    if app_config["clipboard_monitor"]:
        safe_update_status("👀 剪贴板监控已开启", ACCENT_COLOR)
    else:
        safe_update_status("zzz 监控已关闭", TEXT_SUB)

monitor_switch = ctk.CTkSwitch(
    controls_frame, 
    text="📋 监控", 
    command=toggle_monitor,
    font=FONT_SMALL_BOLD,
    text_color=TEXT_MAIN
)
if app_config.get("clipboard_monitor"):
    monitor_switch.select()
else:
    monitor_switch.deselect()
monitor_switch.pack(side="left", padx=(0, 10))
add_tooltip(monitor_switch, "开启后，复制微信/知乎链接自动下载")

theme_switch = ctk.CTkSwitch(
    controls_frame, 
    text="☀️ Light", 
    command=toggle_theme,
    font=FONT_SMALL_BOLD,
    text_color=TEXT_MAIN
)
theme_switch.deselect() # 默认关闭（即亮色）
theme_switch.pack(side="left")
add_tooltip(theme_switch, "切换亮色/暗色主题")

# ==========================================
#              新的输入框
# ============================================
url_textbox = ctk.CTkTextbox(
    main_frame,
    height=200, # 再次加高，满足大量粘贴需求
    corner_radius=12,
    fg_color=INPUT_BG,
    text_color=TEXT_MAIN,
    border_width=1,
    border_color=BORDER_COLOR,
    font=FONT_TEXTBOX,
    border_spacing=10 # 增加内边距，文字不贴边
)
# 默认给里面写点提示词，0.0 表示从第 0 行第 0 个字符开始插入
url_textbox.insert("0.0", "批量模式：在此处粘贴链接，每行一个...\n") 
url_textbox.pack(fill="both", expand=True, pady=(0, 15))
add_tooltip(url_textbox, "粘贴一个或多个文章链接，每行一个 (快捷键: Ctrl+D 清空)")

# 开启撤回功能 (Undo/Redo) - 支持 Ctrl+Z
url_textbox._textbox.configure(undo=True, maxundo=-1, autoseparators=True)

# --- 新增：拖拽文件读取 (需要 pip install windnd) ---
def on_drop_files(filenames):
    try:
        for fname in filenames:
            # windnd 返回的是 bytes，Windows 下通常是 gbk 编码
            path = fname.decode('gbk')
            if os.path.isfile(path) and path.lower().endswith('.txt'):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    url_textbox.insert("end", content + "\n")
                    safe_update_status(f"📂 已读取: {os.path.basename(path)}", TEXT_SUB)
        
        # 模拟按键触发，重置按钮状态
        reset_button_state()
    except Exception as e:
        print(f"拖拽处理出错: {e}")

if windnd:
    # Hook 到文本框底层的 tkinter 组件上，这样拖到白框里就能识别
    windnd.hook_dropfiles(url_textbox._textbox, func=on_drop_files)

# --- 右键菜单 (复制/粘贴/剪切) ---
context_menu = Menu(app, tearoff=0, font=FONT_ICON)
context_menu.add_command(label="复制", command=lambda: app.focus_get().event_generate("<<Copy>>"))
context_menu.add_command(label="粘贴", command=lambda: app.focus_get().event_generate("<<Paste>>"))
context_menu.add_command(label="剪切", command=lambda: app.focus_get().event_generate("<<Cut>>"))

def show_context_menu(event):
    url_textbox.focus_set() # 确保焦点在输入框上
    try:
        context_menu.tk_popup(event.x_root, event.y_root)
    finally:
        context_menu.grab_release()

url_textbox.bind("<Button-3>", show_context_menu)

# 路径选择区
path_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
path_frame.pack(fill="x", pady=(0, 25))

def choose_folder():
    global current_save_path
    selected_dir = filedialog.askdirectory(title="选择保存位置")
    if selected_dir:
        current_save_path = selected_dir
        # 当你选择新路径后，立刻呼叫记忆卡，把它存下来！
        app_config["save_path"] = current_save_path
        save_config() 
        
        display_text = os.path.basename(current_save_path)
        if not display_text: display_text = current_save_path
        path_label.configure(text=f"保存位置: .../{display_text}")

def open_save_folder():
    if os.path.exists(current_save_path):
        try:
            os.startfile(current_save_path) # Windows 系统专用
        except AttributeError:
            import subprocess, platform # Mac/Linux 兼容
            opener = "open" if platform.system() == "Darwin" else "xdg-open"
            subprocess.call([opener, current_save_path])
    else:
        status_label.configure(text="❌ 文件夹不存在", text_color="#F7768E")

# 启动时，把记忆里读取的路径显示在界面上
display_initial_text = os.path.basename(current_save_path)
if not display_initial_text: display_initial_text = current_save_path
path_label = ctk.CTkLabel(path_frame, text=f"保存位置: .../{display_initial_text}", font=FONT_NORMAL, text_color=TEXT_SUB)
path_label.pack(side="left")

change_path_btn = ctk.CTkButton(
    path_frame, 
    text="更改", width=80, height=32, corner_radius=8, 
    fg_color=BTN_GRAY, hover_color=BTN_GRAY_HOVER, border_width=1, border_color=BORDER_COLOR,
    text_color=TEXT_MAIN, font=FONT_SMALL, command=choose_folder)
change_path_btn.pack(side="right")
add_tooltip(change_path_btn, "选择文章和资源的保存位置")

open_btn = ctk.CTkButton(
    path_frame, 
    text="打开", width=80, height=32, corner_radius=8, 
    fg_color=BTN_GRAY, hover_color=BTN_GRAY_HOVER, border_width=1, border_color=BORDER_COLOR,
    text_color=TEXT_MAIN, font=FONT_SMALL, command=open_save_folder)
open_btn.pack(side="right", padx=(0, 10))
add_tooltip(open_btn, "在文件管理器中打开当前保存位置")

# --- 标签输入区 ---
tags_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
tags_frame.pack(fill="x", pady=(0, 15))

ctk.CTkLabel(tags_frame, text="自定义标签:", font=FONT_NORMAL_BOLD, text_color=TEXT_MAIN).pack(side="left", padx=(0, 10))
tags_entry = ctk.CTkEntry(tags_frame, placeholder_text="例如: 科技, 教程 (用逗号分隔)", font=FONT_SMALL, height=32, border_color=BORDER_COLOR)
tags_entry.pack(side="left", fill="x", expand=True)
add_tooltip(tags_entry, "为文章添加自定义标签，多个用逗号分隔")

# --- 导出格式选择区 ---
format_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
format_frame.pack(fill="x", pady=(0, 15))

ctk.CTkLabel(format_frame, text="导出格式:", font=FONT_NORMAL_BOLD, text_color=TEXT_MAIN).pack(side="left", padx=(0, 10))

chk_md = ctk.CTkCheckBox(format_frame, text="Markdown", font=FONT_SMALL, text_color=TEXT_MAIN, fg_color=ACCENT_COLOR)
chk_md.select()
chk_md.pack(side="left", padx=10)
add_tooltip(chk_md, "导出为 .md 文件，适用于 Obsidian、Notion 等笔记软件")

chk_html = ctk.CTkCheckBox(format_frame, text="HTML", font=FONT_SMALL, text_color=TEXT_MAIN, fg_color=ACCENT_COLOR)
chk_html.select()
chk_html.pack(side="left", padx=10)
add_tooltip(chk_html, "导出为 .html 文件，可在浏览器中离线阅读")

chk_docx = ctk.CTkCheckBox(format_frame, text="Word", font=FONT_SMALL, text_color=TEXT_MAIN, fg_color=ACCENT_COLOR)
if not HtmlToDocx:
    chk_docx.configure(state="disabled", text="Word (缺库)")
chk_docx.pack(side="left", padx=10)
add_tooltip(chk_docx, "导出为 .docx 文件，方便在 Microsoft Word 中编辑")

chk_mm = ctk.CTkCheckBox(format_frame, text="MindMap", font=FONT_SMALL, text_color=TEXT_MAIN, fg_color=ACCENT_COLOR)
chk_mm.pack(side="left", padx=10)
add_tooltip(chk_mm, "根据文章目录自动生成 .mm 思维导图 (支持 XMind/FreeMind)")

# 主按钮
download_btn = ctk.CTkButton(
    main_frame, 
    text="开始提取并保存", height=45, corner_radius=22, 
    font=FONT_LARGE_BOLD, 
    fg_color=ACCENT_COLOR, hover_color=HOVER_COLOR, command=start_download)
download_btn.pack(fill="x", pady=(0, 10))
add_tooltip(download_btn, "开始处理输入框中的所有链接 (快捷键: Ctrl+S)")

# 进度条区域 (包含进度条和百分比文字)
progress_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
progress_frame.pack(fill="x", pady=(0, 15))

# 进度条放在左边，自动拉伸
progress_bar = ctk.CTkProgressBar(progress_frame, height=10, corner_radius=5, fg_color=BORDER_COLOR, progress_color=ACCENT_COLOR)
progress_bar.set(0)
progress_bar.pack(side="left", fill="x", expand=True, padx=(0, 10))

# 百分比文字放在右边
progress_label = ctk.CTkLabel(progress_frame, text="0%", font=FONT_SMALL_BOLD, text_color=ACCENT_COLOR, width=40)
progress_label.pack(side="right")

status_label = ctk.CTkLabel(main_frame, text="", font=FONT_NORMAL, text_color=TEXT_SUB)
status_label.pack(anchor="center")

# ==========================================
# 5. 极客交互：全局快捷键绑定
# ==========================================

def shortcut_start(event=None):
    # 安全锁 1：检查按钮状态。如果按钮已经是灰色（正在处理），就忽略快捷键！防止重复召唤工人。
    if download_btn.cget("state") == "normal":
        start_download()
    return "break" # 计算机逻辑：告诉系统“这个按键我已经处理了，不要再输出其他奇怪的字符”

def shortcut_clear(event=None):
    # 只有在空闲状态下，才允许使用快捷键清空
    if download_btn.cget("state") == "normal":
        url_textbox.delete("0.0", "end")
        status_label.configure(text="✨ 输入框已清空", text_color=TEXT_SUB)
        download_btn.configure(text="开始提取并保存")
    return "break"

# 绑定开始保存快捷键 (兼容 Windows 和 Mac)
app.bind('<Control-s>', shortcut_start)
app.bind('<Command-s>', shortcut_start) 

# 绑定清空快捷键 (兼容 Windows 和 Mac)
app.bind('<Control-d>', shortcut_clear)
app.bind('<Command-d>', shortcut_clear) 

# --- 新增：当用户开始输入或修改内容时，重置按钮状态 ---
def reset_button_state(event=None):
    if download_btn.cget("text") == "已完成提取并保存":
        download_btn.configure(text="开始提取并保存")
        status_label.configure(text="") # 顺便把状态栏也清空，看起来更清爽

url_textbox.bind("<KeyPress>", reset_button_state)

# ==========================================
# 6. 剪贴板监控线程
# ==========================================
def clipboard_monitor_loop():
    last_text = ""
    while True:
        # 只有开关开启且库存在时才工作
        if app_config.get("clipboard_monitor", False) and pyperclip:
            try:
                # 获取剪贴板内容
                curr_text = pyperclip.paste().strip()
                
                # 判断是否是新内容，且包含目标域名 (微信/知乎)
                # 这里简单判断 http 和域名，防止误触
                if curr_text != last_text and "http" in curr_text and ("mp.weixin.qq.com" in curr_text or "zhihu.com" in curr_text):
                    last_text = curr_text
                    
                    # 只有当主按钮可用（空闲）时才触发
                    if download_btn.cget("state") == "normal":
                        def auto_trigger():
                            # 1. 清空并填入链接
                            url_textbox.delete("0.0", "end")
                            url_textbox.insert("0.0", curr_text + "\n")
                            # 2. 提示用户
                            safe_update_status("⚡ 捕获剪贴板链接，自动下载中...", ACCENT_COLOR)
                            # 3. 触发下载
                            start_download()
                        
                        app.after(0, auto_trigger)
            except Exception:
                pass # 剪贴板访问偶尔会冲突，忽略即可
        
        time.sleep(0.5) # 每0.5秒检查一次

# 启动监控线程 (守护线程，随主程序关闭)
threading.Thread(target=clipboard_monitor_loop, daemon=True).start()

# ==========================================
# 启动程序 (这行原本就有，保持在最后)
app.mainloop()