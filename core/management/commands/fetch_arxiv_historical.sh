#!/bin/bash
################################################################################
# ArXiv历史数据批量抓取脚本
# 功能：抓取1991年至今所有CS领域论文元数据
# 作者：自动生成
# 日期：2025-10-16
################################################################################

set -e  # 遇到错误立即退出

# 配置项
START_YEAR=2000
END_YEAR=2025
CATEGORY="cs.*"
DELAY_BETWEEN_DAYS=3  # 每天之间的延迟（秒）
LOG_FILE="logs/arxiv_historical_fetch.log"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 创建日志目录
mkdir -p logs

# 记录日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 抓取单天数据
fetch_day() {
    local date=$1
    
    echo -e "${GREEN}========================================${NC}"
    log "开始抓取: ${date}"
    echo -e "${GREEN}========================================${NC}"
    
    # 执行抓取命令
    if python3 manage.py fetch_arxiv_papers \
        --start-date "$date" \
        --end-date "$date" \
        --category "$CATEGORY" \
        --batch-size 1000 \
        --delay 3.0; then
        
        echo -e "${GREEN}✅ 完成: ${date}${NC}"
        log "✅ 成功完成: ${date}"
        return 0
    else
        echo -e "${RED}❌ 失败: ${date}${NC}"
        log "❌ 抓取失败: ${date}"
        return 1
    fi
}

# 主函数
main() {
    local total_days=0
    local success_days=0
    local failed_days=0
    local start_time=$(date +%s)
    
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}ArXiv历史数据批量抓取（按天）${NC}"
    echo -e "${YELLOW}========================================${NC}"
    log "开始批量抓取 - 时间范围: ${START_YEAR} 到 ${END_YEAR}"
    log "分类: ${CATEGORY}"
    echo ""
    
    # 生成日期列表并遍历每一天
    local current_date="${START_YEAR}-01-01"
    local end_date="${END_YEAR}-$(date +%m-%d)"
    
    # 如果结束年份是未来年份，使用该年的12月31日
    if [ $END_YEAR -gt $(date +%Y) ]; then
        end_date="${END_YEAR}-12-31"
    fi
    
    # 使用 date 命令遍历每一天
    while [ "$current_date" != "$(date -j -v+1d -f "%Y-%m-%d" "$end_date" "+%Y-%m-%d" 2>/dev/null || date -d "$end_date + 1 day" "+%Y-%m-%d" 2>/dev/null)" ]; do
        total_days=$((total_days + 1))
        
        # 抓取该天数据
        if fetch_day "$current_date"; then
            success_days=$((success_days + 1))
        else
            failed_days=$((failed_days + 1))
            
            # 可选：失败后是否继续
            echo -e "${YELLOW}⚠️  是否继续？按Ctrl+C退出，或等待${DELAY_BETWEEN_DAYS}秒后自动继续...${NC}"
        fi
        
        # 计算下一天
        current_date=$(date -j -v+1d -f "%Y-%m-%d" "$current_date" "+%Y-%m-%d" 2>/dev/null || date -d "$current_date + 1 day" "+%Y-%m-%d" 2>/dev/null)
        
        # 检查是否已经超过结束日期
        if [[ "$current_date" > "$end_date" ]]; then
            break
        fi
        
        # 天之间延迟
        echo ""
        echo "休息 ${DELAY_BETWEEN_DAYS} 秒..."
        sleep $DELAY_BETWEEN_DAYS
    done
    
    # 统计信息
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}批量抓取完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    log "批量抓取完成"
    log "总天数: ${total_days}"
    log "成功: ${success_days}"
    log "失败: ${failed_days}"
    log "总耗时: ${hours}小时 ${minutes}分钟 ${seconds}秒"
    
    echo "📊 统计信息:"
    echo "   总天数: ${total_days}"
    echo "   成功: ${success_days}"
    echo "   失败: ${failed_days}"
    echo "   总耗时: ${hours}小时 ${minutes}分钟 ${seconds}秒"
    echo ""
    echo "📝 详细日志: ${LOG_FILE}"
}

# 捕获Ctrl+C信号
trap 'echo -e "\n${YELLOW}⚠️  用户中断，正在退出...${NC}"; log "用户中断"; exit 130' INT TERM

# 检查是否在项目根目录
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ 错误: 请在项目根目录下运行此脚本${NC}"
    echo "用法: cd /path/to/xhs_daliy && bash core/management/commands/fetch_arxiv_historical.sh"
    exit 1
fi

# 运行主函数
main

exit 0
