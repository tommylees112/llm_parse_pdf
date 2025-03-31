import PyPDF2
from loguru import logger


def test_main_with_subset_pages():
    source = "downloaded_pdf.pdf"
    is_drive_file = False

    # Override total_pages and modify pdf_reader to only include specified pages
    selected_pages = [17, 18, 19]  # 0-based indexing for pages 18,19,20

    # ====================== #
    # TEST #
    # Create a new PDF with only the selected pages
    new_reader = PyPDF2.PdfReader(source)
    pdf_writer = PyPDF2.PdfWriter()

    for page_num in selected_pages:
        pdf_writer.add_page(new_reader.pages[page_num])

    # Create a temporary file to store the subset PDF
    temp_pdf_path = f"temp_{source}_subset.pdf"
    with open(temp_pdf_path, "wb") as temp_file:
        pdf_writer.write(temp_file)

    # Now read the temporary file with selected pages
    pdf_reader = PyPDF2.PdfReader(temp_pdf_path)
    total_pages = len(pdf_reader.pages)
    # ====================== #

    logger.info(f"Processing only pages 18,19,20 ({total_pages} pages total)")
