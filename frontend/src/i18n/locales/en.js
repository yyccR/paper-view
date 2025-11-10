export default {
  common: {
    search: 'Search',
    upload: 'Upload',
    login: 'Login',
    close: 'Close',
    delete: 'Delete',
    loading: 'Loading...',
    confirm: 'Confirm',
    cancel: 'Cancel',
    back: 'Back',
    viewMore: 'View More',
    total: 'Total',
    items: 'items',
    pages: 'pages',
    locale: 'en-US'
  },
  
  header: {
    features: 'Features',
    about: 'About',
    login: 'Login'
  },
  
  hero: {
    title: 'Paper View',
    searchPlaceholder: 'Enter PDF link or search papers',
    uploadTitle: 'Upload PDF',
    processing: 'Processing...'
  },
  
  features: {
    sectionTitle: 'Core Features',
    arxiv: {
      title: 'arXiv Papers Support',
      description: 'Support full arXiv taxonomy\nCovering 2.8M+ paper resources'
    },
    visualization: {
      title: 'Paper View',
      description: 'Provide 50+ chart visualizations\nMulti-dimensional data display'
    },
    realtime: {
      title: 'Real-time Updates',
      description: 'Daily collection of latest papers\nKeep database synchronized'
    }
  },
  
  footer: {
    description: 'arXiv-based paper search platform\nProviding intelligent visualization services',
    functionsTitle: 'Features',
    arxivSupport: 'arXiv Support',
    paperVisualization: 'Visualization',
    realtimeUpdate: 'Real-time Update',
    supportTitle: 'Support',
    helpCenter: 'Help Center',
    apiDocs: 'API Docs',
    contactUs: 'Contact Us',
    copyright: '© 2025 Paper View. All rights reserved.'
  },
  
  workspace: {
    searchPlaceholder: 'Enter PDF link or search papers',
    uploadPdf: 'Upload PDF',
    
    // Welcome page
    welcome: {
      title: 'Start Your Paper Analysis Journey',
      subtitle: 'Upload PDF files, enter links, or search paper keywords'
    },
    
    // Search results
    searchResults: {
      title: 'Search Results',
      year: '📅 {year}',
      citations: '📊 Citations: {count}',
      images: '🖼️ {count} images'
    },
    
    // Pagination
    pagination: {
      showing: 'Showing',
      of: '/',
      total: 'Total {total} items',
      first: 'First',
      previous: 'Previous',
      next: 'Next',
      last: 'Last'
    },
    
    // Notification panel
    notification: {
      title: 'Notifications',
      chatHistory: 'Chat History',
      analysisComplete: 'Paper analysis completed',
      minutesAgo: '{count} minutes ago',
      noSessions: 'No chat sessions',
      messageCount: '{count} messages',
      deleteSession: 'Delete session',
      confirmDelete: 'Are you sure you want to delete this session?',
      deleteFailed: 'Failed to delete, please try again',
      sessionType: {
        translate: 'Translation',
        chat: 'Chat'
      },
      time: {
        justNow: 'Just now',
        minutesAgo: '{count} minutes ago',
        hoursAgo: '{count} hours ago',
        daysAgo: '{count} days ago'
      }
    },
    
    // User panel
    user: {
      guestUser: 'Guest User',
      notLoggedIn: 'Not logged in',
      profile: 'Profile',
      settings: 'Settings',
      login: 'Login'
    },
    
    // Visualization templates
    templates: {
      title: 'Visualization Templates',
      '3d_bar': '3D Bar Chart',
      'Plot_group_vertical_3d_barplots': 'Grouped 3D Bar Chart',
      'area_chart': 'Area Chart',
      'bar': 'Bar Chart',
      'basic_3d_pie_plot': '3D Pie Chart',
      'basic_GO_term_bp_cc_mf_bar_plot': 'GO Term Enrichment',
      'basic_dual_y_axis_horizontal_bar_plot': 'Dual Y-axis Bar Chart',
      'basic_ggpubr_box_plot': 'Box Plot',
      'basic_ggviolin_plot': 'Violin Plot',
      'basic_histogram_with_without_fit': 'Fitted Histogram',
      'basic_horizontal_bar': 'Horizontal Bar Chart',
      'basic_kaplan_meier_survival_curve_plot': 'Survival Curve',
      'basic_left_right_bar_plot': 'Comparison Bar Chart',
      'basic_ridgeline_plot': 'Ridgeline Plot',
      'basic_scatter_plot_with_fc_lines': 'Line Scatter Plot',
      'basic_upsetR_plot': 'UpSet Plot',
      'basic_vertical_lollipop_chart': 'Lollipop Chart',
      'connected_paper': 'Connected Papers Graph',
      'funnel': 'Funnel Chart',
      'h_bar': 'Horizontal Bar',
      'heatmap': 'Heatmap',
      'matrix_mbti': 'MBTI Matrix',
      'matrix_sparkline': 'Matrix Sparkline',
      'node_align': 'Node Alignment',
      'paper_map': 'Paper Map',
      'pie': 'Pie Chart',
      'plot_basic_m6a_exp_scatter_plot': 'm6A Expression Scatter',
      'plot_basic_scatter_with_marginal_histograms_plot': 'Marginal Histogram Scatter',
      'scatter': 'Scatter Plot',
      'scatter2': 'Scatter Plot 2',
      'structure': 'Structure Diagram',
      'tree_radial': 'Radial Tree',
      'treemap_drip_down': 'Treemap',
      'wordcloud': 'Word Cloud',
      'citation_network': 'Citation Network',
      'density-network': 'Density Network',
      'research_cluster': 'Research Cluster',
      // Template descriptions
      descriptions: {
        '3d_bar': '3D visualization for paper data multi-dimensional analysis',
        'Plot_group_vertical_3d_barplots': 'Multiple experimental groups categorical comparison',
        'area_chart': 'Time-series trend analysis for experimental data',
        'bar': 'Treatment vs control group data comparison',
        'basic_3d_pie_plot': 'Research proportion distribution 3D visualization',
        'basic_GO_term_bp_cc_mf_bar_plot': 'Gene functional enrichment analysis visualization',
        'basic_dual_y_axis_horizontal_bar_plot': 'Dual-metric horizontal comparison analysis',
        'basic_ggpubr_box_plot': 'Statistical distribution analysis for experimental data',
        'basic_ggviolin_plot': 'Sample data probability density visualization',
        'basic_histogram_with_without_fit': 'Frequency distribution with fitting curves',
        'basic_horizontal_bar': 'Horizontal bar for long category labels',
        'basic_kaplan_meier_survival_curve_plot': 'Medical research survival curve and risk analysis',
        'basic_left_right_bar_plot': 'Mirror comparison for control vs treatment data',
        'basic_ridgeline_plot': 'Multi-group data distribution density ridgeline',
        'basic_scatter_plot_with_fc_lines': 'Scatter plot with fold-change trend lines',
        'basic_upsetR_plot': 'Multi-set intersection relationship visualization',
        'basic_vertical_lollipop_chart': 'Highlight key experimental data points',
        'connected_paper': 'Literature citation network graph visualization',
        'funnel': 'Research workflow stage conversion analysis',
        'h_bar': 'Simple horizontal bar for paper data comparison',
        'heatmap': 'Gene expression or correlation matrix heatmap',
        'matrix_mbti': 'Personality type data matrix distribution',
        'matrix_sparkline': 'Multi-dimensional trend matrix sparklines',
        'node_align': 'Research elements hierarchical node alignment',
        'paper_map': 'Literature topic clustering map visualization',
        'pie': 'Research sample or category proportion pie chart',
        'plot_basic_m6a_exp_scatter_plot': 'm6A modification site expression scatter plot',
        'plot_basic_scatter_with_marginal_histograms_plot': 'Scatter plot with marginal frequency histograms',
        'scatter': 'Variable correlation analysis scatter visualization',
        'scatter2': 'Experimental data 2D spatial distribution scatter',
        'structure': 'Paper structure or organizational hierarchy diagram',
        'tree_radial': 'Research taxonomy radial tree structure',
        'treemap_drip_down': 'Hierarchical data proportion treemap visualization',
        'wordcloud': 'Paper keyword frequency word cloud analysis',
        'citation_network': 'Academic literature citation relationship network visualization',
        'density-network': 'Literature distribution density heatmap network visualization',
        'research_cluster': 'cluster analysis for research hotspots visualization'
      }
    },
    
    // PDF preview
    pdf: {
      downloading: 'Downloading...',
      preparing: 'Preparing PDF preview...',
      backToPaper: 'Paper'
    },
    
    // Visualization
    visualization: {
      processing: 'Generating visualization...',
      loadFailed: 'Failed to load paper data, please check file path',
      noPdfLoaded: 'Please select a paper first',
      wordcloudFailed: 'Failed to generate word cloud, please try again',
      ridgelineTitle: 'Timeline Research Field Density Plot',
      resetView: 'Reset View',
      year: 'Year',
      density: 'Density',
      papers: 'Papers',
      yearAxis: 'Year',
      densityLegend: 'Density',
      field: 'Field',
      researchFields: 'Research Fields',
      artificialIntelligence: 'Artificial Intelligence',
      machineLearning: 'Machine Learning',
      deepLearning: 'Deep Learning',
      neuralNetworks: 'Neural Networks',
      naturalLanguageProcessing: 'Natural Language Processing',
      computerVision: 'Computer Vision',
      reinforcementLearning: 'Reinforcement Learning',
      knowledgeGraph: 'Knowledge Graph',
      dataMining: 'Data Mining',
      cloudComputing: 'Cloud Computing',
      blockChain: 'Blockchain',
      quantumComputing: 'Quantum Computing'
    }
  },
  
  wordcloud: {
    zoom: 'Zoom',
    zoomIn: 'Zoom In',
    zoomOut: 'Zoom Out',
    reset: 'Reset',
    frequency: 'Frequency',
    veryHigh: 'Very High',
    high: 'High',
    medium: 'Medium',
    low: 'Low',
    veryLow: 'Very Low'
  },
  
  densityViz: {
    kernelSize: 'Kernel Size',
    resolution: 'Resolution',
    resolutionHigh: 'High',
    resolutionMedium: 'Medium',
    resolutionLow: 'Low',
    showLabels: 'Show Labels',
    reset: 'Reset View',
    density: 'Density',
    low: 'Low',
    high: 'High',
    citations: 'Citations',
    avgCitations: 'Avg. Citations'
  },
  
  paperGraph: {
    // Paper list
    paperList: {
      title: 'Paper List',
      total: 'Total {count} papers'
    },
    
    // Paper details
    paperDetail: {
      title: 'Paper Details',
      titleLabel: 'Title',
      authorsLabel: 'Authors',
      yearLabel: 'Year',
      citationsLabel: 'Citations',
      abstractLabel: 'Abstract',
      viewFullPaper: 'View Full Paper',
      andOthers: 'et al.'
    },
    
    // Loading state
    loading: {
      generating: 'Generating relationship graph...'
    }
  },
  
  paperCard: {
    date: '📅 {date}',
    imageCount: '🖼️ {count} images'
  },
  
  paperModal: {
    deleteContent: 'Delete this content'
  },
  
  sidebar: {
    home: 'Home',
    space: 'Space',
    ai: 'AI',
    subscribe: 'Subscribe',
    notification: 'Notifications',
    my: 'My'
  },
  
  language: {
    zh: '中文',
    en: 'English'
  },
  
  aiConfig: {
    title: 'AI Model Selection',
    selectModel: 'Select AI Model',
    currentModel: 'Current Model',
    provider: 'Provider',
    modelName: 'Model Name',
    configure: 'Configure',
    apiKey: 'API Key',
    apiBase: 'API Base URL',
    save: 'Save',
    cancel: 'Cancel',
    saveSuccess: 'Saved Successfully',
    saveFailed: 'Save Failed',
    models: 'models',
    providers: {
      gpt: 'GPT',
      claude: 'Claude',
      qwen: 'Qwen',
      doubao: 'Doubao',
      gemini: 'Gemini',
      grok: 'Grok',
      deepseek: 'DeepSeek'
    },
    customModel: {
      title: 'Custom Model',
      subtitle: 'Add your own AI model',
      providerName: 'Provider Name',
      providerPlaceholder: 'e.g., OpenAI, Anthropic',
      modelName: 'Model Name',
      modelPlaceholder: 'e.g., gpt-4, claude-3',
      apiBase: 'API Base URL',
      apiBasePlaceholder: 'e.g., https://api.openai.com/v1',
      apiKey: 'API Key',
      apiKeyPlaceholder: 'Enter your API key',
      description: 'Description',
      descriptionPlaceholder: 'Brief description of this model',
      save: 'Save Config',
      reset: 'Reset',
      saveSuccess: 'Custom model saved successfully!',
      saveFailed: 'Save failed, please try again',
      validationError: 'Please fill in provider name and model name'
    }
  }
  ,
  // Selection toolbar
  selection: {
    translate: 'Translate',
    ask: 'Ask',
    copy: 'Copy',
    language: 'Language',
    lang: {
      zh: 'Chinese',
      en: 'English',
      ja: 'Japanese',
      ko: 'Korean',
      es: 'Spanish'
    }
  },
  
  // Translation chat panel
  translateChat: {
    title: 'Translation',
    chatTitle: 'AI Assistant',
    newChat: 'New Chat',
    inputPlaceholder: 'Type a message...',
    translating: 'Translating...',
    sending: 'Sending...'
  },
  
  // File preview
  filePreview: {
    download: 'Download',
    close: 'Close',
    loading: 'Loading...',
    rows: 'Rows',
    columns: 'Columns'
  }
}
