# md-allthethings
turn all the files into markdown with MistralOCR magic, images optional

# Mistral Batch OCR Script (PDF/Image to Markdown)

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)


This script processes PDF and common image files (PNG, JPG/JPEG, WEBP) in a specified directory using the Mistral AI OCR API. It extracts the text content and saves it as a Markdown (`.md`) file with the same base name as the original file.

## Features

*   **Batch Processing:** Processes all supported files found in the current directory.
*   **Multiple Formats:** Supports PDF, PNG, JPG/JPEG, and WEBP files.
*   **Markdown Output:** Saves extracted text content as `.md` files.
*   **Idempotent:** Skips processing files if a corresponding `.md` file already exists, saving API calls and time.
*   **PDF Image Embedding (Optional):** Can optionally embed Base64-encoded images extracted from PDFs directly into the output Markdown (configurable in the script).

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.8 or higher is recommended. ([Download Python](https://www.python.org/downloads/))
2.  **uv:** A fast Python package installer and virtual environment manager. ([Install uv](https://github.com/astral-sh/uv#installation))
4.  **Mistral AI Account:** You need an account with Mistral AI to obtain an API key. ([Mistral AI Platform](https://console.mistral.ai/))

## Setup and Installation

Follow these steps to set up the project:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/hardymathieu/md-allthethings
    cd md-allthethings
    ```


2.  **Create Virtual Environment:**
    Use `uv` to create an isolated Python environment for the project. This typically creates a `.venv` folder.
    ```bash
    uv venv
    ```

3.  **Activate Virtual Environment:**
    You need to activate the environment in your terminal session. The command differs based on your operating system and shell:

    *   **macOS / Linux (bash/zsh):**
        ```bash
        source .venv/bin/activate
        ```
    *   **Windows (Command Prompt):**
        ```bash
        .venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```powershell
        .venv\Scripts\Activate.ps1
        ```
    *   *(You should see `(.venv)` preceding your terminal prompt)*

4.  **Install Dependencies:**
    Install the required Python packages using `uv` and the `requirements.txt` file.
    ```bash
    uv pip install -r requirements.txt
    ```

## Configuration

1.  **Create `.env` File:**
    The script requires your Mistral AI API key. Create a file named `.env` in the root of the project directory.

2.  **Add API Key to `.env`:**
    Open the `.env` file and add your API key in the following format:
    ```dotenv
    # .env
    MISTRAL_API_KEY=your_mistral_api_key_goes_here
    ```
    Replace `your_mistral_api_key_goes_here` with your actual key.

    **Important:** Do **not** commit your `.env` file to Git. It should be listed in your `.gitignore` file (if you don't have one, create it and add `.env` on a new line).

## Usage

1.  **Place Files:** Copy or move the PDF and image files you want to process into the root directory of the project (the same directory where `mistral_ocr_script.py` is located).

2.  **Run the Script:**
    Make sure your virtual environment is activated (`(.venv)` should be visible in your prompt). Then, simply run the Python script:
    ```bash
    python mistral_ocr_script.py
    ```

3.  **Output:**
    *   The script will print progress messages to the console for each file being processed or skipped.
    *   For each successfully processed file (e.g., `mydocument.pdf`), a corresponding Markdown file (e.g., `mydocument.md`) containing the extracted text will be created in the same directory.
    *   If a `.md` file already exists for a source file, the script will skip processing that source file.
    *   A final summary of processed, skipped, and errored files will be displayed.

## Script Configuration (Internal)

You can modify the behavior slightly by editing the constants at the top of the `mistral_ocr_script.py` file:

*   `INCLUDE_BASE64_IMAGES_FROM_PDF`: Set to `True` if you want images extracted from *PDFs* to be embedded directly into the Markdown output. Set to `False` (default) to only include text. This does *not* affect standalone image file processing.
*   `SUPPORTED_EXTENSIONS`: A set of lowercase file extensions the script will attempt to process.

## Dependencies

This project relies on the following Python packages (managed via `requirements.txt`):

*   `mistralai`: The official Mistral AI Python client.
*   `python-dotenv`: For loading environment variables from the `.env` file.
*   `Pillow`: Python Imaging Library, potentially used by dependencies or for future image handling.

## Notes

*   The Mistral AI API has usage limits and associated costs. Be mindful of the number and size of files you process.
*   OCR accuracy can vary depending on the quality, layout, and language of the source document/image. Complex layouts or low-resolution images may yield suboptimal results.
*   The script currently processes files in the directory where it is run. Output `.md` files are saved in the same directory.
