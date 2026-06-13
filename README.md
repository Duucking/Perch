# 栖所 Perch

> 光影之间，片刻永恒 — A place where light and shadow dwell.

**Perch（栖所）** 是一个轻量级的个人照片展览系统，前后端分离，专注于以文艺、简约的方式展示你的照片收藏。

## 功能特色

- **瀑布流布局** — JS 动态瀑布流，图片保持原始比例，无拉伸裁剪
- **无限滚动** — 滚动到底部自动加载，首次 5 行，后续每次 2 行
- **图片预览** — 点击弹出全屏蒙版，支持 2x 缩放、下载
- **EXIF 信息** — 自动读取光圈、快门、ISO、拍摄时间
- **图片故事** — 管理员可为每张照片添加文字简介，日记体样式展示
- **目录扫描** — 管理员指定目录，自动扫描图片并生成 1080p 缩略图
- **用户系统** — 普通用户免登录浏览，管理员通过 `/admin` 入口管理
- **深色模式** — 一键切换亮色/深色主题
- **非线性动画** — 页面加载、图片入场、缩放均有流畅的非线性动画
- **响应式** — 桌面 4 列、平板 3 列、手机 2 列自适应

## 技术栈

| 分层 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia |
| 后端 | Flask + SQLite + Pillow |
| 动画 | CSS cubic-bezier 非线性动画 |
| 认证 | Token 认证 + werkzeug 密码哈希 |

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
2. 管理员访问 `http://localhost:3000/admin` 登录（默认 `admin / admin123`）
3. 在管理面板中选择照片目录进行扫描
4. 返回首页即可浏览照片
5. 点击照片查看大图、拍摄参数与简介

### 启动脚本

```bash
# Windows
.\start.ps1

# Linux
chmod +x start.sh && ./start.sh
```

## API 接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/auth/login` | 管理员登录 | - |
| GET | `/api/auth/me` | 获取当前用户 | Bearer |
| PUT | `/api/auth/profile` | 修改昵称/密码 | Admin |
| GET | `/api/photos` | 获取照片列表（分页） | 公开 |
| GET | `/api/photos/:id` | 获取照片详情（含 EXIF） | 公开 |
| GET | `/api/photo-file/:id` | 获取原始图片 | 公开 |
| GET | `/api/download/:id` | 下载照片 | 公开 |
| GET | `/api/stats` | 统计信息 | 公开 |
| POST | `/api/scan` | 扫描目录 | Admin |
| GET | `/api/suggest-dirs` | 目录浏览 | Admin |
| PUT | `/api/photos/:id` | 更新照片简介 | Admin |
| DELETE | `/api/photos/:id` | 删除照片 | Admin |

## 项目结构

```
perch/
├── backend/
│   ├── app.py              # 主应用 (API + 扫描 + EXIF)
│   ├── config.py           # 配置
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/          # Gallery, AdminLogin, AdminDashboard
│   │   ├── components/     # PhotoModal
│   │   ├── stores/         # gallery.js, auth.js
│   │   ├── router/         # 路由定义
│   │   └── assets/         # 全局样式
│   └── package.json
├── start.ps1 / start.sh    # 启动脚本
├── stop.ps1 / stop.sh      # 停止脚本
└── README.md
```

## License

MIT