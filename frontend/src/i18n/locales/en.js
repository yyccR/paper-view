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
    pages: 'pages'
  },
  
  header: {
    features: 'Features',
    about: 'About',
    login: 'Login'
  },
  
  hero: {
    title: 'Paper Visual Reading System',
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
      title: 'Paper Visualization',
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
      analysisComplete: 'Paper analysis completed',
      minutesAgo: '{count} minutes ago'
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
      'wordcloud': 'Word Cloud'
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
      wordcloudFailed: 'Failed to generate word cloud, please try again'
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
  }
}
