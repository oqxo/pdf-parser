"""
Docling-based PDF to HTML Converter
Converts PDFs (with mixed languages, tables, etc.) to clean, readable HTML.
"""

from pathlib import Path
from collections import defaultdict
from typing import Optional
import logging
from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PDFToHTMLConverter:
    """Convert PDF documents to HTML with proper styling and structure."""
    
    def __init__(self, input_pdf: str, output_dir: str = "output"):
        """
        Initialize converter.
        
        Args:
            input_pdf: Path to input PDF file
            output_dir: Directory for output HTML file
        """
        self.input_pdf = Path(input_pdf)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        if not self.input_pdf.exists():
            raise FileNotFoundError(f"PDF not found: {self.input_pdf}")
        
        logger.info(f"Initialized converter for: {self.input_pdf}")
    
    def convert(self) -> Path:
        """
        Convert PDF to HTML.
        
        Returns:
            Path to generated HTML file
        """
        logger.info("Starting PDF conversion...")
        
        # Convert PDF using Docling
        converter = DocumentConverter()
        result = converter.convert(str(self.input_pdf))
        doc = result.document
        
        # Group items by page
        pages = defaultdict(list)
        for item, _level in doc.iterate_items():
            if item.prov:
                page_no = item.prov[0].page_no
                pages[page_no].append(item)
        
        logger.info(f"Extracted {len(pages)} pages from PDF")
        
        # Generate HTML
        html_content = self._generate_html(pages, doc)
        
        # Write to file
        output_file = self.output_dir / f"{self.input_pdf.stem}.html"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        logger.info(f"✓ HTML generated: {output_file}")
        return output_file
    
    def _generate_html(self, pages: dict, doc) -> str:
        """
        Generate complete HTML document.
        
        Args:
            pages: Dictionary mapping page numbers to content items
            doc: Docling document object
            
        Returns:
            HTML string
        """
        html_parts = [self._get_html_header()]
        
        # Process each page
        for page_no in sorted(pages.keys()):
            items = pages[page_no]
            html_parts.append(self._process_page(page_no, items))
        
        html_parts.append(self._get_html_footer())
        
        return "\n".join(html_parts)
    
    def _process_page(self, page_no: int, items: list) -> str:
        """
        Process single page content.
        
        Args:
            page_no: Page number
            items: List of content items on page
            
        Returns:
            HTML string for the page
        """
        page_html = []
        
        # Page break with page number
        page_html.append(f'    <div class="page">')
        page_html.append(f'      <div class="page-number">Page {page_no}</div>')
        page_html.append(f'      <div class="page-content">')
        
        for item in items:
            # Process text content
            if hasattr(item, "text") and item.text and not isinstance(item, TableItem):
                text = item.text.strip()
                if text:
                    page_html.append(f'        <p>{self._escape_html(text)}</p>')
            
            # Process tables
            elif isinstance(item, TableItem):
                table_html = self._process_table(item)
                page_html.append(f'        {table_html}')
        
        page_html.append(f'      </div>')
        page_html.append(f'    </div>')
        
        return "\n".join(page_html)
    
    def _process_table(self, table_item: TableItem) -> str:
        """
        Convert table to HTML.
        
        Args:
            table_item: TableItem from Docling
            
        Returns:
            HTML table string
        """
        # Get markdown and convert to HTML table
        md_table = table_item.export_to_markdown()
        html_table = self._markdown_table_to_html(md_table)
        return html_table
    
    def _markdown_table_to_html(self, md_table: str) -> str:
        """
        Convert Markdown table to HTML table.
        
        Args:
            md_table: Markdown formatted table string
            
        Returns:
            HTML table string
        """
        lines = md_table.strip().split("\n")
        if not lines:
            return ""
        
        html_lines = ['<div class="table-wrapper">']
        html_lines.append('  <table>')
        
        header_done = False
        
        for line in lines:
            line = line.strip()
            
            # Skip separator lines
            if line.startswith("|") and all(c in "|- " for c in line):
                header_done = True
                continue
            
            # Process table rows
            if line.startswith("|") and line.endswith("|"):
                cells = [cell.strip() for cell in line.split("|")[1:-1]]
                
                if not header_done:
                    # Header row
                    html_lines.append('    <thead>')
                    html_lines.append('      <tr>')
                    for cell in cells:
                        cell_content = self._escape_html(cell)
                        html_lines.append(f'        <th>{cell_content}</th>')
                    html_lines.append('      </tr>')
                    html_lines.append('    </thead>')
                    html_lines.append('    <tbody>')
                else:
                    # Data row
                    html_lines.append('      <tr>')
                    for cell in cells:
                        cell_content = self._escape_html(cell)
                        html_lines.append(f'        <td>{cell_content}</td>')
                    html_lines.append('      </tr>')
        
        html_lines.append('    </tbody>')
        html_lines.append('  </table>')
        html_lines.append('</div>')
        
        return "\n".join(html_lines)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
    
    def _get_html_header(self) -> str:
        """Get HTML header with styling."""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PDF Document</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background-color: #f5f5f5;
            padding: 20px;
            line-height: 1.6;
            color: #333;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
        
        .page {
            margin-bottom: 40px;
            padding-bottom: 30px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .page:last-child {
            border-bottom: none;
            margin-bottom: 0;
            padding-bottom: 0;
        }
        
        .page-number {
            font-size: 0.9em;
            color: #999;
            margin-bottom: 15px;
            font-weight: 500;
        }
        
        .page-content {
            font-size: 1em;
        }
        
        p {
            margin-bottom: 12px;
            text-align: justify;
        }
        
        .table-wrapper {
            margin: 20px 0;
            overflow-x: auto;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background-color: #fafafa;
        }
        
        thead {
            background-color: #f0f0f0;
        }
        
        th {
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
            color: #222;
        }
        
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #e8e8e8;
        }
        
        tbody tr:hover {
            background-color: #f9f9f9;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 20px;
            }
            
            table {
                font-size: 0.9em;
            }
            
            th, td {
                padding: 8px;
            }
        }
        
        @media print {
            body {
                background-color: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
                padding: 0;
            }
        }
    </style>
</head>
<body>
    <div class="container">"""
    
    def _get_html_footer(self) -> str:
        """Get HTML footer."""
        return """    </div>
</body>
</html>"""


def main():
    """Main entry point."""
    try:
        # Configuration
        INPUT_PDF = "268548.pdf"  # Change this to your PDF path
        OUTPUT_DIR = "output"
        
        # Convert
        converter = PDFToHTMLConverter(INPUT_PDF, OUTPUT_DIR)
        output_file = converter.convert()
        
        logger.info(f"✓ Done! Open in browser: {output_file}")
        
    except Exception as e:
        logger.error(f"✗ Conversion failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
