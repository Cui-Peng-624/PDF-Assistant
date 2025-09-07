#!/usr/bin/env python3
"""
启动后端服务
"""

import os
import sys
import subprocess

def start_backend():
    """启动后端Flask服务"""
    print("启动PDF智能分析助手后端服务...")
    
    # 切换到backend目录
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)
    
    print(f"工作目录: {os.getcwd()}")
    
    # 检查requirements.txt是否存在
    if not os.path.exists('requirements.txt'):
        print("[ERROR] 找不到requirements.txt文件")
        return
    
    # 检查Python依赖
    print("检查Python依赖...")
    try:
        import flask
        import pdf2image
        import openai
        print("[OK] 依赖检查通过")
    except ImportError as e:
        print(f"[ERROR] 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return
    
    # 启动Flask应用
    print("启动Flask服务器...")
    print("后端服务地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/health")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    try:
        subprocess.run([sys.executable, 'run.py'], check=True)
    except KeyboardInterrupt:
        print("\n后端服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 启动失败: {e}")

if __name__ == "__main__":
    start_backend()
