__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
import streamlit as st
import logging
import os
import tempfile
import fitz  # PyMuPDF
import hashlib
import json
# Ensure these imports are correct and available
from task4 import extract_searchable_content
from task5 import extract_image_content
from get_chunks import generate_chunks_context
from db import get_rag_response
from metrics import extract_financial_metrics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctim        e)s - %(levelname)s - %(message)s')


def is_pdf_searchable(pdf_path):
    """Checks if a PDF contains searchable text."""
    if not os.path.exists(pdf_path):
        logging.error(f"File not found: {pdf_path}")
        return False
    try:
        with fitz.open(pdf_path) as doc:
            return any(page.get_text().strip() for page in doc)
    except Exception as e:
        logging.error(f"Error checking PDF searchability: {e}")
        return False


@st.cache_data(show_spinner=False)
def process_and_chunk_pdf(uploaded_file_bytes):
    """
    Processes the uploaded PDF, extracts content, and generates chunks.
    This function is cached to prevent re-running on every interaction.
    """
    if uploaded_file_bytes is None:
        return None, None

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file_bytes)
        tmp_path = tmp_file.name

    try:
        searchable = is_pdf_searchable(tmp_path)

        if searchable:
            logging.info("Document is searchable. Extracting text.")
            text = extract_searchable_content(tmp_path)
        else:
            logging.warning("Document is not searchable. Using OCR.")
            text = extract_image_content(tmp_path)

        logging.info("Generating chunks from extracted content.")
        chunks = generate_chunks_context(text_content=text)

        return text, chunks

    except Exception as e:
        logging.error(f"Failed to process PDF or generate chunks: {e}")
        return None, None
    finally:
        os.remove(tmp_path)


def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(layout="wide", page_title="Financial Performance Dashboard")

    st.markdown("""
    <style>
        /* Main App Styling */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 3rem;
            padding-right: 3rem;s
        }

        /* Main Title */
        h1 {
            color: #1E3A8A; /* Dark Blue */
            text-align: center;
            font-weight: bold;
        }

        /* Section Headers */
        h2 {
            color: #1D4ED8; /* Medium Blue */
            border-bottom: 3px solid #93C5FD; /* Lighter Blue */
            padding-bottom: 10px;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }

        /* Sub-section Headers */
        h3 {
            color: #1E40AF;
            font-weight: bold;
        }

        /* Metric Box Styling */
        div[data-testid="stMetric"] {
            background-color: #F0F8FF; /* AliceBlue, a very light blue */
            border: 1px solid #BFDBFE; /* Blue-200 */
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.05);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        div[data-testid="stMetric"]:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }

        /* Metric Label */
        div[data-testid="stMetricLabel"] {
            font-size: 1.1em;
            font-weight: 600;
            color: #374151; /* Cool Gray 700 */
        }

        /* Tab Styling */
        button[data-testid="stTab"] {
            padding: 12px 25px;
            font-weight: 600;
            border-radius: 8px 8px 0 0;
            background-color: #F3F4F6; /* Gray 100 */
            color: #4B5563; /* Gray 600 */
            transition: all 0.3s;
            border: none;
        }

        button[data-testid="stTab"][aria-selected="true"] {
            background-color: #1D4ED8; /* Selected Tab Blue */
            color: white;
        }

        /* File Uploader Styling */
        div[data-testid="stFileUploader"] {
            border: 2px dashed #60A5FA;
            background-color: #F9FAFB;
            padding: 2rem;
            border-radius: 10px;
            text-align: center;
        }

        /* Success/Info Box Styling */
        div[data-testid="stAlert"] {
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.title("📊 Financial Performance Dashboard")

    st.write("""
        This dashboard provides a quick overview of key financial performance measures,
        and allows you to upload PDF files for analysis.
    """)

    if 'text_chunks' not in st.session_state:
        st.session_state['text_chunks'] = None
    if 'uploaded_file_hash' not in st.session_state:
        st.session_state['uploaded_file_hash'] = None
    if 'rag_response' not in st.session_state:
        st.session_state['rag_response'] = ""
    if 'financial_metrics_data' not in st.session_state:
        st.session_state['financial_metrics_data'] = {}

    main_tab_titles = ["⬆️ Upload & Analyze", "📈 Financial Metrics", "💬 Chat with Data"]
    main_tabs = st.tabs(main_tab_titles)

    with main_tabs[0]:
        st.header("Upload Financial Statements for Analysis")
        uploaded_file = st.file_uploader("Choose a PDF file", type="pdf", label_visibility="collapsed")

        if uploaded_file:
            file_bytes = uploaded_file.getvalue()
            current_hash = hashlib.md5(file_bytes).hexdigest()

            if st.session_state['uploaded_file_hash'] != current_hash:
                st.session_state['uploaded_file_hash'] = current_hash
                with st.spinner(f'Analyzing "{uploaded_file.name}" and creating a knowledge base...'):
                    text_content, chunks = process_and_chunk_pdf(file_bytes)

                if chunks:
                    st.session_state['text_chunks'] = chunks
                    # Extract metrics and store them in session state
                    st.session_state['financial_metrics_data'] = extract_financial_metrics(
                        st.session_state['text_chunks'])

                    st.success(f"Analysis Complete! A knowledge base of {len(chunks)} chunks has been created.")
                    st.info(
                        f"You can now ask questions about '{uploaded_file.name}' in the 'Chat with Data' tab and view metrics in the 'Financial Metrics' tab.")
                else:
                    st.error("Failed to process the PDF. Please check the logs for details.")
            else:
                st.info("File already processed. You can chat with it in the 'Chat with Data' tab or view metrics.")
        else:
            st.info("No PDF file uploaded yet. Please upload a file to begin.")
    with main_tabs[1]:
        st.header("Key Financial Metrics & Insights")

        if not st.session_state.get('financial_metrics_data'):
            st.info("Please upload a financial document in the 'Upload & Analyze' tab to begin.")
        else:
            metrics_data = st.session_state['financial_metrics_data']

            if isinstance(metrics_data, dict) and any(metrics_data.values()):
                statement_names = ["Income Statement", "Balance Sheet", "Cash Flow Statement", "Other"]
                statement_tabs = st.tabs(statement_names)

                for i, statement_name in enumerate(statement_names):
                    with statement_tabs[i]:
                        metrics = metrics_data.get(statement_name, {})
                        if metrics:
                            st.subheader(f"{statement_name} Metrics")

                            cols = st.columns(3)
                            col_index = 0
                            for metric_name, data in metrics.items():
                                with cols[col_index]:
                                    # Get delta and delta_color with safe fallbacks
                                    delta_value = data.get("delta", None)
                                    # Explicitly set delta_color based on the presence of a delta value
                                    delta_color_value = data.get("delta_color",
                                                                 "off") if delta_value is not None else "off"

                                    st.metric(
                                        label=metric_name,
                                        value=data.get("value", "N/A"),
                                        delta=delta_value,
                                        delta_color=delta_color_value
                                    )
                                col_index = (col_index + 1) % 3
                        else:
                            st.info(f"No metrics found for {statement_name}.")
            else:
                st.info(
                    "No financial metrics were found in the document. You can now chat with the PDF to get your answers.")

    with main_tabs[2]:
        st.header("Chat with Your Financial Data")
        st.write("Enter your query below to get a response from the uploaded document.")

        input_disabled = st.session_state['text_chunks'] is None

        with st.form(key='query_form', clear_on_submit=True):
            user_input = st.text_input(
                label="Your Query:",
                placeholder="e.g., What is the Gross Margin Profit in 2024?",
                key="qa_input",
                disabled=input_disabled
            )
            submit_button = st.form_submit_button(label="Submit Query", disabled=input_disabled)

            if submit_button and user_input:
                with st.spinner('Generating response...'):
                    response = get_rag_response(docs=st.session_state['text_chunks'], query=user_input)
                    st.session_state['rag_response'] = response

        if st.session_state['rag_response']:
            st.subheader("Response:")
            st.info(st.session_state['rag_response'])

    st.markdown("---")
    st.caption(
        "*:grey[Note: The values displayed in the 'Financial Metrics' tab are extracted from the uploaded document using AI.]*")


if __name__ == "__main__":
    main()