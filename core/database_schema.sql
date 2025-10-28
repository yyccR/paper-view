-- ============================================================
-- Paper-View系统数据库表结构
-- 包含：ArXiv论文表、AI模型配置表等
-- 生成时间: 2025-10-28
-- ============================================================

-- 删除已存在的表（如果需要重建）
-- DROP TABLE IF EXISTS `core_arxivfetchlog`;
-- DROP TABLE IF EXISTS `core_arxivpaper`;

-- ============================================================
-- 表1: ArXiv论文表 (core_arxivpaper)
-- 存储从arXiv API获取的所有论文元数据
-- ============================================================
CREATE TABLE `arxiv_paper` (
    -- 主键
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    
    -- 基本标识信息
    `arxiv_id` VARCHAR(50) NOT NULL UNIQUE COMMENT 'arXiv标识符，如2301.12345',
    `version` INT NOT NULL DEFAULT 1 COMMENT '论文版本号',
    
    -- 基本信息
    `title` TEXT NOT NULL COMMENT '论文标题',
    `summary` TEXT NOT NULL COMMENT '论文摘要/简介',
    
    -- 作者信息
    `authors` JSON NOT NULL COMMENT '作者列表，格式: [{"name": "作者名", "affiliation": "机构"}]',
    
    -- 分类信息
    `primary_category` VARCHAR(50) NOT NULL COMMENT '主要arXiv分类，如cs.AI',
    `categories` JSON NOT NULL COMMENT '所有分类列表',
    
    -- 链接信息
    `arxiv_url` VARCHAR(500) NOT NULL COMMENT '论文的arXiv页面URL',
    `pdf_url` VARCHAR(500) NOT NULL COMMENT '论文PDF的下载URL',
    `doi` VARCHAR(200) NULL COMMENT 'DOI标识符',
    `doi_url` VARCHAR(500) NULL COMMENT 'DOI解析后的URL',
    
    -- 时间信息
    `published` DATETIME NOT NULL COMMENT '首次发布时间（v1版本的提交时间）',
    `updated` DATETIME NOT NULL COMMENT '更新时间（当前版本的提交时间）',
    
    -- 附加信息
    `comment` TEXT NULL COMMENT '作者添加的评论信息',
    `journal_ref` VARCHAR(500) NULL COMMENT '期刊引用信息',
    
    -- 本地管理字段
    `fetched_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '从API获取数据的时间',
    `is_processed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否已处理（如AI摘要生成）',
    `processing_status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '处理状态: pending/processing/completed/failed',
    `processing_error` TEXT NULL COMMENT '处理错误信息',
    
    -- 索引
    INDEX `idx_arxiv_id` (`arxiv_id`),
    INDEX `idx_primary_category` (`primary_category`),
    INDEX `idx_published` (`published` DESC),
    INDEX `idx_updated` (`updated` DESC),
    INDEX `idx_is_processed` (`is_processed`),
    INDEX `idx_category_published` (`primary_category`, `published` DESC),
    INDEX `idx_process_status` (`is_processed`, `processing_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ArXiv论文表';

-- ============================================================
-- 表2: ArXiv获取日志表 (core_arxivfetchlog)
-- 记录每次从arXiv API获取数据的情况
-- ============================================================
CREATE TABLE `arxiv_fetch_log` (
    -- 主键
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    
    -- 获取参数
    `category` VARCHAR(50) NOT NULL COMMENT '获取的arXiv分类，如cs.AI或cs.*',
    `start_date` DATE NULL COMMENT '查询的开始日期',
    `end_date` DATE NULL COMMENT '查询的结束日期',
    
    -- 结果统计
    `total_results` INT NOT NULL DEFAULT 0 COMMENT 'API返回的总结果数',
    `fetched_count` INT NOT NULL DEFAULT 0 COMMENT '实际获取并保存的论文数',
    `new_papers` INT NOT NULL DEFAULT 0 COMMENT '新增的论文数',
    `updated_papers` INT NOT NULL DEFAULT 0 COMMENT '更新的论文数',
    
    -- 执行状态
    `status` VARCHAR(20) NOT NULL DEFAULT 'running' COMMENT '状态: running/completed/failed',
    `error_message` TEXT NULL COMMENT '错误信息',
    
    -- 时间信息
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    `completed_at` DATETIME NULL COMMENT '完成时间',
    `duration_seconds` INT NULL COMMENT '耗时（秒）',
    
    -- 索引
    INDEX `idx_category` (`category`),
    INDEX `idx_started_at` (`started_at` DESC),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ArXiv获取日志表';

-- ============================================================
-- 表3: ArXiv论文参考文献表 (arxiv_paper_reference)
-- 存储从论文PDF中提取的参考文献信息
-- ============================================================
CREATE TABLE `arxiv_paper_reference` (
    -- 主键
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    
    -- 关联的论文
    `paper_id` INT NOT NULL COMMENT '关联的论文ID',
    
    -- 参考文献序号
    `reference_number` INT NOT NULL COMMENT '参考文献在原文中的序号',
    
    -- 参考文献基本信息
    `title` TEXT NULL COMMENT '参考文献的标题',
    `authors` JSON NULL COMMENT '作者姓名列表，格式: ["Author1", "Author2", ...]',
    `year` INT NULL COMMENT '发表年份',
    
    -- 出版信息
    `venue` VARCHAR(500) NULL COMMENT '发表场所（期刊、会议或其他出版场所）',
    `venue_type` VARCHAR(20) NULL COMMENT '场所类型: journal/conference/arxiv/book/thesis/tech_report/other',
    `volume` VARCHAR(50) NULL COMMENT '卷号',
    `issue` VARCHAR(50) NULL COMMENT '期号',
    `pages` VARCHAR(50) NULL COMMENT '页码范围',
    
    -- 标识符
    `doi` VARCHAR(200) NULL COMMENT 'DOI标识符',
    `arxiv_id` VARCHAR(50) NULL COMMENT 'arXiv ID（如果是arXiv论文）',
    `url` VARCHAR(500) NULL COMMENT '在线链接',
    
    -- 原始信息
    `raw_text` TEXT NOT NULL COMMENT '参考文献的原始文本（从PDF提取）',
    
    -- 元数据
    `extracted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '从PDF提取的时间',
    `extraction_method` VARCHAR(50) NOT NULL DEFAULT 'llm' COMMENT '提取方法（如llm、regex等）',
    `confidence_score` FLOAT NULL COMMENT '提取结果的置信度分数（0-1）',
    
    -- 外键约束
    FOREIGN KEY (`paper_id`) REFERENCES `arxiv_paper`(`id`) ON DELETE CASCADE,
    
    -- 唯一约束
    UNIQUE KEY `unique_paper_ref` (`paper_id`, `reference_number`),
    
    -- 索引
    INDEX `idx_paper_id` (`paper_id`),
    INDEX `idx_paper_refnum` (`paper_id`, `reference_number`),
    INDEX `idx_year` (`year`),
    INDEX `idx_doi` (`doi`),
    INDEX `idx_arxiv_id` (`arxiv_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ArXiv论文参考文献表';

-- ============================================================
-- 表4: ArXiv参考文献提取日志表 (arxiv_reference_extract_log)
-- 记录每次从论文PDF提取参考文献的处理情况
-- ============================================================
CREATE TABLE `arxiv_reference_extract_log` (
    -- 主键
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    
    -- 关联的论文
    `paper_id` INT NOT NULL COMMENT '处理的论文ID',
    
    -- 处理状态
    `status` VARCHAR(20) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/downloading/extracting/processing/completed/failed/skipped',
    
    -- 处理结果
    `reference_count` INT NOT NULL DEFAULT 0 COMMENT '成功提取的参考文献数量',
    `pdf_downloaded` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'PDF是否成功下载',
    `pdf_file_path` VARCHAR(500) NULL COMMENT '下载的PDF文件路径',
    `pdf_file_size` INT NULL COMMENT 'PDF文件大小（字节）',
    `text_extracted` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '文本是否成功提取',
    `reference_section_found` TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否找到参考文献部分',
    `reference_raw_text` MEDIUMTEXT NULL COMMENT '从PDF中提取的参考文献部分的原始文本',
    `reference_text_length` INT NULL COMMENT '参考文献原始文本的字符数',
    `llm_processed` TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'LLM是否成功处理',
    
    -- 错误信息
    `error_message` TEXT NULL COMMENT '处理失败时的错误信息',
    `error_type` VARCHAR(50) NULL COMMENT '错误类型（如download_error、extraction_error、llm_error等）',
    
    -- 处理详情
    `processing_details` JSON NULL COMMENT '处理过程中的详细信息（JSON格式）',
    
    `llm_response` MEDIUMTEXT NULL COMMENT 'LLM返回的原始响应内容（用于调试）',
    
    -- 时间信息
    `started_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    `completed_at` DATETIME NULL COMMENT '完成时间',
    `duration_seconds` INT NULL COMMENT '处理耗时（秒）',
    
    -- 重试信息
    `retry_count` INT NOT NULL DEFAULT 0 COMMENT '处理失败后的重试次数',
    
    -- 外键约束
    FOREIGN KEY (`paper_id`) REFERENCES `arxiv_paper`(`id`) ON DELETE CASCADE,
    
    -- 索引
    INDEX `idx_paper_id` (`paper_id`),
    INDEX `idx_paper_started` (`paper_id`, `started_at` DESC),
    INDEX `idx_status` (`status`),
    INDEX `idx_started_at` (`started_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='ArXiv参考文献提取日志表';

-- ============================================================
-- 示例查询语句
-- ============================================================

-- ========== ArXiv论文表查询 ==========
-- 查询最近发布的论文
-- SELECT * FROM arxiv_paper ORDER BY published DESC LIMIT 10;

-- 查询特定分类的论文
-- SELECT * FROM arxiv_paper WHERE primary_category = 'cs.AI' ORDER BY published DESC;

-- 查询待处理的论文
-- SELECT * FROM arxiv_paper WHERE is_processed = 0 AND processing_status = 'pending';

-- ========== ArXiv获取日志查询 ==========
-- 查询获取日志统计
-- SELECT category, COUNT(*) as fetch_count, SUM(new_papers) as total_new, SUM(updated_papers) as total_updated 
-- FROM arxiv_fetch_log WHERE status = 'completed' GROUP BY category;

-- 查看最近的获取记录
-- SELECT * FROM arxiv_fetch_log ORDER BY started_at DESC LIMIT 10;

-- ========== 参考文献表查询 ==========
-- 查询某篇论文的所有参考文献
-- SELECT * FROM arxiv_paper_reference WHERE paper_id = 1 ORDER BY reference_number;

-- 查询某篇论文的参考文献数量
-- SELECT p.arxiv_id, p.title, COUNT(r.id) as ref_count 
-- FROM arxiv_paper p 
-- LEFT JOIN arxiv_paper_reference r ON p.id = r.paper_id 
-- GROUP BY p.id ORDER BY ref_count DESC LIMIT 10;

-- 查询特定年份的参考文献
-- SELECT * FROM arxiv_paper_reference WHERE year = 2023 ORDER BY paper_id, reference_number;

-- 查询包含DOI的参考文献
-- SELECT * FROM arxiv_paper_reference WHERE doi IS NOT NULL LIMIT 10;

-- 查询arXiv预印本类型的参考文献
-- SELECT * FROM arxiv_paper_reference WHERE venue_type = 'arxiv' LIMIT 10;

-- 统计各类型参考文献的数量
-- SELECT venue_type, COUNT(*) as count FROM arxiv_paper_reference 
-- WHERE venue_type IS NOT NULL GROUP BY venue_type ORDER BY count DESC;

-- ========== 提取日志表查询 ==========
-- 查看提取进度
-- SELECT status, COUNT(*) as count FROM arxiv_reference_extract_log GROUP BY status;

-- 查看最近的提取记录
-- SELECT l.*, p.arxiv_id, p.title 
-- FROM arxiv_reference_extract_log l 
-- JOIN arxiv_paper p ON l.paper_id = p.id 
-- ORDER BY l.started_at DESC LIMIT 10;

-- 查看失败的提取记录
-- SELECT l.*, p.arxiv_id, p.title 
-- FROM arxiv_reference_extract_log l 
-- JOIN arxiv_paper p ON l.paper_id = p.id 
-- WHERE l.status = 'failed' 
-- ORDER BY l.started_at DESC;

-- 统计各类错误的数量
-- SELECT error_type, COUNT(*) as count 
-- FROM arxiv_reference_extract_log 
-- WHERE status = 'failed' AND error_type IS NOT NULL 
-- GROUP BY error_type ORDER BY count DESC;

-- 查看成功提取的统计信息
-- SELECT 
--     COUNT(*) as total_extractions,
--     SUM(reference_count) as total_references,
--     AVG(reference_count) as avg_refs_per_paper,
--     AVG(duration_seconds) as avg_duration_seconds
-- FROM arxiv_reference_extract_log WHERE status = 'completed';

-- 查看待处理和失败需要重试的论文
-- SELECT p.arxiv_id, p.title, COALESCE(l.status, 'not_started') as extract_status
-- FROM arxiv_paper p
-- LEFT JOIN arxiv_reference_extract_log l ON p.id = l.paper_id
-- WHERE l.status IS NULL OR l.status IN ('failed', 'pending')
-- ORDER BY p.published DESC LIMIT 20;

-- ============================================================
-- 表4: AI模型配置表 (ai_model_config)
-- 存储用户选择的AI模型配置信息
-- ============================================================
CREATE TABLE `ai_model_config` (
    -- 主键
    `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '自增主键',
    
    -- 用户标识（支持登录用户和匿名用户）
    `user_id` INT NULL COMMENT '用户ID，关联auth_user表，NULL表示匿名用户',
    `session_id` VARCHAR(255) NULL COMMENT '匿名用户会话ID',
    
    -- 模型配置
    `provider` VARCHAR(50) NOT NULL COMMENT 'AI模型提供商: gpt, claude, qwen, doubao, gemini',
    `model_name` VARCHAR(100) NOT NULL COMMENT '具体模型名称: gpt-4o, claude-3-5-sonnet等',
    
    -- API配置
    `api_key` VARCHAR(500) DEFAULT '' COMMENT 'API密钥（建议加密存储）',
    `api_base` VARCHAR(500) DEFAULT '' COMMENT 'API基础URL（可选）',
    
    -- 状态标识
    `is_active` TINYINT(1) NOT NULL DEFAULT 1 COMMENT '是否为当前激活的模型配置',
    
    -- 时间戳
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    -- 索引
    INDEX `idx_user_active` (`user_id`, `is_active`),
    INDEX `idx_session_active` (`session_id`, `is_active`),
    INDEX `idx_provider` (`provider`),
    
    -- 外键约束（如果使用Django的auth_user表）
    FOREIGN KEY (`user_id`) REFERENCES `auth_user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI模型配置表';

-- ============================================================
-- AI模型配置表 - 常用查询示例
-- ============================================================

-- 查看所有激活的配置
-- SELECT * FROM ai_model_config WHERE is_active = 1 ORDER BY updated_at DESC;

-- 查看某个用户的当前配置
-- SELECT * FROM ai_model_config WHERE user_id = ? AND is_active = 1 LIMIT 1;

-- 查看某个会话的当前配置
-- SELECT * FROM ai_model_config WHERE session_id = ? AND is_active = 1 LIMIT 1;

-- 统计各模型提供商的使用情况
-- SELECT provider, COUNT(*) as user_count 
-- FROM ai_model_config 
-- WHERE is_active = 1 
-- GROUP BY provider 
-- ORDER BY user_count DESC;

-- 统计具体模型的使用情况
-- SELECT provider, model_name, COUNT(*) as user_count 
-- FROM ai_model_config 
-- WHERE is_active = 1 
-- GROUP BY provider, model_name 
-- ORDER BY user_count DESC;
