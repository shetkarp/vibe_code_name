import pdfplumber
import pandas as pd
import logging
import io
import csv

def extract_searchable_content(pdf_file_path):
    """
    Extracts text and tables from all pages of a PDF file,
    converting tables to string format and adding them to text_content.

    Args:
        pdf_file_path (str): Path to the PDF file.

    Returns:
        list of str: Extracted text from each page, with tables converted to strings
                     and appended within the text_content list.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("document_extraction.log"),
            logging.StreamHandler()
        ]
    )

    text_content = []
    # tables = []  # No longer needed as a separate return item

    try:
        with pdfplumber.open(pdf_file_path) as pdf:
            logging.info(f"Opened PDF file: {pdf_file_path}")
            
            for page_num, page in enumerate(pdf.pages, start=1):
                # Extract text
                try:
                    text = page.extract_text(layout=True)
                    if text:
                        text_content.append(text)
                        logging.info(f"Extracted text from page {page_num}")
                    else:
                        logging.warning(f"No text found on page {page_num}")
                except Exception as e:
                    logging.error(f"Error extracting text from page {page_num}: {e}")

                # Extract tables
                try:
                    page_tables = page.extract_tables(table_settings={
                        "horizontal_strategy": "text",
                        "vertical_strategy": "lines",
                    })
                    if page_tables:
                        for table_data in page_tables: # Renamed 'table' to 'table_data' for clarity
                            if table_data: # Ensure table_data is not empty
                                try:
                                    # Convert list of lists (table_data) to CSV string
                                    output = io.StringIO()
                                    csv_writer = csv.writer(output)
                                    csv_writer.writerows(table_data)
                                    table_string = output.getvalue().strip() # .strip() removes trailing newline

                                    # Append the table string to text_content, optionally with a separator
                                    if table_string: # Only append if the table string is not empty
                                        text_content.append("\n\n--- TABLE START ---\n" + table_string + "\n--- TABLE END ---\n")
                                        logging.info(f"Converted and added table from page {page_num} to text_content")
                                    else:
                                        logging.warning(f"Extracted empty table on page {page_num}, skipping conversion.")
                                        
                                except Exception as e:
                                    logging.error(f"Error converting table on page {page_num} to string: {e}")
                            else:
                                logging.warning(f"Extracted empty table structure on page {page_num}, skipping.")
                    else:
                        logging.warning(f"No tables found on page {page_num}")
                except Exception as e:
                    logging.error(f"Error extracting tables from page {page_num}: {e}")

    except Exception as e:
        logging.critical(f"Failed to open or process PDF file: {e}")

    return text_content