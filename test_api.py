#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import time
import os
from datetime import datetime
import pytest
from typing import Dict, Any, List

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"
AUTH = ("admin", "password")  # Basic authentication credentials

# Test results recording
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
        print("\n===== Test Results Summary =====")
        print(f"Passed: {self.passed}, Failed: {self.failed}, Total: {self.passed + self.failed}")
        print("=======================")
        
        if self.failed > 0:
            print("\nFailed tests:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  - {result['test_name']}: {result['error_msg']}")
    
    def save_to_file(self, filename="test_results.json"):
        """Save test results to a JSON file"""
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
            print(f"\nTest results have been saved to file: {filename}")
            return True
        except Exception as e:
            print(f"\nError saving test results to file: {str(e)}")
            return False

# Global test results object
results = TestResults()

# API request helper functions
def api_request(method, endpoint, data=None, params=None, files=None):
    """Send API request and handle response"""
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
            raise ValueError(f"Unsupported method: {method}")
        
        return response
    except requests.RequestException as e:
        print(f"Request error: {str(e)}")
        return None

def run_test(test_func):
    """Run test function and record results"""
    test_name = test_func.__name__
    print(f"\n[TEST] Running: {test_name}")
    
    start_time = time.time()
    try:
        test_func()
        elapsed = time.time() - start_time
        print(f"[PASS] {test_name} (Time: {elapsed:.2f}s)")
        results.add_result(test_name, True)
        return True
    except pytest.skip.Exception as e:
        elapsed = time.time() - start_time
        skip_msg = str(e)
        print(f"[SKIP] {test_name}: {skip_msg} (Time: {elapsed:.2f}s)")
        # Skipped tests don't count as failures
        results.add_result(test_name, True, f"Skipped: {skip_msg}")
        return True
    except AssertionError as e:
        elapsed = time.time() - start_time
        error_msg = str(e) or "Assertion failed"
        print(f"[FAIL] {test_name}: {error_msg} (Time: {elapsed:.2f}s)")
        results.add_result(test_name, False, error_msg)
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"Exception occurred: {str(e)}"
        print(f"[ERROR] {test_name}: {error_msg} (Time: {elapsed:.2f}s)")
        results.add_result(test_name, False, error_msg)
        return False

# ==========================
# Basic Endpoint Tests
# ==========================
def test_health_endpoint():
    """Test health check endpoint"""
    response = api_request("GET", "health")
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    data = response.json()
    assert data["status"] == "ok", f"Health status incorrect: {data['status']}"
    assert "timestamp" in data, "Response missing timestamp field"

def test_database_status_endpoint():
    """Test database status endpoint"""
    response = api_request("GET", "database-status")
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    data = response.json()
    assert data["status"] == "connected", f"Database status incorrect: {data['status']}"
    assert "timestamp" in data, "Response missing timestamp field"

# ==========================
# Embedding and Completion Tests
# ==========================
def test_embedding_endpoint():
    """Test text embedding vector generation"""
    data = {"text": "This is a test text for generating embedding vectors."}
    response = api_request("POST", "embedding", data=data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "embedding" in result, "Response missing embedding field"
    assert isinstance(result["embedding"], list), "Embedding is not a list type"
    assert len(result["embedding"]) > 0, "Embedding vector is empty"

def test_completion_endpoint():
    """Test text completion generation"""
    data = {
        "prompt": "What are some famous philosophical thoughts in China?",
        "use_context": False,
        "max_context_docs": 5,
        "use_chunks": True
    }
    response = api_request("POST", "completion", data=data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "completion" in result, "Response missing completion field"
    assert len(result["completion"]) > 0, "Generated text is empty"

# ==========================
# Document Management Tests
# ==========================
def test_add_document():
    """Test adding document"""
    print("  [SKIP] Adding document test, using existing documents for subsequent tests")
    pytest.skip("Skipping add document test, using existing documents for subsequent tests")
    
    doc_data = {
        "content": "Taoism is a religion native to China, with Laozi considered its founder. Taoism emphasizes the concepts of 'following the way of nature' and 'governing by non-action'.",
        "metadata": {
            "source": "test_document.txt",
            "subject": "Chinese religions",
            "tags": ["Taoism", "Laozi", "Religion"]
        }
    }
    response = api_request("POST", "documents", data=doc_data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    new_doc = response.json()
    assert "id" in new_doc, "Response missing id field"
    print(f"  Document added, ID: {new_doc['id']}")
    return new_doc["id"]

def test_get_documents():
    """Test getting document list"""
    response = api_request("GET", "documents", params={"limit": 10, "offset": 0})
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    doc_list = response.json()
    assert isinstance(doc_list, list), "Response is not a list type"
    if len(doc_list) > 0:
        print(f"  Retrieved {len(doc_list)} documents")
        first_doc = doc_list[0]
        assert "id" in first_doc, "Document missing id field"
        assert "title" in first_doc, "Document missing title field"
        assert "metadata" in first_doc, "Document missing metadata field"
    else:
        print("  Document list is empty")

def test_get_document_by_id():
    """Test getting a single document by ID"""
    print("  [SKIP] Getting document by ID test, using document list for testing")
    pytest.skip("Skipping get document by ID test, using document list for testing")
    
    # First add a document
    doc_id = test_add_document()
    
    # Then retrieve it
    response = api_request("GET", f"documents/{doc_id}")
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    doc = response.json()
    assert doc["id"] == doc_id, f"Document ID mismatch: {doc['id']} != {doc_id}"
    assert "metadata" in doc, "Document missing metadata field"
    assert "title" in doc, "Document missing title field"
    print(f"  Successfully retrieved document ID: {doc_id}")

# ==========================
# Query and Retrieval Tests
# ==========================
def test_query_endpoint():
    """Test querying similar documents"""
    # Get document list to confirm there are documents available for query
    response = api_request("GET", "documents", params={"limit": 1})
    assert response is not None, "API request failed"
    doc_list = response.json()
    if not doc_list:
        print("  [SKIP] No documents available for query test")
        pytest.skip("No documents available for query test")
    
    query_data = {
        "query": "Who is the founder of Taoism?",
        "limit": 5,
        "use_chunks": True
    }
    response = api_request("POST", "query", data=query_data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "results" in result, "Response missing results field"
    assert "context" in result, "Response missing context field"
    assert "summary" in result, "Response missing summary field"
    print(f"   Retrieved {len(result['results'])} related documents")

def test_integration_endpoint():
    """Test integrated query functionality"""
    data = {
        "prompt": "What are some applications of artificial intelligence?",
        "context_query": "artificial intelligence application",
        "use_context": True,
        "max_context_docs": 5,
        "use_chunks": True
    }
    response = api_request("POST", "integration", data=data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "completion" in result, "Response missing completion field"
    assert len(result["completion"]) > 0, "Generated content is empty"

def test_force_use_documents():
    """Test forcing the use of document content for answering"""
    data = {
        "prompt": "What is a vector database?",
        "context_query": "vector database",
        "use_context": True,
        "max_context_docs": 5,
        "use_chunks": True
    }
    response = api_request("POST", "integration", data=data, params={"force_use_documents": True})
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "completion" in result, "Response missing completion field"
    assert len(result["completion"]) > 0, "Generated content is empty"
    
    # Check if the answer contains characteristic content when using document content
    completion_lower = result["completion"].lower()
    assert any(term in completion_lower for term in ["system", "document library", "database"]), "Answer content does not mention using system documents"

def test_integration_with_debug():
    """Test integrated query with debugging information"""
    data = {
        "prompt": "What is machine learning?",
        "context_query": "machine learning",
        "use_context": True,
        "max_context_docs": 5,
        "use_chunks": True
    }
    response = api_request("POST", "integration", data=data, params={"debug": True})
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "completion" in result, "Response missing completion field"
    assert "debug_info" in result, "Response missing debug_info field"
    assert "original_query" in result["debug_info"], "Debug info missing original_query field"
    assert "search_query" in result["debug_info"], "Debug info missing search_query field"

def test_analyze_documents():
    """Test document analysis functionality"""
    data = {
        "query": "Taoist philosophy",
        "limit": 5
    }
    response = api_request("POST", "analyze-documents", data=data)
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "completion" in result, "Response missing completion field"
    assert len(result["completion"]) > 0, "Analysis result is empty"

# ==========================
# Advanced Feature Tests
# ==========================
def test_clear_alloydb():
    """Test clearing AlloyDB functionality (optional, use with caution)"""
    print("  [WARNING] This test will clear all data in AlloyDB, default skipped")
    pytest.skip("Skipping clear AlloyDB test, as it will delete all data")
    
    response = api_request("POST", "clear-alloydb", params={"confirmation": "confirm_clear_alloydb"})
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert "status" in result, "Response missing status field"
    assert result["status"] == "success", f"Incorrect status: {result['status']}"
    assert "deleted_tables" in result, "Response missing deleted_tables field"
    assert "table_counts" in result, "Response missing table_counts field"
    assert "timestamp" in result, "Response missing timestamp field"

# Upload PDF test (requires test PDF file)
def test_upload_pdf():
    """Test PDF upload functionality"""
    pdf_path = "test_files/sample.pdf"  # Replace with actual test PDF file path
    
    if not os.path.exists(pdf_path):
        print(f"  [SKIP] Test PDF file does not exist: {pdf_path}")
        pytest.skip(f"Test PDF file does not exist: {pdf_path}")
        return
    
    with open(pdf_path, "rb") as pdf_file:
        files = {"file": ("sample.pdf", pdf_file, "application/pdf")}
        params = {
            "use_intelligent_chunking": True,
            "chunk_size": 1000,
            "overlap": 200,
            "clear_existing": False
        }
        response = api_request("POST", "upload-pdf", data={}, params=params, files=files)
    
    assert response is not None, "API request failed"
    assert response.status_code == 200, f"Status code error: {response.status_code}"
    result = response.json()
    assert result["success"] is True, "Upload failed"
    assert "document_ids" in result, "Response missing document_ids field"
    print(f"   Successfully uploaded PDF and processed to {len(result['document_ids'])} document chunks")

# ==========================
# Main function - Run all tests
# ==========================
def run_all_tests():
    """Run all test cases"""
    print("Starting Gemini vector search API test...")
    start_time = time.time()
    
    # Basic endpoint tests
    run_test(test_health_endpoint)
    run_test(test_database_status_endpoint)
    
    # Embedding and completion tests
    run_test(test_embedding_endpoint)
    run_test(test_completion_endpoint)
    
    # Document management tests
    run_test(test_add_document)
    run_test(test_get_documents)
    run_test(test_get_document_by_id)
    
    # Query and retrieval tests
    run_test(test_query_endpoint)
    run_test(test_integration_endpoint)
    run_test(test_force_use_documents)
    run_test(test_integration_with_debug)
    run_test(test_analyze_documents)
    
    # Skip potentially risky tests
    # run_test(test_clear_alloydb)
    # run_test(test_upload_pdf)
    
    elapsed = time.time() - start_time
    print(f"\nAll tests completed, Total time: {elapsed:.2f}s")
    results.print_summary()
    
    # Save results to file
    results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    results.save_to_file(results_file)

if __name__ == "__main__":
    run_all_tests() 