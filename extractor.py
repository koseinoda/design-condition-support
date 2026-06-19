import os
import io

import fitz
import pytesseract
from PIL import Image

from config import CATEGORY_RULES, CATEGORY_ORDER


TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def get_text_with_ocr(page):
    """
    文字が取れない画像PDFページをOCRで文字化する
    """

    try:
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        text = pytesseract.image_to_string(
            img,
            lang="jpn+eng"
        )

        return text

    except Exception as e:
        print(f"OCR失敗：{e}")
        return ""


def get_page_text(page):
    """
    通常の文字抽出を優先し、文字が少ない場合はOCRに切り替える
    """

    text = page.get_text()

    if len(text.strip()) >= 30:
        return text, "text"

    ocr_text = get_text_with_ocr(page)
    return ocr_text, "ocr"


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

    print(f"\n===== 抽出開始：{source_file} =====")

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"PDFを開けませんでした：{e}")
        return records

    total_pages = len(doc)
    print(f"総ページ数：{total_pages}")

    for page_num in range(total_pages):
        page = doc[page_num]
        page_no = page_num + 1

        text, method = get_page_text(page)
        text_length = len(text.strip())

        print(f"{page_no}ページ：文字数 {text_length} / 方法：{method}")

        if not text.strip():
            continue

        if page_num <= 2 and "目次" in text:
            print(f"{page_no}ページ：目次のためスキップ")
            continue

        for category_index, category in enumerate(CATEGORY_ORDER, start=1):
            keywords = CATEGORY_RULES[category]

            hit_keywords = [
                kw for kw in keywords
                if kw in text
            ]

            if hit_keywords:
                print(f"  ヒット：{category} / {page_no}ページ / {hit_keywords}")

            if not hit_keywords:
                continue

            records.append({
                "category_index": category_index,
                "source_file": source_file,
                "source_path": pdf_path,
                "category": category,
                "page_no": page_no,
                "page_num": page_num,
                "keywords": ", ".join(hit_keywords),
                "summary": make_short_summary(category, hit_keywords),
                "has_table": "無",
                "check": "未確認"
            })

    doc.close()

    print(f"抽出完了：{source_file} / {len(records)}件抽出")
    print("====================================\n")

    return records