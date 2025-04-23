#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import requests
import json
import time
from datetime import datetime
import os
from jinja2 import Template
import asyncio
import aiohttp
from tqdm import tqdm
import sys
import shutil
import urllib.request
import http.server
import socketserver
import webbrowser
import threading

# 预设的测试问题集
DEFAULT_QUESTIONS = [
    "What was the percentage allocation across asset classes in 2023?",
    "Which companies contributed most to the fund’s return in 2023?",
    "What was the difference between the fund’s return and the benchmark index?",
    "How did unlisted real estate perform and why?",
    "What strategic shifts were made in response to geopolitical tensions?",
    "Which companies were excluded based on responsible investment criteria?",
    "What insights came out of the stress test scenarios in the report?",
    "How did the fund’s renewable energy investments evolve?",
    "What long-term investment trends were highlighted?",
    "How did fixed-income instruments contribute to the fund’s return?"
]

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>向量搜索基准测试报告</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f8fa;
        }
        h1, h2, h3 {
            color: #0366d6;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        .query-card {
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            margin-bottom: 20px;
            overflow: hidden;
            transition: transform 0.2s;
            position: relative;
        }
        .query-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .query-header {
            padding: 15px 20px;
            background-color: #f1f8ff;
            border-bottom: 1px solid #e1e4e8;
            position: relative;
        }
        .query-title {
            font-weight: 600;
            margin: 0;
            color: #24292e;
        }
        .query-body {
            padding: 20px;
        }
        .result-card {
            border: 1px solid #e1e4e8;
            border-radius: 6px;
            margin-bottom: 15px;
            padding: 15px;
            background-color: #f6f8fa;
        }
        .result-card.fixed {
            border-left: 4px solid #0366d6;
        }
        .result-card.intelligent {
            border-left: 4px solid #28a745;
        }
        .result-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-weight: 600;
        }
        .result-meta {
            font-size: 0.85em;
            color: #586069;
            margin-bottom: 10px;
        }
        .result-content {
            background-color: #fff;
            border: 1px solid #e1e4e8;
            border-radius: 4px;
            padding: 10px;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 0.9em;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
        }
        .highlights {
            background-color: #fffbdd;
            padding: 2px;
            border-radius: 2px;
        }
        .summary {
            margin-top: 30px;
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
            padding: 20px;
        }
        .summary-header {
            border-bottom: 1px solid #e1e4e8;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .summary-stats {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background-color: #f6f8fa;
            border-radius: 6px;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .stat-value {
            font-size: 1.8em;
            font-weight: 600;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 0.9em;
            color: #586069;
            text-align: center;
        }
        .better {
            color: #28a745;
        }
        .worse {
            color: #d73a49;
        }
        .badge {
            display: inline-block;
            padding: 3px 8px;
            font-size: 0.75em;
            font-weight: 600;
            border-radius: 2em;
            margin-left: 8px;
        }
        .badge.fixed {
            background-color: #0366d680;
            color: white;
        }
        .badge.intelligent {
            background-color: #28a74580;
            color: white;
        }
        .winner-label {
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: #ffdf1e;
            color: #24292e;
            padding: 3px 8px;
            font-size: 0.7em;
            border-radius: 2em;
            font-weight: 600;
        }
        .comparison-chart {
            margin-top: 20px;
            height: 300px;
        }
        .chart-container {
            margin-top: 20px;
            height: 350px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding: 20px;
            color: #586069;
            font-size: 0.9em;
        }
        pre {
            overflow-x: auto;
            background-color: #f6f8fa;
            border-radius: 4px;
            padding: 15px;
            margin: 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #e1e4e8;
            padding: 8px 12px;
            text-align: left;
        }
        th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        tr:nth-child(even) {
            background-color: #f6f8fa;
        }
        .page-navigation {
            display: flex;
            justify-content: space-between;
            margin: 20px 0;
        }
        .page-nav-button {
            background-color: #0366d6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 500;
        }
        .page-nav-button:disabled {
            background-color: #c0c0c0;
            cursor: not-allowed;
        }
        .chart-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            margin-top: 20px;
        }
        @media (max-width: 768px) {
            .summary-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
    <script src="chart.min.js" onerror="document.getElementById('chart-error').style.display='block';"></script>
</head>
<body>
    <div id="chart-error" style="display:none; text-align:center; margin:20px; padding:15px; background-color:#f8d7da; color:#721c24; border-radius:5px;">
        <p><strong>错误</strong>: 无法加载Chart.js库，图表将不可用。</p>
        <p>可能的原因: 文件不存在、网络连接问题或脚本被阻止。</p>
    </div>
    
    <div class="header">
        <h1>向量搜索分块策略基准测试报告</h1>
        <p>生成时间: {{ timestamp }}</p>
        <p>测试查询数量: {{ total_queries }}</p>
    </div>

    <div class="summary">
        <div class="summary-header">
            <h2>执行结果摘要</h2>
        </div>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-label">总查询数</div>
                <div class="stat-value">{{ total_queries }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">固定分块策略胜出</div>
                <div class="stat-value">{{ fixed_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能分块策略胜出</div>
                <div class="stat-value">{{ intelligent_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">固定分块平均相似度</div>
                <div class="stat-value">{{ fixed_avg_similarity|round(4) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能分块平均相似度</div>
                <div class="stat-value">{{ intelligent_avg_similarity|round(4) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">固定分块平均处理时间</div>
                <div class="stat-value">{{ fixed_avg_time|round(2) }}ms</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能分块平均处理时间</div>
                <div class="stat-value">{{ intelligent_avg_time|round(2) }}ms</div>
            </div>
        </div>

        <div class="chart-wrapper">
            <h3>分块策略胜出比例</h3>
            <div class="chart-container" style="width:50%; height:300px;">
                <canvas id="winsChart" width="400" height="300"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <h3>查询相似度比较</h3>
            <div class="chart-container">
                <canvas id="similarityChart" width="800" height="350"></canvas>
            </div>
        </div>

        <div class="chart-wrapper">
            <h3>查询处理时间比较</h3>
            <div class="chart-container">
                <canvas id="timeChart" width="800" height="350"></canvas>
            </div>
        </div>
    </div>

    <h2>查询详细结果</h2>
    {% for query in queries %}
    <div class="query-card">
        <div class="query-header">
            <h3 class="query-title">{{ query.query }}</h3>
            {% if query.best_strategy == "fixed_size" %}
            <span class="winner-label">固定分块策略获胜</span>
            {% else %}
            <span class="winner-label">智能分块策略获胜</span>
            {% endif %}
        </div>
        <div class="query-body">
            <div class="result-meta">
                <strong>评估结果:</strong> {{ query.evaluation.reason }}
            </div>
            
            <div class="result-card fixed">
                <div class="result-header">
                    <span>固定分块策略结果<span class="badge fixed">{{ query.strategies.fixed_size.count }} 文档</span></span>
                    <span>相似度: {{ query.strategies.fixed_size.avg_similarity|round(4) }} | 处理时间: {{ query.strategies.fixed_size.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>前5条结果:</strong>
                </div>
                
                {% for doc in query.strategies.fixed_size.documents[:5] %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>文档ID: {{ doc.id }} | 相似度: {{ doc.score|round(4) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
            </div>
            
            <div class="result-card intelligent">
                <div class="result-header">
                    <span>智能分块策略结果<span class="badge intelligent">{{ query.strategies.intelligent.count }} 文档</span></span>
                    <span>相似度: {{ query.strategies.intelligent.avg_similarity|round(4) }} | 处理时间: {{ query.strategies.intelligent.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>前5条结果:</strong>
                </div>
                
                {% for doc in query.strategies.intelligent.documents[:5] %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>文档ID: {{ doc.id }} | 相似度: {{ doc.score|round(4) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
            </div>
            
            <div class="result-meta">
                <strong>相似度和处理时间对比</strong>
            </div>
            
            <div class="comparison-chart">
                <canvas id="comparisonChart-{{ loop.index }}" width="800" height="300"></canvas>
            </div>
        </div>
    </div>
    {% endfor %}

    <div class="footer">
        <p>© {{ current_year }} 向量搜索基准测试报告 | 生成于 {{ timestamp }}</p>
    </div>

    {% if chart_js_missing %}
    <div style="text-align:center; margin:20px; padding:15px; background-color:#fff3cd; color:#856404; border-radius:5px;">
        <p><strong>注意</strong>: Chart.js库无法加载，图表功能不可用。请确保report目录下有chart.min.js文件或网络连接正常。</p>
        <p>您仍然可以查看数据和比较结果。</p>
    </div>
    {% endif %}

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            try {
                // 胜出比例饼图
                const winsCtx = document.getElementById('winsChart').getContext('2d');
                new Chart(winsCtx, {
                    type: 'pie',
                    data: {
                        labels: ['固定分块策略', '智能分块策略'],
                        datasets: [{
                            data: [{{ fixed_wins }}, {{ intelligent_wins }}],
                            backgroundColor: ['rgba(3, 102, 214, 0.8)', 'rgba(40, 167, 69, 0.8)'],
                            borderColor: ['rgba(3, 102, 214, 1)', 'rgba(40, 167, 69, 1)'],
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    font: {
                                        size: 14
                                    }
                                }
                            },
                            tooltip: {
                                bodyFont: {
                                    size: 14
                                },
                                callbacks: {
                                    label: function(context) {
                                        return context.label + ': ' + context.raw + ' 次';
                                    }
                                }
                            }
                        },
                        animation: {
                            duration: 0 // 禁用动画，确保立即渲染
                        }
                    }
                });

                // 相似度比较图
                const similarityCtx = document.getElementById('similarityChart').getContext('2d');
                new Chart(similarityCtx, {
                    type: 'bar',
                    data: {
                        labels: [{% for query in queries %}'Q{{ loop.index }}'{% if not loop.last %}, {% endif %}{% endfor %}],
                        datasets: [{
                            label: '固定分块相似度',
                            data: [{% for query in queries %}{{ query.strategies.fixed_size.avg_similarity }}{% if not loop.last %}, {% endif %}{% endfor %}],
                            backgroundColor: 'rgba(3, 102, 214, 0.6)',
                            borderColor: 'rgba(3, 102, 214, 1)',
                            borderWidth: 1
                        }, {
                            label: '智能分块相似度',
                            data: [{% for query in queries %}{{ query.strategies.intelligent.avg_similarity }}{% if not loop.last %}, {% endif %}{% endfor %}],
                            backgroundColor: 'rgba(40, 167, 69, 0.6)',
                            borderColor: 'rgba(40, 167, 69, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top'
                            },
                            tooltip: {
                                callbacks: {
                                    title: function(context) {
                                        const index = context[0].dataIndex;
                                        return "{{ queries }}".split(",")[index].query;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                min: 0.7,
                                max: 1
                            }
                        },
                        animation: {
                            duration: 0 // 禁用动画，确保立即渲染
                        }
                    }
                });

                // 处理时间比较图
                const timeCtx = document.getElementById('timeChart').getContext('2d');
                new Chart(timeCtx, {
                    type: 'bar',
                    data: {
                        labels: [{% for query in queries %}'Q{{ loop.index }}'{% if not loop.last %}, {% endif %}{% endfor %}],
                        datasets: [{
                            label: '固定分块处理时间 (ms)',
                            data: [{% for query in queries %}{{ query.strategies.fixed_size.time_ms }}{% if not loop.last %}, {% endif %}{% endfor %}],
                            backgroundColor: 'rgba(3, 102, 214, 0.6)',
                            borderColor: 'rgba(3, 102, 214, 1)',
                            borderWidth: 1
                        }, {
                            label: '智能分块处理时间 (ms)',
                            data: [{% for query in queries %}{{ query.strategies.intelligent.time_ms }}{% if not loop.last %}, {% endif %}{% endfor %}],
                            backgroundColor: 'rgba(40, 167, 69, 0.6)',
                            borderColor: 'rgba(40, 167, 69, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top'
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        animation: {
                            duration: 0 // 禁用动画，确保立即渲染
                        }
                    }
                });

                // 各查询的对比图
                {% for query in queries %}
                const comparisonCtx{{ loop.index }} = document.getElementById('comparisonChart-{{ loop.index }}').getContext('2d');
                new Chart(comparisonCtx{{ loop.index }}, {
                    type: 'bar',
                    data: {
                        labels: ['相似度 (x10)', '处理时间 (ms)'],
                        datasets: [{
                            label: '固定分块策略',
                            data: [
                                {{ query.strategies.fixed_size.avg_similarity * 10 }}, 
                                {{ query.strategies.fixed_size.time_ms }}
                            ],
                            backgroundColor: 'rgba(3, 102, 214, 0.6)',
                            borderColor: 'rgba(3, 102, 214, 1)',
                            borderWidth: 1
                        }, {
                            label: '智能分块策略',
                            data: [
                                {{ query.strategies.intelligent.avg_similarity * 10 }}, 
                                {{ query.strategies.intelligent.time_ms }}
                            ],
                            backgroundColor: 'rgba(40, 167, 69, 0.6)',
                            borderColor: 'rgba(40, 167, 69, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'top'
                            },
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        const label = context.dataset.label || '';
                                        let value = context.raw;
                                        if (context.dataIndex === 0) {
                                            return label + ': ' + (value / 10).toFixed(4);
                                        }
                                        return label + ': ' + value + ' ms';
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        },
                        animation: {
                            duration: 0 // 禁用动画，确保立即渲染
                        }
                    }
                });
                {% endfor %}
            } catch (e) {
                console.error('DOMContentLoaded error:', e);
            }
        });
    </script>
</body>
</html>
"""

async def fetch_search_result(session, url, query, limit=5, source_filter=""):
    """异步获取搜索结果"""
    try:
        # 不再尝试使用不存在的compare-strategies-v2端点
        
        payload = {
            "query": query,
            "limit": limit,
            "disable_cache": True  # 添加禁用缓存标志
        }
        
        # 如果有source_filter，添加到payload
        if source_filter:
            payload["source_filter"] = source_filter
            
        headers = {
            "Content-Type": "application/json",
            "X-Disable-Cache": "true"  # 添加HTTP头禁用缓存
        }
        
        print(f"发送请求到 {url}")
        print(f"请求参数: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    # 打印API返回的结果
                    print(f"\n查询: '{query}'")
                    print(f"API响应结果:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    return result
                else:
                    error_text = await response.text()
                    print(f"错误: 状态码 {response.status} - {error_text}")
                    return {
                        "query": query,
                        "error": f"服务器返回错误 (状态码 {response.status}): {error_text}",
                        "strategies": {
                            "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                            "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                        },
                        "best_strategy": "fixed_size",
                        "evaluation": {"strategy": "fixed_size", "reason": "无法完成测试"}
                    }
        except asyncio.TimeoutError:
            print(f"请求超时: {url}")
            return {
                "query": query,
                "error": "请求超时，请检查服务器状态",
                "strategies": {
                    "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                    "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                },
                "best_strategy": "fixed_size",
                "evaluation": {"strategy": "fixed_size", "reason": "请求超时"}
            }
        except aiohttp.ClientConnectorError as e:
            print(f"连接错误: {e}")
            return {
                "query": query,
                "error": f"无法连接到服务器 ({url})，请确保服务器正在运行",
                "strategies": {
                    "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                    "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                },
                "best_strategy": "fixed_size",
                "evaluation": {"strategy": "fixed_size", "reason": "无法连接到服务器"}
            }
            
    except Exception as e:
        print(f"请求异常: {e}")
        return {
            "query": query,
            "error": f"请求失败: {str(e)}",
            "strategies": {
                "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
            },
            "best_strategy": "fixed_size",
            "evaluation": {"strategy": "fixed_size", "reason": "请求异常"}
        }

async def process_queries(base_url, questions, limit=5, source_filter=""):
    """处理所有查询"""
    url = f"{base_url}/api/v1/compare-strategies"
    
    # 不再直接在URL中添加source_filter参数，我们会在payload中处理
    # if source_filter:
    #     url += f"?source_filter={source_filter}"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for question in questions:
            tasks.append(fetch_search_result(session, url, question, limit, source_filter))
        
        # 使用tqdm显示进度
        results = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="处理查询"):
            result = await f
            if result:
                results.append(result)
        
        return results

def download_chart_js(output_dir):
    """下载或复制Chart.js库到指定目录"""
    # 本地Chart.js文件路径
    local_chart_path = os.path.join(os.getcwd(), "static", "js", "chart.min.js")
    output_path = os.path.join(output_dir, "chart.min.js")
    
    # 检查本地文件是否存在
    if os.path.exists(local_chart_path):
        try:
            print(f"复制Chart.js从 {local_chart_path} 到 {output_path}")
            shutil.copy2(local_chart_path, output_path)
            print(f"复制成功，文件大小: {os.path.getsize(output_path)} 字节")
            return True
        except Exception as e:
            print(f"复制Chart.js失败: {e}")
            print(f"尝试从CDN下载...")
            
    # 如果本地文件不存在或复制失败，尝试从CDN下载
    try:
        # 使用最新稳定版本的Chart.js
        url = "https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"
        print(f"从CDN下载Chart.js到 {output_path}")
        urllib.request.urlretrieve(url, output_path)
        file_size = os.path.getsize(output_path)
        print(f"下载成功，文件大小: {file_size} 字节")
        
        # 验证文件大小是否合理 (至少100KB)
        if file_size < 100000:
            print(f"警告: 下载的文件大小异常 ({file_size} 字节)，可能下载不完整")
            
        # 验证文件内容是否为有效的JavaScript
        with open(output_path, 'r', encoding='utf-8', errors='ignore') as f:
            content_start = f.read(100).strip()  # 读取前100个字符
            if not content_start.startswith('!function') and not content_start.startswith('/*') and not content_start.startswith('//'):
                print(f"警告: 下载的文件可能不是有效的JavaScript文件")
                print(f"文件开头: {content_start[:50]}...")
                
        return True
    except Exception as e:
        print(f"下载Chart.js失败: {e}")
        print("尝试使用备用CDN链接...")
        
        try:
            # 备用链接
            url = "https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"
            urllib.request.urlretrieve(url, output_path)
            print(f"备用链接下载成功，文件大小: {os.path.getsize(output_path)} 字节")
            return True
        except Exception as e2:
            print(f"备用链接下载也失败: {e2}")
            print("生成无图表版本的报告...")
            return False

def generate_report(results, output_file):
    """生成HTML报告"""
    # 检查是否有错误
    has_errors = any("error" in r for r in results)
    
    # 计算统计数据
    total_queries = len(results)
    
    # 如果所有查询都失败，生成错误报告
    if all("error" in r for r in results):
        template_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "current_year": datetime.now().year,
            "total_queries": total_queries,
            "errors": [
                {
                    "query": r.get("query", "未知查询"),
                    "error": r.get("error", "未知错误")
                }
                for r in results
            ]
        }
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # 渲染错误报告HTML
        error_html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>基准测试错误报告</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f8fa;
                }}
                h1, h2 {{
                    color: #d73a49;
                }}
                .error-container {{
                    background-color: #fff;
                    border-radius: 8px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.12);
                    padding: 20px;
                    margin-bottom: 20px;
                    border-left: 5px solid #d73a49;
                }}
                .error-details {{
                    background-color: #f6f8fa;
                    border: 1px solid #e1e4e8;
                    border-radius: 4px;
                    padding: 15px;
                    margin: 10px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding: 20px;
                    color: #586069;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <h1>基准测试运行失败</h1>
                <p>所有查询({total_queries}个)均失败。请检查服务器连接和配置。</p>
                
                <h2>错误详情:</h2>
                {"".join([f'''
                <div class="error-details">
                    <strong>查询:</strong> {err['query']}<br>
                    <strong>错误:</strong> {err['error']}
                </div>
                ''' for err in template_data['errors']])}
            </div>
            
            <div class="footer">
                <p>© {template_data['current_year']} 向量搜索基准测试报告 | 生成于 {template_data['timestamp']}</p>
            </div>
        </body>
        </html>
        """
        
        # 写入文件
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(error_html)
            
        print(f"错误报告已生成: {output_file}")
        return
    
    # 有部分成功的查询，计算统计数据
    valid_results = [r for r in results if "error" not in r]
    fixed_wins = sum(1 for r in valid_results if r.get("best_strategy") == "fixed_size")
    intelligent_wins = len(valid_results) - fixed_wins
    
    # 计算平均相似度和处理时间
    fixed_similarities = [r.get("strategies", {}).get("fixed_size", {}).get("avg_similarity", 0) for r in valid_results]
    intelligent_similarities = [r.get("strategies", {}).get("intelligent", {}).get("avg_similarity", 0) for r in valid_results]
    
    fixed_times = [r.get("strategies", {}).get("fixed_size", {}).get("time_ms", 0) for r in valid_results]
    intelligent_times = [r.get("strategies", {}).get("intelligent", {}).get("time_ms", 0) for r in valid_results]
    
    fixed_avg_similarity = sum(fixed_similarities) / len(valid_results) if valid_results else 0
    intelligent_avg_similarity = sum(intelligent_similarities) / len(valid_results) if valid_results else 0
    
    fixed_avg_time = sum(fixed_times) / len(valid_results) if valid_results else 0
    intelligent_avg_time = sum(intelligent_times) / len(valid_results) if valid_results else 0
    
    # 准备模板数据
    template_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "current_year": datetime.now().year,
        "total_queries": len(valid_results),
        "fixed_wins": fixed_wins,
        "intelligent_wins": intelligent_wins,
        "fixed_avg_similarity": fixed_avg_similarity,
        "intelligent_avg_similarity": intelligent_avg_similarity,
        "fixed_avg_time": fixed_avg_time,
        "intelligent_avg_time": intelligent_avg_time,
        "queries": valid_results,
        "has_errors": has_errors,
        "errors": [r for r in results if "error" in r],
        "chart_js_missing": False
    }
    
    # 确保输出目录存在
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 下载Chart.js到输出目录
    has_chart_js = download_chart_js(output_dir)
    
    # 如果无法下载Chart.js，修改模板以使用简单的内联图表
    if not has_chart_js:
        print("检测到Chart.js不可用，使用简单内联图表替代...")
        # 在HTML中添加内联的简单图表代码
        template_data["use_inline_chart"] = True
        template_data["chart_js_missing"] = True
    else:
        template_data["use_inline_chart"] = False
    
    # 渲染HTML
    template = Template(HTML_TEMPLATE)
    html_content = template.render(**template_data)
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"报告已生成: {output_file}")

def start_web_server(report_path, port=8080):
    """启动简单的HTTP服务器来展示报告"""
    report_dir = os.path.dirname(os.path.abspath(report_path))
    os.chdir(report_dir)
    report_filename = os.path.basename(report_path)
    
    # 自定义处理器，自动打开首页
    class MyHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/':
                self.path = f'/{report_filename}'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
    
    # 创建服务器
    handler = MyHandler
    httpd = socketserver.TCPServer(("", port), handler)
    
    # 显示服务器信息
    print(f"服务器启动在 http://localhost:{port}")
    print(f"报告访问地址: http://localhost:{port}/{report_filename}")
    print("按 Ctrl+C 停止服务器")
    
    # 打开浏览器
    webbrowser.open(f"http://localhost:{port}/{report_filename}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("服务器已停止")
    finally:
        httpd.server_close()

def main():
    parser = argparse.ArgumentParser(description="向量搜索基准测试工具")
    parser.add_argument("--url", default="http://35.246.2.155:8000", help="API服务器URL")
    parser.add_argument("--output", default="./static/report/benchmark.html", help="输出HTML报告文件路径")
    parser.add_argument("--questions", nargs="+", help="要测试的问题列表")
    parser.add_argument("--file", help="包含问题列表的文件，每行一个问题")
    parser.add_argument("--limit", type=int, default=5, help="每个查询返回的最大结果数")
    parser.add_argument("--source-filter", default="", help="源文档过滤条件")
    parser.add_argument("--web-server", action="store_true", help="生成报告后启动Web服务器来展示报告")
    parser.add_argument("--port", type=int, default=8080, help="Web服务器端口号，默认为8080")
    
    args = parser.parse_args()
    
    # 先检查服务器连通性
    try:
        print(f"检查服务器连通性 ({args.url})...")
        response = requests.get(f"{args.url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            print(f"服务器连接成功: {response.json()}")
        else:
            print(f"警告: 服务器响应状态码 {response.status_code}")
    except requests.RequestException as e:
        print(f"警告: 无法连接到服务器 ({args.url}): {e}")
        print("测试将继续，但可能无法获取有效结果")
    
    # 获取问题列表
    questions = []
    if args.questions:
        questions = args.questions
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            questions = [line.strip() for line in f if line.strip()]
    else:
        questions = DEFAULT_QUESTIONS
    
    print(f"将处理 {len(questions)} 个问题的查询")
    
    # 执行查询
    results = asyncio.run(process_queries(args.url, questions, args.limit, args.source_filter))
    
    # 生成报告
    generate_report(results, args.output)
    
    # 如果开启了Web服务器选项，启动服务器
    if args.web_server:
        start_web_server(args.output, args.port)

if __name__ == "__main__":
    main() 