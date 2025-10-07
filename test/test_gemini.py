"""
Test file for accessing Google Gemini API and Ollama
"""

import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path
import PyPDF2
import ollama

# Load environment variables
load_dotenv()





def test_gemini_basic():
    """Basic test to verify Gemini API connection"""
    
    # Configure the API key
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return
    
    genai.configure(api_key=api_key)
    
    # Initialize the model
    model = genai.GenerativeModel('gemini-2.0-flash-exp')


    
    
    # Test prompt
    prompt = "what is water"
    
    print(f"Sending prompt: {prompt}\n")
    
    try:
        # Generate response
        response = model.generate_content(prompt)
        print("Response from Gemini:")
        print("-" * 50)
        print(response.text)
        print("-" * 50)
        print("\n✓ Gemini API connection successful!")
        
    except Exception as e:
        print(f"Error calling Gemini API: {e}")


def extract_content_from_pdf(pdf_path: str, custom_prompt: str = None):
    """
    Extract and analyze content from a PDF file using Google Gemini
    
    Args:
        pdf_path: Path to the PDF file
        custom_prompt: Optional custom prompt for analysis. If None, will extract all text content
    """
    
    # Configure the API key
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables")
        return
    
    genai.configure(api_key=api_key)
    
    # Check if file exists
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print(f"Processing PDF: {pdf_file.name}")
    print("-" * 60)
    
    try:
        # Upload the PDF file
        print("Uploading PDF to Gemini...")
        uploaded_file = genai.upload_file(pdf_path)
        print(f"✓ File uploaded: {uploaded_file.name}")
        
        # Initialize the model (use gemini-1.5-flash or gemini-1.5-pro for file uploads)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Default prompt if none provided
        if custom_prompt is None:
            custom_prompt = """Please extract and summarize all the content from this PDF. 
            Include:
            1. Main topics and headings
            2. Key information and details
            3. Any tables, lists, or structured data
            4. Important numbers or dates"""
        
        print(f"\nAnalyzing with prompt: {custom_prompt}\n")
        
        # Generate response with the PDF
        response = model.generate_content([uploaded_file, custom_prompt])
        
        print("Extracted Content:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)
        
        # Clean up - delete the uploaded file
        genai.delete_file(uploaded_file.name)
        print("\n✓ PDF analysis complete!")
        
        return response.text
        
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return None


def extract_specific_info_from_pdf(pdf_path: str, question: str):
    """
    Ask specific questions about a PDF document
    
    Args:
        pdf_path: Path to the PDF file
        question: Specific question to ask about the PDF
    """
    
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    if not api_key:
        print("Error: GEMINI_API_KEY not found")
        return
    
    genai.configure(api_key=api_key)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return
    
    print(f"Analyzing PDF: {pdf_file.name}")
    print(f"Question: {question}")
    print("-" * 60)
    
    try:
        # Upload file
        uploaded_file = genai.upload_file(pdf_path)
        
        # Use model with file support
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Ask the specific question
        response = model.generate_content([uploaded_file, question])
        
        print("\nAnswer:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)
        
        # Clean up
        genai.delete_file(uploaded_file.name)
        print("\n✓ Query complete!")
        
        return response.text
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract raw text content from PDF file using PyPDF2
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as string
    """
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"Error: PDF file not found at {pdf_path}")
        return None
    
    print(f"Extracting text from: {pdf_file.name}")
    
    try:
        text_content = []
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            print(f"Total pages: {total_pages}")
            
            for page_num in range(total_pages):
                page = pdf_reader.pages[page_num]
                text = page.extract_text()
                text_content.append(text)
                print(f"✓ Extracted page {page_num + 1}/{total_pages}")
        
        full_text = "\n\n".join(text_content)
        print(f"\n✓ Successfully extracted {len(full_text)} characters")
        return full_text
        
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None


def process_pdf_with_gemini(pdf_path: str, user_prompt: str):
    """
    Better approach: Extract PDF text first, then pass to Gemini with custom prompt
    This gives more control and flexibility
    
    Args:
        pdf_path: Path to the PDF file
        user_prompt: Your custom prompt/question about the content
    """
    
    # Step 1: Extract text from PDF
    print("=" * 60)
    print("STEP 1: Extracting text from PDF")
    print("=" * 60)
    
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text:
        print("Failed to extract text from PDF")
        return None
    
    # Step 2: Send to Gemini with custom prompt
    print("\n" + "=" * 60)
    print("STEP 2: Processing with Gemini AI")
    print("=" * 60)
    
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    if not api_key:
        print("Error: API key not found")
        return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    # Combine PDF content with user's prompt
    full_prompt = f"""Here is the content extracted from a PDF document:

---PDF CONTENT START---
{pdf_text}
---PDF CONTENT END---

{user_prompt}
"""
    
    print(f"\nUser prompt: {user_prompt}")
    print("Processing with Gemini...\n")
    
    try:
        response = model.generate_content(full_prompt)
        
        print("Gemini Response:")
        print("=" * 60)
        print(response.text)
        print("=" * 60)
        print("\n✓ Processing complete!")
        
        return response.text
        
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None


def analyze_pdf_multiple_prompts(pdf_path: str, prompts_list: list):
    """
    Extract PDF once, then run multiple prompts against it
    Very efficient for multiple analyses of the same document
    
    Args:
        pdf_path: Path to the PDF file
        prompts_list: List of prompts to run against the PDF content
    """
    
    # Extract text once
    print("=" * 60)
    print("Extracting PDF text (one time)")
    print("=" * 60)
    
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text:
        return None
    
    # Configure Gemini
    api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    
    results = []
    
    # Run each prompt
    for idx, user_prompt in enumerate(prompts_list, 1):
        print("\n" + "=" * 60)
        print(f"Analysis {idx}/{len(prompts_list)}")
        print("=" * 60)
        print(f"Prompt: {user_prompt}\n")
        
        full_prompt = f"""Here is a PDF document content:

{pdf_text}

{user_prompt}
"""
        
        try:
            response = model.generate_content(full_prompt)
            print("Response:")
            print("-" * 60)
            print(response.text)
            print("-" * 60)
            
            results.append({
                'prompt': user_prompt,
                'response': response.text
            })
            
        except Exception as e:
            print(f"Error: {e}")
            results.append({
                'prompt': user_prompt,
                'response': f"Error: {e}"
            })
    
    print("\n" + "=" * 60)
    print(f"✓ Completed {len(results)} analyses")
    print("=" * 60)
    
    return results


def process_pdf_with_deepseek(pdf_path: str, user_prompt: str, model_name: str = "deepseek-r1:32b"):
    """
    Process PDF using Ollama DeepSeek-R1 model (local inference)
    DeepSeek-R1 is excellent for reasoning and structured data extraction
    
    Args:
        pdf_path: Path to the PDF file
        user_prompt: Your custom prompt/question about the content
        model_name: Ollama model name (default: deepseek-r1:32b)
    """
    
    # Step 1: Extract text from PDF
    print("=" * 60)
    print("STEP 1: Extracting text from PDF")
    print("=" * 60)
    
    pdf_text = extract_text_from_pdf(pdf_path)
    
    if not pdf_text:
        print("Failed to extract text from PDF")
        return None
    
    # Step 2: Process with DeepSeek via Ollama
    print("\n" + "=" * 60)
    print(f"STEP 2: Processing with Ollama ({model_name})")
    print("=" * 60)
    
    # Combine PDF content with user's prompt
    full_prompt = f"""Here is the content extracted from a PDF document:

---PDF CONTENT START---
{pdf_text}
---PDF CONTENT END---

{user_prompt}
"""
    
    print(f"\nUsing model: {model_name}")
    print(f"User prompt: {user_prompt}")
    print("Processing with DeepSeek...\n")
    
    try:
        # Call Ollama API
        response = ollama.generate(
            model=model_name,
            prompt=full_prompt
        )
        
        print("DeepSeek Response:")
        print("=" * 60)
        print(response['response'])
        print("=" * 60)
        print(f"\n✓ Processing complete!")
        print(f"Tokens generated: {response.get('eval_count', 'N/A')}")
        print(f"Processing time: {response.get('total_duration', 0) / 1e9:.2f}s")
        
        return response['response']
        
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        print("\nMake sure:")
        print("1. Ollama is installed and running")
        print(f"2. Model '{model_name}' is downloaded (run: ollama pull {model_name})")
        print("3. Ollama service is running (run: ollama serve)")
        return None


def extract_invoice_with_deepseek(pdf_path: str, model_name: str = "deepseek-r1:32b"):
    """
    Extract structured invoice data using DeepSeek-R1 (optimized for reasoning)
    
    Args:
        pdf_path: Path to the invoice PDF file
        model_name: Ollama model name (default: deepseek-r1:32b)
    """
    
    invoice_prompt = """You are a professional invoice data extraction specialist. Please extract the following information from this invoice document:

**INVOICE HEADER - Extract these fields:**
1. PO Number (Purchase Order Number)
2. Supplier Name (Vendor/Company Name)
3. Invoice Number
4. Invoice Total Amount (Grand Total)
5. Invoice Date
6. Payment Term (e.g., Net 30, Due on Receipt, etc.)
7. Vendor TRN (Tax Registration Number / VAT Number)

**INVOICE LINES - Extract all line items with:**
1. Line Number (Item sequence number)
2. Line Description (Product/Service description)
3. Tax Rate (VAT/Tax percentage)
4. Line Amount (Line total amount)

**IMPORTANT INSTRUCTIONS:**
- If any field is not found in the document, mark it as "Not Found" or "N/A"
- For Invoice Lines, extract ALL line items present in the invoice
- Preserve exact values, especially for amounts and numbers
- For dates, use the format as shown in the document
- For amounts, include currency symbol if present

**OUTPUT FORMAT: Return as JSON:**
```json
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
}
```

Please extract the data now."""
    
    return process_pdf_with_deepseek(pdf_path, invoice_prompt, model_name)


def compare_gemini_vs_deepseek(pdf_path: str, user_prompt: str):
    """
    Compare results from Gemini and DeepSeek side by side
    Useful for evaluating model performance
    
    Args:
        pdf_path: Path to the PDF file
        user_prompt: Prompt to test with both models
    """
    
    print("=" * 80)
    print("COMPARISON: Gemini vs DeepSeek")
    print("=" * 80)
    
    # Extract PDF once
    pdf_text = extract_text_from_pdf(pdf_path)
    if not pdf_text:
        return None
    
    results = {}
    
    # Test with Gemini
    print("\n\n" + "=" * 80)
    print("Testing with GEMINI 2.0 Flash")
    print("=" * 80)
    try:
        api_key = "AIzaSyCOH5doSg_YSyAr8V5RSHAp0R5YbsNRP6g"
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        full_prompt = f"PDF Content:\n{pdf_text}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)
        
        print("\nGemini Response:")
        print("-" * 80)
        print(response.text)
        print("-" * 80)
        results['gemini'] = response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        results['gemini'] = f"Error: {e}"
    
    # Test with DeepSeek
    print("\n\n" + "=" * 80)
    print("Testing with DEEPSEEK-R1:32B")
    print("=" * 80)
    try:
        full_prompt = f"PDF Content:\n{pdf_text}\n\n{user_prompt}"
        response = ollama.generate(model="deepseek-r1:32b", prompt=full_prompt)
        
        print("\nDeepSeek Response:")
        print("-" * 80)
        print(response['response'])
        print("-" * 80)
        results['deepseek'] = response['response']
    except Exception as e:
        print(f"DeepSeek Error: {e}")
        results['deepseek'] = f"Error: {e}"
    
    print("\n\n" + "=" * 80)
    print("COMPARISON COMPLETE")
    print("=" * 80)
    
    return results




if __name__ == "__main__":
    print("=" * 60)
    print("PDF Processing: Gemini & DeepSeek")
    print("=" * 60)
    print()
    
    # Choose which method to use:
    
    # METHOD 1: Extract invoice with Gemini (FAST, Cloud-based)
    """
    print("\n\nMETHOD 1: Extract Invoice with Gemini")
    print("=" * 60)
    prompt = \"\"\"You are a professional invoice data extraction specialist. Please extract the following information from this invoice document:

**INVOICE HEADER - Extract these fields:**
1. PO Number (Purchase Order Number)
2. Supplier Name (Vendor/Company Name)
3. Invoice Number
4. Invoice Total Amount (Grand Total)
5. Invoice Date
6. Payment Term (e.g., Net 30, Due on Receipt, etc.)
7. Vendor TRN (Tax Registration Number / VAT Number)

**INVOICE LINES - Extract all line items with:**
1. Line Number (Item sequence number)
2. Line Description (Product/Service description)
3. Tax Rate (VAT/Tax percentage)
4. Line Amount (Line total amount)

**IMPORTANT INSTRUCTIONS:**
- If any field is not found in the document, mark it as "Not Found" or "N/A"
- For Invoice Lines, extract ALL line items present in the invoice
- Preserve exact values, especially for amounts and numbers
- For dates, use the format as shown in the document
- For amounts, include currency symbol if present

**OUTPUT FORMAT: Return as JSON:**
```json
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
}
```

Please extract the data now.\"\"\"
    
    process_pdf_with_gemini(r"test\2.pdf", prompt)
    """
    
    # METHOD 2: Extract invoice with DeepSeek-R1 (LOCAL, Better reasoning)
    print("\n\nMETHOD 2: Extract Invoice with DeepSeek-R1:32B")
    print("=" * 60)
    print("Note: Make sure to run 'ollama pull deepseek-r1:32b' first\n")
    
    extract_invoice_with_deepseek(r"test\2.pdf")
    
    # METHOD 3: Custom prompt with DeepSeek
    """
    print("\n\nMETHOD 3: Custom Prompt with DeepSeek")
    print("=" * 60)
    process_pdf_with_deepseek(
        r"test\2.pdf",
        "Summarize this document in 3 bullet points and list all amounts mentioned."
    )
    """
    
    # METHOD 4: Compare both models side by side
    """
    print("\n\nMETHOD 4: Compare Gemini vs DeepSeek")
    print("=" * 60)
    compare_gemini_vs_deepseek(
        r"test\2.pdf",
        "Extract all dates and financial amounts from this invoice."
    )
    """
    
   

