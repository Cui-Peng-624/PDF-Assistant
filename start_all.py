#!/usr/bin/env python3
"""
同时启动前端和后端服务
"""

import os
import sys
import subprocess
import threading
import time
import webbrowser
import signal

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.running = True
        
    def start_backend(self):
        """启动后端服务"""
        print("启动后端服务...")
        backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
        
        try:
            process = subprocess.Popen(
                [sys.executable, 'run.py'],
                cwd=backend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(process)
            
            # 实时输出后端日志
            for line in iter(process.stdout.readline, ''):
                if self.running:
                    print(f"[后端] {line.rstrip()}")
                else:
                    break
                    
        except Exception as e:
            print(f"[ERROR] 后端启动失败: {e}")
    
    def start_frontend(self):
        """启动前端服务"""
        print("启动前端服务...")
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
        
        try:
            process = subprocess.Popen(
                [sys.executable, '-m', 'http.server', '8080'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            self.processes.append(process)
            
            # 延迟打开浏览器
            time.sleep(3)
            if self.running:
                webbrowser.open('http://localhost:8080')
            
        except Exception as e:
            print(f"[ERROR] 前端启动失败: {e}")
    
    def stop_all(self):
        """停止所有服务"""
        print("\n正在停止所有服务...")
        self.running = False
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(f"停止服务时出错: {e}")
        
        print("[OK] 所有服务已停止")

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在停止服务...")
    service_manager.stop_all()
    sys.exit(0)

def main():
    """主函数"""
    print("PDF智能分析助手 - 启动所有服务")
    print("=" * 50)
    
    # 检查依赖
    print("检查环境...")
    
    # 检查后端依赖
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    if not os.path.exists(os.path.join(backend_dir, 'requirements.txt')):
        print("[ERROR] 找不到backend/requirements.txt")
        return
    
    # 检查前端文件
    frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
    if not os.path.exists(os.path.join(frontend_dir, 'index.html')):
        print("[ERROR] 找不到frontend/index.html")
        return
    
    print("[OK] 环境检查通过")
    print()
    
    # 创建服务管理器
    global service_manager
    service_manager = ServiceManager()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动后端服务（在新线程中）
        backend_thread = threading.Thread(target=service_manager.start_backend)
        backend_thread.daemon = True
        backend_thread.start()
        
        # 等待后端启动
        time.sleep(2)
        
        # 启动前端服务（在新线程中）
        frontend_thread = threading.Thread(target=service_manager.start_frontend)
        frontend_thread.daemon = True
        frontend_thread.start()
        
        print("所有服务已启动！")
        print("前端地址: http://localhost:8080")
        print("后端API: http://localhost:5000")
        print("按 Ctrl+C 停止所有服务")
        print("-" * 50)
        
        # 保持主线程运行
        while service_manager.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        service_manager.stop_all()
    except Exception as e:
        print(f"[ERROR] 启动失败: {e}")
        service_manager.stop_all()

if __name__ == "__main__":
    main()
