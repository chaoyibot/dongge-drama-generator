#!/usr/bin/env python3
"""
东哥短剧生成器 - 后端API服务
真正调用 Agnes AI API 生成剧本、角色、场景
"""

import os
import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import base64
import time
import threading

# 从 .bashrc 读取 API Key
def load_api_key():
    bashrc = Path.home() / ".bashrc"
    if bashrc.exists():
        for line in bashrc.read_text().splitlines():
            if line.startswith("export AGNES_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return os.environ.get("AGNES_API_KEY", "")

AGNES_API_KEY = load_api_key()
AGNES_BASE_URL = "https://apihub.agnes-ai.com/v1"

class DramaGeneratorHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """抑制默认日志输出"""
        pass
    
    def do_OPTIONS(self):
        """处理跨域请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data.decode('utf-8'))
        
        if self.path == '/api/generate-script':
            self.generate_script(data)
        elif self.path == '/api/generate-characters':
            self.generate_characters(data)
        elif self.path == '/api/generate-scenes':
            self.generate_scenes(data)
        else:
            self.send_error(404)
    
    def do_GET(self):
        """处理健康检查"""
        if self.path == '/health':
            self.send_json_response({"status": "ok"})
        else:
            self.send_error(404)
    
    def generate_script(self, data):
        """生成剧本 - 调用Agnes文本模型"""
        direction = data.get('direction', '')
        genre = data.get('genre', 'cartoon')
        
        genre_map = {
            'urban_fantasy': '都市奇幻',
            'rebirth': '重生爽文', 
            'ceo_romance': '霸总甜宠',
            'suspense': '悬疑推理',
            'cartoon': '3D卡通动画',
            'custom': '自定义'
        }
        
        prompt = f"""你是一个专业的短剧编剧。请根据以下信息生成一个完整的短剧剧本。

故事方向：{direction}
题材类型：{genre_map.get(genre, '卡通动画')}

要求：
1. 生成12场戏的完整剧本
2. 每场戏必须包含：
   - scene_title: 场景标题（如"翠花林清晨"）
   - description: 详细的场景描述（100字以上，包含视觉元素、光影、色彩、构图）
   - dialogue: 角色对话列表，每个对话包含 character（角色名）和 text（台词）
   - camera: 镜头说明
3. 风格要幽默搞笑，加入笑点、反差萌、意外转折
4. 角色要有鲜明的个性特征
5. 输出必须是严格的JSON格式，不要任何其他文字

输出格式示例：
{{
  "title": "剧本标题",
  "genre": "题材",
  "scenes": [
    {{
      "id": 1,
      "scene_title": "场景标题",
      "description": "详细描述...",
      "dialogue": [
        {{"character": "角色名", "text": "台词内容"}}
      ],
      "camera": "镜头说明"
    }}
  ]
}}"""
        
        try:
            result = self.call_agnes_chat(prompt, max_tokens=4000)
            # 解析JSON
            script = json.loads(result)
            self.send_json_response({"success": True, "script": script})
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            try:
                start = result.find('{')
                end = result.rfind('}') + 1
                if start >= 0 and end > start:
                    script = json.loads(result[start:end])
                    self.send_json_response({"success": True, "script": script})
                else:
                    self.send_json_response({"success": False, "error": "剧本生成失败"})
            except:
                self.send_json_response({"success": False, "error": result[:500]})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def generate_characters(self, data):
        """生成角色设定 - 调用Agnes文本+图片模型"""
        script = data.get('script', {})
        
        # 第一步：用文本模型生成角色描述
        prompt = f"""根据以下剧本，生成4个主要角色的详细设定。

剧本标题：{script.get('title', '')}
剧本内容：{json.dumps(script, ensure_ascii=False)[:1000]}

请为每个角色生成：
1. character_name: 角色名称
2. appearance: 外貌描述（200字以上，包含体型、脸型、眼睛、鼻子、嘴巴、头发/毛发颜色、表情特征）
3. clothing: 服装描述
4. personality: 性格特点
5. props: 标志性道具
6. style: 画风要求（3D卡通，幽默搞笑）

输出JSON格式：
{{
  "characters": [
    {{
      "character_name": "角色名",
      "appearance": "详细外貌描述...",
      "clothing": "服装描述...",
      "personality": "性格特点...",
      "props": "道具...",
      "style": "3D卡通风格"
    }}
  ]
}}"""
        
        try:
            # 生成角色描述
            text_result = self.call_agnes_chat(prompt, max_tokens=2000)
            characters_data = json.loads(text_result)
            
            # 第二步：为每个角色生成图片
            characters_with_images = []
            for char in characters_data.get('characters', []):
                # 生成图片提示词
                image_prompt = f"""3D卡通风格，可爱的{char['character_name']}角色设定图。
外貌：{char['appearance']}
服装：{char['clothing']}
表情：生动有趣，幽默搞笑
背景：纯色背景
高质量，细节丰富"""
                
                # 调用图片生成API
                image_url = self.call_agnes_image(image_prompt, size="1024x1024")
                
                characters_with_images.append({
                    **char,
                    "image_url": image_url or "",
                    "status": "generated" if image_url else "failed"
                })
            
            self.send_json_response({
                "success": True,
                "characters": characters_with_images
            })
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def generate_scenes(self, data):
        """生成场景图 - 调用Agnes图片模型"""
        script = data.get('script', {})
        scenes_data = script.get('scenes', [])
        
        try:
            scenes_with_images = []
            for scene in scenes_data[:12]:  # 最多12场
                # 生成场景图片提示词
                image_prompt = f"""3D卡通风格，{scene.get('scene_title', '场景')}场景图。
{scene.get('description', '')}
幽默搞笑风格，色彩鲜艳，光影效果出色
高质量，电影级画质"""
                
                image_url = self.call_agnes_image(image_prompt, size="1920x1080")
                
                scenes_with_images.append({
                    "id": scene.get('id'),
                    "scene_title": scene.get('scene_title', ''),
                    "description": scene.get('description', ''),
                    "image_url": image_url or "",
                    "status": "generated" if image_url else "failed"
                })
            
            self.send_json_response({
                "success": True,
                "scenes": scenes_with_images
            })
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def call_agnes_chat(self, prompt, max_tokens=2000):
        """调用Agnes文本生成API"""
        if not AGNES_API_KEY:
            raise Exception("API Key未配置")
        
        url = f"{AGNES_BASE_URL}/chat/completions"
        headers = {
            "Authorization": f"Bearer {AGNES_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "agnes-2.0-flash",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        
        req = urllib.request.Request(url, json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read())
            return result['choices'][0]['message']['content']
    
    def call_agnes_image(self, prompt, size="1024x1024"):
        """调用Agnes图片生成API"""
        if not AGNES_API_KEY:
            raise Exception("API Key未配置")
        
        url = f"{AGNES_BASE_URL}/images/generations"
        headers = {
            "Authorization": f"Bearer {AGNES_API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "agnes-image-2.1-flash",
            "prompt": prompt,
            "size": size,
            "response_format": "url"
        }
        
        req = urllib.request.Request(url, json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read())
            # 提取图片URL
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0].get('url', '')
            return ''
    
    def send_json_response(self, data):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())

if __name__ == '__main__':
    port = 8000
    server = HTTPServer(('0.0.0.0', port), DramaGeneratorHandler)
    print(f"🚀 东哥短剧生成器后端服务启动在端口 {port}")
    print(f"📡 API地址: http://127.0.0.1:{port}")
    print(f"🔑 API Key: {'已配置' if AGNES_API_KEY else '未配置'}")
    server.serve_forever()
