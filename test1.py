from pathlib import Path
from collections import defaultdict

from docling.document_converter import DocumentConverter
from docling_core.types.doc import TableItem


INPUT_PDF = "hindi.pdf"
OUTPUT_DIR = Path("output")

OUTPUT_DIR.mkdir(exist_ok=True)


converter = DocumentConverter()

result = converter.convert(INPUT_PDF)

doc = result.document


pages = defaultdict(list)


for item, _level in doc.iterate_items():

    if item.prov:
        page_no = item.prov[0].page_no
        pages[page_no].append(item)


for page_no, items in pages.items():

    output = OUTPUT_DIR / f"page_{page_no}.md"

    with open(output, "w", encoding="utf-8") as f:

        f.write(f"# Page {page_no}\n\n")

        for item in items:

            # normal text
            if hasattr(item, "text") and item.text:
                f.write(item.text + "\n\n")


            # tables
            elif isinstance(item, TableItem):

                table = item.export_to_markdown()

                f.write(table)
                f.write("\n\n")


    print("created:", output)
