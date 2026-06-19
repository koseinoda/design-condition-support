import os
import fitz


SPEC_CHECK_KEYWORDS = [
    "設計",
    "仕様書",
    "設計仕様書",
    "特記仕様書",
    "基準",
    "基準書",
    "示方書",
    "標準",
    "準拠",

    "適用示方書",
    "使用材料",
    "材料",
    "許容応力度",
    "許容応力",
    "応力度",
    "ヤング係数",
    "弾性係数",
    "設計荷重",
    "荷重",
    "構造解析",
    "解析",
    "構造一般図",

    "土木",
    "土木関係",
    "鉄道",
    "地下鉄",
    "地下高速電車",
    "鉄道構造物",
    "コンクリート",
    "鉄筋",
    "鋼材",
    "鋼構造",
    "RC",
    "耐震",
    "地震",
    "土圧",
    "水圧",
    "活荷重",
    "死荷重"
]


def check_spec_pdf(pdf_path):
    """
    PDFが設計仕様書らしいかを簡易判定する
    """

    hit_keywords = []
    checked_text = ""

    try:
        doc = fitz.open(pdf_path)

        total_pages = len(doc)
        check_pages = set()

        for i in range(min(10, total_pages)):
            check_pages.add(i)

        if total_pages > 10:
            check_pages.add(total_pages // 2)

        if total_pages > 20:
            check_pages.add(total_pages - 1)
            check_pages.add(max(total_pages - 2, 0))

        for page_num in sorted(check_pages):
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

    # ファイル名にも仕様書系ワードが入ることがあるため、判定対象に含める
    file_name = os.path.basename(pdf_path)
    check_target = checked_text + " " + file_name

    for keyword in SPEC_CHECK_KEYWORDS:
        if keyword in check_target:
            hit_keywords.append(keyword)

    hit_count = len(hit_keywords)

    if "仕様書" in check_target and hit_count >= 2:
        return {
            "is_spec": True,
            "hit_count": hit_count,
            "message": "設計仕様書の可能性が高いPDFです。"
        }

    if hit_count >= 5:
        return {
            "is_spec": True,
            "hit_count": hit_count,
            "message": "設計仕様書の可能性が高いPDFです。"
        }

    elif hit_count >= 2:
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