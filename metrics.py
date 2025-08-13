import json
import logging
import google.generativeai as genai
from google.generativeai import GenerativeModel
from dotenv import load_dotenv
import os

Gemini_Key = "AIzaSyB0giFpRn5roQqlOeCNqBTgRD4R_YUfkJg"
# load_dotenv()
# api_key = os.getenv("GEMINI_KEY")
genai.configure(api_key=Gemini_Key)

# Initialize the model once for efficiency
model = GenerativeModel("gemini-2.5-flash")  # gemini-1.5-flash is more capable of structured output


def get_response_financial(text_chunks, prompt):
    """
    Sends a prompt and document chunks to the Gemini model.
    """
    full_text = "\n".join(text_chunks)
    response = model.generate_content(f"{prompt}\n\nDocument Text:\n{full_text}")
    return response.text


def extract_financial_metrics(text_chunks):
    """
    Acts as a financial expert using the Gemini model to dynamically
    extract key financial metrics from document chunks.
    """
    if not text_chunks:
        return {"message": "You can now chat with the PDF to get your answers."}

    prompt_template = """
    "Extract key financial metrics from the provided text and structure them into a nested JSON object.

    Identify up to 20 significant financial metrics. For each metric, find its most recent value and the change (delta) from the comparable period, if available.

    Categorize metrics under 'Income Statement', 'Balance Sheet', 'Cash Flow Statement', or 'Other'.

    Format the output as a single nested JSON object. The top-level keys should be the statement categories. Under each category, the key should be the metric name. The value for each metric should be an object with the following structure:
    {"value": "extracted_value", "delta": "change_vs_last_period_or_year", "delta_color": "normal" or "inverse"}

    If no metrics are found, return an empty JSON object: {"Income Statement": {}, "Balance Sheet": {}, "Cash Flow Statement": {}, "Other": {}}.

    Return only the JSON object, without any extra text or markdown."
    """

    try:
        response_text = get_response_financial(text_chunks=text_chunks, prompt=prompt_template)
        # Clean the response to remove markdown (```json ... ```)
        cleaned_response = response_text.replace("```json", "").replace("```", "").strip()
        metric_data = json.loads(cleaned_response)

        # A more robust check for empty results
        if not any(metric_data.values()):
            return {
                "message": "No financial metrics found in the document. You can now chat with the PDF to get your answers."}

        return metric_data

    except json.JSONDecodeError as e:
        logging.error(f"Failed to decode JSON from Gemini response. Response was: {response_text}")
        # Return a user-friendly message without exposing technical errors
        return {"message": "The model's response was not in the expected format. Please try again."}

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        return {"message": "An unexpected error occurred. Please try again."}

# metrics = extract_financial_metrics(["""• Cash and cash equivalents of $9.9 billion
# • Total debt of $46.9 billion2
# • Operating cash flow for FY’24 of $35.7 billion, an increase of $6.9 billion
# • Free cash flow for FY’24 of $15.1 billion1
# , an increase of $3.1 billion
# • Repurchased 18.2 million shares3
#  for FY’24, or $2.8 billio"""])

# metrics= extract_financial_metrics([
#     """BENTONVILLE, Ark., Feb 20, 2024 - Walmart Inc. (NYSE: WMT) announces fourth quarter results, including strong revenue growth of 5.7%. The Company’s omnichannel model continues to resonate with customers helping to deliver strong growth, including comp sales of 4.0% for Walmart U.S. Looking ahead, the company issues guidance for FY25, including growth in net sales in constant currency (“cc”) of 3% to 4% and operating income of 4% to 6%. Consolidated revenue of 173.4 billion, up 5.71.7 billion, or 30.4%; adjusted operating income up 13.2% , positively affected by currency and LIFO of 2.3% and 1.0%, respectively + Global eCommerce sales grew 23% + Global advertising business” grew approximately 33%, including 22% for Walmart Connect in the U.S. + Adjusted EPS' of 1.80 excludes the effect, net of tax, from a net gain of 0.23 on equity and other investments + Walmart agrees to buy VIZIO HOLDING CORP. to further accelerate Walmart Connect in the U.S. Consolidated revenue of 648.1 billion, up 6.03.4 billion + Consolidated operating income up 6.6 billion, or 32.25.74; Adjusted EPS of 6.65 Our team delivered a great quarter, finishing off a strong year. We crossed 100 billion in eCommerce sales and drove share gains as our customer experience metrics improved, even during our highest volume days leading up to the holidays. We’re proud of the team and excited about building on our momentum as we work to bring prices down for our customers and members.” President and CEO, Walmart "See additional information at the end of the release regarding non-GAAP financial measures. Our global advertising business is recorded in either net sales or as a reduction to cost of sales, depending on the nature of the advertising arrangement. Comp sales for the 13-week period ended January 26th, 2024 compared to the 13-week period ended January 27th, 2023, and excludes fuel. See Supplemental Financial Information for additional information. “cc” - constant currency Dollars in billions, except per share data. Dollar and percentage changes may not recalculate due to rounding. Charts may not be to scale. FY’24 Q4 FY'24 +5.7% +6. 7 173.4 Total revenues FY’23 Q4 FY2ˊ4 Q4 FY’23 FY’24 +39 bps —— .+27 bps ae23.57.3 ry i} 4 27.027.1 . a 6 Income 5.6i.4= FY23 Q4 FY24 Q4 FY2ˊ3 CI FY2ˊ4 Q4 FY2ˊ3 FY2ˊ4 FY23 FY24 Reported Adjusted! Reported Adjusted! (12.56.65 Earnings per = 6.52.32 FY'23 Q4 FY24Q4 FY'23 Q4 FY'24 Q4 FY’23 FY24 FY23 FY24 Reported Adjusted! Reported Adjusted! Balance Sheet and Liquidity * Cash and cash equivalents of 9.9 billion −Total debt of 46.9 billion’ * Operating cash flow for FY’24 of 35.7 billion, an increase of 6.9 billion * Free cash flow for FY’24 of 15.1 billion’, an increase of 3.1 billion ¢ Repurchased 18.2 million shares’ for FY’24, or 2.8 billion Inventory of 54.9 billion, a decrease of 1.7 billion "See additional information at the end of this release regarding non−GAAP financial measures. Debt includes short−term borrowings, long−term debt due within one year, finance lease obligations due within one year, long−term debt and long−term finance lease obligations. 316.5 billion remaining of 20 billion authorization approved in November 2022. NM=Not Meaningful"""  
# ])

# print(metrics)