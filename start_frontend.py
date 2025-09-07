#!/usr/bin/env python3
"""
启动前端服务
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading

def start_frontend():
    """启动前端HTTP服务器"""
    print("启动PDF智能分析助手前端服务...")
    
    # 切换到frontend目录
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    os.chdir(frontend_dir)
    
    print(f"工作目录: {os.getcwd()}")
    
    # 检查index.html是否存在
    if not os.path.exists('index.html'):
        print("[ERROR] 找不到index.html文件")
        return
    
    # 启动HTTP服务器
    print("启动HTTP服务器...")
    print("前端服务地址: http://localhost:8080")
    print("应用入口: http://localhost:8080/index.html")
    print("按 Ctrl+C 停止服务")
    print("-" * 50)
    
    def open_browser():
        """延迟打开浏览器"""
        time.sleep(2)
        webbrowser.open('http://localhost:8080')
    
    # 在新线程中打开浏览器
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # 使用Python内置的HTTP服务器
        subprocess.run([sys.executable, '-m', 'http.server', '8080'], check=True)
    except KeyboardInterrupt:
        print("\n前端服务已停止")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] 启动失败: {e}")

if __name__ == "__main__":
    start_frontend()
