"""
PDF Operations Module
Provides functionality to generate, read, and manipulate PDF files.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter, PdfMerger
from datetime import datetime
import os


class PDFGenerator:
    """Generate PDF documents with various content types."""
    
    def __init__(self, filename=None, page_size=letter):
        """
        Initialize PDF Generator.
        
        Args:
            filename (str): Output PDF filename
            page_size: Page size (letter, A4, etc.)
        """
        if filename is None:
            filename = f"document_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        self.filename = filename
        self.page_size = page_size
        self.doc = SimpleDocTemplate(filename, pagesize=page_size)
        self.styles = getSampleStyleSheet()
        self.story = []
    
    def add_title(self, text):
        """Add a title to the document."""
        title_style = self.styles['Title']
        self.story.append(Paragraph(text, title_style))
        self.story.append(Spacer(1, 0.3 * inch))
        return self
    
    def add_heading(self, text, level=1):
        """Add a heading to the document."""
        heading_style = self.styles[f'Heading{level}']
        self.story.append(Paragraph(text, heading_style))
        self.story.append(Spacer(1, 0.2 * inch))
        return self
    
    def add_paragraph(self, text):
        """Add a paragraph to the document."""
        para_style = self.styles['BodyText']
        self.story.append(Paragraph(text, para_style))
        self.story.append(Spacer(1, 0.1 * inch))
        return self
    
    def add_bullet_list(self, items):
        """Add a bullet list to the document."""
        bullet_style = self.styles['Bullet']
        for item in items:
            self.story.append(Paragraph(f"• {item}", bullet_style))
        self.story.append(Spacer(1, 0.1 * inch))
        return self
    
    def add_table(self, data, col_widths=None):
        """
        Add a table to the document.
        
        Args:
            data: List of lists containing table data
            col_widths: List of column widths
        """
        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        self.story.append(table)
        self.story.append(Spacer(1, 0.2 * inch))
        return self
    
    def add_page_break(self):
        """Add a page break."""
        self.story.append(PageBreak())
        return self
    
    def build(self):
        """Build and save the PDF document."""
        self.doc.build(self.story)
        print(f"PDF generated successfully: {self.filename}")
        return self.filename


class PDFOperations:
    """Perform operations on existing PDF files."""
    
    @staticmethod
    def read_pdf(filename):
        """
        Read PDF and extract text content.
        
        Args:
            filename (str): Path to PDF file
            
        Returns:
            dict: PDF metadata and content
        """
        try:
            reader = PdfReader(filename)
            content = {
                'num_pages': len(reader.pages),
                'metadata': reader.metadata,
                'pages': []
            }
            
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                content['pages'].append({
                    'page_number': i + 1,
                    'text': text
                })
            
            return content
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return None
    
    @staticmethod
    def extract_text(filename, page_numbers=None):
        """
        Extract text from specific pages or all pages.
        
        Args:
            filename (str): Path to PDF file
            page_numbers (list): List of page numbers to extract (1-indexed), None for all
            
        Returns:
            str: Extracted text
        """
        try:
            reader = PdfReader(filename)
            text = ""
            
            if page_numbers is None:
                page_numbers = range(1, len(reader.pages) + 1)
            
            for page_num in page_numbers:
                if 0 < page_num <= len(reader.pages):
                    page = reader.pages[page_num - 1]
                    text += f"\n--- Page {page_num} ---\n"
                    text += page.extract_text()
            
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return None
    
    @staticmethod
    def merge_pdfs(pdf_files, output_filename):
        """
        Merge multiple PDF files into one.
        
        Args:
            pdf_files (list): List of PDF file paths to merge
            output_filename (str): Output PDF filename
        """
        try:
            merger = PdfMerger()
            
            for pdf in pdf_files:
                if os.path.exists(pdf):
                    merger.append(pdf)
                else:
                    print(f"Warning: File not found - {pdf}")
            
            merger.write(output_filename)
            merger.close()
            print(f"PDFs merged successfully: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"Error merging PDFs: {e}")
            return None
    
    @staticmethod
    def split_pdf(filename, output_dir=None):
        """
        Split PDF into individual pages.
        
        Args:
            filename (str): Path to PDF file
            output_dir (str): Directory to save split pages
            
        Returns:
            list: List of created file paths
        """
        try:
            if output_dir is None:
                output_dir = "split_pages"
            
            os.makedirs(output_dir, exist_ok=True)
            
            reader = PdfReader(filename)
            base_name = os.path.splitext(os.path.basename(filename))[0]
            created_files = []
            
            for i, page in enumerate(reader.pages):
                writer = PdfWriter()
                writer.add_page(page)
                
                output_file = os.path.join(output_dir, f"{base_name}_page_{i+1}.pdf")
                with open(output_file, 'wb') as output:
                    writer.write(output)
                created_files.append(output_file)
            
            print(f"PDF split into {len(created_files)} pages in {output_dir}")
            return created_files
        except Exception as e:
            print(f"Error splitting PDF: {e}")
            return None
    
    @staticmethod
    def extract_pages(filename, page_numbers, output_filename):
        """
        Extract specific pages from PDF.
        
        Args:
            filename (str): Path to PDF file
            page_numbers (list): List of page numbers to extract (1-indexed)
            output_filename (str): Output PDF filename
        """
        try:
            reader = PdfReader(filename)
            writer = PdfWriter()
            
            for page_num in page_numbers:
                if 0 < page_num <= len(reader.pages):
                    writer.add_page(reader.pages[page_num - 1])
            
            with open(output_filename, 'wb') as output:
                writer.write(output)
            
            print(f"Extracted {len(page_numbers)} pages to {output_filename}")
            return output_filename
        except Exception as e:
            print(f"Error extracting pages: {e}")
            return None


def generate_sample_pdf():
    """Generate a sample PDF demonstrating various features."""
    pdf = PDFGenerator("sample_document.pdf")
    
    pdf.add_title("Sample PDF Document")
    pdf.add_paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    pdf.add_heading("Introduction", level=1)
    pdf.add_paragraph(
        "This is a sample PDF document demonstrating various features of the PDF generator. "
        "You can create professional documents with titles, headings, paragraphs, lists, and tables."
    )
    
    pdf.add_heading("Features", level=2)
    pdf.add_bullet_list([
        "Generate PDF documents programmatically",
        "Add formatted text with different styles",
        "Create tables with custom styling",
        "Read and extract text from existing PDFs",
        "Merge multiple PDF files",
        "Split PDFs into individual pages"
    ])
    
    pdf.add_heading("Sample Table", level=2)
    table_data = [
        ['Feature', 'Status', 'Priority'],
        ['PDF Generation', 'Complete', 'High'],
        ['Text Extraction', 'Complete', 'High'],
        ['PDF Merging', 'Complete', 'Medium'],
        ['PDF Splitting', 'Complete', 'Medium']
    ]
    pdf.add_table(table_data)
    
    pdf.add_page_break()
    
    pdf.add_heading("Conclusion", level=1)
    pdf.add_paragraph(
        "This PDF operations module provides a comprehensive set of tools for working with "
        "PDF documents in your Python applications."
    )
    
    return pdf.build()


if __name__ == "__main__":
    # Example usage
    print("PDF Operations Module")
    print("=" * 50)
    
    # Generate a sample PDF
    print("\n1. Generating sample PDF...")
    sample_file = generate_sample_pdf()
    
    # Read the generated PDF
    print("\n2. Reading PDF content...")
    content = PDFOperations.read_pdf(sample_file)
    if content:
        print(f"   - Pages: {content['num_pages']}")
        print(f"   - First page preview: {content['pages'][0]['text'][:100]}...")
    
    # Extract text
    print("\n3. Extracting text from page 1...")
    text = PDFOperations.extract_text(sample_file, [1])
    if text:
        print(f"   - Extracted {len(text)} characters")
    
    print("\n" + "=" * 50)
    print("All operations completed successfully!")
