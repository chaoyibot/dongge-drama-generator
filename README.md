# 东哥短剧生成器

一个基于 Agnes AI 的 Web 短剧生成工具，支持从剧本到成片的完整流程。

## 功能特点

- 📝 智能剧本生成（基于Agnes AI）
- 🎭 角色设定图生成
- 🎨 场景参考图生成
- 🎥 视频片段自动生成
- 🎞️ 成片自动拼接

## 使用方法

1. 启动后端服务：
```bash
cd backend
python server.py
```

2. 在浏览器中打开 `frontend/index.html`

## 技术栈

- 后端：Python HTTP Server
- 前端：原生 HTML/CSS/JavaScript
- AI 服务：Agnes AI
- 视频处理：FFmpeg

## 项目结构

```
dongge-drama-generator/
├── backend/
│   └── server.py          # 后端API服务
├── frontend/
│   └── index.html         # 前端界面
└── README.md              # 项目说明
```

## 许可证

MIT
