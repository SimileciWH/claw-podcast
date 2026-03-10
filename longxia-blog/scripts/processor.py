#!/usr/bin/env python3
"""
内容处理模块
LLM 摘要、口语化改写
"""

import os
import sys
import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/processor.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self, draft_path: str = None, config_path: str = None):
        self.draft_path = draft_path or "./output/drafts"
        self.output_dir = Path("./output/drafts")
        
        # MiniMax API 配置
        self.minimax_api_key = os.environ.get("MINIMAX_API_KEY", "")
        self.minimax_base_url = "https://api.minimax.chat/v1/text/chatcompletion_v2"
        
    def load_draft(self) -> List[Dict]:
        """加载草稿"""
        draft_dir = Path(self.draft_path)
        if draft_dir.is_file():
            with open(draft_dir, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('articles', [])
        elif draft_dir.exists():
            # 找最新的草稿
            drafts = sorted(draft_dir.glob("draft_*.json"), reverse=True)
            if drafts:
                with open(drafts[0], 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('articles', [])
        logger.warning("No draft found!")
        return []
    
    def summarize_article(self, article: Dict) -> Dict:
        """LLM 摘要"""
        prompt = f"""请阅读以下文章，然后按要求处理:

文章标题: {article.get('title', '')}
文章来源: {article.get('source', '')}
文章内容: {article.get('summary', '')[:3000]}

请按以下格式输出:
1. 一句话总结这篇文章的主要内容
2. 提取 3 个关键字
3. 判断这篇文章是否值得做成播客 (yes/no)

输出格式:
SUMMARY: <一句话总结>
KEYWORDS: <关键字1>, <关键字2>, <关键字3>
WORTH_IT: <yes/no>
"""
        try:
            response = requests.post(
                self.minimax_base_url,
                headers={
                    "Authorization": f"Bearer {self.minimax_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "MiniMax-M2.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 500,
                    "temperature": 0.7
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return self._parse_llm_response(content, article)
            else:
                logger.error(f"LLM API Error: {response.status_code}")
                return {**article, 'summary_short': '', 'keywords': [], 'worth_it': 'unknown'}
        except Exception as e:
            logger.error(f"LLM Error: {e}")
            return {**article, 'summary_short': '', 'keywords': [], 'worth_it': 'unknown'}
    
    def _parse_llm_response(self, content: str, article: Dict) -> Dict:
        """解析 LLM 响应"""
        lines = content.split('\n')
        summary = ""
        keywords = []
        worth_it = "yes"
        
        for line in lines:
            if line.startswith('SUMMARY:'):
                summary = line.replace('SUMMARY:', '').strip()
            elif line.startswith('KEYWORDS:'):
                kw_text = line.replace('KEYWORDS:', '').strip()
                keywords = [k.strip() for k in kw_text.split(',') if k.strip()]
            elif line.startswith('WORTH_IT:'):
                worth_it = line.replace('WORTH_IT:', '').strip().lower()
        
        return {
            **article,
            'summary_short': summary,
            'keywords': keywords,
            'worth_it': worth_it
        }
    
    def convert_to_script(self, article: Dict) -> str:
        """口语化改写为播客稿件"""
        prompt = f"""请把以下文章改写成播客主播的口语化稿件:

原文标题: {article.get('title', '')}
原文摘要: {article.get('summary_short', article.get('summary', '')[:1000])}

要求:
- 使用自然的口语表达，像主播在说话
- 长度控制在 300-500 字
- 可以适当加入过渡词和感叹词
- 保持信息的准确性和完整性

播客稿件:"""

        try:
            response = requests.post(
                self.minimax_base_url,
                headers={
                    "Authorization": f"Bearer {self.minimax_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "MiniMax-M2.1",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.8
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                script = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                return script.strip()
            else:
                return f"今天来聊聊: {article.get('title', '这篇文章')}"
        except Exception as e:
            logger.error(f"Script conversion error: {e}")
            return f"今天来聊聊: {article.get('title', '这篇文章')}"
    
    def process(self) -> List[Dict]:
        """处理所有文章"""
        articles = self.load_draft()
        logger.info(f"Processing {len(articles)} articles...")
        
        processed = []
        for i, article in enumerate(articles):
            logger.info(f"[{i+1}/{len(articles)}] {article.get('title', '')[:50]}...")
            
            # 摘要
            summarized = self.summarize_article(article)
            
            # 口语化稿件
            if summarized.get('worth_it') == 'yes':
                script = self.convert_to_script(summarized)
                summarized['script'] = script
            else:
                summarized['script'] = None
                
            processed.append(summarized)
        
        return processed
    
    def save_scripts(self, processed: List[Dict]) -> List[str]:
        """保存稿件"""
        output_dir = Path("./output/scripts")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        saved = []
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        for i, article in enumerate(processed):
            if not article.get('script'):
                continue
                
            filename = f"script_{date_str}_{i+1:03d}.txt"
            filepath = output_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"# {article.get('title', '')}\n")
                f.write(f"# 来源: {article.get('source', '')}\n")
                f.write(f"# 关键字: {', '.join(article.get('keywords', []))}\n")
                f.write("\n---\n\n")
                f.write(article['script'])
            
            saved.append(str(filepath))
            logger.info(f"Saved: {filename}")
        
        return saved


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Content Processor')
    parser.add_argument('--input', help='Input draft file')
    parser.add_argument('--minimax-key', help='MiniMax API Key')
    args = parser.parse_args()
    
    if args.minimax_key:
        os.environ["MINIMAX_API_KEY"] = args.minimax_key
    
    processor = ContentProcessor(draft_path=args.input)
    processed = processor.process()
    saved = processor.save_scripts(processed)
    
    logger.info(f"Done! Saved {len(saved)} scripts")


if __name__ == "__main__":
    main()
