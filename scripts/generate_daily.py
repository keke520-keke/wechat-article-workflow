#!/usr/bin/env python3
"""
公众号文章半自动生成器（个人订阅号专用）

流程（全自动部分）:
  1. 接收选题 → 生成文章 Markdown
  2. 控制浏览器让 Gemini 生图 → 下载配图
  3. Markdown → 微信富文本 HTML（16套主题，多色高亮）
  4. 配图 base64 内嵌 → 一个 HTML 文件搞定
  5. 保存到当日文件夹

用户只需:
  1. 打开生成的 HTML 文件
  2. Ctrl+A 全选 → Ctrl+C 复制
  3. 粘贴到 135编辑器
  4. 点「复制使用」→ 粘贴到公众号后台

用法:
  python generate_daily.py --topic "年过四十如何养护脾胃" --type 养生健康
  python generate_daily.py --topic "中年夫妻相处之道" --type 中年家庭情感
  python generate_daily.py --topic "手机充电省电技巧" --type 生活实用技巧
"""

import sys, os, json, re, base64, argparse, subprocess
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
OUTPUT_BASE = Path.home() / "Desktop" / "文件管理" / "公众号"

# ── 配置 ──────────────────────────────────────

TOPIC_THEME_MAP = {
    "养生健康": "sage-premium",
    "中年家庭情感": "warm-editorial",
    "生活实用技巧": "refined-blue",
}

ARTICLE_SPECS = {
    "养生健康": {
        "voice": "科学科普，平实走心，卫健委/三甲医院科普逻辑，拒绝神医偏方",
        "min_words": 850, "max_words": 1050,
        "sections": "4～6小节，单段≤4行",
        "images": 4,
    },
    "中年家庭情感": {
        "voice": "落地真实生活，聚焦夫妻相处/子女教育/养老思考/人情世故，杜绝空洞鸡汤",
        "min_words": 850, "max_words": 1050,
        "sections": "4～6小节",
        "images": 4,
    },
    "生活实用技巧": {
        "voice": "社保医保/手机使用/居家窍门/防诈骗/家务省钱，步骤清晰一看就会",
        "min_words": 850, "max_words": 1050,
        "sections": "4～6小节",
        "images": 4,
    },
}

def log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    icons = {"INFO": "[*]", "OK": "[OK]", "WARN": "[!!]", "ERR": "[XX]", "STEP": ">>>"}
    try:
        print(f"{icons.get(level, '•')} [{ts}] {msg}")
    except UnicodeEncodeError:
        print(f"[{level}] [{ts}] {msg.encode('ascii', errors='replace').decode('ascii')}")

# ── 阶段1: 排版渲染 ────────────────────────────

def render_markdown_to_html(md_path, topic_type, output_dir):
    """将 Markdown 渲染为微信兼容 HTML"""
    sys.path.insert(0, str(SCRIPT_DIR))
    from html_converter import convert_markdown_to_wechat_html, load_theme

    theme = TOPIC_THEME_MAP.get(topic_type, "sage-premium")
    log(f"排版主题: {theme}", "STEP")

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    styles, highlights, divider, list_style = load_theme(theme_name=theme)
    html_body = convert_markdown_to_wechat_html(
        md_content, styles=styles, highlights=highlights,
        divider_text=divider, list_style=list_style
    )
    log(f"HTML 渲染完成 ({len(html_body)} 字符)", "OK")
    return html_body, theme

# ── 阶段2: 配图嵌入 ────────────────────────────

def embed_images(html_body, image_dir, image_map):
    """将本地图片以 base64 嵌入 HTML"""
    log("嵌入配图...", "STEP")

    for alt_text, filename in image_map.items():
        img_path = os.path.join(image_dir, filename)
        if not os.path.exists(img_path):
            log(f"图片缺失: {filename}", "WARN")
            continue

        with open(img_path, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode('utf-8')
        data_uri = f"data:image/png;base64,{b64}"

        pattern = f'<img src="[^"]*" alt="{alt_text}"[^>]*>'
        replacement = f'<img src="{data_uri}" alt="{alt_text}" style="max-width:100%;height:auto;display:block;margin:24px auto;">'
        html_body = re.sub(pattern, replacement, html_body, count=1)
        log(f"  {filename} → base64 ({len(b64)//1024}KB)")

    return html_body

# ── 阶段3: 生成最终 HTML ───────────────────────

def build_final_html(html_body, title, topic_type, theme_name):
    """包装成完整 HTML 文档"""
    theme_colors = {
        "sage-premium": ("#1e2a21", "#f7f5ee", "#8a9580"),
        "warm-editorial": ("#5a2f1a", "#fbf7f0", "#9c8877"),
        "refined-blue": ("#0b1530", "#ffffff", "#8a93a8"),
    }
    title_color, bg_color, subtitle_color = theme_colors.get(theme_name, ("#333", "#fff", "#999"))

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<title>{title}</title>
</head>
<body style="margin:0;padding:0;background:{bg_color};">
<div style="max-width:677px;margin:0 auto;padding:28px 22px 0;">
  <h1 style="font-size:22px;font-weight:800;color:{title_color};text-align:center;margin:0 0 6px;padding:0;letter-spacing:1px;line-height:1.5;">{title}</h1>
  <p style="text-align:center;color:{subtitle_color};font-size:13px;margin:0 0 24px;">每日一篇 · 贴近生活 · 科学养护</p>
</div>
<div class="article-body" style="max-width:677px;margin:0 auto;padding:0 22px;">
{html_body}
</div>
<div style="max-width:677px;margin:0 auto;padding:20px 22px 40px;text-align:center;">
  <p style="color:{subtitle_color};font-size:12px;margin:0;">— 如果觉得有用，欢迎转发给身边的朋友 —</p>
</div>
</body>
</html>'''

# ── 阶段4: 轻量版（图片占位）─────

def build_light_html(html_body, title, topic_type, theme_name, image_dir, image_map):
    """生成保留图片引用的轻量版 HTML"""
    for alt_text, filename in image_map.items():
        data_pattern = f'<img src="data:image/png;base64,[^"]*" alt="{alt_text}"[^>]*>'
        replacement = f'<img src="{filename}" alt="{alt_text}" style="max-width:100%;height:auto;display:block;margin:24px auto;">'
        html_body = re.sub(data_pattern, replacement, html_body)

    return build_final_html(html_body, title, topic_type, theme_name)

# ── 主流程 ────────────────────────────────────

def run_semi_auto(topic, topic_type, md_path=None, image_dir=None, output_dir=None):
    """半自动生成公众号文章。"""
    today = datetime.now().strftime("%Y-%m-%d")
    if not output_dir:
        output_dir = OUTPUT_BASE / today
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    log(f"半自动生成开始", "STEP")
    log(f"  选题: {topic}")
    log(f"  类型: {topic_type}")
    log(f"  输出: {output_dir}")

    if md_path and os.path.exists(md_path):
        log(f"使用已有 Markdown: {md_path}", "OK")
    else:
        log("需要先生成 Markdown（通过 Claude Code 对话完成）", "WARN")
        return {"status": "need_markdown", "output_dir": str(output_dir)}

    if not image_dir:
        image_dir = output_dir
    pngs = list(Path(image_dir).glob("配图*.png"))
    if len(pngs) < 4:
        log(f"配图不足 ({len(pngs)}/4)，需要通过 Gemini 生成", "WARN")

    html_body, theme = render_markdown_to_html(md_path, topic_type, output_dir)

    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    title_match = re.search(r'^##\s+(.+)$', md_content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else topic

    image_map = {}
    for i, png in enumerate(sorted(pngs), 1):
        alt_pattern = re.compile(r'!\[(配图[^\]]*)\]')
        alts = alt_pattern.findall(md_content)
        if i <= len(alts):
            image_map[alts[i-1]] = png.name

    if not image_map:
        for i, png in enumerate(sorted(pngs), 1):
            image_map[f"配图{['一','二','三','四'][i-1]}"] = png.name

    html_full = embed_images(html_body, str(image_dir), image_map)
    final_path = output_dir / f"公众号文章-{today}-内嵌版.html"
    final_html = build_final_html(html_full, title, topic_type, theme)
    with open(final_path, 'w', encoding='utf-8') as f:
        f.write(final_html)
    log(f"内嵌版: {final_path} ({len(final_html)//1024}KB)", "OK")

    light_path = output_dir / f"公众号文章-{today}-秀米粘贴版.html"
    light_html = build_light_html(html_full, title, topic_type, theme, str(image_dir), image_map)
    with open(light_path, 'w', encoding='utf-8') as f:
        f.write(light_html)
    log(f"轻量版: {light_path} ({len(light_html)//1024}KB)", "OK")

    summary = f"""# {title}

- 选题类型: {topic_type}
- 排版主题: {theme}
- 生成日期: {today}
- 内嵌版: {final_path.name}
- 配图: {len(pngs)} 张

## 使用步骤
1. 打开内嵌版 → 浏览器中查看
2. Ctrl+A 全选 → Ctrl+C 复制
3. 打开 135编辑器 → Ctrl+V 粘贴
4. 点「复制使用」→ 粘贴到公众号后台
"""
    summary_path = output_dir / "README.md"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(summary)

    log(f"=== 半自动生成完成！", "OK")
    log(f"   内嵌预览版: {final_path.name}", "INFO")
    log(f"   轻量引用版: {light_path.name}", "INFO")
    log(f"现在只需: 打开内嵌版 → 全选 → 复制 → 135粘贴 → 完成!", "INFO")

    return {
        "status": "success", "output_dir": str(output_dir),
        "final_html": str(final_path), "light_html": str(light_path),
        "md_path": md_path, "images": len(pngs), "theme": theme,
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='公众号半自动生成器')
    parser.add_argument('--topic', required=True, help='选题描述')
    parser.add_argument('--type', choices=['养生健康','中年家庭情感','生活实用技巧'],
                       default='养生健康')
    parser.add_argument('--input', help='已有 Markdown 文件路径')
    parser.add_argument('--images', help='配图目录')
    parser.add_argument('--output', help='输出目录')

    args = parser.parse_args()

    result = run_semi_auto(
        topic=args.topic, topic_type=args.type,
        md_path=args.input, image_dir=args.images, output_dir=args.output,
    )

    if result.get('status') == 'need_markdown':
        print("\nWARNING: 请先在 Claude Code 对话中让 AI 写好文章，保存为 .md 文件，然后重新运行。")
        sys.exit(1)
