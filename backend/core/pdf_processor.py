import os
import base64
from typing import List, Dict, Callable, Optional
from pdf2image import convert_from_path
from openai import OpenAI
from dotenv import load_dotenv
import time

# 加载环境变量
load_dotenv()

class PDFProcessor:
    """PDF处理器"""
    
    def __init__(self):
        self.client = None
    
    def create_client(self, api_key: Optional[str] = None, api_base: Optional[str] = None):
        """创建OpenAI客户端"""
        if api_key is None:
            api_key = os.getenv("ZETATECHS_API_KEY")
        if api_base is None:
            api_base = os.getenv("ZETATECHS_API_BASE")
        
        self.client = OpenAI(api_key=api_key, base_url=api_base)
    
    def pdf_to_images(self, pdf_path: str, output_dir: str) -> List[str]:
        """将PDF转换为图片"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 转换PDF为图片
        images = convert_from_path(pdf_path, dpi=300)  # 提高DPI以获得更好的质量
        
        image_paths = []
        for i, page in enumerate(images):
            image_filename = f"page_{i + 1:03d}.png"
            image_path = os.path.join(output_dir, image_filename)
            page.save(image_path, 'PNG', optimize=True)
            image_paths.append(image_path)
        
        return image_paths
    
    def encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    
    def analyze_image(self, image_path: str, prompt: str, system_prompt: str, 
                     model: str = "gpt-4.1-2025-04-14") -> str:
        """使用LLM分析图片，包含重试机制（最多3次，1秒间隔）"""
        if not self.client:
            raise ValueError("客户端未初始化，请先调用create_client")
        
        # 编码图片
        base64_image = self.encode_image(image_path)
        
        last_error = None
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt,
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=4000,
                    temperature=0.7
                )
                return response.choices[0].message.content
            except Exception as e:
                last_error = e
                if attempt < max_retries:
                    time.sleep(1)
                else:
                    raise Exception(f"LLM分析失败(已重试{max_retries}次): {str(e)}")
    
    def process_pdf(self, file_path: str, workspace: dict, prompt: str, 
                   system_prompt: str, api_key: Optional[str] = None, 
                   api_base: Optional[str] = None, model: str = "gpt-4.1-2025-04-14",
                   progress_callback: Optional[Callable] = None, 
                   cancel_check: Optional[Callable] = None) -> List[Dict]:
        """处理PDF文件的主函数"""
        
        # 创建客户端
        self.create_client(api_key, api_base)
        
        # 使用工作空间目录
        images_dir = workspace['images_dir']
        explanations_dir = workspace['explanations_dir']
        pdf_name = workspace['pdf_name']
        
        # 转换PDF为图片
        if progress_callback:
            progress_callback(0, 0, "正在转换PDF为图片...")
        
        image_paths = self.pdf_to_images(file_path, images_dir)
        total_pages = len(image_paths)
        
        if progress_callback:
            progress_callback(0, total_pages, f"PDF转换完成，共{total_pages}页")
        
        results = []
        
        # 处理每一页
        for i, image_path in enumerate(image_paths):
            page_num = i + 1
            
            # 检查是否被取消
            if cancel_check and cancel_check():
                if progress_callback:
                    progress_callback(page_num, total_pages, "任务已取消")
                break
            
            if progress_callback:
                progress_callback(page_num, total_pages, f"正在处理第{page_num}页...")
            
            try:
                # 分析图片
                explanation = self.analyze_image(
                    image_path=image_path,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model=model
                )
                
                # 保存解释文件
                explanation_filename = f"page_{page_num:03d}.md"
                explanation_path = os.path.join(explanations_dir, explanation_filename)
                
                with open(explanation_path, "w", encoding="utf-8") as f:
                    f.write(f"# {pdf_name} - 第{page_num}页分析结果\n\n")
                    f.write(f"**PDF文件**: {pdf_name}\n")
                    f.write(f"**页码**: 第{page_num}页\n")
                    f.write(f"**处理时间**: {os.path.getctime(image_path)}\n")
                    f.write(f"**图片路径**: {image_path}\n\n")
                    f.write("---\n\n")
                    f.write(explanation)
                
                # 保存结果信息
                result = {
                    'page': page_num,
                    'image_path': image_path,
                    'explanation_path': explanation_path,
                    'explanation': explanation,
                    'explanation_preview': explanation[:200] + "..." if len(explanation) > 200 else explanation,
                    'success': True,
                    'pdf_name': pdf_name
                }
                
                results.append(result)
                
            except Exception as e:
                # 记录错误
                error_result = {
                    'page': page_num,
                    'image_path': image_path,
                    'explanation_path': None,
                    'explanation': None,
                    'explanation_preview': f"处理失败: {str(e)}",
                    'success': False,
                    'error': str(e),
                    'pdf_name': pdf_name
                }
                results.append(error_result)
                
                if progress_callback:
                    progress_callback(page_num, total_pages, f"第{page_num}页处理失败: {str(e)}")
        
        if progress_callback:
            progress_callback(total_pages, total_pages, "处理完成！")
        
        return results
