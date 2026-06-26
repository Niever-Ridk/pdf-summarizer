#!/usr/bin/env python
"""PDF 文本提取与结论性章节定位脚本。

用法:
    python extract_pdf.py <pdf_path>                        # 仅提取全文
    python extract_pdf.py <pdf_path> --locate-summary       # 全文 + 自动定位各章小结/结论段
    python extract_pdf.py <pdf_path> --locate-summary --segment-chars 800
    python extract_pdf.py <pdf_path> --max-chars N          # 截断全文(仅短文档用,长文档慎用)

输出 JSON 字段:
    status            : "success" / "scanned" / "error"
    total_pages       : 总页数
    total_chars       : 总字符数
    text              : 全文(或前 N 字符,仅当 --max-chars)
    per_page          : [{page, chars}] 每页字符统计
    summary_segments  : [{keyword, pos, text}] 仅 --locate-summary 时存在;
                        已过滤目录项,每段取关键词后 segment_chars 字符

设计要点:
- 自包含:首次运行自动 pip install --user pdfplumber,无需管理员
- 跨平台:用 sys.executable 调 pip,避免 python/python3 歧义(Windows 无 python3)
- 容错:识别扫描件(平均每页<50字)、损坏文件,给出后续建议
- 结论定位(关键):多页论文/报告必须靠正文小结核对结论,不能只看摘要。
  摘要常为求凝练而与正文细节甚至方向性结论不符。--locate-summary 用内置
  结论关键词扫描全文,自动跳过目录项(关键词后紧跟连续点号+页码的行是目录,
  非正文),返回每个正文小结/结论章节的原文片段,供总结时逐条核对。
"""

import json
import re
import subprocess
import sys


# 结论性章节关键词,按优先级排序(越具体越靠前)。"本章小结"优先于泛化的"小结/总结",
# 这样同一段落会被识别为更具体的标题,避免重复命中。
SUMMARY_KEYWORDS = [
    "本章小结",
    "小结",
    "研究总结",
    "工作总结",
    "总结与展望",
    "主要结论",
    "研究结论",
    "结论与展望",
    "结论",
    "总结",
    "工作展望",
    "展望",
    "Conclusions",
    "Conclusion",
    "Summary",
    "conclusions",
    "conclusion",
    "summary",
]

# 目录项特征:关键词后窗口内出现连续点号(≥3),或点号+空白+页码。
# 形如 "第三章 主燃孔角度对温度分布的影响....................20"
_TOC_PATTERN = re.compile(r"\.{3,}|\.{2,}\s*\d+\s*$")

# 单字关键词(易误报):"总结""结论""展望"等单独成词时,极可能是正文中的
# "综合来看……的研究""……结论之上""展望,2015(期刊年份)"等噪声。
# 约束:这类关键词必须是章节标题——即位于行首(前面是换行或文档开头),
# 且同行剩余部分较短(标题行通常 <40 字符,正文段落会长得多)。
_SHORT_KEYWORDS = {"总结", "结论", "展望", "小结", "Summary", "summary", "Conclusion", "conclusion"}
_TITLE_MAX_LINE_LEN = 40  # 标题所在行最大字符数(含关键词本身)


def _is_title_position(full_text, idx, kw):
    """对短关键词,要求它位于行首且所在行是短行(标题特征)。长关键词(本章小结/
    研究总结/工作展望/结论与展望等)直接视为标题,不额外约束。"""
    if kw not in _SHORT_KEYWORDS:
        return True
    # 检查是否在行首:前一个字符是换行或文档开头
    if idx > 0 and full_text[idx - 1] not in "\n":
        return False
    # 所在行(到下一个换行)的长度
    nl = full_text.find("\n", idx)
    line = full_text[idx: nl if nl >= 0 else len(full_text)]
    return len(line.strip()) <= _TITLE_MAX_LINE_LEN


def ensure_pdfplumber():
    """确保 pdfplumber 可用,缺失则自动安装到用户目录。返回 (ok, note)。"""
    try:
        import pdfplumber  # noqa: F401
        return True, ""
    except ImportError:
        pass
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--user", "-q", "pdfplumber"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import pdfplumber  # noqa: F401
        return True, "auto-installed pdfplumber"
    except Exception as e:
        return False, f"pip install pdfplumber failed: {e}"


def extract_text(pdf_path):
    """逐页提取文本。返回 (拼接全文, per_page, 总页数)。"""
    import pdfplumber
    pages_text = []
    per_page = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            txt = page.extract_text() or ""
            pages_text.append(txt)
            per_page.append({"page": i, "chars": len(txt)})
    return "\n\n".join(pages_text), per_page, total_pages


def locate_summary_segments(full_text, segment_chars=700):
    """在全文中定位结论性章节,过滤目录项,区间去重。

    返回 [{keyword, pos, text}],按文中出现顺序排序。
    去重逻辑:多个关键词(如"结论"与"研究总结")命中同一段落时,
    只保留先匹配到的(优先级由 SUMMARY_KEYWORDS 顺序决定)。
    """
    segments = []
    seen_ranges = []  # [(start, end)] 已占用区间

    def overlaps(start, length):
        end = start + length
        return any(not (end <= s or start >= e) for s, e in seen_ranges)

    for kw in SUMMARY_KEYWORDS:
        start = 0
        while True:
            idx = full_text.find(kw, start)
            if idx < 0:
                break
            window = full_text[idx: idx + 120]
            if _TOC_PATTERN.search(window):
                # 目录项,跳过
                start = idx + len(kw)
                continue
            if not _is_title_position(full_text, idx, kw):
                # 短关键词但不是标题位置(正文里的"总结/结论/展望"),跳过
                start = idx + len(kw)
                continue
            seg_len = len(kw) + segment_chars
            if overlaps(idx, seg_len):
                # 与已定位段重叠,跳过
                start = idx + len(kw)
                continue
            segments.append({
                "keyword": kw,
                "pos": idx,
                "text": full_text[idx: idx + segment_chars],
            })
            seen_ranges.append((idx, idx + seg_len))
            start = idx + len(kw)

    segments.sort(key=lambda s: s["pos"])
    return segments


def main():
    if len(sys.argv) < 2:
        print(json.dumps({
            "status": "error",
            "note": "usage: extract_pdf.py <pdf_path> [--locate-summary] "
                    "[--segment-chars N] [--max-chars N]",
        }))
        sys.exit(1)

    pdf_path = sys.argv[1]
    locate = "--locate-summary" in sys.argv
    max_chars = None
    if "--max-chars" in sys.argv:
        max_chars = int(sys.argv[sys.argv.index("--max-chars") + 1])
    segment_chars = 700
    if "--segment-chars" in sys.argv:
        segment_chars = int(sys.argv[sys.argv.index("--segment-chars") + 1])

    ok, note = ensure_pdfplumber()
    if not ok:
        print(json.dumps({"status": "error", "note": note}))
        sys.exit(1)

    try:
        full_text, per_page, total_pages = extract_text(pdf_path)
    except Exception as e:
        print(json.dumps({"status": "error", "note": f"extraction failed: {e}"}))
        sys.exit(1)

    total_chars = len(full_text)
    avg = total_chars / max(total_pages, 1)

    # 扫描件启发式:平均每页 <50 字符
    if avg < 50:
        result = {
            "status": "scanned",
            "total_pages": total_pages,
            "total_chars": total_chars,
            "text": full_text[:2000],
            "per_page": per_page,
            "note": (
                "Likely a scanned/image-based PDF (avg {0:.0f} chars/page). "
                "Suggest OCR first (ocrmypdf / Tesseract), or render pages to "
                "images and read them with the Read tool."
            ).format(avg),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(2)

    result = {
        "status": "success",
        "total_pages": total_pages,
        "total_chars": total_chars,
        "text": full_text,
        "per_page": per_page,
    }
    if note:
        result["note"] = note
    if max_chars is not None:
        result["text"] = full_text[:max_chars]
    if locate:
        result["summary_segments"] = locate_summary_segments(full_text, segment_chars)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
