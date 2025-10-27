"""
ArXiv API客户端
用于从arXiv API获取论文元数据
"""
import time
import urllib.request
import urllib.parse
from datetime import datetime, date, timedelta
import time
from typing import List, Dict, Optional, Any
import xml.etree.ElementTree as ET
import urllib.parse
from loguru import logger
from django.utils import timezone as django_timezone


class ArxivAPIClient:
    """ArXiv API客户端
    
    提供从arXiv API获取论文元数据的功能
    不下载PDF文件，只获取元数据
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    # arXiv命名空间
    NAMESPACES = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom',
        'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'
    }
    
    def __init__(self, delay_seconds: float = 3.0):
        """初始化客户端
        
        Args:
            delay_seconds: 请求之间的延迟时间（秒），建议至少3秒
        """
        self.delay_seconds = delay_seconds
        self.last_request_time = 0
    
    def _wait_for_rate_limit(self):
        """等待以遵守速率限制"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.delay_seconds:
            wait_time = self.delay_seconds - time_since_last_request
            logger.debug(f"等待 {wait_time:.2f} 秒以遵守速率限制")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, params: Dict[str, Any]) -> str:
        """发送API请求
        
        Args:
            params: 请求参数字典
            
        Returns:
            str: XML响应内容
        """
        self._wait_for_rate_limit()
        
        # 构建URL
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"
        
        logger.debug(f"请求URL: {url}")
        
        try:
            with urllib.request.urlopen(url) as response:
                content = response.read().decode('utf-8')
                return content
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            raise
    
    def _parse_atom_feed(self, xml_content: str) -> Dict[str, Any]:
        """解析Atom feed XML
        
        Args:
            xml_content: XML内容
            
        Returns:
            Dict: 包含总数和条目列表的字典
        """
        root = ET.fromstring(xml_content)
        
        # 获取总结果数
        total_results_elem = root.find('opensearch:totalResults', self.NAMESPACES)
        total_results = int(total_results_elem.text) if total_results_elem is not None else 0
        
        # 解析所有条目
        entries = []
        for entry in root.findall('atom:entry', self.NAMESPACES):
            parsed_entry = self._parse_entry(entry)
            if parsed_entry:
                entries.append(parsed_entry)
        
        return {
            'total_results': total_results,
            'entries': entries
        }
    
    def _parse_entry(self, entry: ET.Element) -> Optional[Dict[str, Any]]:
        """解析单个论文条目
        
        Args:
            entry: XML条目元素
            
        Returns:
            Dict: 论文元数据字典
        """
        try:
            # 基本信息
            id_elem = entry.find('atom:id', self.NAMESPACES)
            arxiv_url = id_elem.text if id_elem is not None else None
            
            # 从URL提取arXiv ID
            if arxiv_url:
                arxiv_id = arxiv_url.replace('http://arxiv.org/abs/', '')
            else:
                logger.warning("条目缺少ID，跳过")
                return None
            
            title_elem = entry.find('atom:title', self.NAMESPACES)
            title = title_elem.text.strip() if title_elem is not None else ''
            
            summary_elem = entry.find('atom:summary', self.NAMESPACES)
            summary = summary_elem.text.strip() if summary_elem is not None else ''
            
            # 时间信息
            published_elem = entry.find('atom:published', self.NAMESPACES)
            published = self._parse_datetime(published_elem.text) if published_elem is not None else None
            
            updated_elem = entry.find('atom:updated', self.NAMESPACES)
            updated = self._parse_datetime(updated_elem.text) if updated_elem is not None else None
            
            # 作者信息
            authors = []
            for author_elem in entry.findall('atom:author', self.NAMESPACES):
                name_elem = author_elem.find('atom:name', self.NAMESPACES)
                affiliation_elem = author_elem.find('arxiv:affiliation', self.NAMESPACES)
                
                author_info = {
                    'name': name_elem.text.strip() if name_elem is not None else '',
                    'affiliation': affiliation_elem.text.strip() if affiliation_elem is not None else ''
                }
                authors.append(author_info)
            
            # 分类信息
            primary_category_elem = entry.find('arxiv:primary_category', self.NAMESPACES)
            primary_category = primary_category_elem.get('term') if primary_category_elem is not None else ''
            
            categories = []
            for category_elem in entry.findall('atom:category', self.NAMESPACES):
                term = category_elem.get('term')
                if term:
                    categories.append(term)
            
            # 链接信息
            pdf_url = None
            doi_url = None
            
            for link_elem in entry.findall('atom:link', self.NAMESPACES):
                title_attr = link_elem.get('title', '')
                rel_attr = link_elem.get('rel', '')
                href = link_elem.get('href', '')
                
                if title_attr == 'pdf' and rel_attr == 'related':
                    pdf_url = href
                elif title_attr == 'doi' and rel_attr == 'related':
                    doi_url = href
            
            # 附加信息
            comment_elem = entry.find('arxiv:comment', self.NAMESPACES)
            comment = comment_elem.text.strip() if comment_elem is not None else None
            
            journal_ref_elem = entry.find('arxiv:journal_ref', self.NAMESPACES)
            journal_ref = journal_ref_elem.text.strip() if journal_ref_elem is not None else None
            
            doi_elem = entry.find('arxiv:doi', self.NAMESPACES)
            doi = doi_elem.text.strip() if doi_elem is not None else None
            
            return {
                'arxiv_id': arxiv_id,
                'title': title,
                'summary': summary,
                'authors': authors,
                'primary_category': primary_category,
                'categories': categories,
                'arxiv_url': arxiv_url,
                'pdf_url': pdf_url,
                'doi': doi,
                'doi_url': doi_url,
                'published': published,
                'updated': updated,
                'comment': comment,
                'journal_ref': journal_ref,
            }
        
        except Exception as e:
            logger.error(f"解析条目失败: {e}")
            return None
    
    def _parse_datetime(self, datetime_str: str) -> datetime:
        """解析datetime字符串
        
        Args:
            datetime_str: ISO格式的datetime字符串
            
        Returns:
            datetime: Python datetime对象（带时区信息）
        """
        # arXiv返回的格式可能是:
        # - 2003-07-07T13:46:39Z (UTC时区)
        # - 2003-07-07T13:46:39-04:00 (带时区偏移)
        # 移除时区信息以简化解析
        
        # 处理Z时区标识符
        if datetime_str.endswith('Z'):
            datetime_str = datetime_str[:-1]
        # 处理带时区偏移的格式
        elif '+' in datetime_str or datetime_str.count('-') > 2:
            datetime_str = datetime_str[:19]
        
        # 解析为naive datetime
        naive_dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S')
        # 转换为带时区的datetime（假定为UTC）
        return django_timezone.make_aware(naive_dt, django_timezone.utc)
    
    def search_papers(
        self,
        search_query: str = None,
        id_list: List[str] = None,
        start: int = 0,
        max_results: int = 100,
        sort_by: str = 'submittedDate',
        sort_order: str = 'descending'
    ) -> Dict[str, Any]:
        """搜索论文
        
        Args:
            search_query: 搜索查询字符串，如 "cat:cs.AI"
            id_list: arXiv ID列表
            start: 起始索引（0-based）
            max_results: 最大结果数（建议不超过2000）
            sort_by: 排序方式 (relevance, lastUpdatedDate, submittedDate)
            sort_order: 排序顺序 (ascending, descending)
            
        Returns:
            Dict: 包含total_results和entries的字典
        """
        params = {
            'start': start,
            'max_results': min(max_results, 2000),  # 限制单次请求最多2000条
            'sortBy': sort_by,
            'sortOrder': sort_order,
        }
        
        if search_query:
            params['search_query'] = search_query
        
        if id_list:
            params['id_list'] = ','.join(id_list)
        
        xml_content = self._make_request(params)
        return self._parse_atom_feed(xml_content)
    
    def search_by_category(
        self,
        category: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        start: int = 0,
        max_results: int = 100
    ) -> Dict[str, Any]:
        """按分类搜索论文
        
        Args:
            category: arXiv分类，如 "cs.AI" 或 "cs.*"（所有CS分类）
            start_date: 开始日期（论文提交日期）
            end_date: 结束日期（论文提交日期）
            start: 起始索引
            max_results: 最大结果数
            
        Returns:
            Dict: 包含total_results和entries的字典
        """
        # 构建搜索查询
        search_query = f"cat:{category}"
        
        # 添加日期过滤
        if start_date or end_date:
            start_str = start_date.strftime('%Y%m%d0000') if start_date else '20070101000'
            end_str = end_date.strftime('%Y%m%d2359') if end_date else datetime.now().strftime('%Y%m%d2359')
            search_query += f" AND submittedDate:[{start_str} TO {end_str}]"
        
        return self.search_papers(
            search_query=search_query,
            start=start,
            max_results=max_results,
            sort_by='submittedDate',
            sort_order='descending'
        )
    
    def fetch_all_cs_papers(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        batch_size: int = 1000,
        max_total: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取所有CS领域论文
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            batch_size: 每批次获取的数量（最大2000）
            max_total: 最大总数（None表示不限制）
            
        Returns:
            List[Dict]: 所有论文的元数据列表
        """
        all_papers = []
        start_index = 0
        batch_size = min(batch_size, 2000)
        
        logger.info(f"开始获取CS领域论文，日期范围: {start_date} 到 {end_date}")
        
        while True:
            logger.info(f"正在获取第 {start_index} 到 {start_index + batch_size} 条记录...")
            
            try:
                result = self.search_by_category(
                    category='cs.*',
                    start_date=start_date,
                    end_date=end_date,
                    start=start_index,
                    max_results=batch_size
                )
                
                total_results = result['total_results']
                entries = result['entries']
                
                if not entries:
                    logger.info("没有更多记录")
                    break
                
                all_papers.extend(entries)
                logger.info(f"已获取 {len(all_papers)}/{total_results} 条记录")
                
                # 检查是否达到最大限制
                if max_total and len(all_papers) >= max_total:
                    logger.info(f"已达到最大限制 {max_total}")
                    all_papers = all_papers[:max_total]
                    break
                
                # 检查是否已获取所有数据
                if len(all_papers) >= total_results:
                    logger.info("已获取所有记录")
                    break
                
                start_index += batch_size
                
            except Exception as e:
                logger.error(f"获取数据失败: {e}")
                break
        
        logger.info(f"获取完成，共 {len(all_papers)} 条记录")
        return all_papers
    
    def fetch_latest_cs_papers(
        self,
        days: int = 1,
        batch_size: int = 1000
    ) -> List[Dict[str, Any]]:
        """获取最近N天的CS论文
        
        Args:
            days: 最近多少天
            batch_size: 每批次获取的数量
            
        Returns:
            List[Dict]: 论文元数据列表
        """
        from datetime import timedelta
        
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        return self.fetch_all_cs_papers(
            start_date=start_date,
            end_date=end_date,
            batch_size=batch_size
        )
