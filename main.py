import os

from config import PDF_FOLDER, OUTPUT_FOLDER, OUTPUT_EXCEL
from extractor import extract_pdf_data
from table_extractor import mark_table_exists
from excel_writer import create_excel


def remove_duplicates(records):
    merged = {}

    for record in records:
        key = (
            record["source_file"],
            record["category"],
            record["page_no"]
        )

        if key not in merged:
            merged[key] = record
        else:
            if record["has_table"] == "有":
                merged[key]["has_table"] = "有"

    return list(merged.values())


def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    all_records = []

    for pdf_file in os.listdir(PDF_FOLDER):
        if not pdf_file.lower().endswith(".pdf"):
            continue

        pdf_path = os.path.join(PDF_FOLDER, pdf_file)

        print(f"\n===== {pdf_file} =====")

        records = extract_pdf_data(pdf_path)
        records = mark_table_exists(pdf_path, records)

        all_records.extend(records)

    all_records = remove_duplicates(all_records)

    all_records.sort(
        key=lambda x: (
            x["category_index"],
            x["source_file"],
            x["page_no"]
        )
    )

    create_excel(all_records, OUTPUT_EXCEL)

    print("\nExcel出力完了")
    print(f"保存先：{OUTPUT_EXCEL}")


if __name__ == "__main__":
    main()