"""
论文处理器模块
用于处理PDF论文和Dify返回结果，生成图片和保存数据
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from core.image_generator import ImageGenerator


class PaperImageProcessor:
    """论文图片处理器类
    
    负责将PDF和Dify返回的数据转换为图片，并保存JSON结果
    """
    
    def __init__(self):
        """初始化处理器"""
        self.image_generator = ImageGenerator()
    
    def process(self, pdf_path: str = None, dify_result: Dict[str, Any] = None, 
                output_dir: Path = None) -> Dict[str, Any]:
        """处理PDF/文本和Dify结果，生成所有图片和JSON文件
        
        Args:
            pdf_path: PDF文件路径（可选，如果为None则为文本请求）
            dify_result: Dify返回的结果字典，包含title, summary, mermaid(可选)
            output_dir: 输出目录（可选，如果为None则使用pdf_path的父目录）
            
        Returns:
            Dict[str, Any]: 处理结果
            {
                "json_path": "JSON文件路径",
                "images": ["图片路径列表"],
                "success": True/False,
                "error": "错误信息（如果有）"
            }
        """
        # 确定输出目录
        if output_dir is None:
            if pdf_path:
                pdf_file = Path(pdf_path)
                output_dir = pdf_file.parent
            else:
                raise ValueError("pdf_path和output_dir至少需要提供一个")
        
        result = {
            "json_path": None,
            "images": [],
            "success": True,
            "error": None
        }
        
        try:
            # 1. 保存Dify返回的JSON数据
            json_path = self._save_json(output_dir, dify_result)
            result["json_path"] = str(json_path)
            
            # 2. 生成所有图片
            images = self._generate_images(pdf_path, dify_result, output_dir)
            result["images"] = images
            
            logger.info(f"处理完成: JSON文件 + {len(images)} 张图片")
            
        except Exception as e:
            logger.error(f"处理失败: {e}")
            result["success"] = False
            result["error"] = str(e)
        
        return result
    
    def _save_json(self, output_dir: Path, dify_result: Dict[str, Any]) -> Path:
        """保存Dify返回的JSON数据
        
        Args:
            output_dir: 输出目录
            dify_result: Dify返回的结果
            
        Returns:
            Path: JSON文件路径
        """
        json_path = output_dir / "dify_result.json"
        
        try:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(dify_result, f, ensure_ascii=False, indent=2)
            logger.info(f"Dify结果已保存到: {json_path}")
            return json_path
        except Exception as e:
            logger.error(f"保存Dify结果JSON失败: {e}")
            raise
    
    def _generate_images(self, pdf_path: str, dify_result: Dict[str, Any], 
                        output_dir: Path) -> List[str]:
        """生成所有图片
        
        Args:
            pdf_path: PDF文件路径（可选，如果为None则为文本请求）
            dify_result: Dify返回的结果
            output_dir: 输出目录
            
        Returns:
            List[str]: 生成的所有图片路径列表
        """
        generated_images = []
        summary_list = dify_result.get('summary', [])
        mermaid_text = dify_result.get('mermaid', '')
        
        if pdf_path:
            # ===== PDF流程 =====
            # 1. 生成PDF第一页图片 (1.png)
            try:
                img_path = self.image_generator.pdf_first_page_to_image(
                    pdf_path, output_dir / "1.png"
                )
                generated_images.append(img_path)
                logger.info(f"生成PDF第一页图片: {img_path}")
            except Exception as e:
                logger.error(f"生成PDF第一页图片失败: {e}")
            
            # 2. 生成mermaid图片 (2.png)
            if mermaid_text:
                try:
                    # 优先使用本地Playwright渲染（避免cairo依赖问题）
                    try:
                        img_path = self.image_generator.mermaid_to_image_local(
                            mermaid_text, str(output_dir / "2.png")
                        )
                    except ImportError:
                        # 如果没有安装playwright，回退到在线服务
                        logger.warning("未安装playwright，使用在线服务生成mermaid图片")
                        img_path = self.image_generator.mermaid_to_image(
                            mermaid_text, str(output_dir / "2.png")
                        )
                    generated_images.append(img_path)
                    logger.info(f"生成mermaid图片: {img_path}")
                except Exception as e:
                    logger.error(f"生成mermaid图片失败: {e}")
            
            # 3. 生成summary图片 (3.png, 4.png, ...)
            for idx, item in enumerate(summary_list, start=3):
                try:
                    title = item.get('title', '标题')
                    content = item.get('content', '')
                    output_path = output_dir / f"{idx}.png"
                    img_path = self.image_generator.summary_to_image(title, content, output_path)
                    generated_images.append(img_path)
                except Exception as e:
                    logger.error(f"生成summary图片 {idx}.png 失败: {e}")
        else:
            # ===== 文本流程 =====
            # 1. 生成居中标题图片 (1.png)
            try:
                title = dify_result.get('title', '未知标题')
                img_path = self.image_generator.title_to_image(
                    title, output_dir / "1.png"
                )
                generated_images.append(img_path)
                logger.info(f"生成标题图片: {img_path}")
            except Exception as e:
                logger.error(f"生成标题图片失败: {e}")
            
            # 2. 生成summary图片 (2.png, 3.png, ...)
            for idx, item in enumerate(summary_list, start=2):
                try:
                    title = item.get('title', '标题')
                    content = item.get('content', '')
                    output_path = output_dir / f"{idx}.png"
                    img_path = self.image_generator.summary_to_image(title, content, output_path)
                    generated_images.append(img_path)
                except Exception as e:
                    logger.error(f"生成summary图片 {idx}.png 失败: {e}")
        
        logger.info(f"共生成 {len(generated_images)} 张图片")
        return generated_images
