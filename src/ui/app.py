import os
import shutil
import platform
import subprocess
import customtkinter as ctk
import math
from pathlib import Path
from tkinter import filedialog
from concurrent.futures import ThreadPoolExecutor
from ..utils.logger import get_logger
from ..utils.config import load_config, update_config
from ..core.downloader import YtDlpDownloader
from ..core.audio_extractor import AudioExtractor
from ..core.oss_provider import OSSProvider
from ..core.asr_provider import ASRProvider
from ..core.llm_provider import LLMProvider

logger = get_logger("UI")


class StepperItem(ctk.CTkFrame):
    """分步进度条中的单个项目"""
    def __init__(self, master, text, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.active = False
        self._glow_step = 0

        self.icon_label = ctk.CTkLabel(
            self, text="●", font=ctk.CTkFont(size=24), text_color="#3B3B3B"
        )
        self.icon_label.pack()

        self.text_label = ctk.CTkLabel(
            self, text=text, font=ctk.CTkFont(size=12), text_color="#7F7F7F"
        )
        self.text_label.pack()

    def set_state(self, state: str):
        """设置状态: pending, active, completed"""
        if state == "active":
            self.active = True
            self.icon_label.configure(text_color="#1F6AA5")
            self.text_label.configure(text_color="#FFFFFF")
            self._animate_glow()
        elif state == "completed":
            self.active = False
            self.icon_label.configure(text="✔", text_color="#2ECC71")
            self.text_label.configure(text_color="#2ECC71")
        else:
            self.active = False
            self.icon_label.configure(text="●", text_color="#3B3B3B")
            self.text_label.configure(text_color="#7F7F7F")

    def _animate_glow(self):
        if not self.active:
            return
        # 简单的呼吸灯效果逻辑
        alpha = (math.sin(self._glow_step) + 1) / 2
        color_val = int(59 + (100 * alpha))  # 在深蓝到亮蓝之间切换
        hex_color = f"#{color_val:02x}6AA5"
        self.icon_label.configure(text_color=hex_color)
        self._glow_step += 0.2
        self.after(100, self._animate_glow)


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # 1. 基础配置
        self.title("VidScript")
        self.geometry("1100x750")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # 2. 状态变量
        self.is_processing = False
        self.executor = ThreadPoolExecutor(max_workers=4)

        # 3. 布局初始化
        self._setup_grid()
        self._init_sidebar()
        self._init_main_area()

        logger.info("VidScript 界面初始化完成")

    def _setup_grid(self):
        """配置全局网格"""
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _init_sidebar(self):
        """初始化侧边栏 (240px)"""
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)  # 底部留白推到底部

        # 品牌 Logo
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="VidScript",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(30, 40))

        # 加载持久化配置
        self.user_config = load_config()

        # 配置组: 下载路径
        self.path_label = ctk.CTkLabel(
            self.sidebar_frame, text="下载路径", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.path_label.grid(row=1, column=0, padx=20, pady=(10, 2), sticky="w")

        self.path_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.path_frame.grid(row=2, column=0, padx=20, pady=(2, 5), sticky="ew")
        self.path_frame.grid_columnconfigure(0, weight=1)

        # 使用保存的路径或默认文档路径
        saved_path = self.user_config.get("download_path", str(Path.home() / "Documents"))
        self.path_entry = ctk.CTkEntry(self.path_frame, height=28, font=ctk.CTkFont(size=11))
        self.path_entry.insert(0, saved_path)
        self.path_entry.configure(state="readonly")
        self.path_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.browse_btn = ctk.CTkButton(
            self.path_frame, text="浏览", width=40, height=28,
            font=ctk.CTkFont(size=11), command=self._on_browse_click
        )
        self.browse_btn.grid(row=0, column=1)

        # 配置组: 模型选择
        self.model_label = ctk.CTkLabel(
            self.sidebar_frame, text="模型选择", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.model_label.grid(row=3, column=0, padx=20, pady=(5, 2), sticky="w")

        self.model_var = ctk.StringVar(value=self.user_config.get("llm_provider", "DeepSeek"))
        self.model_dropdown = ctk.CTkComboBox(
            self.sidebar_frame, values=["DeepSeek", "Qwen"],
            variable=self.model_var,
            font=ctk.CTkFont(size=12),
            command=self._on_model_change
        )
        self.model_dropdown.grid(row=4, column=0, padx=20, pady=(2, 5), sticky="ew")

        # 配置组: 润色风格
        self.config_label = ctk.CTkLabel(
            self.sidebar_frame, text="润色风格", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.config_label.grid(row=5, column=0, padx=20, pady=(5, 2), sticky="w")

        saved_style = self.user_config.get("rewrite_style", "深度润色")
        # 兼容旧配置：如果不是列表，转为列表
        if not isinstance(saved_style, list):
            saved_style = [saved_style] if saved_style else ["深度润色"]

        self.style_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.style_frame.grid(row=6, column=0, padx=20, pady=(2, 5), sticky="ew")

        self.style_checkboxes = {}
        styles = ["深度润色", "口语化转换", "学术风提炼", "自定义"]

        for style in styles:
            chk = ctk.CTkCheckBox(
                self.style_frame, text=style, font=ctk.CTkFont(size=12),
                checkbox_width=20, checkbox_height=20,
                command=lambda s=style: self._on_style_toggle(s)
            )
            chk.pack(anchor="w", pady=2)
            if style in saved_style:
                chk.select()
            self.style_checkboxes[style] = chk

            if style == "自定义":
                # 初始化时根据选中状态显示/隐藏
                if "自定义" in saved_style:
                    self.after(100, lambda: self.custom_style_frame.grid(row=7, column=0, sticky="ew"))
                else:
                    self.after(100, lambda: self.custom_style_frame.grid_forget())

        # 自定义提示词输入框 (默认隐藏)
        self.custom_style_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.custom_style_label = ctk.CTkLabel(
            self.custom_style_frame, text="自定义润色", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.custom_style_label.pack(padx=20, pady=(0, 2), anchor="w")

        self.custom_style_textbox = ctk.CTkTextbox(
            self.custom_style_frame, width=200, height=100, font=ctk.CTkFont(size=12)
        )
        saved_custom_prompt = self.user_config.get("custom_rewrite_prompt", "")
        self.custom_style_textbox.insert("0.0", saved_custom_prompt)
        self.custom_style_textbox.bind("<FocusOut>", self._on_custom_prompt_change)
        self.custom_style_textbox.bind("<KeyRelease>", self._on_custom_prompt_change)
        self.custom_style_textbox.pack(padx=20, pady=(2, 10))

        # self.custom_style_frame.grid(row=5, column=0, sticky="ew") # Removed duplicate grid call

        # 背景信息输入框
        self.context_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.context_label = ctk.CTkLabel(
            self.context_frame, text="背景信息 (可选)", font=ctk.CTkFont(size=13, weight="bold")
        )
        self.context_label.pack(padx=20, pady=(0, 2), anchor="w")

        self.context_textbox = ctk.CTkTextbox(
            self.context_frame, width=200, height=100, font=ctk.CTkFont(size=12)
        )
        saved_context = self.user_config.get("rewrite_context", "")
        self.context_textbox.insert("0.0", saved_context)
        self.context_textbox.bind("<FocusOut>", self._on_context_change)
        self.context_textbox.bind("<KeyRelease>", self._on_context_change)
        self.context_textbox.pack(padx=20, pady=(2, 10))

        self.context_frame.grid(row=8, column=0, sticky="ew")

    def _on_style_toggle(self, style):
        """润色风格复选框回调"""
        # 如果是自定义风格，切换自定义文本框的显示
        if style == "自定义":
            if self.style_checkboxes["自定义"].get():
                self.custom_style_frame.grid(row=7, column=0, sticky="ew")
            else:
                self.custom_style_frame.grid_forget()

        # 实时保存所有选中的风格
        selected_styles = []
        for s_name, chk in self.style_checkboxes.items():
            if chk.get() == 1:
                selected_styles.append(s_name)

        update_config("rewrite_style", selected_styles)
        logger.info(f"润色风格已更新: {selected_styles}")

    def _on_custom_prompt_change(self, event=None):
        """自定义润色提示词变更回调"""
        prompt = self.custom_style_textbox.get("0.0", "end").strip()
        update_config("custom_rewrite_prompt", prompt)
        logger.info("自定义润色提示词已更新")

    def _on_context_change(self, event=None):
        """背景信息变更回调"""
        context = self.context_textbox.get("0.0", "end").strip()
        update_config("rewrite_context", context)
        logger.info("背景信息已更新")

        self.spacer = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.spacer.grid(row=9, column=0, sticky="nsew")

        # 底部状态栏
        self.version_label = ctk.CTkLabel(
            self.sidebar_frame, text="v1.0.0",
            font=ctk.CTkFont(size=11), text_color="#7F7F7F"
        )
        self.version_label.grid(row=10, column=0, padx=20, pady=(0, 20))

    def _init_main_area(self):
        """初始化主工作区"""
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.grid(row=0, column=1, padx=30, pady=30, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(2, weight=1)

        # --- 输入区 ---
        self.input_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.input_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        self.input_frame.grid_columnconfigure(0, weight=1)

        # URL 输入框容器（用于包裹 Entry 和清空按钮）
        self.url_container = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        self.url_container.grid(row=0, column=0, padx=(0, 15), sticky="ew")
        self.url_container.grid_columnconfigure(0, weight=1)

        self.url_var = ctk.StringVar()
        self.url_var.trace_add("write", self._on_url_change)

        self.url_entry = ctk.CTkEntry(
            self.url_container, placeholder_text="请输入视频 URL (如 YouTube, Bilibili...)",
            height=45, font=ctk.CTkFont(size=14),
            textvariable=self.url_var
        )
        self.url_entry.grid(row=0, column=0, sticky="ew")

        # 清空按钮 (初始隐藏)
        self.clear_btn = ctk.CTkButton(
            self.url_container, text="×", width=30, height=30,
            fg_color="transparent", hover_color="#3B3B3B", text_color="#A9B7C6",
            font=ctk.CTkFont(size=20),
            command=self._on_clear_url
        )

        self.start_btn = ctk.CTkButton(
            self.input_frame, text="开始转换", width=120, height=45,
            font=ctk.CTkFont(weight="bold"), command=self._on_start_click
        )
        self.start_btn.grid(row=0, column=2)

        self.select_file_btn = ctk.CTkButton(
            self.input_frame, text="选择文件", width=100, height=45,
            fg_color="#3B3B3B", hover_color="#4B4B4B",
            font=ctk.CTkFont(size=14), command=self._on_select_file
        )
        self.select_file_btn.grid(row=0, column=1, padx=(10, 10))

        # --- 进度监控 (Stepper) ---
        self.stepper_frame = ctk.CTkFrame(self.main_container, height=80, fg_color="#1A1A1A")
        self.stepper_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.stepper_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.steps = []
        step_names = ["视频下载", "音频提取", "语音识别", "大模型润色"]
        for i, name in enumerate(step_names):
            step = StepperItem(self.stepper_frame, text=name)
            step.grid(row=0, column=i, pady=10)
            self.steps.append(step)

        # --- 内容区 (Tabview) ---
        self.tabview = ctk.CTkTabview(self.main_container)
        self.tabview.grid(row=2, column=0, sticky="nsew")

        self.tab_logs = self.tabview.add("执行日志")
        self.tab_raw = self.tabview.add("原始文稿")

        # 文本框初始化
        # 润色讲稿 Tab 动态添加
        self.polished_tabs = []  # 记录当前存在的润色 Tab 名称

        self.txt_raw = self._create_script_textbox(self.tab_raw)
        self.txt_logs = ctk.CTkTextbox(
            self.tab_logs, font=ctk.CTkFont(family="Consolas", size=12),
            fg_color="#000000", text_color="#A9B7C6"
        )
        self.txt_logs.pack(fill="both", expand=True)

        # --- 底部操作栏 ---
        self.action_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.action_frame.grid(row=3, column=0, sticky="ew", pady=(20, 0))

        self.open_dir_btn = ctk.CTkButton(
            self.action_frame, text="打开文件夹", width=100, fg_color="#3B3B3B", hover_color="#4B4B4B",
            command=self._on_open_dir_click
        )
        self.open_dir_btn.pack(side="right")

    def _create_script_textbox(self, master):
        """创建带样式的文稿文本框，并在右上角添加复制按钮"""
        # 创建一个容器 frame
        container = ctk.CTkFrame(master, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # 顶部工具栏
        toolbar = ctk.CTkFrame(container, height=30, fg_color="transparent")
        toolbar.pack(fill="x", pady=(0, 5))

        # 复制按钮
        copy_btn = ctk.CTkButton(
            toolbar, text="复制内容", width=80, height=24,
            font=ctk.CTkFont(size=12),
            command=lambda: self._copy_to_clipboard(txt)
        )
        copy_btn.pack(side="right")

        # 文本框
        txt = ctk.CTkTextbox(
            container, font=ctk.CTkFont(size=14),
            border_width=1, border_color="#3B3B3B"
        )
        txt.pack(fill="both", expand=True)
        return txt

    def _copy_to_clipboard(self, textbox):
        """复制文本框内容到剪贴板"""
        content = textbox.get("0.0", "end").strip()
        if content:
            self.clipboard_clear()
            self.clipboard_append(content)
            self.update()  # 确保剪贴板更新
            logger.info("内容已复制到剪贴板")

            # 简单的视觉反馈（可选）
            # self.tab_logs.focus() # 转移焦点避免选中文本

    # --- 交互逻辑回调 ---

    def _on_select_file(self):
        """选择本地视频/音频文件"""
        file_path = filedialog.askopenfilename(
            filetypes=[
                ("Media Files", "*.mp4;*.mkv;*.avi;*.mov;*.flv;*.webm;*.mp3;*.wav;*.m4a;*.flac"),
                ("Video Files", "*.mp4;*.mkv;*.avi;*.mov;*.flv;*.webm"),
                ("Audio Files", "*.mp3;*.wav;*.m4a;*.flac"),
                ("All Files", "*.*")
            ]
        )
        if file_path:
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, file_path)
            logger.info(f"用户选择了本地文件: {file_path}")

    def _on_browse_click(self):
        """打开文件夹选择对话框"""
        directory = filedialog.askdirectory()
        if directory:
            self.path_entry.configure(state="normal")
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, directory)
            self.path_entry.configure(state="readonly")
            logger.info(f"用户选择了下载路径: {directory}")
            # 持久化保存路径
            update_config("download_path", directory)

    def _on_open_dir_click(self):
        """打开下载目录"""
        path = self.path_entry.get()
        if not path or not os.path.exists(path):
            logger.warning(f"无法打开路径: {path}")
            return

        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(["open", path], check=True)
            else:  # Linux
                subprocess.run(["xdg-open", path], check=True)
            logger.info(f"已打开文件夹: {path}")
        except Exception as e:
            logger.error(f"打开文件夹失败: {e}")

    def _on_model_change(self, choice):
        """模型选择变更回调"""
        update_config("llm_provider", choice)
        logger.info(f"模型选择已更新为: {choice}")

    def _on_url_change(self, *args):
        """URL 输入框内容变更回调"""
        if self.url_var.get():
            self.clear_btn.grid(row=0, column=1, padx=(5, 0))
        else:
            self.clear_btn.grid_forget()

    def _on_clear_url(self):
        """清空 URL 输入框"""
        self.url_var.set("")
        self.url_entry.focus()

    def _on_start_click(self):
        url = self.url_entry.get()
        if not url:
            logger.warning("用户未输入 URL")
            return

        # 获取所有选中的风格
        selected_styles = []
        for style, chk in self.style_checkboxes.items():
            if chk.get() == 1:
                selected_styles.append(style)

        if not selected_styles:
            self.tabview.set("执行日志")
            self.txt_logs.insert("end", "[Error] 请至少选择一种润色风格！\n")
            logger.warning("用户未选择任何润色风格")
            return

        # 持久化保存风格
        update_config("rewrite_style", selected_styles)

        # 持久化保存模型选择
        selected_model = self.model_var.get()
        update_config("llm_provider", selected_model)

        # 如果选择了自定义风格，检查自定义提示词
        custom_prompt = ""
        if "自定义" in selected_styles:
            custom_prompt = self.custom_style_textbox.get("0.0", "end").strip()
            if not custom_prompt:
                self.tabview.set("执行日志")
                self.txt_logs.insert("end", "[Error] 选中了自定义风格，请输入自定义润色提示词！\n")
                logger.warning("用户选择了自定义风格但未输入提示词")
                return
            update_config("custom_rewrite_prompt", custom_prompt)

        # 获取背景信息
        context = self.context_textbox.get("0.0", "end").strip()
        update_config("rewrite_context", context)

        config = {
            "styles": selected_styles,
            "custom_prompt": custom_prompt,
            "context": context,
            "download_path": self.path_entry.get(),
            "llm_provider": selected_model
        }
        self.on_start_processing(url, config)

    def on_start_processing(self, url, config):
        """解耦的业务逻辑入口"""
        if self.is_processing:
            return

        self.is_processing = True
        self.start_btn.configure(state="disabled", text="正在转换...")

        # 清空之前的日志
        self.txt_logs.delete("0.0", "end")

        self.txt_logs.insert("end", f"[Info] 开始处理 URL: {url}\n")

        styles_display = ", ".join(config['styles'])
        if "自定义" in config['styles'] and config['custom_prompt']:
            styles_display = styles_display.replace("自定义", f"自定义 ({config['custom_prompt'][:20]}...)")

        self.txt_logs.insert("end", f"[Config] 风格: {styles_display}, 下载路径: {config['download_path']}\n")
        if config.get('context'):
            self.txt_logs.insert("end", f"[Config] 背景信息: {config['context'][:30]}...\n")

        # 自动切换到“执行日志”标签页
        self.tabview.set("执行日志")

        # 重置所有步骤状态
        for step in self.steps:
            step.set_state("pending")

        # 清空之前的文稿内容
        self.txt_raw.delete("0.0", "end")
        # 清除旧的润色 Tab
        for tab_name in self.polished_tabs:
            self.tabview.delete(tab_name)
        self.polished_tabs = []

        # 开始真正的下载任务
        self.executor.submit(self._run_workflow, url, config)

    def _update_progress(self, data: dict):
        """处理来自下载器的进度回调"""
        try:
            status = data.get('status')
            if status == 'downloading':
                percentage = data.get('percentage', 0)
                speed = data.get('speed', 'N/A')
                eta = data.get('eta', 'N/A')
                msg = f"[下载] {percentage}% | 速度: {speed} | ETA: {eta}\n"
                self.after(0, lambda: self._append_log(msg))
            elif status == 'finished':
                self.after(0, lambda: self._append_log("[下载] 视频文件下载完成！\n"))
        except Exception as e:
            logger.warning(f"更新进度条时发生非致命错误: {str(e)}")

    def _append_log(self, message: str):
        """线程安全地添加日志并滚动到底部"""
        self.txt_logs.insert("end", message)
        self.txt_logs.see("end")

    def _save_text_to_file(self, content, title, process_name, save_dir):
        """保存文本内容到文件"""
        try:
            # 限制标题长度，防止文件名过长
            safe_title = title[:20] if len(title) > 20 else title
            filename = f"{safe_title}_{process_name}.txt"

            # 处理文件名中的非法字符
            invalid_chars = '<>:"/\\|?*'
            for char in invalid_chars:
                filename = filename.replace(char, '_')

            filepath = os.path.join(save_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)

            self.after(0, lambda: self._append_log(f"[Info] 已保存{process_name}文件: {filename}\n"))
            return filepath
        except Exception as e:
            logger.error(f"保存文件失败: {e}")
            error_msg = str(e)
            self.after(0, lambda: self._append_log(f"[Warning] 保存{process_name}文件失败: {error_msg}\n"))
            return None

    def _prepare_video_file(self, url, config):
        video_path = ""
        video_title = ""
        is_audio_file = False

        if os.path.isfile(url):
            self.after(0, lambda: self._append_log(f"[Info] 检测到本地文件: {url}\n"))

            filename = os.path.basename(url)
            video_title = os.path.splitext(filename)[0]
            ext = os.path.splitext(filename)[1].lower()

            # 检查是否为音频文件
            if ext in ['.mp3', '.wav', '.m4a', '.flac']:
                is_audio_file = True
                self.after(0, lambda: self._append_log("[Info] 识别为音频文件，将直接进行语音识别\n"))

            # 复制文件到下载目录
            try:
                dest_dir = config['download_path']
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                dest_path = os.path.join(dest_dir, filename)

                # 如果源文件和目标文件不同，则进行复制
                if os.path.abspath(url) != os.path.abspath(dest_path):
                    self.after(0, lambda: self._append_log("[Info] 正在复制文件到下载目录...\n"))
                    shutil.copy2(url, dest_path)
                    video_path = dest_path
                else:
                    video_path = url

                self.after(0, lambda: self.steps[0].set_state("completed"))
                self.after(0, lambda: self._append_log(f"[Success] 本地文件准备就绪: {video_title}\n"))
                self.after(0, lambda: self._append_log(f"[Info] 文件路径: {video_path}\n"))

            except Exception as e:
                raise Exception(f"本地文件处理失败: {str(e)}")
        else:
            downloader = YtDlpDownloader(on_progress_update=self._update_progress)

            # 执行标准下载
            result = downloader.download(url, save_dir=config['download_path'])
            video_path = result['path']
            video_title = result['title']
            self.after(0, lambda: self.steps[0].set_state("completed"))
            self.after(0, lambda: self._append_log(f"[Success] 视频已下载: {video_title}\n"))
            self.after(0, lambda: self._append_log(f"[Info] 保存路径: {video_path}\n"))

        return video_path, video_title, is_audio_file

    def _run_workflow(self, url, config):
        """实际的业务流逻辑"""
        try:
            # 步骤 1: 视频下载 / 本地文件处理
            self.after(0, lambda: self.steps[0].set_state("active"))

            video_path, video_title, is_audio_file = self._prepare_video_file(url, config)

            # 步骤 2: 音频提取 (如果是音频文件则跳过)
            audio_path = ""
            if is_audio_file:
                self.after(0, lambda: self.steps[1].set_state("completed"))
                self.after(0, lambda: self._append_log("[Info] 跳过音频提取步骤 (直接使用源音频)\n"))
                audio_path = video_path
            else:
                self.after(0, lambda: self.steps[1].set_state("active"))
                extractor = AudioExtractor()
                audio_path = extractor.extract_mp3(video_path)
                self.after(0, lambda: self.steps[1].set_state("completed"))
                self.after(0, lambda: self._append_log(f"[Success] 音频已提取: {Path(audio_path).name}\n"))

            # 步骤 3: 上传 OSS 并进行语音识别
            self.after(0, lambda: self.steps[2].set_state("active"))
            self.after(0, lambda: self._append_log("[Info] 正在上传音频到云端并进行语音识别...\n"))

            # 3.1 上传到 OSS
            oss = OSSProvider()
            signed_url = oss.upload_file(audio_path)
            self.after(0, lambda: self._append_log("[Success] 音频已上传，临时链接已生成\n"))

            # 3.2 调用 ASR
            asr = ASRProvider()
            asr_result = asr.transcribe(signed_url)

            # 将识别结果填入“原始文稿”并切换标签页
            def _update_ui_with_asr():
                self.txt_raw.delete("0.0", "end")
                self.txt_raw.insert("0.0", asr_result)
                self.tabview.set("原始文稿")

            self.after(0, _update_ui_with_asr)
            # 保存原始文稿
            self._save_text_to_file(asr_result, video_title, "原始文稿", config['download_path'])

            self.after(0, lambda: self.steps[2].set_state("completed"))
            self.after(0, lambda: self._append_log("[Success] 语音识别完成！\n"))

            # 步骤 4: 大模型润色
            self.after(0, lambda: self.steps[3].set_state("active"))

            llm_provider_name = config.get("llm_provider", "DeepSeek")
            llm = LLMProvider(provider=llm_provider_name)

            for style in config['styles']:
                self.after(0, lambda s=style: self._append_log(f"[Info] 正在进行大模型润色，风格: {s}...\n"))

                polished_text = llm.polish_text(
                    text=asr_result,
                    style=style,
                    custom_prompt=config.get('custom_prompt', ""),
                    context=config.get('context', "")
                )

                # 动态创建 Tab 并更新 UI
                def _update_ui_with_polished(s=style, text=polished_text):
                    tab_name = f"润色讲稿_{s}"
                    self.tabview.add(tab_name)
                    self.polished_tabs.append(tab_name)

                    # 创建文本框
                    txt_box = self._create_script_textbox(self.tabview.tab(tab_name))
                    txt_box.insert("0.0", text)

                    self.tabview.set(tab_name)

                self.after(0, lambda: _update_ui_with_polished())

                # 保存润色讲稿
                filename_suffix = f"润色讲稿_{style}"
                self._save_text_to_file(polished_text, video_title, filename_suffix, config['download_path'])
                self.after(0, lambda s=style: self._append_log(f"[Success] 风格 [{s}] 润色完成！\n"))

            self.after(0, lambda: self.steps[3].set_state("completed"))
            self.after(0, lambda: self._append_log("[Done] 所有处理步骤已完成！\n"))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"处理流程出错: {error_msg}")
            self.after(0, lambda: self._append_log(f"[Error] 流程中断: {error_msg}\n"))
        finally:
            self.is_processing = False
            self.after(0, lambda: self.start_btn.configure(state="normal", text="开始转换"))

    def _mock_workflow(self):
        """模拟后台业务流"""
        import time
        try:
            for i in range(len(self.steps)):
                # 1. 设置当前步骤为活动状态
                self.after(0, lambda idx=i: self.steps[idx].set_state("active"))
                time.sleep(2)  # 模拟耗时

                # 2. 设置当前步骤为完成状态
                self.after(0, lambda idx=i: self.steps[idx].set_state("completed"))

            # 模拟生成内容
            self.after(0, lambda: self.txt_polished.insert("0.0", "# 润色后的讲稿示例\n\n这是经过 AI 优化后的内容..."))
            self.after(0, lambda: self.txt_raw.insert("0.0", "原始识别文稿内容..."))

        except Exception as e:
            logger.error(f"处理流程出错: {e}")
        finally:
            self.is_processing = False
            self.after(0, lambda: self.start_btn.configure(state="normal", text="开始转换"))

    def run(self):
        self.mainloop()
