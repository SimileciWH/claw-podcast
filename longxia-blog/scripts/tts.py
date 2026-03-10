#!/usr/bin/env python3
"""
TTS 生成模块
使用 edge-tts (免费微软 TTS)
"""

import os
import sys
import asyncio
import logging
import yaml
from datetime import datetime
from pathlib import Path
from typing import Optional
import edge_tts

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/tts.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TTSGenerator:
    def __init__(self, config_path: str = "./config/voices.yaml"):
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = {}
        
        # edge-tts 声音列表
        self.voices = {
            # 中文声音
            "zh-CN-XiaoxiaoNeural": "晓晓 (女声)",
            "zh-CN-YunxiNeural": "云希 (男声)",
            "zh-CN-YunyangNeural": "云扬 (男声)",
            "zh-CN-XiaoyiNeural": "小艺 (女声)",
            # 英文声音
            "en-US-JennyNeural": "Jenny (女声)",
            "en-US-GuyNeural": "Guy (男声)",
        }
        
        # 默认声音
        self.current_voice = self.config.get('current', 'zh-CN-XiaoxiaoNeural')
        
    async def _generate_async(self, text: str, output_path: str) -> Optional[str]:
        """异步生成 TTS"""
        try:
            communicate = edge_tts.Communicate(text, self.current_voice)
            await communicate.save(output_path)
            return output_path
        except Exception as e:
            logger.error(f"Edge-TTS Error: {e}")
            return None
    
    def generate(self, text: str, output_path: str = None) -> Optional[str]:
        """生成 TTS 音频"""
        if not output_path:
            date_str = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            output_path = f"./output/episodes/tts_{date_str}.mp3"
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating TTS: {len(text)} chars -> {output_file.name}")
        
        # 同步调用异步函数
        result = asyncio.run(self._generate_async(text, str(output_file)))
        
        if result and output_file.exists():
            size = output_file.stat().st_size
            logger.info(f"Saved: {output_file} ({size} bytes)")
            return str(output_file)
        else:
            logger.error("Generation failed!")
            return None
    
    def generate_from_script_file(self, script_path: str, output_path: str = None) -> Optional[str]:
        """从脚本文件生成 TTS"""
        script_file = Path(script_path)
        if not script_file.exists():
            logger.error(f"Script not found: {script_path}")
            return None
        
        # 读取脚本，去除标题行
        lines = script_file.read_text(encoding='utf-8').split('\n')
        text_lines = []
        skip = False
        for line in lines:
            if line.startswith('---'):
                skip = True
                continue
            if not skip:
                continue
            if line.strip():
                text_lines.append(line)
        
        text = '\n'.join(text_lines)
        return self.generate(text, output_path)
    
    def list_voices(self):
        """列出可用声音"""
        return self.voices
    
    def batch_generate(self, script_dir: str = "./output/scripts") -> list:
        """批量生成"""
        script_path = Path(script_dir)
        if not script_path.exists():
            logger.error(f"Script dir not found: {script_dir}")
            return []
        
        # 找最新的脚本
        scripts = sorted(script_path.glob("script_*.txt"), reverse=True)
        if not scripts:
            logger.warning("No scripts found!")
            return []
        
        generated = []
        for script_file in scripts[:3]:  # 每次最多处理 3 个
            logger.info(f"Processing: {script_file.name}")
            output = f"./output/episodes/{script_file.stem}.mp3"
            result = self.generate_from_script_file(str(script_file), output)
            if result:
                generated.append(result)
        
        return generated


def main():
    import argparse
    parser = argparse.ArgumentParser(description='TTS Generator (Edge-TTS)')
    parser.add_argument('--input', help='Input script file or text')
    parser.add_argument('--output', help='Output audio file')
    parser.add_argument('--voice', help='Voice ID (e.g., zh-CN-XiaoxiaoNeural)')
    parser.add_argument('--list-voices', action='store_true', help='List available voices')
    args = parser.parse_args()
    
    tts = TTSGenerator()
    
    if args.list_voices:
        print("Available voices:")
        for voice_id, name in tts.list_voices().items():
            print(f"  {voice_id}: {name}")
        return
    
    if args.voice:
        tts.current_voice = args.voice
    
    if args.input:
        # 判断是文件还是文本
        if Path(args.input).exists():
            result = tts.generate_from_script_file(args.input, args.output)
        else:
            result = tts.generate(args.input, args.output)
        
        if result:
            logger.info(f"Generated: {result}")
        else:
            logger.error("Generation failed!")
    else:
        # 批量处理
        tts.batch_generate()


if __name__ == "__main__":
    main()
