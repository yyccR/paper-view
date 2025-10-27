# Paper View Frontend (Vue 3)

这是 Paper View 项目的 Vue.js 前端部分。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **Vue Router** - 官方路由管理器
- **Pinia** - 新一代状态管理库
- **Axios** - HTTP 客户端
- **Vite** - 下一代前端构建工具

## 项目结构

```
frontend/
├── public/              # 静态资源
│   └── index.html      # HTML 模板
├── src/
│   ├── api/            # API 接口封装
│   ├── assets/         # 资源文件（CSS、图片等）
│   ├── components/     # Vue 组件
│   ├── router/         # 路由配置
│   ├── utils/          # 工具函数
│   ├── views/          # 页面视图
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── package.json        # 项目依赖
└── vite.config.js      # Vite 配置

```

## 开发指南

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

开发模式下，前端运行在 `http://localhost:9521`，所有 API 请求会自动代理到 Django 后端 `http://localhost:9520`。

```bash
npm run dev
```

### 生产构建

```bash
npm run build
```

构建后的文件会输出到 `dist/` 目录，可以被 Django 直接提供服务。

### 预览生产构建

```bash
npm run preview
```

## 主要组件说明

### 页面组件

- **HomePage.vue** - 首页，包含搜索、功能介绍、论文列表
- **WorkspacePage.vue** - 工作区页面，包含搜索结果、文件预览等

### 通用组件

- **Header.vue** - 导航栏
- **HeroSection.vue** - 主横幅区域
- **FeaturesSection.vue** - 功能介绍
- **PaperCard.vue** - 论文卡片
- **PaperModal.vue** - 论文详情模态框
- **Sidebar.vue** - 侧边导航栏
- **Footer.vue** - 页脚

## API 集成

所有 API 调用都通过 `src/api/index.js` 统一管理：

```javascript
import { apiService } from '@/api'

// 获取论文列表
const papers = await apiService.getContentList()

// 上传 PDF
await apiService.uploadPdf(file)
```

## 开发注意事项

1. **API 代理** - 开发环境下所有 `/api` 请求会自动代理到后端
2. **热重载** - 代码修改后会自动刷新浏览器
3. **样式** - 使用 scoped CSS 避免样式冲突
4. **路由** - 使用 Vue Router 的 history 模式

## 与 Django 集成

### 开发环境
前后端分离，前端独立运行：
```bash
./start.sh dev
```

### 生产环境
构建后由 Django 提供服务：
```bash
cd frontend && npm run build
cd .. && python manage.py collectstatic
python manage.py runserver
```
