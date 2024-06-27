import os
import math
import fitz
import re
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from PIL import Image


def create_full_page_table(file_name, rows):
    # Create a PDF file
    pdf = canvas.Canvas(file_name, pagesize=letter)
    width, height = letter

    # Define the column width and row height
    num_cols = 2  # Assuming two columns
    col_width = width / num_cols
    row_height = height / 26

    # Define the maximum number of rows per page
    max_rows_per_page = 26

    # Initialize variables
    current_row = 0
    remaining_rows = len(rows)

    while remaining_rows > 0:
        # Calculate the number of rows to be displayed on the current page
        num_rows_on_page = min(max_rows_per_page, remaining_rows)
        table_data = [['' for _ in range(num_cols)] for _ in range(num_rows_on_page)]

        # Populate the table data for the current page
        for i in range(num_rows_on_page):
            for j, cell in enumerate(rows[current_row]):
                table_data[i][j] = cell
            current_row += 1

        # Create the table with specified column widths and row heights
        table = Table(table_data, colWidths=[col_width] * num_cols, rowHeights=[row_height] * num_rows_on_page)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        # Calculate the position of the table to align it with the top of the page
        table_width, table_height = table.wrap(0, 0)
        x = (width - table_width) / 2
        y = height - table_height  # Adjust y to place the table starting from the top

        # Draw the table on the PDF
        table.drawOn(pdf, x, y)

        # Add a new page if there are remaining rows
        if remaining_rows > max_rows_per_page:
            pdf.showPage()

        # Update remaining rows
        remaining_rows -= num_rows_on_page

    # Save the PDF file
    pdf.save()


def populate_index_table(data: list, txt_file):
    n = 25
    rows = []
    with open('index_page.txt', 'r') as f:
        num_lines = sum(1 for _ in f)
    index_pages = math.ceil(num_lines / 25)

    with open('index_page.txt', 'r') as f:
        for line in f:
            chapter, page_number = line.strip().split(':')
            rows.append([chapter, int(page_number) + index_pages])

    for i in range(n, len(rows) + n, n + 1):
        rows.insert(i, data)

    rows.insert(0, data)
    if rows[-1] == data:
        rows.pop()

    return rows


def natural_sort_key(s):
    # Extract numeric parts of the string and convert them to integers
    return [int(text) if text.isdigit() else text for text in re.split(r'(\d+)', s)]


def images_to_pdf(image_files, output_pdf):
    """Converts a list of image files to a single PDF file."""
    image_list = []
    for img_file in image_files:
        img = Image.open(img_file)
        img = img.convert('RGB')  # Ensure image is in RGB mode
        image_list.append(img)

    if image_list:
        image_list[0].save(output_pdf, save_all=True, append_images=image_list[1:])


def generate_pdf_from_folders(base_dir, output_file, topdown=True, onerror=None, followlinks=False):
    """Generates a single PDF from all folders containing image files in base_dir."""
    os.chdir('..')
    pdf_writer = PdfWriter()

    for root, dirs, files in os.walk(base_dir, topdown=True, onerror=None, followlinks=False):
        dirs.sort(key=natural_sort_key)
        files.sort(key=natural_sort_key)
        image_files = [os.path.join(root, file) for file in files if
                       (file.lower().endswith(('png', 'jpg', 'jpeg', 'tiff', 'bmp', 'gif')) and
                        'poster' not in file.lower())]

        if image_files:
            temp_pdf = os.path.join(root, "temp.pdf")
            images_to_pdf(image_files, temp_pdf)

            temp_pdf_reader = PdfReader(temp_pdf)
            for page_num in range(len(temp_pdf_reader.pages)):
                pdf_writer.add_page(temp_pdf_reader.pages[page_num])

            os.remove(temp_pdf)  # Clean up the temporary PDF file

    # Write the final combined PDF
    with open(output_file, 'wb') as f:
        pdf_writer.write(f)


def merge_pdfs(pdf1_path, pdf2_path, output_path):
    # Open the two PDFs
    with open(pdf1_path, 'rb') as pdf1_file, open(pdf2_path, 'rb') as pdf2_file:
        # Create PdfReader objects
        reader1 = PdfReader(pdf1_file)
        reader2 = PdfReader(pdf2_file)

        # Create PdfWriter object for output
        writer = PdfWriter()

        # Add all pages from the first PDF
        for page in reader1.pages:
            writer.add_page(page)

        # Add all pages from the second PDF
        for page in reader2.pages:
            writer.add_page(page)

        # Write the merged PDF to the output file
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)


def generate_hyperlinks(input_pdf, output_pdf):
    doc = fitz.open(input_pdf)
    for page in doc:
        tabs = page.find_tables()
        if tabs.tables:
            tab_data = [t[1] for t in tabs[0].extract()]
            rows = tabs[0].rows
            for t, r in zip(tab_data, rows):
                if t == 'page number':
                    pass
                else:
                    rect = fitz.Rect(r.cells[1])
                    page.insert_link(
                        {"kind": fitz.LINK_GOTO, "page": int(t) - 1, "from": rect, "to": fitz.Point(100.0, -700.0)}
                    )
    doc.save(output_pdf)
