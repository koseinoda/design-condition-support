import os
import io

import fitz
import streamlit as st
from PIL import Image

from config import PDF_FOLDER, OUTPUT_FOLDER, OUTPUT_EXCEL, CATEGORY_ORDER
from extractor import extract_pdf_data
from table_extractor import mark_table_exists
from excel_writer import create_excel
from pdf_checker import check_spec_pdf


st.set_page_config(
    page_title="設計条件書作成支援システム",
    layout="wide"
)

st.title("設計条件書作成支援システム")
st.write("仕様書PDFをアップロードすると、7項目ごとに該当ページを抽出します。")

os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


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


def show_pdf_page_as_image(pdf_path, page_no):
    try:
        doc = fitz.open(pdf_path)
        page_index = page_no - 1

        if page_index < 0 or page_index >= len(doc):
            st.error("指定ページが見つかりません。")
            doc.close()
            return

        page = doc[page_index]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img = Image.open(io.BytesIO(pix.tobytes("png")))

        st.image(img, use_container_width=True)
        doc.close()

    except Exception as e:
        st.error(f"PDF表示中にエラーが発生しました：{e}")


uploaded_files = st.file_uploader(
    "仕様書PDFをアップロードしてください",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    st.success(f"{len(uploaded_files)}件のPDFが選択されました。")

    if st.button("解析開始"):

        st.session_state.pop("selected_pdf", None)
        st.session_state.pop("selected_page", None)
        st.session_state.pop("records", None)
        st.session_state.pop("pdf_paths", None)

        for file in os.listdir(PDF_FOLDER):
            file_path = os.path.join(PDF_FOLDER, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        saved_pdf_paths = []
        skipped_files = []

        for uploaded_file in uploaded_files:
            save_path = os.path.join(PDF_FOLDER, uploaded_file.name)

            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            check_result = check_spec_pdf(save_path)

            if check_result["is_spec"]:
                st.info(
                    f"{uploaded_file.name}: {check_result['message']}（一致数：{check_result['hit_count']}）"
                )
                saved_pdf_paths.append(save_path)
            else:
                st.warning(
                    f"{uploaded_file.name}: {check_result['message']}（一致数：{check_result['hit_count']}）"
                )
                skipped_files.append(uploaded_file.name)

        if skipped_files:
            st.warning("以下のPDFは仕様書ではない可能性があるため、解析対象から除外しました。")
            for skipped in skipped_files:
                st.write(f"- {skipped}")

        if not saved_pdf_paths:
            st.error("解析対象となる仕様書PDFがありません。")
            st.stop()

        all_records = []

        with st.spinner("PDFを解析中です..."):
            for pdf_path in saved_pdf_paths:
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

        st.session_state["records"] = all_records
        st.session_state["pdf_paths"] = {
            os.path.basename(path): path
            for path in saved_pdf_paths
        }

        st.success("解析が完了しました。")


if "records" in st.session_state and "pdf_paths" in st.session_state:

    records = st.session_state["records"]
    pdf_paths = st.session_state["pdf_paths"]

    source_files = sorted(set(record["source_file"] for record in records))

    st.subheader("表示設定")

    selected_source = st.selectbox(
        "表示する仕様書を選択",
        options=["すべて"] + source_files,
        index=0
    )

    if selected_source == "すべて":
        display_records = records
    else:
        display_records = [
            record for record in records
            if record["source_file"] == selected_source
        ]

    st.caption(f"表示中：{selected_source} / {len(display_records)}件")

    left, right = st.columns([1, 1.4])

    with left:
        st.subheader("抽出結果")

        for category in CATEGORY_ORDER:
            category_records = [
                r for r in display_records
                if r["category"] == category
            ]

            if not category_records:
                continue

            with st.expander(f"{category}（{len(category_records)}件）", expanded=False):

                page_options = {
                    f"{record['source_file']}：{record['page_no']}ページ｜表：{record['has_table']}｜{record.get('summary', '')}": record
                    for record in category_records
                }

                selected_label = st.selectbox(
                    "確認したいページを選択",
                    options=list(page_options.keys()),
                    key=f"select_{selected_source}_{category}"
                )

                selected_record = page_options[selected_label]

                if st.button(
                    "選択したページを表示",
                    key=f"show_{selected_source}_{category}"
                ):
                    st.session_state["selected_pdf"] = selected_record["source_file"]
                    st.session_state["selected_page"] = selected_record["page_no"]

                st.caption("候補ページ一覧")
                for record in category_records[:5]:
                    st.write(
                        f"- {record['source_file']}｜{record['page_no']}ページ｜表：{record['has_table']}｜{record.get('summary', '')}"
                    )

                if len(category_records) > 5:
                    st.caption(
                        f"他 {len(category_records) - 5} 件は上の選択欄から確認できます。"
                    )

        st.divider()

        if os.path.exists(OUTPUT_EXCEL):
            with open(OUTPUT_EXCEL, "rb") as f:
                st.download_button(
                    label="Excelをダウンロード",
                    data=f,
                    file_name="設計条件書_該当ページ一覧.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

    with right:
        st.subheader("PDF表示")

        if (
            "selected_pdf" in st.session_state
            and "selected_page" in st.session_state
            and st.session_state["selected_pdf"] in pdf_paths
        ):
            selected_pdf = st.session_state["selected_pdf"]
            selected_page = st.session_state["selected_page"]
            pdf_path = pdf_paths[selected_pdf]

            st.write(f"表示中：**{selected_pdf}**　{selected_page}ページ")
            show_pdf_page_as_image(pdf_path, selected_page)
        else:
            st.info("左側のページボタンを押すと、ここにPDFページが表示されます。")