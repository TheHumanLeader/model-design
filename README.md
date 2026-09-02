# Model Design

基于 **Vue 3.6 Vapor Mode** 与 TypeScript 构建的高性能可视化模型设计器。

> 当前处于 `0.1.0-next` 基线开发阶段，先建立稳定的数据结构、交互模型与 npm 组件边界。Vue 3.6 正式版发布前，npm 包应使用 `next` 标签发布。

## 当前能力

- 无限画板：缩放、平移、内容适配
- 右键画板创建模型或分组
- 双击空白区域快速创建模型
- `Ctrl` / `Shift` 多选模型
- 将一个或多个模型组成分组
- 将模型拖入或拖出分组
- 分组整体移动与尺寸调整
- 配置模型名称、模型标识、模型用途
- 配置字段名称、字段标识、字段类型、字段用途
- 配置字段的必填、主键、唯一属性
- 撤销、重做
- JSON 导入、导出
- 浅色、深色与自动主题
- 只读模式
- 纯 Vapor SFC，不使用 JSX、TSX 或手写 VNode

## 技术栈

- Vue `3.6.0-rc.6`
- Vapor Mode
- TypeScript
- Vite 8
- Vitest

所有 `.vue` 组件都使用：

```vue
<script setup lang="ts" vapor>
```

演示应用通过 `createVaporApp()` 启动，不引入普通 VDOM 应用入口。

## 本地开发

环境要求：

- Node.js `20.19+`，推荐 Node.js 22
- npm 10+

```bash
git clone https://github.com/TheHumanLeader/model-design.git
cd model-design

npm install
npm run dev
```

浏览器打开 Vite 输出的本地地址即可。

## 验证

```bash
npm run typecheck
npm run test:run
npm run build
npm run pack:check
```

构建结果位于 `dist/`。

## 组件使用方式

项目发布到 npm 后：

```bash
npm install model-design@next vue@3.6.0-rc.6
```

入口应用必须使用 Vapor：

```ts
import { createVaporApp } from 'vue'
import App from './App.vue'

createVaporApp(App).mount('#app')
```

组件中使用：

```vue
<script setup lang="ts" vapor>
import { shallowRef } from 'vue'
import {
  ModelDesigner,
  createEmptyDocument,
  type ModelDesignDocument,
} from 'model-design'
import 'model-design/style.css'

const documentModel = shallowRef<ModelDesignDocument>(
  createEmptyDocument(),
)
</script>

<template>
  <ModelDesigner
    v-model="documentModel"
    height="100dvh"
    theme="auto"
  />
</template>
```

## Props

| 属性 | 类型 | 默认值 | 用途 |
|---|---|---:|---|
| `v-model` | `ModelDesignDocument` | 空文档 | 模型设计数据 |
| `readonly` | `boolean` | `false` | 只读模式 |
| `theme` | `'light' \| 'dark' \| 'auto'` | `'light'` | 主题 |
| `height` | `string \| number` | `'100%'` | 组件高度 |
| `showToolbar` | `boolean` | `true` | 是否显示顶部工具栏 |
| `showInspector` | `boolean` | `true` | 是否显示右侧配置面板 |
| `showStatusBar` | `boolean` | `true` | 是否显示底部状态栏 |
| `gridSize` | `number` | `12` | 拖动吸附网格 |
| `minZoom` | `number` | `0.25` | 最小缩放 |
| `maxZoom` | `number` | `2.5` | 最大缩放 |

## Events

```ts
type ModelDesignerEvents = {
  change: [document: ModelDesignDocument, label: string]
  selectionChange: [selection: DesignerSelection]
  ready: [api: ModelDesignerApi]
  error: [error: Error]
}
```

## 公开方法

通过模板引用获取：

```ts
interface ModelDesignerApi {
  createModel(position?, groupId?): string
  createGroup(position?): string
  groupSelected(): string | null
  deleteSelected(): void
  clearSelection(): void
  undo(): void
  redo(): void
  fitView(): void
  zoomIn(): void
  zoomOut(): void
  exportJSON(): string
  importJSON(source: string): void
  getDocument(): ModelDesignDocument
}
```

## 数据结构原则

模型与分组的所属关系只维护一份：

```ts
interface ModelNode {
  id: string
  groupId: string | null
}
```

分组不再额外保存 `modelIds`，避免模型和分组各维护一份成员关系后出现不同步。

模型文档只保存业务设计数据：

```ts
interface ModelDesignDocument {
  version: 1
  models: ModelNode[]
  groups: ModelGroup[]
}
```

选中状态、拖动状态、画板缩放与右键菜单属于运行时编辑器状态，不混入导出的模型文档。

## 目录

```text
src/
├─ components/
│  ├─ ModelDesigner.vue
│  ├─ ModelNode.vue
│  ├─ ModelGroup.vue
│  ├─ ModelInspector.vue
│  └─ DesignerContextMenu.vue
├─ core/
│  ├─ document.ts
│  ├─ id.ts
│  └─ index.ts
├─ playground/
│  ├─ App.vue
│  └─ main.ts
├─ styles/
│  └─ index.css
├─ index.ts
└─ types.ts
```

## 性能约束

项目从基线阶段遵守以下规则：

1. 纯 Vapor 模板，不使用 JSX、TSX、`h()` 或依赖 VNode 的接口。
2. 拖动过程中只更新临时位移，鼠标松开后才提交模型文档。
3. 模型文档采用不可变替换，避免对大型深层结构做无边界的响应式写入。
4. 节点位置使用 `translate3d()`，减少高频布局写入。
5. 高频画板数据与配置面板数据分离。
6. 后续大规模节点场景将加入视口裁剪，而不是依赖框架渲染全部不可见 DOM。

## 下一阶段

- 选框批量选择
- 模型关系与字段关系连线
- 对齐线与吸附线
- 命令系统与可合并事务
- 插件式字段类型
- 自定义模型节点外观
- 视口裁剪与节点虚拟化
- Minimap
- npm `next` 首次发布

## License

[MIT](./LICENSE)
