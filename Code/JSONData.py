import json
from pathlib import Path
from datetime import datetime

class JSONData:
    def __init__(self, json_file="storage/invoices.json"):
        self.json_file = Path(json_file)
        self.json_file.parent.mkdir(exist_ok=True)
        self.documents = []
        self.load()
    
    def load(self):
        if self.json_file.exists():
            try:
                with open(self.json_file, 'r') as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
            except json.JSONDecodeError:
                self.documents = []
        else:
            self.documents = []
    
    def save(self):
        data = {"documents": self.documents}
        with open(self.json_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add(self, document):
        doc_data = document.to_dict()
        doc_data["_saved_at"] = datetime.now().isoformat()
        
        invoice_id = document.invoiceID
        if invoice_id:
            updated = False
            for i, doc in enumerate(self.documents):
                if doc.get("invoiceID") == invoice_id:
                    self.documents[i] = doc_data
                    updated = True
                    break
            
            if not updated:
                self.documents.append(doc_data)
        else:
            self.documents.append(doc_data)
        
        self.save()
    
    def get(self, invoice_id):
        for doc in self.documents:
            if doc.get("invoiceID") == invoice_id:
                return doc
        return None
    
    def get_by_filename(self, filename):
        for doc in self.documents:
            if doc.get("Filename") == filename:
                return doc
        return None
    
    def is_processed(self, filename=None, invoice_id=None):
        if filename and self.get_by_filename(filename):
            return True
        if invoice_id and self.get(invoice_id):
            return True
        return False
    
    def delete(self, invoice_id):
        original_count = len(self.documents)
        self.documents = [doc for doc in self.documents if doc.get("invoiceID") != invoice_id]
        if len(self.documents) < original_count:
            self.save()
            return True
        return False
    
    def list_all(self):
        return self.documents
    
    def count(self):
        return len(self.documents)
    
    def print_summary(self):
        print(f"\n{'='*70}")
        print(f"JSON Data Summary: {self.json_file}")
        print(f"{'='*70}")
        print(f"Total Documents: {self.count()}\n")
        
        for i, doc in enumerate(self.documents, 1):
            invoice_id = doc.get("invoiceID", "N/A")
            filename = doc.get("Filename", "N/A")
            line_items = doc.get("LineItems", [])
            processing_date = doc.get("ProcessingDateTime", "N/A")
            
            print(f"{i}. Invoice ID: {invoice_id}")
            print(f"   Filename: {filename}")
            print(f"   Line Items ({len(line_items)}):")
            for j, item in enumerate(line_items, 1):
                desc = item.get("description", "N/A")[:50]
                qty = item.get("quantity", 0)
                price = item.get("total_price", 0)
                cat = item.get("category", "N/A")
                print(f"      {j}. {desc} | Qty: {qty} | Total: ${price:.2f} | Category: {cat}")
            print(f"   Processed: {processing_date}")
            print()
    
    def print_document(self, invoice_id):
        doc = self.get(invoice_id)
        if doc:
            print(f"\n{'='*70}")
            print(f"Document: {invoice_id}")
            print(f"{'='*70}")
            print(f"Invoice ID: {doc.get('invoiceID', 'N/A')}")
            print(f"Filename: {doc.get('Filename', 'N/A')}")
            print(f"Processing DateTime: {doc.get('ProcessingDateTime', 'N/A')}")
            print(f"\nLine Items ({len(doc.get('LineItems', []))}):")
            print("-" * 70)
            for i, item in enumerate(doc.get("LineItems", []), 1):
                print(f"\n{i}. Description: {item.get('description', 'N/A')}")
                print(f"   Quantity: {item.get('quantity', 0)}")
                print(f"   Unit Price: ${item.get('unit_price', 0):.2f}")
                print(f"   Total Price: ${item.get('total_price', 0):.2f}")
                print(f"   Category: {item.get('category', 'N/A')}")
            
            special_notes = doc.get("SpecialNotes", [])
            if special_notes:
                print(f"\nSpecial Notes:")
                for note in special_notes:
                    print(f"  - {note}")
            
            print(f"\n{'='*70}")
        else:
            print(f"Invoice ID '{invoice_id}' not found.")
    
    def print_all(self):
        print(f"\n{'='*70}")
        print(f"All Documents ({self.count()} total)")
        print(f"{'='*70}\n")
        print(json.dumps({"documents": self.documents}, indent=2))
    
    def search_by_category(self, category):
        results = []
        for doc in self.documents:
            line_items = doc.get("LineItems", [])
            for item in line_items:
                if item.get("category") == category:
                    results.append(doc)
                    break
        return results
    
    def __repr__(self):
        return f"JSONData(file='{self.json_file}', documents={self.count()})"