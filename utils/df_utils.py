from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
import io

def replace_address_in_pdf(input_path, output_path, old_address, new_address):
    """Replaces an address in a PDF and writes the modified PDF to a new file."""
    # Read the PDF
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        # Extract text
        content = page.extract_text()

        # Replace the address if it exists
        if old_address in content:
            # Create an overlay
            packet = io.BytesIO()
            can = canvas.Canvas(packet, pagesize=letter)
            # Overlay white rectangle over the old address (adjust x, y as needed)
            can.setFillColorRGB(1, 1, 1)  # White
            can.rect(100, 700, 300, 20, fill=True, stroke=False)
            # Add new address
            can.setFillColorRGB(0, 0, 0)  # Black
            can.drawString(100, 700, new_address)
            can.save()

            # Merge overlay into the PDF
            packet.seek(0)
            overlay = PdfReader(packet)
            page.merge_page(overlay.pages[0])

        # Add modified page to writer
        writer.add_page(page)

    # Save updated PDF
    with open(output_path, "wb") as output_file:
        writer.write(output_file)
