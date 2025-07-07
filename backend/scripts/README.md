# Development Scripts

This directory contains development and debugging scripts for the invoice processing system.

## Scripts

### `debug_parser.py`
Debug script for testing PDF parsing functionality. Useful for troubleshooting parsing issues with specific invoice files.

### `generate_download_link.py`
Generates download links for invoices stored in the database. Useful for testing the download functionality and getting direct access to processed invoices.

### `simple_download_test.py`
Simple test script for validating S3 download URL generation. Tests the complete download workflow from S3 key to accessible URL.

## Usage

All scripts should be run from the backend directory:

```bash
cd backend
python scripts/script_name.py
```

Make sure your virtual environment is activated and all dependencies are installed before running these scripts.
