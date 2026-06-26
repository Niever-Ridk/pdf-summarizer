# PDF Summarizer — ZCode Skill

Extract text from PDFs and generate **structured, conclusion-verified** summaries — all in Chinese (user language matched automatically).

📄 Drop a PDF path → get a clean, layered summary with tables, pull-quotes, and a one-liner gist.

## Quick Start

Install the skill by placing this directory under any ZCode discovery path:

```bash
# User-level (available in all projects)
cp -r pdf-summarizer ~/.agents/skills/

# Or project-level
cp -r pdf-summarizer <project>/.agents/skills/
```

ZCode auto-discovers it. Then just say:

```
总结一下这个 PDF
帮我看看 C:\docs\paper.pdf 讲了什么
读一下这个文件
```

## Core Features

| Feature | Description |
|---------|-------------|
| 🔍 **Zero-setup** | Auto-installs `pdfplumber` on first run — no manual pip needed |
| 📏 **Smart routing** | ≤5 pages → full-text summary; >5 pages → conclusion-section locator |
| 🎯 **Conclusion locator** | `--locate-summary` scans full text, pinpoints "本章小结 / Conclusions / Summary" paragraphs, **filters out TOC entries** |
| 🚫 **No blind truncation** | Long documents are never head-truncated (conclusions live at the end) |
| ✅ **Abstract ≠ Conclusion** | Specific claims must be verified against chapter summaries — not the abstract alone |
| 🖼️ **Scanned PDF detection** | Detects image-only PDFs and suggests OCR routes |

## Standalone Script Usage

```bash
# Basic extraction
python scripts/extract_pdf.py paper.pdf

# Long documents (thesis/report): locate conclusion sections
python scripts/extract_pdf.py paper.pdf --locate-summary

# Custom segment length
python scripts/extract_pdf.py paper.pdf --locate-summary --segment-chars 1000

# Short documents: optional truncation
python scripts/extract_pdf.py short.pdf --max-chars 6000
```

### Script Output (JSON)

```json
{
  "status": "success",
  "total_pages": 68,
  "total_chars": 49204,
  "text": "...(full text)...",
  "per_page": [{"page": 1, "chars": 131}, ...],
  "summary_segments": [
    {"keyword": "本章小结", "pos": 21530, "text": "..."},
    {"keyword": "研究总结", "pos": 45133, "text": "..."},
    {"keyword": "工作展望", "pos": 46308, "text": "..."}
  ]
}
```

## Two Iron Rules (Why This Skill Exists)

1. **Never head-truncate long PDFs.** Conclusions are always at the end. Truncating from the top = losing all conclusions = guessing from the abstract alone.

2. **Chapter summaries beat the abstract.** Abstracts condense for brevity — they may contradict chapter-level details. Specific claims (best parameter, exact value, ranking) must be verified against in-text chapter summaries.

> Real accident: a 68-page thesis was head-truncated to 12,000 chars, losing all 5 chapter summaries + the final conclusion chapter. The summary writer then claimed "negative angle is optimal" — the actual conclusion was "0° is optimal."

## Summary Format

```
# 📄 Summary: 《Document Title》

## Core Theme
(2-4 sentences — what is this, what problem does it solve, who is it for?)

## Structured Breakdown
### Point One
- bullets, tables, pull-quotes
| Param | Optimal | Worst |
|--------|--------|------|

> Key takeaway in a quote block

## One-Line Gist
> The entire document distilled into one sentence.

## Next Steps (optional)
- Export to Word/PDF? Mind map? Deep-dive into a specific section?
```

## Dependencies

- Python 3.8+
- `pdfplumber` (auto-installed by the script)

## Directory Structure

```
pdf-summarizer/
├── SKILL.md              ← ZCode Skill definition (workflow + format spec)
├── README.md             ← 中文说明
├── README_EN.md          ← English readme (this file)
├── .gitignore
└── scripts/
    └── extract_pdf.py    ← Self-contained extraction + conclusion locator
```

## License

MIT
