#!/usr/bin/env python3
"""
每日情报简报采集脚本
从 RSS 源读取，关键词过滤，推送到飞书
"""

import json
import os
import re
import urllib.request
import urllib.error
from datetime import datetime
from xml.etree import ElementTree

# ============================================================
# 配置
# ============================================================

FEISHU_WEBHOOK = os.environ.get("FEISHU_WEBHOOK", "")

# 直接 RSS 源（不依赖 RSSHub）
RSS_FEEDS = [
    # Tier 1：一手信息源
    {"name": "GitHub Trending", "url": "https://rsshub.app/github/trending/daily/any", "tier": 1},
    {"name": "Hacker News Best", "url": "https://hnrss.org/best", "tier": 1},
    {"name": "Hacker News New", "url": "https://hnrss.org/newest?q=AI+OR+LLM+OR+agent", "tier": 1},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed", "tier": 1},
    
    # Tier 2：技术社区
    {"name": "Reddit LLM", "url": "https://www.reddit.com/r/LocalLLaMA/.rss", "tier": 2},
    {"name": "Reddit ML", "url": "https://www.reddit.com/r/MachineLearning/.rss", "tier": 2},
    
    # Tier 2：技术博客
    {"name": "Simon Willison", "url": "https://simonwillison.net/atom/everything/", "tier": 2},
    
    # Tier 2：科技媒体
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "tier": 2},
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "tier": 2},
    {"name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/technology-lab", "tier": 2},
]

# 通过关键词
PASS_KEYWORDS = [
    "AI", "LLM", "Agent", "GPT", "Claude", "Gemini", "DeepSeek",
    "Cursor", "Copilot", "Windsurf", "Codex", "Qwen",
    "LangChain", "LlamaIndex", "n8n", "Dify",
    "OpenAI", "Anthropic", "Hugging", "Meta AI",
    "编程", "开发", "代码", "开发者", "框架", "SDK", "API",
    "IDE", "coding", "developer", "framework", "release", "update",
    "开源", "GitHub", "模型", "推理", "微调", "部署",
    "自动化", "工作流", "效率", "工具", "办公",
    "RAG", "MCP", "token", "prompt", "embedding",
    "workflow", "automation",
    "AI行业", "AI生态", "AI趋势", "AIGC", "大模型",
    "人工智能", "智能体", "机器学习", "深度学习",
    "商业化", "融资", "市场",
    "Qwen", "Llama", "Mistral", "Phi", "Grok",
    "Harness", "Docker", "Kubernetes", "deploy",
]

# 排除关键词
EXCLUDE_KEYWORDS = [
    "自媒体", "短视频", "直播", "带货", "情感", "职场鸡汤",
    "女性健康", "疗愈", "心灵成长", "博主", "停更",
    "涨粉", "流量", "变现", "内容创作", "内容运营",
    "IP运营", "超创", "漫剧", "职场现状", "薪酬",
    "孕产", "育儿", "婚姻", "护肤", "美妆", "穿搭", "减肥",
    # GitHub 相关排除（只保留 GitHub 上的 AI/开发项目）
    "GitHub down", "Github.com incident", "GitHub status",
    "Alternatives to GitHub", "GitHub outage",
    "Incident with Github", "GIMP Development",
    # 非技术排除
    "Health Coverage", "Universal Health", "Rare Books",
    "Amazon training", "watermark text", "Nvidia financing",
]

# ============================================================
# 核心函数
# ============================================================

def fetch_rss(url, timeout=10):
    """读取 RSS"""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (compatible; AI-Briefing/1.0)"
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except Exception as e:
        print(f"  ✗ 请求失败: {e}")
        return None


def parse_rss(xml_text):
    """解析 RSS/Atom"""
    items = []
    try:
        root = ElementTree.fromstring(xml_text)
        
        # RSS 2.0
        for item in root.iter("item"):
            title_el = item.find("title")
            link_el = item.find("link")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.text.strip() if link_el is not None and link_el.text else ""
            if title:
                items.append({"title": title, "link": link})
        
        # Atom
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.iter("{http://www.w3.org/2005/Atom}entry"):
            title_el = entry.find("{http://www.w3.org/2005/Atom}title")
            link_el = entry.find("{http://www.w3.org/2005/Atom}link")
            title = title_el.text.strip() if title_el is not None and title_el.text else ""
            link = link_el.get("href", "") if link_el is not None else ""
            if title:
                items.append({"title": title, "link": link})
    except Exception as e:
        print(f"  ✗ 解析失败: {e}")
    
    return items


def passes_filter(title):
    """过滤"""
    text = title.lower()
    
    for kw in EXCLUDE_KEYWORDS:
        if kw.lower() in text:
            return False
    
    for kw in PASS_KEYWORDS:
        if kw.lower() in text:
            return True
    
    return False


def dedup(items):
    """去重"""
    seen = []
    result = []
    for item in items:
        key = re.sub(r"[^\w]", "", item["title"].lower())[:25]
        if key not in seen:
            seen.append(key)
            result.append(item)
    return result


def format_message(items):
    """格式化飞书消息"""
    today = datetime.now().strftime("%Y-%m-%d")
    tier1 = [i for i in items if i.get("tier") == 1]
    tier2 = [i for i in items if i.get("tier") == 2]
    
    lines = [
        f"📊 每日情报简报 | {today}",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"采集 {len(items)} 条（一手 {len(tier1)} / 社区 {len(tier2)}）",
        "",
    ]
    
    if tier1:
        lines.append("🔴 一手源")
        for i, item in enumerate(tier1[:8], 1):
            lines.append(f"  {i}. {item['title']}")
            if item.get("link"):
                lines.append(f"     {item['link']}")
        lines.append("")
    
    if tier2:
        lines.append("🟠 社区/媒体")
        for i, item in enumerate(tier2[:8], 1):
            lines.append(f"  {i}. {item['title']}")
            if item.get("link"):
                lines.append(f"     {item['link']}")
        lines.append("")
    
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("数据源：GitHub, HN, PH, Reddit, Simon Willison, The Verge, TechCrunch")
    lines.append(f"生成时间：{datetime.now().strftime('%H:%M')}")
    
    return "\n".join(lines)


def send_feishu(webhook_url, message):
    """推送到飞书"""
    if not webhook_url:
        print("⚠️  未配置 FEISHU_WEBHOOK，仅打印")
        print(message)
        return False
    
    data = json.dumps({
        "msg_type": "text",
        "content": {"text": message}
    }).encode("utf-8")
    
    try:
        req = urllib.request.Request(webhook_url, data=data,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode())
            print(f"✅ 飞书推送: {result}")
            return True
    except Exception as e:
        print(f"❌ 飞书推送失败: {e}")
        return False


# ============================================================
# 主流程
# ============================================================

def main():
    print(f"🚀 开始采集 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"📋 RSS 源: {len(RSS_FEEDS)} 个")
    print()
    
    all_items = []
    
    for feed in RSS_FEEDS:
        print(f"📡 [{feed['name']}]")
        
        xml_text = fetch_rss(feed["url"])
        if not xml_text:
            continue
        
        items = parse_rss(xml_text)
        print(f"  → 解析 {len(items)} 条")
        
        passed = []
        for item in items:
            if passes_filter(item["title"]):
                item["tier"] = feed["tier"]
                item["source"] = feed["name"]
                passed.append(item)
        
        print(f"  → 过滤后 {len(passed)} 条")
        all_items.extend(passed)
    
    all_items = dedup(all_items)
    print(f"\n📊 去重后 {len(all_items)} 条")
    
    message = format_message(all_items)
    send_feishu(FEISHU_WEBHOOK, message)
    
    # 保存数据
    os.makedirs("data", exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    with open(f"data/{today}.json", "w", encoding="utf-8") as f:
        json.dump({
            "date": today,
            "total": len(all_items),
            "items": all_items,
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 完成")


if __name__ == "__main__":
    main()
