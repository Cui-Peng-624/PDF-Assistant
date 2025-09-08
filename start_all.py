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
import socket

# 检测是否在打包环境中运行
def is_frozen():
    """检测是否在PyInstaller打包环境中运行"""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_base_path():
    """获取基础路径"""
    if is_frozen():
        # 打包环境
        return sys._MEIPASS
    else:
        # 开发环境
        return os.path.dirname(os.path.abspath(__file__))

def get_backend_path():
    """获取后端路径"""
    base_path = get_base_path()
    if is_frozen():
        # 打包环境：后端文件在根目录下
        return base_path
    else:
        # 开发环境：后端文件在backend目录下
        return os.path.join(base_path, 'backend')

def get_frontend_path():
    """获取前端路径"""
    base_path = get_base_path()
    if is_frozen():
        # 打包环境：前端文件在frontend子目录下
        return os.path.join(base_path, 'frontend')
    else:
        # 开发环境：前端文件在frontend目录下
        return os.path.join(base_path, 'frontend')

def check_port(port):
    """检查端口是否被占用"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def wait_for_port(port, timeout=10):
    """等待端口可用"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        if check_port(port):
            return True
        time.sleep(0.1)
    return False

class ServiceManager:
    def __init__(self):
        self.processes = []
        self.running = True
        self.base_path = get_base_path()
        self.backend_path = get_backend_path()
        self.frontend_path = get_frontend_path()
        self.frontend_port = None
        self.http_server = None
        self.http_server_thread = None
        self.browser_opened = False  # 防止重复打开浏览器
        
        print(f"基础路径: {self.base_path}")
        print(f"后端路径: {self.backend_path}")
        print(f"前端路径: {self.frontend_path}")
        
    def start_backend(self):
        """启动后端服务"""
        print("启动后端服务...")
        
        if is_frozen():
            # 打包环境：直接导入并运行
            try:
                # 添加后端路径到Python路径
                sys.path.insert(0, self.backend_path)
                
                # 导入并运行Flask应用
                from app import app
                print("后端服务已启动 (打包模式)")
                app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
            except Exception as e:
                print(f"[ERROR] 后端启动失败: {e}")
                import traceback
                traceback.print_exc()
        else:
            # 开发环境：子进程运行
            try:
                process = subprocess.Popen(
                    [sys.executable, 'run.py'],
                    cwd=self.backend_path,
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
        
        # 检查前端目录是否存在
        if not os.path.exists(self.frontend_path):
            print(f"[ERROR] 前端目录不存在: {self.frontend_path}")
            return
        
        # 检查index.html是否存在
        index_file = os.path.join(self.frontend_path, 'index.html')
        if not os.path.exists(index_file):
            print(f"[ERROR] index.html不存在: {index_file}")
            return
        
        print(f"[OK] 前端目录: {self.frontend_path}")
        print(f"[OK] index.html: {index_file}")
        
        try:
            # 检查端口是否被占用，并自动选择可用端口
            port = None
            for test_port in [8080, 8081, 8082, 8083, 8084, 8085]:
                if check_port(test_port):
                    port = test_port
                    print(f"[OK] 使用端口: {port}")
                    break
            
            if port is None:
                print("[ERROR] 无法找到可用端口")
                return
            
            self.frontend_port = port
            print(f"工作目录: {self.frontend_path}")
            
            if is_frozen():
                # 打包环境：使用内置HTTP服务器，减少子进程与环境差异问题
                from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
                class RootedHandler(SimpleHTTPRequestHandler):
                    def __init__(self, *args, **kwargs):
                        # 指定前端目录为根目录
                        kwargs['directory'] = self.server_root
                        super().__init__(*args, **kwargs)
                
                RootedHandler.server_root = self.frontend_path
                server_address = ('0.0.0.0', port)
                self.http_server = ThreadingHTTPServer(server_address, RootedHandler)
                
                def serve_forever():
                    try:
                        self.http_server.serve_forever()
                    except Exception as e:
                        print(f"[HTTP服务器] 运行异常: {e}")
                
                import threading as _threading
                self.http_server_thread = _threading.Thread(target=serve_forever)
                self.http_server_thread.daemon = True
                self.http_server_thread.start()
                
                print(f"[OK] 前端服务已启动（内置），端口: {port}")
            else:
                # 开发环境：使用子进程方式
                print(f"启动HTTP服务器命令: python -m http.server {port} --bind 0.0.0.0")
                process = subprocess.Popen(
                    [sys.executable, '-m', 'http.server', str(port), '--bind', '0.0.0.0'],
                    cwd=self.frontend_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if hasattr(subprocess, 'CREATE_NEW_PROCESS_GROUP') else 0
                )
                self.processes.append(process)
                
                # 实时监控HTTP服务器输出
                import threading
                def monitor_output():
                    try:
                        for line in iter(process.stdout.readline, ''):
                            if line:
                                print(f"[HTTP服务器] {line.strip()}")
                    except Exception as e:
                        print(f"[HTTP服务器监控] 错误: {e}")
                
                monitor_thread = threading.Thread(target=monitor_output)
                monitor_thread.daemon = True
                monitor_thread.start()
            
            # 等待服务稳定
            time.sleep(2)
            
            # 验证端口是否真的在监听（重试3次）
            import socket as _socket
            port_ok = False
            for attempt in range(3):
                try:
                    with _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM) as s:
                        s.settimeout(2)
                        result = s.connect_ex(('localhost', port))
                        if result == 0:
                            print(f"[OK] 端口 {port} 正在监听")
                            port_ok = True
                            break
                        else:
                            print(f"[INFO] 端口检查尝试 {attempt + 1}/3: 端口 {port} 暂未响应")
                            if attempt < 2:
                                time.sleep(1)
                except Exception as e:
                    print(f"[WARNING] 端口检查尝试 {attempt + 1}/3 出错: {e}")
                    if attempt < 2:
                        time.sleep(1)
            
            if not port_ok:
                print(f"[WARNING] 端口 {port} 可能未正确监听，但继续启动浏览器")
            
            # 延迟打开浏览器（只打开一次）
            time.sleep(1)
            if self.running and not self.browser_opened:
                url = f'http://localhost:{port}'
                print(f"正在打开浏览器: {url}")
                webbrowser.open(url)
                self.browser_opened = True
        except Exception as e:
            print(f"[ERROR] 前端启动失败: {e}")
            import traceback
            traceback.print_exc()
    
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
    
    # 检查环境
    if is_frozen():
        print("运行模式: 打包环境")
    else:
        print("运行模式: 开发环境")
    
    # 检查依赖
    print("检查环境...")
    
    # 检查后端文件
    backend_path = get_backend_path()
    if is_frozen():
        # 打包环境：检查关键文件是否存在
        app_file = os.path.join(backend_path, 'app.py')
        if not os.path.exists(app_file):
            print(f"[ERROR] 找不到app.py: {app_file}")
            return
        print(f"[OK] 找到app.py: {app_file}")
    else:
        # 开发环境：检查requirements.txt
        requirements_file = os.path.join(backend_path, 'requirements.txt')
        if not os.path.exists(requirements_file):
            print(f"[ERROR] 找不到requirements.txt: {requirements_file}")
            return
        print(f"[OK] 找到requirements.txt: {requirements_file}")
    
    # 检查前端文件
    frontend_path = get_frontend_path()
    index_file = os.path.join(frontend_path, 'index.html')
    if not os.path.exists(index_file):
        print(f"[ERROR] 找不到index.html: {index_file}")
        return
    print(f"[OK] 找到index.html: {index_file}")
    
    print("[OK] 环境检查通过")
    print()
    
    # 创建服务管理器
    global service_manager
    service_manager = ServiceManager()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if is_frozen():
            # 打包环境：先启动后端，再启动前端
            print("启动后端服务...")
            # 启动后端服务（在新线程中）
            backend_thread = threading.Thread(target=service_manager.start_backend)
            backend_thread.daemon = True
            backend_thread.start()
            
            # 等待后端服务启动
            print("等待后端服务启动...")
            time.sleep(5)  # 增加等待时间确保后端完全启动
            
            # 检查后端服务是否启动成功
            if not wait_for_port(5000, timeout=10):
                print("[WARNING] 后端服务可能未完全启动，继续启动前端...")
            else:
                print("[OK] 后端服务已启动")
            
            # 启动前端服务（在新线程中）
            print("启动前端服务...")
            frontend_thread = threading.Thread(target=service_manager.start_frontend)
            frontend_thread.daemon = True
            frontend_thread.start()
        else:
            # 开发环境：使用原来的逻辑
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
        if service_manager.frontend_port:
            print(f"前端地址: http://localhost:{service_manager.frontend_port}")
        else:
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
        import traceback
        traceback.print_exc()
        service_manager.stop_all()

if __name__ == "__main__":
    main()