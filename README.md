# PDF Summarizer — ZCode Skill

[English version →](README_EN.md) | [GitHub Repo](https://github.com/Niever-Ridk/pdf-summarizer)

从 PDF 文件中提取文本并生成结构化中文总结的 **ZCode Skill**。

📄 给一个 PDF 路径 → 产出一篇层次清晰、重点突出、**结论可靠**的结构化总结。

## 触发方式

```
/总结这个PDF
这个文件讲了什么
帮我提炼一下 C:\docs\论文.pdf
读一下这个文件
```

## 核心能力

| 能力 | 说明 |
|------|------|
| 🔍 **自动依赖安装** | 首次运行自动 `pip install pdfplumber`，无需手动配置 |
| 📏 **体量分流** | ≤5 页直接全文总结；>5 页自动定位结论性章节 |
| 🎯 **结论定位引擎** | `--locate-summary` 扫描全文，精准定位"本章小结/结论/研究总结"段落，**过滤目录项** |
| 🚫 **防截断保护** | 长文档禁止从头部截断（结论永远在文档后部） |
| ✅ **摘要≠结论** | 具体数据/结论以正文小结原文为准，不凭空泛化 |
| 🖼️ **扫描件识别** | 检测纯图片 PDF，提示 OCR 方案 |

## 安装（ZCode 用户）

```bash
# 将整个目录放到 ZCode 的 skills 路径之一：
#   ~/.agents/skills/pdf-summarizer/
# 或 <project>/.agents/skills/pdf-summarizer/
```

ZCode 会自动发现并加载。

## 手工使用提取脚本

```bash
# 基本提取
python scripts/extract_pdf.py paper.pdf

# 长文档（论文/报告）：定位结论章节
python scripts/extract_pdf.py paper.pdf --locate-summary

# 自定义结论段长度
python scripts/extract_pdf.py paper.pdf --locate-summary --segment-chars 1000

# 短文档：可截断
python scripts/extract_pdf.py short.pdf --max-chars 6000
```

## 依赖

- Python 3.8+
- `pdfplumber`（脚本自动安装）

## 目录结构

```
pdf-summarizer/
├── SKILL.md              ← ZCode Skill 主文件（工作流 + 格式规范）
├── README.md             ← 本文件
└── scripts/
    └── extract_pdf.py    ← PDF 提取与结论定位脚本（自包含）
```

## 总结格式示例

```
# 📄 文档总结：《文章标题》

## 核心主题
（2-4 句说清这是什么、讨论什么问题）

## 正文分点
### 要点一
- 简短描述
- | 表格 | 对比 | ...

> 点睛金句

## 一句话主旨
> 全文最凝练的概括

## 后续建议
- 导出为文档 / 做成思维导图 / ……
```

## License

MIT
