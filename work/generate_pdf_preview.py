from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app

lines, gross, total, shares, note = app.calculate(
    [
        {"article": 1, "name": "Abuso de Autoridade", "level": 3, "label": "MODERADO", "value": 3_000_000, "description": "Conduta descrita para validação da diagramação."},
        {"article": 3, "name": "Desacato", "level": 2, "label": "LEVE-MODERADO", "value": 2_000_000, "description": "Segundo artigo selecionado para o exemplo."},
    ],
    [{"name": "Derrite", "id": "870", "assets": None}],
)
pdf = app.build_pdf(
    {
        "process": "014-2026",
        "prosecutor": "Dico Prior",
        "prosecutor_id": "49912",
        "date": "12 de Maio de 2026",
        "defendants": [{"name": "Derrite", "id": "870", "assets": None}],
        "victims": [{"name": "Jhonny Moretti", "id": "865"}],
        "facts": "Em 05 de maio de 2026, a vítima compareceu à delegacia para relatar os fatos narrados nesta denúncia.\n\nA conduta descrita apresenta elementos que justificam a apuração pelos órgãos competentes.",
        "lines": lines,
        "gross": gross,
        "total": total,
        "note": note,
        "proofs": ["Link: https://medal.tv/exemplo"],
        "signature": None,
    }
)
Path("work/pdf_preview.pdf").write_bytes(pdf)
