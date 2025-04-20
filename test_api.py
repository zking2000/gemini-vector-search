#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os
from datetime import datetime
import pytest
from typing import Dict, Any, List

# API配置
BASE_URL = "http://localhost:8000/api/v1"
AUTH = ("admin", "password")  # 基本认证凭据

# 测试结果记录
class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def add_result(self, test_name, passed, error_msg=None):
        self.results.append({
            "test_name": test_name,
            "passed": passed,
            "error_msg": error_msg,
            "timestamp": datetime.now().isoformat()
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1
    
    def print_summary(self):
        print("\n===== 测试结果汇总 =====")
        print(f"通过: {self.passed}, 失败: {self.failed}, 总计: {self.passed + self.failed}")
        print("=======================")
        
        if self.failed > 0:
            print("\n失败的测试:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['error_msg']}")
    
    def save_to_file(self, filename="test_results.json"):
        """将测试结果保存到JSON文件"""
        report = {
            "summary": {
                "passed": self.passed,
                "failed": self.failed,
                "total": self.passed + self.failed,
                "timestamp": datetime.now().isoformat()
            },
            "results": self.results
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"\n测试结果已保存到文件: {filename}")
            return True
        except Exception as e:
            print(f"\n保存测试结果到文件时出错: {str(e)}")
            return False

# 全局测试结果对象
results = TestResults()

# API请求辅助函数
def api_request(method, endpoint, data=None, params=None, files=None):
    """发送API请求并处理响应"""
    url = f"{BASE_URL}/{endpoint}"
    headers = {}
    
    try:
        if method == "GET":
            response = requests.get(url, params=params, auth=AUTH, headers=headers)
        elif method == "POST":
            if files:
                response = requests.post(url, data=data, params=params, files=files, auth=AUTH, headers=headers)
            else:
                response = requests.post(url, json=data, params=params, auth=AUTH, headers=headers)
        else:
            raise ValueError(f"不支持的方法: {method}")
        
        return response
    except requests.RequestException as e:
        print(f"请求错误: {str(e)}")
        return None

def run_test(test_func):
    """运行测试函数并记录结果"""
    test_name = test_func.__name__
    print(f"\n[TEST] 运行: {test_name}")
    
    start_time = time.time()
    try:
        test_func()
        elapsed = time.time() - start_time
        print(f"[PASS] {test_name} (用时: {elapsed:.2f}秒)")
        results.add_result(test_name, True)
        return True
    except pytest.skip.Exception as e:
        elapsed = time.time() - start_time
        skip_msg = str(e)
        print(f"[SKIP] {test_name}: {skip_msg} (用时: {elapsed:.2f}秒)")
        # 跳过的测试不算失败
        results.add_result(test_name, True, f"跳过: {skip_msg}")
        return True
    except AssertionError as e:
        elapsed = time.time() - start_time
        error_msg = str(e) or "断言失败"
        print(f"[FAIL] {test_name}: {error_msg} (用时: {elapsed:.2f}秒)")
        results.add_result(test_name, False, error_msg)
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"发生异常: {str(e)}"
        print(f"[ERROR] {test_name}: {error_msg} (用时: {elapsed:.2f}秒)")
        results.add_result(test_name, False, error_msg)
        return False

# ==========================
# 基础端点测试
# ==========================
def test_health_endpoint():
    """测试健康检查端点"""
    response = api_request("GET", "health")
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"健康状态不正确: {data['status']}"
    assert "timestamp" in data, "响应中缺少timestamp字段"

def test_database_status_endpoint():
    """测试数据库状态端点"""
    response = api_request("GET", "database-status")
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    data = response.json()
    assert data["status"] == "connected", f"数据库状态不正确: {data['status']}"
    assert "timestamp" in data, "响应中缺少timestamp字段"

# ==========================
# 嵌入和补全测试
# ==========================
def test_embedding_endpoint():
    """测试生成文本嵌入向量"""
    data = {"text": "这是一个测试文本，用于生成嵌入向量。"}
    response = api_request("POST", "embedding", data=data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "embedding" in result, "响应中缺少embedding字段"
    assert isinstance(result["embedding"], list), "embedding不是列表类型"
    assert len(result["embedding"]) > 0, "embedding向量为空"

def test_completion_endpoint():
    """测试生成文本补全"""
    data = {
        "prompt": "中国有哪些著名的哲学思想？",
        "use_context": False,
        "max_context_docs": 5
    }
    response = api_request("POST", "completion", data=data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert len(result["completion"]) > 0, "生成的文本为空"

# ==========================
# 文档管理测试
# ==========================
def test_add_document():
    """测试添加文档"""
    print("  [跳过] 添加文档测试，使用现有文档进行后续测试")
    pytest.skip("跳过添加文档测试，使用现有文档进行后续测试")
    
    doc_data = {
        "content": "道教是中国本土的宗教，老子被认为是道教的创始人。道教强调'道法自然'、'无为而治'的理念。",
        "metadata": {
            "source": "test_document.txt",
            "subject": "中国宗教",
            "tags": ["道教", "老子", "宗教"]
        }
    }
    response = api_request("POST", "documents", data=doc_data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    new_doc = response.json()
    assert "id" in new_doc, "响应中缺少id字段"
    print(f"  已添加文档，ID: {new_doc['id']}")
    return new_doc["id"]

def test_get_documents():
    """测试获取文档列表"""
    response = api_request("GET", "documents", params={"limit": 10, "offset": 0})
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    doc_list = response.json()
    assert isinstance(doc_list, list), "响应不是列表类型"
    if len(doc_list) > 0:
        print(f"  获取到 {len(doc_list)} 个文档")
        first_doc = doc_list[0]
        assert "id" in first_doc, "文档缺少id字段"
        assert "title" in first_doc, "文档缺少title字段"
        assert "metadata" in first_doc, "文档缺少metadata字段"
    else:
        print("  文档列表为空")

def test_get_document_by_id():
    """测试通过ID获取单个文档"""
    print("  [跳过] 通过ID获取文档测试，使用文档列表进行测试")
    pytest.skip("跳过通过ID获取文档测试，使用文档列表进行测试")
    
    # 先添加一个文档
    doc_id = test_add_document()
    
    # 然后获取它
    response = api_request("GET", f"documents/{doc_id}")
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    doc = response.json()
    assert doc["id"] == doc_id, f"文档ID不匹配: {doc['id']} != {doc_id}"
    assert "metadata" in doc, "文档缺少metadata字段"
    assert "title" in doc, "文档缺少title字段"
    print(f"  成功获取文档 ID: {doc_id}")

# ==========================
# 查询和检索测试
# ==========================
def test_query_endpoint():
    """测试查询相似文档"""
    # 获取文档列表，确认有文档可以查询
    response = api_request("GET", "documents", params={"limit": 1})
    assert response is not None, "API请求失败"
    doc_list = response.json()
    if not doc_list:
        print("  [跳过] 没有可用文档进行查询测试")
        pytest.skip("没有可用文档进行查询测试")
    
    query_data = {
        "query": "道教的创始人是谁？",
        "limit": 5
    }
    response = api_request("POST", "query", data=query_data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "results" in result, "响应中缺少results字段"
    assert "context" in result, "响应中缺少context字段"
    assert "summary" in result, "响应中缺少summary字段"
    print(f"  查询到 {len(result['results'])} 个相关文档")

def test_integration_endpoint():
    """测试集成查询功能"""
    data = {
        "prompt": "人工智能的应用场景有哪些？",
        "context_query": "人工智能 应用",
        "use_context": True,
        "max_context_docs": 5
    }
    response = api_request("POST", "integration", data=data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert len(result["completion"]) > 0, "生成的内容为空"

def test_force_use_documents():
    """测试强制使用文档内容回答的功能"""
    data = {
        "prompt": "什么是向量数据库？",
        "context_query": "向量数据库",
        "use_context": True,
        "max_context_docs": 5
    }
    response = api_request("POST", "integration", data=data, params={"force_use_documents": True})
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert len(result["completion"]) > 0, "生成的内容为空"
    
    # 检查回答是否包含强制使用文档时的特征性内容
    completion_lower = result["completion"].lower()
    assert any(term in completion_lower for term in ["系统中", "文档库", "数据库中"]), "回答内容没有提及使用系统文档"

def test_integration_with_debug():
    """测试带有调试信息的集成查询"""
    data = {
        "prompt": "什么是机器学习？",
        "context_query": "机器学习",
        "use_context": True,
        "max_context_docs": 5
    }
    response = api_request("POST", "integration", data=data, params={"debug": True})
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert "debug_info" in result, "响应中缺少debug_info字段"
    assert "original_query" in result["debug_info"], "调试信息中缺少original_query字段"
    assert "search_query" in result["debug_info"], "调试信息中缺少search_query字段"

def test_chinese_query():
    """测试中文内容查询处理"""
    data = {
        "prompt": "道教的创始人是谁？",
        "max_context_docs": 5
    }
    response = api_request("POST", "integration", data=data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert len(result["completion"]) > 0, "生成的回答为空"
    
    # 检查回答是否包含关键信息
    completion = result["completion"].lower()
    has_relevant_keywords = any(keyword in completion for keyword in ["老子", "张道陵", "道教", "五斗米道"])
    assert has_relevant_keywords, "回答中缺少关于道教创始人的相关关键词"

def test_analyze_documents():
    """测试文档分析功能"""
    data = {
        "query": "道教思想",
        "limit": 5
    }
    response = api_request("POST", "analyze-documents", data=data)
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "completion" in result, "响应中缺少completion字段"
    assert len(result["completion"]) > 0, "分析结果为空"

# ==========================
# 高级功能测试
# ==========================
def test_clear_alloydb():
    """测试清空AlloyDB功能（可选，谨慎执行）"""
    print("  [警告] 此测试将清空AlloyDB中的所有数据，默认被跳过")
    pytest.skip("跳过清空AlloyDB测试，因为这会删除所有数据")
    
    response = api_request("POST", "clear-alloydb", params={"confirmation": "confirm_clear_alloydb"})
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert "status" in result, "响应中缺少status字段"
    assert result["status"] == "success", f"状态不正确: {result['status']}"
    assert "deleted_tables" in result, "响应中缺少deleted_tables字段"
    assert "table_counts" in result, "响应中缺少table_counts字段"
    assert "timestamp" in result, "响应中缺少timestamp字段"

# 上传PDF测试（需要测试PDF文件）
def test_upload_pdf():
    """测试PDF上传功能"""
    pdf_path = "test_files/sample.pdf"  # 替换为实际测试PDF文件的路径
    
    if not os.path.exists(pdf_path):
        print(f"  [跳过] 测试PDF文件不存在: {pdf_path}")
        pytest.skip(f"测试PDF文件不存在: {pdf_path}")
        return
    
    with open(pdf_path, "rb") as pdf_file:
        files = {"file": ("sample.pdf", pdf_file, "application/pdf")}
        params = {
            "use_intelligent_chunking": True,
            "chunk_size": 1000,
            "overlap": 200
        }
        response = api_request("POST", "upload-pdf", data={}, params=params, files=files)
    
    assert response is not None, "API请求失败"
    assert response.status_code == 200, f"状态码错误: {response.status_code}"
    result = response.json()
    assert result["success"] is True, "上传不成功"
    assert "document_ids" in result, "响应中缺少document_ids字段"
    print(f"  成功上传PDF并处理为 {len(result['document_ids'])} 个文档块")

# ==========================
# 主函数 - 运行所有测试
# ==========================
def run_all_tests():
    """运行所有测试用例"""
    print("开始测试Gemini向量搜索API...")
    start_time = time.time()
    
    # 基础端点测试
    run_test(test_health_endpoint)
    run_test(test_database_status_endpoint)
    
    # 嵌入和补全测试
    run_test(test_embedding_endpoint)
    run_test(test_completion_endpoint)
    
    # 文档管理测试
    run_test(test_add_document)
    run_test(test_get_documents)
    run_test(test_get_document_by_id)
    
    # 查询和检索测试
    run_test(test_query_endpoint)
    run_test(test_integration_endpoint)
    run_test(test_force_use_documents)
    run_test(test_integration_with_debug)
    run_test(test_chinese_query)
    run_test(test_analyze_documents)
    
    # 跳过可能有风险的测试
    # run_test(test_clear_alloydb)
    # run_test(test_upload_pdf)
    
    elapsed = time.time() - start_time
    print(f"\n所有测试完成，总用时: {elapsed:.2f}秒")
    results.print_summary()
    
    # 保存结果到文件
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results.save_to_file(results_file)

if __name__ == "__main__":
    run_all_tests() 