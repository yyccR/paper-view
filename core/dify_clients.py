import re
import json
import traceback
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional

import requests
from loguru import logger
import mimetypes


class JSONParseError(Exception):
    """JSON解析错误异常"""
    pass


class DifyAPIClient:
    """Dify API客户端类"""
    def __init__(self, api_key: str = None, max_retries: int = 3, base_delay: int = 1):
        self.max_retries = max_retries
        self.base_delay = base_delay
        # 优先使用传入的api_key，否则从环境变量读取，最后使用默认值
        self.api_key = api_key or os.getenv('DIFY_API_KEY', 'app-BSFod2AonY8NmiaxfogFgstt')
        self.base_url = os.getenv('DIFY_BASE_URL', 'https://difyzzc.zuzuche.com')
    
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
        
        # 处理严重损坏的JSON结构
        # 如果JSON结构过于损坏，尝试提取关键信息重构
        if self._is_severely_malformed(text):
            return self._reconstruct_from_malformed_json(text)
        
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
    
    def _is_severely_malformed(self, text: str) -> bool:
        """检查JSON是否严重损坏
        
        Args:
            text: JSON字符串
            
        Returns:
            bool: 是否严重损坏
        """
        # 检查是否有明显的结构问题
        issues = 0
        
        # 检查是否有不匹配的引号
        quote_count = text.count('"')
        if quote_count % 2 != 0:
            issues += 1
        
        # 检查是否有不完整的对象
        if 'content": "' in text and not text.count('content": "') == text.count('"'):
            issues += 1
            
        # 检查是否有明显的语法错误
        if ': {' in text and not '": {' in text:
            issues += 1
            
        return issues >= 2
    
    def _reconstruct_from_malformed_json(self, text: str) -> str:
        """从严重损坏的JSON中重构数据
        
        Args:
            text: 损坏的JSON字符串
            
        Returns:
            str: 重构后的JSON字符串
        """
        try:
            # 提取title
            title_match = re.search(r'"title":\s*"([^"]*)"', text)
            title = title_match.group(1) if title_match else "未知标题"
            
            # 提取summary数组中的内容
            summary_items = []
            
            # 查找所有的title和content对
            title_pattern = r'"title":\s*"([^"]*)"'
            content_pattern = r'"content":\s*"([^"]*(?:[^"\\]|\\.)*)"'
            
            titles = re.findall(title_pattern, text)
            contents = re.findall(content_pattern, text)
            
            # 跳过第一个title（这是主标题）
            if len(titles) > 1:
                for i in range(1, len(titles)):
                    content = contents[i-1] if i-1 < len(contents) else ""
                    summary_items.append({
                        "title": titles[i],
                        "content": content
                    })
            
            # 如果没有找到足够的数据，创建基本结构
            if not summary_items:
                # 尝试提取任何可用的文本内容
                text_content = re.sub(r'[{}"\[\],:]', ' ', text)
                text_content = ' '.join(text_content.split())
                if len(text_content) > 100:
                    text_content = text_content[:500] + "..."
                
                summary_items = [{
                    "title": "内容摘要",
                    "content": text_content
                }]
            
            # 提取mermaid内容（如果存在）
            mermaid_match = re.search(r'"mermaid":\s*"([^"]*(?:[^"\\]|\\.)*)"', text, re.DOTALL)
            mermaid = mermaid_match.group(1) if mermaid_match else ""
            
            # 构建重构后的JSON
            reconstructed = {
                "title": title,
                "summary": summary_items,
                "mermaid": mermaid
            }
            
            return json.dumps(reconstructed, ensure_ascii=False)
            
        except Exception as e:
            logger.warning(f"重构JSON失败: {e}")
            # 返回最基本的结构
            return json.dumps({
                "title": "解析失败",
                "summary": [{"title": "原始内容", "content": text[:500] + "..."}],
                "mermaid": ""
            }, ensure_ascii=False)
    
    def _parse_json_field(self, value: Any) -> Any:
        """解析可能是JSON字符串的字段
        
        Args:
            value: 待解析的值，可能是dict、list、str或None
            
        Returns:
            解析后的Python对象
            
        Raises:
            JSONParseError: JSON解析失败
        """
        # 如果已经是dict或list，直接返回
        if isinstance(value, (dict, list)):
            return value
        
        if value is None:
            raise JSONParseError("值为 None，无法解析为JSON")
        
        # 去除可能的markdown代码块标记
        cleaned = self._strip_md_code_fence(str(value))
        
        # 清理无效控制字符
        cleaned = self._clean_json_string(cleaned)
        
        # 修复JSON结构问题
        cleaned = self._fix_json_structure(cleaned)
        
        # 尝试直接解析
        try:
            return json.loads(cleaned)
        except Exception:
            logger.error(f"json.loads(cleaned): {traceback.format_exc()}")
            # 尝试提取JSON对象
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                snippet = cleaned[start: end + 1]
                try:
                    # 再次清理和修复提取的片段
                    snippet = self._clean_json_string(snippet)
                    snippet = self._fix_json_structure(snippet)
                    return json.loads(snippet)
                except Exception as e2:
                    raise JSONParseError(f"JSON解析失败: {e2}")
            
            # 尝试提取JSON数组
            start = cleaned.find("[")
            end = cleaned.rfind("]")
            if start != -1 and end != -1 and end > start:
                snippet = cleaned[start: end + 1]
                try:
                    # 再次清理和修复提取的片段
                    snippet = self._clean_json_string(snippet)
                    snippet = self._fix_json_structure(snippet)
                    return json.loads(snippet)
                except Exception as e3:
                    raise JSONParseError(f"JSON解析失败: {e3}")
            
            raise JSONParseError("未找到可解析的JSON对象或数组")
    
    def _append_error_record(self, payload: Dict, reason: str, raw_outputs: Any = None, error_msg: str = None):
        """记录错误请求到文件
        
        Args:
            payload: 请求参数
            reason: 错误原因
            raw_outputs: 原始输出
            error_msg: 错误消息
        """
        try:
            base_dir = Path(__file__).resolve().parent.parent
            error_dir = base_dir / "logs"
            error_dir.mkdir(exist_ok=True)
            file_path = error_dir / "dify_error_record.txt"
            
            record = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                "reason": reason,
                "request_params": payload.get("inputs", {}),
                "api_key": self.api_key[:20] + "..." if self.api_key else None,
            }
            if error_msg:
                record["error"] = str(error_msg)
            if raw_outputs is not None:
                record["raw_outputs"] = raw_outputs
            
            with file_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            
            logger.info(f"错误记录已保存到: {file_path}")
        except Exception:
            logger.exception("记录失败请求到 dify_error_record.txt 时出错")

    def _format_mermaid(self, mermaid_text: str) -> str:
        """格式化mermaid字符串，处理转义字符
        
        Args:
            mermaid_text: 原始mermaid文本，可能包含转义字符
            
        Returns:
            str: 格式化后的mermaid文本
        """
        if not isinstance(mermaid_text, str):
            return str(mermaid_text) if mermaid_text else ""
        
        # 处理常见的转义字符
        # 将 \" 转换为 "
        # 将 \n 保持为实际换行符（如果需要）
        formatted = mermaid_text.replace('\\"', '"')
        
        return formatted
    
    def run_workflow(self, pdf_path: str = None, question: str = None, user: str = "xhs_daily_user") -> Dict[str, Any]:
        """运行Dify工作流，支持PDF文件和问题参数
        
        Args:
            pdf_path: 本地PDF文件路径（可选）
            question: 问题文本（可选）
            user: 用户标识
            
        Returns:
            Dict: 包含title和summary的字典，如果传入pdf_path则还包含mermaid字段
            {
                "title": "标题",
                "summary": [
                    {"title": "章节标题", "content": "章节内容"},
                    ...
                ],
                "mermaid": "mermaid图表代码"  # 仅当pdf_path不为空时返回
            }
            
        Raises:
            ValueError: pdf_path和question都为空，或文件格式错误
            FileNotFoundError: PDF文件不存在
            Exception: API调用失败
        """
        # 至少需要提供一个参数
        if not pdf_path and not question:
            raise ValueError("pdf_path和question至少需要提供一个参数")
        
        # 构建inputs
        inputs = {}
        
        # 处理PDF文件
        if pdf_path:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF文件不存在: {pdf_path}")
            
            if pdf_file.suffix.lower() != '.pdf':
                raise ValueError(f"文件不是PDF格式: {pdf_path}")
            
            # 上传文件获取upload_file_id
            logger.info(f"开始上传PDF文件: {pdf_path}")
            upload_file_id = self.upload_file(pdf_path)
            logger.info(f"文件上传成功，upload_file_id: {upload_file_id}")
            
            inputs["file"] = [
                {
                    "transfer_method": "local_file",
                    "type": "document",
                    "upload_file_id": upload_file_id
                }
            ]
        
        # 处理问题参数
        if question:
            inputs["question"] = question
            logger.info(f"添加问题参数: {question[:100]}..." if len(question) > 100 else f"添加问题参数: {question}")
        
        # 构建workflow请求
        url = f'{self.base_url}/v1/workflows/run'
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": inputs,
            "response_mode": "blocking",
            "user": user
        }
        
        # 执行workflow
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(f"执行workflow - 尝试 {attempt + 1}/{self.max_retries + 1}")
                logger.info(f"请求payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                
                response = requests.post(url, headers=headers, json=payload, timeout=300)
                response.raise_for_status()
                response_data = response.json()
                
                logger.info(f"Dify API响应成功: {response.status_code}")
                logger.info(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                
                # 解析返回结果
                outputs = response_data.get('data', {}).get('outputs', {})
                
                # 如果outputs是字符串，尝试解析为JSON
                if isinstance(outputs, str):
                    try:
                        outputs = json.loads(outputs)
                    except Exception:
                        pass

                if not isinstance(outputs, dict):
                    raise JSONParseError("outputs 不是字典，无法解析需要的字段")
                
                # 获取text字段
                result_text = outputs.get('result', '')
                
                # 尝试解析JSON格式的返回结果
                try:
                    result = self._parse_json_field(result_text)
                except JSONParseError as e:
                    logger.warning(f"JSON解析失败: {e}，使用默认结构")
                    result = {
                        "title": "未知标题",
                        "summary": [{"title": "内容", "content": result_text}]
                    }
                
                # 验证返回结构
                if not isinstance(result, dict):
                    result = {
                        "title": "未知标题",
                        "summary": [{"title": "内容", "content": str(result)}]
                    }
                
                # 解析嵌套的JSON字段
                title = result.get('title', '未知标题')
                summary_raw = result.get('summary', [])
                mermaid_raw = result.get('mermaid', '')
                
                # 如果summary是字符串，尝试解析
                if isinstance(summary_raw, str):
                    try:
                        summary_parsed = self._parse_json_field(summary_raw)
                        if not isinstance(summary_parsed, list):
                            raise JSONParseError("summary字段不是数组")
                        summary_raw = summary_parsed
                    except JSONParseError:
                        summary_raw = [{"title": "内容", "content": summary_raw}]
                
                # 确保summary是列表
                if not isinstance(summary_raw, list):
                    summary_raw = []
                
                # 构建最终结果
                result = {
                    "title": str(title) if title else "未知标题",
                    "summary": summary_raw
                }
                
                # 只有当pdf_path不为空时，才添加mermaid字段
                if pdf_path:
                    mermaid_formatted = self._format_mermaid(mermaid_raw)
                    result["mermaid"] = mermaid_formatted
                
                return result
                
            except Exception as e:
                is_parse_error = isinstance(e, JSONParseError) or "JSON解析失败" in str(e) or "outputs 不是字典" in str(e)
                
                if attempt >= self.max_retries:
                    if is_parse_error:
                        raw = None
                        try:
                            raw = response_data.get('data', {}).get('outputs')
                        except Exception:
                            raw = None
                        self._append_error_record(payload, reason="json_parse_failed", raw_outputs=raw, error_msg=str(e))
                        logger.error(f"解析JSON失败且已重试{self.max_retries + 1}次，已记录请求参数")
                    
                    logger.error(f"重试次数耗尽: {traceback.format_exc()}")
                    raise
                
                delay = self.base_delay * (2 ** attempt)
                logger.warning(f"请求失败 ({attempt + 1}/{self.max_retries + 1}): {str(e)}, 等待 {delay} 秒后重试")
                time.sleep(delay)

    def upload_file(self, file_path: str, user: str = "xhs_daily_user") -> str:
        """上传文件到Dify
        
        Args:
            file_path: 文件路径
            user: 用户标识
            
        Returns:
            str: 上传文件的ID
            
        Raises:
            FileNotFoundError: 文件不存在
            Exception: 上传失败
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        url = f'{self.base_url}/v1/files/upload'
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, mime_type)}
            data = {'user': user}
            
            for attempt in range(self.max_retries + 1):
                try:
                    response = requests.post(url, headers=headers, files=files, data=data, timeout=300)
                    response.raise_for_status()
                    response_data = response.json()
                    logger.info(f"文件上传成功: {response.status_code}")
                    return response_data.get('id')
                except Exception as e:
                    if attempt >= self.max_retries:
                        logger.error(f"文件上传重试次数耗尽: {traceback.format_exc()}")
                        raise
                    delay = self.base_delay * (2 ** attempt)
                    logger.warning(f"文件上传失败 ({attempt + 1}/{self.max_retries + 1}): {str(e)}, 等待 {delay} 秒后重试")
                    time.sleep(delay)
    
    def parse_pdf_workflow(self, pdf_path: str, user: str = "xhs_daily_user") -> Dict[str, Any]:
        """解析PDF工作流（向后兼容方法）
        
        此方法保留用于向后兼容，内部调用run_workflow。
        请使用run_workflow方法以获取更多功能。
        
        Args:
            pdf_path: 本地PDF文件路径
            user: 用户标识
            
        Returns:
            Dict: 包含title和summary的字典
        """
        logger.warning("使用已废弃的parse_pdf_workflow方法，请改用run_workflow")
        return self.run_workflow(pdf_path=pdf_path, user=user)