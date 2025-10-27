#!/bin/bash
################################################################################
# ArXiv历史数据抓取测试脚本
# 功能：抓取少量月份用于测试（2024年10月-2025年10月）
# 用于验证脚本是否正常工作
################################################################################

set -e

# 配置项（测试版本 - 仅抓取最近13个月）
START_YEAR=2024
START_MONTH=10
END_YEAR=2025
END_MONTH=10
CATEGORY="cs.*"
DELAY_BETWEEN_MONTHS=5  # 测试时缩短延迟
LOG_FILE="logs/arxiv_test_fetch.log"

# 颜色输出
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

get_last_day() {
    local year=$1
    local month=$2
    case $month in
        01|03|05|07|08|10|12) echo "31" ;;
        04|06|09|11) echo "30" ;;
        02)
            if [ $((year % 4)) -eq 0 ] && [ $((year % 100)) -ne 0 ] || [ $((year % 400)) -eq 0 ]; then
                echo "29"
            else
                echo "28"
            fi
            ;;
    esac
}

fetch_month() {
    local year=$1
    local month=$2
    local start_date="${year}-${month}-01"
    local last_day=$(get_last_day $year $month)
    local end_date="${year}-${month}-${last_day}"
    
    echo -e "${GREEN}========================================${NC}"
    log "抓取: ${start_date} 到 ${end_date}"
    echo -e "${GREEN}========================================${NC}"
    
    if python3 manage.py fetch_arxiv_papers \
        --start-date "$start_date" \
        --end-date "$end_date" \
        --category "$CATEGORY" \
        --batch-size 1000 \
        --delay 3.0; then
        echo -e "${GREEN}✅ 完成: ${start_date}${NC}"
        log "✅ 成功: ${start_date}"
        return 0
    else
        echo -e "${RED}❌ 失败: ${start_date}${NC}"
        log "❌ 失败: ${start_date}"
        return 1
    fi
}

main() {
    local total=0
    local success=0
    local start_time=$(date +%s)
    
    echo -e "${YELLOW}========================================${NC}"
    echo -e "${YELLOW}ArXiv测试抓取 (2024.10 - 2025.10)${NC}"
    echo -e "${YELLOW}========================================${NC}"
    log "开始测试抓取"
    
    # 抓取2024年10-12月
    for month_num in $(seq $START_MONTH 12); do
        month=$(printf "%02d" $month_num)
        total=$((total + 1))
        fetch_month "2024" "$month" && success=$((success + 1))
        sleep $DELAY_BETWEEN_MONTHS
    done
    
    # 抓取2025年1月到当前月
    for month_num in $(seq 1 $END_MONTH); do
        month=$(printf "%02d" $month_num)
        total=$((total + 1))
        fetch_month "2025" "$month" && success=$((success + 1))
        [ $month_num -lt $END_MONTH ] && sleep $DELAY_BETWEEN_MONTHS
    done
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    local minutes=$((duration / 60))
    local seconds=$((duration % 60))
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}测试完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo "📊 统计: 总${total}个月, 成功${success}个, 耗时${minutes}分${seconds}秒"
    log "测试完成: 总${total}, 成功${success}, 耗时${minutes}分${seconds}秒"
}

trap 'echo -e "\n${YELLOW}⚠️  中断${NC}"; exit 130' INT TERM

if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ 请在项目根目录运行${NC}"
    exit 1
fi

main
exit 0
