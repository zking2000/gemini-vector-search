#!/bin/bash

# 定义颜色常量
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # 无颜色

# 定义文件路径和目录
PID_DIR="./pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
FRONTEND_DIR="./static/gemini-ui"
LOG_DIR="./logs"

# 创建日志子目录
BACKEND_LOG_DIR="$LOG_DIR/backend"
FRONTEND_LOG_DIR="$LOG_DIR/frontend"
mkdir -p $BACKEND_LOG_DIR
mkdir -p $FRONTEND_LOG_DIR

# 使用时间戳创建唯一的日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKEND_LOG="$BACKEND_LOG_DIR/backend_${TIMESTAMP}.log"
FRONTEND_LOG="$FRONTEND_LOG_DIR/frontend_${TIMESTAMP}.log"
BACKEND_CURRENT_LOG="$LOG_DIR/backend_current.log"
FRONTEND_CURRENT_LOG="$LOG_DIR/frontend_current.log"

# 创建必要的目录
mkdir -p $PID_DIR
mkdir -p $LOG_DIR
mkdir -p $BACKEND_LOG_DIR
mkdir -p $FRONTEND_LOG_DIR

# 检查端口占用并清理进程
check_and_clean_port() {
    port=$1
    service_name=$2

    echo -e "${YELLOW}检查端口 $port 是否被占用...${NC}"

    # 尝试使用lsof（大多数Linux/Unix系统支持）
    if command -v lsof &> /dev/null; then
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo -e "${RED}发现端口 $port 被进程 $pid 占用${NC}"
            echo -e "${YELLOW}正在终止占用 $service_name 端口的进程...${NC}"
            kill -9 $pid
            sleep 1
            echo -e "${GREEN}端口 $port 已释放${NC}"
            return 0
        fi
    # 如果lsof不可用，尝试使用netstat
    elif command -v netstat &> /dev/null; then
        pid=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -n1)
        if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
            echo -e "${RED}发现端口 $port 被进程 $pid 占用${NC}"
            echo -e "${YELLOW}正在终止占用 $service_name 端口的进程...${NC}"
            kill -9 $pid
            sleep 1
            echo -e "${GREEN}端口 $port 已释放${NC}"
            return 0
        fi
    # 如果都不可用，提示用户手动检查
    else
        echo -e "${YELLOW}无法检查端口占用情况，请确保端口 $port 未被占用${NC}"
    fi

    echo -e "${GREEN}端口 $port 可用${NC}"
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}Gemini 向量搜索平台控制脚本${NC}"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start         启动前后端服务"
    echo "  start-frontend 仅启动前端服务"
    echo "  start-backend 仅启动后端服务"
    echo "  stop          停止前后端服务"
    echo "  stop-frontend 仅停止前端服务"
    echo "  stop-backend  仅停止后端服务"
    echo "  restart       重启前后端服务"
    echo "  restart-frontend 仅重启前端服务"
    echo "  restart-backend  仅重启后端服务"
    echo "  status        查看服务运行状态"
    echo "  logs          查看当前日志"
    echo "  help          显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start      启动所有服务"
    echo "  $0 start-frontend 仅启动前端服务"
    echo "  $0 start-backend  仅启动后端服务"
    echo "  $0 stop       停止所有服务"
    echo "  $0 logs       显示当前日志"
}

# 检查服务状态
check_process() {
    pid=$1
    if ps -p $pid > /dev/null 2>&1; then
        return 0  # 进程正在运行
    else
        return 1  # 进程不存在
    fi
}

# 启动后端服务
start_backend() {
    echo -e "${YELLOW}正在启动后端服务...${NC}"

    # 检查端口占用
    check_and_clean_port 8000 "后端"

    # 检查是否已经运行
    if [ -f $BACKEND_PID_FILE ]; then
        pid=$(cat $BACKEND_PID_FILE)
        if check_process $pid; then
            echo -e "${RED}后端服务已经在运行中 (PID: $pid)${NC}"
            return 1
        else
            # 如果PID文件存在但进程不存在，删除旧的PID文件
            rm $BACKEND_PID_FILE
        fi
    fi

    # 在日志文件开始添加启动时间信息
    echo "===== 后端服务启动于 $(date) =====" > $BACKEND_LOG
    
    # 启动后端服务
    python main.py >> $BACKEND_LOG 2>&1 &
    backend_pid=$!
    echo $backend_pid > $BACKEND_PID_FILE

    # 创建指向当前日志的符号链接
    rm -f $BACKEND_CURRENT_LOG
    ln -sf $BACKEND_LOG $BACKEND_CURRENT_LOG
    
    # 记录日志文件路径到PID文件旁边，以便其他命令可以找到它
    echo $BACKEND_LOG > "${BACKEND_PID_FILE}.log"

    # 等待一会儿确认进程仍在运行
    sleep 2
    if check_process $backend_pid; then
        echo -e "${GREEN}后端服务已启动 (PID: $backend_pid)${NC}"
        echo -e "${GREEN}日志文件: $BACKEND_LOG${NC}"
        echo -e "${GREEN}当前日志链接: $BACKEND_CURRENT_LOG${NC}"
        return 0
    else
        echo -e "${RED}后端服务启动失败，请查看日志：$BACKEND_LOG${NC}"
        return 1
    fi
}

# 启动前端服务
start_frontend() {
    echo -e "${YELLOW}正在启动前端服务...${NC}"

    # 检查端口占用
    check_and_clean_port 5173 "前端"

    # 检查前端目录是否存在
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}前端目录不存在: $FRONTEND_DIR${NC}"
        return 1
    fi

    # 检查是否已经运行
    if [ -f $FRONTEND_PID_FILE ]; then
        pid=$(cat $FRONTEND_PID_FILE)
        if check_process $pid; then
            echo -e "${RED}前端服务已经在运行中 (PID: $pid)${NC}"
            return 1
        else
            # 如果PID文件存在但进程不存在，删除旧的PID文件
            rm $FRONTEND_PID_FILE
        fi
    fi

    # 在日志文件开始添加启动时间信息
    echo "===== 前端服务启动于 $(date) =====" > $FRONTEND_LOG
    
    # 进入前端目录并启动服务
    cd $FRONTEND_DIR

    # 检查是否安装了依赖
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}安装前端依赖...${NC}" | tee -a ../../$FRONTEND_LOG
        npm install >> ../../$FRONTEND_LOG 2>&1
    fi

    # 启动前端服务
    npm start >> ../../$FRONTEND_LOG 2>&1 &
    frontend_pid=$!
    cd ../../
    echo $frontend_pid > $FRONTEND_PID_FILE
    
    # 创建指向当前日志的符号链接
    rm -f $FRONTEND_CURRENT_LOG
    ln -sf $FRONTEND_LOG $FRONTEND_CURRENT_LOG
    
    # 记录日志文件路径到PID文件旁边，以便其他命令可以找到它
    echo $FRONTEND_LOG > "${FRONTEND_PID_FILE}.log"

    # 等待一会儿确认进程仍在运行
    sleep 3
    if check_process $frontend_pid; then
        echo -e "${GREEN}前端服务已启动 (PID: $frontend_pid)${NC}"
        echo -e "${BLUE}前端访问地址: http://localhost:5173${NC}"
        echo -e "${GREEN}日志文件: $FRONTEND_LOG${NC}"
        echo -e "${GREEN}当前日志链接: $FRONTEND_CURRENT_LOG${NC}"
        return 0
    else
        echo -e "${RED}前端服务启动失败，请查看日志：$FRONTEND_LOG${NC}"
        return 1
    fi
}

# 停止服务
stop_service() {
    service_name=$1
    pid_file=$2

    if [ -f $pid_file ]; then
        pid=$(cat $pid_file)
        echo -e "${YELLOW}正在停止${service_name}服务 (PID: $pid)...${NC}"

        if check_process $pid; then
            kill $pid
            sleep 2

            # 检查是否成功停止
            if check_process $pid; then
                echo -e "${RED}${service_name}服务未能正常停止，尝试强制终止...${NC}"
                kill -9 $pid
                sleep 1
            fi

            if check_process $pid; then
                echo -e "${RED}无法停止${service_name}服务，请手动终止进程 $pid${NC}"
                return 1
            else
                echo -e "${GREEN}${service_name}服务已停止${NC}"
            fi
        else
            echo -e "${YELLOW}${service_name}服务不在运行中${NC}"
        fi

        rm $pid_file
        # 删除日志文件路径记录但保留日志文件本身
        if [ -f "${pid_file}.log" ]; then
            rm "${pid_file}.log"
        fi
    else
        echo -e "${YELLOW}${service_name}服务未运行${NC}"
    fi

    return 0
}

# 显示日志
show_logs() {
    # 检查后端日志
    if [ -f $BACKEND_CURRENT_LOG ]; then
        echo -e "${GREEN}=== 后端日志 (最新) ===${NC}"
        tail -n 20 $BACKEND_CURRENT_LOG
        echo -e "${GREEN}查看完整日志: less $BACKEND_CURRENT_LOG${NC}"
    else
        echo -e "${YELLOW}后端日志不存在${NC}"
    fi
    
    echo ""
    
    # 检查前端日志
    if [ -f $FRONTEND_CURRENT_LOG ]; then
        echo -e "${GREEN}=== 前端日志 (最新) ===${NC}"
        tail -n 20 $FRONTEND_CURRENT_LOG
        echo -e "${GREEN}查看完整日志: less $FRONTEND_CURRENT_LOG${NC}"
    else
        echo -e "${YELLOW}前端日志不存在${NC}"
    fi
}

# 启动所有服务
start_all() {
    echo -e "${BLUE}=== 启动所有服务 ===${NC}"
    start_backend
    backend_status=$?
    start_frontend
    frontend_status=$?

    echo ""
    if [ $backend_status -eq 0 ] && [ $frontend_status -eq 0 ]; then
        echo -e "${GREEN}所有服务已成功启动${NC}"
        return 0
    else
        echo -e "${RED}一个或多个服务启动失败${NC}"
        return 1
    fi
}

# 停止所有服务
stop_all() {
    echo -e "${BLUE}=== 停止所有服务 ===${NC}"
    echo -e "${YELLOW}优先停止前端服务...${NC}"
    stop_service "前端" $FRONTEND_PID_FILE

    echo -e "${YELLOW}然后停止后端服务...${NC}"
    stop_service "后端" $BACKEND_PID_FILE

    echo ""
    echo -e "${GREEN}所有服务已停止${NC}"
}

# 重启所有服务
restart_all() {
    echo -e "${BLUE}=== 重启所有服务 ===${NC}"
    stop_all
    echo ""
    start_all
}

# 重启前端服务
restart_frontend() {
    echo -e "${BLUE}=== 重启前端服务 ===${NC}"
    stop_service "前端" $FRONTEND_PID_FILE
    echo ""
    start_frontend
}

# 重启后端服务
restart_backend() {
    echo -e "${BLUE}=== 重启后端服务 ===${NC}"
    stop_service "后端" $BACKEND_PID_FILE
    echo ""
    start_backend
}

# 显示服务状态
show_status() {
    echo -e "${BLUE}=== 服务状态 ===${NC}"

    # 检查后端状态
    if [ -f $BACKEND_PID_FILE ]; then
        backend_pid=$(cat $BACKEND_PID_FILE)
        if check_process $backend_pid; then
            echo -e "${GREEN}后端服务: 运行中 (PID: $backend_pid)${NC}"
            # 如果有日志文件记录，显示日志路径
            if [ -f "${BACKEND_PID_FILE}.log" ]; then
                backend_log=$(cat "${BACKEND_PID_FILE}.log")
                echo -e "${GREEN}后端日志: $backend_log${NC}"
            fi
        else
            echo -e "${RED}后端服务: 进程不存在，但PID文件存在${NC}"
        fi
    else
        echo -e "${YELLOW}后端服务: 未运行${NC}"
    fi

    # 检查前端状态
    if [ -f $FRONTEND_PID_FILE ]; then
        frontend_pid=$(cat $FRONTEND_PID_FILE)
        if check_process $frontend_pid; then
            echo -e "${GREEN}前端服务: 运行中 (PID: $frontend_pid)${NC}"
            echo -e "${BLUE}前端访问地址: http://localhost:5173${NC}"
            # 如果有日志文件记录，显示日志路径
            if [ -f "${FRONTEND_PID_FILE}.log" ]; then
                frontend_log=$(cat "${FRONTEND_PID_FILE}.log")
                echo -e "${GREEN}前端日志: $frontend_log${NC}"
            fi
        else
            echo -e "${RED}前端服务: 进程不存在，但PID文件存在${NC}"
        fi
    else
        echo -e "${YELLOW}前端服务: 未运行${NC}"
    fi
}

# 主逻辑
case "$1" in
    start)
        start_all
        ;;
    start-frontend)
        start_frontend
        ;;
    start-backend)
        start_backend
        ;;
    stop)
        stop_all
        ;;
    stop-frontend)
        stop_service "前端" $FRONTEND_PID_FILE
        ;;
    stop-backend)
        stop_service "后端" $BACKEND_PID_FILE
        ;;
    restart)
        restart_all
        ;;
    restart-frontend)
        restart_frontend
        ;;
    restart-backend)
        restart_backend
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac

exit 0