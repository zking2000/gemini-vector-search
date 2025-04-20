"""
Main entry file, used to start the application from the project root directory
"""
import os
import argparse
from app.main import app

if __name__ == "__main__":
    import uvicorn
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Gemini Vector Search Platform Launcher')
    parser.add_argument('--host', type=str, default=os.getenv("HOST", "0.0.0.0"),
                        help='Binding host address (default: 0.0.0.0 or HOST environment variable)')
    parser.add_argument('--port', type=int, default=int(os.getenv("PORT", "8000")),
                        help='Binding port (default: 8000 or PORT environment variable)')
    parser.add_argument('--reload', action='store_true', default=True,
                        help='Enable auto-reload (default: enabled)')
    parser.add_argument('--no-reload', dest='reload', action='store_false',
                        help='Disable auto-reload')
    
    args = parser.parse_args()
    
    # Start server with command line arguments
    print(f"Starting backend service - Address: {args.host}:{args.port} - Auto-reload: {'enabled' if args.reload else 'disabled'}")
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload) 