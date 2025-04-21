#!/usr/bin/env python3
"""
检查Gemini API配额的剩余量
此脚本用于检查当前Google AI Gemini API的配额使用情况
"""

import os
import sys
import time
import json
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv
import requests

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 加载环境变量
load_dotenv()

# 获取API密钥
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    print("错误: 未找到GOOGLE_API_KEY环境变量")
    sys.exit(1)

# 设置API密钥
genai.configure(api_key=API_KEY)

def get_quota_info():
    """获取Gemini API配额信息"""
    try:
        # 尝试获取模型列表以验证API密钥是否有效
        models = genai.list_models()
        model_names = [model.name for model in models if "gemini" in model.name.lower()]
        
        # 初始化要返回的信息
        quota_info = {
            "status": "正常",
            "models": model_names,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_valid": True,
            "error": None
        }
        
        # 尝试通过一个简单请求来检查API配额
        # 不同的模型有不同的配额，这里选择最常用的gemini-1.5-pro模型进行测试
        try:
            model = genai.GenerativeModel("gemini-1.5-pro")
            response = model.generate_content("Hello")
            quota_info["test_request_success"] = True
        except Exception as e:
            error_message = str(e)
            quota_info["test_request_success"] = False
            quota_info["error"] = error_message
            
            # 检查是否是配额相关的错误
            if "429" in error_message or "quota" in error_message.lower() or "resource exhausted" in error_message.lower():
                quota_info["status"] = "配额已用尽"
        
        # 尝试获取更多配额信息 - 注意：Google AI API目前没有直接提供配额查询的接口
        # 这里我们可以使用请求头中的信息或根据错误消息来推断
        
        return quota_info
    
    except Exception as e:
        return {
            "status": "错误",
            "error": str(e),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_key_valid": False
        }

def get_model_info(model_name):
    """获取特定模型的信息"""
    try:
        # 这里可以添加获取特定模型信息的代码
        # 目前Google AI API没有直接提供模型配额信息的接口
        model = None
        models = genai.list_models()
        for m in models:
            if m.name == model_name:
                model = m
                break
        
        if model:
            return {
                "name": model.name,
                "display_name": getattr(model, "display_name", model.name),
                "description": getattr(model, "description", "无描述"),
                "input_token_limit": getattr(model, "input_token_limit", "未知"),
                "output_token_limit": getattr(model, "output_token_limit", "未知"),
                "supported_generation_methods": getattr(model, "supported_generation_methods", [])
            }
        else:
            return {"error": f"未找到模型: {model_name}"}
    
    except Exception as e:
        return {"error": str(e)}

def print_quota_info(quota_info):
    """打印配额信息"""
    print("\n===== Gemini API 配额信息 =====")
    print(f"检查时间: {quota_info['timestamp']}")
    print(f"API密钥状态: {'有效' if quota_info.get('api_key_valid', False) else '无效'}")
    print(f"配额状态: {quota_info['status']}")
    
    if quota_info.get('test_request_success', False):
        print("测试请求: 成功")
    else:
        print("测试请求: 失败")
        if quota_info.get('error'):
            print(f"错误信息: {quota_info['error']}")
    
    if quota_info.get('models'):
        print("\n可用的Gemini模型:")
        for model in quota_info['models']:
            print(f"  - {model}")
    
    print("\n注意: Google AI API目前没有直接提供查询配额剩余量的接口。")
    print("      如果您遇到429错误，这表示您已达到API调用限制。")
    print("      大多数Gemini模型的默认限制是每分钟60次请求。")
    print("===============================\n")

if __name__ == "__main__":
    quota_info = get_quota_info()
    print_quota_info(quota_info)
    
    # 如果有命令行参数，并且是模型名称，则显示该模型的详细信息
    if len(sys.argv) > 1:
        model_name = sys.argv[1]
        model_info = get_model_info(model_name)
        print(f"\n===== 模型详细信息: {model_name} =====")
        for key, value in model_info.items():
            print(f"{key}: {value}")
        print("===============================\n") 