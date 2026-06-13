# 栖所 Perch

> 光影之间，片刻永恒 — A place where light and shadow dwell.

**Perch（栖所）** 是一个轻量级的个人照片展览系统，前后端分离，专注于以文艺、简约的方式展示照片收藏。

## 功能特色

- **瀑布流布局** — JS 动态瀑布流，图片保持原始比例，无拉伸裁剪
- **无限滚动** — 基于 scroll 事件监听的自动加载，滚动到底部前 400px 触发
- **图片预览** — 点击弹出全屏蒙版，支持 2x 缩放、下载
- **EXIF 信息** — 自动读取光圈、快门、ISO、拍摄时间
- **图片故事** — 管理员可为每张照片添加文字简介，日记体宋体样式展示
- **目录扫描** — 管理员手动输入路径，递归扫描并生成 1080p 缩略图
- **用户系统** — 普通用户免登录浏览，管理员通过 `/admin` 入口登录管理
- **深色模式** — 一键切换亮色/深色主题（米黄色主调）
- **非线性动画** — 图片入场、缩放、切换均有流畅的 cubic-bezier 动画
- **响应式** — 桌面 4 列、平板 3 列、手机 2 列自适应
- **Docker 部署** — 单镜像，Flask 直 serve Vue 构建产物

## 权限

| 角色 | 查看 | 下载 | 扫描目录 | 删除照片 | 编辑简介 | 修改账户 |
|------|------|------|---------|---------|---------|---------|
| 普通用户 | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ |
| 管理员 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

管理员入口：`/admin`（默认账号 `admin / admin123`）

## 技术栈

| 分层 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia |
| 后端 | Flask + SQLite + Pillow |
| 容器 | Docker + docker-compose |
| 安全 | Origin 白名单 + X-Requested-With 头校验 + Bearer Token |

## 快速开始

### 本地开发

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py

# 前端
cd frontend
npm install
npm run dev
```

### Docker 部署

```bash
docker compose build
docker compose up -d
# 访问 http://你的IP:5000
```

### 启动脚本

```bash
# Windows
.\start.ps1

# Linux
chmod +x start.sh && ./start.sh
```

## 项目结构

```
perch/
├── backend/
│   ├── app.py              # 主应用 (API + EXIF + 安全校验)
│   ├── config.py           # 配置 (缩略图尺寸、白名单)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/          # Gallery, AdminLogin, AdminDashboard
│   │   ├── components/     # PhotoModal
│   │   ├── stores/         # gallery.js, auth.js
│   │   ├── router/         # 路由定义
│   │   └── assets/         # 全局样式 (主题变量 + 动画)
│   └── package.json
├── Dockerfile               # 单镜像 (前端构建 + 后端运行)
├── docker-compose.yml
├── start.sh / start.ps1
└── stop.sh / stop.ps1
```

## API 接口

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/auth/login` | 管理员登录 | - |
| GET | `/api/auth/me` | 获取当前用户 | Bearer |
| PUT | `/api/auth/profile` | 修改昵称/密码 | Admin |
| GET | `/api/photos` | 照片列表（分页） | 公开 |
| GET | `/api/photos/:id` | 照片详情（含 EXIF） | 公开 |
| GET | `/api/photo-file/:id` | 原始图片 | 公开 |
| GET | `/api/download/:id` | 下载 | 公开 |
| GET | `/api/stats` | 统计 | 公开 |
| POST | `/api/scan` | 扫描目录 | Admin |
| PUT | `/api/photos/:id` | 更新简介 | Admin |
| DELETE | `/api/photos/:id` | 删除照片 | Admin |
| GET | `/api/settings/:key` | 读取设置 | 公开 |
| PUT | `/api/settings/:key` | 保存设置 | Admin |

## License MIT