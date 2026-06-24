"""Conversor mínimo Markdown -> .docx para los documentos de justificación.
Soporta: # / ## / ### encabezados, **negrita**, listas '- ', citas '> ', y '---'.
Uso: python _md_to_docx.py entrada.md salida.docx
"""
import re
import sys
from docx import Document
from docx.shared import Pt, RGBColor


def add_runs(paragraph, text):
    """Divide el texto en fragmentos por **negrita** y los añade al párrafo."""
    for i, frag in enumerate(re.split(r"\*\*(.+?)\*\*", text)):
        run = paragraph.add_run(frag)
        if i % 2 == 1:
            run.bold = True


def convert(md_path, docx_path):
    doc = Document()
    estilo = doc.styles["Normal"]
    estilo.font.name = "Calibri"
    estilo.font.size = Pt(11)

    with open(md_path, encoding="utf-8") as f:
        lineas = f.read().splitlines()

    for linea in lineas:
        s = linea.rstrip()
        if not s.strip():
            continue
        if s.startswith("# "):
            doc.add_heading(s[2:], level=0)
        elif s.startswith("## "):
            doc.add_heading(s[3:], level=1)
        elif s.startswith("### "):
            doc.add_heading(s[4:], level=2)
        elif s.strip() == "---":
            doc.add_paragraph()
        elif s.startswith("> "):
            p = doc.add_paragraph(style="Intense Quote")
            add_runs(p, s[2:])
        elif re.match(r"^[-*] ", s):
            p = doc.add_paragraph(style="List Bullet")
            add_runs(p, s[2:])
        elif re.match(r"^\d+\. ", s):
            p = doc.add_paragraph(style="List Number")
            add_runs(p, re.sub(r"^\d+\. ", "", s))
        else:
            p = doc.add_paragraph()
            add_runs(p, s)

    doc.save(docx_path)
    print(f"Generado: {docx_path}")


if __name__ == "__main__":
    convert(sys.argv[1], sys.argv[2])
