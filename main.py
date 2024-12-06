from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PyPDF2 import PdfReader, PdfWriter

import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)

# Define the schema for the incoming request
class ReplaceTextRequest(BaseModel):
    file_name: str
    old_text: str
    new_text: str


# handle file uploads
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Ensure the uploads directory exists

# upload multiple files
@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """Endpoint to upload multiple PDF files."""
    uploaded_files = []
    for file in files:
        file_path = Path(UPLOAD_DIR) / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())  # Save file to uploads directory
        uploaded_files.append(file.filename)

    return {"message": "Files uploaded successfully!", "files": uploaded_files}


# List Uploaded Files
@app.get("/files")
async def list_uploaded_files():
    files = os.listdir(UPLOAD_DIR)
    return {"files": files}

# upload single file
@app.post("/replace-address")
async def replace_address(file_name: str, old_address: str, new_address: str):
    """Replace an address in the given PDF file."""
    input_path = Path(UPLOAD_DIR) / file_name
    output_path = Path(UPLOAD_DIR) / f"updated_{file_name}"

    if not input_path.exists():
        return {"error": "File not found"}

    replace_address_in_pdf(input_path, output_path, old_address, new_address)

    return FileResponse(output_path, media_type="application/pdf", filename=f"updated_{file_name}")

# Extract Text from a PDF
@app.get("/extract-text")
async def extract_text(file_name: str):
    file_path = Path(UPLOAD_DIR) / file_name
    if not file_path.exists():
        return {"error": "File not found"}

    reader = PdfReader(file_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return {"file_name": file_name, "text": text}

# Replace Text in a PDF
@app.post("/replace-text")
async def replace_text(request: ReplaceTextRequest):
    try:
        # Access the fields from the request
        file_name = request.file_name
        old_text = request.old_text
        new_text = request.new_text

        # Define file paths
        input_path = Path(UPLOAD_DIR) / file_name
        output_path = Path(UPLOAD_DIR) / f"updated_{file_name}"

        # Check if the file exists
        if not input_path.exists():
            raise HTTPException(status_code=404, detail="File not found")

        # Read the PDF file
        reader = PdfReader(input_path)
        writer = PdfWriter()

        # Iterate over all pages and attempt to replace the text
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            content = page.extract_text()

            # Check if old text is in the content, and replace it
            if old_text in content:
                content = content.replace(old_text, new_text)

            # We need to recreate the page with updated content if modification is done
            page = reader.pages[page_num]
            page.extract_text = lambda: content  # Override extract_text method for testing

            # Add the page to writer
            writer.add_page(page)

        # Save the modified PDF to the output file
        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return {"message": f"Text replacement successful. File saved as {output_path.name}"}

    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    



@app.get("/")
async def read_root():
    return {"message": "Welcome to the PDF address replacement service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
