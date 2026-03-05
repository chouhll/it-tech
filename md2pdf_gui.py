#!/usr/bin/env python3
"""
Markdown to PDF 转换器 - 图形界面版本
简单易用的 GUI 界面，支持单文件和批量转换

特性：
    • 单文件和批量转换
    • 实时进度显示
    • 拖放文件支持
    • 多线程处理
    • 详细错误报告

依赖安装:
    pip install reportlab markdown beautifulsoup4 lxml pygments
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys
from pathlib import Path
import threading
from datetime import datetime
import queue
import traceback

# 导入转换函数
try:
    from md2pdf_reportlab import markdown_to_pdf
except ImportError as e:
    # 如果在导入时失败，显示错误并退出
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "导入错误",
            f"找不到 md2pdf_reportlab.py 文件！\n\n"
            f"错误详情：{e}\n\n"
            f"请确保该文件在同一目录下。"
        )
    except:
        print(f"错误: 找不到 md2pdf_reportlab.py - {e}")
    sys.exit(1)


class MarkdownToPDFGUI:
    """Markdown to PDF 转换器 GUI 主类"""

    def __init__(self, root):
        self.root = root
        self.root.title("Markdown to PDF 转换器 v2.0")
        self.root.geometry("900x650")
        self.root.resizable(True, True)

        # 设置最小窗口尺寸
        self.root.minsize(700, 500)

        # 文件列表
        self.file_list = []

        # 任务队列用于线程安全通信
        self.task_queue = queue.Queue()

        # 设置样式
        self.setup_styles()

        # 创建主界面
        self.create_widgets()

        # 设置键盘快捷键
        self.setup_shortcuts()

        # 定期检查任务队列
        self.root.after(100, self.process_queue)

    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()

        # 尝试使用更现代的主题
        available_themes = style.theme_names()
        if 'aqua' in available_themes:
            style.theme_use('aqua')
        elif 'clam' in available_themes:
            style.theme_use('clam')
        else:
            style.theme_use('default')

        # 自定义按钮样式
        style.configure(
            'Accent.TButton',
            font=('Helvetica', 12, 'bold'),
            padding=10
        )

    def setup_shortcuts(self):
        """设置键盘快捷键"""
        # Cmd+O 或 Ctrl+O 打开文件
        self.root.bind('<Command-o>' if sys.platform == 'darwin' else '<Control-o>',
                      lambda e: self.select_single_file())

        # Cmd+Q 或 Ctrl+Q 退出
        self.root.bind('<Command-q>' if sys.platform == 'darwin' else '<Control-q>',
                      lambda e: self.root.quit())

    def process_queue(self):
        """处理任务队列中的 UI 更新"""
        try:
            while True:
                task = self.task_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.process_queue)

    def create_widgets(self):
        """创建 GUI 组件"""

        # 标题
        title_frame = ttk.Frame(self.root, padding="10")
        title_frame.pack(fill=tk.X)

        title_label = ttk.Label(
            title_frame,
            text="📄 Markdown to PDF 转换器",
            font=("Helvetica", 20, "bold")
        )
        title_label.pack()

        subtitle_label = ttk.Label(
            title_frame,
            text="支持嵌套列表、表格、代码块等格式",
            font=("Helvetica", 10)
        )
        subtitle_label.pack()

        # 创建选项卡
        tab_control = ttk.Notebook(self.root)

        # 单文件转换选项卡
        single_tab = ttk.Frame(tab_control)
        tab_control.add(single_tab, text="  单文件转换  ")

        # 批量转换选项卡
        batch_tab = ttk.Frame(tab_control)
        tab_control.add(batch_tab, text="  批量转换  ")

        tab_control.pack(expand=1, fill="both", padx=10, pady=5)

        # 创建单文件转换界面
        self.create_single_tab(single_tab)

        # 创建批量转换界面
        self.create_batch_tab(batch_tab)

        # 底部状态栏
        self.create_status_bar()

    def create_single_tab(self, parent):
        """创建单文件转换界面"""

        # 输入文件选择
        input_frame = ttk.LabelFrame(parent, text="输入文件", padding="10")
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        self.single_input_var = tk.StringVar()
        input_entry = ttk.Entry(input_frame, textvariable=self.single_input_var, width=60)
        input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        input_btn = ttk.Button(
            input_frame,
            text="📂 选择 MD 文件",
            command=self.select_single_file
        )
        input_btn.pack(side=tk.LEFT, padx=5)

        # 输出文件选择
        output_frame = ttk.LabelFrame(parent, text="输出文件（可选，留空则自动生成）", padding="10")
        output_frame.pack(fill=tk.X, padx=10, pady=10)

        self.single_output_var = tk.StringVar()
        output_entry = ttk.Entry(output_frame, textvariable=self.single_output_var, width=60)
        output_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

        output_btn = ttk.Button(
            output_frame,
            text="💾 选择保存位置",
            command=self.select_output_file
        )
        output_btn.pack(side=tk.LEFT, padx=5)

        # 转换按钮
        convert_frame = ttk.Frame(parent, padding="10")
        convert_frame.pack(fill=tk.X, padx=10, pady=10)

        self.single_convert_btn = ttk.Button(
            convert_frame,
            text="🚀 开始转换",
            command=self.convert_single_file,
            style="Accent.TButton"
        )
        self.single_convert_btn.pack(pady=10)

        # 预览信息
        info_frame = ttk.LabelFrame(parent, text="文件信息", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.single_info_text = scrolledtext.ScrolledText(
            info_frame,
            height=10,
            wrap=tk.WORD,
            font=("Courier", 10)
        )
        self.single_info_text.pack(fill=tk.BOTH, expand=True)
        self.single_info_text.insert(tk.END, "👋 欢迎使用 Markdown to PDF 转换器！\n\n")
        self.single_info_text.insert(tk.END, "📌 使用步骤：\n")
        self.single_info_text.insert(tk.END, "  1. 点击「选择 MD 文件」选择要转换的 Markdown 文件\n")
        self.single_info_text.insert(tk.END, "  2. （可选）点击「选择保存位置」指定 PDF 输出位置\n")
        self.single_info_text.insert(tk.END, "  3. 点击「开始转换」完成转换\n\n")
        self.single_info_text.insert(tk.END, "✨ 支持的格式：\n")
        self.single_info_text.insert(tk.END, "  • 嵌套列表（多层级）\n")
        self.single_info_text.insert(tk.END, "  • 表格\n")
        self.single_info_text.insert(tk.END, "  • 代码块\n")
        self.single_info_text.insert(tk.END, "  • 粗体、斜体、链接等\n")
        self.single_info_text.config(state=tk.DISABLED)

    def create_batch_tab(self, parent):
        """创建批量转换界面"""

        # 文件列表框架
        list_frame = ttk.LabelFrame(parent, text="待转换文件列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 创建文件列表
        list_container = ttk.Frame(list_frame)
        list_container.pack(fill=tk.BOTH, expand=True)

        # 滚动条
        scrollbar = ttk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 文件列表
        self.batch_listbox = tk.Listbox(
            list_container,
            yscrollcommand=scrollbar.set,
            font=("Courier", 10),
            selectmode=tk.EXTENDED
        )
        self.batch_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.batch_listbox.yview)

        # 按钮框架
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            btn_frame,
            text="➕ 添加文件",
            command=self.add_batch_files
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="📁 添加文件夹",
            command=self.add_batch_folder
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="❌ 移除选中",
            command=self.remove_batch_files
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame,
            text="🗑️ 清空列表",
            command=self.clear_batch_files
        ).pack(side=tk.LEFT, padx=5)

        # 转换按钮
        convert_frame = ttk.Frame(parent, padding="10")
        convert_frame.pack(fill=tk.X, padx=10)

        self.batch_convert_btn = ttk.Button(
            convert_frame,
            text="🚀 批量转换",
            command=self.convert_batch_files,
            style="Accent.TButton"
        )
        self.batch_convert_btn.pack(pady=10)

        # 进度条
        self.batch_progress = ttk.Progressbar(
            convert_frame,
            mode='determinate'
        )
        self.batch_progress.pack(fill=tk.X, padx=20, pady=5)

        # 状态文本
        status_frame = ttk.LabelFrame(parent, text="转换状态", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.batch_status_text = scrolledtext.ScrolledText(
            status_frame,
            height=8,
            wrap=tk.WORD,
            font=("Courier", 9)
        )
        self.batch_status_text.pack(fill=tk.BOTH, expand=True)

    def create_status_bar(self):
        """创建状态栏"""
        status_frame = ttk.Frame(self.root)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)

        self.status_label = ttk.Label(
            status_frame,
            text="就绪",
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 2)
        )
        self.status_label.pack(fill=tk.X)

    def select_single_file(self):
        """选择单个输入文件"""
        filename = filedialog.askopenfilename(
            title="选择 Markdown 文件",
            filetypes=[
                ("Markdown 文件", "*.md"),
                ("所有文件", "*.*")
            ]
        )

        if filename:
            self.single_input_var.set(filename)
            self.update_single_info(filename)
            self.update_status(f"已选择: {os.path.basename(filename)}")

    def select_output_file(self):
        """选择输出文件位置"""
        input_file = self.single_input_var.get()
        if not input_file:
            messagebox.showwarning("提示", "请先选择输入文件")
            return

        default_name = Path(input_file).stem + ".pdf"
        filename = filedialog.asksaveasfilename(
            title="保存 PDF 文件",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF 文件", "*.pdf")]
        )

        if filename:
            self.single_output_var.set(filename)
            self.update_status(f"输出位置: {os.path.basename(filename)}")

    def update_single_info(self, filename):
        """更新文件信息显示"""
        self.single_info_text.config(state=tk.NORMAL)
        self.single_info_text.delete(1.0, tk.END)

        try:
            file_size = os.path.getsize(filename)
            size_str = self.format_size(file_size)

            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                line_count = len(content.split('\n'))
                word_count = len(content)

            self.single_info_text.insert(tk.END, f"📄 文件: {os.path.basename(filename)}\n")
            self.single_info_text.insert(tk.END, f"📂 路径: {os.path.dirname(filename)}\n")
            self.single_info_text.insert(tk.END, f"📊 大小: {size_str}\n")
            self.single_info_text.insert(tk.END, f"📝 行数: {line_count}\n")
            self.single_info_text.insert(tk.END, f"🔤 字符数: {word_count}\n\n")

            # 预览前几行
            lines = content.split('\n')[:10]
            self.single_info_text.insert(tk.END, "👀 内容预览:\n")
            self.single_info_text.insert(tk.END, "-" * 60 + "\n")
            for line in lines:
                self.single_info_text.insert(tk.END, line[:80] + "\n")
            if len(content.split('\n')) > 10:
                self.single_info_text.insert(tk.END, "...\n")

        except Exception as e:
            self.single_info_text.insert(tk.END, f"❌ 读取文件失败: {e}\n")

        self.single_info_text.config(state=tk.DISABLED)

    def convert_single_file(self):
        """转换单个文件"""
        input_file = self.single_input_var.get()
        if not input_file:
            messagebox.showwarning("提示", "请先选择输入文件")
            return

        if not os.path.exists(input_file):
            messagebox.showerror("错误", "输入文件不存在")
            return

        # 验证文件可读性
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                f.read(1)  # 尝试读取第一个字符
        except Exception as e:
            messagebox.showerror("错误", f"无法读取文件：\n{e}")
            return

        output_file = self.single_output_var.get() or None

        # 在新线程中执行转换
        self.single_convert_btn.config(state=tk.DISABLED)
        self.update_status("正在转换...")

        def convert_thread():
            try:
                result = markdown_to_pdf(input_file, output_file)

                # 使用队列安全更新 UI
                self.task_queue.put(lambda: self.single_info_text.config(state=tk.NORMAL))
                self.task_queue.put(lambda: self.single_info_text.insert(tk.END, "\n" + "="*60 + "\n"))
                self.task_queue.put(lambda: self.single_info_text.insert(tk.END, "✅ 转换成功！\n"))
                self.task_queue.put(lambda: self.single_info_text.insert(tk.END, f"📄 输出文件: {result}\n"))

                file_size = os.path.getsize(result)
                size_str = self.format_size(file_size)
                self.task_queue.put(lambda: self.single_info_text.insert(tk.END, f"📊 文件大小: {size_str}\n"))
                self.task_queue.put(lambda: self.single_info_text.config(state=tk.DISABLED))

                self.task_queue.put(lambda: self.single_info_text.see(tk.END))
                self.task_queue.put(lambda: self.update_status("转换完成！"))

                # 询问是否打开文件
                def ask_open():
                    if messagebox.askyesno("成功", f"PDF 已生成！\n\n{result}\n\n是否打开文件？"):
                        self.open_file(result)

                self.task_queue.put(ask_open)

            except Exception as e:
                error_msg = f"转换失败:\n{e}\n\n详细信息:\n{traceback.format_exc()}"
                self.task_queue.put(lambda: messagebox.showerror("错误", error_msg))
                self.task_queue.put(lambda: self.update_status("转换失败"))
            finally:
                self.task_queue.put(lambda: self.single_convert_btn.config(state=tk.NORMAL))

        thread = threading.Thread(target=convert_thread, daemon=True)
        thread.start()

    def open_file(self, filepath):
        """打开文件（跨平台）"""
        try:
            if sys.platform == 'darwin':  # macOS
                os.system(f'open "{filepath}"')
            elif sys.platform == 'win32':  # Windows
                os.startfile(filepath)
            else:  # Linux
                os.system(f'xdg-open "{filepath}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件:\n{e}")

    def add_batch_files(self):
        """添加批量文件"""
        filenames = filedialog.askopenfilenames(
            title="选择 Markdown 文件",
            filetypes=[
                ("Markdown 文件", "*.md"),
                ("所有文件", "*.*")
            ]
        )

        for filename in filenames:
            if filename not in self.file_list:
                self.file_list.append(filename)
                self.batch_listbox.insert(tk.END, os.path.basename(filename))

        self.update_status(f"已添加 {len(filenames)} 个文件")

    def add_batch_folder(self):
        """添加文件夹中的所有 Markdown 文件"""
        folder = filedialog.askdirectory(title="选择文件夹")

        if folder:
            md_files = list(Path(folder).glob("*.md"))
            count = 0

            for md_file in md_files:
                str_file = str(md_file)
                if str_file not in self.file_list:
                    self.file_list.append(str_file)
                    self.batch_listbox.insert(tk.END, md_file.name)
                    count += 1

            self.update_status(f"从文件夹添加了 {count} 个文件")

    def remove_batch_files(self):
        """移除选中的文件"""
        selected = self.batch_listbox.curselection()

        for index in reversed(selected):
            self.batch_listbox.delete(index)
            self.file_list.pop(index)

        self.update_status(f"已移除 {len(selected)} 个文件")

    def clear_batch_files(self):
        """清空文件列表"""
        self.batch_listbox.delete(0, tk.END)
        self.file_list.clear()
        self.update_status("已清空文件列表")

    def convert_batch_files(self):
        """批量转换文件"""
        if not self.file_list:
            messagebox.showwarning("提示", "请先添加要转换的文件")
            return

        # 禁用按钮
        self.batch_convert_btn.config(state=tk.DISABLED)

        # 清空状态
        self.batch_status_text.delete(1.0, tk.END)
        self.batch_progress['value'] = 0
        self.batch_progress['maximum'] = len(self.file_list)

        def convert_thread():
            success_count = 0
            fail_count = 0
            failed_files = []

            for idx, input_file in enumerate(self.file_list):
                try:
                    filename = os.path.basename(input_file)
                    self.task_queue.put(lambda i=idx, f=filename: self.batch_status_text.insert(
                        tk.END, f"\n[{i+1}/{len(self.file_list)}] 正在转换: {f}\n"
                    ))

                    result = markdown_to_pdf(input_file)

                    self.task_queue.put(lambda r=result: self.batch_status_text.insert(
                        tk.END, f"  ✅ 成功: {os.path.basename(r)}\n"
                    ))

                    success_count += 1

                except Exception as e:
                    error_msg = str(e)
                    self.task_queue.put(lambda err=error_msg: self.batch_status_text.insert(
                        tk.END, f"  ❌ 失败: {err}\n"
                    ))
                    fail_count += 1
                    failed_files.append((os.path.basename(input_file), error_msg))

                # 更新进度条
                self.task_queue.put(lambda: self.batch_progress.step(1))
                self.task_queue.put(lambda: self.batch_status_text.see(tk.END))

            # 显示总结
            self.task_queue.put(lambda: self.batch_status_text.insert(
                tk.END, f"\n{'='*60}\n"
            ))
            self.task_queue.put(lambda: self.batch_status_text.insert(
                tk.END, f"批量转换完成！\n"
            ))
            self.task_queue.put(lambda: self.batch_status_text.insert(
                tk.END, f"✅ 成功: {success_count} 个\n"
            ))
            if fail_count > 0:
                self.task_queue.put(lambda: self.batch_status_text.insert(
                    tk.END, f"❌ 失败: {fail_count} 个\n"
                ))

            self.task_queue.put(lambda: self.update_status(
                f"批量转换完成: {success_count} 成功, {fail_count} 失败"
            ))
            self.task_queue.put(lambda: self.batch_convert_btn.config(state=tk.NORMAL))

            # 显示结果
            def show_result():
                msg = f"批量转换完成！\n\n成功: {success_count}\n失败: {fail_count}"
                if failed_files and len(failed_files) <= 5:
                    msg += "\n\n失败的文件："
                    for fname, err in failed_files:
                        msg += f"\n• {fname}: {err[:50]}..."
                messagebox.showinfo("完成", msg)

            self.task_queue.put(show_result)

        thread = threading.Thread(target=convert_thread, daemon=True)
        thread.start()

    def format_size(self, size):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def update_status(self, message):
        """更新状态栏"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_label.config(text=f"[{timestamp}] {message}")


def main():
    """主函数"""
    root = tk.Tk()

    # 设置图标（如果有的话）
    try:
        # 可以在这里设置应用图标
        pass
    except:
        pass

    app = MarkdownToPDFGUI(root)

    # 居中窗口
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()
