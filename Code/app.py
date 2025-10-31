import streamlit as st
import json
import sys
from pathlib import Path
import tempfile
import os
import time

sys.path.append(str(Path(__file__).parent))

from Document import Document
from JSONData import JSONData

def load_tax_rates():
    tax_rates_path = Path(__file__).parent.parent / 'tax_rates.json'
    if tax_rates_path.exists():
        with open(tax_rates_path, 'r') as f:
            return json.load(f)
    return {}


def init_session_state():
    if 'session_key' not in st.session_state:
        st.session_state.session_key = 0


def process_single_invoice(uploaded_file, json_data):
    if json_data.is_processed(filename=uploaded_file.name):
        return {
            "status": "skipped",
            "filename": uploaded_file.name,
            "reason": "Already processed"
        }
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    try:
        doc = Document(tmp_file_path)
        doc.Filename = uploaded_file.name
        doc.extract_text()
        doc.parse_text()
        json_data.add(doc)
        
        return {
            "status": "success",
            "filename": uploaded_file.name,
            "invoice_id": doc.invoiceID,
            "line_items": len(doc.LineItems),
            "pre_tax_total": doc.PreTaxTotal,
            "post_tax_total": doc.PostTaxTotal
        }
    finally:
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)


def process_invoices(uploaded_files, json_data):
    progress_bar = st.progress(0)
    status_text = st.empty()
    results = {"success": [], "skipped": [], "failed": []}
    
    for idx, uploaded_file in enumerate(uploaded_files):
        progress = idx / len(uploaded_files)
        progress_bar.progress(progress)
        status_text.text(f"Processing {idx + 1}/{len(uploaded_files)}: {uploaded_file.name}...")
        
        try:
            result = process_single_invoice(uploaded_file, json_data)
            results[result["status"]].append(result)
        except Exception as e:
            results["failed"].append({
                "filename": uploaded_file.name,
                "error": str(e)
            })
    
    progress_bar.progress(1.0)
    status_text.text("Processing complete!")
    
    if results["skipped"]:
        for item in results["skipped"]:
            st.warning(f"{item['filename']} - {item['reason']}")
        time.sleep(1)
    
    json_data.load()
    st.session_state.session_key += 1
    st.rerun()


def render_upload_section(json_data):
    st.header("Upload Invoices")
    st.write("Upload multiple PDF invoices to process them automatically.")
    
    uploaded_files = st.file_uploader(
        "Choose PDF files",
        type=['pdf'],
        accept_multiple_files=True,
        help="Select one or more PDF invoice files to process",
        key=f"file_uploader_{st.session_state.session_key}"
    )
    
    if uploaded_files:
        st.write(f"**{len(uploaded_files)} file(s) selected**")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("Process All", type="primary", use_container_width=True):
                process_invoices(uploaded_files, json_data)


def calculate_line_item_with_tax(item, tax_rates):
    category = item.get('category', 'N/A')
    total_price = item.get('total_price', 0)
    tax_rate = float(tax_rates.get(category, 0))
    tax_amount = total_price * (tax_rate / 100)
    total_with_tax = total_price + tax_amount
    
    return {
        "Description": item.get('description', 'N/A'),
        "Quantity": item.get('quantity', 0),
        "Unit Price": f"${item.get('unit_price', 0):.2f}",
        "Total Price": f"${total_price:.2f}",
        "Category": category,
        "Tax Rate": f"{tax_rate}%",
        "Tax Amount": f"${tax_amount:.2f}",
        "Total with Tax": f"${total_with_tax:.2f}"
    }


def render_invoice_details(doc, tax_rates):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Invoice ID:** {doc.get('invoiceID', 'N/A')}")
        st.write(f"**Filename:** {doc.get('Filename', 'N/A')}")
        st.write(f"**Processing Date:** {doc.get('ProcessingDateTime', 'N/A')}")
    
    with col2:
        st.write(f"**Prompt Tokens:** {doc.get('AIPromptTokens', 'N/A')}")
        st.write(f"**Completion Tokens:** {doc.get('AICompletionTokens', 'N/A')}")
    
    if doc.get('PreTaxTotal') is not None:
        st.subheader("Totals")
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1:
            st.metric("Pre-Tax Total", f"${doc.get('PreTaxTotal', 0):.2f}")
        with col_t2:
            st.metric("Tax Total", f"${doc.get('TaxTotal', 0):.2f}")
        with col_t3:
            st.metric("Post-Tax Total", f"${doc.get('PostTaxTotal', 0):.2f}")
    
    if doc.get('LineItems'):
        st.subheader("Line Items")
        line_items_data = [
            calculate_line_item_with_tax(item, tax_rates)
            for item in doc['LineItems']
        ]
        st.dataframe(line_items_data, use_container_width=True)
    
    if doc.get('SpecialNotes'):
        st.subheader("Special Notes")
        for note in doc['SpecialNotes']:
            st.write(f"- {note}")


def render_invoice_list(json_data, tax_rates):
    st.header("All Invoices")
    json_data.load()
    
    if json_data.count() == 0:
        st.info("No invoices processed yet.")
        return
    
    st.write(f"**Total Invoices:** {json_data.count()}")
    
    for i, doc in enumerate(json_data.list_all(), 1):
        invoice_id = doc.get('invoiceID', 'N/A')
        filename = doc.get('Filename', 'N/A')
        
        col_header, col_delete = st.columns([10, 1])
        
        with col_header:
            with st.expander(f"Invoice {i}: {invoice_id} - {filename}"):
                render_invoice_details(doc, tax_rates)
        
        with col_delete:
            if invoice_id != 'N/A':
                if st.button("Delete", key=f"delete_{invoice_id}", type="secondary"):
                    if json_data.delete(invoice_id):
                        st.success(f"Invoice {invoice_id} deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete invoice")


def main():
    st.set_page_config(page_title="Invoice Processor", layout="wide")
    st.title("Invoice Processing System")
    
    init_session_state()
    tax_rates = load_tax_rates()
    json_data = JSONData("storage/invoices.json")
    
    render_upload_section(json_data)
    st.divider()
    render_invoice_list(json_data, tax_rates)


if __name__ == "__main__":
    main()
