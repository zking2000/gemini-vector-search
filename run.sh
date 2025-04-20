#!/bin/bash

# Define color constants
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No color

# Define file paths and directories
PID_DIR="./pids"
BACKEND_PID_FILE="$PID_DIR/backend.pid"
FRONTEND_PID_FILE="$PID_DIR/frontend.pid"
FRONTEND_DIR="./static/gemini-ui"
LOG_DIR="./logs"

# Create log subdirectories
BACKEND_LOG_DIR="$LOG_DIR/backend"
FRONTEND_LOG_DIR="$LOG_DIR/frontend"
mkdir -p $BACKEND_LOG_DIR
mkdir -p $FRONTEND_LOG_DIR

# Create unique log filename using timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKEND_LOG="$BACKEND_LOG_DIR/backend_${TIMESTAMP}.log"
FRONTEND_LOG="$FRONTEND_LOG_DIR/frontend_${TIMESTAMP}.log"
BACKEND_CURRENT_LOG="$LOG_DIR/backend_current.log"
FRONTEND_CURRENT_LOG="$LOG_DIR/frontend_current.log"

# Create necessary directories
mkdir -p $PID_DIR
mkdir -p $LOG_DIR
mkdir -p $BACKEND_LOG_DIR
mkdir -p $FRONTEND_LOG_DIR

# Check port usage and clean processes
check_and_clean_port() {
    port=$1
    service_name=$2

    echo -e "${YELLOW}Checking if port $port is in use...${NC}"

    # Try using lsof (supported by most Linux/Unix systems)
    if command -v lsof &> /dev/null; then
        pid=$(lsof -ti:$port)
        if [ ! -z "$pid" ]; then
            echo -e "${RED}Port $port is in use by process $pid${NC}"
            echo -e "${YELLOW}Terminating process using $service_name port...${NC}"
            kill -9 $pid
            sleep 1
            echo -e "${GREEN}Port $port has been released${NC}"
            return 0
        fi
    # If lsof is not available, try using netstat
    elif command -v netstat &> /dev/null; then
        pid=$(netstat -tulpn 2>/dev/null | grep ":$port " | awk '{print $7}' | cut -d'/' -f1 | head -n1)
        if [ ! -z "$pid" ] && [ "$pid" != "-" ]; then
            echo -e "${RED}Port $port is in use by process $pid${NC}"
            echo -e "${YELLOW}Terminating process using $service_name port...${NC}"
            kill -9 $pid
            sleep 1
            echo -e "${GREEN}Port $port has been released${NC}"
            return 0
        fi
    # If both are not available, prompt user to check manually
    else
        echo -e "${YELLOW}Unable to check port usage, please ensure port $port is not in use${NC}"
    fi

    echo -e "${GREEN}Port $port is available${NC}"
}

# Display help information
show_help() {
    echo -e "${BLUE}Gemini Vector Search Platform Control Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start         Start frontend and backend services"
    echo "  start-frontend Start only the frontend service"
    echo "  start-backend Start only the backend service"
    echo "  stop          Stop frontend and backend services"
    echo "  stop-frontend Stop only the frontend service"
    echo "  stop-backend  Stop only the backend service"
    echo "  restart       Restart frontend and backend services"
    echo "  restart-frontend Restart only the frontend service"
    echo "  restart-backend  Restart only the backend service"
    echo "  status        Check service running status"
    echo "  logs          View current logs"
    echo "  help          Display this help information"
    echo ""
    echo "Examples:"
    echo "  $0 start      Start all services"
    echo "  $0 start-frontend Start only the frontend service"
    echo "  $0 start-backend  Start only the backend service"
    echo "  $0 stop       Stop all services"
    echo "  $0 logs       Show current logs"
}

# Check service status
check_process() {
    pid=$1
    if ps -p $pid > /dev/null 2>&1; then
        return 0  # Process is running
    else
        return 1  # Process does not exist
    fi
}

# Start backend service
start_backend() {
    echo -e "${YELLOW}Starting backend service...${NC}"

    # Check port usage
    check_and_clean_port 8000 "backend"

    # Check if already running
    if [ -f $BACKEND_PID_FILE ]; then
        pid=$(cat $BACKEND_PID_FILE)
        if check_process $pid; then
            echo -e "${RED}Backend service is already running (PID: $pid)${NC}"
            return 1
        else
            # If PID file exists but process doesn't, delete old PID file
            rm $BACKEND_PID_FILE
        fi
    fi

    # Add start time information at the beginning of the log file
    echo "===== Backend service started at $(date) =====" > $BACKEND_LOG
    
    # Start backend service
    python main.py >> $BACKEND_LOG 2>&1 &
    backend_pid=$!
    echo $backend_pid > $BACKEND_PID_FILE

    # Create symbolic link to current log - use absolute path for reliability
    BACKEND_LOG_ABSOLUTE=$(realpath $BACKEND_LOG)
    rm -f $BACKEND_CURRENT_LOG
    ln -sf $BACKEND_LOG_ABSOLUTE $BACKEND_CURRENT_LOG
    
    # Record log file path next to PID file, so other commands can find it
    echo $BACKEND_LOG_ABSOLUTE > "${BACKEND_PID_FILE}.log"

    # Wait a moment to confirm the process is still running
    sleep 2
    if check_process $backend_pid; then
        echo -e "${GREEN}Backend service started (PID: $backend_pid)${NC}"
        echo -e "${GREEN}Log file: $BACKEND_LOG${NC}"
        echo -e "${GREEN}Current log link: $BACKEND_CURRENT_LOG${NC}"
        return 0
    else
        echo -e "${RED}Backend service failed to start, please check the log: $BACKEND_LOG${NC}"
        return 1
    fi
}

# Start frontend service
start_frontend() {
    echo -e "${YELLOW}Starting frontend service...${NC}"

    # Check port usage
    check_and_clean_port 5173 "frontend"

    # Check if frontend directory exists
    if [ ! -d "$FRONTEND_DIR" ]; then
        echo -e "${RED}Frontend directory does not exist: $FRONTEND_DIR${NC}"
        return 1
    fi

    # Check if already running
    if [ -f $FRONTEND_PID_FILE ]; then
        pid=$(cat $FRONTEND_PID_FILE)
        if check_process $pid; then
            echo -e "${RED}Frontend service is already running (PID: $pid)${NC}"
            return 1
        else
            # If PID file exists but process doesn't, delete old PID file
            rm $FRONTEND_PID_FILE
        fi
    fi

    # Add start time information at the beginning of the log file
    echo "===== Frontend service started at $(date) =====" > $FRONTEND_LOG
    
    # Enter frontend directory and start service
    cd $FRONTEND_DIR

    # Check if dependencies are installed
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing frontend dependencies...${NC}" | tee -a ../../$FRONTEND_LOG
        npm install >> ../../$FRONTEND_LOG 2>&1
    fi

    # Get absolute path for frontend log
    FRONTEND_LOG_ABSOLUTE=$(realpath ../../$FRONTEND_LOG)

    # Start frontend service
    npm start >> ../../$FRONTEND_LOG 2>&1 &
    frontend_pid=$!
    cd ../../
    echo $frontend_pid > $FRONTEND_PID_FILE
    
    # Create symbolic link to current log - use absolute path for reliability
    rm -f $FRONTEND_CURRENT_LOG
    ln -sf $FRONTEND_LOG_ABSOLUTE $FRONTEND_CURRENT_LOG
    
    # Record log file path next to PID file, so other commands can find it
    echo $FRONTEND_LOG_ABSOLUTE > "${FRONTEND_PID_FILE}.log"

    # Wait a moment to confirm the process is still running
    sleep 3
    if check_process $frontend_pid; then
        echo -e "${GREEN}Frontend service started (PID: $frontend_pid)${NC}"
        echo -e "${BLUE}Frontend access address: http://localhost:5173${NC}"
        echo -e "${GREEN}Log file: $FRONTEND_LOG${NC}"
        echo -e "${GREEN}Current log link: $FRONTEND_CURRENT_LOG${NC}"
        return 0
    else
        echo -e "${RED}Frontend service failed to start, please check the log: $FRONTEND_LOG${NC}"
        return 1
    fi
}

# Stop service
stop_service() {
    service_name=$1
    pid_file=$2

    if [ -f $pid_file ]; then
        pid=$(cat $pid_file)
        echo -e "${YELLOW}Stopping ${service_name} service (PID: $pid)...${NC}"

        if check_process $pid; then
            kill $pid
            sleep 2

            # Check if successfully stopped
            if check_process $pid; then
                echo -e "${RED}${service_name} service did not stop normally, trying to force terminate...${NC}"
                kill -9 $pid
                sleep 1
            fi

            if check_process $pid; then
                echo -e "${RED}Unable to stop ${service_name} service, please manually terminate process $pid${NC}"
                return 1
            else
                echo -e "${GREEN}${service_name} service stopped${NC}"
            fi
        else
            echo -e "${YELLOW}${service_name} service is not running${NC}"
        fi

        rm $pid_file
        # Delete log file path record but keep log file itself
        if [ -f "${pid_file}.log" ]; then
            rm "${pid_file}.log"
        fi
    else
        echo -e "${YELLOW}${service_name} service is not running${NC}"
    fi

    return 0
}

# Display logs
show_logs() {
    # Check backend log
    if [ -f $BACKEND_CURRENT_LOG ] && [ -r $BACKEND_CURRENT_LOG ]; then
        echo -e "${GREEN}=== Backend log (latest) ===${NC}"
        tail -n 20 $BACKEND_CURRENT_LOG
        echo -e "${GREEN}View full log: less $BACKEND_CURRENT_LOG${NC}"
    else
        # Try to find the latest backend log
        LATEST_BACKEND_LOG=$(ls -t $BACKEND_LOG_DIR/backend_*.log 2>/dev/null | head -1)
        if [ ! -z "$LATEST_BACKEND_LOG" ] && [ -f "$LATEST_BACKEND_LOG" ]; then
            echo -e "${GREEN}=== Backend log (latest from $BACKEND_LOG_DIR) ===${NC}"
            tail -n 20 "$LATEST_BACKEND_LOG"
            echo -e "${GREEN}View full log: less $LATEST_BACKEND_LOG${NC}"
            
            # Attempt to fix the symbolic link
            echo -e "${YELLOW}Fixing backend log symbolic link...${NC}"
            rm -f $BACKEND_CURRENT_LOG
            ln -sf "$LATEST_BACKEND_LOG" $BACKEND_CURRENT_LOG
            echo -e "${GREEN}Symbolic link fixed. Next time you can use './run.sh logs' normally.${NC}"
        else
            echo -e "${YELLOW}Backend log does not exist or cannot be found${NC}"
        fi
    fi
    
    echo ""
    
    # Check frontend log
    if [ -f $FRONTEND_CURRENT_LOG ] && [ -r $FRONTEND_CURRENT_LOG ]; then
        echo -e "${GREEN}=== Frontend log (latest) ===${NC}"
        tail -n 20 $FRONTEND_CURRENT_LOG
        echo -e "${GREEN}View full log: less $FRONTEND_CURRENT_LOG${NC}"
    else
        # Try to find the latest frontend log
        LATEST_FRONTEND_LOG=$(ls -t $FRONTEND_LOG_DIR/frontend_*.log 2>/dev/null | head -1)
        if [ ! -z "$LATEST_FRONTEND_LOG" ] && [ -f "$LATEST_FRONTEND_LOG" ]; then
            echo -e "${GREEN}=== Frontend log (latest from $FRONTEND_LOG_DIR) ===${NC}"
            tail -n 20 "$LATEST_FRONTEND_LOG"
            echo -e "${GREEN}View full log: less $LATEST_FRONTEND_LOG${NC}"
            
            # Attempt to fix the symbolic link
            echo -e "${YELLOW}Fixing frontend log symbolic link...${NC}"
            rm -f $FRONTEND_CURRENT_LOG
            ln -sf "$LATEST_FRONTEND_LOG" $FRONTEND_CURRENT_LOG
            echo -e "${GREEN}Symbolic link fixed. Next time you can use './run.sh logs' normally.${NC}"
        else
            echo -e "${YELLOW}Frontend log does not exist or cannot be found${NC}"
        fi
    fi
}

# Start all services
start_all() {
    echo -e "${BLUE}=== Starting all services ===${NC}"
    start_backend
    backend_status=$?
    start_frontend
    frontend_status=$?

    echo ""
    if [ $backend_status -eq 0 ] && [ $frontend_status -eq 0 ]; then
        echo -e "${GREEN}All services started successfully${NC}"
        return 0
    else
        echo -e "${RED}One or more services failed to start${NC}"
        return 1
    fi
}

# Stop all services
stop_all() {
    echo -e "${BLUE}=== Stopping all services ===${NC}"
    echo -e "${YELLOW}Stopping frontend service first...${NC}"
    stop_service "frontend" $FRONTEND_PID_FILE

    echo -e "${YELLOW}Then stopping backend service...${NC}"
    stop_service "backend" $BACKEND_PID_FILE

    echo ""
    echo -e "${GREEN}All services stopped${NC}"
}

# Restart all services
restart_all() {
    echo -e "${BLUE}=== Restarting all services ===${NC}"
    stop_all
    echo ""
    start_all
}

# Restart frontend service
restart_frontend() {
    echo -e "${BLUE}=== Restarting frontend service ===${NC}"
    stop_service "frontend" $FRONTEND_PID_FILE
    echo ""
    start_frontend
}

# Restart backend service
restart_backend() {
    echo -e "${BLUE}=== Restarting backend service ===${NC}"
    stop_service "backend" $BACKEND_PID_FILE
    echo ""
    start_backend
}

# Show service status
show_status() {
    echo -e "${BLUE}=== Service status ===${NC}"

    # Check backend status
    if [ -f $BACKEND_PID_FILE ]; then
        backend_pid=$(cat $BACKEND_PID_FILE)
        if check_process $backend_pid; then
            echo -e "${GREEN}Backend service: running (PID: $backend_pid)${NC}"
            # If there is a log file record, display log path
            if [ -f "${BACKEND_PID_FILE}.log" ]; then
                backend_log=$(cat "${BACKEND_PID_FILE}.log")
                echo -e "${GREEN}Backend log: $backend_log${NC}"
            fi
        else
            echo -e "${RED}Backend service: process does not exist, but PID file exists${NC}"
        fi
    else
        echo -e "${YELLOW}Backend service: not running${NC}"
    fi

    # Check frontend status
    if [ -f $FRONTEND_PID_FILE ]; then
        frontend_pid=$(cat $FRONTEND_PID_FILE)
        if check_process $frontend_pid; then
            echo -e "${GREEN}Frontend service: running (PID: $frontend_pid)${NC}"
            echo -e "${BLUE}Frontend access address: http://localhost:5173${NC}"
            # If there is a log file record, display log path
            if [ -f "${FRONTEND_PID_FILE}.log" ]; then
                frontend_log=$(cat "${FRONTEND_PID_FILE}.log")
                echo -e "${GREEN}Frontend log: $frontend_log${NC}"
            fi
        else
            echo -e "${RED}Frontend service: process does not exist, but PID file exists${NC}"
        fi
    else
        echo -e "${YELLOW}Frontend service: not running${NC}"
    fi
}

# Main logic
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
        stop_service "frontend" $FRONTEND_PID_FILE
        ;;
    stop-backend)
        stop_service "backend" $BACKEND_PID_FILE
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