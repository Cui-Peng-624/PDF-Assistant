import os
import shutil
from typing import List, Optional
from datetime import datetime

class FileManager:
    """文件管理器"""
    
    def __init__(self, base_dir='files'):
        # 确保base_dir是相对于backend目录的绝对路径
        if not os.path.isabs(base_dir):
            # 获取当前文件所在目录（backend/core）
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # 获取backend目录
            backend_dir = os.path.dirname(current_dir)
            # 构建完整的base_dir路径
            self.base_dir = os.path.join(backend_dir, base_dir)
        else:
            self.base_dir = base_dir
        self.ensure_directories()
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [
            self.base_dir,
            os.path.join(self.base_dir, 'uploads'),
            os.path.join(self.base_dir, 'images'),
            os.path.join(self.base_dir, 'explanations')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def save_uploaded_file(self, file, filename: str) -> str:
        """保存上传的文件"""
        upload_dir = os.path.join(self.base_dir, 'uploads')
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        return file_path
    
    def create_session_directory(self, session_id: str) -> str:
        """为处理会话创建目录"""
        session_dir = os.path.join(self.base_dir, 'sessions', session_id)
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
    
    def create_pdf_workspace(self, pdf_filename: str) -> dict:
        """为PDF文件创建工作空间目录"""
        # 移除文件扩展名
        pdf_name = os.path.splitext(pdf_filename)[0]
        # 清理文件名，移除特殊字符
        safe_name = "".join(c for c in pdf_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        
        workspace = {
            'pdf_name': safe_name,
            'images_dir': os.path.join(self.base_dir, 'images', safe_name),
            'explanations_dir': os.path.join(self.base_dir, 'explanations', safe_name)
        }
        
        # 创建所有必要的目录
        for key, dir_path in workspace.items():
            if key.endswith('_dir'):
                os.makedirs(dir_path, exist_ok=True)
        
        return workspace
    
    def cleanup_old_files(self, days: int = 7):
        """清理旧文件"""
        try:
            current_time = datetime.now().timestamp()
            cutoff_time = current_time - (days * 24 * 60 * 60)
            
            # 清理uploads目录
            upload_dir = os.path.join(self.base_dir, 'uploads')
            if os.path.exists(upload_dir):
                for filename in os.listdir(upload_dir):
                    file_path = os.path.join(upload_dir, filename)
                    if os.path.isfile(file_path):
                        file_time = os.path.getmtime(file_path)
                        if file_time < cutoff_time:
                            os.remove(file_path)
            
            # 清理sessions目录
            sessions_dir = os.path.join(self.base_dir, 'sessions')
            if os.path.exists(sessions_dir):
                for session_id in os.listdir(sessions_dir):
                    session_path = os.path.join(sessions_dir, session_id)
                    if os.path.isdir(session_path):
                        session_time = os.path.getmtime(session_path)
                        if session_time < cutoff_time:
                            shutil.rmtree(session_path)
        except Exception as e:
            print(f"清理文件失败: {e}")
    
    def get_file_size(self, file_path: str) -> int:
        """获取文件大小（字节）"""
        try:
            return os.path.getsize(file_path)
        except OSError:
            return 0
    
    def get_file_info(self, file_path: str) -> dict:
        """获取文件信息"""
        try:
            stat = os.stat(file_path)
            return {
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'exists': True
            }
        except OSError:
            return {
                'size': 0,
                'created': None,
                'modified': None,
                'exists': False
            }
