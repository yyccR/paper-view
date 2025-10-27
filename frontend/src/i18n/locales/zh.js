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
    pages: '页'
  },
  
  header: {
    features: '功能',
    about: '关于',
    login: '登录'
  },
  
  hero: {
    title: 'Paper Visual Reading System',
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
      analysisComplete: '论文分析完成',
      minutesAgo: '{count}分钟前'
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
      'wordcloud': '词云图'
    },
    
    // PDF预览
    pdf: {
      downloading: '下载中...',
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
  }
}
