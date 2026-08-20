from markdown_pdf import Section, MarkdownPdf
import sys

def main():
    md_file = "docs/Manual_RDL_Consolidado.md"
    pdf_file = "docs/Manual_RDL_Consolidado.pdf"
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    pdf = MarkdownPdf()
    pdf.add_section(Section(md_text))
    pdf.save(pdf_file)
    print("PDF generated successfully.")

if __name__ == "__main__":
    main()
