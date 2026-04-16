from PyPDF2 import PdfReader
import os

class PDFParser:
    def __init__(self, storage_path):
        self.storage_path = storage_path

    def parse_pdf(self, file_path):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"The file {file_path} does not exist.")
        
        text = ""
        with open(file_path, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        
        return text.strip()  # Return the extracted text without leading/trailing whitespace

    def save_pdf(self, pdf_file):
        file_path = os.path.join(self.storage_path, pdf_file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(pdf_file.file.read())
        return file_path  # Return the path where the PDF is saved