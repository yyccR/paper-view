/**
 * BibTeX 文件解析器
 */

/**
 * 解析 BibTeX 文件内容
 * @param {string} bibContent - BibTeX 文件内容
 * @returns {Array} 论文数据数组
 */
export function parseBibTeX(bibContent) {
  const papers = []
  
  // 匹配每个 @article 条目
  const entryRegex = /@article\{([^,]+),\s*([\s\S]*?)\n\}/gi
  let match
  
  while ((match = entryRegex.exec(bibContent)) !== null) {
    const id = match[1].trim()
    const content = match[2]
    
    const paper = {
      id,
      paperId: id,
      title: extractField(content, 'title'),
      authors: parseAuthors(extractField(content, 'author')),
      year: extractField(content, 'year'),
      abstract: extractField(content, 'abstract'),
      url: extractField(content, 'url'),
      citations: Math.floor(Math.random() * 100), // 模拟引用数
      references: [] // 后续处理引用关系
    }
    
    papers.push(paper)
  }
  
  return papers
}

/**
 * 提取字段值
 */
function extractField(content, fieldName) {
  const regex = new RegExp(`${fieldName}\\s*=\\s*\\{([^}]+)\\}`, 'i')
  const match = content.match(regex)
  return match ? match[1].trim() : ''
}

/**
 * 解析作者列表
 */
function parseAuthors(authorString) {
  if (!authorString) return []
  
  // 作者之间用 "and" 分隔
  const authors = authorString.split(' and ').map(author => {
    // 移除多余空格和换行
    return author.replace(/\s+/g, ' ').trim()
  })
  
  return authors.slice(0, 5) // 最多返回5个作者
}

/**
 * 将论文数据转换为 ConnectedPapers 格式
 * @param {Array} papers - 解析后的论文数组
 * @returns {Object} ConnectedPapers 需要的数据格式
 */
export function convertToConnectedPapersFormat(papers) {
  if (!papers || papers.length === 0) {
    console.error('没有论文数据')
    return { mainPaper: null, nodes: [], edges: [] }
  }
  
  console.log('开始转换论文数据，共', papers.length, '篇')
  
  // 为主论文（第一篇）构建引用关系图
  const mainPaper = papers[0]
  
  // 创建节点数组
  const nodes = papers.map((paper, index) => ({
    id: paper.id,
    paperId: paper.paperId,
    title: paper.title,
    authors: paper.authors,
    year: parseInt(paper.year) || 2024,
    citationCount: paper.citations,
    abstract: paper.abstract || '',
    url: paper.url || '',
    isMainPaper: index === 0,
    // ConnectedPapers 需要的位置信息（会被库重新计算）
    x: 0,
    y: 0
  }))
  
  console.log('创建了', nodes.length, '个节点')
  
  // 创建边（引用关系）- 模拟一个引用网络
  const edges = []
  
  // 主论文引用后面的一些论文
  for (let i = 1; i < Math.min(papers.length, 8); i++) {
    edges.push({
      source: mainPaper.id,
      target: papers[i].id
    })
  }
  
  // 其他论文之间的引用关系
  for (let i = 1; i < papers.length; i++) {
    const numConnections = Math.floor(Math.random() * 3)
    for (let j = 0; j < numConnections; j++) {
      const targetIndex = Math.floor(Math.random() * papers.length)
      if (targetIndex !== i) {
        edges.push({
          source: papers[i].id,
          target: papers[targetIndex].id
        })
      }
    }
  }
  
  return {
    mainPaper: nodes[0],
    nodes,
    edges
  }
}
