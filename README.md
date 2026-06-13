# 栖所 Perch

> 光影之间，片刻永恒 — A place where light and shadow dwell.

**Perch（栖所）** 是一个轻量级的个人照片展览系统，前后端分离，专注于以文艺、简约的方式展示你的照片收藏。

## 功能特色

- **照片画廊** — 瀑布流式布局，优雅展示照片
- **目录扫描** — 扫描指定目录，自动建立照片索引
- **照片详情** — 点击查看大图，支持缩放与下载
- **非线性动画** — 页面加载、图片入场、缩放、下载均有流畅的非线性动画
- **深色模式** — 一键切换亮色/深色主题
- **米黄色主调** — 温暖柔和的视觉风格

## 技术栈

| 分层 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia + Vue Router |
| 后端 | Flask + SQLite + Pillow |
| 动画 | CSS cubic-bezier 非线性动画 |

## 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+

### 1. 启动后端

```bash
cd backend
pip install -r requirements.txt
python app.py
```

后端运行在 `http://localhost:5000`

### 2. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:3000`

### 3. 使用

1. 打开浏览器访问 `http://localhost:3000`
2. 点击右上角的 **+** 按钮，选择照片目录进行扫描
3. 扫描完成后即可浏览照片
4. 点击照片查看详情，支持缩放与下载

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/scan` | 扫描目录 |
| GET | `/api/photos` | 获取照片列表 |
| GET | `/api/photos/:id` | 获取照片详情 |
| GET | `/api/photo-file/:id` | 获取原始照片文件 |
| GET | `/api/download/:id` | 下载照片 |
| GET | `/api/stats` | 获取统计信息 |
| GET | `/api/suggest-dirs` | 目录浏览建议 |

## 项目结构

```
perch/
├── backend/           # Flask 后端
│   ├── app.py         # 主应用
│   ├── config.py      # 配置
│   └── requirements.txt
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── views/     # 页面组件
│   │   ├── components/ # 通用组件
│   │   ├── stores/    # Pinia 状态管理
│   │   ├── router/    # 路由
│   │   └── assets/    # 样式
│   └── package.json
└── README.md
```

## License

MIT