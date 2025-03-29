#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mistral OCR PDF/Image to Markdown Converter Script (Using Standard Exceptions)

This script iterates through PDF and supported image files in the current directory,
uses the Mistral OCR API to extract text (and optionally images from PDFs),
and saves the output as Markdown (.md) files with the same base name.
It relies on standard Python exceptions for error handling related to the API.
"""

# --- CONFIGURATION ---
INCLUDE_BASE64_IMAGES_FROM_PDF = False
SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}
# --- END CONFIGURATION ---

# Import necessary libraries
import os
import base64
import mimetypes
import sys
from pathlib import Path
from typing import Dict, List, Any

from dotenv import load_dotenv
# Use the correct client class name based on your installed version
# It's often MistralClient or just Mistral
try:
    from mistralai import MistralClient as MistralAPIClient # Try newer client name
except ImportError:
    from mistralai import Mistral as MistralAPIClient # Fallback to older name

print("Libraries imported.")

# --- Helper Functions ---

def replace_images_in_markdown(markdown_str: str, images_dict: Dict[str, str]) -> str:
    """Replaces image placeholders in markdown with base64 data."""
    if not images_dict:
        return markdown_str
    updated_markdown = markdown_str
    for img_id, base64_data_url in images_dict.items():
        placeholder = f"![{img_id}]({img_id})"
        replacement = f"![{img_id}]({base64_data_url})"
        updated_markdown = updated_markdown.replace(placeholder, replacement)
    return updated_markdown

def generate_markdown_from_response(
    ocr_response: Any, include_images: bool
) -> str:
    """Combines OCR text and optionally images into markdown."""
    markdown_parts: List[str] = []
    if not hasattr(ocr_response, 'pages') or not ocr_response.pages:
         print("Warning: OCR response object does not contain 'pages' or is empty.")
         return ""

    for i, page in enumerate(ocr_response.pages):
        page_num = i + 1
        if not hasattr(page, 'markdown'):
             print(f"Warning: Page {page_num} object missing 'markdown' attribute. Skipping page.")
             continue
        page_markdown = page.markdown
        page_images = getattr(page, 'images', [])

        if include_images and page_images:
            image_data = {}
            for img in page_images:
                if not hasattr(img, 'id') or not hasattr(img, 'image_base64'):
                     print(f"Warning: Image object on page {page_num} missing 'id' or 'image_base64'. Skipping image.")
                     continue
                image_data[img.id] = f"data:image/png;base64,{img.image_base64}"
            page_markdown = replace_images_in_markdown(page_markdown, image_data)
        markdown_parts.append(page_markdown)

    return "\n\n---\n\n".join(markdown_parts)

# --- Core Processing Logic ---

def process_pdf_file(
    client: MistralAPIClient, file_path: Path, include_images: bool
) -> Any | None:
    """Uploads PDF using the dictionary format, gets URL, sends for OCR."""
    print(f"  Processing PDF: {file_path.name}...")
    uploaded_file_id = None

    try:
        # 1. Upload PDF file using the dictionary structure from your example
        print("    Uploading file using dictionary format...")
        with open(file_path, "rb") as f:
            # --- FIX: Use the dictionary format for the 'file' parameter ---
            file_data_dict = {
                "file_name": file_path.name,
                "content": f  # Pass the file object handle here
            }
            # --- End of FIX ---

            # Prioritize 'upload' method based on your example, fallback to 'create'
            if hasattr(client.files, 'upload'):
                uploaded_file_obj = client.files.upload(
                    file=file_data_dict,
                    purpose="ocr"
                )
            elif hasattr(client.files, 'create'):
                 # Fallback in case 'upload' isn't present in some client version
                 uploaded_file_obj = client.files.create(
                     file=file_data_dict,
                     purpose="ocr"
                 )
            else:
                 print("Error: Could not find a suitable file upload/create method on the client.", file=sys.stderr)
                 return None

            uploaded_file_id = uploaded_file_obj.id
            print(f"    File uploaded successfully. File ID: {uploaded_file_id}")

        # 2. Get signed URL
        print("    Getting signed URL...")
        # Use 'get_signed_url' as in your example and previous attempts
        signed_url_obj = client.files.get_signed_url(file_id=uploaded_file_id)
        # Extract the URL string - check common attribute names
        signed_url_str = getattr(signed_url_obj, 'signed_url', getattr(signed_url_obj, 'url', None))

        if not signed_url_str:
             print("Error: Could not retrieve signed URL string from the response object.", file=sys.stderr)
             # Attempt cleanup before returning None
             raise Exception("Failed to get signed URL string from response.") # Ensures finally block runs

        print("    Signed URL obtained.")

        # 3. Process PDF with OCR
        print("    Sending to Mistral OCR...")
        pdf_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={"type": "document_url", "document_url": signed_url_str},
            include_image_base64=include_images # Correctly passed here
        )
        print("    OCR processing complete.")
        return pdf_response

    except IOError as e:
        # Handle file system errors during file open/read
        print(f"  File Error accessing PDF {file_path.name}: {e}")
        return None
    except Exception as e:
        # Catch other exceptions during API interaction or processing
        print(f"  Error during PDF processing or API interaction for {file_path.name}: {e}")
        # Optionally print the type for debugging if needed:
        # print(f"  Error Type: {type(e)}")
        return None # Indicate failure
    finally:
        # 4. Clean up uploaded file - runs even if errors occur after upload
        if uploaded_file_id:
            try:
                print(f"    Attempting to clean up uploaded file: {uploaded_file_id}")
                # Use 'delete' method as assumed before for cleanup
                client.files.delete(file_id=uploaded_file_id)
                print(f"    Cleaned up uploaded file: {uploaded_file_id}")
            except Exception as e_del: # Catch any error during deletion
                print(f"    Warning: Could not delete uploaded file {uploaded_file_id}: {e_del}")



def process_image_file(
    client: MistralAPIClient, file_path: Path
) -> Any | None:
    """Encodes image, sends for OCR, handling errors generically."""
    print(f"  Processing Image: {file_path.name}...")
    try:
        # 1. Read and encode image
        print("    Reading and encoding image...")
        image_bytes: bytes | None = None
        try:
            with open(file_path, "rb") as f:
                image_bytes = f.read()
            if not image_bytes:
                 print(f"  Error: Read 0 bytes from image file {file_path.name}")
                 return None
            print(f"    Read {len(image_bytes)} bytes from {file_path.name}")
        except IOError as e:
             print(f"  File Error reading image file {file_path.name} before encoding: {e}")
             return None

        encoded_string = base64.b64encode(image_bytes).decode("utf-8")
        print(f"    Encoded string length: {len(encoded_string)}") # Check size indicator

        # 2. Determine MIME type - WITH DEBUGGING
        mime_type_guessed, _ = mimetypes.guess_type(file_path)
        print(f"    MIME type guessed by mimetypes: {mime_type_guessed}") # DEBUG PRINT

        final_mime_type = mime_type_guessed # Start with the guessed type
        if not final_mime_type:
            ext = file_path.suffix.lower()
            print(f"    MIME guess failed, falling back on extension: {ext}") # DEBUG PRINT
            mime_map = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
            # Use get with a default, but be specific if possible
            final_mime_type = mime_map.get(ext)
            if not final_mime_type:
                 print(f"    Extension fallback failed, defaulting to image/jpeg.") # DEBUG PRINT
                 final_mime_type = "image/jpeg" # Default fallback

        print(f"    Using final MIME type: {final_mime_type}") # DEBUG PRINT

        # Construct the data URL
        base64_data_url = f"data:{final_mime_type};base64,{encoded_string}"
        # Print only the prefix and length, not the huge string
        print(f"    Sending Data URL prefix: data:{final_mime_type};base64,... (length: {len(encoded_string)})") # DEBUG PRINT

        # 3. Process image with OCR using the data URL
        print("    Sending to Mistral OCR API...")
        image_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": base64_data_url
            }
        )
        print("    OCR processing complete.")
        return image_response

    # Keep existing IOError handling if needed for other potential issues
    except IOError as e:
        print(f"  File Error during image processing (check permissions/existence): {file_path.name}: {e}")
        return None
    except Exception as e:
        # Catch other exceptions, including API errors (like the one you saw)
        print(f"  Error during image processing or API interaction for {file_path.name}: {e}")
        # Optionally print type again if needed: print(f"  Error Type: {type(e)}")
        return None

# --- Main Execution ---

# --- Main Execution ---

def main():
    """Main function to orchestrate the OCR processing."""
    load_dotenv()
    api_key = os.getenv("MISTRAL_API_KEY")

    if not api_key:
        print("Error: MISTRAL_API_KEY not found in environment variables or .env file.", file=sys.stderr)
        sys.exit(1)
    print("Mistral API Key loaded successfully.")

    try:
        client = MistralAPIClient(api_key=api_key)
        print("Mistral client initialized.")
    except Exception as e:
        print(f"Error initializing Mistral client: {e}", file=sys.stderr)
        sys.exit(1)

    script_dir = Path(".")
    files_processed = 0
    files_skipped = 0 # Counter for files skipped due to existing .md or other reasons
    errors_occurred = 0

    print(f"\nStarting OCR processing in directory: {script_dir.resolve()}")
    print(f"Include base64 images from PDFs: {INCLUDE_BASE64_IMAGES_FROM_PDF}")
    print(f"Supported extensions: {SUPPORTED_EXTENSIONS}\n")

    try:
        all_items = list(script_dir.iterdir())
    except OSError as e:
        print(f"Error listing files in directory {script_dir.resolve()}: {e}", file=sys.stderr)
        sys.exit(1)

    # Filter for supported files only (excluding .md files explicitly)
    files_to_process = [
        item for item in all_items
        if item.is_file()
           and item.suffix.lower() in SUPPORTED_EXTENSIONS
           and item.suffix.lower() != ".md" # Ensure we don't try to process existing output
    ]

    if not files_to_process:
        print("No supported files found to process in the current directory.")
        sys.exit(0)

    print(f"Found {len(files_to_process)} potential files to process.")

    for file_path in files_to_process:
        print(f"\nProcessing file: {file_path.name}")
        output_md_path = file_path.with_suffix(".md")

        # --- ADDED CHECK FOR EXISTING MARKDOWN FILE ---
        if output_md_path.exists():
            print(f"  Skipping: Output file {output_md_path.name} already exists.")
            files_skipped += 1 # Increment the skipped counter
            continue # Move to the next file in the list immediately
        # --- END OF ADDED CHECK ---

        # Avoid processing the script itself (existing check)
        try:
             script_file_path = Path(__file__).resolve()
             if file_path.resolve() == script_file_path:
                 print(f"  Skipping: Cannot process the script file itself ({file_path.name}).")
                 files_skipped += 1
                 continue
        except NameError:
             # __file__ might not be defined in some environments (like interactive)
             pass

        # Original processing logic starts here
        ocr_response = None
        file_type = file_path.suffix.lower()

        try:
            # Calls to process_pdf_file / process_image_file
            if file_type == ".pdf":
                ocr_response = process_pdf_file(
                    client, file_path, INCLUDE_BASE64_IMAGES_FROM_PDF
                )
            elif file_type in SUPPORTED_EXTENSIONS: # Should be true if we got here
                ocr_response = process_image_file(client, file_path)
            # No explicit 'else' needed because filtering excludes unsupported types

            # Handling of ocr_response
            if ocr_response:
                print("  Generating Markdown content...")
                markdown_content = generate_markdown_from_response(
                    ocr_response,
                    include_images=(file_type == ".pdf" and INCLUDE_BASE64_IMAGES_FROM_PDF)
                )

                if not markdown_content and hasattr(ocr_response, 'pages') and ocr_response.pages:
                     print(f"  Warning: Markdown generation resulted in empty content for {file_path.name}, though pages were present.")
                elif not markdown_content:
                     print(f"  Warning: Markdown generation resulted in empty content for {file_path.name}.")

                # Writing the markdown file
                print(f"  Saving Markdown to: {output_md_path.name}")
                try:
                    with open(output_md_path, "w", encoding="utf-8") as f:
                        f.write(markdown_content)
                    print(f"  Successfully saved {output_md_path.name}")
                    files_processed += 1
                except IOError as e:
                    print(f"  Error writing Markdown file {output_md_path.name}: {e}")
                    errors_occurred += 1
            else:
                # Processing function returned None (error already logged)
                print(f"  Skipping Markdown generation due to previous error for {file_path.name}.")
                errors_occurred += 1 # Count error reported by processing function

        # Error handling for the main processing block
        except Exception as e:
            print(f"  An unexpected critical error occurred while processing {file_path.name}: {e}")
            errors_occurred += 1
        # End of loop for one file

    print("\n--- Processing Summary ---")
    print(f"Files processed successfully: {files_processed}")
    # Updated summary message to be clearer about skip reasons
    print(f"Files skipped (already processed, self, etc.): {files_skipped}")
    print(f"Errors encountered: {errors_occurred}")
    print("--------------------------\n")

    sys.exit(1 if errors_occurred > 0 else 0)

# Standard Python script entry point remains the same
if __name__ == "__main__":
    main()