# 📊 AI 每日情报简报

基于 GitHub Actions + RSSHub 的免费每日情报采集系统。

## 原理

```
GitHub Actions（每天 07:30 自动触发）
  → RSSHub 公共实例（读取 12 个 RSS 源）
  → Python 脚本（关键词过滤 + 去重）
  → 飞书 Webhook（推送到飞书群）
```

**完全免费，不需要服务器，不需要 AI token。**

## 快速开始

### 1. Fork 本仓库

点击右上角 Fork，把仓库复制到你的 GitHub 账号下。

### 2. 配置飞书 Webhook

1. 飞书 → 群设置 → 群机器人 → 添加机器人 → 自定义机器人
2. 复制 Webhook URL
3. GitHub → 仓库 → Settings → Secrets and variables → Actions → New repository secret
4. 名称：`FEISHU_WEBHOOK`
5. 值：粘贴 Webhook URL

### 3. 启用 Actions

GitHub → 仓库 → Actions → 启用 workflows

### 4. 手动测试

Actions → 每日情报简报 → Run workflow → Run

### 5. 完成

每天 07:30（北京时间）自动运行，推送到飞书群。

## RSS 源

| 来源 | 层级 | 说明 |
|------|------|------|
| GitHub Trending | Tier 1 | 每日热门项目 |
| Hacker News | Tier 1 | 技术社区热帖 |
| Product Hunt | Tier 1 | 新产品发布 |
| 少数派 | Tier 2 | 效率/科技文章 |
| 掘金 | Tier 2 | 开发者社区 |
| 阮一峰 | Tier 2 | 技术博客 |
| Reddit LLM | Tier 2 | LocalLLaMA 社区 |
| Reddit ML | Tier 2 | MachineLearning 社区 |
| V2EX | Tier 2 | 技术论坛 |
| The Verge | Tier 2 | 科技媒体 |
| TechCrunch | Tier 2 | 科技媒体 |
| Ars Technica | Tier 2 | 科技媒体 |

## 过滤规则

**通过关键词：** AI, LLM, Agent, Cursor, Copilot, Claude, DeepSeek, 编程, 开发, 框架, 工具, 自动化, ...

**排除关键词：** 自媒体, 短视频, 直播, 职场鸡汤, 女性健康, ...

**排除域名：** CSDN, 百家号, 搜狐, ...

## 自定义

编辑 `scripts/collect.py` 修改：
- `RSS_FEEDS`：添加/删除 RSS 源
- `PASS_KEYWORDS`：修改通过关键词
- `EXCLUDE_KEYWORDS`：修改排除关键词
- `RSSHUB_INSTANCES`：更换 RSSHub 实例

## 本地测试

```bash
python3 scripts/collect.py
```

## 和 AI Skill 的关系

| | GitHub Actions（本方案） | AI Skill |
|---|---|---|
| 费用 | 免费 | 消耗 AI token |
| 智能程度 | 关键词过滤 | AI 理解内容 |
| 个性化 | 固定规则 | 画像匹配、反馈驱动 |
| 适合 | 每日基础覆盖 | 深度分析、周报 |

**推荐：两套并行**
- GitHub Actions：每天推基础信息（免费）
- AI Skill：每周跑一次深度分析（省 token）
