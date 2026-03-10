#!/usr/bin/env python3
"""
发布模块
RSS Feed 生成、Webhook 通知、文件管理
"""

import os
import sys
import json
import yaml
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/publisher.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class Publisher:
    def __init__(self, config_path: str = "./config/publish.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 配置
        self.rss_config = self.config.get('rss', {})
        self.storage = self.config.get('storage', {})
        self.webhook = self.config.get('webhook', {})
        
    def generate_rss(self, episodes: List[Dict]) -> str:
        """生成 RSS Feed"""
        rss_file = self.storage.get('rss_file', './output/rss.xml')
        rss_path = Path(rss_file)
        rss_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 构建 RSS XML
        rss = ET.Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:itunes', 'http://www.itunes.com/dtds/podcast-1.0.dtd')
        
        channel = ET.SubElement(rss, 'channel')
        
        # Channel 信息
        self._add_element(channel, 'title', self.rss_config.get('title', '龙虾博客'))
        self._add_element(channel, 'description', self.rss_config.get('description', ''))
        self._add_element(channel, 'language', self.rss_config.get('language', 'zh-CN'))
        self._add_element(channel, 'link', 'https://example.com')
        self._add_element(channel, 'itunes:author', self.rss_config.get('author', ''))
        self._add_element(channel, 'itunes:category', self.rss_config.get('category', 'Technology'))
        self._add_element(channel, 'itunes:explicit', self.rss_config.get('explicit', 'no'))
        
        # 封面
        cover = self.rss_config.get('cover_image', '')
        if cover:
            itunes_image = ET.SubElement(channel, 'itunes:image')
            itunes_image.set('href', cover)
        
        # Episodes
        for ep in episodes:
            item = ET.SubElement(channel, 'item')
            self._add_element(item, 'title', ep.get('title', ''))
            self._add_element(item, 'description', ep.get('description', ''))
            self._add_element(item, 'pubDate', ep.get('pubDate', ''))
            self._add_element(item, 'enclosure', '')
            item.find('enclosure').set('url', ep.get('url', ''))
            item.find('enclosure').set('type', 'audio/mpeg')
            item.find('enclosure').set('length', str(ep.get('length', 0)))
            self._add_element(item, 'guid', ep.get('guid', ''))
        
        # 保存
        tree = ET.ElementTree(rss)
        tree.write(rss_path, encoding='utf-8', xml_declaration=True)
        
        logger.info(f"RSS generated: {rss_path}")
        return str(rss_path)
    
    def _add_element(self, parent: ET.Element, tag: str, text: str = None):
        """添加子元素"""
        elem = ET.SubElement(parent, tag)
        if text:
            elem.text = text
        return elem
    
    def scan_episodes(self) -> List[Dict]:
        """扫描已有的 episodes"""
        output_dir = Path(self.storage.get('output_dir', './output/episodes'))
        if not output_dir.exists():
            return []
        
        episodes = []
        for ep_file in output_dir.glob("*.mp3"):
            stat = ep_file.stat()
            episodes.append({
                'title': ep_file.stem,
                'url': f"https://example.com/episodes/{ep_file.name}",
                'file': str(ep_file),
                'length': stat.st_size,
                'pubDate': datetime.fromtimestamp(stat.st_mtime).strftime('%a, %d %b %Y %H:%M:%S GMT'),
                'guid': f"episode-{ep_file.stem}",
                'description': f"第 {ep_file.stem} 期"
            })
        
        # 按日期排序
        episodes.sort(key=lambda x: x['pubDate'], reverse=True)
        
        # 限制数量
        max_ep = self.storage.get('max_episodes', 30)
        return episodes[:max_ep]
    
    def publish(self) -> str:
        """发布"""
        logger.info("Publishing...")
        
        # 扫描 episodes
        episodes = self.scan_episodes()
        logger.info(f"Found {len(episodes)} episodes")
        
        # 生成 RSS
        rss_path = self.generate_rss(episodes)
        
        # Webhook 通知
        if self.webhook.get('enabled') and self.webhook.get('url'):
            self._send_webhook('episode_published', {
                'episodes_count': len(episodes),
                'rss_url': rss_path
            })
        
        return rss_path
    
    def _send_webhook(self, event: str, data: dict):
        """发送 Webhook"""
        try:
            payload = {
                'event': event,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            response = requests.post(
                self.webhook['url'],
                json=payload,
                timeout=10
            )
            if response.status_code == 200:
                logger.info(f"Webhook sent: {event}")
            else:
                logger.warning(f"Webhook failed: {response.status_code}")
        except Exception as e:
            logger.error(f"Webhook error: {e}")
    
    def cleanup_old_episodes(self):
        """清理旧 episodes"""
        output_dir = Path(self.storage.get('output_dir', './output/episodes'))
        max_ep = self.storage.get('max_episodes', 30)
        
        if not output_dir.exists():
            return
        
        episodes = sorted(output_dir.glob("*.mp3"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        if len(episodes) > max_ep:
            for ep in episodes[max_ep:]:
                ep.unlink()
                logger.info(f"Deleted old episode: {ep.name}")


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Publisher')
    parser.add_argument('--episode', help='Publish specific episode')
    parser.add_argument('--cleanup', action='store_true', help='Cleanup old episodes')
    args = parser.parse_args()
    
    publisher = Publisher()
    
    if args.cleanup:
        publisher.cleanup_old_episodes()
    else:
        publisher.publish()


if __name__ == "__main__":
    main()
