#!/usr/bin/env python3
"""
Markdown to PDF Converter (使用 ReportLab - 纯 Python 实现)
将 Markdown 文件转换为 PDF，保留格式渲染

特性:
    • 完整的 Markdown 语法支持（表格、列表、代码块等）
    • 代码语法高亮（使用 Pygments）
    • 中文字体自动检测
    • GitHub 风格提示框
    • 任务列表支持
    • 嵌套列表完美渲染
    • 性能优化的转换引擎

使用方法:
    python md2pdf_reportlab.py input.md [output.pdf]

依赖安装:
    pip install reportlab markdown beautifulsoup4 lxml pygments

版本: 2.0
作者: Claude
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple
import re
import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Preformatted
)
from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup

# 代码高亮支持
PYGMENTS_AVAILABLE = False
_pygments_lex = None
_pygments_get_lexer = None
_pygments_Token = None

try:
    from pygments import lex as _pygments_lex
    from pygments.lexers import get_lexer_by_name as _pygments_get_lexer
    from pygments.token import Token as _pygments_Token
    PYGMENTS_AVAILABLE = True
except ImportError:
    pass  # 静默失败，在运行时才显示警告


# ============================================================================
# 字体管理
# ============================================================================

def setup_chinese_fonts() -> str:
    """
    自动检测并设置中文字体

    Returns:
        str: 可用的字体名称
    """
    # 系统字体候选列表 (路径, 字体名)
    font_candidates: List[Tuple[str, str]] = [
        # macOS
        ('/System/Library/Fonts/STHeiti Light.ttc', 'STHeiti'),
        ('/System/Library/Fonts/PingFang.ttc', 'PingFang'),
        ('/System/Library/Fonts/Hiragino Sans GB.ttc', 'HiraginoSansGB'),

        # Windows
        ('C:\\Windows\\Fonts\\simhei.ttf', 'SimHei'),
        ('C:\\Windows\\Fonts\\msyh.ttc', 'MicrosoftYaHei'),
        ('C:\\Windows\\Fonts\\simsun.ttc', 'SimSun'),

        # Linux
        ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WQY'),
        ('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'NotoSansCJK'),
        ('/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf', 'DroidSans'),
    ]

    for font_path, font_name in font_candidates:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                return font_name
            except Exception:
                # 字体注册失败，尝试下一个
                continue

    # 所有中文字体都失败，返回默认字体（不支持中文但不会报错）
    print("⚠️  警告: 未找到中文字体，中文可能显示为方框")
    return 'Helvetica'



# ============================================================================
# 主转换函数
# ============================================================================

def markdown_to_pdf(md_file_path: str, pdf_file_path: str = None) -> str:
    """
    将 Markdown 文件转换为 PDF

    Args:
        md_file_path: Markdown 文件路径
        pdf_file_path: 输出的 PDF 文件路径（可选，默认同名.pdf）

    Returns:
        str: 生成的 PDF 文件路径

    Raises:
        FileNotFoundError: 输入文件不存在
        ValueError: 文件格式错误
        Exception: 转换过程中的其他错误
    """
    # 检查输入文件
    if not os.path.exists(md_file_path):
        raise FileNotFoundError(f"文件不存在: {md_file_path}")

    # 确定输出文件路径
    if pdf_file_path is None:
        pdf_file_path = str(Path(md_file_path).with_suffix('.pdf'))
    else:
        pdf_file_path = str(pdf_file_path)

    # 读取 Markdown 文件
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            md_content = f.read()
    except UnicodeDecodeError:
        raise ValueError(f"文件编码错误，请确保文件是 UTF-8 编码: {md_file_path}")

    # 转换 Markdown 为 HTML，启用扩展
    extensions = [
        'markdown.extensions.extra',       # 表格、定义列表等
        'markdown.extensions.codehilite',  # 代码高亮
        'markdown.extensions.fenced_code', # 围栏代码块
        'markdown.extensions.tables',      # 表格支持
        'markdown.extensions.footnotes',   # 脚注支持
        'markdown.extensions.attr_list',   # 属性列表
        'markdown.extensions.def_list',    # 定义列表
        'markdown.extensions.abbr',        # 缩写
    ]
    html_content = markdown.markdown(md_content, extensions=extensions)

    # 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 设置中文字体
    chinese_font = setup_chinese_fonts()

    # 创建 PDF
    doc = SimpleDocTemplate(
        pdf_file_path,
        pagesize=A4,
        topMargin=2*cm,
        bottomMargin=2*cm,
        leftMargin=2*cm,
        rightMargin=2*cm
    )

    # 创建样式
    styles = getSampleStyleSheet()

    # 自定义样式
    styles.add(ParagraphStyle(
        name='ChineseBody',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=11,
        leading=16,
        alignment=TA_JUSTIFY
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading1',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=24,
        leading=30,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=20,
        spaceAfter=12,
        borderWidth=2,
        borderColor=colors.HexColor('#3498db'),
        borderPadding=8
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading2',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=18,
        leading=24,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=16,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='ChineseHeading3',
        parent=styles['Heading3'],
        fontName=chinese_font,
        fontSize=14,
        leading=20,
        textColor=colors.HexColor('#34495e'),
        spaceBefore=14,
        spaceAfter=8
    ))

    # 代码样式 - 添加多种颜色用于高亮
    styles.add(ParagraphStyle(
        name='ChineseCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=9,
        leading=12,
        backColor=colors.HexColor('#f8f8f8'),
        borderColor=colors.HexColor('#ddd'),
        borderWidth=1,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=6,
        spaceAfter=6
    ))

    # 代码语言标签样式
    styles.add(ParagraphStyle(
        name='CodeLanguageTag',
        parent=styles['ChineseBody'],
        fontName='Courier',
        fontSize=8,
        textColor=colors.HexColor('#666'),
        backColor=colors.HexColor('#e8e8e8'),
        borderColor=colors.HexColor('#ccc'),
        borderWidth=0.5,
        borderPadding=4,
        leftIndent=10,
        spaceBefore=10,
        spaceAfter=2
    ))

    # 列表样式
    styles.add(ParagraphStyle(
        name='ChineseListItem',
        parent=styles['ChineseBody'],
        leftIndent=0,
        fontSize=11,
        leading=16
    ))

    styles.add(ParagraphStyle(
        name='ChineseListItemIndent',
        parent=styles['ChineseBody'],
        leftIndent=20,
        fontSize=11,
        leading=16
    ))

    # 脚注样式
    styles.add(ParagraphStyle(
        name='Footnote',
        parent=styles['ChineseBody'],
        fontSize=9,
        textColor=colors.HexColor('#666'),
        leftIndent=20,
        firstLineIndent=-15,
        spaceBefore=2,
        spaceAfter=2
    ))

    # 警告框样式
    styles.add(ParagraphStyle(
        name='AlertNote',
        parent=styles['ChineseBody'],
        fontSize=11,
        backColor=colors.HexColor('#e3f2fd'),
        borderColor=colors.HexColor('#2196f3'),
        borderWidth=2,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=10,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='AlertWarning',
        parent=styles['ChineseBody'],
        fontSize=11,
        backColor=colors.HexColor('#fff3e0'),
        borderColor=colors.HexColor('#ff9800'),
        borderWidth=2,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=10,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='AlertTip',
        parent=styles['ChineseBody'],
        fontSize=11,
        backColor=colors.HexColor('#e8f5e9'),
        borderColor=colors.HexColor('#4caf50'),
        borderWidth=2,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=10,
        spaceAfter=10
    ))

    styles.add(ParagraphStyle(
        name='AlertImportant',
        parent=styles['ChineseBody'],
        fontSize=11,
        backColor=colors.HexColor('#fce4ec'),
        borderColor=colors.HexColor('#e91e63'),
        borderWidth=2,
        borderPadding=10,
        leftIndent=10,
        rightIndent=10,
        spaceBefore=10,
        spaceAfter=10
    ))

    # 删除线样式（通过颜色模拟）
    styles.add(ParagraphStyle(
        name='Strikethrough',
        parent=styles['ChineseBody'],
        textColor=colors.HexColor('#999'),
        fontSize=11
    ))

    # 构建 PDF 内容
    story = []

    def html_to_reportlab(html_str):
        """将 HTML 字符串转换为 ReportLab 支持的格式"""
        # 保留 <b>, <i>, <strong>, <em>, <code> 等标签
        html_str = str(html_str)
        # 移除 <p> 标签但保留内容
        html_str = html_str.replace('<p>', '').replace('</p>', '')
        # 处理特殊字符
        html_str = html_str.replace('&gt;', '>').replace('&lt;', '<').replace('&amp;', '&')
        # 处理删除线（用灰色和删除线模拟）
        html_str = html_str.replace('<del>', '<strike><font color="#999">').replace('</del>', '</font></strike>')
        html_str = html_str.replace('<s>', '<strike><font color="#999">').replace('</s>', '</font></strike>')

        # 移除不支持的HTML属性（如 id, class 等）
        import re
        # 移除所有标签中的 id 属性
        html_str = re.sub(r'<(\w+)\s+id="[^"]*"([^>]*)>', r'<\1\2>', html_str)
        html_str = re.sub(r'<(\w+)([^>]*)\s+id="[^"]*">', r'<\1\2>', html_str)
        # 移除所有标签中的 class 属性
        html_str = re.sub(r'<(\w+)\s+class="[^"]*"([^>]*)>', r'<\1\2>', html_str)
        html_str = re.sub(r'<(\w+)([^>]*)\s+class="[^"]*">', r'<\1\2>', html_str)

        # 处理链接，显示链接文本和URL
        # 查找所有链接并格式化
        link_pattern = r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>'
        html_str = re.sub(link_pattern, r'\2 <font color="#2196f3" size="9">(\1)</font>', html_str)

        # 移除脚注引用的复杂结构，只保留数字
        html_str = re.sub(r'<sup[^>]*>(\d+)[^<]*</sup>', r'<super>\1</super>', html_str)

        return html_str

    def get_code_language(code_element):
        """从代码块元素中提取语言类型"""
        # 检查 class 属性，例如 class="language-python"
        classes = code_element.get('class', [])
        for cls in classes:
            if cls.startswith('language-'):
                return cls.replace('language-', '')
            elif cls.startswith('lang-'):
                return cls.replace('lang-', '')
            elif cls.startswith('highlight-'):
                return cls.replace('highlight-', '')
        return None

    def apply_syntax_highlighting(code_text, language):
        """应用简单的语法高亮（使用颜色标记关键字）"""
        if not PYGMENTS_AVAILABLE or not language or not _pygments_lex or not _pygments_get_lexer or not _pygments_Token:
            return code_text

        try:
            lexer = _pygments_get_lexer(language, stripall=True)
            tokens = list(_pygments_lex(code_text, lexer))

            # 构建带颜色的文本
            colored_parts = []
            for token_type, value in tokens:
                # 根据 token 类型设置颜色
                if token_type in _pygments_Token.Keyword:
                    colored_parts.append(f'<font color="#0000FF">{value}</font>')  # 蓝色关键字
                elif token_type in _pygments_Token.String:
                    colored_parts.append(f'<font color="#008000">{value}</font>')  # 绿色字符串
                elif token_type in _pygments_Token.Comment:
                    colored_parts.append(f'<font color="#808080"><i>{value}</i></font>')  # 灰色注释
                elif token_type in _pygments_Token.Number:
                    colored_parts.append(f'<font color="#FF00FF">{value}</font>')  # 紫色数字
                elif token_type in _pygments_Token.Name.Function or token_type in _pygments_Token.Name.Class:
                    colored_parts.append(f'<font color="#0080FF"><b>{value}</b></font>')  # 蓝色函数/类
                elif token_type in _pygments_Token.Operator:
                    colored_parts.append(f'<font color="#800000">{value}</font>')  # 棕色操作符
                else:
                    colored_parts.append(value)

            return ''.join(colored_parts)
        except Exception:
            # 如果高亮失败，返回原始文本
            return code_text

    def process_list_item(li, level=0, parent_type='ul', item_index=1):
        """递归处理列表项，支持正确的缩进和任务列表

        GitHub 风格：
        - 第一层：无缩进
        - 第二层：缩进 2 个空格（约 15pt）
        - 第三层及以上：每层增加 15pt
        """
        # 缩进计算 - 更接近 GitHub 的视觉效果
        # GitHub 使用约 1.5em 的缩进，在 11pt 字体下约为 16-17pt
        indent = level * 16  # 从 20 改为 16，更接近 GitHub

        # Bullet 和内容之间的间距
        bullet_indent = 5  # bullet 后面的空格

        # 创建适当的样式，确保缩进正确
        style = ParagraphStyle(
            name=f'ListIndent{level}_{id(li)}',
            parent=styles['ChineseBody'],
            leftIndent=indent,
            fontSize=11,
            leading=16,
            spaceBefore=1,  # 减少项目间距，从 2 改为 1
            spaceAfter=1
        )

        # 获取列表项内容（不包括嵌套的列表）
        li_copy = BeautifulSoup(str(li), 'html.parser').find('li')

        # 移除嵌套的 ul/ol
        for nested_list in li_copy.find_all(['ul', 'ol']):
            nested_list.decompose()

        # 获取文本内容
        content = html_to_reportlab(li_copy)

        # 移除 <li> 和 </li> 标签
        content = content.replace('<li>', '').replace('</li>', '')
        content = content.strip()

        # 检查是否是任务列表
        is_task = False
        task_checked = False
        if content.startswith('[ ] '):
            is_task = True
            task_checked = False
            content = content[4:]  # 移除 [ ]
        elif content.startswith('[x] ') or content.startswith('[X] '):
            is_task = True
            task_checked = True
            content = content[4:]  # 移除 [x]

        # 确定 bullet 符号
        if is_task:
            # 任务列表使用特殊符号
            if task_checked:
                bullet = '☑'  # 已完成的任务
            else:
                bullet = '☐'  # 未完成的任务
        elif parent_type == 'ul':
            # 无序列表使用不同符号表示不同层级
            if level == 0:
                bullet = '•'  # 第一层
            elif level == 1:
                bullet = '◦'  # 第二层
            else:
                bullet = '▪'  # 第三层及以上
        else:  # ol
            bullet = f'{item_index}.'

        # 添加 bullet 和内容
        if content:
            full_text = f"{bullet} {content}"
            # 如果是已完成的任务，使用灰色
            if is_task and task_checked:
                full_text = f'<font color="#999">{full_text}</font>'
            story.append(Paragraph(full_text, style))

        # 处理嵌套的列表
        original_li = BeautifulSoup(str(li), 'html.parser').find('li')
        for nested_list in original_li.find_all(['ul', 'ol'], recursive=False):
            nested_items = nested_list.find_all('li', recursive=False)
            for idx, nested_li in enumerate(nested_items, 1):
                process_list_item(nested_li, level + 1, nested_list.name, idx)

    def process_element(element):
        """递归处理 HTML 元素"""
        if element.name == 'h1':
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph(element.get_text(), styles['ChineseHeading1']))
            story.append(Spacer(1, 0.3*cm))
        elif element.name == 'h2':
            story.append(Spacer(1, 0.4*cm))
            story.append(Paragraph(element.get_text(), styles['ChineseHeading2']))
            story.append(Spacer(1, 0.2*cm))
        elif element.name == 'h3':
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph(element.get_text(), styles['ChineseHeading3']))
            story.append(Spacer(1, 0.2*cm))
        elif element.name == 'p':
            text = html_to_reportlab(element)
            if text.strip():
                story.append(Paragraph(text, styles['ChineseBody']))
                story.append(Spacer(1, 0.2*cm))
        elif element.name in ['ul', 'ol']:
            # 处理列表
            list_items = element.find_all('li', recursive=False)
            for idx, li in enumerate(list_items, 1):
                process_list_item(li, level=0, parent_type=element.name, item_index=idx)
            story.append(Spacer(1, 0.3*cm))
        elif element.name == 'div' and 'codehilite' in element.get('class', []):
            # 处理 codehilite 包裹的代码块
            pre_element = element.find('pre')
            if pre_element:
                code_element = pre_element.find('code')
                if code_element:
                    code_text = code_element.get_text()
                    language = get_code_language(code_element)

                    # 添加语言标签
                    if language:
                        story.append(Paragraph(
                            f'  📝 <b>{language.upper()}</b>  ',
                            styles['CodeLanguageTag']
                        ))

                    # 添加带行号的代码
                    lines = code_text.split('\n')
                    formatted_lines = []
                    for i, line in enumerate(lines, 1):
                        formatted_lines.append(f"{i:3d} | {line}")
                    numbered_code = '\n'.join(formatted_lines)
                    story.append(Preformatted(numbered_code, styles['ChineseCode']))
                    story.append(Spacer(1, 0.3*cm))
        elif element.name == 'table':
            data = []
            alignments = []  # 存储每列的对齐方式

            # 首先检查表格头部以确定对齐方式
            thead = element.find('thead')
            if thead:
                header_row = thead.find('tr')
                if header_row:
                    for th in header_row.find_all('th'):
                        # 检查对齐样式
                        style_attr = th.get('style', '')
                        align = th.get('align', '')
                        if 'text-align: right' in style_attr or align == 'right':
                            alignments.append('RIGHT')
                        elif 'text-align: center' in style_attr or align == 'center':
                            alignments.append('CENTER')
                        else:
                            alignments.append('LEFT')

            # 提取表格数据
            for tr in element.find_all('tr'):
                row = [cell.get_text().strip() for cell in tr.find_all(['th', 'td'])]
                data.append(row)

            if data:
                # 自动计算列宽 - 根据内容长度
                col_widths = []
                if data:
                    # 计算每列的最大内容长度
                    num_cols = len(data[0])
                    for col_idx in range(num_cols):
                        max_len = max(len(str(row[col_idx])) if col_idx < len(row) else 0
                                     for row in data)
                        # 基础宽度 + 内容长度系数
                        col_widths.append(max(1.5*cm, min(max_len * 0.15*cm, 6*cm)))

                t = Table(data, colWidths=col_widths)

                # 构建表格样式 - 更接近 GitHub 风格
                table_style = [
                    # 表头样式 - 使用 GitHub 的灰色系
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6f8fa')),  # GitHub 的表头背景
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#24292f')),   # GitHub 的深灰色文字
                    ('FONTNAME', (0, 0), (-1, 0), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('FONTNAME', (0, 1), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),

                    # 内边距 - GitHub 风格
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('LEFTPADDING', (0, 0), (-1, -1), 13),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 13),

                    # 边框 - GitHub 使用细边框
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d0d7de')),  # GitHub 的边框颜色
                    ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#d0d7de')),  # 表头下方加粗

                    # 行背景 - 不使用斑马纹，保持全白（更接近 GitHub）
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),

                    # 垂直对齐
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]

                # 应用列对齐
                for col_idx, align in enumerate(alignments):
                    if col_idx < len(data[0]):
                        table_style.append(('ALIGN', (col_idx, 0), (col_idx, -1), align))

                t.setStyle(TableStyle(table_style))
                story.append(t)
                story.append(Spacer(1, 0.3*cm))
        elif element.name == 'pre':
            # 处理代码块（没有 div 包裹的情况）
            code_element = element.find('code')
            if code_element:
                code_text = code_element.get_text()
                language = get_code_language(code_element)

                # 添加语言标签
                if language:
                    story.append(Paragraph(
                        f'  📝 <b>{language.upper()}</b>  ',
                        styles['CodeLanguageTag']
                    ))

                # 添加带行号的代码
                lines = code_text.split('\n')
                formatted_lines = []
                for i, line in enumerate(lines, 1):
                    formatted_lines.append(f"{i:3d} | {line}")
                numbered_code = '\n'.join(formatted_lines)
                story.append(Preformatted(numbered_code, styles['ChineseCode']))
                story.append(Spacer(1, 0.3*cm))
            else:
                code_text = element.get_text()
                story.append(Preformatted(code_text, styles['ChineseCode']))
                story.append(Spacer(1, 0.3*cm))
        elif element.name == 'code' and element.parent.name != 'pre':
            # 内联代码
            text = element.get_text()
            story.append(Paragraph(f'<font face="Courier" backColor="#f0f0f0">{text}</font>', styles['ChineseBody']))
            story.append(Spacer(1, 0.1*cm))
        elif element.name == 'hr':
            story.append(Spacer(1, 0.3*cm))
            story.append(Paragraph('-' * 80, styles['ChineseBody']))
            story.append(Spacer(1, 0.3*cm))
        elif element.name == 'blockquote':
            # 检查是否是 GitHub 风格的提示框
            text = element.get_text().strip()
            first_line = text.split('\n')[0] if '\n' in text else text

            alert_style = None
            alert_icon = ''
            alert_title = ''

            # 检测提示框类型
            if first_line.startswith('[!NOTE]'):
                alert_style = styles['AlertNote']
                alert_icon = 'ℹ️'
                alert_title = 'NOTE'
                text = text[7:].strip()  # 移除 [!NOTE]
            elif first_line.startswith('[!TIP]'):
                alert_style = styles['AlertTip']
                alert_icon = '💡'
                alert_title = 'TIP'
                text = text[6:].strip()
            elif first_line.startswith('[!IMPORTANT]'):
                alert_style = styles['AlertImportant']
                alert_icon = '❗'
                alert_title = 'IMPORTANT'
                text = text[12:].strip()
            elif first_line.startswith('[!WARNING]'):
                alert_style = styles['AlertWarning']
                alert_icon = '⚠️'
                alert_title = 'WARNING'
                text = text[10:].strip()
            elif first_line.startswith('[!CAUTION]'):
                alert_style = styles['AlertWarning']
                alert_icon = '🚫'
                alert_title = 'CAUTION'
                text = text[10:].strip()

            if alert_style:
                # 显示为提示框
                story.append(Paragraph(
                    f'<b>{alert_icon} {alert_title}</b>',
                    alert_style
                ))
                story.append(Paragraph(text, alert_style))
            else:
                # 普通引用块
                story.append(Paragraph(f'<i>{text}</i>', styles['ChineseBody']))
            story.append(Spacer(1, 0.2*cm))
        elif element.name == 'div' and 'footnote' in element.get('class', []):
            # 处理脚注
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph('<b>───── 脚注 ─────</b>', styles['ChineseBody']))
            story.append(Spacer(1, 0.2*cm))
            for item in element.find_all('li'):
                footnote_text = item.get_text().strip()
                story.append(Paragraph(footnote_text, styles['Footnote']))
            story.append(Spacer(1, 0.3*cm))
        elif element.name == 'dl':
            # 定义列表
            story.append(Spacer(1, 0.2*cm))
            for child in element.children:
                if child.name == 'dt':
                    # 定义术语（加粗）
                    story.append(Paragraph(f'<b>{child.get_text()}</b>', styles['ChineseBody']))
                elif child.name == 'dd':
                    # 定义描述（缩进）
                    dd_style = ParagraphStyle(
                        name='DefinitionDescription',
                        parent=styles['ChineseBody'],
                        leftIndent=20,
                        spaceBefore=2,
                        spaceAfter=10
                    )
                    story.append(Paragraph(child.get_text(), dd_style))

    # 处理所有元素
    for element in soup.find_all(recursive=False):
        process_element(element)

    # 生成 PDF
    try:
        doc.build(story)
        print(f"✓ PDF 生成成功: {pdf_file_path}")

        # 显示文件大小
        file_size = os.path.getsize(pdf_file_path)
        if file_size < 1024:
            size_str = f"{file_size} B"
        elif file_size < 1024 * 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        print(f"  文件大小: {size_str}")

        return pdf_file_path
    except Exception as e:
        print(f"✗ PDF 生成失败: {e}")
        raise


def main():
    """命令行入口"""
    if len(sys.argv) < 2:
        print("Markdown to PDF 转换器 (ReportLab)")
        print("=" * 50)
        print("\n使用方法:")
        print("  python md2pdf_reportlab.py <input.md> [output.pdf]")
        print("\n示例:")
        print("  python md2pdf_reportlab.py README.md")
        print("  python md2pdf_reportlab.py README.md output.pdf")
        print("\n依赖安装:")
        print("  pip install reportlab markdown beautifulsoup4")
        print("=" * 50)
        sys.exit(1)

    md_file = sys.argv[1]
    pdf_file = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        markdown_to_pdf(md_file, pdf_file)
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
