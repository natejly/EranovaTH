"""
Document class for processing invoice documents.
"""
import fitz 
import pytesseract
from PIL import Image, ImageEnhance
import io
import re
import json
import os
from pathlib import Path
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

_env_path = Path(__file__).parent.parent / '.env'
if _env_path.exists():
    load_dotenv(_env_path)
else:
    load_dotenv()

_tax_rates_path = Path(__file__).parent.parent / 'tax_rates.json'
if _tax_rates_path.exists():
    with open(_tax_rates_path, 'r') as f:
        tax_rates = json.load(f)
else:
    tax_rates = {}
    
class LineItem:
    def __init__(self, description, quantity, unit_price, total_price, category=None):
        self.description = description
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = total_price
        self.category = category
    
class Document:
    
    def __init__(self, file_path):

        self.file_path = Path(file_path)
        self.text = None
        self.invoiceID = None
        self.Filename = None
        self.AIPromptTokens = None
        self.AICompletionTokens = None
        self.ProcessingDateTime = None
        self.LineItems = []
        self.SpecialNotes = []
        self.PreTaxTotal = 0
        self.PostTaxTotal = 0
        self.TaxTotal = 0
        
    def process_totals(self):
        self.PreTaxTotal = 0
        self.TaxTotal = 0
        self.PostTaxTotal = 0
        
        for item in self.LineItems:
            item_tax_rate = 0
            if item.category and item.category in tax_rates:
                item_tax_rate = float(tax_rates[item.category]) / 100

            self.PreTaxTotal += item.total_price
            self.TaxTotal += item.total_price * item_tax_rate
            self.PostTaxTotal += item.total_price + item.total_price * item_tax_rate
        
    def extract_text(self):
        pdf_document = fitz.open(self.file_path)
        
        text = ""
        
        for page in pdf_document:
            text += page.get_text("text")

        if not text.strip():
            print("No embedded text found, performing OCR...")
            ocr_text = ""
            for page_number in range(len(pdf_document)):
                page = pdf_document[page_number]
                pix = page.get_pixmap(dpi=400, alpha=False)

                img = Image.open(io.BytesIO(pix.tobytes()))
                img = img.convert("L")
                img = ImageEnhance.Contrast(img).enhance(2.0)
                img = ImageEnhance.Sharpness(img).enhance(2.0)

                custom_config = (
                    r'--oem 3 --psm 6 '
                    r'-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
                )

                page_text = pytesseract.image_to_string(img, config=custom_config)
                page_text = re.sub(r'[^A-Za-z0-9\s]', '', page_text)
                ocr_text += page_text + "\n"

            text = ocr_text
        else:
            print("Embedded text found, skipping OCR.")

        pdf_document.close()

        self.text = text
        
    def parse_text(self, api_key=None, model="gpt-4o-mini"):

        if not self.text:
            raise ValueError("No text to parse. Call extract_text() first.")
        
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass api_key parameter.")
        
        client = OpenAI(api_key=api_key)
        
        available_categories = list(tax_rates.keys())
        categories_list = ", ".join(available_categories)
        
        prompt = f"""Extract invoice information from the following text and return a JSON object with the following structure:
                {{
                    "invoiceID": "invoice number or ID",
                    "LineItems": [
                        {{
                            "description": "item description",
                            "quantity": quantity as float,
                            "unit_price": unit price as float,
                            "total_price": total price as float,
                            "category": "one of the available categories below"
                        }}
                    ],
                    "SpecialNotes": ["any special notes or remarks as an array of strings"]
                }}

                Available categories to choose from: {categories_list}

                For each line item, assign the most appropriate category from the list above based on the item description.

                Invoice text:
                {self.text}

                Return only valid JSON, no additional text or explanation."""

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured data from invoices. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0
            )
            
            content = response.choices[0].message.content
            parsed_data = json.loads(content)
            
            self.AIPromptTokens = response.usage.prompt_tokens
            self.AICompletionTokens = response.usage.completion_tokens
            
            self.ProcessingDateTime = datetime.now().isoformat()
            
            if not self.Filename:
                self.Filename = str(self.file_path.name)
            
            self.invoiceID = parsed_data.get("invoiceID")
            
            self.LineItems = []
            for item_data in parsed_data.get("LineItems", []):
                line_item = LineItem(
                    description=item_data.get("description", ""),
                    quantity=item_data.get("quantity", 0),
                    unit_price=item_data.get("unit_price", 0),
                    total_price=item_data.get("total_price", 0),
                    category=item_data.get("category")
                )
                self.LineItems.append(line_item)
            
            self.SpecialNotes = parsed_data.get("SpecialNotes", [])
            
            self.process_totals()
            
            return {
                "invoiceID": self.invoiceID,
                "LineItems": [
                    {
                        "description": item.description,
                        "quantity": item.quantity,
                        "unit_price": item.unit_price,
                        "total_price": item.total_price,
                        "category": item.category
                    }
                    for item in self.LineItems
                ],
                "SpecialNotes": self.SpecialNotes
            }
            
        except Exception as e:
            raise Exception(f"Error parsing text with OpenAI: {str(e)}")
    
    def to_dict(self):
        """Convert document to dictionary."""
        return {
            "invoiceID": self.invoiceID,
            "Filename": self.Filename,
            "AIPromptTokens": self.AIPromptTokens,
            "AICompletionTokens": self.AICompletionTokens,
            "ProcessingDateTime": self.ProcessingDateTime,
            "PreTaxTotal": self.PreTaxTotal,
            "TaxTotal": self.TaxTotal,
            "PostTaxTotal": self.PostTaxTotal,
            "LineItems": [
                {
                    "description": item.description,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "category": item.category
                }
                for item in self.LineItems
            ],
            "SpecialNotes": self.SpecialNotes
        }
        
def main():
    """Main function to run the document processing."""
    from JSONData import JSONData
    
    json_data = JSONData("storage/invoices.json")
    
    document = Document("Invoices/AlphaImportInvoice.pdf")
    document.extract_text()
    document.parse_text()
    
    json_data.add(document)
    json_data.print_summary()
    
if __name__ == "__main__":
    main()