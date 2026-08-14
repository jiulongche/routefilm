# RouteFilm

[![CI](https://github.com/jiulongche/routefilm/actions/workflows/ci.yml/badge.svg)](https://github.com/jiulongche/routefilm/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/jiulongche/routefilm?display_name=tag&sort=semver)](https://github.com/jiulongche/routefilm/releases)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-2f855a.svg)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent_Skills-Codex_%7C_Claude_Code-f2b84b)](docs/agent-compatibility.md)

**把任意一串城市交给智能体，得到真实地图上的电影感路线视频。** 只需按顺序输入地名，不用填写经纬度；RouteFilm 自动处理实际道路、距离感知镜头、载具运动、轮渡交接、城市地标和配乐版本。

![RouteFilm 动态演示](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-preview.gif)

内置 63 座城市地标，无生图服务也能丰富到站画面；Codex 和 Claude Code 均可直接通过 Skill 引导完成。路线始终来自用户输入，示例只是可替换的起点。

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

Skill 一次只问一个问题：先收路线，再用选择界面询问载具，检查当前环境是否具备生图能力后询问地标，最后给出一个结合路线主题的具体片名建议，也支持自定义标题。推荐选项排在第一，每个选项说明实际影响，并保留“其他”输入。

坐标由项目自动查询、筛选和缓存，用户不需要输入经纬度；只有“临平”这类名称确实对应多个同等匹配地点时，智能体才会用候选选择题单独询问具体地点。

项目内置新版暖金箭头、无品牌黑色电动 SUV 和滚装轮渡。轮渡不是全程载具选项，只在识别到海峡路段时自动完成车船交接。想换成自己的透明素材或 GPT Image 2 生成载具时，在同一句话里补充即可。地图样式、长短途镜头、城市标签、海报、局部样片和质量检查都由智能体处理，不需要先理解配置文件或命令行。

## 三条路线示例

- [江浙沪密集城市](examples/jiangnan-city-cluster.yaml)：短距离站点自动拉近，适合检查标签与镜头节奏
- [跨省长途路线](examples/cross-province-road-trip.yaml)：长距离自动拉高并提速，区域段落保持可读
- [琼州海峡轮渡](examples/haikou-ferry-route.yaml)：自动触发接近、登船、航行、下船、驶离五阶段

复制任一 YAML 后只需替换 `route` 中的城市顺序。也可以完全不接触配置文件，直接把自己的路线发给 Skill。

## 成片细节

[查看正式成片前 5 个到达点节选](https://github.com/jiulongche/routefilm/raw/refs/heads/main/docs/media/routefilm-five-stops-demo.mp4) · 40 秒 · 720×1280 · 静音母版

![RouteFilm 完整到站分镜](https://raw.githubusercontent.com/jiulongche/routefilm/main/docs/media/routefilm-full-storyboard.jpg)

## 智能体安装

需要 Python 3.10+ 和 FFmpeg；系统还需要一款可显示中文的字体。让 Codex 或 Claude Code 在仓库中完成安装和预检：

```bash
git clone https://github.com/jiulongche/routefilm.git
cd routefilm
python -m pip install -e ".[cutout]"
python skills/build-route-map-video/scripts/preflight.py
```

仓库内已经同时配置 Codex 和 Claude Code Skill。需要把 Skill 安装到所有项目时，再使用：

```bash
python scripts/install_agent_skills.py --agent both
```

## 默认效果

- 真实 OpenStreetMap 中文地图与 OSRM 实际道路
- 全程 Web Mercator，拉远时地图不变形
- 状态栏固定在地图外，不遮挡道路；行驶时保留方向箭头，到站时显示地标缩略图
- 长距离自动拉高并稍快，短距离和密集城市自动拉近
- 城市名尽量持续显示并自动避让
- 内置暖金箭头与无品牌黑色电动 SUV 两种路线标记
- 载具位置按行驶距离采样，车头沿同一轨迹切线，不侧滑
- 海峡路段自动切换内置轮渡，使用接近、登船、航行、下船、驶离五阶段
- 内置 63 个不重复城市的离线地标库，覆盖 34 个省级行政区代表城市与原路线 35 城，无生图服务也能使用
- 未到地标灰显，首次到达从城市移动到地图中央放大并回落常驻，重复到达只脉冲点亮
- 开场显示完整路线、起终点和行程摘要，区域行程自动收紧视野，跨多区域长线才使用全国尺度；结尾慢速拉远并停留
- 智能体推荐一个具体片名，也可写入任意自定义标题
- 每次海报和视频渲染自动建立不可覆盖的 `runs/<run-id>/`，记录配置、素材哈希、代码版本和 QA

## 可选能力

**自定义载具**：只支持 GPT Image 2。智能体会先给出提示词供确认，再通过安全配置解析器读取 API URL 和 Key，不在对话中收集密钥。生成后优先使用 `rembg` 本地抠图，纯色键作为兜底。

**城市地标**：智能体优先推荐无需 Key 的内置全国地标库，也支持已有图片或 GPT Image 2 补全。选择自定义后才检查生图能力；不可用时不会提供可执行的自动生成选项。选择配置会暂停整个视觉渲染流程，检测通过后再回到地标来源选择。生成前会确认完整地标清单和全部提示词。

**历史版本**：`routefilm poster` 和 `routefilm render` 自动保留不可变运行目录，成品通过临时文件渲染并在检查通过后原子发布。用 `routefilm runs list --workspace .` 查看历史，用 `routefilm runs compare RUN_ID RUN_ID --output compare.jpg` 对比版本。

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
- [发布与社区传播素材](docs/launch-kit.md)
- [English README](README.en.md)

代码使用 MIT License；`docs/media/` 中的原创演示内容使用 CC BY 4.0。地图、字体、音频、生成素材与外部服务保留各自条款。使用 OSM 数据或瓦片时必须保留 `© OpenStreetMap contributors`，并遵守对应服务策略。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。
