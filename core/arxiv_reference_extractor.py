"""
ArXiv 参考文献提取器
负责下载PDF、提取文本、识别参考文献部分并使用LLM进行结构化处理
"""
import os
import re
import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
import PyPDF2
import fitz  # PyMuPDF

try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

from core.llm.factory import LLMFactory


class ArxivReferenceExtractor:
    """ArXiv 参考文献提取器"""
    
    def __init__(
        self,
        pdf_download_dir: Optional[str] = None,
        llm_provider: str = 'qwen',
        llm_model: str = 'qwen3-max',
        request_timeout: int = 60,
        max_retries: int = 3,
        llm_timeout: int = 180
    ):
        """
        初始化提取器
        
        Args:
            pdf_download_dir: PDF下载目录，默认为 data/arxiv_pdfs
            llm_provider: LLM提供商
            llm_model: LLM模型名称
            request_timeout: HTTP请求超时时间（秒）
            max_retries: 最大重试次数
            llm_timeout: LLM API超时时间（秒），默认180秒
        """
        if not PDF_SUPPORT:
            raise ImportError("请安装 PyPDF2: pip install PyPDF2")
        
        # 设置PDF下载目录
        if pdf_download_dir is None:
            base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
            pdf_download_dir = os.path.join(base_dir, 'data', 'arxiv_pdfs')
        
        self.pdf_download_dir = Path(pdf_download_dir)
        self.pdf_download_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM配置
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.llm_client = None
        self.llm_timeout = llm_timeout
        
        # 请求配置
        self.request_timeout = request_timeout
        self.max_retries = max_retries
        
        # 参考文献部分的常见标题（更精确的匹配）
        # 要求在行首，且可能有编号或特殊格式
        # (?:\d+\.?\s+)? 表示可选的编号前缀，如 "7. "
        # \.? 表示可选的尾部句点，如 "References."
        self.reference_section_patterns = [
            r'^\s*(?:\d+\.?\s+)?References?\.?\s*$',  # References / References. / 7. References.
            r'^\s*(?:\d+\.?\s+)?REFERENCES?\.?\s*$',  # REFERENCES.
            r'^\s*(?:\d+\.?\s+)?Bibliography\.?\s*$',  # Bibliography.
            r'^\s*(?:\d+\.?\s+)?BIBLIOGRAPHY\.?\s*$',  # BIBLIOGRAPHY.
            r'^\s*(?:\d+\.?\s+)?Bibliographical\s+References?\.?\s*$',  # Bibliographical References.
            r'^\s*(?:\d+\.?\s+)?BIBLIOGRAPHICAL\s+REFERENCES?\.?\s*$',
            r'^\s*(?:\d+\.?\s+)?Bibliographic\s+References?\.?\s*$',  # Bibliographic References.
            r'^\s*(?:\d+\.?\s+)?References?\s+and\s+Notes?\.?\s*$',
            r'^\s*(?:\d+\.?\s+)?Literature\s+Cited\.?\s*$',
            r'^\s*(?:\d+\.?\s+)?Works?\s+Cited\.?\s*$',
            r'^\s*(?:\d+\.?\s+)?Citations?\.?\s*$',
            r'^\s*(?:\d+\.?\s+)?References?\s+Cited\.?\s*$',
        ]
    
    def _get_llm_client(self):
        """获取LLM客户端（延迟初始化）"""
        if self.llm_client is None:
            # 使用自定义配置创建LLM客户端，设置更长的超时时间
            from core.llm.config import LLMConfig, LLMProviderConfig
            import os
            
            # 从环境变量获取配置
            provider_config = LLMConfig.get_provider_config(self.llm_provider)
            api_key = os.getenv(f"{self.llm_provider.upper()}_API_KEY")
            
            if not api_key:
                raise ValueError(f"未找到 {self.llm_provider.upper()}_API_KEY 环境变量")
            
            config = LLMProviderConfig(
                provider=self.llm_provider,
                api_key=api_key,
                base_url=provider_config['base_url'],
                model=self.llm_model,
                max_tokens=8000,
                temperature=0.1,
                timeout=self.llm_timeout  # 使用更长的超时时间
            )
            
            self.llm_client = LLMFactory.create(
                provider=self.llm_provider,
                config=config
            )
        return self.llm_client
    
    def download_pdf(self, pdf_url: str, arxiv_id: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        下载PDF文件
        
        Args:
            pdf_url: PDF下载链接
            arxiv_id: arXiv ID
            
        Returns:
            (成功标志, 文件路径, 错误信息)
        """
        # 生成文件名（使用arxiv_id作为文件名）
        safe_id = arxiv_id.replace('/', '_').replace(':', '_')
        pdf_filename = f"{safe_id}.pdf"
        pdf_path = self.pdf_download_dir / pdf_filename
        
        # 如果文件已存在且不为空，直接返回
        if pdf_path.exists() and pdf_path.stat().st_size > 0:
            return True, str(pdf_path), None
        
        # 下载PDF
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    pdf_url,
                    timeout=self.request_timeout,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                response.raise_for_status()
                
                # 保存文件
                with open(pdf_path, 'wb') as f:
                    f.write(response.content)
                
                # 验证文件大小
                if pdf_path.stat().st_size == 0:
                    raise ValueError("下载的PDF文件为空")
                
                return True, str(pdf_path), None
                
            except Exception as e:
                error_msg = f"下载失败 (尝试 {attempt + 1}/{self.max_retries}): {str(e)}"
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                return False, None, error_msg
        
        return False, None, "下载失败：超过最大重试次数"
    
    def extract_text_from_pdf(self, pdf_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        从PDF提取文本，优先使用PyMuPDF处理多栏布局
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            (成功标志, 提取的文本, 错误信息)
        """
        # 优先使用 PyMuPDF (fitz)，它对多栏布局处理更好
        try:
            return self._extract_with_pymupdf(pdf_path)
        except Exception as e:
            # 如果失败，回退到 PyPDF2
            try:
                return self._extract_with_pypdf2(pdf_path)
            except Exception as e2:
                return False, None, f"PDF文本提取失败 (PyMuPDF: {str(e)}, PyPDF2: {str(e2)})"
    
    def _extract_with_pymupdf(self, pdf_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        使用PyMuPDF (fitz)提取文本，智能处理多栏布局
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            (成功标志, 提取的文本, 错误信息)
        """
        try:
            doc = fitz.open(pdf_path)
            text_parts = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # 使用 "blocks" 模式提取文本块
                blocks = page.get_text("blocks")
                
                # 过滤掉空块
                blocks = [b for b in blocks if len(b) >= 5 and b[4].strip()]
                
                if not blocks:
                    continue
                
                # 智能排序：检测是否为多栏布局
                page_text = self._sort_blocks_for_reading(blocks, page.rect.width)
                
                if page_text:
                    text_parts.append('\n'.join(page_text))
            
            doc.close()
            
            if not text_parts:
                return False, None, "无法从PDF中提取文本"
            
            full_text = '\n\n'.join(text_parts)
            return True, full_text, None
            
        except Exception as e:
            raise Exception(f"PyMuPDF提取失败: {str(e)}")
    
    def _sort_blocks_for_reading(self, blocks: List, page_width: float) -> List[str]:
        """
        智能排序文本块，正确处理单栏和多栏布局
        
        Args:
            blocks: 文本块列表 [(x0, y0, x1, y1, text, block_no, block_type), ...]
            page_width: 页面宽度
            
        Returns:
            按阅读顺序排列的文本列表
        """
        if not blocks:
            return []
        
        # 检测是否为双栏布局
        # 简单启发式：检查是否有明显的左右两组块
        x_coords = [b[0] for b in blocks]  # x0 坐标
        mid_x = page_width / 2
        
        left_blocks = [b for b in blocks if b[0] < mid_x and b[2] < mid_x * 1.2]
        right_blocks = [b for b in blocks if b[0] > mid_x * 0.8]
        
        # 如果左右两边都有足够多的块，认为是双栏布局
        is_two_column = len(left_blocks) > 3 and len(right_blocks) > 3
        
        if is_two_column:
            # 双栏布局：先左栏从上到下，再右栏从上到下
            sorted_text = []
            
            # 左栏：按 y 坐标排序
            left_blocks.sort(key=lambda b: b[1])
            for block in left_blocks:
                sorted_text.append(block[4].strip())
            
            # 右栏：按 y 坐标排序
            right_blocks.sort(key=lambda b: b[1])
            for block in right_blocks:
                sorted_text.append(block[4].strip())
            
            return sorted_text
        else:
            # 单栏布局或不规则布局：按 (y, x) 坐标排序
            blocks.sort(key=lambda b: (b[1], b[0]))
            return [block[4].strip() for block in blocks]
    
    def _extract_with_pypdf2(self, pdf_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        使用PyPDF2提取文本（备选方案）
        
        Args:
            pdf_path: PDF文件路径
            
        Returns:
            (成功标志, 提取的文本, 错误信息)
        """
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 提取所有页面的文本
                text_parts = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
                
                if not text_parts:
                    return False, None, "无法从PDF中提取文本"
                
                full_text = '\n\n'.join(text_parts)
                return True, full_text, None
                
        except Exception as e:
            raise Exception(f"PyPDF2提取失败: {str(e)}")
    
    def find_reference_section(self, text: str) -> Tuple[bool, Optional[str], int]:
        """
        查找并提取参考文献部分
        
        Args:
            text: PDF提取的完整文本
            
        Returns:
            (找到标志, 参考文献文本, 起始位置)
        """
        best_match = None
        best_score = -1
        
        # 尝试多个模式查找参考文献部分
        for pattern in self.reference_section_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            
            # 对每个匹配进行验证和评分
            for match in matches:
                start_pos = match.start()
                
                # 验证这是否是真正的参考文献章节开始
                score = self._validate_reference_section_start(text, start_pos)
                
                # 选择得分最高的匹配
                if score > best_score:
                    best_score = score
                    best_match = (start_pos, match)
        
        # 如果找到了可靠的匹配（得分 >= 2）
        if best_match and best_score >= 2:
            start_pos, match = best_match
            
            # 提取从匹配位置开始的文本
            text_after_ref = text[start_pos:]
            
            # 查找参考文献部分的结束位置
            end_pos = self._find_reference_section_end(text_after_ref)
            if end_pos > 0:
                reference_text = text_after_ref[:end_pos]
                print(f"  ℹ️  参考文献文本被截断，长度: {len(reference_text)} 字符")
            else:
                reference_text = text_after_ref
                print(f"  ℹ️  使用全部剩余文本，长度: {len(reference_text)} 字符")
            
            # 基本验证：确保提取的文本不是太短也不是太长
            if len(reference_text) < 100:
                print(f"  ⚠️  参考文献文本太短 ({len(reference_text)} 字符)，可能检测错误")
                # 如果太短，尝试使用全部剩余文本
                reference_text = text_after_ref
                print(f"  ℹ️  改用全部剩余文本，长度: {len(reference_text)} 字符")
            
            if 100 < len(reference_text) < 50000:
                return True, reference_text, start_pos
            elif len(reference_text) >= 50000:
                print(f"  ⚠️  参考文献文本过长 ({len(reference_text)} 字符)，将在后续截断")
                return True, reference_text, start_pos
        
        # 如果没有找到明确的标题，尝试启发式检测
        print("  ℹ️  未找到明确标题，尝试启发式检测...")
        heuristic_result = self._heuristic_reference_detection(text)
        if heuristic_result[0]:
            return heuristic_result
        
        return False, None, -1
    
    def _validate_reference_section_start(self, text: str, pos: int) -> int:
        """
        验证某个位置是否是真正的参考文献章节开始
        
        Args:
            text: 完整文本
            pos: 匹配位置
            
        Returns:
            int: 得分，越高越可靠（范围 0-10）
        """
        score = 0
        
        # 1. 位置评分：越靠后得分越高（参考文献通常在文末）
        text_length = len(text)
        position_ratio = pos / text_length
        if position_ratio > 0.8:  # 在后 20% 的位置
            score += 3
        elif position_ratio > 0.6:  # 在后 40% 的位置
            score += 2
        elif position_ratio > 0.4:  # 在后 60% 的位置
            score += 1
        
        # 2. 上下文验证：检查前后文本
        # 获取匹配位置所在行以及前后几行
        start = max(0, pos - 200)
        end = min(len(text), pos + 500)
        context = text[start:end]
        lines = context.split('\n')
        
        # 找到包含 'References' 的那一行
        ref_line_idx = -1
        for i, line in enumerate(lines):
            if pos - start >= sum(len(l) + 1 for l in lines[:i]) and \
               pos - start < sum(len(l) + 1 for l in lines[:i+1]):
                ref_line_idx = i
                break
        
        if ref_line_idx >= 0:
            # 检查该行是否相对独立（不在句子中间）
            ref_line = lines[ref_line_idx].strip()
            
            # 如果这一行只有 'References' 和可能的编号，得分更高
            if re.match(r'^\s*(?:\d+\.?\s+)?REFERENCES?\s*$', ref_line, re.IGNORECASE):
                score += 3
            elif len(ref_line) < 30:  # 行很短，可能是标题
                score += 2
            
            # 检查后面几行是否有典型的参考文献格式
            next_lines = lines[ref_line_idx+1:ref_line_idx+6]
            reference_patterns_found = 0
            for next_line in next_lines:
                next_line_stripped = next_line.strip()
                # 检测常见的参考文献格式
                if re.match(r'^\[\d+\]', next_line_stripped):  # [1], [2], ...
                    reference_patterns_found += 1
                elif re.match(r'^\d+\.', next_line_stripped):  # 1., 2., ...
                    reference_patterns_found += 1
                elif re.search(r'\(\d{4}\)', next_line_stripped):  # 年份 (2020)
                    reference_patterns_found += 1
                elif re.search(r'et al\.', next_line_stripped, re.IGNORECASE):  # et al.
                    reference_patterns_found += 1
            
            if reference_patterns_found >= 2:
                score += 2
            elif reference_patterns_found >= 1:
                score += 1
        
        return score
    
    def _find_reference_section_end(self, reference_text: str) -> int:
        """
        查找参考文献部分的结束位置，过滤掉附录、致谢等非参考文献内容
        
        Args:
            reference_text: 从参考文献标题开始的文本
            
        Returns:
            int: 参考文献部分的结束位置（相对于reference_text的开始），如果找不到则返回-1
        """
        # 定义参考文献之后可能出现的章节标题模式（只检测非常明确的标志）
        # 采用更严格的匹配，避免误判
        end_section_patterns = [
            # 附录 - 各种常见格式
            r'^\s*[A-Z]\s+Appendi(x|ces)\s*$',  # A Appendix, B Appendix
            r'^\s*Appendi(x|ces)\s+[A-Z]\s*[:\.]?\s*',  # Appendix A, Appendix A:, Appendix A.
            r'^\s*Appendi(x|ces)\s*$',  # 只有 Appendix 的行
            r'^\s*[A-Z]\s*\.\s*Appendi(x|ces)',  # A. Appendix
            r'^\s*[A-Z]\.[0-9]+\s+',  # A.1 Details... (附录子标题，必须有编号)
            # 移除过于宽泛的模式：r'^\s*[A-Z]\s+[A-Z][a-z]+\s+[A-Z]' 会误匹配普通句子
            r'^\s*Supplementary\s+(Materials?|Information)',
            r'^\s*Supporting\s+Information',
            
            # 致谢 - 单独成行
            r'^\s*Acknowledgeme?nts?\s*$',
            
            # 作者信息 - 单独成行
            r'^\s*Author\s+(Information|Contributions?)',
            r'^\s*Authors?[\']?\s+Contributions?',
            r'^\s*Competing\s+Interests?',
            r'^\s*Conflict\s+of\s+Interests?',
            r'^\s*Data\s+Availability',
            r'^\s*Code\s+Availability',
        ]
        
        # 按行分析文本
        lines = reference_text.split('\n')
        
        # 用于检测是否在页码行之后（页码通常是单独的数字行）
        last_line_was_number = False
        
        # 只检测非常明确的章节标题
        current_pos = 0
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            current_pos += len(line) + 1  # +1 for newline
            
            # 跳过前5行（参考文献标题本身）
            if i < 5:
                continue
            
            # 检测页码行（通常是1-2个数字）
            if line_stripped.isdigit() and len(line_stripped) <= 3:
                last_line_was_number = True
                continue
            
            # 如果上一行是页码，当前行可能是新章节标题，更加敏感
            sensitivity_threshold = 80 if last_line_was_number else 50
            
            # 只有当行长度较短且匹配特定模式时才认为是章节标题
            if len(line_stripped) < sensitivity_threshold:
                for pattern in end_section_patterns:
                    if re.search(pattern, line_stripped, re.IGNORECASE):
                        # 找到了明确的结束标志
                        print(f"  ℹ️  检测到参考文献结束标志: {line_stripped}")
                        return current_pos - len(line) - 1
            
            # 如果当前行不是空行，重置页码标志
            if line_stripped:
                last_line_was_number = False
        
        # 默认不截断，使用全部文本
        return -1
    
    def parse_references_with_llm(
        self,
        reference_text: str,
        arxiv_id: str,
        max_chars: int = 50000
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str], Optional[str]]:
        """
        使用LLM解析参考文献
        
        Args:
            reference_text: 参考文献部分的文本
            arxiv_id: arXiv ID（用于日志）
            max_chars: 最大字符数限制（默认50000，避免超时）
            
        Returns:
            (成功标志, 参考文献列表, 错误信息, LLM原始响应)
        """
        # 截取文本以适应LLM上下文限制
        original_length = len(reference_text)
        if len(reference_text) > max_chars:
            reference_text = reference_text[:max_chars]
            print(f"  ⚠️  参考文献文本过长 ({original_length} 字符)，已截取至 {max_chars} 字符")
        
        # 构建提示词
        prompt = self._build_reference_extraction_prompt(reference_text)
        
        llm_raw_response = None  # 存储LLM原始响应
        
        try:
            llm_client = self._get_llm_client()
            
            # 调用LLM
            response = llm_client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的学术文献解析助手，擅长从论文中提取和结构化参考文献信息。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 使用较低的温度以获得更稳定的输出
                max_tokens=8000
            )
            
            # 解析返回的JSON
            content = response.get('content', '')
            llm_raw_response = content  # 保存原始响应
            
            references = self._parse_llm_response(content)
            
            if references is None:
                return False, None, "LLM返回的格式无效", llm_raw_response
            
            return True, references, None, llm_raw_response
            
        except Exception as e:
            error_msg = f"LLM处理失败: {str(e)}"
            return False, None, error_msg, llm_raw_response
    
    def _strip_md_code_fence(self, text: str) -> str:
        """去除markdown代码块标记
        
        Args:
            text: 可能包含markdown代码块的文本
            
        Returns:
            str: 去除代码块标记后的文本
        """
        if not isinstance(text, str):
            return text
        
        s = text.strip()
        
        # 匹配 ```json ... ``` 或 ```... ``` 格式
        m = re.match(r"^\s*```[a-zA-Z0-9_-]*\s*(.*?)\s*```\s*$", s, re.DOTALL)
        if m:
            return m.group(1).strip()
        return s
    
    def _clean_json_string(self, text: str) -> str:
        """清理JSON字符串中的无效控制字符
        
        Args:
            text: 原始JSON字符串
            
        Returns:
            str: 清理后的JSON字符串
        """
        if not isinstance(text, str):
            return text
        
        # 移除或替换常见的无效控制字符
        # 保留合法的控制字符：\t (tab), \n (newline), \r (carriage return)
        cleaned = ""
        for char in text:
            # 获取字符的Unicode码点
            code = ord(char)
            # 保留可打印字符、空格、制表符、换行符、回车符
            if (code >= 32 and code <= 126) or code in (9, 10, 13) or code >= 128:
                cleaned += char
            else:
                # 将其他控制字符替换为空格或移除
                if code < 32:  # 控制字符
                    cleaned += " "  # 替换为空格
        
        return cleaned
    
    def _fix_json_structure(self, text: str) -> str:
        """修复常见的JSON结构问题
        
        Args:
            text: 可能有结构问题的JSON字符串
            
        Returns:
            str: 修复后的JSON字符串
        """
        if not isinstance(text, str):
            return text
        
        # 去除多余的空白字符
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                cleaned_lines.append(line)
        
        # 重新组合
        text = '\n'.join(cleaned_lines)
        
        # 修复常见的JSON语法问题
        # 1. 在对象结束前添加缺失的逗号
        text = re.sub(r'"\s*\n\s*{', '",\n{', text)  # 在对象前添加逗号
        text = re.sub(r'"\s*\n\s*"', '",\n"', text)  # 在字符串前添加逗号
        text = re.sub(r'}\s*\n\s*{', '},\n{', text)  # 在对象间添加逗号
        text = re.sub(r'}\s*\n\s*"', '},\n"', text)  # 在对象和字符串间添加逗号
        
        # 2. 修复数组中的逗号问题
        text = re.sub(r'}\s*\n\s*]', '}\n]', text)  # 数组结束前不需要逗号
        
        # 3. 处理字符串中的换行符
        # 将字符串内的实际换行符转换为\n转义序列
        in_string = False
        escape_next = False
        result = []
        
        for char in text:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
                
            if char == '\\':
                escape_next = True
                result.append(char)
                continue
                
            if char == '"' and not escape_next:
                in_string = not in_string
                result.append(char)
                continue
                
            if in_string and char == '\n':
                result.append('\\n')  # 转换为转义序列
            else:
                result.append(char)
        
        return ''.join(result)
    
    def _build_reference_extraction_prompt(self, reference_text: str) -> str:
        """构建参考文献提取的提示词"""
        return f"""请从以下学术论文的参考文献部分提取所有参考文献，并将每条参考文献转换为结构化的JSON格式。

参考文献部分内容：
```
{reference_text}
```

请按照以下JSON格式返回结果（返回一个JSON数组，每个元素是一条参考文献）：
```json
[
  {{
    "reference_number": 1,
    "title": "论文标题",
    "authors": ["作者1", "作者2", "作者3"],
    "year": 2023,
    "venue": "发表场所（期刊名或会议名）",
    "venue_type": "journal/conference/arxiv/book/thesis/tech_report/other",
    "volume": "卷号（如果有）",
    "issue": "期号（如果有）",
    "pages": "页码范围（如果有）",
    "doi": "DOI标识符（如果有）",
    "arxiv_id": "arXiv标识符（如果有）",
    "url": "在线链接（如果有）",
    "raw_text": "原始参考文献文本"
  }}
]
```

要求：
1. 尽可能提取所有字段，如果某个字段不存在，设置为null
2. reference_number 是参考文献的序号（从1开始）
3. authors 应该是一个字符串数组
4. year 应该是整数类型
5. venue_type 应该从提供的选项中选择最合适的一个
6. raw_text 保留原始的参考文献文本
7. 只返回JSON数组，不要包含其他解释性文字
8. 如果无法解析某条参考文献，可以跳过

请开始提取："""
    
    def _parse_llm_response(self, content: str) -> Optional[List[Dict]]:
        """解析LLM返回的内容"""
        try:
            # 去除可能的markdown代码块标记
            cleaned = self._strip_md_code_fence(content)
            
            # 清理无效控制字符
            cleaned = self._clean_json_string(cleaned)
            
            # 修复JSON结构问题
            cleaned = self._fix_json_structure(cleaned)
            
            # 尝试直接解析JSON
            references = json.loads(cleaned)
            if isinstance(references, list):
                return references
            
            # 如果返回的是字典，尝试提取列表
            if isinstance(references, dict):
                for key in ['references', 'data', 'result', 'items']:
                    if key in references and isinstance(references[key], list):
                        return references[key]
            
            return None
            
        except json.JSONDecodeError:
            # 尝试提取JSON数组
            try:
                # 再次尝试清理和修复
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end != -1 and end > start:
                    snippet = content[start: end + 1]
                    snippet = self._clean_json_string(snippet)
                    snippet = self._fix_json_structure(snippet)
                    references = json.loads(snippet)
                    if isinstance(references, dict):
                        for key in ['references', 'data', 'result', 'items']:
                            if key in references and isinstance(references[key], list):
                                return references[key]
                    return None
            except json.JSONDecodeError:
                pass
            
            # 尝试提取JSON数组
            try:
                start = content.find("[")
                end = content.rfind("]")
                if start != -1 and end != -1 and end > start:
                    snippet = content[start: end + 1]
                    snippet = self._clean_json_string(snippet)
                    snippet = self._fix_json_structure(snippet)
                    references = json.loads(snippet)
                    if isinstance(references, list):
                        return references
            except json.JSONDecodeError:
                pass
            
            return None
    
    def extract_reference_text_only(
        self,
        paper_id: int,
        arxiv_id: str,
        pdf_url: str,
        progress_callback=None
    ) -> Dict:
        """
        只提取参考文献原始文本（不调用LLM）
        
        Args:
            paper_id: 论文数据库ID
            arxiv_id: arXiv ID
            pdf_url: PDF下载链接
            progress_callback: 进度回调函数，接收 (step_name: str, details: str) 参数
            
        Returns:
            处理结果字典
        """
        result = {
            'success': False,
            'paper_id': paper_id,
            'arxiv_id': arxiv_id,
            'pdf_downloaded': False,
            'pdf_path': None,
            'pdf_size': None,
            'text_extracted': False,
            'reference_section_found': False,
            'reference_text': None,
            'reference_text_length': 0,
            'error_type': None,
            'error_message': None,
        }
        
        local_pdf_path = None
        
        try:
            # 步骤1: 下载PDF
            if progress_callback:
                progress_callback('downloading', f'正在下载PDF: {pdf_url}')
            
            success, local_pdf_path, error = self.download_pdf(pdf_url, arxiv_id)
            if not success:
                result['error_type'] = 'download_error'
                result['error_message'] = error
                if progress_callback:
                    progress_callback('download_failed', f'下载失败: {error}')
                return result
            
            result['pdf_downloaded'] = True
            result['pdf_path'] = pdf_url
            result['pdf_size'] = os.path.getsize(local_pdf_path)
            
            if progress_callback:
                progress_callback('downloaded', f'下载成功，文件大小: {result["pdf_size"] / 1024:.1f} KB')
            
            # 步骤2: 提取文本
            if progress_callback:
                progress_callback('extracting_text', '正在从PDF提取文本...')
            
            success, full_text, error = self.extract_text_from_pdf(local_pdf_path)
            if not success:
                result['error_type'] = 'extraction_error'
                result['error_message'] = error
                if progress_callback:
                    progress_callback('extraction_failed', f'文本提取失败: {error}')
                return result
            
            result['text_extracted'] = True
            
            if progress_callback:
                progress_callback('text_extracted', f'文本提取成功，共 {len(full_text)} 字符')
            
            # 步骤3: 查找参考文献部分
            if progress_callback:
                progress_callback('finding_references', '正在定位参考文献部分...')
            
            success, reference_text, start_pos = self.find_reference_section(full_text)
            if not success:
                result['error_type'] = 'reference_not_found'
                result['error_message'] = '未找到参考文献部分'
                if progress_callback:
                    progress_callback('reference_not_found', '未找到参考文献部分')
                return result
            
            result['reference_section_found'] = True
            result['reference_text'] = reference_text
            result['reference_text_length'] = len(reference_text)
            result['success'] = True
            
            if progress_callback:
                progress_callback('references_found', f'找到参考文献部分，长度: {len(reference_text)} 字符')
            
            return result
            
        finally:
            # 处理完成后，删除本地PDF文件以节省空间
            if local_pdf_path and os.path.exists(local_pdf_path):
                try:
                    os.remove(local_pdf_path)
                except Exception:
                    pass
    
    def process_reference_text_with_llm(
        self,
        reference_text: str,
        arxiv_id: str,
        max_chars: int = 50000
    ) -> Tuple[bool, Optional[List[Dict]], Optional[str], Optional[str]]:
        """
        对已提取的参考文献原始文本进行LLM处理
        
        Args:
            reference_text: 已提取的参考文献原始文本
            arxiv_id: arXiv ID（用于日志）
            max_chars: 最大字符数限制
            
        Returns:
            (成功标志, 参考文献列表, 错误信息, LLM原始响应)
        """
        return self.parse_references_with_llm(reference_text, arxiv_id, max_chars)
    
    def process_paper(
        self,
        paper_id: int,
        arxiv_id: str,
        pdf_url: str,
        progress_callback=None
    ) -> Dict:
        """
        处理单篇论文（完整流程）
        
        Args:
            paper_id: 论文数据库ID
            arxiv_id: arXiv ID
            pdf_url: PDF下载链接
            progress_callback: 进度回调函数，接收 (step_name: str, details: str) 参数
            
        Returns:
            处理结果字典
        """
        result = {
            'success': False,
            'paper_id': paper_id,
            'arxiv_id': arxiv_id,
            'pdf_downloaded': False,
            'pdf_path': None,  # 保存arXiv PDF链接
            'pdf_size': None,
            'text_extracted': False,
            'reference_section_found': False,
            'llm_processed': False,
            'references': [],
            'reference_count': 0,
            'error_type': None,
            'error_message': None,
            'llm_response': None,  # LLM原始响应（用于调试）
        }
        
        local_pdf_path = None  # 临时本地PDF路径
        
        try:
            # 步骤1: 下载PDF
            if progress_callback:
                progress_callback('downloading', f'正在下载PDF: {pdf_url}')
            
            success, local_pdf_path, error = self.download_pdf(pdf_url, arxiv_id)
            if not success:
                result['error_type'] = 'download_error'
                result['error_message'] = error
                if progress_callback:
                    progress_callback('download_failed', f'下载失败: {error}')
                return result
            
            result['pdf_downloaded'] = True
            result['pdf_path'] = pdf_url  # 保存arXiv的PDF链接而非本地路径
            result['pdf_size'] = os.path.getsize(local_pdf_path)
            
            if progress_callback:
                progress_callback('downloaded', f'下载成功，文件大小: {result["pdf_size"] / 1024:.1f} KB')
            
            # 步骤2: 提取文本
            if progress_callback:
                progress_callback('extracting_text', '正在从PDF提取文本...')
            
            success, full_text, error = self.extract_text_from_pdf(local_pdf_path)
            if not success:
                result['error_type'] = 'extraction_error'
                result['error_message'] = error
                if progress_callback:
                    progress_callback('extraction_failed', f'文本提取失败: {error}')
                return result
            
            result['text_extracted'] = True
            
            if progress_callback:
                progress_callback('text_extracted', f'文本提取成功，共 {len(full_text)} 字符')
            
            # 步骤3: 查找参考文献部分
            if progress_callback:
                progress_callback('finding_references', '正在定位参考文献部分...')
            
            success, reference_text, start_pos = self.find_reference_section(full_text)
            if not success:
                result['error_type'] = 'reference_not_found'
                result['error_message'] = '未找到参考文献部分'
                if progress_callback:
                    progress_callback('reference_not_found', '未找到参考文献部分')
                return result
            
            result['reference_section_found'] = True
            
            if progress_callback:
                progress_callback('references_found', f'找到参考文献部分，长度: {len(reference_text)} 字符')
            
            # 步骤4: 使用LLM解析参考文献
            if progress_callback:
                progress_callback('llm_processing', f'正在调用 {self.llm_provider}/{self.llm_model} 解析参考文献...')
            
            success, references, error, llm_response = self.parse_references_with_llm(
                reference_text,
                arxiv_id
            )
            
            # 保存LLM原始响应（无论成功或失败）
            result['llm_response'] = llm_response
            
            if not success:
                result['error_type'] = 'llm_error'
                result['error_message'] = error
                if progress_callback:
                    progress_callback('llm_failed', f'LLM处理失败: {error}')
                return result
            
            result['llm_processed'] = True
            result['references'] = references
            result['reference_count'] = len(references)
            result['success'] = True
            
            if progress_callback:
                progress_callback('llm_completed', f'LLM解析完成，提取到 {len(references)} 条参考文献')
            
            return result
            
        finally:
            # 处理完成后，删除本地PDF文件以节省空间
            if local_pdf_path and os.path.exists(local_pdf_path):
                try:
                    os.remove(local_pdf_path)
                except Exception:
                    pass  # 忽略删除失败的情况
    
    def _heuristic_reference_detection(self, text: str) -> Tuple[bool, Optional[str], int]:
        """
        启发式检测参考文献部分（针对没有明确标题的情况）
        
        策略：
        1. 在文档后 30% 的位置开始搜索
        2. 查找密集出现的引用编号模式（如 [1], [2] 或 1., 2.)
        3. 检测是否有典型的参考文献格式
        
        Args:
            text: 完整文本
            
        Returns:
            (found, reference_text, start_pos)
        """
        # 只在文档后部搜索（70% 位置开始）
        search_start = int(len(text) * 0.7)
        search_text = text[search_start:]
        lines = search_text.split('\n')
        
        # 引用编号模式
        citation_patterns = [
            r'^\s*\[\d+\]\s+',  # [1] Author...
            r'^\s*\d+\.\s+[A-Z]',  # 1. Author...
            r'^\s*\[\d+\]\s*[A-Z]',  # [1]Author...
        ]
        
        # 记录每行是否匹配引用模式
        matches = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if len(line_stripped) < 10:  # 太短的行跳过
                continue
                
            for pattern in citation_patterns:
                if re.match(pattern, line_stripped):
                    matches.append(i)
                    break
        
        # 如果找到足够多的匹配，认为是参考文献部分
        if len(matches) >= 3:
            # 对匹配进行排序
            sorted_matches = sorted(matches)
            start_line = sorted_matches[0]
            
            # 如果找到很多匹配 (>= 5)，直接认为成功
            if len(matches) >= 5:
                # 向前回溯几行，可能有分隔线或空行
                while start_line > 0 and len(lines[start_line - 1].strip()) < 5:
                    start_line -= 1
                
                reference_text = '\n'.join(lines[start_line:])
                actual_start_pos = search_start + sum(len(lines[i]) + 1 for i in range(start_line))
                
                if len(reference_text) > 100:
                    print(f"  ✅ 启发式检测成功！找到 {len(matches)} 个引用模式")
                    
                    # 查找结束位置
                    end_pos = self._find_reference_section_end(reference_text)
                    if end_pos > 0:
                        reference_text = reference_text[:end_pos]
                        print(f"  ℹ️  参考文献文本被截断，长度: {len(reference_text)} 字符")
                    
                    return True, reference_text, actual_start_pos
            
            # 如果只有 3-4 个匹配，检查它们是否集中
            else:
                first_matches = sorted_matches[:5] if len(sorted_matches) >= 5 else sorted_matches
                if len(first_matches) >= 3:
                    span = first_matches[-1] - first_matches[0]
                    # 如果匹配在 20 行以内，认为找到了参考文献
                    if span <= 20:
                        # 向前回溯几行
                        while start_line > 0 and len(lines[start_line - 1].strip()) < 5:
                            start_line -= 1
                        
                        reference_text = '\n'.join(lines[start_line:])
                        actual_start_pos = search_start + sum(len(lines[i]) + 1 for i in range(start_line))
                        
                        if len(reference_text) > 100:
                            print(f"  ✅ 启发式检测成功！找到 {len(matches)} 个引用模式")
                            
                            # 查找结束位置
                            end_pos = self._find_reference_section_end(reference_text)
                            if end_pos > 0:
                                reference_text = reference_text[:end_pos]
                                print(f"  ℹ️  参考文献文本被截断，长度: {len(reference_text)} 字符")
                            
                            return True, reference_text, actual_start_pos
        
        print(f"  ⚠️  启发式检测失败（只找到 {len(matches)} 个引用模式）")
        return False, None, -1
    
    def cleanup_old_pdfs(self, days: int = 30):
        """
        清理旧的PDF文件
        
        Args:
            days: 保留最近多少天的文件
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        deleted_count = 0
        for pdf_file in self.pdf_download_dir.glob('*.pdf'):
            if pdf_file.stat().st_mtime < cutoff_time:
                try:
                    pdf_file.unlink()
                    deleted_count += 1
                except Exception:
                    pass
        
        return deleted_count
