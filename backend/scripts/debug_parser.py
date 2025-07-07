#!/usr/bin/env python3
"""
Debug script to test LawnFawn parser with the actual invoice.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.pdf_parser import PDFParserService
from app.parsers.lawnfawn import LawnFawnParsingStrategy

async def debug_parser():
    """Debug the LawnFawn parser with the actual invoice."""
    
    # Path to the invoice file
    invoice_path = "/Users/fabianpuehringer/Downloads/KK-Inv_CPSummer25_from_Lawn_Fawn_35380 (003).pdf"
    
    if not os.path.exists(invoice_path):
        print(f"❌ Invoice file not found: {invoice_path}")
        return
    
    print(f"🔍 Debugging LawnFawn parser with: {invoice_path}")
    
    # Read the PDF file
    with open(invoice_path, 'rb') as f:
        pdf_content = f.read()
    
    print(f"📄 PDF file size: {len(pdf_content)} bytes")
    
    # Parse the PDF
    pdf_parser = PDFParserService()
    
    try:
        # Extract text and tables
        pdf_text, tables = pdf_parser.extract_text_and_tables(pdf_content)
        
        print(f"📝 Extracted text length: {len(pdf_text)} characters")
        print(f"📊 Extracted tables: {len(tables)} tables")
        
        # Show first 500 characters of text
        print("\n" + "="*50)
        print("FIRST 500 CHARACTERS OF PDF TEXT:")
        print("="*50)
        print(pdf_text[:500])
        print("="*50)
        
        # Show table structure
        print(f"\nTABLE ANALYSIS:")
        for i, table in enumerate(tables):
            print(f"Table {i+1}: {len(table)} rows x {len(table[0]) if table else 0} columns")
            if table:
                print(f"  Header: {table[0]}")
                print(f"  Sample rows: {min(3, len(table)-1)}")
                for j in range(1, min(4, len(table))):
                    print(f"    Row {j}: {table[j]}")
        
        # Test the LawnFawn parser
        print(f"\n" + "="*50)
        print("TESTING LAWNFAWN PARSER:")
        print("="*50)
        
        parser = LawnFawnParsingStrategy()
        result = parser.parse_invoice(pdf_text, tables)
        
        print(f"✅ Parsing completed!")
        print(f"📦 Products found: {result.total_products}")
        print(f"📈 Success rate: {result.parsing_success_rate}%")
        print(f"🏢 Supplier: {result.supplier}")
        
        if result.parsing_errors:
            print(f"\n❌ Parsing errors ({len(result.parsing_errors)}):")
            for error in result.parsing_errors:
                print(f"  - {error}")
        
        if result.products:
            print(f"\n📋 PARSED PRODUCTS (showing first 10):")
            for i, product in enumerate(result.products[:10]):
                print(f"  {i+1}. {product.supplier_sku} - {product.product_name}")
                print(f"     Category: {product.category}, Qty: {product.quantity}, Price: ${product.price_usd}")
        
        # Show metadata
        print(f"\n📄 METADATA:")
        print(f"  Invoice Number: {result.metadata.invoice_number}")
        print(f"  Invoice Date: {result.metadata.invoice_date}")
        print(f"  Currency: {result.metadata.currency}")
        print(f"  Total Amount: {result.metadata.total_amount}")
        
    except Exception as e:
        print(f"❌ Error during parsing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_parser())
