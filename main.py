"""
主入口文件，用于从项目根目录启动应用
"""
import os
import argparse
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='Gemini向量搜索平台启动器')
    parser.add_argument('--host', type=str, default=os.getenv("HOST", "0.0.0.0"),
                        help='绑定的主机地址 (默认: 0.0.0.0 或环境变量HOST)')
    parser.add_argument('--port', type=int, default=int(os.getenv("PORT", "8000")),
                        help='绑定的端口 (默认: 8000 或环境变量PORT)')
    parser.add_argument('--reload', action='store_true', default=True,
                        help='启用自动重载 (默认: 开启)')
    parser.add_argument('--no-reload', dest='reload', action='store_false',
                        help='禁用自动重载')
    
    args = parser.parse_args()
    
    # 使用命令行参数启动服务器
    print(f"启动后端服务 - 地址: {args.host}:{args.port} - 自动重载: {'启用' if args.reload else '禁用'}")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload) 