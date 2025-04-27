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

# Default test questions
DEFAULT_QUESTIONS = [
    "What was the percentage allocation across asset classes in 2023?",
    "Which companies contributed most to the fund's return in 2023?",
    "What was the difference between the fund's return and the benchmark index?",
    "How did unlisted real estate perform and why?",
    "What strategic shifts were made in response to geopolitical tensions?",
    "Which companies were excluded based on responsible investment criteria?",
    "What insights came out of the stress test scenarios in the report?",
    "How did the fund's renewable energy investments evolve?",
    "What long-term investment trends were highlighted?",
    "How did fixed-income instruments contribute to the fund's return?"
]

# HTML template for English
HTML_TEMPLATE_EN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Vector Search Benchmark Report</title>
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
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .comparison-table th, .comparison-table td {
            border: 1px solid #e1e4e8;
            padding: 8px 12px;
            text-align: left;
        }
        .comparison-table th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        .comparison-table tr:nth-child(even) {
            background-color: #f9f9f9;
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
        @media (max-width: 768px) {
            .summary-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Vector Search Benchmark Report</h1>
        <p>Generated on {{ timestamp }}</p>
    </div>

    <div class="summary">
        <div class="summary-header">
            <h2>Execution Results Summary</h2>
        </div>
        <div class="summary-stats">
            <div class="stat-card">
                <div class="stat-label">Total Queries</div>
                <div class="stat-value">{{ total_queries }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fixed Search Wins</div>
                <div class="stat-value">{{ fixed_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Intelligent Search Wins</div>
                <div class="stat-value">{{ intelligent_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fixed Search Avg Similarity</div>
                <div class="stat-value">{{ "%.4f"|format(fixed_avg_similarity) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Intelligent Search Avg Similarity</div>
                <div class="stat-value">{{ "%.4f"|format(intelligent_avg_similarity) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Fixed Search Avg Time</div>
                <div class="stat-value">{{ "%.2f"|format(fixed_avg_time) }}ms</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Intelligent Search Avg Time</div>
                <div class="stat-value">{{ "%.2f"|format(intelligent_avg_time) }}ms</div>
            </div>
        </div>

        <div class="summary-header" style="margin-top: 30px;">
            <h2>Strategy Comparison Table</h2>
        </div>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>Metric</th>
                    <th>Fixed Search Strategy</th>
                    <th>Intelligent Search Strategy</th>
                    <th>Winning Strategy</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>Wins Count</td>
                    <td>{{ fixed_wins }}</td>
                    <td>{{ intelligent_wins }}</td>
                    <td>{{ "Fixed Search" if fixed_wins > intelligent_wins else "Intelligent Search" }}</td>
                </tr>
                <tr>
                    <td>Average Similarity</td>
                    <td>{{ "%.4f"|format(fixed_avg_similarity) }}</td>
                    <td>{{ "%.4f"|format(intelligent_avg_similarity) }}</td>
                    <td>{{ "Fixed Search" if fixed_avg_similarity > intelligent_avg_similarity else "Intelligent Search" }}</td>
                </tr>
                <tr>
                    <td>Average Processing Time</td>
                    <td>{{ "%.2f"|format(fixed_avg_time) }}ms</td>
                    <td>{{ "%.2f"|format(intelligent_avg_time) }}ms</td>
                    <td>{{ "Fixed Search" if fixed_avg_time < intelligent_avg_time else "Intelligent Search" }}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <h2>Query Detailed Results</h2>
    
    {% for query in queries %}
    <div class="query-card">
        <div class="query-header">
            <h3 class="query-title">{{ query.query }}</h3>
            
            <span class="winner-label">{{ "Fixed Search Strategy Won" if query.best_strategy == "fixed_size" else "Intelligent Search Strategy Won" }}</span>
            
        </div>
        <div class="query-body">
            <div class="result-meta">
                <strong>Evaluation Result:</strong> {{ query.evaluation.reason }}
            </div>
            
            <div class="result-card fixed">
                <div class="result-header">
                    <span>Fixed Search Strategy Results<span class="badge fixed">{{ query.strategies.fixed_size.count }} documents</span></span>
                    <span>Similarity: {{ "%.4f"|format(query.strategies.fixed_size.avg_similarity) }} | Processing Time: {{ query.strategies.fixed_size.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>Top {{ query.strategies.fixed_size.documents|length }} results:</strong>
                </div>
                
                {% for doc in query.strategies.fixed_size.documents %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>Document ID: {{ doc.id }} | Similarity: {{ "%.4f"|format(doc.score) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
                
            </div>
            
            <div class="result-card intelligent">
                <div class="result-header">
                    <span>Intelligent Search Strategy Results<span class="badge intelligent">{{ query.strategies.intelligent.count }} documents</span></span>
                    <span>Similarity: {{ "%.4f"|format(query.strategies.intelligent.avg_similarity) }} | Processing Time: {{ query.strategies.intelligent.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>Top {{ query.strategies.intelligent.documents|length }} results:</strong>
                </div>
                
                {% for doc in query.strategies.intelligent.documents %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>Document ID: {{ doc.id }} | Similarity: {{ "%.4f"|format(doc.score) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
                
            </div>
            
            <div class="result-meta">
                <strong>Similarity and Processing Time Comparison</strong>
            </div>
            
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>Strategy</th>
                        <th>Average Similarity</th>
                        <th>Processing Time (ms)</th>
                        <th>Winning Metric</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Fixed Search Strategy</td>
                        <td>{{ "%.4f"|format(query.strategies.fixed_size.avg_similarity) }}</td>
                        <td>{{ "%.2f"|format(query.strategies.fixed_size.time_ms) }}</td>
                        <td>{% if query.best_strategy == "fixed_size" %}Higher Similarity{% endif %}</td>
                    </tr>
                    <tr>
                        <td>Intelligent Search Strategy</td>
                        <td>{{ "%.4f"|format(query.strategies.intelligent.avg_similarity) }}</td>
                        <td>{{ "%.2f"|format(query.strategies.intelligent.time_ms) }}</td>
                        <td>{% if query.best_strategy == "intelligent" %}Higher Similarity{% endif %}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    {% endfor %}

    {% if has_errors %}
    <div class="summary">
        <div class="summary-header">
            <h2>Execution Errors</h2>
        </div>
        <div class="error-details">
            {% for error in errors %}
            <div class="result-card" style="border-left: 4px solid #d73a49;">
                <div class="result-header">
                    <span>Query: {{ error.query }}</span>
                </div>
                <div class="result-content">
                    <pre>{{ error.error }}</pre>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>© {{ current_year }} Vector Search Benchmark Report | Generated on {{ timestamp }}</p>
    </div>
</body>
</html>
"""

# HTML template for Chinese
HTML_TEMPLATE_ZH = """
<!DOCTYPE html>
<html lang="zh">
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
        .comparison-table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        .comparison-table th, .comparison-table td {
            border: 1px solid #e1e4e8;
            padding: 8px 12px;
            text-align: left;
        }
        .comparison-table th {
            background-color: #f6f8fa;
            font-weight: 600;
        }
        .comparison-table tr:nth-child(even) {
            background-color: #f9f9f9;
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
        @media (max-width: 768px) {
            .summary-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>向量搜索基准测试报告</h1>
        <p>生成时间：{{ timestamp }}</p>
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
                <div class="stat-label">固定搜索获胜</div>
                <div class="stat-value">{{ fixed_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能搜索获胜</div>
                <div class="stat-value">{{ intelligent_wins }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">固定搜索平均相似度</div>
                <div class="stat-value">{{ "%.4f"|format(fixed_avg_similarity) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能搜索平均相似度</div>
                <div class="stat-value">{{ "%.4f"|format(intelligent_avg_similarity) }}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">固定搜索平均时间</div>
                <div class="stat-value">{{ "%.2f"|format(fixed_avg_time) }}ms</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">智能搜索平均时间</div>
                <div class="stat-value">{{ "%.2f"|format(intelligent_avg_time) }}ms</div>
            </div>
        </div>

        <div class="summary-header" style="margin-top: 30px;">
            <h2>策略比较表</h2>
        </div>
        <table class="comparison-table">
            <thead>
                <tr>
                    <th>指标</th>
                    <th>固定搜索策略</th>
                    <th>智能搜索策略</th>
                    <th>获胜策略</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>获胜次数</td>
                    <td>{{ fixed_wins }}</td>
                    <td>{{ intelligent_wins }}</td>
                    <td>{{ "固定搜索" if fixed_wins > intelligent_wins else "智能搜索" }}</td>
                </tr>
                <tr>
                    <td>平均相似度</td>
                    <td>{{ "%.4f"|format(fixed_avg_similarity) }}</td>
                    <td>{{ "%.4f"|format(intelligent_avg_similarity) }}</td>
                    <td>{{ "固定搜索" if fixed_avg_similarity > intelligent_avg_similarity else "智能搜索" }}</td>
                </tr>
                <tr>
                    <td>平均处理时间</td>
                    <td>{{ "%.2f"|format(fixed_avg_time) }}ms</td>
                    <td>{{ "%.2f"|format(intelligent_avg_time) }}ms</td>
                    <td>{{ "固定搜索" if fixed_avg_time < intelligent_avg_time else "智能搜索" }}</td>
                </tr>
            </tbody>
        </table>
    </div>

    <h2>查询详细结果</h2>
    
    {% for query in queries %}
    <div class="query-card">
        <div class="query-header">
            <h3 class="query-title">{{ query.query }}</h3>
            
            <span class="winner-label">{{ "固定搜索策略获胜" if query.best_strategy == "fixed_size" else "智能搜索策略获胜" }}</span>
            
        </div>
        <div class="query-body">
            <div class="result-meta">
                <strong>评估结果:</strong> {{ query.evaluation.reason }}
            </div>
            
            <div class="result-card fixed">
                <div class="result-header">
                    <span>固定搜索策略结果<span class="badge fixed">{{ query.strategies.fixed_size.count }} 文档</span></span>
                    <span>相似度: {{ "%.4f"|format(query.strategies.fixed_size.avg_similarity) }} | 处理时间: {{ query.strategies.fixed_size.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>前 {{ query.strategies.fixed_size.documents|length }} 结果:</strong>
                </div>
                
                {% for doc in query.strategies.fixed_size.documents %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>文档 ID: {{ doc.id }} | 相似度: {{ "%.4f"|format(doc.score) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
                
            </div>
            
            <div class="result-card intelligent">
                <div class="result-header">
                    <span>智能搜索策略结果<span class="badge intelligent">{{ query.strategies.intelligent.count }} 文档</span></span>
                    <span>相似度: {{ "%.4f"|format(query.strategies.intelligent.avg_similarity) }} | 处理时间: {{ query.strategies.intelligent.time_ms }}ms</span>
                </div>
                
                <div class="result-meta">
                    <strong>前 {{ query.strategies.intelligent.documents|length }} 结果:</strong>
                </div>
                
                {% for doc in query.strategies.intelligent.documents %}
                <div class="result-content">
                    <pre>{{ doc.content }}</pre>
                    <div><small>文档 ID: {{ doc.id }} | 相似度: {{ "%.4f"|format(doc.score) }}</small></div>
                </div>
                {% if not loop.last %}<hr>{% endif %}
                {% endfor %}
                
            </div>
            
            <div class="result-meta">
                <strong>相似度和处理时间比较</strong>
            </div>
            
            <table class="comparison-table">
                <thead>
                    <tr>
                        <th>策略</th>
                        <th>平均相似度</th>
                        <th>处理时间 (ms)</th>
                        <th>获胜指标</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>固定搜索策略</td>
                        <td>{{ "%.4f"|format(query.strategies.fixed_size.avg_similarity) }}</td>
                        <td>{{ "%.2f"|format(query.strategies.fixed_size.time_ms) }}</td>
                        <td>{% if query.best_strategy == "fixed_size" %}更高相似度{% endif %}</td>
                    </tr>
                    <tr>
                        <td>智能搜索策略</td>
                        <td>{{ "%.4f"|format(query.strategies.intelligent.avg_similarity) }}</td>
                        <td>{{ "%.2f"|format(query.strategies.intelligent.time_ms) }}</td>
                        <td>{% if query.best_strategy == "intelligent" %}更高相似度{% endif %}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>
    {% endfor %}

    {% if has_errors %}
    <div class="summary">
        <div class="summary-header">
            <h2>执行错误</h2>
        </div>
        <div class="error-details">
            {% for error in errors %}
            <div class="result-card" style="border-left: 4px solid #d73a49;">
                <div class="result-header">
                    <span>查询: {{ error.query }}</span>
                </div>
                <div class="result-content">
                    <pre>{{ error.error }}</pre>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <div class="footer">
        <p>© {{ current_year }} 向量搜索基准测试报告 | 生成于 {{ timestamp }}</p>
    </div>
</body>
</html>
"""

async def fetch_search_result(session, url, query, limit=5, source_filter=""):
    """Asynchronously fetch search results"""
    try:
        payload = {
            "query": query,
            "limit": limit,
            "disable_cache": True
        }
        
        if source_filter:
            payload["source_filter"] = source_filter
            
        headers = {
            "Content-Type": "application/json",
            "X-Disable-Cache": "true"
        }
        
        print(f"Sending request to {url}")
        print(f"Request parameters: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            async with session.post(url, json=payload, headers=headers, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"\nQuery: '{query}'")
                    print(f"API Response Result:")
                    print(json.dumps(result, ensure_ascii=False, indent=2))
                    
                    # 处理返回结果，确保包含所有必要的明细信息
                    processed_result = {
                        "query": query,
                        "strategies": {
                            "fixed_size": {
                                "count": result.get("strategies", {}).get("fixed_size", {}).get("count", 0),
                                "documents": result.get("strategies", {}).get("fixed_size", {}).get("documents", []),
                                "avg_similarity": result.get("strategies", {}).get("fixed_size", {}).get("avg_similarity", 0),
                                "time_ms": result.get("strategies", {}).get("fixed_size", {}).get("time_ms", 0)
                            },
                            "intelligent": {
                                "count": result.get("strategies", {}).get("intelligent", {}).get("count", 0),
                                "documents": result.get("strategies", {}).get("intelligent", {}).get("documents", []),
                                "avg_similarity": result.get("strategies", {}).get("intelligent", {}).get("avg_similarity", 0),
                                "time_ms": result.get("strategies", {}).get("intelligent", {}).get("time_ms", 0)
                            }
                        },
                        "best_strategy": result.get("best_strategy", "fixed_size"),
                        "evaluation": {
                            "strategy": result.get("evaluation", {}).get("strategy", "fixed_size"),
                            "reason": result.get("evaluation", {}).get("reason", "No evaluation provided")
                        }
                    }
                    
                    # 打印处理后的结果
                    print("\nProcessed Result:")
                    print(json.dumps(processed_result, ensure_ascii=False, indent=2))
                    
                    return processed_result
                else:
                    error_text = await response.text()
                    print(f"Error: Status code {response.status} - {error_text}")
                    return {
                        "query": query,
                        "error": f"Server returned error (Status code {response.status}): {error_text}",
                        "strategies": {
                            "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                            "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                        },
                        "best_strategy": "fixed_size",
                        "evaluation": {"strategy": "fixed_size", "reason": "Unable to complete test"}
                    }
        except asyncio.TimeoutError:
            print(f"Request timeout: {url}")
            return {
                "query": query,
                "error": "Request timeout, please check server status",
                "strategies": {
                    "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                    "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                },
                "best_strategy": "fixed_size",
                "evaluation": {"strategy": "fixed_size", "reason": "Request timeout"}
            }
        except aiohttp.ClientConnectorError as e:
            print(f"Connection error: {e}")
            return {
                "query": query,
                "error": f"Unable to connect to server ({url}), please ensure server is running",
                "strategies": {
                    "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                    "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
                },
                "best_strategy": "fixed_size",
                "evaluation": {"strategy": "fixed_size", "reason": "Unable to connect to server"}
            }
            
    except Exception as e:
        print(f"Request exception: {e}")
        return {
            "query": query,
            "error": f"Request failed: {str(e)}",
            "strategies": {
                "fixed_size": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0},
                "intelligent": {"count": 0, "documents": [], "avg_similarity": 0, "time_ms": 0}
            },
            "best_strategy": "fixed_size",
            "evaluation": {"strategy": "fixed_size", "reason": "Request exception"}
        }

async def process_queries(base_url, questions, limit=5, source_filter=""):
    """Process all queries"""
    url = f"{base_url}/api/v1/compare-strategies"
    
    # No longer adding source_filter parameter directly in URL, we'll handle it in payload
    # if source_filter:
    #     url += f"?source_filter={source_filter}"
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for question in questions:
            tasks.append(fetch_search_result(session, url, question, limit, source_filter))
        
        # Use tqdm to show progress
        results = []
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing queries"):
            result = await f
            if result:
                results.append(result)
        
        return results

def download_chart_js(output_dir):
    """
    No longer need to download Chart.js library as we've removed all pie charts
    Keeping this function to maintain code compatibility with other calls
    """
    print("All pie charts have been removed, Chart.js library no longer needed")
    return True

def generate_report(results, output_file, language='en'):
    """Generate HTML report from benchmark results"""
    ensure_output_dir(output_file)
    
    # Select template based on language
    template = HTML_TEMPLATE_EN if language == 'en' else HTML_TEMPLATE_ZH
    
    # Prepare data for template
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_year = datetime.now().year
    
    # Calculate statistics
    total_queries = len(results)
    fixed_wins = sum(1 for r in results if r.get('best_strategy') == 'fixed_size')
    intelligent_wins = sum(1 for r in results if r.get('best_strategy') == 'intelligent')
    
    # Calculate average similarity and processing time
    fixed_similarities = [r.get('strategies', {}).get('fixed_size', {}).get('avg_similarity', 0) for r in results]
    intelligent_similarities = [r.get('strategies', {}).get('intelligent', {}).get('avg_similarity', 0) for r in results]
    
    fixed_times = [r.get('strategies', {}).get('fixed_size', {}).get('time_ms', 0) for r in results]
    intelligent_times = [r.get('strategies', {}).get('intelligent', {}).get('time_ms', 0) for r in results]
    
    fixed_avg_similarity = sum(fixed_similarities) / len(results) if results else 0
    intelligent_avg_similarity = sum(intelligent_similarities) / len(results) if results else 0
    
    fixed_avg_time = sum(fixed_times) / len(results) if results else 0
    intelligent_avg_time = sum(intelligent_times) / len(results) if results else 0
    
    # Check for errors
    has_errors = any('error' in r for r in results)
    errors = [r for r in results if 'error' in r]
    
    # Render template
    template = Template(template)
    html_content = template.render(
        queries=results,  # 将 results 重命名为 queries
        timestamp=timestamp,
        current_year=current_year,
        total_queries=total_queries,
        fixed_wins=fixed_wins,
        intelligent_wins=intelligent_wins,
        fixed_avg_similarity=fixed_avg_similarity,
        intelligent_avg_similarity=intelligent_avg_similarity,
        fixed_avg_time=fixed_avg_time,
        intelligent_avg_time=intelligent_avg_time,
        has_errors=has_errors,
        errors=errors
    )
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Report generated: {output_file}")

def ensure_output_dir(output_file):
    """确保输出目录存在"""
    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")

def main():
    # 确保输出目录存在
    output_dir = os.path.join(os.getcwd(), "static", "gemini-ui", "public", "report")
    os.makedirs(output_dir, exist_ok=True)
    
    # 生成报告文件
    output_en = os.path.join(output_dir, "benchmark_en.html")
    output_zh = os.path.join(output_dir, "benchmark_zh.html")
    
    # 处理查询并生成报告
    base_url = "http://localhost:8000"  # 或者从环境变量获取
    results = asyncio.run(process_queries(
        base_url=base_url,
        questions=DEFAULT_QUESTIONS,
        limit=5
    ))
    generate_report(results, output_en, 'en')
    generate_report(results, output_zh, 'zh')
    
    print(f"报告已生成: {output_en}, {output_zh}")

if __name__ == "__main__":
    main() 