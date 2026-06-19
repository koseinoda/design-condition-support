import os
import fitz
from config import CATEGORY_RULES, CATEGORY_ORDER


def make_short_summary(category, hit_keywords):
    kws = set(hit_keywords)

    if category.startswith("1."):
        return "適用基準・示方書に関するページ"

    if category.startswith("2."):
        if "コンクリート" in kws or "f'ck" in kws or "fck" in kws:
            return "コンクリート材料に関するページ"
        if "鉄筋" in kws:
            return "鉄筋材料に関するページ"
        if "鋼材" in kws:
            return "鋼材材料に関するページ"
        return "使用材料に関するページ"

    if category.startswith("3."):
        return "許容応力度に関するページ"

    if category.startswith("4."):
        return "ヤング係数・弾性係数に関するページ"

    if category.startswith("5."):
        if "活荷重" in kws:
            return "活荷重に関するページ"
        if "死荷重" in kws:
            return "死荷重に関するページ"
        if "土圧" in kws:
            return "土圧に関するページ"
        if "水圧" in kws:
            return "水圧に関するページ"
        if "地震荷重" in kws:
            return "地震荷重に関するページ"
        return "設計荷重に関するページ"

    if category.startswith("6."):
        return "構造解析方法に関するページ"

    if category.startswith("7."):
        return "構造一般図に関するページ"

    return "関連ページ"


def extract_pdf_data(pdf_path):
    records = []
    source_file = os.path.basename(pdf_path)

    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()

        if not text.strip():
            continue

        if page_num <= 2 and "目次" in text:
            continue

        for category_index, category in enumerate(CATEGORY_ORDER, start=1):
            keywords = CATEGORY_RULES[category]
            hit_keywords = [kw for kw in keywords if kw in text]

            if not hit_keywords:
                continue

            records.append({
                "category_index": category_index,
                "source_file": source_file,
                "source_path": pdf_path,
                "category": category,
                "page_no": page_num + 1,
                "page_num": page_num,
                "keywords": ", ".join(hit_keywords),
                "summary": make_short_summary(category, hit_keywords),
                "has_table": "無",
                "check": "未確認"
            })

    doc.close()
    return records