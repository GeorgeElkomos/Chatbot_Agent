"""
Test file for image analysis using Ollama models
Test Gemma 3:27B with image input
"""

import ollama
from pathlib import Path
import base64


def encode_image_to_base64(image_path: str) -> str:
    """
    Encode image file to base64 string
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Base64 encoded string
    """
    with open(image_path, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def test_gemma_with_image(image_path: str, prompt: str = "Describe this image in detail.", model_name: str = "gemma3:27b"):
    """
    Test Gemma 3:27B model with image input
    
    Args:
        image_path: Path to the image file
        prompt: Question or instruction about the image
        model_name: Ollama model name (default: gemma3:27b)
    """
    
    # Check if image exists
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"Error: Image file not found at {image_path}")
        return None
    
    print("=" * 60)
    print(f"Testing {model_name.upper()} with Image Analysis")
    print("=" * 60)
    print(f"\nImage: {image_file.name}")
    print(f"Prompt: {prompt}")
    print("\nProcessing with Ollama...\n")
    
    try:
        # Generate response with image
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            images=[image_path]
        )
        
        print("Model Response:")
        print("=" * 60)
        print(response['response'])
        print("=" * 60)
        print(f"\n✓ Analysis complete!")
        print(f"Tokens generated: {response.get('eval_count', 'N/A')}")
        print(f"Processing time: {response.get('total_duration', 0) / 1e9:.2f}s")
        
        return response['response']
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure:")
        print(f"1. Model '{model_name}' is installed (run: ollama pull {model_name})")
        print("2. The model supports vision/image input")
        print("3. Ollama is running")
        return None


def test_multiple_images(image_paths: list, prompt: str, model_name: str = "gemma3:27b"):
    """
    Test model with multiple images
    
    Args:
        image_paths: List of paths to image files
        prompt: Question or instruction about the images
        model_name: Ollama model name
    """
    
    print("=" * 60)
    print(f"Testing {model_name.upper()} with Multiple Images")
    print("=" * 60)
    print(f"\nNumber of images: {len(image_paths)}")
    print(f"Prompt: {prompt}")
    print("\nProcessing...\n")
    
    # Verify all images exist
    valid_images = []
    for img_path in image_paths:
        if Path(img_path).exists():
            valid_images.append(img_path)
            print(f"✓ Found: {Path(img_path).name}")
        else:
            print(f"✗ Not found: {img_path}")
    
    if not valid_images:
        print("\nNo valid images found!")
        return None
    
    print("\n" + "-" * 60)
    
    try:
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            images=valid_images
        )
        
        print("\nModel Response:")
        print("=" * 60)
        print(response['response'])
        print("=" * 60)
        print(f"\n✓ Analysis complete!")
        
        return response['response']
        
    except Exception as e:
        print(f"Error: {e}")
        return None


def analyze_invoice_image(image_path: str, model_name: str = "gemma3:27b"):
    """
    Specialized function to extract invoice data from image
    
    Args:
        image_path: Path to the invoice image
        model_name: Ollama model name
    """
    
    invoice_prompt = """Analyze this invoice image and extract the following information:

**INVOICE HEADER:**
- PO Number (Purchase Order Number)
- Supplier Name (Vendor/Company Name)
- Invoice Number
- Invoice Total Amount
- Invoice Date
- Payment Term
- Vendor TRN (Tax Registration Number)

**INVOICE LINES:**
For each line item, extract:
- Line Number
- Line Description
- Tax Rate
- Line Amount

**OUTPUT FORMAT:**
Please provide the data in a structured JSON format like this:
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

If any field is not visible or found, mark it as "Not Found"."""

    return test_gemma_with_image(image_path, invoice_prompt, model_name)


def compare_models_on_image(image_path: str, prompt: str, models: list = ["gemma3:27b", "llava"]):
    """
    Compare different vision models on the same image
    
    Args:
        image_path: Path to the image file
        prompt: Question or instruction
        models: List of model names to compare
    """
    
    print("=" * 80)
    print("MODEL COMPARISON ON IMAGE")
    print("=" * 80)
    
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"Error: Image not found at {image_path}")
        return None
    
    print(f"\nImage: {image_file.name}")
    print(f"Prompt: {prompt}")
    print(f"Models to test: {', '.join(models)}\n")
    
    results = {}
    
    for model_name in models:
        print("\n" + "=" * 80)
        print(f"Testing: {model_name.upper()}")
        print("=" * 80)
        
        try:
            response = ollama.generate(
                model=model_name,
                prompt=prompt,
                images=[image_path]
            )
            
            print(f"\n{model_name} Response:")
            print("-" * 80)
            print(response['response'])
            print("-" * 80)
            
            results[model_name] = {
                'response': response['response'],
                'tokens': response.get('eval_count', 'N/A'),
                'time': f"{response.get('total_duration', 0) / 1e9:.2f}s"
            }
            
        except Exception as e:
            print(f"\n{model_name} Error: {e}")
            results[model_name] = {'error': str(e)}
    
    print("\n\n" + "=" * 80)
    print("COMPARISON SUMMARY")
    print("=" * 80)
    
    for model_name, result in results.items():
        print(f"\n{model_name}:")
        if 'error' in result:
            print(f"  Status: ✗ Error - {result['error']}")
        else:
            print(f"  Status: ✓ Success")
            print(f"  Tokens: {result['tokens']}")
            print(f"  Time: {result['time']}")
    
    return results


def test_image_with_chat(image_path: str, model_name: str = "gemma3:27b"):
    """
    Interactive chat mode with image context
    
    Args:
        image_path: Path to the image file
        model_name: Ollama model name
    """
    
    image_file = Path(image_path)
    if not image_file.exists():
        print(f"Error: Image not found at {image_path}")
        return
    
    print("=" * 60)
    print(f"Interactive Chat with Image - {model_name.upper()}")
    print("=" * 60)
    print(f"\nImage loaded: {image_file.name}")
    print("Type your questions about the image. Type 'exit' or 'quit' to stop.\n")
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['exit', 'quit', 'bye']:
            print("Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            print(f"\n{model_name}: ", end='', flush=True)
            
            response = ollama.generate(
                model=model_name,
                prompt=user_input,
                images=[image_path]
            )
            
            print(response['response'])
            print()
            
        except Exception as e:
            print(f"Error: {e}\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Ollama Vision Model Testing Suite")
    print("=" * 60)
    print()
    
    # TEST 1: Basic image analysis with Gemma 3:27B
    print("\n\nTEST 1: Analyze Single Image")
    print("=" * 60)
    test_gemma_with_image(
        r"test\Screenshot 2025-10-07 195137.png",  # Replace with your image path
        """"You are a professional invoice data extraction specialist. Your task is to accurately and completely extract structured information from the provided invoice document.

========================
INVOICE HEADER FIELDS
========================
Extract the following fields exactly as shown in the invoice:
1. PO Number (Purchase Order Number)
2. Supplier Name (Vendor/Company Name)
3. Invoice Number
4. Invoice Total Amount (Grand Total)
5. Invoice Date
6. Payment Term (e.g., Net 30, Due on Receipt, etc.)
7. Vendor TRN / VAT Number / Tax Registration Number

========================
INVOICE LINE ITEMS
========================
Extract ALL individual line items with these fields:
1. Line Number (Item sequence number)
2. Line Description (Exact item/service description)
3. Tax Rate (VAT or tax percentage)
4. Line Amount (Include currency symbol if present)

========================
IMPORTANT EXTRACTION RULES
========================
- If any field is not present, write "Not Found" or "N/A".
- Preserve all values exactly as they appear — do not modify or infer.
- For dates, keep the exact format from the document (do not reformat).
- For amounts, include the currency symbol (e.g., $1,230.50 or AED 250).
- Preserve decimal precision and spacing exactly.
- For multi-page invoices, include all pages.
- If multiple totals or dates appear, use the one clearly labeled or most relevant.
- Validate that the extracted total makes logical sense relative to line items.
- Ensure the final output is valid JSON — no missing commas, quotes, or brackets.

========================
OUTPUT FORMAT (RETURN AS VALID JSON)
========================
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

========================
VALIDATION BEFORE RETURN
========================
- Check that all expected fields exist in the JSON.
- Ensure no field is left empty — use "Not Found" if missing.
- Verify that the JSON is syntactically correct.
- Make sure line items reflect all items in the invoice.
- Double-check all amounts and text are extracted exactly as in the document.

Now extract the data from the invoice document and return only the valid JSON output.""",
        model_name="gemma3:27b"
    )
    
    # TEST 2: Extract invoice data from image
    """
    print("\n\nTEST 2: Extract Invoice Data from Image")
    print("=" * 60)
    analyze_invoice_image(
        r"test\invoice_image.jpg",  # Replace with your invoice image
        model_name="gemma3:27b"
    )
    """
    
    # TEST 3: Compare different vision models
    """
    print("\n\nTEST 3: Compare Models")
    print("=" * 60)
    compare_models_on_image(
        r"test\sample_image.jpg",
        "What objects can you identify in this image?",
        models=["gemma3:27b", "llava", "llava:13b"]
    )
    """
    
    # TEST 4: Interactive chat with image
    """
    print("\n\nTEST 4: Interactive Chat with Image")
    print("=" * 60)
    test_image_with_chat(
        r"test\sample_image.jpg",
        model_name="gemma3:27b"
    )
    """
    
    # TEST 5: Multiple images analysis
    """
    print("\n\nTEST 5: Analyze Multiple Images")
    print("=" * 60)
    test_multiple_images(
        [
            r"test\image1.jpg",
            r"test\image2.jpg",
            r"test\image3.jpg"
        ],
        "Compare these images and describe the differences.",
        model_name="gemma3:27b"
    )
    """
