#!/bin/bash
# Gemini Vector Search API自动化测试运行脚本

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
NC='\033[0m' # 无颜色

# 确保脚本从项目根目录运行
cd "$(dirname "$0")/.." || exit 1
PROJ_ROOT=$(pwd)
echo "项目根目录: $PROJ_ROOT"

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}= Gemini Vector Search API 自动化测试 =${NC}"
echo -e "${BLUE}=======================================${NC}"

# 加载环境变量
ENV_FILE="$PROJ_ROOT/.env"
if [ -f "$ENV_FILE" ]; then
    echo -e "${BLUE}从.env文件加载环境变量${NC}"
    # 显示关键配置信息（不包含敏感数据）
    echo -e "${YELLOW}API配置信息:${NC}"
    grep -E "^(HOST|PORT|GOOGLE_CLOUD_PROJECT)" "$ENV_FILE" | sed 's/=/ = /'
    
    # 导出环境变量供测试使用
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    
    # 验证数据库连接信息
    echo -e "${YELLOW}数据库连接信息:${NC}"
    echo "数据库主机: $DB_HOST"
    echo "数据库端口: $DB_PORT"
    echo "数据库名称: $ALLOYDB_DATABASE"
else
    echo -e "${RED}未找到.env文件，使用默认配置${NC}"
    # 设置默认值
    export HOST="0.0.0.0"
    export PORT="8000"
fi

# 检查依赖
echo -e "\n${BLUE}检查环境依赖...${NC}"
# 尝试多种pip安装命令
if command -v pip &> /dev/null; then
    echo "使用pip安装依赖"
    pip install -q pytest requests pytest-html python-dotenv
elif command -v pip3 &> /dev/null; then
    echo "使用pip3安装依赖"
    pip3 install -q pytest requests pytest-html python-dotenv
elif command -v python -m pip &> /dev/null; then
    echo "使用python -m pip安装依赖"
    python -m pip install -q pytest requests pytest-html python-dotenv
elif command -v python3 -m pip &> /dev/null; then
    echo "使用python3 -m pip安装依赖"
    python3 -m pip install -q pytest requests pytest-html python-dotenv
else
    echo -e "${RED}未找到pip命令，请手动安装依赖${NC}"
    echo "需要安装: pytest requests pytest-html python-dotenv"
fi

# 确保API服务正在运行
echo -e "\n${BLUE}检查API服务状态...${NC}"
HOST=${HOST:-"0.0.0.0"}
PORT=${PORT:-"8000"}
API_URL="http://${HOST}:${PORT}/api/v1/health"
echo "测试API地址: $API_URL"

# 尝试访问API
if curl -s "$API_URL" > /dev/null; then
    echo -e "${GREEN}API服务正在运行${NC}"
else
    echo -e "${RED}无法连接到API服务，请确保服务已启动${NC}"
    echo "提示: 运行 'python -m app.main' 启动服务"
    exit 1
fi

# 显示Gemini API配置
echo -e "\n${BLUE}Gemini API配置信息:${NC}"
echo "Google Cloud项目: ${GOOGLE_CLOUD_PROJECT:-'未设置'}"
if [ -n "$GOOGLE_API_KEY" ]; then
    echo "API密钥: 已配置"
else
    echo -e "${RED}API密钥: 未配置${NC}"
fi

# 运行测试
echo -e "\n${BLUE}开始运行API测试...${NC}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_DIR="$PROJ_ROOT/tests/reports"
mkdir -p $REPORT_DIR

# 设置测试环境变量
export TEST_HOST="$HOST"
export TEST_PORT="$PORT"
export TEST_API_BASE_URL="http://${HOST}:${PORT}/api/v1"

# 运行完整测试并生成HTML报告
echo -e "${BLUE}执行测试命令: python -m pytest -xvs tests/test_api_complete.py${NC}"
python -m pytest -xvs "$PROJ_ROOT/tests/test_api_complete.py" --html="$REPORT_DIR/test_report_$TIMESTAMP.html"

# 检查测试结果
TEST_RESULT=$?
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "\n${GREEN}所有测试通过! 🎉${NC}"
    echo -e "测试报告: $REPORT_DIR/test_report_$TIMESTAMP.html"
else
    echo -e "\n${RED}测试失败，请查看上方错误信息${NC}"
    echo -e "详细报告: $REPORT_DIR/test_report_$TIMESTAMP.html"
fi

echo -e "\n${BLUE}=======================================${NC}"
echo -e "${BLUE}= 测试完成 (退出码: $TEST_RESULT) =${NC}"
echo -e "${BLUE}=======================================${NC}"

# 返回测试结果
exit $TEST_RESULT 