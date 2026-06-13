# 栖所 Perch 开发日志

## 项目概述

前后端分离的照片展览系统。前端 Vue 3 + Vite，后端 Flask + SQLite。

---

## 开发历程

### Phase 1 — 项目骨架

- 初始化项目结构：backend (Flask) + frontend (Vue 3 + Vite)
- 后端实现：目录扫描、缩略图生成、照片列表/详情/下载 API
- 前端实现：照片画廊页、图片详情页
- 基础样式：米黄色主题 + 深色模式切换

**经验：** Pillow 的 `thumbnail()` 不会放大图片，适合生成缩略图。

### Phase 2 — 瀑布流 + 无限滚动

- CSS columns 瀑布流 → 动态加载后列数错乱 → 换用 JS 绝对定位瀑布流
- 分页 → 无限滚动（IntersectionObserver）
- 首次加载 10 行，后续每次 2 行（后改为统一 per_page 避免分页重叠）

**教训：** CSS columns 在动态追加内容时会重排所有元素导致布局错乱。改用 JS 绝对定位 + `offsetHeight` 计算容器高度。

**教训：** 不同页使用不同 `per_page` 会导致分页偏移量错位、数据重叠。必须统一 `per_page`。

**教训：** IntersectionObserver 在快速级联加载时状态判断复杂，不如 scroll 事件 + debounce 直观可靠。

### Phase 3 — 用户管理

- 后端：用户表 + Token 认证 + `@require_admin` 装饰器
- 前端：`/admin` 登录页 + 管理面板（照片管理/扫描/账户设置）
- 普通用户免登录，管理员入口不暴露在页面中

**经验：** Pinia 多个 store（auth + gallery）职责分离清晰，auth store 统一管理 token 和请求头。

### Phase 4 — 图片预览改造

- 独立详情页 → 全屏蒙版弹窗
- 蒙版内展示：大图（点击缩放 2x）、EXIF 参数、下载按钮
- 蒙版打开时锁定 body 滚动

**教训：** 蒙版打开时记得设 `document.body.style.overflow = 'hidden'`，关闭时恢复。

### Phase 5 — EXIF 读取

- Pillow 读取 EXIF 返回 `IFDRational` 类型而非 tuple
- `isinstance(raw, tuple)` 判断失败导致快门/光圈不显示
- 统一 `to_float()` 处理所有数值类型

**教训：** Python Pillow 的 `_getexif()` 返回 `IFDRational` 对象，需要用 `float()` 转换。不同相机厂商的 EXIF 标签填充方式也不同，需做好兼容。

### Phase 6 — 图片故事

- 后台：`photos` 表加 `description` 字段 + `PUT` 更新 API
- 前端：蒙版内日记体宋体简介展示
- 管理面板：行内编辑简介文本框

**经验：** SQLite `ALTER TABLE ADD COLUMN` 用 `try/except OperationalError` 兼容已有数据库。

### Phase 7 — 安全加固

- Origin 白名单校验（`ALLOWED_ORIGINS`）
- `X-Requested-With: XMLHttpRequest` 头校验
- Docker 模式：`ALLOW_ALL_ORIGINS = True` 放行内网访问
- API 路由才校验自定义头，静态文件放行

### Phase 8 — Docker 化

- 双镜像 → 单镜像（Flask 直 serve Vue 构建产物）
- 前端 Node 构建阶段 → Python 运行时阶段
- Flask catch-all 路由处理 Vue history 模式路由

**经验：** `createWebHistory()` 需要服务端所有非 API 路径返回 `index.html`。

### Phase 9 — 生产部署 & 分页调整

- 管理面板分页（默认每页 10 条，可选 10/20/50/100）
- 扫描路径持久化（`settings` 表 key-value 存储）
- 纯净 Docker 代码包（排除 testresource/node_modules/data/uploads）

---

## 架构决策记录

### 瀑布流方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| CSS columns | 简单，纯 CSS | 动态追加内容时重排错乱 | 放弃 |
| JS 绝对定位 | 稳定，动态追加不重排 | 需手动计算容器高度 | 采用 |

### 无限滚动方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| IntersectionObserver | 性能好 | 级联加载时状态判断复杂 | 弃用 |
| scroll 事件 + debounce | 直观可控 | 性能略差（可接受） | 采用 |

### 镜像方案

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| 双镜像（Nginx + Flask） | 职责分离 | 多容器配置复杂 | 放弃 |
| 单镜像（Flask serve 前端） | 简单，一个端口 | Flask 静态文件性能不如 Nginx | 采用 |

---

## 已知问题 / 待办

- [ ] 首页无限滚动有时仍不触发，需继续排查 scroll 事件绑定时机
- [ ] 图片加载骨架屏 shimmer 动画在部分浏览器不流畅
- [ ] 管理面板照片列表没有批量操作功能
- [ ] 没有图片上传功能（仅支持目录扫描）
- [ ] EXIF 读取未覆盖所有相机品牌
- [ ] 没有设置页面，扫描路径无法手动清除
- [ ] 没有日志系统，扫描错误仅在 API 响应中返回

---

## 后续规划

1. **首页加载优化**：确认 scroll 事件 + watch 级联的双重保障机制能稳定加载所有图片
2. **文件上传**：支持网页端直接上传图片
3. **图片管理增强**：批量删除、移动、标签分类
4. **相册功能**：创建相册，照片归类
5. **分享功能**：生成分享链接
6. **图片编辑**：基础裁剪、滤镜
7. **更多 EXIF**：镜头信息、白平衡、GPS 位置
8. **国际化**：中英文切换