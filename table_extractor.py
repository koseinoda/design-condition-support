import pdfplumber


def mark_table_exists(pdf_path, records):
    target_pages = {
        record["page_num"]
        for record in records
        if record["source_path"] == pdf_path
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num in target_pages:
                if page_num < 0 or page_num >= len(pdf.pages):
                    continue

                page = pdf.pages[page_num]
                tables = page.extract_tables()

                if not tables:
                    continue

                for record in records:
                    if (
                        record["source_path"] == pdf_path
                        and record["page_num"] == page_num
                    ):
                        record["has_table"] = "有"

    except Exception as e:
        print(f"表確認エラー: {pdf_path} / {e}")

    return records