"""
Enhanced PDF Extraction and Preprocessing for Better OCR/Extraction Quality
"""

from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
from pathlib import Path
import pytesseract
import os


def enhance_image_for_ocr(image):
    """
    Apply image preprocessing to improve OCR/extraction quality
    
    Args:
        image: PIL Image object
        
    Returns:
        Enhanced PIL Image
    """
    # Convert PIL to OpenCV format
    img_array = np.array(image)
    
    # Convert to grayscale if not already
    if len(img_array.shape) == 3:
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    else:
        gray = img_array
    
    # 1. Noise Removal (removes small artifacts)
    denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
    
    # 2. Thresholding (converts to pure black and white)
    # Use adaptive thresholding for better results with varying lighting
    thresh = cv2.adaptiveThreshold(
        denoised, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY, 
        11, 2
    )
    
    # 3. Deskew (straighten rotated text)
    coords = np.column_stack(np.where(thresh > 0))
    angle = cv2.minAreaRect(coords)[-1]
    
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle
    
    # Only rotate if angle is significant
    if abs(angle) > 0.5:
        (h, w) = thresh.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            thresh, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
    else:
        rotated = thresh
    
    # 4. Morphological operations (improve text structure)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
    morph = cv2.morphologyEx(rotated, cv2.MORPH_CLOSE, kernel)
    
    # Convert back to PIL Image
    enhanced_image = Image.fromarray(morph)
    
    return enhanced_image


def preprocess_pdf_advanced(pdf_path: str, output_dir: str = None, dpi: int = 300):
    """
    Convert PDF to high-quality preprocessed images
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save processed images (optional)
        dpi: Resolution for conversion (300-600 recommended, higher = better quality)
        
    Returns:
        List of preprocessed PIL Images
    """
    
    print("=" * 70)
    print("ADVANCED PDF PREPROCESSING")
    print("=" * 70)
    
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"❌ Error: PDF not found at {pdf_path}")
        return None
    
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📄 PDF: {pdf_file.name}")
    print(f"🔍 DPI: {dpi} (higher = better quality, slower)")
    print("\nStep 1: Converting PDF to images...")
    
    try:
        # Convert PDF to images at high resolution
        images = convert_from_path(pdf_path, dpi=dpi)
        print(f"   ✅ Converted {len(images)} page(s)")
        
        print("\nStep 2: Applying image enhancements...")
        enhanced_images = []
        
        for idx, image in enumerate(images, 1):
            print(f"   Processing page {idx}/{len(images)}...", end=" ")
            
            # Apply enhancements
            enhanced = enhance_image_for_ocr(image)
            enhanced_images.append(enhanced)
            
            # Save if output directory provided
            if output_dir:
                output_path = os.path.join(output_dir, f"page_{idx}_enhanced.png")
                enhanced.save(output_path, "PNG", optimize=True, quality=95)
                print(f"✅ Saved: {output_path}")
            else:
                print("✅")
        
        print("\n" + "=" * 70)
        print("✅ PREPROCESSING COMPLETE")
        print("=" * 70)
        
        return enhanced_images
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Poppler is installed (see setup guide)")
        return None


def extract_text_with_tesseract(image):
    """
    Extract text from image using Tesseract OCR with optimized settings
    
    Args:
        image: PIL Image object
        
    Returns:
        Extracted text as string
    """
    # Tesseract configuration for better accuracy
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    
    # Extract text
    text = pytesseract.image_to_string(image, config=custom_config)
    
    return text


def preprocess_and_extract_text(pdf_path: str, dpi: int = 300, save_images: bool = False):
    """
    Complete pipeline: Preprocess PDF and extract text
    
    Args:
        pdf_path: Path to PDF file
        dpi: Resolution (300-600 recommended)
        save_images: Whether to save preprocessed images
        
    Returns:
        Extracted text from all pages
    """
    
    output_dir = "preprocessed_pages" if save_images else None
    
    # Preprocess PDF
    enhanced_images = preprocess_pdf_advanced(pdf_path, output_dir, dpi)
    
    if not enhanced_images:
        return None
    
    print("\n" + "=" * 70)
    print("EXTRACTING TEXT WITH TESSERACT OCR")
    print("=" * 70)
    
    all_text = []
    
    for idx, image in enumerate(enhanced_images, 1):
        print(f"\nExtracting text from page {idx}/{len(enhanced_images)}...")
        
        text = extract_text_with_tesseract(image)
        all_text.append(f"=== PAGE {idx} ===\n{text}")
        
        print(f"   ✅ Extracted {len(text)} characters")
    
    full_text = "\n\n".join(all_text)
    
    print("\n" + "=" * 70)
    print("✅ TEXT EXTRACTION COMPLETE")
    print(f"   Total pages: {len(enhanced_images)}")
    print(f"   Total characters: {len(full_text)}")
    print("=" * 70)
    
    return full_text


def simple_image_enhancement(image_path: str, output_path: str = None):
    """
    Quick image enhancement without OpenCV (PIL only)
    Good for simple cases without complex preprocessing
    
    Args:
        image_path: Path to image file
        output_path: Where to save enhanced image (optional)
        
    Returns:
        Enhanced PIL Image
    """
    
    print(f"📄 Enhancing image: {Path(image_path).name}")
    
    # Open image
    image = Image.open(image_path)
    
    # Convert to grayscale
    image = image.convert('L')
    
    # Increase contrast
    enhancer = ImageEnhance.Contrast(image)
    image = enhancer.enhance(2.0)
    
    # Increase sharpness
    enhancer = ImageEnhance.Sharpness(image)
    image = enhancer.enhance(1.5)
    
    # Apply slight blur to reduce noise
    image = image.filter(ImageFilter.MedianFilter(size=3))
    
    # Increase brightness slightly
    enhancer = ImageEnhance.Brightness(image)
    image = enhancer.enhance(1.1)
    
    # Save if output path provided
    if output_path:
        image.save(output_path, "PNG", optimize=True, quality=95)
        print(f"   ✅ Saved: {output_path}")
    
    print("   ✅ Enhancement complete!")
    
    return image


if __name__ == "__main__":
    print("PDF Enhancement & Extraction Tools")
    print("=" * 70)
    print()
    
    # Example 1: Preprocess PDF and save enhanced images
    print("Example 1: Preprocess PDF (with image enhancement)")
    print("-" * 70)
    preprocess_pdf_advanced(
        pdf_path=r"2.pdf",
        output_dir=r"preprocessed_output",
        dpi=400  # Higher DPI for better quality
    )
    
    # Example 2: Complete extraction pipeline
    print("\n\nExample 2: Preprocess + Extract Text")
    print("-" * 70)
    text = preprocess_and_extract_text(
        pdf_path=r"2.pdf",
        dpi=300,
        save_images=True
    )
    
    if text:
        # Save extracted text
        with open("extracted_text.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("\n📝 Text saved to: extracted_text.txt")
    
    # Example 3: Simple image enhancement
    print("\n\nExample 3: Simple Image Enhancement (PIL only)")
    print("-" * 70)
    simple_image_enhancement(
        image_path=r"Screenshot 2025-10-07 195137.png",
        output_path=r"enhanced_screenshot.png"
    )
