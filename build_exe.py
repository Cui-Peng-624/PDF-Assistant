#!/usr/bin/env python3
"""
PDF智能分析助手 - 打包脚本
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build_dirs():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"已清理目录: {dir_name}")

def create_spec_file():
    """创建PyInstaller配置文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# 收集所有数据文件
datas = [
    ('frontend', 'frontend'),
    ('backend/core', 'core'),
    ('backend/files', 'files'),
    ('backend/config.json', '.'),
    ('backend/requirements.txt', '.'),
    ('backend/app.py', '.'),
    ('backend/run.py', '.'),
]

# 收集隐藏导入
hiddenimports = [
    'flask',
    'flask_cors',
    'openai',
    'pdf2image',
    'PIL',
    'PIL.Image',
    'werkzeug',
    'requests',
    'dotenv',
    'threading',
    'subprocess',
    'webbrowser',
    'signal',
    'zipfile',
    'io',
    'base64',
    'json',
    'os',
    'sys',
    'time',
    'datetime',
    'tempfile',
    'shutil',
    'pathlib'
]

a = Analysis(
    ['start_all.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PDF智能分析助手',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
    
    with open('PDF智能分析助手.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)
    print("已创建PyInstaller配置文件")

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 使用spec文件构建
    cmd = [
        'pyinstaller',
        '--clean',
        '--noconfirm',
        'PDF智能分析助手.spec'
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False

def create_launcher_script():
    """创建启动脚本"""
    launcher_content = '''@echo off
chcp 65001 >nul
title PDF智能分析助手

echo ========================================
echo    PDF智能分析助手
echo ========================================
echo.
echo 正在启动应用（自动选择可用端口 8080-8085），请稍候...
echo.

"PDF智能分析助手.exe"

echo.
echo 应用已关闭，按任意键退出...
pause >nul
'''
    
    with open('dist/启动PDF智能分析助手.bat', 'w', encoding='utf-8') as f:
        f.write(launcher_content)
    print("已创建启动脚本")

def create_readme():
    """创建使用说明"""
    readme_content = '''# PDF智能分析助手 - 使用说明

## 快速开始

1. 双击 "启动PDF智能分析助手.bat" 启动应用
2. 等待浏览器自动打开（程序会自动选择 8080-8085 中的一个可用端口）
   - 如果没有自动打开，请根据控制台中显示的“前端地址”手动访问，例如 http://localhost:8081
3. 在网页中配置API信息并上传PDF文件

## 系统要求

- Windows 10/11
- 至少2GB可用内存
- 至少500MB可用磁盘空间

## 使用步骤

### 1. 配置API
- 在网页顶部填写您的API Key和API Base URL
- 选择使用的AI模型
- 点击"保存配置"和"测试连接"

### 2. 上传PDF
- 拖拽PDF文件到上传区域或点击选择文件
- 支持最大50MB的PDF文件
- 可以自定义分析提示词

### 3. 开始分析
- 点击"上传并开始分析"
- 等待AI分析完成
- 查看分析结果

### 4. 管理文件
- 在文件管理区域查看所有已处理的文件
- 点击"预览"浏览分析结果
- 点击"下载"下载ZIP格式的分析结果
- 点击"删除"删除不需要的文件

## 常见问题

### Q: 应用启动失败怎么办？
A: 请确保您的系统支持运行exe文件，并检查是否有杀毒软件阻止。

### Q: 浏览器没有自动打开怎么办？
A: 请手动打开浏览器，访问控制台中显示的地址（例如 http://localhost:8082）

### Q: API连接失败怎么办？
A: 请检查您的网络连接和API配置是否正确。

### Q: PDF处理失败怎么办？
A: 请确保PDF文件没有密码保护，且文件大小不超过50MB。

## 技术支持

如遇到问题，请检查：
1. 系统是否满足要求
2. 网络连接是否正常
3. API配置是否正确
4. PDF文件是否符合要求

## 更新说明

当前版本：v2.0.0
- 支持PDF智能分析
- 支持文件管理
- 支持预览功能
- 支持ZIP下载
'''
    
    with open('dist/使用说明.txt', 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("已创建使用说明")

def main():
    """主函数"""
    print("PDF智能分析助手 - 打包工具")
    print("=" * 50)
    
    # 检查当前目录
    if not os.path.exists('start_all.py'):
        print("❌ 错误：请在项目根目录下运行此脚本")
        return
    
    # 清理构建目录
    print("1. 清理构建目录...")
    clean_build_dirs()
    
    # 创建spec文件
    print("2. 创建PyInstaller配置...")
    create_spec_file()
    
    # 构建可执行文件
    print("3. 构建可执行文件...")
    if not build_executable():
        return
    
    # 创建启动脚本
    print("4. 创建启动脚本...")
    create_launcher_script()
    
    # 创建使用说明
    print("5. 创建使用说明...")
    create_readme()
    
    print("\n" + "=" * 50)
    print("✅ 打包完成！")
    print("📁 可执行文件位置: dist/PDF智能分析助手.exe")
    print("�� 启动脚本位置: dist/启动PDF智能分析助手.bat")
    print("📖 使用说明位置: dist/使用说明.txt")
    print("\n�� 提示：将dist文件夹中的内容复制到目标机器即可使用")

if __name__ == "__main__":
    main()