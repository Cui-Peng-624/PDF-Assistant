#!/usr/bin/env python3
"""
PDF智能分析助手 - 后端启动脚本
"""

import os
import sys
import subprocess
from app import app

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import flask_cors
        import openai
        import pdf2image
        from PIL import Image
        print("[OK] 所有Python依赖已安装")
        return True
    except ImportError as e:
        print(f"[ERROR] 缺少依赖: {e}")
        print("请运行: pip install -r requirements.txt")
        return False

def check_poppler():
    """检查poppler是否安装"""
    try:
        result = subprocess.run(['pdftoppm', '-h'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("[OK] Poppler已安装")
            return True
    except FileNotFoundError:
        pass
    
    print("[ERROR] Poppler未安装")
    print("请根据您的操作系统安装Poppler:")
    print("Windows: 下载并安装 poppler for Windows")
    print("Ubuntu/Debian: sudo apt-get install poppler-utils")
    print("macOS: brew install poppler")
    return False

def main():
    """主函数"""
    print("启动PDF智能分析助手后端服务...")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    if not check_poppler():
        print("[WARNING] Poppler未安装，PDF转换功能可能无法使用")
        response = input("是否继续启动? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    print("=" * 50)
    print("启动Web服务器...")
    print("后端API地址: http://localhost:5000")
    print("API文档: http://localhost:5000/api/health")
    print("按 Ctrl+C 停止服务器")
    print("=" * 50)
    
    # 启动Flask应用
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
