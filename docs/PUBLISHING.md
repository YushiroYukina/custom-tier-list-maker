# GitHub 发布准备

当前公开仓库：[YushiroYukina/custom-tier-list-maker](https://github.com/YushiroYukina/custom-tier-list-maker)

本地维护目录：通过 GitHub Desktop 中的 `custom-tier-list-maker` 仓库管理。

建议描述：通用自定义排行榜制作工具：在浏览器中拖拽图文卡片、自定义档位，支持素材池、JSON 存档和 PNG 导出。

建议主题：`tier-list`、`ranking`、`html`、`javascript`、`offline`、`canvas`。

## 当前准备包

包含可直接运行的 `index.html`、功能与适用范围说明、通用模板、素材池示例、界面截图和变更记录。无需 Node.js、Python 或构建工具即可使用。未包含原始 Excel、个人榜单、个人封面、抓取脚本及缓存。

## 正式上传前

1. 确认原始代码发布授权，选择开源许可证并增加 `LICENSE`。本包不擅自指定许可证或虚构作者归属。
2. 复查 README 的界面、功能和已知限制是否符合准备发布的版本。
3. 后续更新在本地仓库修改，提交后通过 GitHub Desktop 推送，保持 `index.html`、README 和示例目录结构。
4. 如需在线访问，可另行启用静态页面托管；当前已创建公开仓库并推送代码，尚未启用页面托管。
5. 如制作 Release，使用通用名称 ZIP，并附上 CHANGELOG 内容。不要把个人榜单 JSON、图片和浏览器存储当作演示素材提交。

## 本地检查

双击入口，检查演示卡片完整显示；导入素材池示例后所有卡片应留在素材池，档位为空；拖入档位再导出 PNG 和 JSON。刷新后检查自动保存。移动文件前先导出 JSON 备份。

保留的旧格式标记 `hanla-ranking` 和浏览器存储键仅用于兼容；它们不是公开产品名称。
