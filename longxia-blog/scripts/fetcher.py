#!/usr/bin/env python3
"""
新闻抓取模块
支持: RSS 订阅、URL 抓取、本地文件夹
"""

import os
import sys
import json
import yaml
import time
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import feedparser
import requests
from bs4 import BeautifulSoup

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/fetcher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NewsFetcher:
    def __init__(self, config_path: str = "./config/sources.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        self.output_dir = Path("./output/drafts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def fetch_rss(self) -> List[Dict]:
        """抓取 RSS 订阅源"""
        articles = []
        for source in self.config.get('rss', []):
            if not source.get('enabled', False):
                continue
            try:
                logger.info(f"Fetching RSS: {source['name']}")
                feed = feedparser.parse(source['url'])
                for entry in feed.entries[:10]:  # 每源取最新 10 条
                    article = {
                        'title': entry.get('title', ''),
                        'url': entry.get('link', ''),
                        'summary': entry.get('summary', ''),
                        'published': entry.get('published', ''),
                        'source': source['name'],
                        'type': 'rss'
                    }
                    articles.append(article)
                logger.info(f"  -> Got {len(feed.entries)} entries")
            except Exception as e:
                logger.error(f"  -> Error: {e}")
        return articles
    
    def fetch_urls(self) -> List[Dict]:
        """抓取指定 URL"""
        articles = []
        for source in self.config.get('urls', []):
            if not source.get('enabled', False):
                continue
            try:
                logger.info(f"Fetching URL: {source['name']}")
                resp = requests.get(source['url'], timeout=30)
                soup = BeautifulSoup(resp.text, 'html.parser')
                
                # 提取正文 (简单实现)
                text = soup.get_text(separator='\n', strip=True)[:2000]
                
                article = {
                    'title': source['name'],
                    'url': source['url'],
                    'summary': text,
                    'published': datetime.now().isoformat(),
                    'source': source['name'],
                    'type': 'url'
                }
                articles.append(article)
            except Exception as e:
                logger.error(f"  -> Error: {e}")
        return articles
    
    def fetch_local(self) -> List[Dict]:
        """读取本地文件夹"""
        articles = []
        for source in self.config.get('local', []):
            if not source.get('enabled', False):
                continue
            path = Path(source.get('path', './inputs'))
            if not path.exists():
                logger.warning(f"Path not exists: {path}")
                continue
                
            recursive = source.get('recursive', True)
            pattern = '**/*' if recursive else '*'
            
            for file_path in path.glob(pattern):
                if not file_path.is_file():
                    continue
                if file_path.name.startswith('.'):
                    continue
                    
                try:
                    # 根据扩展名选择解析方式
                    ext = file_path.suffix.lower()
                    content = self._read_file(file_path, ext)
                    
                    article = {
                        'title': file_path.stem,
                        'url': str(file_path),
                        'summary': content[:2000],
                        'published': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                        'source': f"local:{file_path.name}",
                        'type': 'local'
                    }
                    articles.append(article)
                    logger.info(f"  -> Read: {file_path.name}")
                except Exception as e:
                    logger.error(f"  -> Error reading {file_path}: {e}")
        return articles
    
    def _read_file(self, path: Path, ext: str) -> str:
        """根据扩展名读取文件"""
        # 基础文本格式
        text_formats = {'.txt', '.md', '.html', '.htm', '.xml', '.json', '.yaml', '.yml'}
        
        if ext in text_formats:
            return path.read_text(encoding='utf-8')
        elif ext == '.pdf':
            # PDF 需要额外库，这里简化处理
            return f"[PDF 文件: {path.name}]"
        elif ext == '.docx':
            return f"[Word 文件: {path.name}]"
        elif ext == '.epub':
            return f"[EPUB 文件: {path.name}]"
        else:
            # 默认尝试读取
            try:
                return path.read_text(encoding='utf-8')
            except:
                return f"[无法读取: {path.name}]"
    
    def save_draft(self, articles: List[Dict]) -> str:
        """保存草稿"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_file = self.output_dir / f"draft_{timestamp}.json"
        
        with open(draft_file, 'w', encoding='utf-8') as f:
            json.dump({
                'fetched_at': datetime.now().isoformat(),
                'articles': articles
            }, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Draft saved: {draft_file}")
        return str(draft_file)
    
    def run(self):
        """运行抓取"""
        logger.info("=" * 50)
        logger.info("News Fetcher Started")
        logger.info("=" * 50)
        
        all_articles = []
        all_articles.extend(self.fetch_rss())
        all_articles.extend(self.fetch_urls())
        all_articles.extend(self.fetch_local())
        
        logger.info(f"Total articles: {len(all_articles)}")
        
        if all_articles:
            draft_path = self.save_draft(all_articles)
            logger.info(f"Saved to: {draft_path}")
        else:
            logger.warning("No articles fetched!")
        
        return all_articles


def main():
    import argparse
    parser = argparse.ArgumentParser(description='News Fetcher')
    parser.add_argument('--source', choices=['rss', 'url', 'local', 'all'], default='all')
    parser.add_argument('--config', default='./config/sources.yaml')
    args = parser.parse_args()
    
    fetcher = NewsFetcher(args.config)
    fetcher.run()


if __name__ == "__main__":
    main()
