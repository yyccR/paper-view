#!/bin/bash

# Paper View 一键安装脚本
# 自动完成环境配置、依赖安装和数据库初始化

set -e  # 遇到错误时退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   Paper View 一键安装脚本${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 步骤 1: 检查前提条件
echo -e "${YELLOW}[1/7] 检查前提条件...${NC}"

# 检查 Conda
if ! command -v conda &> /dev/null; then
    echo -e "${RED}✗ Conda 未安装${NC}"
    echo -e "${YELLOW}请安装 Anaconda 或 Miniconda:${NC}"
    echo -e "${YELLOW}  Anaconda: https://www.anaconda.com/download${NC}"
    echo -e "${YELLOW}  Miniconda: https://docs.conda.io/en/latest/miniconda.html${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Conda: $(conda --version)${NC}"

# 检查 MySQL
if ! command -v mysql &> /dev/null; then
    echo -e "${RED}✗ MySQL 未安装${NC}"
    echo -e "${YELLOW}请安装 MySQL 5.7+: https://dev.mysql.com/downloads/mysql/${NC}"
    exit 1
fi
echo -e "${GREEN}✓ MySQL 已安装${NC}"

# 步骤 2: 初始化 Conda 环境
echo -e "\n${YELLOW}[2/7] 初始化 Conda 环境...${NC}"

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
    echo -e "${RED}错误: 未找到 Conda 初始化脚本${NC}"
    exit 1
fi

# 激活 conda
source "$CONDA_PATH/etc/profile.d/conda.sh"
echo -e "${GREEN}✓ Conda 已初始化${NC}"

# 检查 paper-view 环境是否存在
echo -e "\n${YELLOW}检查 paper-view 环境...${NC}"
if conda env list | grep -q "^paper-view "; then
    echo -e "${YELLOW}⚠ paper-view 环境已存在${NC}"
    echo -e "${BLUE}是否删除并重新创建? (y/N):${NC}"
    read -r RECREATE
    if [[ "$RECREATE" =~ ^[Yy]$ ]]; then
        conda env remove -n paper-view -y
        echo -e "${GREEN}✓ 已删除旧环境${NC}"
        conda create -n paper-view python=3.10 -y
        echo -e "${GREEN}✓ paper-view 环境创建成功${NC}"
    else
        echo -e "${GREEN}✓ 使用现有环境${NC}"
    fi
else
    echo -e "${YELLOW}正在创建 paper-view 环境（Python 3.10）...${NC}"
    conda create -n paper-view python=3.10 -y
    echo -e "${GREEN}✓ paper-view 环境创建成功${NC}"
fi

# 激活环境
conda activate paper-view
echo -e "${GREEN}✓ 已激活 paper-view 环境${NC}"
echo -e "${GREEN}  Python 版本: $(python --version)${NC}"

# 步骤 3: 安装 Python 依赖
echo -e "\n${YELLOW}[3/7] 安装 Python 依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Python 依赖安装完成${NC}"

# 步骤 4: 配置环境变量
echo -e "\n${YELLOW}[4/7] 配置环境变量...${NC}"
if [ -f ".env" ]; then
    echo -e "${GREEN}✓ .env 文件已存在，跳过${NC}"
else
    cp .env.example .env
    echo -e "${GREEN}✓ 已创建 .env 文件${NC}"
    echo -e "${YELLOW}⚠ 请编辑 .env 文件，配置数据库和 API 密钥${NC}"
fi

# 步骤 5: 创建数据库
echo -e "\n${YELLOW}[5/7] 创建数据库...${NC}"
echo -e "${BLUE}请输入 MySQL root 密码（用于创建数据库）:${NC}"
read -s MYSQL_PASSWORD
echo ""

# 从 .env 读取数据库配置
DB_NAME=$(grep DB_NAME .env | cut -d '=' -f2)
DB_NAME=${DB_NAME:-paper_view}

mysql -u root -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS $DB_NAME CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ 数据库创建成功${NC}"
else
    echo -e "${YELLOW}⚠ 数据库可能已存在或创建失败，继续...${NC}"
fi

# 步骤 6: 执行数据库迁移
echo -e "\n${YELLOW}[6/7] 执行数据库迁移...${NC}"
python manage.py makemigrations
python manage.py migrate
echo -e "${GREEN}✓ 数据库迁移完成${NC}"

# 步骤 7: 安装前端依赖（可选）
echo -e "\n${YELLOW}[7/7] 安装前端依赖...${NC}"
if command -v npm &> /dev/null; then
    cd frontend
    if [ -d "node_modules" ]; then
        echo -e "${GREEN}✓ 前端依赖已存在，跳过${NC}"
    else
        npm install
        echo -e "${GREEN}✓ 前端依赖安装完成${NC}"
    fi
    cd ..
else
    echo -e "${YELLOW}⚠ Node.js 未安装，跳过前端依赖安装${NC}"
    echo -e "${YELLOW}  如需开发模式，请安装 Node.js: https://nodejs.org/${NC}"
fi
# 完成
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   ✓ 安装完成！${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "\n${BLUE}下一步操作：${NC}"
echo -e "1. 编辑 ${YELLOW}.env${NC} 文件，配置数据库和 API 密钥"
echo -e "2. 激活 Conda 环境："
echo -e "   ${GREEN}conda activate paper-view${NC}"
echo -e "3. 启动开发服务器："
echo -e "   ${GREEN}./start.sh dev${NC}       # 前后端分离模式（推荐）"
echo -e "   ${GREEN}./start.sh${NC}           # 仅后端模式"
echo ""
echo -e "${BLUE}访问地址：${NC}"
echo -e "  开发模式: ${GREEN}http://localhost:9521${NC}"
echo ""
