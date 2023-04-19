import os
from pathlib import Path
from fpdf import FPDF
from tqdm import tqdm
import multiprocessing
from PyPDF2 import PdfFileMerger, PdfFileReader, PdfFileWriter

FILTERS = [
    "*.go",
    "*.ts",
    "*.tsx",
    "*.js",
    "*.jsx",
    "*.cpp",
    "*.java",
    "*.lua",
    "*.yaml",
    "*.yml",
    "*.json",
    "*.sh",
    "*.sql",
]

TARGET_DIR = Path(".")
RESULTS = []

def search_files(root_dir, filters):
    results = []
    for ftype in filters:
        searched_files = list(root_dir.rglob(ftype))
        results.extend(searched_files)
    return results

def pdf_worker(file):
    try:
        file_name = os.path.basename(file)
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font("Arial", "", "Arial Cyr.ttf", uni=True)
        pdf.set_font("Arial", "B", 12.5)
        pdf.multi_cell(
            0, 6, txt=str(file) + "\n---\n", align="L"
        )  # explicitly convert file to string with str()
        pdf.set_font("Arial", "", 12.5)
        text = (
            str(file.read_text(encoding="utf-8", errors="replace"))
            .replace("\n\n", "\n")
            .replace("\t", " "*4)
        )
        pdf.multi_cell(200, 6, txt=text, align="L")
        tmp_pdf_file = Path(f"./{os.getpid()}.pdf")
        pdf.output(tmp_pdf_file.as_posix(), 'F')
        pdf_reader = PdfFileReader(tmp_pdf_file)
        tmp_pdf_file.unlink()
        return pdf_reader
    except Exception as e:
        print(f"Could not process file: {file}, error: {e}")
        return None

RESULTS = search_files(TARGET_DIR, FILTERS)

with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
    pdf_files = list(
        tqdm(
            pool.imap(pdf_worker, RESULTS),
            total=len(RESULTS),
            unit=" files",
            bar_format="{l_bar}{bar:10}{r_bar}{bar:-10b}"
        )
    )

pdf_files = [pdf for pdf in pdf_files if pdf is not None]

if pdf_files:
    pdf_merger = PdfFileMerger()
    for pdf in pdf_files:
        pdf_merger.append(pdf)
    try:
        with open(Path("result.pdf"), "wb") as f:
            pdf_merger.write(f)
    except Exception as e:
        print(f"Could not write to PDF output file, error: {e}")
else:
    print("No PDF files were generated.")
