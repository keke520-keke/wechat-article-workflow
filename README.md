# 微信公众号半自动工作流

> AI写作 + Gemini生图 + 16套专业排版 → 一粘贴到135编辑器 → 公众号发布

## 快速开始

```bash
cd scripts
python generate_daily.py \
  --topic "年过四十如何养护脾胃" \
  --type "养生健康" \
  --input article.md \
  --images ./images/ \
  --output ./output/
```

输出两个HTML：
- `公众号文章-日期-内嵌版.html` → ⭐ 浏览器打开 → Ctrl+A → Ctrl+C → 135编辑器 Ctrl+V
- `公众号文章-日期-秀米粘贴版.html` → 轻量存档

## 工作流程

```
选题 → AI写作(Markdown) → Gemini生图(4张) → 排版渲染(16主题) → 内嵌版HTML → 粘贴135编辑器 → 公众号发布
```

详细文档见 [WORKFLOW.md](WORKFLOW.md)

## 主题配色

| 话题 | 主题 | 风格 |
|------|------|------|
| 养生健康 | sage-premium | 🟢 鼠尾草墨绿+象牙白 |
| 家庭情感 | warm-editorial | 🟤 栗色+米白+衬线体 |
| 实用技巧 | refined-blue | 🔵 专业蓝 |

> 共16套主题，见 `themes/` 目录

## 已验证结论

| 编辑器 | 粘贴保留样式 | 推荐 |
|--------|-------------|------|
| 秀米 XIUMI | ❌ 全部剥离 | 不推荐 |
| 135编辑器 | ✅ 完美保留 | ⭐ 推荐 |

## 目录结构

```
├── README.md
├── WORKFLOW.md                    # 完整流程文档
├── scripts/
│   ├── generate_daily.py          # 半自动生成器
│   └── html_converter.py          # Markdown → 微信HTML
├── themes/
│   ├── sage-premium.json          # 养生健康
│   ├── warm-editorial.json        # 家庭情感
│   └── refined-blue.json         # 实用技巧
├── config/
│   └── wechat-publisher.yaml.example
└── templates/
    └── article-template.md
```

## 依赖

```bash
pip install pyyaml
```

## 许可证

MIT
