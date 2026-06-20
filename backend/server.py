#!/usr/bin/env python3
"""
东哥短剧生成器 - 后端API服务
提供Agnes AI API代理和短剧生成服务
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
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
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
    
    def generate_script(self, data):
        """生成剧本"""
        direction = data.get('direction', '')
        genre = data.get('genre', 'cartoon')
        
        # 调用Agnes AI生成剧本
        prompt = f"""请根据以下信息生成一个完整的短剧剧本：
故事方向：{direction}
题材类型：{genre}

要求：
1. 生成12场戏的完整剧本
2. 每场戏包含：场景标题、角色对话、动作描述、镜头说明
3. 输出JSON格式：{{"title": "剧本标题", "scenes": [{{"id": 1, "title": "场景标题", "description": "详细描述", "dialogue": "角色对话", "camera": "镜头说明"}}]}}
4. 风格幽默搞笑"""
        
        try:
            response = self.call_agnes_chat(prompt)
            self.send_json_response({"success": True, "script": response})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def generate_characters(self, data):
        """生成角色设定图"""
        script = data.get('script', {})
        
        # 调用Agnes AI生成角色描述
        prompt = f"""根据以下剧本生成角色设定：
剧本标题：{script.get('title', '')}
剧本内容：{json.dumps(script, ensure_ascii=False)}

请生成4个主要角色的详细描述，包括：
1. 角色名称
2. 外貌特征
3. 性格特点
4. 服装描述

输出JSON格式"""
        
        try:
            characters = self.call_agnes_chat(prompt)
            # 这里应该调用图像生成API
            self.send_json_response({"success": True, "characters": characters})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def generate_scenes(self, data):
        """生成场景图"""
        script = data.get('script', {})
        
        try:
            # 调用图像生成API生成场景图
            scenes = []
            for i in range(12):
                scene_prompt = f"生成第{i+1}场戏的场景图，基于剧本：{json.dumps(script, ensure_ascii=False)}"
                scenes.append({"id": i+1, "prompt": scene_prompt})
            
            self.send_json_response({"success": True, "scenes": scenes})
        except Exception as e:
            self.send_json_response({"success": False, "error": str(e)})
    
    def call_agnes_chat(self, prompt):
        """调用Agnes聊天API"""
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
            "max_tokens": 2000
        }
        
        req = urllib.request.Request(url, json.dumps(data).encode(), headers)
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read())
            return result['choices'][0]['message']['content']
    
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
    server.serve_forever()
