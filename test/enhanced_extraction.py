"""
Integration: Enhanced PDF Extraction with Gemini/Ollama
Combines preprocessing with AI extraction for best results
"""

import google.generativeai as genai
import ollama
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
from pathlib import Path
import json
import os


# Your invoice prompt (unchanged)
INVOICE_PROMPT = """you are a professional invoice data extraction specialist operating in STRICT MODE.

GOALS
- Extract ONLY what appears in the document. Copy text exactly (case, spacing, punctuation, currency symbols, decimals).
- Never guess, normalize, reformat, calculate, or infer. If a value isn't explicitly present, output "Not Found" (or "N/A" only if the invoice literally shows "N/A").

SOURCE-OF-TRUTH & SCOPE
- Use only the provided invoice (all pages). Ignore prior knowledge or external data.
- If the document is a pro forma, quote, receipt, or credit note, still follow the same instructions and return "Not Found" for missing fields.

FIELD LABEL SYNONYMS (for locating text; do NOT rewrite the values)
- PO Number: "PO", "P.O.", "Purchase Order", "Purchase Order No.", "Order No.", "LPO"
- Supplier Name: "Supplier", "Vendor", "Company", "From", letterhead/company name
- Invoice Number: "Invoice No.", "Invoice#", "Invoice #", "Inv No.", "Bill No."
- Invoice Total Amount (Grand Total): "Grand Total", "Total", "Total Due", "Amount Due", "Invoice Total", "Balance Due"
- Invoice Date: "Invoice Date", "Date"
- Payment Term: "Payment Terms", "Terms", "Due on Receipt", "Net 7/10/15/30/60", "COD"
- Vendor TRN/VAT/Tax Reg No.: "TRN", "Tax Registration Number", "VAT No.", "VAT Reg No.", "Tax ID", "TIN", "GSTIN", "ABN", "EIN" (use only if clearly the vendor's number)

LINE ITEMS (table or listed items)
- Include every billable line in the document, across all pages, in the original order.
- Description may be multi-line—preserve line breaks as "\\n".
- Tax Rate must be what is shown per line. If only a global tax is shown (no per-line rate), set per-line "tax_rate" to "Not Found".
- Line Amount must include the currency symbol if present on that line; if the symbol is absent on the line but present elsewhere, do NOT add it—copy exactly what's on the line.

OUTPUT (RETURN ONLY VALID JSON — no extra text)
{
  "invoice_header": {
    "po_number": "",
    "supplier_name": "",
    "invoice_number": "",
    "invoice_total_amount": "",
    "invoice_date": "",
    "payment_term": "",
    "vendor_trn": ""
  },
  "invoice_lines": [
    {
      "line_number": 1,
      "line_description": "",
      "tax_rate": "",
      "line_amount": ""
    }
  ]
}"""


def enhance_image_simple(image):
    """
    Quick image enhancement using PIL only (no OpenCV needed)
    
    Args:
        image: PIL Image object
        
    Returns:
        Enhanced PIL Image
    """
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.5)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(2.0)
    
    # Reduce noise with median filter
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    # Slight brightness increase
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.2)
    
    return image


def preprocess_pdf_for_extraction(pdf_path: str, dpi: int = 400, enhance: bool = True, save_dir: str = None):
    """
    Convert PDF to high-quality images with optional enhancement
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution (300-600 recommended, higher = better quality)
        enhance: Apply image enhancement (improves OCR accuracy)
        save_dir: Directory to save processed images (optional)
        
    Returns:
        List of PIL Images (enhanced if enhance=True)
    """
    
    print("=" * 70)
    print("PDF PREPROCESSING FOR AI EXTRACTION")
    print("=" * 70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ Error: PDF not found at {pdf_path}")
        return None
    
    if save_dir:
        os.makedirs(save_dir, exist_ok=True)
    
    print(f"\n📄 PDF: {pdf_file.name}")
    print(f"🔍 DPI: {dpi} (resolution)")
    print(f"✨ Enhancement: {'Enabled' if enhance else 'Disabled'}")
    print("\nConverting PDF to images...")
    
    try:
        # Convert PDF to images at high resolution
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"   ✅ Converted {len(images)} page(s)")
        
        if enhance:
            print("\nApplying image enhancements...")
            enhanced_images = []
            
            for idx, image in enumerate(images, 1):
                print(f"   Page {idx}/{len(images)}...", end=" ")
                
                # Apply enhancement
                enhanced = enhance_image_simple(image)
                enhanced_images.append(enhanced)
                
                # Save if directory provided
                if save_dir:
                    output_path = os.path.join(save_dir, f"page_{idx}_enhanced.png")
                    enhanced.save(output_path, "PNG", optimize=True, quality=95)
                    print(f"✅ Saved: {output_path}")
                else:
                    print("✅")
            
            images = enhanced_images
        
        print("\n" + "=" * 70)
        print("✅ PREPROCESSING COMPLETE")
        print("=" * 70)
        
        return images
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure pdf2image is installed: pip install pdf2image")
        print("💡 And Poppler is installed (see setup guide)")
        return None


def extract_invoice_with_gemini_enhanced(pdf_path: str, dpi: int = 400, enhance: bool = True):
    """
    Extract invoice using Gemini with preprocessed PDF
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution for PDF conversion
        enhance: Apply image enhancement
        
    Returns:
        Extracted invoice data as JSON string
    """
    
    print("\n" + "=" * 70)
    print("INVOICE EXTRACTION: GEMINI + PREPROCESSING")
    print("=" * 70)
    
    # Step 1: Preprocess PDF
    images = preprocess_pdf_for_extraction(pdf_path, dpi=dpi, enhance=enhance, save_dir="temp_processed")
    
    if not images:
        return None
    
    # Step 2: Upload to Gemini
    print("\n" + "=" * 70)
    print("GEMINI AI EXTRACTION")
    print("=" * 70)
    
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Save first page temporarily for upload
    temp_image_path = "temp_page_1.png"
    images[0].save(temp_image_path, "PNG")
    
    print("\n📤 Uploading processed image to Gemini...")
    
    try:
        uploaded_file = genai.upload_file(temp_image_path)
        print(f"   ✅ Uploaded: {uploaded_file.name}")
        
        print("\n🤖 Processing with Gemini AI...")
        response = model.generate_content([uploaded_file, INVOICE_PROMPT])
        
        result = response.text
        
        # Clean up
        genai.delete_file(uploaded_file.name)
        os.remove(temp_image_path)
        
        print("\n" + "=" * 70)
        print("EXTRACTED INVOICE DATA")
        print("=" * 70)
        print(result)
        print("=" * 70)
        
        # Validate JSON
        try:
            json_data = json.loads(result)
            print("\n✅ Valid JSON output!")
            print(f"   Supplier: {json_data.get('invoice_header', {}).get('supplier_name', 'N/A')}")
            print(f"   Invoice #: {json_data.get('invoice_header', {}).get('invoice_number', 'N/A')}")
            print(f"   Total: {json_data.get('invoice_header', {}).get('invoice_total_amount', 'N/A')}")
        except:
            print("\n⚠️  Output may not be valid JSON")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


def extract_invoice_with_ollama_enhanced(pdf_path: str, model_name: str = "gemma3:27b", dpi: int = 400, enhance: bool = True):
    """
    Extract invoice using Ollama vision model with preprocessed PDF
    
    Args:
        pdf_path: Path to PDF file
        model_name: Ollama vision model
        dpi: Resolution for PDF conversion
        enhance: Apply image enhancement
        
    Returns:
        Extracted invoice data as JSON string
    """
    
    print("\n" + "=" * 70)
    print(f"INVOICE EXTRACTION: OLLAMA ({model_name}) + PREPROCESSING")
    print("=" * 70)
    
    # Step 1: Preprocess PDF
    images = preprocess_pdf_for_extraction(pdf_path, dpi=dpi, enhance=enhance, save_dir="temp_processed")
    
    if not images:
        return None
    
    # Step 2: Process with Ollama
    print("\n" + "=" * 70)
    print("OLLAMA AI EXTRACTION")
    print("=" * 70)
    
    # Save first page for Ollama
    temp_image_path = "temp_page_1.png"
    images[0].save(temp_image_path, "PNG")
    
    print(f"\n🤖 Processing with Ollama ({model_name})...")
    
    try:
        response = ollama.chat(
            model=model_name,
            messages=[{
                'role': 'user',
                'content': INVOICE_PROMPT,
                'images': [temp_image_path]
            }],
            options={
                'temperature': 0.1,
                'num_predict': 2048,
            }
        )
        
        result = response['message']['content']
        
        # Clean up
        os.remove(temp_image_path)
        
        print("\n" + "=" * 70)
        print("EXTRACTED INVOICE DATA")
        print("=" * 70)
        print(result)
        print("=" * 70)
        
        # Validate JSON
        try:
            json_data = json.loads(result)
            print("\n✅ Valid JSON output!")
            print(f"   Supplier: {json_data.get('invoice_header', {}).get('supplier_name', 'N/A')}")
            print(f"   Invoice #: {json_data.get('invoice_header', {}).get('invoice_number', 'N/A')}")
            print(f"   Total: {json_data.get('invoice_header', {}).get('invoice_total_amount', 'N/A')}")
        except:
            print("\n⚠️  Output may not be valid JSON")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return None


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("ENHANCED INVOICE EXTRACTION")
    print("=" * 70)
    print("\nOptions:")
    print("1. Gemini + Preprocessing (Cloud, Fast)")
    print("2. Ollama + Preprocessing (Local, Private)")
    print("=" * 70)
    
    PDF_PATH = r"2.pdf"  # Your PDF file
    
    # Choose one:
    
    # Option 1: Gemini (Cloud-based, fast, requires API key)
    extract_invoice_with_gemini_enhanced(
        pdf_path=PDF_PATH,
        dpi=400,      # Higher DPI = better quality
        enhance=True  # Apply image enhancement
    )
    
    # Option 2: Ollama (Local, private, requires model installed)
    # extract_invoice_with_ollama_enhanced(
    #     pdf_path=PDF_PATH,
    #     model_name="gemma3:27b",  # or "llama3.2-vision"
    #     dpi=400,
    #     enhance=True
    # )
