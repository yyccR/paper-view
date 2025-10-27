"""
图片生成模块
用于将PDF和Dify返回的数据转换为图片
"""
import os
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import markdown2
from loguru import logger
import requests
import base64
import urllib.parse


class ImageGenerator:
    """图片生成器类"""
    
    # 图片尺寸 (3:4 比例)
    IMAGE_WIDTH = 1080
    IMAGE_HEIGHT = 1440
    
    # 边距设置
    MARGIN_TOP = 80
    MARGIN_BOTTOM = 80
    MARGIN_LEFT = 60
    MARGIN_RIGHT = 60
    
    # 字体大小
    TITLE_FONT_SIZE = 56  # summary中的标题
    TITLE_IMAGE_FONT_SIZE = 100  # 纯标题图片的字体
    CONTENT_FONT_SIZE = 40
    MARKDOWN_FONT_SIZE = 36
    MARKDOWN_H1_SIZE = 52
    MARKDOWN_H2_SIZE = 44
    MARKDOWN_H3_SIZE = 38
    MARKDOWN_NORMAL_SIZE = 36
    
    # 行间距
    LINE_SPACING = 20
    TITLE_CONTENT_SPACING = 40
    TABLE_CELL_PADDING = 10
    TABLE_BORDER_WIDTH = 2
    
    # 颜色
    BG_COLOR = (255, 255, 255)  # 白色背景
    TITLE_COLOR = (30, 30, 30)  # 深灰色标题
    CONTENT_COLOR = (60, 60, 60)  # 灰色内容
    
    def __init__(self):
        """初始化图片生成器"""
        self.font_title = None
        self.font_title_image = None  # 纯标题图片用
        self.font_content = None
        self.font_markdown = None
        self.font_md_h1 = None
        self.font_md_h2 = None
        self.font_md_h3 = None
        self.font_md_normal = None
        self.font_md_bold = None
        self._load_fonts()
    
    def _load_fonts(self):
        """加载字体"""
        try:
            # 尝试加载系统中文字体
            font_paths = [
                "/System/Library/Fonts/PingFang.ttc",  # macOS
                "/System/Library/Fonts/STHeiti Light.ttc",  # macOS
                "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",  # Linux
                "C:\\Windows\\Fonts\\msyh.ttc",  # Windows
            ]
            
            font_path = None
            for path in font_paths:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if font_path:
                self.font_title = ImageFont.truetype(font_path, self.TITLE_FONT_SIZE)
                self.font_title_image = ImageFont.truetype(font_path, self.TITLE_IMAGE_FONT_SIZE)
                self.font_content = ImageFont.truetype(font_path, self.CONTENT_FONT_SIZE)
                self.font_markdown = ImageFont.truetype(font_path, self.MARKDOWN_FONT_SIZE)
                self.font_md_h1 = ImageFont.truetype(font_path, self.MARKDOWN_H1_SIZE)
                self.font_md_h2 = ImageFont.truetype(font_path, self.MARKDOWN_H2_SIZE)
                self.font_md_h3 = ImageFont.truetype(font_path, self.MARKDOWN_H3_SIZE)
                self.font_md_normal = ImageFont.truetype(font_path, self.MARKDOWN_NORMAL_SIZE)
                self.font_md_bold = ImageFont.truetype(font_path, self.MARKDOWN_NORMAL_SIZE)
                logger.info(f"成功加载字体: {font_path}")
            else:
                logger.warning("未找到系统字体，使用默认字体")
                self.font_title = ImageFont.load_default()
                self.font_title_image = ImageFont.load_default()
                self.font_content = ImageFont.load_default()
                self.font_markdown = ImageFont.load_default()
                self.font_md_h1 = ImageFont.load_default()
                self.font_md_h2 = ImageFont.load_default()
                self.font_md_h3 = ImageFont.load_default()
                self.font_md_normal = ImageFont.load_default()
                self.font_md_bold = ImageFont.load_default()
        except Exception as e:
            logger.error(f"加载字体失败: {e}，使用默认字体")
            self.font_title = ImageFont.load_default()
            self.font_title_image = ImageFont.load_default()
            self.font_content = ImageFont.load_default()
            self.font_markdown = ImageFont.load_default()
            self.font_md_h1 = ImageFont.load_default()
            self.font_md_h2 = ImageFont.load_default()
            self.font_md_h3 = ImageFont.load_default()
            self.font_md_normal = ImageFont.load_default()
            self.font_md_bold = ImageFont.load_default()
    
    def pdf_first_page_to_image(self, pdf_path: str, output_path: str = None) -> str:
        """将PDF第一页转换为图片，保存完整页面不做裁剪
        
        Args:
            pdf_path: PDF文件路径
            output_path: 输出图片路径，如果为None则保存到PDF同目录下的1.png
            
        Returns:
            str: 生成的图片路径
        """
        pdf_file = Path(pdf_path)
        if not pdf_file.exists():
            raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
        
        # 确定输出路径
        if output_path is None:
            output_path = pdf_file.parent / "1.png"
        else:
            output_path = Path(output_path)
        
        # 打开PDF
        doc = fitz.open(pdf_path)
        if len(doc) == 0:
            raise ValueError(f"PDF文件为空: {pdf_path}")
        
        # 获取第一页
        page = doc[0]
        
        # 计算缩放比例以适应目标尺寸 (3:4)
        mat = fitz.Matrix(2.0, 2.0)  # 2倍缩放以提高清晰度
        pix = page.get_pixmap(matrix=mat)
        
        # 转换为PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        
        # 直接调整为目标尺寸 (1080x1440)，不做裁剪
        img = img.resize((self.IMAGE_WIDTH, self.IMAGE_HEIGHT), Image.Resampling.LANCZOS)
        
        # 保存图片
        img.save(output_path, "PNG", quality=95)
        doc.close()
        
        logger.info(f"PDF第一页已保存为图片（完整页面）: {output_path}")
        return str(output_path)
    
    def _crop_white_borders(self, img: Image.Image, threshold: int = 240) -> Image.Image:
        """裁剪图片的白色边距
        
        Args:
            img: PIL Image对象
            threshold: 白色阈值，像素值大于此值视为白色（0-255）
            
        Returns:
            Image.Image: 裁剪后的图片
        """
        # 转换为灰度图以便分析
        gray = img.convert('L')
        
        # 获取图片数据
        import numpy as np
        img_array = np.array(gray)
        
        # 找到非白色区域
        # 对于每一行和每一列，如果有任何像素小于阈值，则认为该行/列有内容
        non_white_rows = np.where(np.any(img_array < threshold, axis=1))[0]
        non_white_cols = np.where(np.any(img_array < threshold, axis=0))[0]
        
        # 如果没有找到非白色区域，返回原图
        if len(non_white_rows) == 0 or len(non_white_cols) == 0:
            logger.warning("未检测到非白色区域，返回原图")
            return img
        
        # 计算裁剪边界
        top = non_white_rows[0]
        bottom = non_white_rows[-1] + 1
        left = non_white_cols[0]
        right = non_white_cols[-1] + 1
        
        # 裁剪图片
        cropped = img.crop((left, top, right, bottom))
        
        logger.info(f"裁剪边距: 上={top}, 下={img.height-bottom}, 左={left}, 右={img.width-right}")
        
        return cropped
    
    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """文本换行处理
        
        Args:
            text: 要换行的文本
            font: 字体
            max_width: 最大宽度
            
        Returns:
            List[str]: 换行后的文本列表
        """
        lines = []
        paragraphs = text.split('\n')
        
        for paragraph in paragraphs:
            if not paragraph.strip():
                lines.append('')
                continue
            
            words = list(paragraph)  # 中文按字符分割
            current_line = ''
            
            for word in words:
                test_line = current_line + word
                bbox = font.getbbox(test_line)
                width = bbox[2] - bbox[0]
                
                if width <= max_width:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word
            
            if current_line:
                lines.append(current_line)
        
        return lines
    
    def _draw_text_centered(self, draw: ImageDraw.ImageDraw, text: str, 
                           font: ImageFont.FreeTypeFont, y_position: int, 
                           color: tuple, max_width: int) -> int:
        """绘制居中文本
        
        Args:
            draw: ImageDraw对象
            text: 文本内容
            font: 字体
            y_position: Y坐标
            color: 颜色
            max_width: 最大宽度
            
        Returns:
            int: 下一行的Y坐标
        """
        lines = self._wrap_text(text, font, max_width)
        current_y = y_position
        
        for line in lines:
            bbox = font.getbbox(line)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (self.IMAGE_WIDTH - text_width) // 2
            # 调整y坐标以实现垂直居中，补偿bbox的top偏移
            y_adjusted = current_y - bbox[1]
            draw.text((x, y_adjusted), line, font=font, fill=color)
            current_y += text_height + self.LINE_SPACING
        
        return current_y
    
    def title_to_image(self, title: str, output_path: str) -> str:
        """将标题渲染为居中的图片（用于文本请求的第一张图片）
        
        Args:
            title: 标题文本
            output_path: 输出路径
            
        Returns:
            str: 生成的图片路径
        """
        # 创建图片
        img = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # 计算可用宽度
        max_width = self.IMAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        
        # 绘制居中标题（使用大字体）
        start_y = (self.IMAGE_HEIGHT - self.TITLE_IMAGE_FONT_SIZE) // 2
        self._draw_text_centered(draw, title, self.font_title_image, start_y, 
                                self.TITLE_COLOR, max_width)
        
        # 保存图片
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        
        logger.info(f"标题图片已保存: {output_path}")
        return str(output_path)
    
    def summary_to_image(self, title: str, content: str, output_path: str) -> str:
        """将summary的一个元素渲染为图片
        
        Args:
            title: 标题
            content: 内容
            output_path: 输出路径
            
        Returns:
            str: 生成的图片路径
        """
        # 创建图片
        img = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # 计算可用宽度
        max_width = self.IMAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        
        # 计算总内容高度
        total_height = 0
        # 标题高度
        title_lines = self._wrap_text(title, self.font_title, max_width)
        for line in title_lines:
            bbox = self.font_title.getbbox(line)
            total_height += bbox[3] - bbox[1] + self.LINE_SPACING
        
        # 标题和内容之间的间距
        total_height += self.TITLE_CONTENT_SPACING
        
        # 内容高度
        content_lines = self._wrap_text(content, self.font_content, max_width)
        for line in content_lines:
            bbox = self.font_content.getbbox(line)
            total_height += bbox[3] - bbox[1] + self.LINE_SPACING
        
        # 计算起始Y坐标，使内容垂直居中
        start_y = (self.IMAGE_HEIGHT - total_height) // 2
        
        # 绘制标题（左对齐）
        current_y = start_y
        current_y = self._draw_text_left_aligned(draw, title, self.font_title, 
                                                 current_y, self.TITLE_COLOR, max_width)
        
        # 标题和内容之间的间距
        current_y += self.TITLE_CONTENT_SPACING
        
        # 绘制内容（左对齐）
        self._draw_text_left_aligned(draw, content, self.font_content, 
                                     current_y, self.CONTENT_COLOR, max_width)
        
        # 保存图片
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        
        logger.info(f"Summary图片已保存: {output_path}")
        return str(output_path)
    
    def markdown_to_image(self, markdown_text: str, output_path: str) -> str:
        """将markdown文本渲染为图片
        
        Args:
            markdown_text: markdown文本
            output_path: 输出路径
            
        Returns:
            str: 生成的图片路径
        """
        # 创建图片
        img = Image.new('RGB', (self.IMAGE_WIDTH, self.IMAGE_HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        
        # 计算可用宽度
        max_width = self.IMAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        
        # 先计算总内容高度
        total_height = self._calculate_markdown_height(markdown_text, max_width)
        
        # 计算起始Y坐标，使内容垂直居中
        start_y = (self.IMAGE_HEIGHT - total_height) // 2
        
        # 解析markdown并渲染
        current_y = start_y
        current_y = self._render_markdown(draw, markdown_text, current_y, max_width)
        
        # 保存图片
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        
        logger.info(f"Markdown图片已保存: {output_path}")
        return str(output_path)
    
    def _calculate_markdown_height(self, markdown_text: str, max_width: int) -> int:
        """计算markdown内容的总高度
        
        Args:
            markdown_text: markdown文本
            max_width: 最大宽度
            
        Returns:
            int: 总高度
        """
        lines = markdown_text.split('\n')
        total_height = 0
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 空行
            if not line.strip():
                total_height += self.LINE_SPACING
                i += 1
                continue
            
            # 检测表格
            if '|' in line:
                table_lines = []
                j = i
                while j < len(lines) and '|' in lines[j]:
                    table_lines.append(lines[j])
                    j += 1
                
                if len(table_lines) >= 2:
                    total_height += self._calculate_table_height(table_lines, max_width)
                    total_height += self.LINE_SPACING
                    i = j
                    continue
            
            # H1 标题
            if line.startswith('# ') and not line.startswith('## '):
                text = line[2:].strip().replace('**', '')
                wrapped = self._wrap_text(text, self.font_md_h1, max_width)
                for l in wrapped:
                    bbox = self.font_md_h1.getbbox(l)
                    total_height += bbox[3] - bbox[1] + self.LINE_SPACING
                total_height += self.LINE_SPACING
            
            # H2 标题
            elif line.startswith('## ') and not line.startswith('### '):
                text = line[3:].strip().replace('**', '')
                wrapped = self._wrap_text(text, self.font_md_h2, max_width)
                for l in wrapped:
                    bbox = self.font_md_h2.getbbox(l)
                    total_height += bbox[3] - bbox[1] + self.LINE_SPACING
                total_height += self.LINE_SPACING // 2
            
            # H3 标题
            elif line.startswith('### '):
                text = line[4:].strip().replace('**', '')
                wrapped = self._wrap_text(text, self.font_md_h3, max_width)
                for l in wrapped:
                    bbox = self.font_md_h3.getbbox(l)
                    total_height += bbox[3] - bbox[1] + self.LINE_SPACING
                total_height += self.LINE_SPACING // 2
            
            # 列表项
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                indent_level = len(line) - len(line.lstrip())
                text = '• ' + line.strip()[2:].strip().replace('**', '')
                wrapped = self._wrap_text(text, self.font_md_normal, max_width - indent_level - 20)
                for l in wrapped:
                    bbox = self.font_md_normal.getbbox(l)
                    total_height += bbox[3] - bbox[1] + self.LINE_SPACING
            
            # 普通文本
            else:
                text = line.replace('**', '')
                wrapped = self._wrap_text(text, self.font_md_normal, max_width)
                for l in wrapped:
                    bbox = self.font_md_normal.getbbox(l)
                    total_height += bbox[3] - bbox[1] + self.LINE_SPACING
            
            i += 1
        
        return total_height
    
    def _calculate_table_height(self, table_lines: List[str], max_width: int) -> int:
        """计算表格的总高度
        
        Args:
            table_lines: 表格的所有行
            max_width: 最大宽度
            
        Returns:
            int: 表格总高度
        """
        rows = []
        for line in table_lines:
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            if cells and not all('-' in cell or ':' in cell for cell in cells):
                rows.append(cells)
        
        if not rows:
            return 0
        
        num_cols = max(len(row) for row in rows)
        col_width = (max_width - (num_cols + 1) * self.TABLE_BORDER_WIDTH) // num_cols
        
        total_height = 0
        for row in rows:
            while len(row) < num_cols:
                row.append('')
            
            row_height = 0
            for cell in row:
                cell_text = cell.replace('**', '')
                wrapped = self._wrap_text(cell_text, self.font_md_normal, 
                                        col_width - 2 * self.TABLE_CELL_PADDING)
                if wrapped:
                    bbox = self.font_md_normal.getbbox(wrapped[0])
                    line_height = bbox[3] - bbox[1]
                    cell_height = len(wrapped) * (line_height + 5) + 2 * self.TABLE_CELL_PADDING
                    row_height = max(row_height, cell_height)
            
            if row_height == 0:
                row_height = 50
            
            total_height += row_height
        
        return total_height
    
    def _render_markdown(self, draw: ImageDraw.ImageDraw, markdown_text: str, 
                        y_position: int, max_width: int) -> int:
        """渲染markdown文本到图片
        
        Args:
            draw: ImageDraw对象
            markdown_text: markdown文本
            y_position: 起始Y坐标
            max_width: 最大宽度
            
        Returns:
            int: 下一行的Y坐标
        """
        lines = markdown_text.split('\n')
        current_y = y_position
        i = 0
        
        while i < len(lines):
            line = lines[i].rstrip()
            
            # 空行
            if not line.strip():
                current_y += self.LINE_SPACING
                i += 1
                continue
            
            # 检测表格
            if '|' in line:
                # 尝试解析表格
                table_lines = []
                j = i
                while j < len(lines) and '|' in lines[j]:
                    table_lines.append(lines[j])
                    j += 1
                
                # 如果找到至少2行（表头+分隔符），则渲染表格
                if len(table_lines) >= 2:
                    current_y = self._draw_table(draw, table_lines, current_y, max_width)
                    current_y += self.LINE_SPACING
                    i = j
                    continue
            
            # H1 标题 (# )
            if line.startswith('# ') and not line.startswith('## '):
                text = line[2:].strip()
                current_y = self._draw_markdown_line(draw, text, self.font_md_h1, 
                                                     current_y, self.TITLE_COLOR, 
                                                     max_width, indent=0)
                current_y += self.LINE_SPACING
            
            # H2 标题 (## )
            elif line.startswith('## ') and not line.startswith('### '):
                text = line[3:].strip()
                current_y = self._draw_markdown_line(draw, text, self.font_md_h2, 
                                                     current_y, self.TITLE_COLOR, 
                                                     max_width, indent=0)
                current_y += self.LINE_SPACING // 2
            
            # H3 标题 (### )
            elif line.startswith('### '):
                text = line[4:].strip()
                current_y = self._draw_markdown_line(draw, text, self.font_md_h3, 
                                                     current_y, self.TITLE_COLOR, 
                                                     max_width, indent=0)
                current_y += self.LINE_SPACING // 2
            
            # 列表项 (- 或 * )
            elif line.strip().startswith('- ') or line.strip().startswith('* '):
                # 计算缩进
                indent_level = len(line) - len(line.lstrip())
                text = line.strip()[2:].strip()
                # 添加项目符号
                bullet = '• '
                text = bullet + text
                current_y = self._draw_markdown_line(draw, text, self.font_md_normal, 
                                                     current_y, self.CONTENT_COLOR, 
                                                     max_width, indent=indent_level + 20)
            
            # 普通文本（处理粗体）
            else:
                current_y = self._draw_markdown_line_with_bold(draw, line, current_y, 
                                                               max_width)
            
            i += 1
        
        return current_y
    
    def _draw_markdown_line(self, draw: ImageDraw.ImageDraw, text: str, 
                           font: ImageFont.FreeTypeFont, y_position: int, 
                           color: tuple, max_width: int, indent: int = 0) -> int:
        """绘制单行markdown文本
        
        Args:
            draw: ImageDraw对象
            text: 文本内容
            font: 字体
            y_position: Y坐标
            color: 颜色
            max_width: 最大宽度
            indent: 缩进像素
            
        Returns:
            int: 下一行的Y坐标
        """
        # 去除粗体标记（简单处理）
        text = text.replace('**', '')
        
        lines = self._wrap_text(text, font, max_width - indent)
        current_y = y_position
        
        for line in lines:
            x = self.MARGIN_LEFT + indent
            bbox = font.getbbox(line)
            # 调整y坐标以实现垂直居中
            y_adjusted = current_y - bbox[1]
            draw.text((x, y_adjusted), line, font=font, fill=color)
            current_y += bbox[3] - bbox[1] + self.LINE_SPACING
        
        return current_y
    
    def _draw_markdown_line_with_bold(self, draw: ImageDraw.ImageDraw, text: str, 
                                     y_position: int, max_width: int) -> int:
        """绘制带粗体的markdown文本行
        
        Args:
            draw: ImageDraw对象
            text: 文本内容（可能包含**粗体**标记）
            y_position: Y坐标
            max_width: 最大宽度
            
        Returns:
            int: 下一行的Y坐标
        """
        import re
        
        # 分割文本为普通文本和粗体文本
        parts = re.split(r'(\*\*.*?\*\*)', text)
        
        current_y = y_position
        current_x = self.MARGIN_LEFT
        
        for part in parts:
            if not part:
                continue
            
            # 判断是否是粗体
            if part.startswith('**') and part.endswith('**'):
                # 粗体文本
                bold_text = part[2:-2]
                font = self.font_md_bold
                color = self.TITLE_COLOR
            else:
                # 普通文本
                bold_text = part
                font = self.font_md_normal
                color = self.CONTENT_COLOR
            
            # 绘制文本（简单处理，不考虑换行中的粗体）
            lines = self._wrap_text(bold_text, font, max_width)
            for line in lines:
                bbox = font.getbbox(line)
                # 调整y坐标以实现垂直居中
                y_adjusted = current_y - bbox[1]
                draw.text((current_x, y_adjusted), line, font=font, fill=color)
                current_y += bbox[3] - bbox[1] + self.LINE_SPACING
                current_x = self.MARGIN_LEFT
        
        return current_y
    
    def _draw_table(self, draw: ImageDraw.ImageDraw, table_lines: List[str], 
                   y_position: int, max_width: int) -> int:
        """绘制markdown表格
        
        Args:
            draw: ImageDraw对象
            table_lines: 表格的所有行
            y_position: Y坐标
            max_width: 最大宽度
            
        Returns:
            int: 下一行的Y坐标
        """
        # 解析表格数据
        rows = []
        for line in table_lines:
            # 去除首尾的|，然后分割
            cells = [cell.strip() for cell in line.strip('|').split('|')]
            # 跳过分隔符行（包含---的行）
            if cells and not all('-' in cell or ':' in cell for cell in cells):
                rows.append(cells)
        
        if not rows:
            return y_position
        
        # 计算列数
        num_cols = max(len(row) for row in rows)
        
        # 计算每列的宽度（平均分配）
        col_width = (max_width - (num_cols + 1) * self.TABLE_BORDER_WIDTH) // num_cols
        
        # 绘制表格
        current_y = y_position
        
        for row_idx, row in enumerate(rows):
            # 确保所有行有相同的列数
            while len(row) < num_cols:
                row.append('')
            
            # 计算行高（基于最高的单元格）
            row_height = 0
            cell_contents = []
            
            for cell in row:
                # 去除粗体标记
                cell_text = cell.replace('**', '')
                # 换行处理
                wrapped = self._wrap_text(cell_text, self.font_md_normal, 
                                         col_width - 2 * self.TABLE_CELL_PADDING)
                cell_contents.append(wrapped)
                # 计算单元格高度
                if wrapped:
                    bbox = self.font_md_normal.getbbox(wrapped[0])
                    line_height = bbox[3] - bbox[1]
                    cell_height = len(wrapped) * (line_height + 5) + 2 * self.TABLE_CELL_PADDING
                    row_height = max(row_height, cell_height)
            
            # 如果行高为0，使用默认高度
            if row_height == 0:
                row_height = 50
            
            # 绘制单元格边框和内容
            for col_idx, (cell, wrapped_lines) in enumerate(zip(row, cell_contents)):
                x = self.MARGIN_LEFT + col_idx * (col_width + self.TABLE_BORDER_WIDTH)
                
                # 绘制单元格边框
                cell_rect = [
                    x, current_y,
                    x + col_width, current_y + row_height
                ]
                
                # 表头使用浅灰色背景
                if row_idx == 0:
                    draw.rectangle(cell_rect, outline=(100, 100, 100), 
                                 fill=(240, 240, 240), width=self.TABLE_BORDER_WIDTH)
                else:
                    draw.rectangle(cell_rect, outline=(150, 150, 150), 
                                 width=self.TABLE_BORDER_WIDTH)
                
                # 绘制单元格文本
                text_y = current_y + self.TABLE_CELL_PADDING
                for line in wrapped_lines:
                    text_x = x + self.TABLE_CELL_PADDING
                    # 表头使用粗体颜色
                    color = self.TITLE_COLOR if row_idx == 0 else self.CONTENT_COLOR
                    bbox = self.font_md_normal.getbbox(line)
                    # 调整y坐标以实现垂直居中
                    y_adjusted = text_y - bbox[1]
                    draw.text((text_x, y_adjusted), line, font=self.font_md_normal, fill=color)
                    text_y += bbox[3] - bbox[1] + 5
            
            current_y += row_height
        
        return current_y
    
    def _draw_text_left_aligned(self, draw: ImageDraw.ImageDraw, text: str, 
                                font: ImageFont.FreeTypeFont, y_position: int, 
                                color: tuple, max_width: int) -> int:
        """绘制左对齐文本
        
        Args:
            draw: ImageDraw对象
            text: 文本内容
            font: 字体
            y_position: Y坐标
            color: 颜色
            max_width: 最大宽度
            
        Returns:
            int: 下一行的Y坐标
        """
        lines = self._wrap_text(text, font, max_width)
        current_y = y_position
        
        for line in lines:
            bbox = font.getbbox(line)
            # 调整y坐标以实现垂直居中
            y_adjusted = current_y - bbox[1]
            draw.text((self.MARGIN_LEFT, y_adjusted), line, font=font, fill=color)
            current_y += bbox[3] - bbox[1] + self.LINE_SPACING
        
        return current_y
    
    def mermaid_to_image(self, mermaid_code: str, output_path: str = None, 
                        theme: str = "default", background_color: str = "white",
                        scale: float = 3.0, width: int = 3240) -> str:
        """将Mermaid代码转换为图片（高清版本）
        
        Args:
            mermaid_code: Mermaid图表代码
            output_path: 输出图片路径，如果为None则保存到临时目录
            theme: 主题 (default, forest, dark, neutral)
            background_color: 背景颜色 (white, transparent, etc.)
            scale: 缩放比例，用于提高清晰度 (默认3.0，生成3倍分辨率)
            width: 图片宽度（像素），默认3240适合高清显示
            
        Returns:
            str: 生成的图片路径
            
        Raises:
            ValueError: Mermaid代码为空
            Exception: 图片生成失败
        """
        if not mermaid_code or not mermaid_code.strip():
            raise ValueError("Mermaid代码不能为空")
        
        # 确定输出路径
        if output_path is None:
            output_dir = Path(__file__).resolve().parent.parent / "data" / "test_output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "mermaid.png"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"开始生成Mermaid图片: {output_path}")
        
        try:
            # 使用 mermaid.ink 在线服务生成SVG（矢量图，无损质量）
            # 编码mermaid代码
            encoded = base64.urlsafe_b64encode(mermaid_code.encode('utf-8')).decode('ascii')
            
            # 使用SVG端点获取矢量图
            url = f"https://mermaid.ink/svg/{encoded}"
            
            logger.info(f"请求Mermaid.ink服务（SVG格式）: {url[:100]}...")
            
            # 下载SVG
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 先保存SVG文件
            svg_path = output_path.with_suffix('.svg')
            with open(svg_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"SVG文件已保存: {svg_path}")
            
            # 尝试将SVG转换为高清PNG
            try:
                from cairosvg import svg2png
                
                # 使用cairosvg转换为高清PNG
                svg2png(
                    file_obj=open(svg_path, 'rb'),
                    write_to=str(output_path),
                    output_width=width,
                    scale=scale
                )
                
                logger.info(f"高清PNG图片生成成功: {output_path} (宽度={width}px, 缩放={scale}x)")
                return str(output_path)
                
            except ImportError:
                logger.warning("未安装cairosvg，返回SVG文件（矢量图，质量无损）")
                logger.info("提示: SVG是矢量图格式，可直接使用或用其他工具转换")
                logger.info("macOS安装Cairo: brew install cairo")
                logger.info("然后安装: pip install cairosvg")
                return str(svg_path)
            except Exception as e:
                logger.warning(f"SVG转PNG失败: {str(e)[:200]}，返回SVG文件路径")
                logger.info("SVG文件是矢量图，质量无损，可直接使用")
                return str(svg_path)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"请求Mermaid.ink服务失败: {e}")
            raise Exception(f"生成Mermaid图片失败: {e}")
        except Exception as e:
            logger.error(f"生成Mermaid图片时出错: {e}")
            raise
    
    def mermaid_to_image_local(self, mermaid_code: str, output_path: str = None, 
                              scale: float = 2.0, width: int = None, height: int = None,
                              padding: int = 30) -> str:
        """使用本地方法将Mermaid代码转换为高清图片（备用方案，保持3:4比例）
        
        此方法需要安装 playwright
        
        Args:
            mermaid_code: Mermaid图表代码
            output_path: 输出图片路径
            scale: 设备像素比，用于提高清晰度 (默认2.0)
            width: 视口宽度（像素），默认使用IMAGE_WIDTH (1080)
            height: 视口高度（像素），默认使用IMAGE_HEIGHT (1440)，保持3:4比例
            padding: 图表周围的留白（像素），默认30px
            
        Returns:
            str: 生成的图片路径
            
        Raises:
            ImportError: 缺少必要的依赖
            Exception: 图片生成失败
        """
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            raise ImportError(
                "需要安装 playwright 才能使用本地渲染功能。\n"
                "请运行: pip install playwright && playwright install chromium"
            )
        
        if not mermaid_code or not mermaid_code.strip():
            raise ValueError("Mermaid代码不能为空")
        
        # 使用默认的3:4比例尺寸
        if width is None:
            width = self.IMAGE_WIDTH  # 1080
        if height is None:
            height = self.IMAGE_HEIGHT  # 1440
        
        # 确定输出路径
        if output_path is None:
            output_dir = Path(__file__).resolve().parent.parent / "data" / "test_output"
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / "mermaid_local.png"
        else:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"使用本地Playwright生成Mermaid图片: {output_path} (3:4比例)")
        
        # 创建HTML模板，设置容器为3:4比例，最小化留白
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    width: {width}px;
                    height: {height}px;
                    background: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    overflow: hidden;
                }}
                .container {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: {padding}px;
                }}
                .mermaid {{
                    width: 100%;
                    height: 100%;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }}
                .mermaid svg {{
                    max-width: 100% !important;
                    max-height: 100% !important;
                    width: auto !important;
                    height: auto !important;
                }}
            </style>
            <script type="module">
                import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                mermaid.initialize({{ 
                    startOnLoad: true, 
                    theme: 'default',
                    flowchart: {{
                        useMaxWidth: true,
                        htmlLabels: true,
                        curve: 'basis'
                    }}
                }});
            </script>
        </head>
        <body>
            <div class="container">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
        </body>
        </html>
        """
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch()
                # 设置3:4比例的视口和高设备像素比
                page = browser.new_page(
                    viewport={'width': width, 'height': height},
                    device_scale_factor=scale
                )
                
                # 设置页面内容
                page.set_content(html_content)
                
                # 等待mermaid渲染完成
                page.wait_for_timeout(3000)  # 增加等待时间确保完全渲染
                
                # 截取整个页面（保持3:4比例）
                page.screenshot(
                    path=str(output_path),
                    type='png',
                    full_page=False  # 只截取视口大小，保持3:4比例
                )
                
                logger.info(f"高清Mermaid图片生成成功: {output_path} (3:4比例 {width}x{height}, DPR={scale})")
                
                browser.close()
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"使用Playwright生成Mermaid图片失败: {e}")
            raise
    
