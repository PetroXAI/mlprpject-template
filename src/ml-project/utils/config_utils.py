import os
import yaml
from pathlib import Path
import copy
from typing import Dict, Any, List, Optional, Union

# 配置文件默认根目录
DEFAULT_CONFIG_DIR = Path(__file__).parent.parent / "configs"

def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    加载单个YAML配置文件
    
    参数:
        file_path: YAML文件路径
        
    返回:
        配置字典
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        try:
            config = yaml.safe_load(f)
            return config or {}
        except yaml.YAMLError as e:
            raise ValueError(f"解析配置文件 {file_path} 出错: {e}")

def update_nested_dict(base: Dict[str, Any], update: Dict[str, Any]) -> Dict[str, Any]:
    """
    递归更新嵌套字典
    
    参数:
        base: 基础字典
        update: 要更新的内容
        
    返回:
        更新后的字典
    """
    result = copy.deepcopy(base)
    
    for k, v in update.items():
        if isinstance(v, dict) and k in result and isinstance(result[k], dict):
            result[k] = update_nested_dict(result[k], v)
        else:
            result[k] = v
            
    return result

def apply_overrides(config: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    """
    应用扁平化的配置覆盖
    
    参数:
        config: 原始配置字典
        overrides: 扁平化的覆盖字典 (如 {"model.params.hidden_dim": 256})
        
    返回:
        更新后的配置
    """
    result = copy.deepcopy(config)
    
    for key_path, value in overrides.items():
        keys = key_path.split('.')
        current = result
        
        # 遍历嵌套路径直到倒数第二级
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # 设置最后一级的值
        current[keys[-1]] = value
        
    return result

def load_config(
    config_file: str,
    config_dir: Optional[Union[str, Path]] = None,
    overrides: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    加载配置文件，处理导入和覆盖
    
    参数:
        config_file: 配置文件名或路径
        config_dir: 配置文件目录，默认为项目配置目录
        overrides: 要应用的配置覆盖
        
    返回:
        完整的配置字典
    """
    # 确定配置文件目录
    config_dir = Path(config_dir) if config_dir else DEFAULT_CONFIG_DIR
    
    # 解析配置文件路径
    if os.path.isabs(config_file):
        config_path = Path(config_file)
    else:
        config_path = config_dir / config_file
        
    # 加载主配置文件
    config = load_yaml(config_path)
    
    # 处理导入的配置文件
    if "imports" in config:
        imports = config.pop("imports")
        if not isinstance(imports, list):
            imports = [imports]
            
        # 加载并合并所有导入的配置
        base_config = {}
        for import_file in imports:
            import_config = load_config(import_file, config_dir)
            base_config = update_nested_dict(base_config, import_config)
            
        # 使用当前配置更新基础配置
        config = update_nested_dict(base_config, config)
    
    # 应用命令行覆盖
    if overrides:
        config = apply_overrides(config, overrides)

    return config 