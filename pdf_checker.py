import fitz


SPEC_CHECK_KEYWORDS = [
    "設計",
    "仕様書",
    "基準",
    "示方書",
    "材料",
    "使用材料",
    "荷重",
    "設計荷重",
    "許容応力度",
    "許容応力",
    "ヤング係数",
    "弾性係数",
    "構造解析",
    "構造一般図",
    "コンクリート",
    "鉄筋",
    "鋼材"
]


def check_spec_pdf(pdf_path):
    """
    PDFが設計仕様書らしいかを簡易判定する
    """

    hit_count = 0
    checked_text = ""

    try:
        doc = fitz.open(pdf_path)

        # 最初の5ページだけ確認
        max_pages = min(5, len(doc))

        for page_num in range(max_pages):
            page = doc[page_num]
            text = page.get_text()
            checked_text += text

        doc.close()

    except Exception as e:
        return {
            "is_spec": False,
            "hit_count": 0,
            "message": f"PDFを読み取れませんでした: {e}"
        }

    for keyword in SPEC_CHECK_KEYWORDS:
        if keyword in checked_text:
            hit_count += 1

    if hit_count >= 5:
        return {
            "is_spec": True,
            "hit_count": hit_count,
            "message": "設計仕様書の可能性が高いPDFです。"
        }

    elif hit_count >= 3:
        return {
            "is_spec": True,
            "hit_count": hit_count,
            "message": "仕様書の可能性がありますが、確認が必要です。"
        }

    else:
        return {
            "is_spec": False,
            "hit_count": hit_count,
            "message": "仕様書ではない可能性があります。"
        }