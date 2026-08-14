# RouteFilm

把一串城市交给智能体，得到真实地图上的自驾路线视频：实际道路、自动镜头、载具运动、轮渡交接、城市地标和配乐版本。

![RouteFilm 正式成片海报](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-poster.jpg)

[查看正式成片前 5 个到达点节选](https://github.com/jiulongche/routefilm/raw/refs/heads/main/docs/media/routefilm-five-stops-demo.mp4) · 40 秒 · 720×1280 · 静音母版

![RouteFilm 完整到站分镜](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-full-storyboard.jpg)

## 最快使用

在这个仓库里打开 Codex 或 Claude Code，只需按顺序说出地名，并按需选择载具：

**Codex**

```text
$build-route-map-video 把海口、徐闻、湛江、南宁做成竖屏自驾路线视频，载具用默认箭头。
```

**Claude Code**

```text
/build-route-map-video 把海口、徐闻、湛江、南宁做成竖屏自驾路线视频，载具用默认箭头。
```

Skill 一次只问一个问题：先收路线，再用选择界面询问载具，最后检查当前环境是否具备生图能力后再询问地标。推荐选项排在第一，每个选项说明实际影响，并保留“其他”输入。

坐标由项目自动查询、筛选和缓存，用户不需要输入经纬度；只有“临平”这类名称确实对应多个同等匹配地点时，智能体才会用候选选择题单独询问具体地点。

项目内置新版暖金箭头、无品牌黑色电动 SUV 和滚装轮渡。轮渡不是全程载具选项，只在识别到海峡路段时自动完成车船交接。想换成自己的透明素材或 GPT Image 2 生成载具时，在同一句话里补充即可。地图样式、长短途镜头、城市标签、海报、局部样片和质量检查都由智能体处理，不需要先理解配置文件或命令行。

## 智能体安装

需要 Python 3.10+ 和 FFmpeg；系统还需要一款可显示中文的字体。让 Codex 或 Claude Code 在仓库中完成安装和预检：

```bash
git clone https://github.com/jiulongche/routefilm.git
cd routefilm
python -m pip install -e .
python skills/build-route-map-video/scripts/preflight.py
```

仓库内已经同时配置 Codex 和 Claude Code Skill。需要把 Skill 安装到所有项目时，再使用：

```bash
python scripts/install_agent_skills.py --agent both
```

## 默认效果

- 真实 OpenStreetMap 中文地图与 OSRM 实际道路
- 全程 Web Mercator，拉远时地图不变形
- 状态栏固定在地图外，不遮挡道路
- 长距离自动拉高并稍快，短距离和密集城市自动拉近
- 城市名尽量持续显示并自动避让
- 内置暖金箭头与无品牌黑色电动 SUV 两种路线标记
- 载具位置按行驶距离采样，车头沿同一轨迹切线，不侧滑
- 海峡路段自动切换内置轮渡，使用接近、登船、航行、下船、驶离五阶段
- 首次到达放大地标，重复到达只点亮
- 开场先看完整路线，结尾慢速拉远并停留

## 可选能力

**自定义载具**：只支持 GPT Image 2。智能体会先给出提示词供确认，再从环境变量读取用户配置的 API URL 和 Key。生成后优先使用 `rembg` 本地抠图，纯色键作为兜底。

**城市地标**：系统先检测生图能力。可用时提供“智能推荐并生成 / 不展示 / 使用已有图片”；不可用时不显示自动生成选项，只提供“不展示 / 使用已有图片 / 先配置生图服务”。生成前会确认完整地标清单和提示词。

**音乐**：支持 Openverse、Wikimedia 授权音乐检索，保存来源和许可证记录，并完成 BPM 分析、区域换曲、交叉淡化、到站卡点及静音母版无损视频复用。

**手动模式**：需要精确控制 YAML、渲染、音乐和 QA 时，查看[命令行参考](docs/cli-reference.md)。

## 项目来源

这套方法来自一条 40 个到达点、39 段、35 座城市、约 6,806 km 的中国自驾路线。制作过程经历 15 个主版本和 6 条方案分叉，最终收敛为“真实地图 + 实际道路 + 无侧滑载具 + 双向轮渡 + 逐城地标”的工作流。

详细经验见[中文真实地图路线视频制作复盘](docs/production-lessons.zh-CN.md)。

## 智能体支持

| 智能体 | 支持情况 |
| --- | --- |
| Codex | 一级支持，使用 `.agents/skills` |
| Claude Code | 一级支持，使用 `.claude/skills` |
| 支持 Agent Skills 标准的工具 | 尽力兼容 |
| 读取 `AGENTS.md` 的其他工具 | 通用工作流兼容 |

项目只维护一份核心 `SKILL.md`，避免为多个厂商复制同一套流程后逐渐分叉。详见[智能体兼容性](docs/agent-compatibility.md)。

## 更多文档

- [命令行参考](docs/cli-reference.md)
- [架构与数据流](docs/architecture.md)
- [地图、投影与合规](docs/maps-and-compliance.md)
- [音乐工作流](docs/music-workflow.md)
- [English README](README.en.md)

代码使用 MIT License；`docs/media/` 中的原创演示内容使用 CC BY 4.0。地图、字体、音频、生成素材与外部服务保留各自条款。使用 OSM 数据或瓦片时必须保留 `© OpenStreetMap contributors`，并遵守对应服务策略。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
