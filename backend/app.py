from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import json
import threading
import time
from werkzeug.utils import secure_filename
from datetime import datetime

# 导入核心处理模块
try:
    from core.pdf_processor import PDFProcessor
    from core.config_manager import ConfigManager
    from core.file_manager import FileManager
    CORE_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"警告: 核心模块导入失败: {e}")
    CORE_MODULES_AVAILABLE = False

app = Flask(__name__)
CORS(app)  # 启用CORS支持

# 配置
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'files/uploads'

# 确保目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 支持的文件类型
ALLOWED_EXTENSIONS = {'pdf'}

# 全局变量存储处理状态
processing_tasks = {}
cancelled_tasks = set()  # 存储被取消的任务ID

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/config', methods=['POST'])
def save_config():
    """保存用户配置"""
    try:
        config = request.json
        if CORE_MODULES_AVAILABLE:
            config_manager = ConfigManager()
            success = config_manager.save_config(config)
        else:
            # 简化版本：直接保存到文件
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            success = True
        
        if success:
            return jsonify({'success': True, 'message': '配置保存成功'})
        else:
            return jsonify({'success': False, 'message': '配置保存失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'配置保存失败: {str(e)}'})

@app.route('/api/config', methods=['GET'])
def get_config():
    """获取用户配置"""
    try:
        if CORE_MODULES_AVAILABLE:
            config_manager = ConfigManager()
            config = config_manager.get_config()
        else:
            # 简化版本：直接从文件读取
            try:
                with open('config.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except FileNotFoundError:
                config = {
                    'api_key': '',
                    'api_base': 'https://api.openai.com/v1',
                    'model': 'gpt-4.1-2025-04-14',
                    'system_prompt': '你是一个专业的图片内容分析助手。'
                }
        
        return jsonify({'success': True, 'config': config})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'})

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理PDF文件上传"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}_{filename}"
            
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            return jsonify({
                'success': True, 
                'message': '文件上传成功',
                'file_id': filename,
                'file_path': file_path
            })
        
        return jsonify({'success': False, 'message': '不支持的文件类型'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'文件上传失败: {str(e)}'})

@app.route('/api/process', methods=['POST'])
def process_pdf():
    """开始处理PDF文件"""
    try:
        if not CORE_MODULES_AVAILABLE:
            return jsonify({'success': False, 'message': '核心模块未加载，请检查依赖安装'})
        
        data = request.json
        file_id = data.get('file_id')
        prompt_text = data.get('prompt', '请根据图片内容，给出详细的解释。')
        config = data.get('config', {})
        
        if not file_id:
            return jsonify({'success': False, 'message': '缺少文件ID'})
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file_id)
        if not os.path.exists(file_path):
            return jsonify({'success': False, 'message': '文件不存在'})
        
        # 检查是否已有相同任务在处理
        if file_id in processing_tasks and processing_tasks[file_id]['is_processing']:
            return jsonify({'success': False, 'message': '该文件正在处理中，请稍候...'})
        
        # 创建任务ID
        task_id = f"{file_id}_{int(time.time())}"
        
        # 初始化任务状态
        processing_tasks[file_id] = {
            'task_id': task_id,
            'is_processing': True,
            'current_page': 0,
            'total_pages': 0,
            'progress': 0,
            'status_message': '准备开始处理...',
            'results': [],
            'error': None
        }
        
        # 启动异步处理
        thread = threading.Thread(
            target=process_pdf_async, 
            args=(file_id, file_path, prompt_text, config, task_id)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'message': '开始处理PDF文件',
            'task_id': task_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'开始处理失败: {str(e)}'})

def process_pdf_async(file_id, file_path, prompt_text, config, task_id):
    """异步处理PDF文件"""
    try:
        if not CORE_MODULES_AVAILABLE:
            processing_tasks[file_id]['is_processing'] = False
            processing_tasks[file_id]['status_message'] = '核心模块未加载，无法处理PDF'
            processing_tasks[file_id]['error'] = '核心模块未加载'
            return
        
        # 检查任务是否已被取消
        if file_id in cancelled_tasks:
            processing_tasks[file_id]['is_processing'] = False
            processing_tasks[file_id]['status_message'] = '任务已取消'
            processing_tasks[file_id]['error'] = '用户取消'
            return
        
        # 更新状态
        processing_tasks[file_id]['status_message'] = '开始处理PDF文件...'
        processing_tasks[file_id]['results'] = []
        
        # 创建文件管理器
        file_manager = FileManager()
        
        # 创建工作空间
        workspace = file_manager.create_pdf_workspace(file_id)
        
        # 创建PDF处理器
        processor = PDFProcessor()
        
        # 设置配置
        if config.get('api_key'):
            os.environ['ZETATECHS_API_KEY'] = config['api_key']
        if config.get('api_base'):
            os.environ['ZETATECHS_API_BASE'] = config['api_base']
        
        print(f"API配置: {config.get('api_key', 'None')[:10]}...{config.get('api_base', 'None')}")
        
        # 处理PDF
        results = processor.process_pdf(
            file_path=file_path,
            workspace=workspace,
            prompt=prompt_text,
            system_prompt=config.get('system_prompt', '你是一个专业的图片内容分析助手。'),
            api_key=config.get('api_key'),
            api_base=config.get('api_base'),
            model=config.get('model', 'gpt-4.1-2025-04-14'),
            progress_callback=lambda page, total, message: update_progress(file_id, page, total, message),
            cancel_check=lambda: file_id in cancelled_tasks
        )
        
        # 更新最终状态
        processing_tasks[file_id]['is_processing'] = False
        processing_tasks[file_id]['status_message'] = '处理完成！'
        processing_tasks[file_id]['results'] = results
        processing_tasks[file_id]['workspace'] = workspace
        
    except Exception as e:
        processing_tasks[file_id]['is_processing'] = False
        processing_tasks[file_id]['status_message'] = f'处理出错: {str(e)}'
        processing_tasks[file_id]['error'] = str(e)

def update_progress(file_id, current_page, total_pages, message):
    """更新处理进度"""
    if file_id in processing_tasks:
        # 检查任务是否已被取消
        if file_id in cancelled_tasks:
            processing_tasks[file_id]['is_processing'] = False
            processing_tasks[file_id]['status_message'] = '任务已取消'
            processing_tasks[file_id]['error'] = '用户取消'
            return
        
        processing_tasks[file_id]['current_page'] = current_page
        processing_tasks[file_id]['total_pages'] = total_pages
        processing_tasks[file_id]['progress'] = int((current_page / total_pages) * 100) if total_pages > 0 else 0
        processing_tasks[file_id]['status_message'] = message

@app.route('/api/status/<file_id>', methods=['GET'])
def get_status(file_id):
    """获取处理状态"""
    if file_id not in processing_tasks:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    return jsonify({
        'success': True,
        'status': processing_tasks[file_id]
    })

@app.route('/api/cancel/<file_id>', methods=['POST'])
def cancel_task(file_id):
    """取消正在处理的任务"""
    if file_id not in processing_tasks:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    task = processing_tasks[file_id]
    if not task['is_processing']:
        return jsonify({'success': False, 'message': '任务未在处理中'})
    
    # 标记任务为已取消
    cancelled_tasks.add(file_id)
    task['is_processing'] = False
    task['status_message'] = '任务已取消'
    task['error'] = '用户取消'
    
    return jsonify({
        'success': True,
        'message': '任务已取消'
    })

@app.route('/api/results/<file_id>', methods=['GET'])
def get_results(file_id):
    """获取处理结果"""
    if file_id not in processing_tasks:
        return jsonify({'success': False, 'message': '任务不存在'})
    
    task = processing_tasks[file_id]
    if task['is_processing']:
        return jsonify({'success': False, 'message': '任务仍在处理中'})
    
    return jsonify({
        'success': True,
        'results': task['results']
    })

@app.route('/api/download/<file_id>/<int:page>', methods=['GET'])
def download_explanation(file_id, page):
    """下载指定页面的解释文件"""
    try:
        if file_id not in processing_tasks:
            return jsonify({'success': False, 'message': '任务不存在'})
        
        task = processing_tasks[file_id]
        if page < 1 or page > len(task['results']):
            return jsonify({'success': False, 'message': '页面不存在'})
        
        result = task['results'][page - 1]
        explanation_path = result['explanation_path']
        
        if os.path.exists(explanation_path):
            return send_file(explanation_path, as_attachment=True)
        else:
            return jsonify({'success': False, 'message': '文件不存在'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'})

@app.route('/api/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    tasks = []
    for file_id, task in processing_tasks.items():
        tasks.append({
            'file_id': file_id,
            'task_id': task['task_id'],
            'is_processing': task['is_processing'],
            'progress': task['progress'],
            'status_message': task['status_message'],
            'total_pages': task['total_pages'],
            'current_page': task['current_page'],
            'workspace': task.get('workspace', {})
        })
    
    return jsonify({'success': True, 'tasks': tasks})

@app.route('/api/files', methods=['GET'])
def list_files():
    """列出所有已处理的PDF文件"""
    try:
        file_manager = FileManager() if CORE_MODULES_AVAILABLE else None
        files = []
        
        # 扫描images目录获取所有PDF文件
        images_dir = os.path.join('files', 'images')
        if os.path.exists(images_dir):
            for pdf_name in os.listdir(images_dir):
                pdf_dir = os.path.join(images_dir, pdf_name)
                if os.path.isdir(pdf_dir):
                    # 统计图片数量
                    image_count = len([f for f in os.listdir(pdf_dir) if f.endswith('.png')])
                    
                    # 检查是否有分析结果
                    explanations_dir = os.path.join('files', 'explanations', pdf_name)
                    explanation_count = 0
                    if os.path.exists(explanations_dir):
                        explanation_count = len([f for f in os.listdir(explanations_dir) if f.endswith('.md')])
                    
                    files.append({
                        'pdf_name': pdf_name,
                        'image_count': image_count,
                        'explanation_count': explanation_count,
                        'images_dir': pdf_dir,
                        'explanations_dir': explanations_dir if os.path.exists(explanations_dir) else None
                    })
        
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文件列表失败: {str(e)}'})

@app.route('/api/files/<pdf_name>', methods=['GET'])
def get_file_details(pdf_name):
    """获取特定PDF文件的详细信息"""
    try:
        images_dir = os.path.join('files', 'images', pdf_name)
        explanations_dir = os.path.join('files', 'explanations', pdf_name)
        
        if not os.path.exists(images_dir):
            return jsonify({'success': False, 'message': 'PDF文件不存在'})
        
        # 获取图片列表
        images = []
        if os.path.exists(images_dir):
            for img_file in sorted(os.listdir(images_dir)):
                if img_file.endswith('.png'):
                    images.append({
                        'filename': img_file,
                        'path': os.path.join(images_dir, img_file)
                    })
        
        # 获取分析结果列表
        explanations = []
        if os.path.exists(explanations_dir):
            for md_file in sorted(os.listdir(explanations_dir)):
                if md_file.endswith('.md'):
                    explanations.append({
                        'filename': md_file,
                        'path': os.path.join(explanations_dir, md_file)
                    })
        
        return jsonify({
            'success': True,
            'pdf_name': pdf_name,
            'images': images,
            'explanations': explanations,
            'images_dir': images_dir,
            'explanations_dir': explanations_dir
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取文件详情失败: {str(e)}'})

@app.route('/api/files/<pdf_name>', methods=['DELETE'])
def delete_file(pdf_name):
    """删除PDF文件及其所有相关文件"""
    try:
        import shutil
        
        # 检查文件是否存在
        images_dir = os.path.join('files', 'images', pdf_name)
        if not os.path.exists(images_dir):
            return jsonify({'success': False, 'message': 'PDF文件不存在'})
        
        # 检查是否有正在处理的任务
        if pdf_name in processing_tasks and processing_tasks[pdf_name]['is_processing']:
            return jsonify({'success': False, 'message': '文件正在处理中，无法删除'})
        
        # 删除相关目录和文件
        deleted_items = []
        
        # 删除图片目录
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            deleted_items.append(f'图片目录: {images_dir}')
        
        # 删除分析结果目录
        explanations_dir = os.path.join('files', 'explanations', pdf_name)
        if os.path.exists(explanations_dir):
            shutil.rmtree(explanations_dir)
            deleted_items.append(f'分析结果目录: {explanations_dir}')
        
        
        # 删除原始PDF文件
        pdf_file = os.path.join('files', 'uploads', f'{pdf_name}.pdf')
        if os.path.exists(pdf_file):
            os.remove(pdf_file)
            deleted_items.append(f'原始PDF文件: {pdf_file}')
        
        # 从处理任务中移除（如果存在）
        if pdf_name in processing_tasks:
            del processing_tasks[pdf_name]
        
        # 从取消任务列表中移除（如果存在）
        if pdf_name in cancelled_tasks:
            cancelled_tasks.discard(pdf_name)
        
        return jsonify({
            'success': True,
            'message': f'文件 {pdf_name} 及其所有相关文件已删除',
            'deleted_items': deleted_items
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除文件失败: {str(e)}'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
