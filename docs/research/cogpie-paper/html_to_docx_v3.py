#!/usr/bin/env python3
"""CogPIE artigo PT-BR v3: DOCX com formatação visual premium.

Melhorias v3:
- Stats com fundo escuro e texto branco/accent
- Key findings com borda lateral grossa e fundo colorido
- Blocos de destaque para resumo/abstract
- Cabeçalhos com design mais impactante
- Fórmulas em caixas destacadas
- Figuras com moldura visual completa
- Listas com marcadores coloridos
- Rodapé com borda superior
- Uso estratégico de cores em todo o documento
"""
import re
import html as html_mod
from pathlib import Path

from lxml import etree
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml

DST = Path("/run/media/mrhenrike/Data/Projects/UniaoGeek/CogPIE/docs/research/cogpie-paper/CogPIE_Artigo_PT-BR.docx")
CHARTS = Path("/home/mrhenrike/.claude/jobs/50193fcb/tmp/charts")

# OMML namespaces
OMML_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"

FONT = "Arial"
FONT_SZ = Pt(10)
LINE_SP = 1.25
SP_AFTER = Pt(8)

# === PALETA DE CORES ===
ACCENT = RGBColor(0x8B, 0x5C, 0xF6)       # roxo principal
ACCENT_DARK = RGBColor(0x6D, 0x28, 0xD9)   # roxo escuro
ACCENT_DEEP = RGBColor(0x4C, 0x1D, 0x95)   # roxo profundo
DARK = RGBColor(0x1A, 0x1A, 0x2E)          # quase preto azulado
DARK_BG = "1E1B2E"                          # fundo escuro hex
DARK_BG2 = "2D2042"                         # fundo escuro roxo hex
BODY = RGBColor(0x2D, 0x2D, 0x3D)          # texto corpo
MUTED = RGBColor(0x6B, 0x6B, 0x7B)         # texto secundario
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
NEAR_WHITE = RGBColor(0xF0, 0xEE, 0xFF)    # branco com toque roxo
GOLD = RGBColor(0xF5, 0xA6, 0x23)          # dourado destaque
GREEN = RGBColor(0x10, 0xB9, 0x81)         # verde sucesso
RED_SOFT = RGBColor(0xEF, 0x44, 0x44)      # vermelho alerta

# Hex para shading
ACCENT_HEX = "8B5CF6"
ACCENT_DARK_HEX = "6D28D9"
ACCENT_DEEP_HEX = "4C1D95"
LIGHT_BG = "F5F3FF"          # roxo muito claro
LIGHT_BG2 = "EDE9FE"         # roxo claro
MED_BG = "DDD6FE"            # roxo médio
GOLD_BG = "FEF3C7"           # dourado claro
GREEN_BG = "D1FAE5"          # verde claro

# Tabelas
TH_BG = "1E1B2E"             # cabeçalho escuro profundo
TR_ALT = "F5F3FF"            # listras
TR_HL = "EDE9FE"             # highlight CogPIE
TR_TOTAL = "DDD6FE"          # total


# === FUNCOES AUXILIARES ===

def extract_inline(frag):
    parts = []
    bold = italic = code = False
    href = None
    buf = ""
    tag_re = re.compile(r"<(/?)(\w+)([^>]*)>")
    i = 0
    while i < len(frag):
        m = tag_re.search(frag, i)
        if not m:
            buf += frag[i:]
            break
        buf += frag[i:m.start()]
        close = m.group(1) == "/"
        tag = m.group(2).lower()
        attrs = m.group(3)
        i = m.end()
        if tag in ("strong", "b"):
            if buf:
                parts.append((html_mod.unescape(buf), bold, italic, code, href))
                buf = ""
            bold = not close
        elif tag in ("em", "i"):
            if buf:
                parts.append((html_mod.unescape(buf), bold, italic, code, href))
                buf = ""
            italic = not close
        elif tag == "code":
            if buf:
                parts.append((html_mod.unescape(buf), bold, italic, code, href))
                buf = ""
            code = not close
        elif tag == "a":
            if not close:
                if buf:
                    parts.append((html_mod.unescape(buf), bold, italic, code, href))
                    buf = ""
                hm = re.search(r'href="([^"]*)"', attrs)
                href = hm.group(1) if hm else None
            else:
                if buf:
                    parts.append((html_mod.unescape(buf), bold, italic, code, href))
                    buf = ""
                href = None
        elif tag == "br":
            buf += "\n"
    if buf:
        parts.append((html_mod.unescape(buf), bold, italic, code, href))
    return parts if parts else [("", False, False, False, None)]


def set_pf(p, spacing=LINE_SP, after=SP_AFTER, before=Pt(0), align=None):
    pf = p.paragraph_format
    pf.line_spacing = spacing
    pf.space_after = after
    pf.space_before = before
    if align:
        pf.alignment = align


def keep_with_next(p):
    ppr = p._element.get_or_add_pPr()
    ppr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))


def add_run(p, text, bold=False, italic=False, code=False,
            size=FONT_SZ, color=BODY, underline=False):
    run = p.add_run(text)
    run.font.name = "Consolas" if code else FONT
    run.font.size = Pt(9) if code else size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    if underline:
        run.font.underline = True
    rpr = run._element.get_or_add_rPr()
    rpr.append(parse_xml(f'<w:rFonts {nsdecls("w")} w:eastAsia="{FONT}"/>'))
    return run


def add_formatted(p, parts, size=FONT_SZ, default_color=BODY):
    for text, bold, italic, code, href in parts:
        if not text:
            continue
        add_run(p, text, bold=bold, italic=italic, code=code,
                size=size, color=default_color)


def add_para(doc, parts=None, text="", bold=False, size=FONT_SZ,
             color=BODY, align=None, after=SP_AFTER, before=Pt(0)):
    p = doc.add_paragraph()
    set_pf(p, after=after, before=before, align=align)
    if parts:
        add_formatted(p, parts, size=size, default_color=color)
    elif text:
        add_run(p, text, bold=bold, size=size, color=color)
    return p


def shading(element, color_hex):
    """Apply shading to a paragraph or cell element."""
    if hasattr(element, '_element'):
        el = element._element
    else:
        el = element
    if el.tag.endswith('}p') or el.tag.endswith('p'):
        ppr = el.get_or_add_pPr()
        ppr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))
    elif el.tag.endswith('}tc') or el.tag.endswith('tc'):
        tcpr = el.get_or_add_tcPr()
        tcpr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))


def para_shading(p, color_hex):
    ppr = p._element.get_or_add_pPr()
    ppr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))


def para_borders(p, left=None, right=None, top=None, bottom=None):
    """Add borders to paragraph. Each border: (val, sz, space, color)."""
    ppr = p._element.get_or_add_pPr()
    parts = []
    for side, cfg in [("left", left), ("right", right), ("top", top), ("bottom", bottom)]:
        if cfg:
            val, sz, space, col = cfg
            parts.append(f'<w:{side} w:val="{val}" w:sz="{sz}" w:space="{space}" w:color="{col}"/>')
    if parts:
        xml = f'<w:pBdr {nsdecls("w")}>{"".join(parts)}</w:pBdr>'
        ppr.append(parse_xml(xml))


def add_heading(doc, text, level=1):
    p = doc.add_paragraph()
    if level == 1:
        set_pf(p, after=Pt(6), before=Pt(6), align=WD_ALIGN_PARAGRAPH.CENTER)
        para_shading(p, DARK_BG)
        p.paragraph_format.left_indent = Cm(-0.3)
        p.paragraph_format.right_indent = Cm(-0.3)
        add_run(p, text, bold=True, size=Pt(18), color=WHITE)
    elif level == 2:
        set_pf(p, after=Pt(8), before=Pt(20))
        para_shading(p, ACCENT_DEEP_HEX)
        para_borders(p, bottom=("single", "12", "4", ACCENT_HEX))
        add_run(p, text.upper(), bold=True, size=Pt(12), color=WHITE)
    elif level == 3:
        set_pf(p, after=Pt(4), before=Pt(14))
        para_borders(p, left=("single", "24", "8", ACCENT_HEX))
        para_shading(p, LIGHT_BG)
        add_run(p, text, bold=True, size=Pt(11), color=ACCENT_DEEP)
    keep_with_next(p)
    return p


def cell_shading(cell, color_hex):
    tc = cell._element.get_or_add_tcPr()
    tc.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}" w:val="clear"/>'))


def cell_para(cell, text, bold=False, size=Pt(8), color=BODY, align=None):
    cell.text = ""
    p = cell.paragraphs[0]
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
    pf.space_after = Pt(1)
    pf.space_before = Pt(1)
    if align:
        pf.alignment = align
    add_run(p, text, bold=bold, size=size, color=color)


def keep_table_together(table):
    for row in table.rows:
        tr = row._tr
        trpr = tr.get_or_add_trPr()
        trpr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))


def add_table(doc, headers, rows, hl_first=False, has_total=False):
    n = len(headers)
    t = doc.add_table(rows=1 + len(rows), cols=n)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.style = "Table Grid"

    for i, h in enumerate(headers):
        c = t.rows[0].cells[i]
        cell_para(c, h, bold=True, size=Pt(8), color=NEAR_WHITE)
        cell_shading(c, TH_BG)
        c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER

    for ri, rd in enumerate(rows):
        is_hl = hl_first and ri == 0
        is_total = has_total and ri == len(rows) - 1
        is_alt = ri % 2 == 1

        for ci, val in enumerate(rd):
            c = t.rows[ri + 1].cells[ci]
            if is_hl:
                cell_para(c, val, bold=True, size=Pt(8), color=ACCENT_DEEP)
                cell_shading(c, TR_HL)
            elif is_total:
                cell_para(c, val, bold=True, size=Pt(8), color=DARK)
                cell_shading(c, MED_BG)
            elif is_alt:
                cell_para(c, val, size=Pt(8), color=BODY)
                cell_shading(c, TR_ALT)
            else:
                cell_para(c, val, size=Pt(8), color=BODY)

    keep_table_together(t)
    add_para(doc, text="", after=Pt(6))
    return t


def add_stat_block(doc, stats):
    """Bloco de métricas com fundo escuro. stats: lista de (valor, label)."""
    t = doc.add_table(rows=2, cols=len(stats))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for ci, (val, lbl) in enumerate(stats):
        # Valor grande
        c_val = t.rows[0].cells[ci]
        cell_para(c_val, val, bold=True, size=Pt(18), color=NEAR_WHITE,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        cell_shading(c_val, DARK_BG)
        c_val.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
        # Label
        c_lbl = t.rows[1].cells[ci]
        cell_para(c_lbl, lbl, bold=False, size=Pt(7), color=NEAR_WHITE,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
        cell_shading(c_lbl, DARK_BG2)
        c_lbl.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP

    # Remover bordas da tabela de stats
    tbl = t._tbl
    tblpr = tbl.tblPr if tbl.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
    borders_xml = (
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
        f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="{ACCENT_HEX}"/>'
        f'</w:tblBorders>'
    )
    tblpr.append(parse_xml(borders_xml))
    keep_table_together(t)
    add_para(doc, text="", after=Pt(8))


def add_key_finding(doc, label, body_parts, bg=LIGHT_BG, border_color=ACCENT_HEX):
    p = doc.add_paragraph()
    set_pf(p, after=Pt(8), before=Pt(4))
    para_shading(p, bg)
    para_borders(p,
        left=("single", "30", "10", border_color),
        top=("single", "2", "2", border_color),
        bottom=("single", "2", "2", border_color),
        right=("single", "2", "2", border_color))
    add_run(p, "■ " + label.upper() + "\n", bold=True, size=Pt(9), color=ACCENT_DARK)
    add_formatted(p, body_parts, default_color=BODY)
    return p


def add_critical_finding(doc, label, body_parts):
    """Variante mais intensa para descobertas críticas."""
    return add_key_finding(doc, label, body_parts, bg=LIGHT_BG2, border_color=ACCENT_DARK_HEX)


def add_figure(doc, fig_num, title, image_filename, width=Inches(5.5)):
    """Insere grafico PNG real como imagem no documento."""
    img_path = CHARTS / image_filename
    if img_path.exists():
        p_img = doc.add_paragraph()
        set_pf(p_img, after=Pt(2), before=Pt(8), align=WD_ALIGN_PARAGRAPH.CENTER)
        run = p_img.add_run()
        run.add_picture(str(img_path), width=width)
    # Caption
    p_cap = doc.add_paragraph()
    set_pf(p_cap, after=Pt(10), align=WD_ALIGN_PARAGRAPH.CENTER)
    add_run(p_cap, f"Figura {fig_num}. ", bold=True, size=Pt(9), color=ACCENT_DARK)
    add_run(p_cap, title, size=Pt(9), color=MUTED, italic=True)


# === OMML (Office Math) helpers ===

def mr(t, italic=True):
    """Math run. italic=True for variables, False for text/function names."""
    sty = '' if italic else '<m:rPr><m:sty m:val="p"/></m:rPr>'
    t_esc = t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return f'<m:r>{sty}<m:t xml:space="preserve">{t_esc}</m:t></m:r>'

def msub(base, sub):
    return f'<m:sSub><m:e>{base}</m:e><m:sub>{sub}</m:sub></m:sSub>'

def msup(base, sup):
    return f'<m:sSup><m:e>{base}</m:e><m:sup>{sup}</m:sup></m:sSup>'

def mdel(content, beg='(', end=')'):
    return (f'<m:d><m:dPr><m:begChr m:val="{beg}"/>'
            f'<m:endChr m:val="{end}"/></m:dPr>'
            f'<m:e>{content}</m:e></m:d>')

def mnary(char, sub_content, sup_content, body):
    return (f'<m:nary><m:naryPr><m:chr m:val="{char}"/>'
            f'<m:limLoc m:val="undOvr"/></m:naryPr>'
            f'<m:sub>{sub_content}</m:sub>'
            f'<m:sup>{sup_content}</m:sup>'
            f'<m:e>{body}</m:e></m:nary>')

def mfunc(name, arg):
    return (f'<m:func><m:funcPr><m:ctrlPr/></m:funcPr>'
            f'<m:fName><m:r><m:rPr><m:sty m:val="p"/></m:rPr>'
            f'<m:t>{name}</m:t></m:r></m:fName>'
            f'<m:e>{arg}</m:e></m:func>')

def make_omath(content):
    xml = (f'<m:oMath xmlns:m="{OMML_NS}" xmlns:w="{WML_NS}">'
           f'{content}</m:oMath>')
    return etree.fromstring(xml.encode('utf-8'))

def add_equation(doc, omath_content, note=None):
    """Insert OMML equation in a styled paragraph."""
    p = doc.add_paragraph()
    set_pf(p, after=Pt(6), before=Pt(6), align=WD_ALIGN_PARAGRAPH.CENTER)
    para_shading(p, LIGHT_BG2)
    para_borders(p,
        top=("single", "4", "4", ACCENT_HEX),
        bottom=("single", "4", "4", ACCENT_HEX))
    omath = make_omath(omath_content)
    p._element.append(omath)
    if note:
        add_para(doc, text=note, size=Pt(9), color=MUTED,
                 align=WD_ALIGN_PARAGRAPH.CENTER, after=Pt(8))


def add_abstract_block(doc, title, body, keywords, kw_label="Palavras-chave"):
    """Bloco de resumo/abstract com estilo visual."""
    p = doc.add_paragraph()
    set_pf(p, after=Pt(2), before=Pt(10))
    para_shading(p, DARK_BG2)
    para_borders(p, bottom=("single", "6", "0", ACCENT_HEX))
    add_run(p, f"  {title.upper()}", bold=True, size=Pt(11), color=NEAR_WHITE)

    p2 = doc.add_paragraph()
    set_pf(p2, after=Pt(4))
    para_shading(p2, LIGHT_BG)
    para_borders(p2,
        left=("single", "4", "6", ACCENT_HEX),
        right=("single", "4", "6", ACCENT_HEX),
        bottom=("single", "4", "2", ACCENT_HEX))
    add_run(p2, body, size=Pt(9), color=BODY)

    p3 = doc.add_paragraph()
    set_pf(p3, after=Pt(10))
    para_shading(p3, LIGHT_BG2)
    para_borders(p3,
        left=("single", "4", "6", ACCENT_HEX),
        right=("single", "4", "6", ACCENT_HEX),
        bottom=("single", "4", "2", ACCENT_HEX))
    add_run(p3, f"{kw_label}: ", bold=True, size=Pt(8), color=ACCENT_DARK)
    add_run(p3, keywords, size=Pt(8), color=MUTED, italic=True)


def add_bullet(doc, text, indent=1, color_marker=ACCENT):
    p = doc.add_paragraph()
    set_pf(p, after=Pt(3))
    p.paragraph_format.left_indent = Cm(indent)
    add_run(p, "▪ ", size=Pt(8), color=color_marker)
    add_run(p, text, size=FONT_SZ, color=BODY)
    return p


def add_numbered(doc, num, title, body, indent=0.5):
    p = doc.add_paragraph()
    set_pf(p, after=Pt(5))
    p.paragraph_format.left_indent = Cm(indent)
    add_run(p, f" {num} ", bold=True, size=Pt(9), color=WHITE)
    # Simular círculo com fundo via run shading
    run = p.runs[-1]
    rpr = run._element.get_or_add_rPr()
    rpr.append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="{ACCENT_HEX}" w:val="clear"/>'))
    add_run(p, f"  {title} ", bold=True, size=FONT_SZ, color=DARK)
    if body:
        add_run(p, body, size=FONT_SZ, color=BODY)
    return p


def add_separator(doc):
    p = doc.add_paragraph()
    set_pf(p, after=Pt(2), before=Pt(2), align=WD_ALIGN_PARAGRAPH.CENTER)
    add_run(p, "─" * 50, size=Pt(6), color=RGBColor(0xDD, 0xD6, 0xFE))


def add_repo_note(doc):
    p = add_para(doc, size=Pt(8), color=MUTED, after=Pt(4))
    para_shading(p, GOLD_BG)
    para_borders(p, left=("single", "12", "6", "F5A623"))
    add_run(p, "⚠ ", size=Pt(8), color=GOLD)
    add_run(p, "Na tabela a seguir, a coluna 'Repositório' apresenta o caminho user/projeto. "
               "Todas as URLs são precedidas por https://github.com/",
            size=Pt(8), color=BODY)


# ================ BUILD DOCUMENT ================

doc = Document()

for sec in doc.sections:
    sec.page_width = Cm(21)
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.5)
    sec.bottom_margin = Cm(2.5)
    sec.left_margin = Cm(2.5)
    sec.right_margin = Cm(2.5)

style = doc.styles["Normal"]
style.font.name = FONT
style.font.size = FONT_SZ
style.font.color.rgb = BODY
style.paragraph_format.line_spacing = LINE_SP
style.paragraph_format.space_after = SP_AFTER

# ==== CAPA / TITULO ====
add_para(doc, text="", after=Pt(20))

add_heading(doc, "CogPIE", 1)
p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, after=Pt(4), before=Pt(2))
para_shading(p, DARK_BG2)
add_run(p, "Cognitive Pattern Inference Engine", italic=True, size=Pt(12), color=NEAR_WHITE)

p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, after=Pt(2))
para_shading(p, DARK_BG2)
add_run(p, "Motor de Inferência de Padrões Cognitivos para Geração Direcionada de Candidatos a Senhas",
        size=Pt(10), color=NEAR_WHITE)

p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, after=Pt(12), before=Pt(12))
add_run(p, "André Henrique de Oliveira", bold=True, size=Pt(12), color=DARK)
add_run(p, "\nUnião Geek Security Research, 2026", size=Pt(9), color=MUTED, italic=True)

# ==== METRICAS DESTAQUE ====
add_stat_block(doc, [
    ("89,7%", "Cobertura WLF"),
    ("51,4%", "CI Leaks Reais"),
    ("75,95%", "Hit@1000 GPU"),
    ("13.487", "Credenciais Reais"),
])

# ==== RESUMO ====
add_abstract_block(doc, "Resumo",
    "A segurança de senhas permanece como um dos desafios mais críticos em segurança da informação. "
    "Este artigo apresenta o CogPIE (Cognitive Pattern Inference Engine), um algoritmo híbrido de cinco camadas "
    "que modela vieses cognitivos para gerar candidatos direcionados de senhas. O CogPIE combina expansão semântica "
    "de tokens pessoais, regras de transformação cognitiva baseadas em vieses psicológicos documentados, um sistema "
    "híbrido de ranqueamento por cadeias de Markov e PCFG, pontuação de entropia prática e filtragem sensível a políticas. "
    "Nossa avaliação experimental abrange dados sintéticos, comparativos com 10 ferramentas externas e validação com "
    "13.487 credenciais reais de vazamentos. O CogPIE atinge 89,7% de cobertura média em benchmarks WLF (10 personas), "
    "51,38% case-insensitive contra credenciais reais e 75,95% hit@1000 com corpus GPU de 1M. Adicionalmente, "
    "demonstramos que a integração do CogPIE ao WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge) elevou a "
    "cobertura média do framework de 39,97% para 89,7%, representando um salto de +124,4% relativo. Nossos resultados "
    "reforçam que cofres de senhas com geração criptograficamente aleatória, ou algoritmos de permutação não baseados em "
    "padrões humanos, permanecem a única defesa confiável contra ataques direcionados. Código-fonte: "
    "github.com/mrhenrike/CogPIE e PyPI.",
    "segurança de senhas, viés cognitivo, adivinhação de senhas, cadeias de Markov, PCFG, ataques direcionados, WordlistXPL-Forge"
)

# ==== ABSTRACT ====
add_abstract_block(doc, "Abstract",
    "Password security remains one of the most critical challenges in information security. This paper presents "
    "CogPIE (Cognitive Pattern Inference Engine), a 5-layer hybrid algorithm that models cognitive biases for targeted "
    "password candidate generation. Our evaluation spans synthetic data, 10 external tools comparison, and validation on "
    "13,487 real leaked credentials. CogPIE achieves 89.7% average coverage on WLF benchmarks, 51.38% case-insensitive "
    "against real leaks, and 75.95% hit@1000 on 1M GPU corpus. We additionally show that integrating CogPIE into "
    "WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge) raised the framework's average coverage from 39.97% to "
    "89.7%, a +124.4% relative improvement. Source: github.com/mrhenrike/CogPIE.",
    "password security, cognitive bias, password guessing, Markov chains, PCFG, targeted attacks, WordlistXPL-Forge",
    kw_label="Keywords"
)

# ============================================================
# 1. INTRODUCAO
# ============================================================
add_heading(doc, "1. Introdução", 2)

add_para(doc, text=(
    "A fraqueza persistente de senhas escolhidas por humanos representa uma tensão fundamental em cibersegurança: "
    "sistemas de autenticação requerem segredos que sejam simultaneamente memoráveis e imprevisíveis. Decadas de "
    "evidências empíricas demonstram que esses objetivos são fundamentalmente incompatíveis quando usuários geram "
    "senhas de memória (Bonneau, 2012; Florêncio e Herley, 2007; Wang et al., 2016)."
))

add_para(doc, text=(
    "A literatura de ciência cognitiva identifica diversos vieses que sistemáticamente reduzem a entropia: "
    "ancoragem (construir ao redor de uma palavra-base reconhecível), efeito de posição serial (modificações "
    "concentradas no início e fim), desconto hiperbólico (priorizar memorabilidade sobre segurança) e heurística "
    "de familiaridade (tokens pessoalmente significativos). Mazurek et al. (2013) confirmaram que mesmo políticas "
    "rigorosas de composição não impedem que ~10% das senhas de uma universidade inteira sejam crackeáveis offline."
))

add_critical_finding(doc, "Contexto-Chave", extract_inline(
    "<strong>76,2%</strong> dos usuários pesquisados fazem apenas modificações menores em senhas existentes "
    "(pesquisa 2026, N=248). <strong>43-51%</strong> reutilizam a mesma senha entre sites (Das et al., 2014). "
    "<strong>41%</strong> das autenticações bem-sucedidas envolvem credenciais vazadas (Cloudflare, 2024). "
    "<strong>81%</strong> dos breaches corporativos envolvem senhas fracas ou roubadas (Verizon DBIR, 2023). "
    "<strong>59%</strong> das pessoas incorporam nome ou data de nascimento em suas senhas (Google/Harris Poll, 2019). "
    "Apenas <strong>34%</strong> da população utiliza um gerenciador de senhas (Bitwarden, 2023)."
))

add_para(doc, text=(
    "Este artigo introduz o CogPIE, um algoritmo híbrido de 5 camadas: (L1) Expansão Semântica, (L2) Transformadas "
    "Cognitivas, (L3) Ranking Probabilístico Markov+PCFG, (L4) Score de Entropia e (L5) Filtragem por Política. "
    "Demonstramos também como a integração do CogPIE ao WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge) "
    "transformou o framework, elevando sua cobertura média de 39,97% para 89,7% em benchmarks de 10 personas."
))

# ============================================================
# 2. TRABALHOS RELACIONADOS
# ============================================================
add_heading(doc, "2. Trabalhos Relacionados", 2)

add_heading(doc, "2.1 Adivinhação Não Direcionada", 3)
add_para(doc, text=(
    "Weir et al. (2009) introduziram PCFG para decomposição de senhas, quebrando 28-129% mais que o John the "
    "Ripper (github.com/openwall/john, acesso: out. 2026). O OMEN (Dürmuth et al., 2015; github.com/RUB-SysSec/OMEN, "
    "acesso: out. 2026) atingiu >40% de taxa de crack em 90M de tentativas com modelo de n-gramas otimizado. "
    "PassGAN (Hitaj et al., 2019; github.com/brannondorsey/PassGAN, acesso: out. 2026) e PassGPT (Rando et al., 2023) "
    "representam abordagens neurais: PassGPT relatou ~20% mais senhas inéditas que modelos anteriores."
))

add_heading(doc, "2.2 Adivinhação Direcionada", 3)
add_para(doc, text=(
    "Wang et al. (2016) formalizaram o TarGuess: 30% de senhas modificadas crackeáveis em 10 tentativas, analisando "
    "28,8M de contas. Li et al. (2017) estenderam com Personal-PCFG, integrando 7 tipos de PII na gramática. "
    "CUPP (Mebus, 2010; github.com/Mebus/cupp, acesso: out. 2026) representa o extremo prático: regras heurísticas "
    "sem modelagem probabilística."
))

add_heading(doc, "2.3 Viéses Cognitivos na Criação de Senhas", 3)
add_para(doc, text=(
    "Abdrabou et al. (2021) forneceram evidências neurofisiológicas via pupilometria (CHI 2021): diâmetro pupilar "
    "correlaciona-se inversamente com a força da senha. Uma pesquisa de 2026 (N=248) encontrou 76,2% dos participantes "
    "fazendo apenas modificações menores. Ur et al. (2015, SOUPS) documentaram que usuários adicionam caracteres "
    "especiais quase exclusivamente no final, e dígitos são tipicamente anos ou datas significativas."
))

add_heading(doc, "2.4 Estimativa de Força de Senhas", 3)
add_para(doc, text=(
    "Bonneau (2012) introduziu alpha-guesswork analisando 70 milhões de senhas anonimizadas. Wheeler (2016) "
    "operacionalizou esses insights no zxcvbn (github.com/dropbox/zxcvbn, acesso: out. 2026). Golla e Dürmuth "
    "(2018) avaliaram sistemáticamente a precisão de medidores de força."
))

add_heading(doc, "2.5 Padrões de Políticas", 3)
add_para(doc, text=(
    "NIST SP 800-63B (2017, rev. 2024) recomenda: mínimo 8 caracteres, verificação contra breaches, sem rotação "
    "periódica, incentivo a passphrases. Kelley et al. (2012) demonstraram que políticas de 16 caracteres sem "
    "requisitos de classe produzem senhas mais fortes que políticas complexas de 8 caracteres."
))

add_heading(doc, "2.6 Reutilização de Senhas", 3)
add_para(doc, text=(
    "Das et al. (2014): 43-51% de reutilização. Florêncio e Herley (2007): média de 25 contas por usuário, 6-7 "
    "senhas distintas. Cloudflare (2024): 41% do tráfego de autenticação envolve credenciais vazadas. Wang et al. "
    "(2016) demonstraram que 73% dos usuários compartilham pelo menos uma senha entre serviços."
))

# ============================================================
# 3. FUNDAMENTACAO TEORICA
# ============================================================
add_heading(doc, "3. Fundamentação Teórica", 2)

add_heading(doc, "3.1 Cadeias de Markov para Modelagem de Senhas", 3)
eq1 = (
    msub(mr('P'), mr('markov', False)) +
    mdel(mr('p')) +
    mr(' = ') +
    mr('P') +
    mdel(msub(mr('c'), mr('1')) + mr(' | ') + msup(mr('START', False), mr('n'))) +
    mr(' ⋅ ') +
    mnary('∏', mr('i = 2'), mr('L'),
        mr('P') + mdel(msub(mr('c'), mr('i')) + mr(' | ') +
            msub(mr('c'), mr('i−n')) + mr('…') + msub(mr('c'), mr('i−1')))
    ) +
    mr(' ⋅ ') +
    mr('P') + mdel(mr('END', False) + mr(' | ') +
        msub(mr('c'), mr('L−n+1')) + mr('…') + msub(mr('c'), mr('L')))
)
add_equation(doc, eq1, "Modelo de n-gramas com suavização Katz (Katz, 1987)")
add_para(doc, text=(
    "Narayanan e Shmatikov (2005) demonstraram eficácia de cadeias de Markov em ataques a dicionários. Ma et al. "
    "(2014) sistematizaram a comparação entre modelos probabilísticos, encontrando que Markov de ordem 4 oferece "
    "o melhor equilíbrio."
))

add_heading(doc, "3.2 Gramáticas Livres de Contexto Probabilísticas", 3)
eq2 = (
    msub(mr('P'), mr('pcfg', False)) +
    mdel(mr('p')) +
    mr(' = ') +
    mr('P') + mdel(mr('S')) +
    mr(' ⋅ ') +
    mnary('∏', mr('i = 1'), mr('k'),
        mr('P') + mdel(msub(mr('terminal', False), mr('i')) + mr(' | ') + msub(mr('s'), mr('i')))
    )
)
add_equation(doc, eq2, "Decomposição estrutural: letras, dígitos, especiais (Weir et al., 2009)")

add_heading(doc, "3.3 Função de Score Híbrido", 3)
eq3 = (
    mr('H') + mdel(mr('c')) +
    mr(' = ') +
    mr('α') + mr(' ⋅ ') +
    mfunc('log', msub(mr('P'), mr('markov', False)) + mdel(mr('c'))) +
    mr(' + ') +
    mdel(mr('1 − α − β')) +
    mr(' ⋅ ') +
    mfunc('log', msub(mr('P'), mr('pcfg', False)) + mdel(mr('c'))) +
    mr(' + ') +
    mr('β') + mr(' ⋅ ') +
    mfunc('log', msub(mr('P'), mr('freq', False)) + mdel(mr('c')))
)
add_equation(doc, eq3, "onde α = 0,4, β = 0,2. Combinação log-linear convexa no espaço de log-probabilidade.")

add_heading(doc, "3.4 Entropia Prática", 3)
eq4 = (
    msub(mr('E'), mr('p')) +
    mdel(mr('c')) +
    mr(' = ') +
    msub(mr('log', False), mr('2')) +
    mdel(mr('G') + mdel(mr('c')))
)
add_equation(doc, eq4, "G(c) = tentativas para atacante ótimo. Bonneau (2012): alpha-guesswork como métrica realista.")

add_heading(doc, "3.5 Modelo Formal de Viés Cognitivo", 3)
eq5 = (
    mr('senha') + mr(' = ') +
    mr('PolicyAdapt', False) +
    mdel(mr('Combine', False) +
        mdel(mr('Transform', False) +
            mdel(mr('Select', False) + mdel(mr('C')))))
)
add_equation(doc, eq5, "Seleção → Transformação → Combinação → Adaptação a política vigente.")

add_heading(doc, "3.6 Teoria da Carga Cognitiva", 3)
add_para(doc, text=(
    "A teoria de Sweller (1988) e o modelo de memória de trabalho de Baddeley (1986) explicam as restrições "
    "fundamentais. O achado clássico de Miller (1956) de 7+-2 itens restringe diretamente a complexidade de "
    "senhas integráveis na memória de trabalho. Adams e Sasse (1999) argumentaram que 'usuários não são o inimigo'."
))

add_key_finding(doc, "Implicação Teórica", extract_inline(
    "Restrições da memória de trabalho significam que usuários não conseguem manter uma senha complexa e única "
    "enquanto a codificam para recuperação posterior. O resultado é dependência sistemática de tokens pessoalmente "
    "significativos e padrões de modificação previsíveis. <strong>O CogPIE modela precisamente essas restrições.</strong>"
))

# ============================================================
# 4. ALGORITMO COGPIE
# ============================================================
add_heading(doc, "4. Algoritmo CogPIE", 2)

add_heading(doc, "4.1 Visão Geral da Arquitetura", 3)
add_figure(doc, 1, "Arquitetura do pipeline de 5 camadas do CogPIE", "fig1_pipeline.png")

add_heading(doc, "4.2 Camada 1: Expansão Semântica", 3)
add_para(doc, text=(
    "[L1] Mapeia cada token bruto para variantes: case_variants, strip_accents, abbreviations, nicknames, leet_single. "
    "Fator médio de expansão: 21,5x (13 tokens brutos para ~279 variantes). Inclui diminutivos culturais, "
    "hipocorísticos e variações ortográficas regionais."
))

add_heading(doc, "4.3 Camada 2: Transformadas Cognitivas", 3)
add_para(doc, text=(
    "[L2] Distribuição das transformadas: combinações de pares (42,5%), sufixos de ano (40,1%), caractere "
    "especial (4,5%), dígito único (3,9%), leetspeak parcial (3,6%), capitalização (2,1%), prefixos (2,1%), "
    "mutações de teclado (1,2%)."
))

add_heading(doc, "4.4 Camada 3: Ranking Probabilístico", 3)
add_para(doc, text=(
    "[L3] Score unificado via combinação log-linear. Convergência O(1/sqrt(|T|)) para Markov, O(1/|T|) para PCFG. "
    "Parâmetro ótimo: a=0,4, b=0,2 para taxa máxima de 60,9% nos dados sintéticos."
))

add_heading(doc, "4.5 Score de Entropia e Filtragem", 3)
add_para(doc, text=(
    "[L4] Score zxcvbn (github.com/dropbox/zxcvbn, acesso: out. 2026): 0 (<10 bits) a 4 (>=34 bits). "
    "[L5] Deduplicação CRC32: 1 em 4,3B falso positivo, 10x economia de memória. "
    "Filtragem sensível a políticas NIST SP 800-63B e requisitos customizáveis."
))

add_heading(doc, "4.6 Complexidade e Margem de Segurança", 3)
add_para(doc, text=(
    "Tempo: O(C . log C). Espaço: O(C + |T| . n . |Sigma|). Típico: 100k-200k candidatos, 28 MB pico, 1,2s. "
    "Entropia efetiva de senha baseada em perfil: ~21 bits (vs. 52,6 bits teóricos para 8 caracteres "
    "alfanuméricos aleatórios)."
))

# ============================================================
# 5. IMPLEMENTACAO
# ============================================================
add_heading(doc, "5. Implementação", 2)
add_para(doc, text=(
    "Módulo Python dentro do WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge, XPL-Suite). "
    "Seis arquivos (~800 LOC): semantic_expander.py (L1), cognitive_transforms.py (L2), markov_pcfg_hybrid.py (L3), "
    "scorer.py (L4), policy_filter.py (L5), engine.py (orquestrador). Integra-se com o ecossistema WLF existente: "
    "motor Markov posicional (baseado em OMEN), gerador PCFG, profiler CUPP, permutador leet, keyboard walk generator "
    "(9 layouts) e estimador de entropia. Distribuído via PyPI (v1.0.1, acesso: out. 2026). "
    "Código-fonte: github.com/mrhenrike/CogPIE."
))

# ============================================================
# 6. AVALIACAO EXPERIMENTAL
# ============================================================
add_heading(doc, "6. Avaliação Experimental", 2)

add_heading(doc, "6.1 Metodologia", 3)
add_para(doc, text=(
    "Avaliação em seis frentes: (i) datasets sintéticos com 5 perfis e 87 senhas; (ii) 10 personas WLF com "
    "complexidade crescente; (iii) 10 ferramentas externas; (iv) 13.487 credenciais reais de vazamentos; "
    "(v) escala GPU com corpus de 1M; (vi) evolução do WLF pre e pós-CogPIE. Todos os experimentos sintéticos "
    "utilizam exclusivamente dados sintéticos. A validação com credenciais reais emprega métricas agregadas conforme "
    "protocolo de Das et al. (2014)."
))

# -- 6.2 Sintéticos --
add_heading(doc, "6.2 Resultados Sintéticos", 3)

# Mini stat block para sintéticos
t_syn = doc.add_table(rows=2, cols=3)
t_syn.alignment = WD_TABLE_ALIGNMENT.CENTER
for ci, (name, val, detail) in enumerate([
    ("CogPIE", "60,9%", "53/87 senhas | ~119.880 cand."),
    ("CUPP Baseline", "51,7%", "45/87 senhas | ~121 cand."),
    ("Markov Baseline", "0,0%", "0/87 senhas | 71 comuns"),
]):
    c0 = t_syn.rows[0].cells[ci]
    cell_para(c0, val, bold=True, size=Pt(16), color=NEAR_WHITE if ci == 0 else WHITE,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_shading(c0, ACCENT_HEX if ci == 0 else DARK_BG)
    c1 = t_syn.rows[1].cells[ci]
    cell_para(c1, f"{name}\n{detail}", size=Pt(7),
              color=NEAR_WHITE if ci == 0 else WHITE,
              align=WD_ALIGN_PARAGRAPH.CENTER)
    cell_shading(c1, ACCENT_DARK_HEX if ci == 0 else DARK_BG2)

# Remove bordas
tbl_s = t_syn._tbl
tblpr_s = tbl_s.tblPr if tbl_s.tblPr is not None else parse_xml(f'<w:tblPr {nsdecls("w")}/>')
tblpr_s.append(parse_xml(
    f'<w:tblBorders {nsdecls("w")}>'
    f'<w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    f'<w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    f'<w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    f'<w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    f'<w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>'
    f'<w:insideV w:val="single" w:sz="4" w:space="0" w:color="FFFFFF"/>'
    f'</w:tblBorders>'
))
keep_table_together(t_syn)
add_para(doc, text="", after=Pt(6))

add_para(doc, text=(
    "CogPIE supera CUPP em 4 de 5 perfis e empata em um (Ana 52,9%). Melhoria relativa de 17,8%. O Markov baseline "
    "(sem treinamento direcionado) não encontra nenhuma senha, confirmando que adivinhação não direcionada e "
    "ineficaz sem corpus de treinamento relevante."
))

# -- 6.3 Ablação --
add_heading(doc, "6.3 Estudo de Ablação por Camada", 3)
add_table(doc,
    ["Configuração", "Taxa", "Delta", "Nota"],
    [
        ["CogPIE Completo", "60,9%", "baseline", "5 camadas ativas"],
        ["Sem L1 (expansão)", "35,0%", "-25,9pp", "Sem apelidos, abreviações, variantes"],
        ["Sem L2 (transformadas)", "20,0%", "-40,9pp", "Sem sufixo/leet/pares"],
        ["Sem L3 (ranking)", "60,9%", "0pp", "Mesmos candidatos, sem ordenação"],
        ["CUPP baseline", "51,7%", "-9,2pp", "Concatenação simples"],
    ], hl_first=True)

add_figure(doc, 2, "Estudo de ablação: impacto da remoção de cada camada", "fig2_ablation.png")

# -- 6.4 Online --
add_heading(doc, "6.4 Cenário de Ataque Online", 3)
add_table(doc,
    ["Budget", "CogPIE", "CUPP", "Vantagem"],
    [
        ["Top 10", "8,0%", "6,9%", "+1,1pp"],
        ["Top 100", "23,0%", "20,7%", "+2,3pp"],
        ["Top 1.000", "40,2%", "37,9%", "+2,3pp"],
        ["Top 10.000", "52,9%", "48,3%", "+4,6pp"],
        ["Completo", "60,9%", "51,7%", "+9,2pp"],
    ])

add_para(doc, text=(
    "A vantagem do CogPIE cresce com o budget disponível, indicando que o ranking probabilístico (L3) posiciona "
    "candidatos mais prováveis no topo."
))

# ============================================================
# 6.5 Corpus Real
# ============================================================
add_heading(doc, "6.5 Validação com Corpus Real: 13.487 Credenciais de Vazamentos", 3)
add_para(doc, text=(
    "Para validar o CogPIE além de dados sintéticos, conduzimos avaliação em larga escala com 13.487 credenciais "
    "reais de compilações públicas (SecLists, IntelX)."
))

add_table(doc,
    ["Região/Tipo", "Quantidade", "%"],
    [
        ["Webmail global (Gmail, Yahoo, Hotmail)", "9.890", "73,3%"],
        ["Outros domínios", "3.000", "22,2%"],
        ["CN/TW/HK", "517", "3,8%"],
        ["Brasil (.br)", "80", "0,6%"],
        ["Total", "13.487", "100%"],
    ], has_total=True)

add_repo_note(doc)

add_table(doc,
    ["Algoritmo", "Repositório", "CS", "CI", "Exclusivos", "Rank Med."],
    [
        ["CogPIE", "mrhenrike/CogPIE (PyPI)", "46,61%", "51,38%", "541", "20"],
        ["CUPP-WLF", "Mebus/cupp", "38,27%", "38,51%", "674", "8"],
        ["BopScrk", "R3nt0n/bopscrk", "35,58%", "36,45%", "2", "-"],
        ["ElpScrk", "D4Vinci/elpscrk", "34,49%", "35,02%", "3", "-"],
        ["PsudoHash", "t3l3machus/psudohash", "32,76%", "33,17%", "9", "-"],
        ["Pydictor SEDB", "LandGrey/pydictor", "31,64%", "32,38%", "2", "-"],
        ["LongTongue", "edoardottt/longtongue", "25,55%", "26,29%", "0", "-"],
        ["Combinado (todos)", "", "52,14%", "52,14%", "-", "-"],
    ], hl_first=True, has_total=True)

p = add_para(doc, text="Todos os repositórios acessados em outubro de 2026.", size=Pt(8), color=MUTED)

add_figure(doc, 3, "Taxa CI de cada algoritmo contra 13.487 credenciais reais", "fig3_real_leaks.png")

add_critical_finding(doc, "Resultado: Corpus Real", extract_inline(
    "O CogPIE atinge <strong>46,61% CS e 51,38% CI</strong> contra 13.487 credenciais reais, superando o "
    "segundo colocado (CUPP-WLF, 38,27%) por <strong>+8,34pp</strong>. Produz <strong>541 hits exclusivos</strong> "
    "que nenhuma outra ferramenta encontra. A cobertura combinada (52,14%) supera o CogPIE sozinho em apenas "
    "0,76pp, confirmando que o CogPIE captura a vasta maioria do espaço acessível."
))

# ============================================================
# 6.6 WLF 10 Personas
# ============================================================
add_heading(doc, "6.6 Comparativo WLF Interno: 10 Personas", 3)
add_para(doc, text=(
    "Benchmark com 10 personas (P01_minimal a P10_complete), budget de 50K candidatos, perfis com complexidade "
    "crescente de informação pessoal disponível:"
))

add_table(doc,
    ["Persona", "CogPIE", "CUPP", "BopScrk", "Markov"],
    [
        ["P01_minimal", "80,00%", "33,33%", "26,67%", "20,00%"],
        ["P02_basic", "85,00%", "45,00%", "15,00%", "10,00%"],
        ["P03_standard", "88,46%", "38,46%", "23,08%", "11,54%"],
        ["P04_extended", "87,50%", "37,50%", "18,75%", "12,50%"],
        ["P05_extended", "90,91%", "40,91%", "22,73%", "13,64%"],
        ["P06_social", "91,30%", "43,48%", "17,39%", "13,04%"],
        ["P07_cultural", "96,00%", "36,00%", "24,00%", "16,00%"],
        ["P08_technical", "88,89%", "37,04%", "22,22%", "14,81%"],
        ["P09_rich", "96,15%", "42,31%", "19,23%", "11,54%"],
        ["P10_complete", "93,55%", "45,16%", "25,81%", "16,13%"],
        ["Média", "89,7%", "39,97%", "21,51%", "13,80%"],
    ], hl_first=False, has_total=True)

add_figure(doc, 4, "CogPIE vs CUPP vs BopScrk vs Markov em 10 personas", "fig4_personas.png")

add_key_finding(doc, "Resultado WLF", extract_inline(
    "CogPIE: <strong>89,7% média</strong> (min 80%, max 96,15%), vencendo 10/10. "
    "Diferenca para CUPP: <strong>+49,73pp</strong>. Correlação riqueza do perfil vs cobertura: Pearson r=0,81."
))

# ============================================================
# 6.7 Ferramentas Externas
# ============================================================
add_heading(doc, "6.7 Comparativo com Ferramentas Externas: 10 Algoritmos", 3)

add_repo_note(doc)

add_table(doc,
    ["Ferramenta", "Repositório", "Tipo", "Personas 0%", "Melhor"],
    [
        ["CogPIE", "mrhenrike/CogPIE (PyPI)", "Cognitivo híbrido", "0", "96,15%"],
        ["WLF Combinado", "mrhenrike/WordlistXPL-Forge", "Ensemble", "0", "100%"],
        ["CUPP-WLF", "Mebus/cupp", "Profiling", "0", "45,16%"],
        ["ElpScrk", "D4Vinci/elpscrk", "Combinatorio", "0", "~50%"],
        ["PsudoHash", "t3l3machus/psudohash", "Pattern-based", "0", "~45%"],
        ["BopScrk", "R3nt0n/bopscrk", "Combinatorio", "0", "~35%"],
        ["LongTongue", "edoardottt/longtongue", "Concatenação", "0", "~30%"],
        ["Pydictor SEDB", "LandGrey/pydictor", "Social eng. dict.", "0", "~35%"],
        ["CUPP Original", "Mebus/cupp", "Interativo", "10/10", "0%"],
        ["PassPwn", "Proprietario", "Credenciais", "~10/10", "~0%"],
    ], hl_first=True)

p = add_para(doc, text="Todos os repositórios acessados em outubro de 2026.", size=Pt(8), color=MUTED)

add_figure(doc, 5, "7 algoritmos: credenciais reais (CI) + hits exclusivos", "fig5_external_ci.png")

add_critical_finding(doc, "Descoberta Crítica", extract_inline(
    "O <strong>CUPP original atinge 0% em todas as 10 personas</strong>: seu modo interativo excede o timeout de "
    "15s ao processar perfis via API, gerando zero candidatos. A ferramenta mais citada em tutoriais de pentest "
    "falha completamente em uso programático automatizado."
))

# ============================================================
# 6.8 Ferramentas Expandidas
# ============================================================
add_heading(doc, "6.8 Ferramentas Expandidas: CrackSmith e ElpScrk", 3)
add_para(doc, text=(
    "Benchmark com 6 algoritmos (cogpie, cupp_wlf, bopscrk, elpscrk, cracksmith, expanded_combined), budget 50K, "
    "10 personas. CrackSmith (módulo interno do WLF) demonstra força em perfis minimalistas (P01: 86,67%). "
    "ElpScrk é competitivo em budgets baixos. O CogPIE e o ensemble expandido frequentemente empatam, confirmando "
    "que o CogPIE captura a vasta maioria dos candidatos que as ferramentas expandidas adicionariam."
))

# ============================================================
# 6.9 Escala GPU
# ============================================================
add_heading(doc, "6.9 Benchmarks de Escala: GPU com Corpus de 1M", 3)

add_table(doc,
    ["Cenário", "CogPIE", "CUPP", "Markov"],
    [
        ["GPU 1M / 500 alvos", "48,0%", "46,0%", "3,2%"],
        ["GPU 1M / 2.000 alvos", "50,15% (1.003 hits)", "47,55% (951)", "4,80%"],
    ], hl_first=False)

add_para(doc, text="Métricas de ranking do CogPIE standalone (1M corpus, 2.000 alvos):", bold=True)

add_table(doc,
    ["Métrica", "Valor", "Interpretação"],
    [
        ["Hit@10", "24,05%", "~1 em 4 senhas nas primeiras 10 tentativas"],
        ["Hit@100", "59,30%", "Maioria encontrada em 100 tentativas"],
        ["Hit@1.000", "75,95%", "3/4 das senhas em budget moderado"],
        ["MRR", "0,137", "Ranking eficiente; senha correta tipicamente no top 7"],
        ["Rank Médiano", "35", "Metade das senhas nos primeiros 35 candidatos"],
    ])

add_figure(doc, 6, "Curva Hit@K: CogPIE vs CUPP vs Markov (GPU 1M, 2.000 alvos)", "fig6_hitk.png")

add_critical_finding(doc, "Resultado de Escala GPU", extract_inline(
    "Com corpus de 1M e treinamento GPU, CogPIE atinge <strong>75,95% hit@1000</strong>: tres quartos das senhas "
    "encontradas em 1.000 tentativas. Rank médiano de 35 indica que a senha correta tipicamente aparece entre os "
    "primeiros 35 candidatos."
))

add_para(doc, text="RockYou 500K (200 alvos com PII detectável, 46,5% do total):", bold=True, before=Pt(6))
add_table(doc,
    ["Algoritmo", "Hit@1.000", "Vantagem vs. Markov"],
    [
        ["CogPIE", "67,5%", "+39,0pp"],
        ["CUPP", "43,5%", "+15,0pp"],
        ["Markov", "28,5%", "baseline"],
    ], hl_first=True)

# ============================================================
# 6.10 Evolução do WLF
# ============================================================
add_heading(doc, "6.10 Evolução do WordlistXPL-Forge com CogPIE", 3)
add_para(doc, text=(
    "O WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge) é um framework de geração de wordlists "
    "direcionadas que integra multiplos algoritmos. A incorporação do CogPIE (github.com/mrhenrike/CogPIE) "
    "em outubro de 2026 (v2.0.0) representou uma transformação fundamental."
))

add_heading(doc, "WLF Pré-CogPIE (antes de outubro de 2026)", 3)
add_table(doc,
    ["Módulo", "Técnica", "Média 10 Personas"],
    [
        ["CUPP-WLF (profiler adaptado)", "Concatenação heurística de tokens", "39,97%"],
        ["BopScrk", "Combinação exaustiva de tokens", "21,51%"],
        ["Markov posicional (OMEN-based)", "N-gramas sem contexto pessoal", "13,80%"],
        ["Permutador leet", "Substituições alfanuméricas", "Complementar"],
        ["Estimador de entropia", "Score zxcvbn", "Filtragem"],
        ["WLF Combinado (pré-CogPIE)", "Ensemble de todos acima", "~45-55%"],
    ], has_total=True)

add_heading(doc, "WLF Pós-CogPIE (outubro de 2026 em diante, v2.0.0+)", 3)
add_para(doc, text="O CogPIE adicionou:")
for item in [
    "Expansão semântica (L1): apelidos, hipocorísticos, abreviaturas culturais (21,5x expansão)",
    "Transformadas cognitivas (L2): 8 tipos de mutação baseados em vieses documentados",
    "Ranking híbrido (L3): Markov+PCFG+frequência com combinação log-linear",
    "Score de entropia prática (L4) + filtragem por política (L5)",
    "V2.1.0 (W21): keyboard walk com 9 layouts, plate profiler, 662 testes",
]:
    add_bullet(doc, item)

# Tabela de evolução
add_table(doc,
    ["Métrica", "WLF Pré-CogPIE", "WLF Pós-CogPIE", "Evolução"],
    [
        ["Média 10 personas (melhor módulo)", "39,97% (CUPP-WLF)", "89,7% (CogPIE)", "+124,4% relativo"],
        ["Mínima (pior persona)", "33,33%", "80,00%", "+140,0% relativo"],
        ["Máxima (melhor persona)", "45,16%", "96,15%", "+112,9% relativo"],
        ["CI em leaks reais (13.487)", "38,51% (CUPP-WLF)", "51,38% (CogPIE)", "+33,4% relativo"],
        ["Hits exclusivos (leaks)", "674 (CUPP-WLF)", "541 (CogPIE)", "Complementares"],
        ["Hit@1000 (GPU 1M)", "~43,5% (CUPP)", "75,95% (CogPIE)", "+74,6% relativo"],
        ["Ensemble combinado (leaks)", "~42%", "52,14%", "+24,1% relativo"],
        ["Módulos totais (v2.1.0)", "~15", "32+", "+113%"],
        ["Testes automáticos", "~200", "662", "+231%"],
    ])

# WLF vs External
add_heading(doc, "WLF vs. Ferramentas Externas Populares (com e sem CogPIE)", 3)
add_repo_note(doc)

add_table(doc,
    ["Ferramenta", "Repositório", "Direcionada?", "Média Personas", "Leaks CI"],
    [
        ["WLF + CogPIE", "mrhenrike/WordlistXPL-Forge", "Sim (9 PII)", "89,7%", "51,38%"],
        ["WLF (sem CogPIE)", "mrhenrike/WordlistXPL-Forge", "Sim (limitado)", "39,97%", "38,51%"],
        ["CUPP", "Mebus/cupp", "Sim (interativo)", "0% (API)", "-"],
        ["BopScrk", "R3nt0n/bopscrk", "Sim", "21,51%", "36,45%"],
        ["ElpScrk", "D4Vinci/elpscrk", "Sim", "-", "35,02%"],
        ["PsudoHash", "t3l3machus/psudohash", "Sim", "-", "33,17%"],
        ["Pydictor", "LandGrey/pydictor", "Sim (SEDB)", "-", "32,38%"],
        ["LongTongue", "edoardottt/longtongue", "Sim", "-", "26,29%"],
        ["hashcat (rules)", "hashcat/hashcat", "Não (regras)", "N/A", "N/A"],
        ["John the Ripper", "openwall/john", "Não (regras)", "N/A", "N/A"],
        ["OMEN", "RUB-SysSec/OMEN", "Não (n-gramas)", "13,80%", "-"],
        ["PassGAN", "brannondorsey/PassGAN", "Não (GAN)", "N/A", "N/A"],
    ], hl_first=True)

p = add_para(doc, text=(
    "Todos os repositórios acessados em outubro de 2026. hashcat e John the Ripper são crackers "
    "(consomem wordlists), não geradores direcionados."
), size=Pt(8), color=MUTED)

add_figure(doc, 7, "Evolução do WLF: pre vs pos CogPIE em 5 métricas-chave", "fig7_evolution.png")

add_critical_finding(doc, "Evolução WLF", extract_inline(
    "A integração do CogPIE elevou o melhor resultado individual do WLF de <strong>39,97% para 89,7%</strong> "
    "(+124,4% relativo). O WLF com CogPIE supera todas as ferramentas externas testadas. "
    "Contra credenciais reais (13.487), o WLF+CogPIE (51,38% CI) supera o melhor resultado "
    "pré-CogPIE (38,51%) por +12,87pp absolutos."
))

# ============================================================
# 6.11 Limitações
# ============================================================
add_heading(doc, "6.11 Limitações", 3)
for i, item in enumerate([
    "Dependência do perfil: A eficácia é proporcional a completude do perfil-alvo. Personas minimalistas (P01) "
    "atingem 80%, enquanto perfis completos (P09/P10) ultrapassam 96%.",
    "Lacunas de benchmark: Comparação direta com TarGuess (Wang et al., 2016) e Personal-PCFG (Li et al., 2017) "
    "em datasets compartilhados permanece pendente.",
    "Ausência de modelagem temporal: O CogPIE não modela a evolução de senhas ao longo do tempo (password aging).",
], 1):
    add_numbered(doc, str(i), item.split(":")[0] + ":", item.split(":", 1)[1].strip())

# ============================================================
# 7. DISCUSSAO
# ============================================================
add_heading(doc, "7. Discussão", 2)

add_heading(doc, "7.1 Implicações: Fenômeno Cognitivo Universal", 3)
add_para(doc, text=(
    "Nossos resultados fornecem evidência quantitativa: senhas geradas por humanos são fundamentalmente inseguras "
    "contra ataques direcionados. Os vieses cognitivos modelados pelo CogPIE são universais entre culturas:"
))
for item in [
    "Bonneau (2012): 70 milhões de senhas; padrões idênticos entre nacionalidades.",
    "Wang et al. (2016): 28,8M de contas; 30% das senhas modificadas crackeáveis em 10 tentativas.",
    "Li et al. (2019): Estudo em larga escala de senhas chinesas confirmou os mesmos vieses.",
    "Cloudflare (2024): 41% do tráfego de autenticação global envolve credenciais vazadas.",
    "Verizon DBIR (2023): 81% dos breaches corporativos envolvem credenciais fracas ou roubadas.",
    "IBM (2023): Custo médio de um data breach: US$ 4,45M; credenciais comprometidas tem maior tempo de detecção.",
]:
    add_bullet(doc, item)

add_critical_finding(doc, "Tese Central", extract_inline(
    "Os vieses cognitivos são <strong>propriedades da espécie humana</strong>, enraizados na arquitetura da "
    "memória de trabalho. <strong>Nenhuma complexidade de política pode superar os limites da memória humana.</strong> "
    "A única solução eficaz é remover o humano do processo de geração de senhas."
))

add_heading(doc, "7.2 Recomendações de Defesa", 3)
defenses = [
    ("Gerenciadores de senhas", "com geração criptograficamente aleatória: Única defesa confiável. Exemplos: 1Password, Bitwarden, KeePassXC."),
    ("Geração automática via vault corporativo:", "HashiCorp Vault, CyberArk, AWS Secrets Manager."),
    ("MFA (Autenticação Multifator):", "TOTP, push notifications e hardware tokens."),
    ("FIDO2/WebAuthn passkeys:", "Elimina senhas inteiramente da cadeia de autenticação."),
    ("Verificação contra breaches:", "Conforme NIST SP 800-63B, HIBP API com k-anonimato."),
    ("Modernização de políticas:", "Comprimento mínimo de 15+ caracteres + verificação de vazamentos."),
    ("Algoritmos de geração não baseados em perfil humano:", "/dev/urandom, secrets.token_urlsafe(), Diceware."),
]
for i, (title, body) in enumerate(defenses, 1):
    add_numbered(doc, str(i), title, body)

add_heading(doc, "7.3 Considerações Éticas", 3)
add_para(doc, text=(
    "O CogPIE é projetado para testes de segurança autorizados. Bonneau (2012) analisou 70M de senhas de forma "
    "completamente anonimizada. Wang et al. (2016) conduziram análises com protocolo rigoroso de divulgação "
    "responsável. Todos os testes com o CogPIE requerem autorização explícita."
))

add_heading(doc, "7.4 Comparação com Abordagens Neurais", 3)
add_table(doc,
    ["Dimensão", "CogPIE", "PassGAN/PassGPT", "TarGuess"],
    [
        ["Modo", "Direcionado", "Não direcionado", "Direcionado"],
        ["Perfil", "9 tipos PII", "Nenhum", "7 tipos PII"],
        ["Modelagem cognitiva", "Explícita (5 camadas)", "Implicita (latente)", "Implicita (probabilística)"],
        ["Interpretabilidade", "Alta (cada camada auditável)", "Baixa (caixa-preta)", "Média"],
        ["Dados de treinamento", "Opcional (melhora ranking)", "Obrigatório (milhões)", "Obrigatório"],
        ["Tempo de geração", "1,2s (CPU)", "Horas (GPU)", "Segundos (CPU)"],
        ["Expansão semântica", "Sim (cultural)", "Não", "Não"],
        ["Keyboard walk", "Sim (9 layouts)", "Não", "Parcial (Xie, 2020)"],
    ])

add_heading(doc, "7.5 Trabalhos Futuros", 3)
futures = [
    ("Expansão cross-cultural.", "O CogPIE v1.0 implementa expansão semântica para português, espanhol e inglês. "
     "Idiomas com sistemas de escrita distintos (hindi, árabe, coreano, japonês) apresentam padrões de romanização "
     "e hipocorísticos que o pipeline atual não captura inteiramente."),
    ("Modelagem temporal e password aging.", "O CogPIE trata cada senha como evento estático. Pal et al. (2019) "
     "demonstraram que usuários aplicam transformações previsíveis ao atualizar senhas: incremento numérico, "
     "rotação de sufixo e substituição leet crescente."),
    ("Aprendizado ativo com feedback de tentativas.", "Em cenários de online guessing, um mecanismo de reinforcement "
     "learning poderia ajustar os pesos do ranking L3 em tempo real, maximizando a probabilidade de sucesso."),
    ("Integração com transformers para ranking neural.", "Pasquini et al. (2021) demonstraram que representações "
     "aprendidas via redes neurais superam n-gramas tradicionais. Arquitetura hibrida mantendo pipeline cognitivo "
     "para geração, substituindo ranking L3 por scorer neural."),
    ("Análise de passphrases multi-palavra.", "Com a adoção crescente de Diceware e BIP-39, emerge nova classe de "
     "senhas onde vieses cognitivos operam no nível lexical."),
    ("Correlação cross-service.", "Das et al. (2014) revelaram que 43-51% dos usuários reutilizam senhas com "
     "modificações previsíveis. Extensão que modelasse regras de derivação cross-service."),
    ("Benchmark compartilhado.", "Comparação direta com TarGuess e Personal-PCFG permanece pendente. "
     "Criação de benchmark com perfis anonimizados e credenciais sintéticas padronizadas."),
]
for i, (title, body) in enumerate(futures, 1):
    add_numbered(doc, str(i), title, body)

# ============================================================
# 8. CONCLUSAO
# ============================================================
add_heading(doc, "8. Conclusão", 2)

conclusions = [
    "Este trabalho apresentou o CogPIE (Cognitive Pattern Inference Engine), um motor de inferência de padrões "
    "cognitivos de cinco camadas para geração direcionada de candidatos a senhas. A premissa central é que a criação "
    "de senhas por humanos e governada por vieses cognitivos documentados (ancoragem, familiaridade, posição serial, "
    "esforço mínimo e desconto hiperbólico) que operam de forma universal.",

    "Nos benchmarks sintéticos com 5 perfis e 87 senhas ground-truth, o CogPIE atingiu 60,9% de cobertura, "
    "superando o CUPP em +17,8% relativo. Na avaliação com as 10 personas do WordlistXPL-Forge, o CogPIE obteve "
    "89,7% de média (mínimo 80%, máximo 96,15%), vencendo em 10 de 10 personas.",

    "A validação contra 13.487 credenciais reais (SecLists, IntelX) confirmou que esses ganhos se estendem além "
    "de dados sintéticos: CogPIE atingiu 51,38% de cobertura case-insensitive, contra 38,51% do CUPP-WLF. "
    "541 credenciais foram encontradas exclusivamente pelo CogPIE.",

    "Na escala GPU com corpus de 1M e 2.000 alvos, o CogPIE alcancou 50,15% de hit rate global, com Hit@10 de "
    "24,05%, Hit@100 de 59,30%, Hit@1000 de 75,95% e rank médiano de 35.",

    "A comparação com ferramentas externas revelou que o CUPP original atingiu 0% em todas as 10 personas quando "
    "utilizado via API programática. Ferramentas como BopScrk (36,45% CI), ElpScrk (35,02%), PsudoHash (33,17%), "
    "Pydictor SEDB (32,38%) e LongTongue (26,29%) demonstraram cobertura substancialmente inferior.",

    "A integração do CogPIE ao WordlistXPL-Forge (github.com/mrhenrike/WordlistXPL-Forge) na versão 2.0.0 "
    "transformou o framework: o melhor resultado individual saltou de 39,97% para 89,7% (+124,4% relativo), "
    "o piso de desempenho subiu de 33,33% para 80,00% (+140,0% relativo).",

    "A defesa eficaz requer a remoção do ser humano do processo de geração de credenciais. Gerenciadores de "
    "senhas com geração CSPRNG, vaults corporativos com rotação automática, FIDO2/WebAuthn com passkeys e "
    "verificação contra bases de vazamentos oferecem as únicas defesas confiáveis.",

    "A contribuição central é tripla: (1) demonstração empírica de que vieses cognitivos são exploráveis de "
    "forma sistemática; (2) arquitetura de pipeline de cinco camadas auditável; e (3) integração como módulo "
    "de um framework real (WLF, github.com/mrhenrike/WordlistXPL-Forge). "
    "Código-fonte: github.com/mrhenrike/CogPIE.",
]
for text in conclusions:
    add_para(doc, text=text)

# Bloco final de sintese
add_separator(doc)

add_critical_finding(doc, "Síntese dos Resultados", extract_inline(
    "<strong>60,9%</strong> (sintético) -> <strong>89,7%</strong> (personas) -> <strong>51,38%</strong> (13.487 leaks reais) "
    "-> <strong>75,95%</strong> Hit@1000 (GPU 1M). WLF transformado: de 39,97% para 89,7% (+124,4%). "
    "541 hits exclusivos. CUPP original: 0% em uso programático. Execução: <2s, 28 MB, hardware commodity. "
    "A única defesa comprovada: remoção do humano da geração de credenciais via CSPRNG, vaults com rotação "
    "automática e passkeys FIDO2/WebAuthn."
))

# ============================================================
# REFERENCIAS
# ============================================================
add_heading(doc, "Referências", 2)

refs = [
    "Abdrabou, Y., et al. (2021). 'Cognitive Load and Password Strength: A Pupillometry Study.' CHI 2021.",
    "Adams, A. and Sasse, M. A. (1999). 'Users Are Not the Enemy.' CACM, 42(12), pp. 40-46.",
    "Baddeley, A. D. (1986). Working Memory. Oxford University Press.",
    "Bitwarden (2023). 'World Password Day Survey.' Bitwarden Blog.",
    "Bonneau, J. (2012). 'The Science of Guessing: Analyzing an Anonymized Corpus of 70 Million Passwords.' IEEE S&P.",
    "Bonneau, J. (2012). 'Statistical Metrics for Individual Password Strength.' Security Protocols Workshop, LNCS 7622.",
    "Castelluccia, C. and Dürmuth, M. (2012). 'Adaptive Password-Strength Meters from Markov Models.' NDSS.",
    "Cloudflare (2024). 'Leaked Credentials in Authentication Traffic.' Cloudflare Radar Annual Report.",
    "Das, A., et al. (2014). 'The Tangled Web of Password Reuse.' NDSS.",
    "Dell'Amico, M. and Filippone, M. (2015). 'Monte Carlo Strength Evaluation.' ACM CCS.",
    "Dürmuth, M., et al. (2015). 'OMEN: Faster Password Guessing Using an Ordered Markov Enumerator.' ESSoS. Repo: github.com/RUB-SysSec/OMEN.",
    "Florêncio, D. and Herley, C. (2007). 'A Large-Scale Study of Web Password Habits.' WWW 2007.",
    "Forget, A., et al. (2008). 'Improving Text Passwords Through Persuasion.' SOUPS 2008.",
    "Golla, M. and Dürmuth, M. (2018). 'On the Accuracy of Password Strength Meters.' ACM CCS.",
    "Google/Harris Poll (2019). 'Online Security Survey.' Google Blog.",
    "Hitaj, B., et al. (2019). 'PassGAN: A Deep Learning Approach for Password Guessing.' ACNS. Repo: github.com/brannondorsey/PassGAN.",
    "IBM (2023). 'Cost of a Data Breach Report 2023.' IBM Security / Ponemon Institute.",
    "Imperva (2010). 'Consumer Password Worst Practices.' ADC Report.",
    "Katz, S. M. (1987). 'Estimation of Probabilities from Sparse Data.' IEEE TASSP, 35(3).",
    "Kelley, P. G., et al. (2012). 'Guess Again: Measuring Password Strength by Simulating Cracking.' IEEE S&P.",
    "Komanduri, S., et al. (2011). 'Of Passwords and People.' CHI 2011.",
    "Li, Y., Wang, H., and Sun, K. (2017). 'Personal Information in Passwords and Its Security Implications.' IEEE TIFS, 12(10).",
    "Li, Z., et al. (2019). 'Large-Scale Empirical Study of Chinese Web Passwords.' USENIX Security.",
    "Ma, J., et al. (2014). 'A Study of Probabilistic Password Models.' IEEE S&P.",
    "Mazurek, M. L., et al. (2013). 'Measuring Password Guessability for an Entire University.' ACM CCS.",
    "Mebus, M. (2010). 'CUPP: Common User Passwords Profiler.' Repo: github.com/Mebus/cupp.",
    "Melicher, W., et al. (2016). 'Fast, Lean, and Accurate: Modeling Password Guessability Using Neural Networks.' USENIX Security.",
    "Miller, G. A. (1956). 'The Magical Number Seven, Plus or Minus Two.' Psychological Review, 63(2), pp. 81-97.",
    "Narayanan, A. and Shmatikov, V. (2005). 'Fast Dictionary Attacks on Passwords.' ACM CCS.",
    "NIST (2017, rev. 2024). 'Digital Identity Guidelines: Authentication and Lifecycle Management.' SP 800-63B.",
    "Oesch, S. and Ruoti, S. (2020). 'That Was Then, This Is Now: Security Evaluation of Browser-Based Password Managers.' USENIX Security.",
    "Pal, B., et al. (2019). 'Beyond Credential Stuffing: Password Similarity Models Using Neural Networks.' IEEE S&P.",
    "Pasquini, D., et al. (2021). 'Improving Password Guessing via Representation Learning.' IEEE S&P.",
    "Rando, J., et al. (2023). 'PassGPT: Password Modeling with Large Language Models.' ESORICS.",
    "Shay, R., et al. (2010). 'Encountering Stronger Password Requirements.' SOUPS 2010.",
    "Sweller, J. (1988). 'Cognitive Load During Problem Solving.' Cognitive Science, 12(2), pp. 257-285.",
    "Ur, B., et al. (2015). 'Measuring Real-World Accuracies in Modeling Password Guessability.' USENIX Security.",
    "Ur, B., et al. (2015). 'I Added ! at the End to Make It Secure: Observing Password Creation in the Lab.' SOUPS 2015.",
    "Ur, B., et al. (2016). 'Do Users Perceptions of Password Security Match Reality?' CHI 2016.",
    "Veras, R., et al. (2014). 'On the Semantic Patterns of Passwords.' NDSS.",
    "Verizon (2023). 'Data Breach Investigations Report (DBIR).' 16th Edition.",
    "Wang, D. and Jian, G. (2014). 'Zipf's Law in Passwords.' IACR ePrint 2014/631.",
    "Wang, D., et al. (2016). 'Targeted Online Password Guessing: An Underestimated Threat.' ACM CCS.",
    "Wang, D., et al. (2016). 'The Next Domino to Fall: Empirical Analysis of User Passwords across Services.' ACM CCS.",
    "Wash, R., et al. (2016). 'Understanding Password Choices.' SOUPS 2016.",
    "Weir, M., et al. (2009). 'Password Cracking Using Probabilistic Context-Free Grammars.' IEEE S&P.",
    "Wheeler, D. L. (2016). 'zxcvbn: Low-Budget Password Strength Estimation.' USENIX Security. Repo: github.com/dropbox/zxcvbn.",
    "Xie, X. (2020). 'Modified TarGuess-I: Adding Keyboard Patterns.' Master's Thesis.",
    "Survey (2026). 'Cognitive Biases in Password Security: A Survey-Based Analysis.' arXiv:2607.19586.",
    "AI Password Study (2026). 'AI vs. User-Generated Passwords: Cognitive Bias Patterns.' arXiv:2604.19410.",
    "MDPI (2023). 'Systematic Review of Password Guessing Methods.' MDPI Entropy.",
    "Yan, J., et al. (2004). 'Password Memorability and Security: Empirical Results.' IEEE S&P, 2(5).",
]
for i, ref in enumerate(refs, 1):
    p = add_para(doc, after=Pt(2))
    p.paragraph_format.left_indent = Cm(0.8)
    p.paragraph_format.first_line_indent = Cm(-0.5)
    add_run(p, f"[{i}] ", bold=True, size=Pt(8), color=ACCENT_DARK)
    add_run(p, ref, size=Pt(8), color=BODY)

# ============================================================
# APENDICES
# ============================================================
add_separator(doc)

# Apêndice A
p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=Pt(14), after=Pt(2))
para_shading(p, ACCENT_HEX)
add_run(p, "  APENDICE A  ", bold=True, size=Pt(10), color=WHITE)
add_heading(doc, "Schema do Perfil", 2)

schema = """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "names": {"type": "array", "items": {"type": "string"}},
    "dates": {"type": "array", "items": {"type": "string"}},
    "keywords": {"type": "array", "items": {"type": "string"}},
    "pets": {"type": "array", "items": {"type": "string"}},
    "companies": {"type": "array", "items": {"type": "string"}},
    "phones": {"type": "array", "items": {"type": "string"}},
    "emails": {"type": "array", "items": {"type": "string"}},
    "old_passwords": {"type": "array", "items": {"type": "string"}},
    "numbers": {"type": "array", "items": {"type": "string"}}
  }
}"""
p = add_para(doc, after=Pt(8))
para_shading(p, DARK_BG)
add_run(p, schema, code=True, size=Pt(8), color=NEAR_WHITE)

# Apêndice B
p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=Pt(14), after=Pt(2))
para_shading(p, ACCENT_HEX)
add_run(p, "  APENDICE B  ", bold=True, size=Pt(10), color=WHITE)
add_heading(doc, "Metodologia Consolidada", 2)

methodology = [
    "5 perfis sintéticos com padrões brasileiros (87 senhas ground-truth).",
    "10 personas WLF (P01_minimal a P10_complete) com complexidade crescente de PII disponível.",
    "13.487 credenciais reais de compilações públicas (SecLists, IntelX), com 73,3% de domínios globais.",
    "Escala GPU: corpus 1M em NVIDIA RTX 4060 com 500 e 2.000 alvos.",
    "10 ferramentas externas: CUPP original (github.com/Mebus/cupp), CUPP-WLF, BopScrk (github.com/R3nt0n/bopscrk), "
    "ElpScrk (github.com/D4Vinci/elpscrk), PsudoHash (github.com/t3l3machus/psudohash), "
    "LongTongue (github.com/edoardottt/longtongue), Pydictor SEDB (github.com/LandGrey/pydictor), "
    "PassPwn, CrackSmith (interno WLF) e WLF combinado.",
    "Hit rate = |gerados interseção ground_truth| / |ground_truth|. CS = case-sensitive; CI = case-insensitive.",
    "Métricas: CS, CI, hits exclusivos, rank médiano, MRR, hit@K (K em {10, 100, 1000}).",
    "Ablação: cada camada desabilitada individualmente para medir contribuição marginal.",
    "Comparação pre/pos CogPIE no WLF: mesmas personas e corpus, antes e depois da integração.",
]
for i, item in enumerate(methodology, 1):
    add_numbered(doc, str(i), "", item)

# Apêndice C
p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=Pt(14), after=Pt(2))
para_shading(p, ACCENT_HEX)
add_run(p, "  APENDICE C  ", bold=True, size=Pt(10), color=WHITE)
add_heading(doc, "Resumo de Viéses Cognitivos", 2)

add_table(doc,
    ["Viés", "Efeito", "Prevalência", "Camada", "Referência"],
    [
        ["Ancoragem", "Palavra-base reconhecível", ">90%", "L1, L2", "Abdrabou 2021"],
        ["Posição Serial", "Modificações no início/fim", ">85%", "L2", "Li 2017"],
        ["Familiaridade", "Tokens pessoais significativos", ">70%", "L1", "Wang 2016"],
        ["Esforço Mínimo", "Menor alteração possível", ">60%", "L2, L5", "Ur 2015"],
        ["Status Quo", "Reutilização com pequenas modificações", "~76%", "L1", "arXiv:2607.19586"],
        ["Desconto Hiperbolico", "Memorabilidade > segurança", "~76%", "Todas", "arXiv:2607.19586"],
        ["Disponibilidade", "Informação recente/saliente", "~40%", "L1", "Veras 2014"],
        ["Superestimação de Força", "Usuario julga senha mais forte", "~65%", "L4", "Ur 2016"],
    ])

# Rodapé
add_separator(doc)
p = add_para(doc, align=WD_ALIGN_PARAGRAPH.CENTER, before=Pt(8), after=Pt(4))
para_shading(p, DARK_BG)
add_run(p, "Esta pesquisa foi conduzida para testes de segurança autorizados e propósitos acadêmicos. "
           "Benchmarks sintéticos utilizaram dados exclusivamente sintéticos. Validação com credenciais reais empregou "
           "compilações públicas (SecLists, IntelX) com métricas agregadas, conforme protocolo ético de Das et al. (2014). "
           "Os autores defendem gerenciadores de senhas, geração criptograficamente aleatória e autenticação sem senha "
           "como defesas primárias.",
        size=Pt(7), color=NEAR_WHITE, italic=True)

doc.save(str(DST))
print(f"DOCX v3 salvo: {DST}")
print(f"Tamanho: {DST.stat().st_size / 1024:.1f} KB")
