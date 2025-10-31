# Invoice Processing System

## Summary

This solution provides an automated invoice processing system that leverages AI to extract, parse, and analyze invoice data from PDF documents. The system combines OCR with OpenAI's GPT models to extract structured information from the invoices, including item name, and tax amount based on category specific rates. This data is then stored in JSON format for later retrieval.

### Technical Architecture

The solution is built with a modular architecture consisting of three core components:

1. **Document Processing Layer** (`Document.py`) - Handles PDF text extraction, OCR processing, and AI-powered parsing
2. **Data Management Layer** (`JSONData.py`) - Manages invoice storage, retrieval, and duplicate detection in JSON format
3. **User Interface Layer** (`app.py`) - Provides the web-based frontend for upload, processing, and viewing invoices

## Implementation Details

### Document Processing (`Document.py`)

The `Document` class handles PDF processing and AI-powered invoice parsing.

**Class Attributes:**

- `file_path` - Path to the PDF invoice file
- `text` - Extracted text content from the PDF
- `invoiceID` - Unique invoice identifier
- `Filename` - Original filename
- `LineItems` - List of LineItem objects containing invoice line items
- `SpecialNotes` - Array of special notes or remarks from the invoice
- `PreTaxTotal` - Total amount before tax
- `TaxTotal` - Total tax amount
- `PostTaxTotal` - Total amount including tax
- `AIPromptTokens` - Number of tokens used in the AI prompt
- `AICompletionTokens` - Number of tokens in the AI response
- `ProcessingDateTime` - ISO format timestamp of processing

**Key Methods:**

- `extract_text()` - Extracts text from PDF using PyMuPDF with OCR fallback

  - Extracts native text from PDF
  - If text extraction doesn't work, converts PDF pages to images and applies Tesseract OCR
- `parse_text(api_key=None, model="gpt-4o-mini")` - AI-powered parsing of extracted text
- - Sends extracted text to OpenAI GPT model with structured JSON schema
  - Identifies invoice ID, line items (description, quantity, unit price, total, category), and special notes
  - Assigns appropriate tax category to each line item from available categories
  - Tracks token usage
  - Returns structured JSON data
- `process_totals()` - Calculates financial totals

  - Computes pre-tax total by summing all line item prices
  - Applies category-specific tax rates to calculate tax amounts
  - Calculates post-tax total (pre-tax + tax)
- `to_dict()` - Serializes document object to dictionary format for JSON storage

**LineItem Class:**

- Simple data class storing: `description`, `quantity`, `unit_price`, `total_price`, `category`

### Data Management (`JSONData.py`)

The `JSONData` class manages invoice storage, retrieval, and persistence in JSON format.

**Key Methods:**

- `__init__(json_file)` - Initializes storage, creates directory structure if needed
- `load()` - Loads invoices from JSON file into memory
- `save()` - Persists in-memory invoice data to JSON file
- `add(document)` - Adds a new invoice document to storage and saves
- `get(invoice_id)` - Retrieves a specific invoice by ID
- `get_by_filename(filename)` - Retrieves an invoice by original filename
- `is_processed(filename, invoice_id)` - Checks if an invoice was already processed (prevents duplicates)
- `delete(invoice_id)` - Removes an invoice from storage
- `list_all()` - Returns all stored invoices
- `count()` - Returns total number of invoices
- `search_by_category(category)` - Finds all invoices containing items of a specific category

### User Interface (`app.py`)

**Core Functions:**

- `load_tax_rates()` - Loads tax rate configuration from JSON file
- `init_session_state()` - Initializes Streamlit session state for UI persistence
- `process_single_invoice(uploaded_file, json_data)` - Handles individual invoice processing
- `process_invoices(uploaded_files, json_data)` - Orchestrates batch processing
- `render_upload_section(json_data)` - Renders file upload interface
- `render_invoice_list(json_data, tax_rates)` - Displays all processed invoices with expandable details
- `render_invoice_details(doc, tax_rates)` - Formats and displays individual invoice information
- `calculate_line_item_with_tax(item, tax_rates)` - Computes tax breakdown for display

### Processing Flow

1. User uploads PDF invoice(s) via web interface
2. System checks if invoice already exists (by filename)
3. PDF is saved to temporary file
4. `extract_text()` extracts content using PyMuPDF + OCR fallback
5. `parse_text()` sends extracted text to OpenAI GPT for structured parsing
6. AI returns JSON with invoice ID, line items, and categories
7. `process_totals()` calculates tax amounts using category-specific rates
8. Invoice is serialized and stored in JSON database
9. UI refreshes to show newly processed invoice
10. Temporary file is cleaned up

### Tax Rate Configuration

Tax rates are defined in `tax_rates.json` with category-to-percentage mappings. Categories include:

- Food items (groceries, beverages, etc.)
- Electronics and appliances
- Clothing and textiles
- Services (labor, installation, etc.)
- Medical supplies and pharmaceuticals
- And 45+ other categories

Each line item is automatically assigned the most appropriate category by the AI, ensuring accurate tax calculations.

## Setup Instructions

### Installation

1. **Clone or download the repository**
2. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

3. **Install Tesseract OCR**

- **macOS**: `brew install tesseract`
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr`
- **Windows**: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

4. **Configure environment variables**

Create a `.env` file in the project root:

```
OPENAI_API_KEY=your_api_key_here
```

### Running the Application

1. **Start the Streamlit application**

```bash
streamlit run Code/app.py
```

3. **Access the application**

The application will automatically open in your default browser at `http://localhost:8501`

### Using the System

1. **Upload Invoices**: Click "Choose PDF files" and select one or more PDF invoices
2. **Process**: Click "Process All" to begin automated extraction and parsing
3. **View Results**: Processed invoices appear below with expandable details including line items, totals, and tax breakdowns
4. **Manage Data**: Use the Delete button to remove invoices as needed

## Project Structure

```
Eranova_Platform_Engineer_Interview_Round1/
├── Code/
│   ├── app.py              # Main Streamlit application
│   ├── Document.py         # PDF processing and AI parsing
│   ├── JSONData.py         # Data management
│   └── storage/
│       └── invoices.json   # Invoice data storage
├── Invoices/               # Sample invoice PDFs
├── tax_rates.json          # Tax rate configuration
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Technology Stack

- **Frontend**: Streamlit
- **AI Processing**: OpenAI GPT-4
- **PDF Processing**: PyMuPDF (fitz)
- **OCR**: Tesseract, pytesseract
- **Image Processing**: Pillow, pdf2image
- **Data Storage**: JSON
