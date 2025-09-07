import json
import os
from typing import Dict, Any

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file='config.json'):
        self.config_file = config_file
        self.default_config = {
            'api_key': '',
            'api_base': 'https://api.openai.com/v1',
            'model': 'gpt-4.1-2025-04-14',
            'system_prompt': '你是一个专业的图片内容分析助手。'
        }
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            # 合并默认配置和用户配置
            merged_config = {**self.default_config, **config}
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(merged_config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """从文件读取配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 确保所有必要的键都存在
                    return {**self.default_config, **config}
            else:
                return self.default_config.copy()
        except Exception as e:
            print(f"读取配置失败: {e}")
            return self.default_config.copy()
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, str]:
        """验证配置的有效性"""
        if not config.get('api_key'):
            return False, 'API Key不能为空'
        
        if not config.get('api_base'):
            return False, 'API Base URL不能为空'
        
        # 验证URL格式
        api_base = config.get('api_base', '')
        if not (api_base.startswith('http://') or api_base.startswith('https://')):
            return False, 'API Base URL格式不正确'
        
        return True, '配置有效'
