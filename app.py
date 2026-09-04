from __future__ import annotations

from datetime import date
from io import BytesIO
from pathlib import Path
from typing import Any
import re
import unicodedata

import streamlit as st
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    HRFlowable,
    Image as RLImage,
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(page_title="ᴍᴀɢɪsᴛʀᴀᴛᴜʀᴀ | SIA", page_icon="M", layout="wide")

st.markdown(
    """
    <style>
        .stApp { background: #090a0b; color: #eeeae1; }
        [data-testid="stHeader"] { background: #090a0b; }
        [data-testid="stSidebar"] { background: #0c0d0f; border-right: 1px solid #3c321e; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: #e7c16f !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { padding: 0.35rem 0; }
        .block-container { max-width: 1160px; padding-top: 2rem; padding-bottom: 3rem; }
        .mid-header { display: flex; align-items: center; justify-content: space-between; gap: 1rem; border-bottom: 1px solid #b48a3a; padding: 0 0 1.2rem; margin-bottom: 1.5rem; }
        .mid-brand { display: flex; align-items: center; gap: 0.8rem; }
        .mid-monogram { display: grid; place-items: center; width: 2.55rem; height: 2.55rem; border: 1px solid #c89d4a; color: #e7c16f; font-weight: 700; font-size: 0.85rem; }
        .mid-kicker { color: #e2bd72; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.12em; margin: 0; }
        .mid-title { color: #f4f0e7; font-size: 1.55rem; font-weight: 700; line-height: 1; margin: 0.2rem 0 0; }
        .mid-subtitle { color: #aca99f; margin: 0; font-size: 0.88rem; text-align: right; }
        .mid-status { display: none; }
        div[data-testid="stForm"] { background: #121416; border: 1px solid #292d30; border-radius: 6px; padding: 1.65rem; }
        h3 { color: #e7c16f; font-size: 0.98rem !important; font-weight: 700 !important; letter-spacing: 0.04em; text-transform: uppercase; padding-bottom: 0.65rem; border-bottom: 1px solid #303437; }
        p, label, [data-testid="stWidgetLabel"] p { color: #dedbd3 !important; }
        div[data-testid="stTextInput"] input, div[data-testid="stTextArea"] textarea, div[data-testid="stNumberInput"] input, div[data-baseweb="select"] > div { background: #0c0d0f !important; color: #f2eee6 !important; border-color: #35393d !important; border-radius: 4px !important; }
        div[data-testid="stTextInput"] input:focus, div[data-testid="stTextArea"] textarea:focus, div[data-testid="stNumberInput"] input:focus, div[data-baseweb="select"] > div:focus-within { border-color: #c89d4a !important; box-shadow: 0 0 0 1px #c89d4a !important; }
        div[data-baseweb="select"] span, div[data-baseweb="select"] input { color: #f2eee6 !important; }
        div[data-testid="stFormSubmitButton"] button, div[data-testid="stDownloadButton"] button { background: #c89d4a; border-color: #c89d4a; color: #111111; font-weight: 750; border-radius: 4px; }
        div[data-testid="stFormSubmitButton"] button:hover, div[data-testid="stDownloadButton"] button:hover { background: #e1bc70; border-color: #e1bc70; color: #111111; }
        div[data-testid="stFileUploader"] { border: 1px dashed #5d5139; background: #0c0d0f; padding: 0.45rem; border-radius: 4px; }
        div[data-testid="stFileUploader"] small, [data-testid="stCaptionContainer"] { color: #aaa69d !important; }
        div[data-testid="stAlert"] { border-radius: 4px; }
        div[data-testid="stAlert"][data-baseweb] { border-left-color: #bd3c35; }
        hr { border-color: #303437; }
        @media (max-width: 640px) { .mid-header { align-items: flex-start; } .mid-subtitle { text-align: left; } }
    </style>
    """,
    unsafe_allow_html=True,
)

LEVELS = {
    1: ("LEVE", 1_000_000),
    2: ("LEVE-MODERADO", 2_000_000),
    3: ("MODERADO", 3_000_000),
    4: ("MODERADO-GRAVE", 4_000_000),
    5: ("GRAVE", 5_000_000),
    6: ("MUITO GRAVE", 6_000_000),
    7: ("GRAVIDADE MÁXIMA", 7_000_000),
}

RAW_CRIMES = {
    1: [(21,"Adultério"),(22,"Bigamia"),(55,"Desobediência"),(61,"Perturbação da Ordem"),(65,"Alta Velocidade"),(67,"Corridas Ilegais"),(69,"Poluição Sonora"),(70,"Veículo Muito Danificado"),(71,"Veículo Ilegalmente Estacionado"),(72,"Uso Excessivo de Insulfilm"),(75,"Uso de Colete (Roupa)")],
    2: [(3,"Desacato"),(4,"Impedir Exercício Profissional"),(14,"Assédio Moral"),(15,"Calúnia"),(16,"Difamação"),(17,"Injúria"),(37,"Posse de Peças de Armas"),(38,"Posse de Cápsula"),(43,"Porte de Arma Branca"),(62,"QRR Ilegal"),(63,"Tentativa de Fuga"),(66,"Condução Imprudente"),(68,"Dirigir na Contramão"),(74,"Uso de Coldre")],
    3: [(1,"Abuso de Autoridade"),(5,"Prevaricação"),(6,"Prisão Disciplinar"),(18,"Importunação Sexual"),(30,"Dano à Propriedade do Governo"),(35,"Posse de Produtos Ilegais"),(46,"Posse de Componentes Narcóticos"),(52,"Apologia ao Crime"),(53,"Falsidade Ideológica"),(60,"Omissão de Socorro"),(73,"Ocultação Facial")],
    4: [(2,"Corrupção Passiva/Ativa"),(7,"Tráfico de Influência"),(8,"Uso Irregular de Função Pública"),(19,"Perjúrio"),(31,"Estelionato"),(36,"Tráfico de Produtos Ilegais"),(39,"Porte de Arma Leve"),(44,"Posse de Munição (1–100)"),(47,"Posse de Drogas (6–100)"),(49,"Dinheiro Sujo Leve"),(56,"Exercício Ilegal de Profissão"),(57,"Falsa Comunicação de Crime"),(59,"Ocultação de Provas"),(76,"Porte de Colete Balístico")],
    5: [(24,"Ameaça"),(25,"Extorsão"),(26,"Lesão Corporal"),(29,"Vandalismo"),(32,"Invasão de Propriedade"),(41,"Porte de Arma Pesada"),(45,"Tráfico de Munição (+100)"),(48,"Tráfico de Drogas (+100)"),(50,"Dinheiro Sujo Médio"),(64,"Tentativa de Suborno"),(77,"Tráfico de Colete Balístico")],
    6: [(10,"Homicídio Culposo"),(20,"Abandono de Incapaz"),(27,"Sequestro"),(33,"Furto"),(40,"Tráfico de Armas Leve"),(51,"Dinheiro Sujo Grave"),(54,"Formação de Quadrilha"),(58,"Obstrução de Justiça")],
    7: [(9,"Tentativa de Homicídio"),(11,"Homicídio Doloso"),(12,"Homicídio Qualificado"),(13,"Latrocínio"),(23,"Crime Sexual Intrafamiliar"),(28,"Tortura"),(34,"Roubo"),(42,"Tráfico de Armas Pesada")],
}
CRIMES = {f"Art. {article} — {name}": {"article": article, "name": name, "level": level, "label": LEVELS[level][0], "value": LEVELS[level][1]} for level, items in RAW_CRIMES.items() for article, name in items}

def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def escape(text: Any) -> str:
    return str(text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def calculate(crimes: list[dict], defendants: list[dict]) -> tuple[list[dict], float, float, list[float], str]:
    occurrences: dict[int, int] = {}
    lines = []
    gross = 0.0
    for crime in crimes:
        level = crime["level"]
        occurrences[level] = occurrences.get(level, 0) + 1
        factor = 1.0 if occurrences[level] == 1 else 0.2
        applied = crime["value"] * factor
        gross += applied
        lines.append({**crime, "factor": factor, "applied": applied})
    capped = min(gross, 20_000_000)
    if not defendants:
        return lines, gross, capped, [], "Teto geral de R$ 20.000.000 aplicado quando necessário."
    share = capped / len(defendants)
    shares = []
    asset_limits_used = False
    for defendant in defendants:
        assets = defendant.get("assets")
        limit = assets * 0.25 if assets is not None and assets > 0 else None
        if limit is not None and share > limit:
            asset_limits_used = True
            shares.append(limit)
        else:
            shares.append(share)
    final = sum(shares)
    note = "Teto geral de R$ 20.000.000 aplicado quando necessário."
    if asset_limits_used:
        note += " A quota individual foi reduzida para respeitar 25% do patrimônio informado de cada réu."
    elif any(d.get("assets") is None for d in defendants):
        note += " Patrimônio não informado: não foi presumido valor patrimonial."
    return lines, gross, final, shares, note

def build_legacy_pdf(data: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=1.7*cm, bottomMargin=1.7*cm, title="Denúncia — SIA")
    base = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, alignment=TA_CENTER, spaceAfter=5)
    heading = ParagraphStyle("Heading", parent=base["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("Body", parent=base["Normal"], fontName="Helvetica", fontSize=10, leading=14, alignment=TA_JUSTIFY, spaceAfter=7)
    small = ParagraphStyle("Small", parent=body, fontSize=9.5, leading=13)
    story = [Paragraph("MINISTÉRIO PÚBLICO - CIDADE ALTA RIO DE JANEIRO", title), HRFlowable(width="100%", thickness=.7, color=colors.black), Spacer(1, 10)]
    story += [Paragraph(f"<b>Processo n°:</b> {escape(data['process'])}", body), Paragraph("<b>RÉUS:</b>", body)]
    story += [Paragraph(f"• {escape(d['name'])} - ID: {escape(d['id'])}", body) for d in data["defendants"]]
    story.append(Paragraph("<b>VÍTIMA:</b>", body))
    story += [Paragraph(f"• {escape(v['name'])} - ID: {escape(v['id'])}", body) for v in data["victims"]]
    intro = (f"O Ministério Público, por meio de seu Promotor de Justiça {escape(data['prosecutor'])} | {escape(data['prosecutor_id'])}, "
             "no exercício de suas atribuições constitucionais, com base nas provas carreadas e na narrativa fática a seguir exposta, "
             "vem perante o Juízo competente oferecer a presente denúncia em face dos réus acima qualificados, pelas condutas tipificadas "
             "no Código Penal, conforme se demonstra.")
    story += [Paragraph("Introdução do Ministério Público", heading), Paragraph(intro, body), Paragraph("I – DOS FATOS", heading), Paragraph(escape(data["facts"]).replace("\n", "<br/>"), body), Paragraph("II – DOS CRIMES", heading)]
    for line in data["lines"]:
        detail = escape(line.get("description") or "")
        factor = "100%" if line["factor"] == 1 else "20%"
        block = [Paragraph(f"<b>NÍVEL {line['level']} – {line['label']} | {brl(line['applied'])}</b>", body), Paragraph(f"<b>Art. {line['article']} – {escape(line['name'])}</b>", body), Paragraph(f"Valor considerado nesta incidência: {factor}. {detail}", body)]
        story.append(KeepTogether(block))
    story.append(Paragraph("Totalização dos artigos e cálculo da indenização", heading))
    for idx, line in enumerate(data["lines"], 1):
        factor = "100%" if line["factor"] == 1 else "20%"
        story.append(Paragraph(f"{idx}. Art. {line['article']} (Nível {line['level']}; {factor}): {brl(line['applied'])}", small))
    story += [Paragraph(f"Soma calculada: {brl(data['gross'])}.", body), Paragraph(f"<b>Indenização total devida: {brl(data['total'])}.</b> {escape(data['note'])}", body), Paragraph("Regra aplicada: artigos de níveis diferentes são integralmente acumuláveis; no mesmo nível, o primeiro artigo corresponde a 100% e os demais a 20%.", body)]
    story += [Paragraph("III – DO DIREITO E DO DANO MORAL", heading), Paragraph("As condutas descritas, se comprovadas, ensejam a responsabilização pelos artigos indicados e a reparação do dano moral decorrente dos fatos narrados.", body), ListFlowable([ListItem(Paragraph("Dano moral à vítima, conforme os fatos narrados.", body)), ListItem(Paragraph("Reparação civil proporcional, observados os limites de cálculo aplicáveis.", body))], bulletType="bullet", leftIndent=18), Paragraph("IV – DOS PEDIDOS E REQUERIMENTOS", heading)]
    requests = ["O recebimento da presente denúncia e o regular prosseguimento do feito.", "A citação dos réus para responderem aos termos da denúncia.", "A produção das provas admitidas em direito, incluindo as relacionadas no Anexo I.", f"A fixação da indenização no valor total de {brl(data['total'])}, assim distribuída: 75% à vítima ({brl(data['total']*.75)}), 15% ao Promotor ({brl(data['total']*.15)}) e 10% ao Magistrado ({brl(data['total']*.10)})."]
    story.append(ListFlowable([ListItem(Paragraph(escape(item), body)) for item in requests], bulletType="1", leftIndent=18))
    story += [Spacer(1, 12), Paragraph("Nestes termos, pede deferimento.", body), Spacer(1, 14), Paragraph(f"Cidade Alta, {escape(data['date'])}.", body), Spacer(1, 20), Paragraph(escape(data['prosecutor']), body), Paragraph(escape(data['prosecutor_id']), body), Paragraph("Promotor de Justiça", body), PageBreak(), Paragraph("Anexo I", heading), Paragraph("<b>Provas Audiovisuais:</b>", body)]
    if data["proofs"]:
        story += [Paragraph(f"• Prova {i}: {escape(proof)}", body) for i, proof in enumerate(data["proofs"], 1)]
    else:
        story.append(Paragraph("Nenhuma prova audiovisual informada.", body))
    doc.build(story)
    return buffer.getvalue()

MODEL_REFERENCE = Path(__file__).parent / "work" / "magistratura_crest_reference.png"
JUDICIARY_CREST = Path(__file__).parent / "assets" / "poder_judiciario_brasao.png"


def draw_document_page(canvas, doc):
    """Draw the fixed judicial-paper frame used on every PDF page."""
    page_width, page_height = A4
    canvas.saveState()
    wine = colors.HexColor("#762824")
    gold = colors.HexColor("#bd9448")

    canvas.setFillColor(wine)
    canvas.rect(1.35 * cm, 0.5 * cm, 0.85 * cm, page_height - 1.0 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(1.775 * cm, 0.72 * cm, f"P.G. {doc.page}")

    if MODEL_REFERENCE.exists():
        image = ImageReader(str(MODEL_REFERENCE))
        image_width, image_height = image.getSize()
        crop_left, crop_top, crop_width, crop_height = 278, 26, 92, 96
        crest_width, crest_height = 1.65 * cm, 1.70 * cm
        scale = min(crest_width / crop_width, crest_height / crop_height)
        left = (page_width - crest_width) / 2
        bottom = page_height - 2.95 * cm
        crop_bottom = image_height - crop_top - crop_height
        canvas.saveState()
        path = canvas.beginPath()
        path.rect(left, bottom, crest_width, crest_height)
        canvas.clipPath(path, stroke=0, fill=0)
        canvas.drawImage(
            image,
            left - crop_left * scale,
            bottom - crop_bottom * scale,
            width=image_width * scale,
            height=image_height * scale,
            mask="auto",
        )
        canvas.restoreState()
    else:
        canvas.setStrokeColor(gold)
        canvas.setLineWidth(1)
        canvas.circle(page_width / 2, page_height - 2.10 * cm, 0.61 * cm, stroke=1, fill=0)

    canvas.setFillColor(colors.HexColor("#1b1b1b"))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(page_width / 2, page_height - 4.18 * cm, "MINISTÉRIO PÚBLICO - CIDADE ALTA RIO DE JANEIRO")
    line_y = page_height - 4.53 * cm
    canvas.setStrokeColor(colors.HexColor("#8b8b8b"))
    canvas.setLineWidth(3.5)
    canvas.line(2.95 * cm, line_y + 2.1, page_width - 2.0 * cm, line_y + 2.1)
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(2.2)
    canvas.line(2.95 * cm, line_y - 1.4, page_width - 2.0 * cm, line_y - 1.4)
    canvas.restoreState()


def signature_flowable(signature: bytes | None):
    if not signature:
        return None
    image_data = BytesIO(signature)
    image_width, image_height = ImageReader(image_data).getSize()
    max_width, max_height = 4.0 * cm, 1.7 * cm
    scale = min(max_width / image_width, max_height / image_height, 1)
    flowable = RLImage(BytesIO(signature), width=image_width * scale, height=image_height * scale)
    flowable.hAlign = "CENTER"
    return flowable


def build_pdf(data: dict) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=3.18 * cm,
        rightMargin=2.0 * cm,
        topMargin=6.0 * cm,
        bottomMargin=1.65 * cm,
        title="Denúncia - Magistratura",
    )
    base = getSampleStyleSheet()
    body = ParagraphStyle(
        "JudicialBody", parent=base["Normal"], fontName="Helvetica", fontSize=9.2,
        leading=13.2, alignment=TA_JUSTIFY, spaceAfter=9,
    )
    body_bold = ParagraphStyle("JudicialBold", parent=body, fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=5)
    section = ParagraphStyle(
        "JudicialSection", parent=body, fontName="Helvetica-Bold", fontSize=11,
        leading=14, alignment=TA_LEFT, spaceBefore=13, spaceAfter=13,
    )
    title = ParagraphStyle(
        "JudicialTitle", parent=body, fontName="Helvetica-Bold", fontSize=12,
        leading=15, alignment=TA_CENTER, spaceBefore=14, spaceAfter=18,
    )
    centered = ParagraphStyle("JudicialCenter", parent=body, alignment=TA_CENTER, spaceAfter=4)
    small = ParagraphStyle("JudicialSmall", parent=body, fontSize=8.8, leading=12, spaceAfter=5)

    story = [Paragraph(f"<b>Processo n°: {escape(data['process'])}</b>", body_bold), Paragraph("<b>RÉUS:</b>", body_bold)]
    story += [Paragraph(f"• &nbsp; <b>{escape(d['name'])}</b> - ID: {escape(d['id'])}", body, bulletText="") for d in data["defendants"]]
    story.append(Paragraph("<b>VÍTIMA:</b>", body_bold))
    story += [Paragraph(f"• &nbsp; <b>{escape(v['name'])}</b> - ID: {escape(v['id'])}", body, bulletText="") for v in data["victims"]]

    intro = (
        f"O Ministério Público, por meio de seu Promotor de Justiça {escape(data['prosecutor'])} | "
        f"{escape(data['prosecutor_id'])}, no exercício de suas atribuições constitucionais, "
        "com base nas provas carreadas e na narrativa fática a seguir exposta, vem perante o Juízo competente "
        "oferecer a presente denúncia em face dos réus acima qualificados, pelas condutas tipificadas no Código Penal, conforme se demonstra."
    )
    story += [Paragraph("Introdução do Ministério Público", title), Paragraph(intro, body), Paragraph("I - DOS FATOS", section)]
    for fact in (part.strip() for part in data["facts"].split("\n\n")):
        if fact:
            story.append(Paragraph(escape(fact).replace("\n", "<br/>"), body))

    story.append(Paragraph("II - DOS CRIMES", section))
    for line in data["lines"]:
        factor = "100%" if line["factor"] == 1 else "20%"
        description = escape(line.get("description") or "")
        story.append(KeepTogether([
            Paragraph(f"<b>Art. {line['article']} - {escape(line['name'])}</b>", body_bold),
            Paragraph(f"Nível {line['level']} - {line['label']} | {brl(line['applied'])} ({factor}). {description}", body),
        ]))

    story += [
        Paragraph("III - DA INDENIZAÇÃO", section),
        Paragraph(f"Soma calculada: {brl(data['gross'])}.", body),
        Paragraph(f"<b>Indenização total devida: {brl(data['total'])}.</b> {escape(data['note'])}", body),
        Paragraph("IV - DOS PEDIDOS E REQUERIMENTOS", section),
    ]
    requests = [
        "O recebimento da presente denúncia e o regular prosseguimento do feito.",
        "A citação dos réus para responderem aos termos da denúncia.",
        "A produção das provas admitidas em direito, incluindo as relacionadas no Anexo I.",
        f"A fixação da indenização no valor total de {brl(data['total'])}.",
    ]
    requests.extend(request for request in data.get("prosecutor_requests", []) if request.strip())
    story.append(ListFlowable([ListItem(Paragraph(escape(item), body)) for item in requests], bulletType="bullet", leftIndent=16))
    story += [Spacer(1, 13), Paragraph("Nestes termos, pede deferimento.", body_bold), Spacer(1, 12), Paragraph(f"Cidade Alta, {escape(data['date'])}.", body_bold), Spacer(1, 28)]
    signature = signature_flowable(data.get("signature"))
    if signature:
        story += [signature, Spacer(1, 4)]
    story += [
        Paragraph(f"<i>{escape(data['prosecutor'])}</i>", centered),
        Paragraph(escape(data['prosecutor_id']), centered),
        Paragraph("Promotor de Justiça", centered),
        Spacer(1, 15),
        Paragraph("Anexo I", centered),
        Paragraph("Provas Audiovisuais:", centered),
        Spacer(1, 9),
    ]
    if data["proofs"]:
        for index, proof in enumerate(data["proofs"], 1):
            story.append(Paragraph(f"• &nbsp; Prova {index}:<br/>&nbsp;&nbsp;&nbsp;{escape(proof)}", small))
    else:
        story.append(Paragraph("Nenhuma prova audiovisual informada.", small))

    doc.build(story, onFirstPage=draw_document_page, onLaterPages=draw_document_page)
    return buffer.getvalue()


def init_state():
    for key, default in {"defendant_count": 1, "victim_count": 1}.items():
        if key not in st.session_state:
            st.session_state[key] = default


PACIFICATION_REQUIREMENTS = [
    ("Baú da FAC/ORG", ("bau", "faccao organizacao"), "Clip da localização do baú da FAC/ORG com apresentação."),
    ("Bancada da FAC/ORG", ("bancada", "faccao organizacao"), "Clip da bancada da FAC/ORG com apresentação."),
    ("Confissão de ações", ("assaltos sequestros acoes", "afirmando confessando"), "Clip dos investigados afirmando assaltos, sequestros ou ações."),
    ("Atividade comercial", ("comercializam comercializacao",), "Clip informando o que os investigados comercializam."),
    ("Características visuais", ("mochila", "cor roupa", "foto", "numeracao numero"), "Mochila, cor da roupa, numeração e foto dos investigados."),
    ("Lideranças identificadas", ("lider sub lider gerente", "id"), "Nome e ID de todas as lideranças indicadas."),
    ("Confissão individual de função", ("lider sub lider gerente", "confessando afirmando ser"), "Clip individual de cada liderança declarando sua própria função."),
    ("Compra de produto da FAC/ORG", ("comprando compra", "fabricado membro"), "Clip de compra de item fabricado por membro da FAC/ORG."),
    ("Mapeamento 360°", ("mapeamento", "360 helicoptero aereo panoramico"), "Mapeamento 360° da área comum por helicóptero."),
    ("Relatório investigativo", ("relatorio",), "Relatório obrigatório anexado ou referenciado."),
    ("Investigadores identificados", ("investigador investigadores", "id registro funcional"), "Nome e identificação dos investigadores."),
    ("Departamento policial", ("departamento policia civil prf deic",), "Identificação formal do departamento policial responsável."),
]


def normalized(value: str) -> str:
    decomposed = unicodedata.normalize("NFD", value.lower())
    return "".join(character for character in decomposed if unicodedata.category(character) != "Mn")


def any_words_match(text: str, choices: str) -> bool:
    return any(word in text for word in choices.split())


def evidence_snippet(text: str, terms: tuple[str, ...]) -> str:
    for group in terms:
        for word in group.split():
            position = text.find(word)
            if position >= 0:
                return " ".join(text[max(0, position - 72):position + 180].split())
    return "Não localizado no texto extraível do documento."


URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", flags=re.IGNORECASE)


def repair_wrapped_urls(text: str) -> str:
    """Recompose URL tokens split by a PDF line wrap without joining normal prose."""
    repaired_lines: list[str] = []
    for line in text.splitlines():
        candidate = line.strip()
        previous = repaired_lines[-1] if repaired_lines else ""
        url_match = URL_PATTERN.search(previous)
        continuation = re.fullmatch(r"[A-Za-z0-9_~%=&?/#.+-]{8,}", candidate or "")
        if url_match and continuation and not re.search(r"[.);,:]$", previous):
            repaired_lines[-1] = previous.rstrip() + candidate
        else:
            repaired_lines.append(line)
    return "\n".join(repaired_lines)


def extract_document_urls(text: str) -> list[str]:
    urls = []
    for match in URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(".,;:)]}")
        if url not in urls:
            urls.append(url)
    return urls


def extract_pdf_text(pdf_bytes: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError as error:
        raise RuntimeError("A biblioteca pypdf não está instalada. Execute a instalação das dependências do projeto.") from error
    reader = PdfReader(BytesIO(pdf_bytes))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def review_pacification_pdf(pdf_bytes: bytes) -> tuple[list[dict], str]:
    original_source = repair_wrapped_urls(extract_pdf_text(pdf_bytes))
    source = normalized(original_source)
    urls = extract_document_urls(original_source)
    has_link_reference = any(marker in source for marker in ("http", "www", "medal", "youtube", "clip"))
    findings = []
    for title, groups, guidance in PACIFICATION_REQUIREMENTS:
        matched = all(any_words_match(source, group) for group in groups)
        requires_link = title not in {"Investigadores identificados", "Departamento policial"}
        if requires_link and not urls:
            suggested_status = "Não verificado" if has_link_reference else "Não comprovado"
        elif matched:
            suggested_status = "Comprovado"
        else:
            suggested_status = "Não comprovado"
        if title == "Lideranças identificadas":
            role_references = len(re.findall(r"\b(?:01|02|gerente|sub lider)\b", source))
            if suggested_status == "Comprovado" and role_references < 3:
                suggested_status = "Não comprovado"
        if title == "Confissão individual de função":
            role_pattern = r"(lider|sub lider|gerente).*?(confess|afirm)"
            reverse_pattern = r"(confess|afirm).*?(lider|sub lider|gerente)"
            role_count = len(re.findall(r"\b(?:01|02|gerente|sub lider)\b", source))
            if suggested_status == "Comprovado" and (role_count < 3 or not (re.search(role_pattern, source) or re.search(reverse_pattern, source))):
                suggested_status = "Não comprovado"
        findings.append({"title": title, "passed": suggested_status == "Comprovado", "status": suggested_status, "guidance": guidance, "evidence": evidence_snippet(source, groups), "urls": urls})
    return findings, source


def extract_pacification_details(source: str) -> dict[str, str]:
    original = source.replace("\n", " ")
    def find(pattern: str) -> str:
        match = re.search(pattern, original, flags=re.IGNORECASE)
        return " ".join(match.group(1).split()) if match else ""
    applicant = find(r"(?:requerente|departamento respons[aá]vel)\s*[:\-]?\s*([^\n]{3,80})")
    applicant = re.split(r"\brespons[aá]vel\b|\bdeclara", applicant, maxsplit=1, flags=re.IGNORECASE)[0].strip(" |:-")
    return {
        "process": find(r"processo.{0,10}?[:\-]\s*([\w./-]+)"),
        "applicant": applicant,
        "area": find(r"(?:[aá]rea a ser pacificada|localidade denominada)\s*[:\-]?\s*([^\n,.]{3,80})"),
    }


def draw_pacification_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#762824"))
    canvas.rect(1.35 * cm, 0.5 * cm, 0.85 * cm, height - 1.0 * cm, stroke=0, fill=1)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7)
    canvas.drawCentredString(1.775 * cm, 0.72 * cm, f"P.G. {doc.page}")
    canvas.setFillColor(colors.HexColor("#1b1b1b"))
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(width / 2, height - 2.2 * cm, "PODER JUDICIÁRIO - CIDADE ALTA RIO DE JANEIRO")
    canvas.setStrokeColor(colors.HexColor("#8b8b8b"))
    canvas.setLineWidth(3.2)
    canvas.line(2.95 * cm, height - 2.62 * cm, width - 2.0 * cm, height - 2.62 * cm)
    canvas.setStrokeColor(colors.black)
    canvas.setLineWidth(2)
    canvas.line(2.95 * cm, height - 2.72 * cm, width - 2.0 * cm, height - 2.72 * cm)
    canvas.restoreState()


def draw_approval_page(canvas, doc):
    """First-page heading matching the formal deferment model."""
    width, height = A4
    canvas.saveState()
    if doc.page == 1:
        if JUDICIARY_CREST.exists():
            canvas.drawImage(str(JUDICIARY_CREST), (width - 2.8 * cm) / 2, height - 4.4 * cm, width=2.8 * cm, height=2.55 * cm, mask="auto")
        canvas.setFillColor(colors.black)
        canvas.setFont("Helvetica-Bold", 10.5)
        canvas.drawCentredString(width / 2, height - 4.85 * cm, "Poder Judiciário da Cidade Alta - RJ")
        canvas.drawCentredString(width / 2, height - 5.7 * cm, "Comarca da Cidade Alta Vara")
        canvas.drawCentredString(width / 2, height - 6.55 * cm, "Criminal")
    else:
        canvas.setStrokeColor(colors.HexColor("#a27c1d"))
        canvas.setLineWidth(0.6)
        canvas.line(2.2 * cm, height - 1.7 * cm, width - 2.2 * cm, height - 1.7 * cm)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(width / 2, height - 1.4 * cm, "PODER JUDICIÁRIO CIDADE ALTA RJ")
    canvas.restoreState()


STANDARD_BLUE = colors.HexColor("#173d71")


class StandardDecisionCanvas(Canvas):
    """Adds the final page count after ReportLab has laid out the document."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.setFillColor(STANDARD_BLUE)
            self.setFont("Times-Roman", 8)
            self.drawRightString(A4[0] - 2.45 * cm, 1.25 * cm, f"Página {self._pageNumber} de {total_pages}")
            Canvas.showPage(self)
        Canvas.save(self)


def draw_standard_decision_page(canvas, doc):
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(STANDARD_BLUE)
    canvas.setFont("Times-Bold", 14)
    canvas.drawCentredString(width / 2, height - 2.45 * cm, "PODER JUDICIÁRIO DO ESTADO DO RIO DE JANEIRO")
    canvas.setFont("Times-Roman", 10)
    canvas.drawCentredString(width / 2, height - 3.22 * cm, "Comarca de Cidade Alta - RJ")
    canvas.setFont("Times-Italic", 10)
    canvas.drawCentredString(width / 2, height - 3.82 * cm, "Vara de Execuções Criminais e Medidas de Segurança")
    canvas.setStrokeColor(STANDARD_BLUE)
    canvas.setLineWidth(1.2)
    canvas.line(2.45 * cm, height - 4.38 * cm, width - 2.45 * cm, height - 4.38 * cm)
    canvas.restoreState()


def formal_date() -> str:
    months = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
    today = date.today()
    return f"Cidade Alta - RJ, {today.day} de {months[today.month - 1]} de {today.year}."


def build_standard_pacification_decision(
    case_number: str,
    applicant: str,
    area: str,
    findings: list[dict],
    decision: str,
    legal_name: str,
    legal_id: str,
    signature: bytes | None,
    manual_override: bool,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2.45 * cm, rightMargin=2.45 * cm, topMargin=5.05 * cm, bottomMargin=2.15 * cm, title=f"Decisão de Pacificação - {decision}")
    base = getSampleStyleSheet()
    body = ParagraphStyle("StandardDecisionBody", parent=base["Normal"], fontName="Times-Roman", fontSize=10.3, leading=15.2, alignment=TA_JUSTIFY, firstLineIndent=0.55 * cm, spaceAfter=10)
    heading = ParagraphStyle("StandardDecisionHeading", parent=body, fontName="Times-Bold", fontSize=10.8, leading=14, textColor=STANDARD_BLUE, firstLineIndent=0, spaceBefore=12, spaceAfter=7)
    table_label = ParagraphStyle("StandardTableLabel", parent=body, fontName="Times-Bold", fontSize=9.5, leading=12, textColor=STANDARD_BLUE, firstLineIndent=0)
    table_value = ParagraphStyle("StandardTableValue", parent=body, fontName="Times-Roman", fontSize=9.5, leading=12, firstLineIndent=0)
    check_text = ParagraphStyle("StandardCheck", parent=body, fontName="Times-Roman", fontSize=8.5, leading=10.5, firstLineIndent=0)
    signature_text = ParagraphStyle("StandardSignature", parent=body, fontName="Times-Bold", fontSize=10.2, leading=13, alignment=TA_CENTER, textColor=STANDARD_BLUE, firstLineIndent=0)
    approved = decision == "Deferir"
    subject = "Pedido de Autorização para Operação de Pacificação e Busca e Apreensão Operacional"
    metadata = [
        [Paragraph("PROCESSO Nº:", table_label), Paragraph(escape(case_number or "Não informado"), table_value)],
        [Paragraph("REQUERENTE:", table_label), Paragraph(escape(applicant or "Não informado"), table_value)],
        [Paragraph("INVESTIGADOS:", table_label), Paragraph(f"Organização criminosa vinculada à área \"{escape(area or 'Não informada')}\".", table_value)],
        [Paragraph("ASSUNTO:", table_label), Paragraph(subject, table_value)],
    ]
    metadata_table = Table(metadata, colWidths=[3.7 * cm, 11.65 * cm])
    metadata_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f5f8fc")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#b9c8da")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    requirements_heading = Paragraph("QUADRO DE CONFERÊNCIA", heading)
    story = [
        metadata_table,
        Paragraph("1. RELATÓRIO", heading),
        HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#d8e1ec"), spaceAfter=9),
        Paragraph("Vistos etc.", body),
        Paragraph(f"Trata-se de requerimento de autorização para operação de pacificação formulado por {escape(applicant or 'o órgão requerente')}, referente à área identificada como \"{escape(area or 'não informada')}\".", body),
        Paragraph("Consta dos autos conjunto documental e audiovisual destinado à demonstração das circunstâncias investigadas, das lideranças identificadas e da necessidade das providências requeridas.", body),
        Paragraph("2. FUNDAMENTAÇÃO", heading),
        HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#d8e1ec"), spaceAfter=9),
        Paragraph("Os elementos apresentados devem ser examinados em conjunto, observada a regularidade da representação, a coerência das evidências e a necessidade da medida diante da proteção da ordem pública e da segurança coletiva.", body),
        Paragraph("A conferência abaixo registra a análise documental realizada pelo responsável jurídico. A decisão final considera esse controle e as informações constantes dos autos.", body),
        requirements_heading,
        build_pacification_table(findings, check_text),
        Paragraph("3. DISPOSITIVO E DECISÃO", heading),
        HRFlowable(width="100%", thickness=0.45, color=colors.HexColor("#d8e1ec"), spaceAfter=9),
    ]
    if approved:
        basis = "acolho a conclusão da conferência jurídica" if not manual_override else "acolho a conclusão expressamente confirmada pelo responsável jurídico"
        story += [
            Paragraph(f"Ante o exposto, {basis} e <b>DEFIRO O PEDIDO DE PACIFICAÇÃO E INTERVENÇÃO OPERACIONAL</b> na área indicada, determinando:", body),
            Paragraph("1. <b>AUTORIZAÇÃO PARA INGRESSO E PACIFICAÇÃO</b> nos pontos mapeados pelas forças de segurança, incluída a apreensão dos elementos vinculados à investigação.", body),
            Paragraph("2. <b>EXPEDIÇÃO DAS MEDIDAS CABÍVEIS</b> em face dos investigados devidamente individualizados nos autos.", body),
            Paragraph("3. <b>PRESERVAÇÃO E ENCAMINHAMENTO DAS PROVAS</b> às autoridades responsáveis, na forma aplicável.", body),
            Table([[Paragraph("<b>Cumpra-se com urgência.</b> Expeçam-se as comunicações necessárias ao órgão requerente para execução das medidas e preservação da segurança coletiva.", body)]], colWidths=[15.35 * cm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef3f9")), ("LINEBEFORE", (0, 0), (0, -1), 3, STANDARD_BLUE), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])),
        ]
    else:
        missing = [item["title"] for item in findings if not item["passed"]]
        reason = "; ".join(missing) if missing else "insuficiência dos elementos analisados"
        story += [
            Paragraph(f"Ante o exposto, <b>INDEFIRO O PEDIDO DE PACIFICAÇÃO</b>, pois não houve comprovação suficiente dos requisitos obrigatórios, especialmente quanto a: {escape(reason)}.", body),
            Table([[Paragraph("A nova representação poderá ser apresentada quando instruída com os elementos pendentes e as referências audiovisuais legíveis.", body)]], colWidths=[15.35 * cm], style=TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fff4f2")), ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor("#8b3030")), ("LEFTPADDING", (0, 0), (-1, -1), 9), ("RIGHTPADDING", (0, 0), (-1, -1), 9), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)])),
        ]
    story += [
        Spacer(1, 22),
        Paragraph(formal_date(), ParagraphStyle("StandardDate", parent=body, alignment=TA_RIGHT, firstLineIndent=0, spaceAfter=8)),
    ]
    signature_image = signature_flowable(signature)
    if signature_image:
        story += [signature_image, Spacer(1, 3)]
    story += [
        HRFlowable(width=5.7 * cm, thickness=0.7, color=colors.HexColor("#222222"), hAlign="CENTER", spaceBefore=2, spaceAfter=8),
        Paragraph(escape(legal_name or "Jurídico responsável").upper(), signature_text),
        Paragraph(f"Jurídico responsável - ID: {escape(legal_id or 'Não informado')}", ParagraphStyle("StandardRole", parent=signature_text, fontName="Times-Roman", fontSize=9.5, textColor=STANDARD_BLUE)),
        Paragraph("Comarca de Cidade Alta - RJ", ParagraphStyle("StandardCourt", parent=signature_text, fontName="Times-Roman", fontSize=9.5, textColor=STANDARD_BLUE)),
    ]
    doc.build(story, onFirstPage=draw_standard_decision_page, onLaterPages=draw_standard_decision_page, canvasmaker=StandardDecisionCanvas)
    return buffer.getvalue()


def build_pacification_table(findings: list[dict], text_style: ParagraphStyle) -> Table:
    rows = [[Paragraph("Requisito", text_style), Paragraph("Resultado", text_style)]]
    for item in findings:
        status = {"Comprovado": "CONFERIDO", "Não verificado": "NÃO VERIFICADO"}.get(item.get("status"), "NÃO COMPROVADO")
        rows.append([Paragraph(escape(item["title"]), text_style), Paragraph(status, text_style)])
    table = Table(rows, colWidths=[10.2 * cm, 4.2 * cm], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e5df")),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#777777")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.HexColor("#7a1f1c")),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def build_approved_pacification_decision(
    case_number: str,
    applicant: str,
    area: str,
    findings: list[dict],
    legal_name: str,
    legal_id: str,
    signature: bytes | None,
    manual_override: bool,
) -> bytes:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=2.45 * cm, rightMargin=2.45 * cm, topMargin=8.7 * cm, bottomMargin=2.0 * cm, title="Decisão de Pacificação - Deferida")
    base = getSampleStyleSheet()
    body = ParagraphStyle("ApprovedBody", parent=base["Normal"], fontName="Helvetica", fontSize=10.4, leading=15.5, alignment=TA_JUSTIFY, spaceAfter=13)
    heading = ParagraphStyle("ApprovedHeading", parent=body, fontName="Helvetica-Bold", fontSize=12.5, leading=16, spaceBefore=17, spaceAfter=16)
    centered = ParagraphStyle("ApprovedCentered", parent=body, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=11)
    details = ParagraphStyle("ApprovedDetails", parent=body, fontName="Helvetica-Bold", alignment=TA_LEFT, spaceAfter=3)
    table_text = ParagraphStyle("ApprovedTable", parent=body, fontSize=8.6, leading=10.5, spaceAfter=0)
    decision_basis = "As provas coligidas aos autos revelam-se consistentes, idôneas e suficientes à formação do convencimento deste Juízo." if not manual_override else "Após conferência expressa do responsável jurídico, o conjunto documental foi considerado suficiente para a deliberação."
    story = [
        Paragraph("PODER JUDICIÁRIO CIDADE ALTA RJ", centered),
        Paragraph(f"<b>Processo n°:</b> {escape(case_number or 'Não informado')}", details),
        Paragraph(f"<b>Interessado:</b> {escape(applicant or 'Não informado')}", details),
        Paragraph(f"<b>Pedido de Pacificação de Área controlada por Organização Criminosa</b><br/>“{escape(area or 'Área não informada')}”", details),
        Paragraph(f"<b>Jurídico responsável:</b> {escape(legal_name)} {escape(legal_id)}", details),
        Paragraph("DECISÃO", heading),
        Paragraph(f"Trata-se de pedido formulado por {escape(applicant or 'órgão requerente não identificado')}, visando à autorização judicial para adoção de medidas destinadas à pacificação de área atualmente sob domínio de organização criminosa denominada “{escape(area or 'não informada')}”.", body),
        Paragraph(decision_basis, body),
        Paragraph("Verifica-se que o conjunto probatório evidencia, de forma clara e objetiva, a necessidade da medida, em atenção à ordem pública, à segurança coletiva e à efetividade da atuação institucional.", body),
        Paragraph("CONFERÊNCIA DOS REQUISITOS", heading),
        build_pacification_table(findings, table_text),
        Paragraph("Diante do exposto, <b>DEFIRO</b> o pedido de pacificação, autorizando a adoção das providências necessárias à sua implementação, nos termos das normas aplicáveis.", body),
        Paragraph("Publique-se. Registre-se. Cumpra-se.", body),
        Paragraph("Cidade Alta, " + date.today().strftime("%d/%m/%Y") + ".", body),
        Spacer(1, 13),
    ]
    signature_image = signature_flowable(signature)
    if signature_image:
        story += [signature_image, Spacer(1, 4)]
    story += [Paragraph(escape(legal_name or "Jurídico responsável"), centered), Paragraph(escape(legal_id), centered), Paragraph("Magistratura", centered)]
    doc.build(story, onFirstPage=draw_approval_page, onLaterPages=draw_approval_page)
    return buffer.getvalue()


def build_pacification_decision(
    case_number: str,
    applicant: str,
    area: str,
    findings: list[dict],
    decision: str,
    legal_name: str,
    legal_id: str,
    signature: bytes | None,
    manual_override: bool,
) -> bytes:
    return build_standard_pacification_decision(
        case_number, applicant, area, findings, decision, legal_name, legal_id, signature, manual_override
    )

    approved = decision == "Deferir"
    if approved:
        return build_approved_pacification_decision(
            case_number, applicant, area, findings, legal_name, legal_id, signature, manual_override
        )
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=3.18 * cm, rightMargin=2 * cm, topMargin=4.1 * cm, bottomMargin=1.05 * cm, title="Decisão de Pacificação")
    base = getSampleStyleSheet()
    body = ParagraphStyle("PacificationBody", parent=base["Normal"], fontName="Helvetica", fontSize=9.2, leading=13.1, alignment=TA_JUSTIFY, spaceAfter=9)
    heading = ParagraphStyle("PacificationHeading", parent=body, fontName="Helvetica-Bold", fontSize=11, leading=14, spaceBefore=12, spaceAfter=10)
    centered = ParagraphStyle("PacificationCentered", parent=body, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=14)
    table_text = ParagraphStyle("PacificationTable", parent=body, fontSize=8.4, leading=10.2, spaceAfter=0)
    story = [
        Paragraph("DECISÃO", centered),
        Paragraph(f"<b>Processo n°:</b> {escape(case_number or 'Não informado')} &nbsp;&nbsp;&nbsp; <b>Interessado:</b> {escape(applicant or 'Não informado')}<br/><b>Pedido:</b> Pacificação de área controlada por organização criminosa<br/><b>Área indicada:</b> {escape(area or 'Não informada')}", body),
        Paragraph("I - DO PEDIDO", heading),
        Paragraph(f"Trata-se de pedido formulado por {escape(applicant or 'órgão requerente não identificado')}, visando à autorização judicial para adoção de medidas destinadas à pacificação da área denominada {escape(area or 'não informada')}.", body),
        Paragraph("II - DA ANÁLISE DOCUMENTAL", heading),
        Paragraph("Foram conferidas as referências documentais apresentadas na representação. A leitura automática serve como apoio à análise e a conclusão final abaixo observa a conferência realizada pelo responsável jurídico.", body),
    ]
    story.append(build_pacification_table(findings, table_text))
    missing = [item for item in findings if not item["passed"]]
    story += [Spacer(1, 12), Paragraph("III - DECISÃO", heading)]
    if approved:
        basis = "Verificado o atendimento dos requisitos documentais obrigatórios" if not manual_override else "Por decisão expressa do responsável jurídico, após conferência manual do conjunto apresentado"
        story.append(Paragraph(f"{basis}, <b>DEFIRO</b> o pedido de pacificação, autorizando o encaminhamento às autoridades competentes para adoção das providências cabíveis, observadas as normas aplicáveis.", body))
    else:
        story.append(Paragraph("Diante das pendências apontadas na conferência documental, <b>INDEFIRO</b> o pedido, facultada nova apresentação após regularização dos itens necessários.", body))
        story.append(Paragraph("Pendências documentais", heading))
        story.append(ListFlowable([ListItem(Paragraph(f"<b>{escape(item['title'])}:</b> {escape(item['guidance'])}", body)) for item in missing], bulletType="bullet", leftIndent=16))
    signature_image = signature_flowable(signature)
    closing = [Spacer(1, 6), Paragraph("Publique-se. Registre-se. Cumpra-se.", body), Spacer(1, 7), Paragraph("Cidade Alta, " + date.today().strftime("%d/%m/%Y") + ".", body), Spacer(1, 10)]
    if signature_image:
        closing += [signature_image, Spacer(1, 4)]
    closing += [Paragraph(escape(legal_name or "Jurídico responsável"), centered), Paragraph(escape(legal_id), centered), Paragraph("Magistratura", centered)]
    story.append(KeepTogether(closing))
    doc.build(story, onFirstPage=draw_pacification_page, onLaterPages=draw_pacification_page)
    return buffer.getvalue()


def render_pacification_page():
    st.markdown("<div class='mid-header'><div class='mid-brand'><div class='mid-monogram'>MN</div><div><p class='mid-kicker'>ᴍᴀɢɪsᴛʀᴀᴛᴜʀᴀ</p><div class='mid-title'>Pacificação</div></div></div><p class='mid-subtitle'>Conferência documental de operações</p></div>", unsafe_allow_html=True)
    st.markdown("### Análise de representação")
    st.caption("A leitura do documento é uma conferência inicial. O responsável jurídico pode confirmar ou corrigir cada requisito antes de emitir a decisão.")
    uploaded_document = st.file_uploader("Representação policial em PDF", type=["pdf"], key="pacification_pdf")
    first, second, third = st.columns(3)
    case_number = first.text_input("Número do processo", key="pacification_case")
    applicant = second.text_input("Órgão requerente", key="pacification_applicant")
    area = third.text_input("Área a pacificar", key="pacification_area")
    legal_name, legal_id = st.columns(2)
    legal_name_value = legal_name.text_input("Nome do jurídico responsável *", key="pacification_legal_name")
    legal_id_value = legal_id.text_input("ID do jurídico responsável", key="pacification_legal_id")
    legal_signature = st.file_uploader("Assinatura do jurídico (opcional)", type=["png", "jpg", "jpeg"], key="pacification_signature", help="A assinatura será inserida acima do nome no fim da decisão.")
    if uploaded_document and st.button("Analisar representação", type="primary", use_container_width=True):
        try:
            findings, source = review_pacification_pdf(uploaded_document.getvalue())
            st.session_state["pacification_findings"] = findings
            st.session_state["pacification_filename"] = uploaded_document.name
            st.session_state["pacification_details"] = extract_pacification_details(source)
        except Exception as error:
            st.error(f"Não foi possível analisar o PDF: {error}")
    findings = st.session_state.get("pacification_findings")
    if findings:
        details = st.session_state.get("pacification_details", {})
        if any(details.values()):
            st.caption("Dados identificados no documento: " + " | ".join(f"{label}: {value}" for label, value in (("Processo", details.get("process")), ("Requerente", details.get("applicant")), ("Área", details.get("area"))) if value))
        document_urls = findings[0].get("urls", [])
        if document_urls:
            st.caption(f"{len(document_urls)} link(s) recomposto(s) e identificado(s) no PDF.")
            with st.expander("Links identificados no documento"):
                for url in document_urls:
                    st.link_button(url, url, use_container_width=True)
        else:
            st.info("Nenhum link legível foi identificado automaticamente. Itens dependentes de prova audiovisual ficam como não verificados até a conferência do jurídico.")
        st.subheader("Conferência do jurídico")
        reviewed_findings = []
        for index, item in enumerate(findings):
            left, right = st.columns([3, 1])
            left.markdown(f"**{item['title']}**")
            left.caption(item["guidance"])
            with left.expander("Evidência localizada no PDF"):
                st.write(item["evidence"])
            statuses = ["Comprovado", "Não comprovado", "Não verificado"]
            initial_index = statuses.index(item.get("status", "Comprovado" if item["passed"] else "Não comprovado"))
            status = right.selectbox("Status", statuses, index=initial_index, key=f"pacification_status_{index}", label_visibility="collapsed")
            reviewed_findings.append({**item, "passed": status == "Comprovado", "status": status})

        approved = all(item["passed"] for item in reviewed_findings)
        has_unproven = any(item["status"] == "Não comprovado" for item in reviewed_findings)
        if approved:
            st.success("Todos os requisitos foram confirmados pelo jurídico.")
        elif has_unproven:
            st.warning("Há requisitos não comprovados. A decisão automática é de indeferimento.")
        else:
            st.info("Há itens não verificados. Eles não causam indeferimento automático; confira os links e registre a decisão jurídica.")
        proceed = st.checkbox("Prosseguir mesmo havendo itens não comprovados", key="pacification_proceed")
        can_choose_decision = not has_unproven or proceed
        decision_options = ["Deferir", "Indeferir"] if can_choose_decision else ["Indeferir"]
        final_decision = st.selectbox("Decisão final", decision_options, key="pacification_final_decision")
        if not legal_name_value.strip():
            st.info("Informe o nome do jurídico responsável para liberar o PDF de decisão.")
        else:
            signature = legal_signature.getvalue() if legal_signature else None
            decision_pdf = build_pacification_decision(
                case_number or details.get("process", ""),
                applicant or details.get("applicant", ""),
                area or details.get("area", ""),
                reviewed_findings,
                final_decision,
                legal_name_value,
                legal_id_value,
                signature,
                proceed and not approved,
            )
            outcome = "deferida" if final_decision == "Deferir" else "indeferida"
            st.download_button(f"Baixar decisão {outcome}", decision_pdf, file_name=f"decisao_pacificacao_{outcome}.pdf", mime="application/pdf", type="primary", use_container_width=True)

init_state()
with st.sidebar:
    st.markdown("### ᴍᴀɢɪsᴛʀᴀᴛᴜʀᴀ")
    active_module = st.radio("Módulos", ["Processos", "Pacificação"], label_visibility="collapsed")
    st.divider()
    st.caption("Sistema judicial de Cidade Alta")

if active_module == "Pacificação":
    render_pacification_page()
    st.stop()

st.markdown(
    """
    <div class="mid-header">
        <div class="mid-brand">
            <div class="mid-monogram">MN</div>
            <div>
                <p class="mid-kicker">ᴍᴀɢɪsᴛʀᴀᴛᴜʀᴀ</p>
                <div class="mid-title">SIA</div>
            </div>
        </div>
        <p class="mid-subtitle">Sistema de Indenizações e Acusações</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.form("complaint_form"):
    st.subheader("Dados do processo")
    c1, c2 = st.columns(2)
    process = c1.text_input("Número do Processo *")
    complaint_date = c2.date_input("Data da denúncia *", value=date.today(), format="DD/MM/YYYY")
    prosecutor, prosecutor_id = st.columns(2)
    prosecutor_name = prosecutor.text_input("Nome do Promotor *")
    prosecutor_identification = prosecutor_id.text_input("ID do Promotor *")
    st.subheader("Partes envolvidas")
    st.markdown("**Réus**")
    defendants = []
    for i in range(st.session_state.defendant_count):
        cols = st.columns([3, 2, 2])
        defendants.append({"name": cols[0].text_input("Nome *", key=f"def_name_{i}"), "id": cols[1].text_input("ID *", key=f"def_id_{i}"), "assets": cols[2].number_input("Patrimônio (R$, opcional)", min_value=0.0, step=1000.0, key=f"def_assets_{i}")})
    st.markdown("**Vítimas**")
    victims = []
    for i in range(st.session_state.victim_count):
        cols = st.columns(2)
        victims.append({"name": cols[0].text_input("Nome *", key=f"victim_name_{i}"), "id": cols[1].text_input("ID *", key=f"victim_id_{i}")})
    facts = st.text_area("Fatos ou resumo da situação *", height=180, help="Registre a narrativa que deve constar na denúncia com base nas provas disponíveis.")
    st.subheader("Crimes")
    choices = list(CRIMES)
    chosen_crimes = st.multiselect(
        "Pesquisar e selecionar artigos aplicáveis *",
        choices,
        placeholder="Pesquise pelo artigo ou nome do crime",
        help="Digite para filtrar e selecione todos os crimes aplicáveis ao caso.",
    )
    selected_crimes = []
    for chosen in chosen_crimes:
        crime = CRIMES[chosen]
        st.caption(f"Nome: {crime['name']}  |  Nível {crime['level']} — {crime['label']}  |  Valor-base: {brl(crime['value'])}")
        description = st.text_area(
            f"Descrição da conduta imputada — Art. {crime['article']} *",
            key=f"crime_description_{crime['article']}",
            height=80,
        )
        selected_crimes.append({**crime, "description": description})

    st.subheader("Vídeo e resumo dos fatos")
    uploaded_video = st.file_uploader(
        "Carregar vídeo do computador (opcional)",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        help="O vídeo fica apenas nesta sessão para visualização e não é incorporado ao PDF.",
    )
    if uploaded_video:
        st.video(uploaded_video)
        st.caption(f"Vídeo selecionado: {uploaded_video.name}")
    proof_text = st.text_area("Links de outros vídeos/provas (um por linha)", height=100)
    uploaded_signature = st.file_uploader(
        "Assinatura do promotor (opcional)",
        type=["png", "jpg", "jpeg"],
        help="A imagem será inserida acima do nome no final do PDF.",
    )
    st.subheader("Pedidos do promotor")
    prosecutor_request_1 = st.text_area("Pedido adicional 1 (opcional)", height=80)
    prosecutor_request_2 = st.text_area("Pedido adicional 2 (opcional)", height=80)
    submitted = st.form_submit_button("Gerar Denúncia PDF", type="primary", use_container_width=True)

controls = st.columns(2)
if controls[0].button("+ Adicionar réu"):
    st.session_state.defendant_count += 1; st.rerun()
if controls[1].button("+ Adicionar vítima"):
    st.session_state.victim_count += 1; st.rerun()
if submitted:
    assets_normalized = [{**d, "assets": d["assets"] if d["assets"] > 0 else None} for d in defendants]
    required = [process, prosecutor_name, prosecutor_identification, facts]
    valid_people = all(d["name"] and d["id"] for d in assets_normalized + victims)
    valid_crimes = bool(selected_crimes) and all(c["description"].strip() for c in selected_crimes)
    if not all(required) or not valid_people or not valid_crimes:
        st.error("Preencha todos os campos obrigatórios, inclusive a descrição de cada crime.")
    else:
        lines, gross, total, shares, note = calculate(selected_crimes, assets_normalized)
        proofs = [p.strip() for p in proof_text.splitlines() if p.strip()]
        if uploaded_video:
            proofs.insert(0, f"Vídeo local selecionado: {uploaded_video.name}")
        signature = uploaded_signature.getvalue() if uploaded_signature else None
        pdf = build_pdf({"process": process, "prosecutor": prosecutor_name, "prosecutor_id": prosecutor_identification, "date": complaint_date.strftime("%d/%m/%Y"), "defendants": assets_normalized, "victims": victims, "facts": facts, "lines": lines, "gross": gross, "total": total, "note": note, "proofs": proofs, "signature": signature, "prosecutor_requests": [prosecutor_request_1, prosecutor_request_2]})
        st.success(f"PDF gerado. Indenização total: {brl(total)}")
        if shares:
            st.caption("Quota por réu: " + " | ".join(f"{d['name']}: {brl(s)}" for d, s in zip(assets_normalized, shares)))
        st.download_button("Baixar Denúncia PDF", data=pdf, file_name=f"denuncia_{process.replace('/', '-')}.pdf", mime="application/pdf", type="primary", use_container_width=True)
