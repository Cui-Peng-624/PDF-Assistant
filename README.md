# PDF 智能分析助手

一个基于 AI 的 PDF 文档智能分析工具，可以将 PDF 文件转换为图片，并使用大语言模型对每页内容进行详细分析。

## ✨ 主要功能

- **PDF 文件上传** - 支持拖拽上传，最大 50MB
- **智能分析** - 使用 AI 模型分析 PDF 每页内容
- **实时进度** - 显示处理进度，支持随时取消
- **文件管理** - 查看、下载、删除已处理的文件
- **结果导出** - 支持下载分析结果

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+ (可选，用于前端开发)

### 安装步骤

1. **克隆项目**

   ```bash
   git clone <repository-url>
   cd ReviewAssistant
   ```

2. **安装 Python 依赖**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### 启动方式

#### 方式一：一键启动（推荐）

```bash
# 同时启动前端和后端
python start_all.py
```

#### 方式二：分别启动

```bash
# 启动后端服务
python start_backend.py

# 启动前端服务（新终端窗口）
python start_frontend.py
```

#### 方式三：Windows 批处理文件

```bash
# 双击运行
start_all.bat        # 启动所有服务
start_backend.bat    # 仅启动后端
start_frontend.bat   # 仅启动前端
```

#### 方式四：手动启动

```bash
# 启动后端
cd backend
python run.py

# 启动前端（新终端）
cd frontend
python -m http.server 8080
```

### 访问应用

- **前端地址**: http://localhost:8080
- **后端 API**: http://localhost:5000
- 配置 API Key 和 API Base URL
- 开始使用

## 📁 项目结构

```
ReviewAssistant/
├── backend/                 # 后端API服务
│   ├── app.py              # Flask主应用
│   ├── run.py              # 后端启动脚本
│   ├── requirements.txt    # Python依赖
│   ├── core/               # 核心模块
│   │   ├── config_manager.py
│   │   ├── file_manager.py
│   │   └── pdf_processor.py
│   └── files/              # 文件存储
│       ├── uploads/        # 原始PDF文件
│       ├── images/         # 转换的图片
│       └── explanations/   # 分析结果
├── frontend/               # 前端界面
│   ├── index.html          # 主页面
│   └── js/
│       └── app.js          # 前端逻辑
└── README.md               # 项目说明
```

## 🔧 配置说明

### API 配置

在应用界面中配置以下参数：

- **API Key**: 您的 OpenAI API 密钥
- **API Base URL**: API 服务地址（默认：https://api.openai.com/v1）
- **模型名称**: 使用的模型（默认：gpt-4.1-2025-04-14）
- **系统提示词**: 自定义分析提示词

### 环境变量

也可以通过环境变量配置：

```bash
export ZETATECHS_API_KEY="your-api-key"
export ZETATECHS_API_BASE="https://api.openai.com/v1"
```

## 📖 使用指南

### 1. 上传 PDF 文件

- 拖拽 PDF 文件到上传区域
- 或点击选择文件按钮
- 支持最大 50MB 的 PDF 文件

### 2. 配置分析参数

- 填写 API 配置信息
- 自定义分析提示词
- 选择使用的 AI 模型

### 3. 开始分析

- 点击"上传并开始分析"按钮
- 系统会自动转换 PDF 为图片
- 使用 AI 模型分析每页内容

### 4. 查看结果

- 实时查看处理进度
- 可以随时取消处理
- 查看分析结果和预览

### 5. 文件管理

- 查看所有已处理的文件
- 下载分析结果
- 删除不需要的文件

## 🛠️ 技术栈

### 后端

- **Flask** - Web 框架
- **pdf2image** - PDF 转图片
- **OpenAI** - AI 模型接口
- **Werkzeug** - 文件上传处理

### 前端

- **HTML5** - 页面结构
- **Bootstrap 5** - UI 框架
- **JavaScript ES6** - 交互逻辑
- **Font Awesome** - 图标库

## 🔒 安全说明

- API 密钥仅存储在本地，不会上传到服务器
- 所有文件处理都在本地进行
- 支持删除功能，保护用户隐私

## 📝 更新日志

### v1.0.0

- ✅ 基础 PDF 分析功能
- ✅ 文件上传和管理
- ✅ 实时进度显示
- ✅ 取消处理功能
- ✅ 文件删除功能
- ✅ 结果导出功能

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目。

## 📄 许可证

本项目采用 MIT 许可证。

## 📞 支持

如有问题，请提交 Issue 或联系开发者。
