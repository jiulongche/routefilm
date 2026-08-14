# RouteFilm 发布与社区传播素材

这份发布包帮助维护者和贡献者准确介绍 RouteFilm。发布前请把版本号和链接替换为当前值，不要宣称尚未发布的能力。

## 一句话定位

中文：把任意城市名单交给智能体，自动生成真实地图上的电影感路线视频，无需输入经纬度。

English: Give an agent any ordered city list and get a cinematic route video on real maps, with no coordinates to enter.

## GitHub Release 文案

### RouteFilm v0.1.0：从城市名单到真实地图路线电影

RouteFilm 首个公开版本把真实地图、实际道路、距离感知镜头、动态载具、轮渡交接和逐城地标整理成 Codex 与 Claude Code 都能使用的 Agent Skill。

- 用户只需按顺序输入地名，坐标自动解析与复核
- 长途自动拉高并提速，密集城市自动拉近
- 内置暖金箭头、黑色电动 SUV、滚装轮渡和 63 座城市地标
- 无生图服务也可完成丰富的地图视频；自定义生图仅支持 GPT Image 2
- 海报、局部样片、静音母版、音乐版本与不可覆盖的渲染历史
- 支持 Python 3.10-3.14，使用 MIT License

快速开始、动态演示和三类路线范例见项目 README。

## 中文社交平台短文案

把一串城市名交给 AI，能不能直接得到一条像样的真实地图旅行片？我们把一趟 40 个到达点、39 段行程、35 座城市、约 6,806 公里的自驾制作经验整理成了开源项目 RouteFilm。它会自动找坐标和实际道路，处理远近镜头、城市地标、载具运动、轮渡交接和配乐；Codex、Claude Code 都能直接用。现在项目内置 63 座城市地标，没有生图服务也能做。AI 时代，很多曾经只有想法却没有能力完成的事，边界正在逐渐模糊。

项目：https://github.com/jiulongche/routefilm

## English launch post

RouteFilm turns any ordered city list into a cinematic travel video on real maps. It automatically resolves coordinates and routed roads, adapts camera height and timing to distance, animates markers and ferry handoffs, and can showcase city landmarks. The repository ships an Agent Skill for Codex and Claude Code plus 63 offline landmarks, so image generation is optional. MIT licensed and built from a 6,806 km production route.

Project: https://github.com/jiulongche/routefilm

## Show HN / 技术社区标题

- Show HN: RouteFilm – Turn a city list into a cinematic route video on real maps
- RouteFilm：把任意城市名单变成真实地图动态路线片
- 我把 6,806 公里自驾视频的制作流程做成了 Codex / Claude Code Skill

## 发布清单

1. README 第一屏能直接看到 GIF，手机端也可读。
2. Release、README 和帖子中的版本号一致。
3. 分享图使用 `docs/media/social-preview.png`，演示使用 `docs/media/routefilm-preview.gif`。
4. 帖子包含真实输入和真实输出，不只列功能。
5. 清楚说明地图数据、演示媒体和代码的许可证边界。
6. 不上传 API Key、私人路线、下载音乐、地图缓存或来源不明素材。
7. 对每个社区单独调整标题与篇幅，避免重复灌水。
8. 发布后把安装失败、路线歧义和视觉问题分别沉淀成可复现 Issue。

## 建议发布顺序

先发布 GitHub Release 并开启 Discussions，再发布一篇中文制作复盘和一篇英文技术介绍。首周只选择 2-3 个与开发工具、地图可视化或旅行创作相关的社区，集中回应真实问题；后续用用户作品、城市地标补充和视觉对比持续更新，而不是反复转发同一条介绍。
