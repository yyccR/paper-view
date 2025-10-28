#!/bin/bash

# Paper View 启动脚本
# 用于快速启动 Django 后端和 Vue 前端开发服务器

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Paper View 启动脚本${NC}"
echo -e "${GREEN}========================================${NC}"

# 1. 检查 .env 文件
echo -e "\n${YELLOW}[1/4] 检查环境配置...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}错误: .env 文件不存在${NC}"
    echo -e "${YELLOW}提示: 请先运行安装脚本${NC}"
    echo -e "  ${GREEN}./install.sh${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 环境配置文件存在${NC}"

# 2. 激活 Conda 环境
echo -e "\n${YELLOW}[2/4] 激活 Conda 环境...${NC}"

# 检测 conda 安装路径
if [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="/opt/anaconda3"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="$HOME/anaconda3"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="$HOME/miniconda3"
elif [ -f "$HOME/opt/anaconda3/etc/profile.d/conda.sh" ]; then
    CONDA_PATH="$HOME/opt/anaconda3"
else
    echo -e "${RED}错误: 未找到 Conda 安装${NC}"
    echo -e "${YELLOW}请先安装 Anaconda 或 Miniconda${NC}"
    exit 1
fi

# 激活 conda
source "$CONDA_PATH/etc/profile.d/conda.sh"

# 检查 paper-view 环境是否存在
if ! conda env list | grep -q "^paper-view "; then
    echo -e "${RED}错误: paper-view 环境不存在${NC}"
    echo -e "${YELLOW}提示: 请先运行安装脚本${NC}"
    echo -e "  ${GREEN}./install.sh${NC}"
    exit 1
fi

conda activate paper-view
echo -e "${GREEN}✓ 已激活 paper-view 环境${NC}"
echo -e "${GREEN}  Python 版本: $(python --version)${NC}"

# 3. 检查数据库并执行迁移
echo -e "\n${YELLOW}[3/4] 检查数据库并执行迁移...${NC}"
if python manage.py check --database default 2>/dev/null; then
    echo -e "${GREEN}✓ 数据库连接正常${NC}"
else
    echo -e "${RED}警告: 数据库连接失败${NC}"
    echo -e "${YELLOW}请检查 .env 中的数据库配置${NC}"
    echo -e "${YELLOW}继续启动...${NC}"
fi

# 检查是否有未创建的迁移
echo -e "${YELLOW}检查模型变更...${NC}"
if python manage.py makemigrations --dry-run --noinput | grep -q "No changes detected"; then
    echo -e "${GREEN}✓ 无模型变更${NC}"
else
    echo -e "${YELLOW}检测到模型变更，创建迁移文件...${NC}"
    python manage.py makemigrations --noinput
    echo -e "${GREEN}✓ 迁移文件创建完成${NC}"
fi

# 执行数据库迁移
echo -e "${YELLOW}应用数据库迁移...${NC}"
python manage.py migrate --noinput
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 4. 启动开发服务器
echo -e "\n${YELLOW}[4/4] 启动开发服务器...${NC}"
echo -e "${GREEN}========================================${NC}"

# 检查是否传入了 dev 参数
if [ "$1" = "dev" ] || [ "$1" = "frontend" ] || [ "$1" = "vue" ]; then
    echo -e "${GREEN}启动模式: 前后端分离开发${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Django 后端: http://localhost:9520${NC}"
    echo -e "${GREEN}Vue 前端:   http://localhost:9521${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
    echo ""
    
    # 启动Django后端（后台运行）
    echo -e "${YELLOW}启动 Django 后端...${NC}"
    python manage.py runserver 0.0.0.0:9520 &
    DJANGO_PID=$!
    
    # 等待Django启动
    sleep 2
    
    # 检查Node.js和npm是否安装
    if ! command -v node &> /dev/null; then
        echo -e "${RED}错误: Node.js 未安装${NC}"
        echo -e "${YELLOW}请安装 Node.js: https://nodejs.org/${NC}"
        kill $DJANGO_PID
        exit 1
    fi
    
    # 进入前端目录
    cd frontend
    
    # 检查是否安装了依赖
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}检测到未安装前端依赖，正在安装...${NC}"
        npm install
    fi
    
    # 启动Vue前端
    echo -e "${YELLOW}启动 Vue 前端...${NC}"
    npm run dev
    
    # 清理：当前端停止时，也停止后端
    kill $DJANGO_PID 2>/dev/null || true
else
    # 生产模式或只启动Django
    PORT=${1:-9520}
    echo -e "${GREEN}启动模式: Django 单体应用${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}服务器地址:${NC}"
    echo -e "${GREEN}  http://127.0.0.1:$PORT${NC}"
    echo -e "${GREEN}  http://localhost:$PORT${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}提示: 使用 './start.sh dev' 启动前后端分离开发模式${NC}"
    echo -e "${YELLOW}按 Ctrl+C 停止服务器${NC}"
    echo ""
    
    python manage.py runserver 0.0.0.0:$PORT
fi
