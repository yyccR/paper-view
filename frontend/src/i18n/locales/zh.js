export default {
  common: {
    search: '搜索',
    upload: '上传',
    login: '登录',
    close: '关闭',
    delete: '删除',
    loading: '加载中...',
    confirm: '确认',
    cancel: '取消',
    back: '返回',
    viewMore: '查看更多',
    total: '共',
    items: '条',
    pages: '页',
    locale: 'zh-CN'
  },
  
  header: {
    features: '功能',
    about: '关于',
    login: '登录'
  },
  
  hero: {
    title: 'Paper View',
    searchPlaceholder: '输入pdf链接或者直接搜索论文',
    uploadTitle: '上传PDF',
    processing: '处理中...'
  },
  
  features: {
    sectionTitle: '核心功能',
    arxiv: {
      title: 'arXiv论文支持',
      description: '支持arXiv全分类体系\n涵盖280W+论文资源'
    },
    visualization: {
      title: '论文可视化',
      description: '提供50+图表可视化\n多维展示数据与关系'
    },
    realtime: {
      title: '实时更新',
      description: '每日收录最新论文\n保持数据库实时同步'
    }
  },
  
  footer: {
    description: '基于arXiv的论文检索平台\n提供智能可视化分析服务',
    functionsTitle: '功能',
    arxivSupport: 'arXiv论文支持',
    paperVisualization: '论文可视化',
    realtimeUpdate: '实时更新',
    supportTitle: '支持',
    helpCenter: '帮助中心',
    apiDocs: 'API文档',
    contactUs: '联系我们',
    copyright: '© 2025 Paper View. All rights reserved.'
  },
  
  workspace: {
    searchPlaceholder: '输入pdf链接或者直接搜索论文',
    uploadPdf: '上传PDF',
    
    // 欢迎页
    welcome: {
      title: '开始你的论文分析之旅',
      subtitle: '上传PDF文件、输入链接或搜索论文关键词'
    },
    
    // 搜索结果
    searchResults: {
      title: '搜索结果',
      year: '📅 {year}',
      citations: '📊 引用: {count}',
      images: '🖼️ {count} 张图片'
    },
    
    // 分页
    pagination: {
      showing: '显示',
      of: '/',
      total: '共 {total} 条',
      first: '首页',
      previous: '上一页',
      next: '下一页',
      last: '尾页'
    },
    
    // 通知面板
    notification: {
      title: '通知',
      chatHistory: '对话历史',
      analysisComplete: '论文分析完成',
      minutesAgo: '{count}分钟前',
      noSessions: '暂无对话记录',
      messageCount: '{count} 条消息',
      deleteSession: '删除会话',
      confirmDelete: '确定要删除这个会话吗？',
      deleteFailed: '删除失败，请重试',
      sessionType: {
        translate: '翻译',
        chat: '对话'
      },
      time: {
        justNow: '刚刚',
        minutesAgo: '{count}分钟前',
        hoursAgo: '{count}小时前',
        daysAgo: '{count}天前'
      }
    },
    
    // 用户面板
    user: {
      guestUser: '访客用户',
      notLoggedIn: '未登录',
      profile: '个人资料',
      settings: '设置',
      login: '登录'
    },
    
    // 可视化模板
    templates: {
      title: '可视化模板',
      '3d_bar': '三维柱状图',
      'Plot_group_vertical_3d_barplots': '分组三维柱状图',
      'area_chart': '面积图',
      'bar': '柱状图',
      'basic_3d_pie_plot': '三维饼图',
      'basic_GO_term_bp_cc_mf_bar_plot': 'GO功能富集图',
      'basic_dual_y_axis_horizontal_bar_plot': '双Y轴横向柱状图',
      'basic_ggpubr_box_plot': '箱线图',
      'basic_ggviolin_plot': '小提琴图',
      'basic_histogram_with_without_fit': '拟合直方图',
      'basic_horizontal_bar': '基础横向柱状图',
      'basic_kaplan_meier_survival_curve_plot': '生存曲线图',
      'basic_left_right_bar_plot': '左右对比柱状图',
      'basic_ridgeline_plot': '山脊线图',
      'basic_scatter_plot_with_fc_lines': '折线散点图',
      'basic_upsetR_plot': 'UpSet图',
      'basic_vertical_lollipop_chart': '棒棒糖图',
      'connected_paper': '论文关系图',
      'funnel': '漏斗图',
      'h_bar': '横向柱状图',
      'heatmap': '热力图',
      'matrix_mbti': 'MBTI矩阵图',
      'matrix_sparkline': '矩阵迷你图',
      'node_align': '节点对齐图',
      'paper_map': '论文地图',
      'pie': '饼图',
      'plot_basic_m6a_exp_scatter_plot': 'm6A表达散点图',
      'plot_basic_scatter_with_marginal_histograms_plot': '边缘分布散点图',
      'scatter': '散点图',
      'scatter2': '散点图2',
      'structure': '结构图',
      'tree_radial': '径向树图',
      'treemap_drip_down': '矩形树图',
      'wordcloud': '词云图',
      'citation_network': '文献引用网络',
      'density-network': '密度网络图',
      'research_cluster': '研究聚类图',
      // 模板描述
      descriptions: {
        '3d_bar': '立体展示论文数据多维度对比分析',
        'Plot_group_vertical_3d_barplots': '多组实验数据分类对比可视化呈现',
        'area_chart': '论文实验数据时序变化趋势分析',
        'bar': '论文中实验组与对照组数据对比',
        'basic_3d_pie_plot': '研究占比分布立体可视化展示',
        'basic_GO_term_bp_cc_mf_bar_plot': '基因功能富集分析结果可视化',
        'basic_dual_y_axis_horizontal_bar_plot': '双指标数据对比分析横向展示',
        'basic_ggpubr_box_plot': '实验数据分布特征统计分析图',
        'basic_ggviolin_plot': '样本数据概率密度分布可视化',
        'basic_histogram_with_without_fit': '实验结果频数分布及拟合曲线',
        'basic_horizontal_bar': '长标签分类数据横向柱状对比',
        'basic_kaplan_meier_survival_curve_plot': '医学研究生存曲线与风险分析',
        'basic_left_right_bar_plot': '正负对照实验数据镜像对比',
        'basic_ridgeline_plot': '多组实验数据分布密度山脊图',
        'basic_scatter_plot_with_fc_lines': '实验数据散点图叠加变化趋势',
        'basic_upsetR_plot': '多集合数据交集关系可视化',
        'basic_vertical_lollipop_chart': '关键实验数据点突出展示对比',
        'connected_paper': '文献引用关系网络图谱可视化',
        'funnel': '研究流程各阶段转化率分析',
        'h_bar': '论文数据简洁横向柱状对比',
        'heatmap': '基因表达或相关性矩阵热力图',
        'matrix_mbti': '性格类型数据矩阵分布分析',
        'matrix_sparkline': '多维数据趋势矩阵式迷你图',
        'node_align': '研究要素层次关系节点对齐',
        'paper_map': '文献主题聚类地图分布可视化',
        'pie': '研究样本或类别占比饼图展示',
        'plot_basic_m6a_exp_scatter_plot': 'm6A修饰位点表达差异散点图',
        'scatter': '论文变量相关性分析散点可视化',
        'scatter2': '实验数据二维空间分布散点图',
        'structure': '论文结构或组织层次关系图谱',
        'tree_radial': '研究分类体系径向树状结构图',
        'treemap_drip_down': '层次数据占比矩形树图可视化',
        'wordcloud': '论文关键词与主题词云图可视化',
        'citation_network': '学术文献引用关系网络结构图',
        'density-network': '文献分布密度热力网络可视化',
        'research_cluster': '聚类图谱研究热点分析'
      }
    },
    
    // PDF预览
    pdf: {
      preparing: '准备预览PDF...',
      backToPaper: '论文'
    },
    
    // 可视化
    visualization: {
      processing: '正在生成可视化...',
      loadFailed: '加载论文数据失败，请检查文件路径',
      noPdfLoaded: '请先选择一篇论文',
      wordcloudFailed: '词云生成失败，请重试'
    }
  },
  
  wordcloud: {
    zoom: '缩放',
    zoomIn: '放大',
    zoomOut: '缩小',
    reset: '重置',
    frequency: '频率',
    veryHigh: '极高',
    high: '高',
    medium: '中',
    low: '低',
    veryLow: '极低'
  },
  
  densityViz: {
    kernelSize: '核大小',
    resolution: '分辨率',
    resolutionHigh: '高',
    resolutionMedium: '中',
    resolutionLow: '低',
    showLabels: '显示标签',
    reset: '重置视图',
    density: '密度',
    low: '低',
    high: '高',
    citations: '引用数',
    avgCitations: '平均引用数'
  },
  
  paperGraph: {
    // 论文列表
    paperList: {
      title: '论文列表',
      total: '共 {count} 篇'
    },
    
    // 论文详情
    paperDetail: {
      title: '论文详情',
      titleLabel: '标题',
      authorsLabel: '作者',
      yearLabel: '年份',
      citationsLabel: '引用数',
      abstractLabel: '摘要',
      viewFullPaper: '查看完整论文',
      andOthers: '等'
    },
    
    // 加载状态
    loading: {
      generating: '正在生成关系图...'
    }
  },
  
  paperCard: {
    date: '📅 {date}',
    imageCount: '🖼️ {count} 张图片'
  },
  
  paperModal: {
    deleteContent: '删除此内容'
  },
  
  sidebar: {
    home: '首页',
    space: '空间',
    ai: 'AI',
    subscribe: '订阅',
    notification: '通知',
    my: '我的'
  },
  
  language: {
    zh: '中文',
    en: 'English'
  },
  
  aiConfig: {
    title: 'AI模型选择',
    selectModel: '选择AI模型',
    currentModel: '当前模型',
    provider: '提供商',
    modelName: '模型名称',
    configure: '配置',
    apiKey: 'API Key',
    apiBase: 'API基础URL',
    save: '保存',
    cancel: '取消',
    saveSuccess: '保存成功',
    saveFailed: '保存失败',
    models: '个模型',
    providers: {
      gpt: 'GPT',
      claude: 'Claude',
      qwen: '通义千问',
      doubao: '豆包',
      gemini: 'Gemini',
      grok: 'Grok',
      deepseek: 'DeepSeek'
    },
    customModel: {
      title: '自定义模型',
      subtitle: '添加自己的AI模型',
      providerName: '提供商名称',
      providerPlaceholder: '例如: OpenAI, Anthropic',
      modelName: '模型名称',
      modelPlaceholder: '例如: gpt-4, claude-3',
      apiBase: 'API基础URL',
      apiBasePlaceholder: '例如: https://api.openai.com/v1',
      apiKey: 'API密钥',
      apiKeyPlaceholder: '输入您的API密钥',
      description: '模型描述',
      descriptionPlaceholder: '简要描述此模型的特点',
      save: '保存配置',
      reset: '重置',
      saveSuccess: '自定义模型保存成功！',
      saveFailed: '保存失败，请重试',
      validationError: '请填写提供商名称和模型名称'
    }
  }
  ,
  // 文本选择工具条
  selection: {
    translate: '翻译',
    ask: '提问',
    copy: '复制',
    language: '切换语言',
    lang: {
      zh: '中文',
      en: '英语',
      ja: '日语',
      ko: '韩语',
      es: '西班牙语'
    }
  },
  
  // 翻译聊天面板
  translateChat: {
    title: '翻译',
    chatTitle: 'AI助手',
    newChat: '新建对话',
    inputPlaceholder: '输入消息...',
    translating: '翻译中...',
    sending: '发送中...'
  },
  
  // 文件预览
  filePreview: {
    download: '下载',
    close: '关闭',
    loading: '加载中...',
    rows: '行',
    columns: '列'
  }
}
