import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import logging
import csv # Import csv for table conversion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ocr_extraction.log"),
        logging.StreamHandler()
    ]
)

# Define Tesseract path
pytesseract.pytesseract.tesseract_cmd = r'C:/Users/2345029/AppData/Local/Programs/Tesseract-OCR/tesseract.exe'

def extract_image_content(pdf_path, dpi=300):
    """
    Extracts text and tables from all pages of a PDF using OCR.
    Tables are converted to string format and appended directly to text_content.

    Args:
        pdf_path (str): Path to the PDF file.
        dpi (int): Resolution for rendering PDF pages.

    Returns:
        list of str: Extracted text from each page, with OCR-detected tables
                     converted to strings and interleaved within the text_content list.
    """
    # tables = [] # No longer needed as a separate return item
    text_content = []

    try:
        doc = fitz.open(pdf_path)
        logging.info(f"Opened PDF file: {pdf_path}")
    except Exception as e:
        logging.critical(f"Failed to open PDF file: {e}")
        return [] # Return an empty list instead of a tuple

    for page_num, page in enumerate(doc, start=1):
        try:
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72))
            img_bytes = pix.tobytes("png")
            pil_image = Image.open(io.BytesIO(img_bytes))

            extracted_text = pytesseract.image_to_string(pil_image)
            
            # Append the extracted text for the current page
            if extracted_text.strip(): # Only append if there's actual text
                text_content.append(extracted_text)
                logging.info(f"Extracted text from page {page_num}")
            else:
                logging.warning(f"No significant OCR text found on page {page_num}.")


            # Basic table detection from OCR text
            # We'll collect potential table rows and then convert them to a string
            # when a table block ends or the page ends.
            lines = extracted_text.split('\n')
            current_table_rows = []
            
            # --- START Table processing logic ---
            for line in lines:
                words = line.strip().split()
                # This heuristic for table detection is very basic.
                # It looks for lines with more than 2 words, where some words are lowercase alphabets.
                # This might need refinement based on your actual table structures.
                if len(words) > 2 and any(word.isalpha() and word.islower() for word in words):
                    current_table_rows.append(words)
                elif current_table_rows: # If a table block just ended
                    # Convert the collected table rows to a string
                    output = io.StringIO()
                    csv_writer = csv.writer(output)
                    # The table_data here is a list of lists (rows of words)
                    csv_writer.writerows(current_table_rows) 
                    table_string = output.getvalue().strip() # .strip() removes trailing newline

                    if table_string:
                        # Append the table string to text_content
                        text_content.append("\n\n--- OCR TABLE START ---\n" + table_string + "\n--- OCR TABLE END ---\n")
                        logging.info(f"Converted and added OCR-detected table from page {page_num} to text_content")
                    else:
                         logging.warning(f"OCR detected an empty table structure on page {page_num}, skipping conversion.")
                    current_table_rows = [] # Reset for the next potential table
            
            # Append any remaining table rows if the page ends with a table
            if current_table_rows:
                output = io.StringIO()
                csv_writer = csv.writer(output)
                csv_writer.writerows(current_table_rows)
                table_string = output.getvalue().strip()

                if table_string:
                    text_content.append("\n\n--- OCR TABLE START ---\n" + table_string + "\n--- OCR TABLE END ---\n")
                    logging.info(f"Converted and added OCR-detected table from page {page_num} (end of page) to text_content")
                else:
                    logging.warning(f"OCR detected an empty table structure at end of page {page_num}, skipping conversion.")
            # --- END Table processing logic ---

        except Exception as e:
            logging.error(f"Error processing page {page_num}: {e}")
            continue

    doc.close()
    return text_content