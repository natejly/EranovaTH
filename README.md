# Invoice Processing System

## Summary

This solution provides an automated invoice processing system that leverages AI to extract, parse, and analyze invoice data from PDF documents. The system combines OCR with OpenAI's GPT models to extract structured information from the invoices, including item name, and tax amount based on category specific rates. This data is then stored in JSON format for later retrieval. 

### Technical Architecture

The solution is built with a modular architecture consisting of three core components:

1. **Document Processing Layer** (`Document.py`) - Handles PDF text extraction, OCR processing, and AI-powered parsing
2. **Data Management Layer** (`JSONData.py`) - Manages invoice storage, retrieval, and duplicate detection in JSON format
3. **User Interface Layer** (`app.py`) - Provides the web-based frontend for upload, processing, and viewing invoices

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
