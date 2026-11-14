#!/usr/bin/env python3
"""
Generate a plain-language PDF about C's memory model and its flaws.
Pure ReportLab: text + vector diagrams, no external assets.
"""
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, Flowable,
)

# ---------------------------------------------------------------------------
# Palette
# ---------------------------------------------------------------------------
INK      = HexColor("#1f2430")
MUTED    = HexColor("#5b6472")
LINE     = HexColor("#c9d1dc")
WHITE    = HexColor("#ffffff")
LIGHT    = HexColor("#f1f5f9")
ACCENT   = HexColor("#2457a6")
ACCENT_L = HexColor("#dbe7f7")
GREEN    = HexColor("#2f7d4f")
GREEN_L  = HexColor("#dcefe4")
ORANGE   = HexColor("#b45309")
ORANGE_L = HexColor("#fbe9d2")
RED      = HexColor("#b23b3b")
RED_L    = HexColor("#f8dcdc")
CODE_BG  = HexColor("#f4f6f9")

# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = A4
MARGIN_L = MARGIN_R = 22 * mm
MARGIN_T = 22 * mm
MARGIN_B = 20 * mm
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# ---------------------------------------------------------------------------
# Drawing helpers
# ---------------------------------------------------------------------------
def ctext(c, cx, cy, lines, font="Helvetica", size=8.5, color=INK, leading=None):
    if isinstance(lines, str):
        lines = lines.split("\n")
    leading = leading or size * 1.25
    total = (len(lines) - 1) * leading
    c.setFillColor(color)
    c.setFont(font, size)
    base = cy - size * 0.35 + total / 2
    for i, ln in enumerate(lines):
        c.drawCentredString(cx, base - i * leading, ln)


def box(c, x, y, w, h, fill, stroke, text=None, font="Helvetica",
        size=8.5, tcolor=INK, radius=4, lw=0.9, dash=None):
    c.saveState()
    if dash:
        c.setDash(*dash)
    c.setFillColor(fill)
    c.setStrokeColor(stroke)
    c.setLineWidth(lw)
    c.roundRect(x, y, w, h, radius, stroke=1, fill=1)
    c.restoreState()
    if text:
        ctext(c, x + w / 2, y + h / 2, text, font, size, tcolor)


def arrow(c, x1, y1, x2, y2, color=ACCENT, lw=1.1, head=5):
    c.setStrokeColor(color)
    c.setFillColor(color)
    c.setLineWidth(lw)
    c.line(x1, y1, x2, y2)
    ang = math.atan2(y2 - y1, x2 - x1)
    for s in (1, -1):
        c.line(x2, y2,
               x2 - head * math.cos(ang - s * 0.5),
               y2 - head * math.sin(ang - s * 0.5))


def darrow(c, x1, y1, x2, y2, color=MUTED, lw=0.9, head=3):
    arrow(c, x1, y1, x2, y2, color, lw, head)
    arrow(c, x2, y2, x1, y1, color, lw, head)


class Fig(Flowable):
    def __init__(self, w, h, fn):
        super().__init__()
        self.width = w
        self.height = h
        self.fn = fn

    def wrap(self, aw, ah):
        return (self.width, self.height)

    def draw(self):
        self.fn(self.canv)


class CodeBlock(Flowable):
    def __init__(self, text, size=8.4, leading=12.4, pad=8):
        super().__init__()
        self.text = text
        self.size = size
        self.leading = leading
        self.pad = pad
        self.width = CONTENT_W
        self.height = 2 * pad + len(text.split("\n")) * leading

    def wrap(self, aw, ah):
        self.width = aw
        return (aw, self.height)

    def draw(self):
        c = self.canv
        c.setFillColor(CODE_BG)
        c.setStrokeColor(LINE)
        c.setLineWidth(0.7)
        c.roundRect(0, 0, self.width, self.height, 3, stroke=1, fill=1)
        c.setFillColor(INK)
        c.setFont("Courier", self.size)
        y = self.height - self.pad - self.size * 0.9
        for ln in self.text.split("\n"):
            c.drawString(self.pad + 2, y, ln)
            y -= self.leading


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------
style_body = ParagraphStyle(
    "body", fontName="Helvetica", fontSize=10.1, leading=15.2,
    textColor=INK, spaceAfter=5.5, alignment=TA_LEFT)
style_lead = ParagraphStyle(
    "lead", parent=style_body, fontSize=11.2, leading=17.2,
    textColor=HexColor("#2b3342"), spaceAfter=8)
style_h1 = ParagraphStyle(
    "h1", fontName="Helvetica-Bold", fontSize=15.5, leading=20,
    textColor=INK, spaceBefore=15, spaceAfter=7, keepWithNext=1)
style_h2mini = ParagraphStyle(
    "h2mini", fontName="Helvetica-Bold", fontSize=9, leading=12,
    textColor=MUTED, spaceBefore=4, spaceAfter=2, keepWithNext=1)
style_bullet = ParagraphStyle(
    "bullet", parent=style_body, leftIndent=15, bulletIndent=3,
    spaceAfter=3.2, bulletFontName="Helvetica", bulletFontSize=9,
    bulletColor=ACCENT)
style_cap = ParagraphStyle(
    "cap", fontName="Helvetica-Oblique", fontSize=8.2, leading=11,
    textColor=MUTED, alignment=1, spaceBefore=3, spaceAfter=7)
style_callout = ParagraphStyle(
    "callout", parent=style_body, fontSize=9.7, leading=14.6, spaceAfter=0)
style_th = ParagraphStyle(
    "th", fontName="Helvetica-Bold", fontSize=8.6, leading=11, textColor=WHITE)
style_td = ParagraphStyle(
    "td", fontName="Helvetica", fontSize=8.6, leading=11.6, textColor=INK)
style_toc = ParagraphStyle(
    "toc", fontName="Helvetica", fontSize=9.6, leading=16.5, textColor=INK)


# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
def on_page(canv, doc):
    canv.saveState()
    if doc.page > 1:
        canv.setStrokeColor(ACCENT)
        canv.setLineWidth(1.3)
        canv.line(MARGIN_L, PAGE_H - MARGIN_T + 13,
                  PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 13)
        canv.setFillColor(MUTED)
        canv.setFont("Helvetica", 7.4)
        canv.drawString(MARGIN_L, PAGE_H - MARGIN_T + 18, "C MEMORY MODEL")
        canv.drawRightString(PAGE_W - MARGIN_R, PAGE_H - MARGIN_T + 18,
                             "a plain-language guide")
    canv.setStrokeColor(LINE)
    canv.setLineWidth(0.6)
    canv.line(MARGIN_L, 15 * mm, PAGE_W - MARGIN_R, 15 * mm)
    canv.setFillColor(MUTED)
    canv.setFont("Helvetica", 8)
    canv.drawString(MARGIN_L, 11 * mm, "How C Manages Memory")
    canv.drawRightString(PAGE_W - MARGIN_R, 11 * mm, str(doc.page))
    canv.restoreState()


def make_doc(path):
    doc = BaseDocTemplate(
        path, pagesize=A4,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        title="How C Manages Memory",
        author="Research notes",
        subject="C's memory model: how it works and how it fails",
    )
    frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W,
                  PAGE_H - MARGIN_T - MARGIN_B, id="main",
                  leftPadding=0, rightPadding=0,
                  topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])
    return doc


def figure(fn, h, caption):
    return KeepTogether([
        Fig(CONTENT_W, h, fn),
        Spacer(1, 3),
        Paragraph(caption, style_cap),
    ])


def callout(text, color=ACCENT, bg=ACCENT_L):
    t = Table([[Paragraph(text, style_callout)]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ("LEFTPADDING", (0, 0), (-1, -1), 14),
        ("RIGHTPADDING", (0, 0), (-1, -1), 14),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    return t


def data_table(header, rows, fracs):
    widths = [f * CONTENT_W for f in fracs]
    data = [[Paragraph(h, style_th) for h in header]]
    for r in rows:
        data.append([Paragraph(x, style_td) for x in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def h1(num, title):
    return Paragraph(
        '<font color="#2457a6">%s</font>&nbsp;&nbsp;%s' % (num, title), style_h1)

# ---------------------------------------------------------------------------
# Diagrams
# ---------------------------------------------------------------------------
def fig_flat(c):
    n, cellw, x0, y0, hh = 14, CONTENT_W / 14, 0, 42, 38
    for i in range(n):
        fill = ACCENT_L if i == 5 else (LIGHT if i % 2 == 0 else WHITE)
        c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(0.7)
        c.rect(x0 + i * cellw, y0, cellw, hh, stroke=1, fill=1)
        c.setFillColor(MUTED); c.setFont("Courier", 6.2)
        c.drawCentredString(x0 + i * cellw + cellw / 2, y0 - 10, "0x%02x" % i)
    c.setFillColor(ACCENT); c.setFont("Courier-Bold", 10)
    c.drawCentredString(x0 + 5.5 * cellw, y0 + 16, "0x41")
    c.setFillColor(MUTED); c.setFont("Courier", 6.0)
    c.drawCentredString(x0 + 5.5 * cellw, y0 + 6, "byte")
    arrow(c, x0 + 5.5 * cellw, y0 + hh + 3, x0 + 5.5 * cellw, y0 + hh + 24, ACCENT, 1.0, 5)
    c.setFillColor(ACCENT); c.setFont("Helvetica-Bold", 8.2)
    c.drawCentredString(x0 + 5.5 * cellw, y0 + hh + 29, "each cell is one byte")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.5)
    c.drawString(0, y0 - 24, "address increases  ->")


def fig_address_space(c):
    bar_x, bar_w, y = 62, 122, 14
    regions = [
        ("Text", "machine code", 34, INK, WHITE),
        ("Data", "initialized globals", 34, ACCENT, WHITE),
        ("BSS", "zeroed globals", 26, HexColor("#4f7fbf"), WHITE),
        ("Heap", "malloc / free", 50, GREEN, WHITE),
        ("", "free space", 34, LIGHT, MUTED),
        ("Stack", "locals, calls", 52, ORANGE, WHITE),
    ]
    for name, desc, hh, fill, tcol in regions:
        c.setFillColor(fill); c.setStrokeColor(WHITE); c.setLineWidth(1.2)
        c.rect(bar_x, y, bar_w, hh, stroke=1, fill=1)
        if name:
            c.setFillColor(tcol); c.setFont("Helvetica-Bold", 9)
            c.drawCentredString(bar_x + bar_w / 2, y + hh / 2 - 3, name)
        lx = bar_x + bar_w + 14
        c.setFillColor(INK); c.setFont("Helvetica-Bold", 8.4)
        c.drawString(lx, y + hh / 2 + 1, name if name else "free space")
        c.setFillColor(MUTED); c.setFont("Helvetica", 7.4)
        c.drawString(lx, y + hh / 2 - 9, desc)
        if name == "Heap":
            arrow(c, bar_x + bar_w - 15, y + 8, bar_x + bar_w - 15, y + hh - 7, WHITE, 1.0, 4)
        if name == "Stack":
            arrow(c, bar_x + bar_w - 15, y + hh - 7, bar_x + bar_w - 15, y + 8, WHITE, 1.0, 4)
        y += hh
    ax = bar_x - 20
    c.setStrokeColor(MUTED); c.setLineWidth(0.8)
    c.line(ax, 14, ax, 244)
    arrow(c, ax, 220, ax, 246, MUTED, 0.8, 3)
    c.setFillColor(MUTED); c.setFont("Helvetica", 6.8)
    c.drawRightString(ax - 4, 238, "high")
    c.drawRightString(ax - 4, 15, "low")


def fig_stack(c):
    x, w = 96, 232
    bar_y, bar_h = 22, 72
    foo_y, foo_h = 102, 66
    main_y, main_h = 176, 66
    for fy, fh, fill in [(main_y, main_h, LIGHT), (foo_y, foo_h, ACCENT_L), (bar_y, bar_h, ORANGE_L)]:
        c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.rect(x, fy, w, fh, stroke=1, fill=1)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 10, main_y + main_h - 15, "main()")
    c.drawString(x + 10, foo_y + foo_h - 15, "foo()")
    slots = [("locals", bar_y, 18), ("saved rbp", bar_y + 18, 18),
             ("return address", bar_y + 36, 18), ("arguments", bar_y + 54, 18)]
    for label, sy, sh in slots:
        c.setStrokeColor(LINE); c.setLineWidth(0.6)
        c.line(x, sy + sh, x + w, sy + sh)
        c.setFillColor(INK); c.setFont("Courier", 7.8)
        c.drawString(x + 58, sy + 6, label)
    c.setFillColor(INK); c.setFont("Helvetica-Bold", 8.4)
    c.drawString(x + w + 12, main_y + main_h / 2 - 3, "main()")
    c.drawString(x + w + 12, foo_y + foo_h / 2 - 3, "foo()")
    c.setFillColor(ORANGE); c.setFont("Helvetica-Bold", 8.4)
    c.drawString(x + w + 12, bar_y + bar_h / 2 - 3, "bar()  <- current")
    arrow(c, x + 42, 3, x + 42, bar_y - 1, ACCENT, 1.1, 5)
    c.setFillColor(ACCENT); c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 50, 5, "SP")
    darrow(c, x - 24, 240, x - 24, 24, MUTED, 0.9, 3)
    c.saveState(); c.translate(x - 33, 132); c.rotate(90)
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.4)
    c.drawCentredString(0, 0, "stack grows down")
    c.restoreState()


def fig_heap(c):
    x0, y, hh = 30, 58, 44
    segs = [("size", 60, HexColor("#dfe6ee"), INK),
            ("flags", 50, HexColor("#cfdae7"), INK),
            ("payload  (n bytes)", 250, GREEN_L, GREEN)]
    xx = x0
    for name, w_, fill, tc in segs:
        c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.rect(xx, y, w_, hh, stroke=1, fill=1)
        c.setFillColor(tc); c.setFont("Helvetica-Bold", 8.4)
        c.drawCentredString(xx + w_ / 2, y + hh / 2 - 3, name)
        xx += w_
    c.setStrokeColor(MUTED); c.setLineWidth(0.8)
    c.line(x0, y + hh + 6, x0, y + hh + 11); c.line(x0, y + hh + 11, x0 + 110, y + hh + 11)
    c.line(x0 + 110, y + hh + 6, x0 + 110, y + hh + 11)
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.6)
    c.drawCentredString(x0 + 55, y + hh + 15, "allocator header (hidden)")
    c.line(x0 + 110, y + hh + 11, x0 + 360, y + hh + 11)
    c.line(x0 + 360, y + hh + 6, x0 + 360, y + hh + 11)
    c.setFillColor(GREEN); c.setFont("Helvetica-Bold", 7.6)
    c.drawCentredString(x0 + 235, y + hh + 15, "what p points to")
    arrow(c, x0 + 118, 14, x0 + 118, y - 1, ACCENT, 1.1, 5)
    c.setFillColor(ACCENT); c.setFont("Courier-Bold", 9)
    c.drawString(x0 + 126, 17, "p = malloc(n)")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.2)
    c.drawString(x0 + 126, 6, "points just past the header")


def fig_ptr_arith(c):
    x0, y, hh, cw = 18, 52, 40, 64
    for i in range(5):
        x = x0 + i * cw
        c.setFillColor(LIGHT if i % 2 == 0 else WHITE); c.setStrokeColor(LINE); c.setLineWidth(1)
        c.rect(x, y, cw, hh, stroke=1, fill=1)
        ctext(c, x + cw / 2, y + hh / 2, "a[%d]" % i, "Helvetica", 8, INK)
        c.setFillColor(MUTED); c.setFont("Courier", 7)
        c.drawCentredString(x + cw / 2, y - 11, str(i * 4))
    xp = x0 + 5 * cw
    c.saveState(); c.setDash(3, 2); c.setStrokeColor(MUTED); c.setLineWidth(0.9)
    c.rect(xp, y, cw, hh, stroke=1, fill=0); c.restoreState()
    ctext(c, xp + cw / 2, y + hh / 2, ["one past", "end"], "Helvetica", 7.4, MUTED)
    c.setFillColor(MUTED); c.setFont("Courier", 7)
    c.drawCentredString(xp + cw / 2, y - 11, "20")
    c.setFont("Helvetica", 7.0)
    c.drawCentredString(xp + cw / 2, y - 24, "(may not dereference)")
    arrow(c, x0 + cw * 0.25, 16, x0 + cw * 0.25, y - 1, ACCENT, 1.1, 5)
    c.setFillColor(ACCENT); c.setFont("Courier-Bold", 8.5)
    c.drawString(x0 + cw * 0.25 + 5, 17, "p")
    arrow(c, x0 + cw * 2.25, 16, x0 + cw * 2.25, y - 1, ORANGE, 1.1, 5)
    c.setFillColor(ORANGE); c.setFont("Courier-Bold", 8.5)
    c.drawString(x0 + cw * 2.25 + 5, 17, "p+2")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.4)
    c.drawString(x0, y + hh + 14, "byte offsets:  p+2 = p + 2 x sizeof(int) = p + 8")


def fig_aliasing(c):
    cx, cw, ch, cy = 185, 130, 46, 8
    box(c, cx, cy, cw, ch, ORANGE_L, ORANGE, "int x = 42", "Courier-Bold", 10, INK)
    box(c, 20, cy + 2, 110, 44, LIGHT, LINE, "int *p", "Courier-Bold", 9.5, INK)
    box(c, 360, cy + 2, 110, 44, LIGHT, LINE, "int *q", "Courier-Bold", 9.5, INK)
    arrow(c, 132, cy + 24, cx - 2, cy + 24, ACCENT, 1.2, 6)
    arrow(c, 358, cy + 24, cx + cw + 2, cy + 24, ACCENT, 1.2, 6)
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.6)
    c.drawCentredString(cx + cw / 2, cy + ch + 10, "both pointers refer to the same bytes")


def fig_ub(c):
    y, hh, w, gap = 24, 54, 138, 28
    xs = [0, w + gap, 2 * (w + gap)]
    labels = [("Your C source", LIGHT, LINE, INK),
              ("Compiler assumes:\nno undefined behavior", ACCENT_L, ACCENT, INK),
              ("Anything\nis allowed", RED_L, RED, RED)]
    for x, (t, fill, st, tc) in zip(xs, labels):
        box(c, x, y, w, hh, fill, st, t, "Helvetica-Bold", 9, tc)
    for i in range(2):
        arrow(c, xs[i] + w + 4, y + hh / 2, xs[i + 1] - 4, y + hh / 2, MUTED, 1.2, 6)


def fig_uaf(c):
    y, hh, w, gap = 12, 56, 100, 20
    stages = [("malloc()\np is valid", LIGHT, LINE, INK),
              ("use *p\nOK", GREEN_L, GREEN, GREEN),
              ("free(p)\nreleased", LIGHT, LINE, INK),
              ("use *p\nBUG", RED_L, RED, RED)]
    xs = [0, w + gap, 2 * (w + gap), 3 * (w + gap)]
    for x, (t, fill, st, tc) in zip(xs, stages):
        box(c, x, y, w, hh, fill, st, t, "Helvetica-Bold", 8.6, tc)
    for i in range(3):
        arrow(c, xs[i] + w + 3, y + hh / 2, xs[i + 1] - 3, y + hh / 2, MUTED, 1.1, 5)


def fig_race(c):
    box(c, 20, 64, 130, 38, LIGHT, LINE, "Thread 1", "Helvetica-Bold", 9, INK)
    box(c, 20, 14, 130, 38, LIGHT, LINE, "Thread 2", "Helvetica-Bold", 9, INK)
    box(c, 290, 33, 150, 50, RED_L, RED, "int counter", "Courier-Bold", 10, INK)
    arrow(c, 155, 83, 285, 63, RED, 1.3, 6)
    arrow(c, 155, 33, 285, 53, RED, 1.3, 6)
    c.setFillColor(RED); c.setFont("Helvetica", 7.6)
    c.drawString(198, 87, "write")
    c.drawString(198, 21, "write")


def fig_overflow(c):
    x0, y, hh, cw = 16, 58, 44, 66
    for i in range(4):
        x = x0 + i * cw
        box(c, x, y, cw, hh, LIGHT if i % 2 == 0 else WHITE, LINE,
            "a[%d]" % i, "Helvetica", 8, INK, radius=2)
    xb = x0 + 4 * cw + 18
    box(c, xb, y, 165, hh, ORANGE_L, ORANGE,
        "other data\n(next variable)", "Helvetica-Bold", 8.2, INK, radius=2)
    c.saveState(); c.setDash(3, 2); c.setStrokeColor(RED); c.setLineWidth(1.4)
    c.line(x0 + 4 * cw, y - 6, x0 + 4 * cw, y + hh + 6); c.restoreState()
    arrow(c, xb + 30, y - 28, xb + 30, y - 2, RED, 1.4, 6)
    c.setFillColor(RED); c.setFont("Helvetica-Bold", 8)
    c.drawString(xb + 40, y - 30, "write a[4]  ->  out of bounds")
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.6)
    c.drawString(x0, y + hh + 12, "four-element array")


def fig_frag(c):
    x0, y, hh = 16, 36, 40
    segs = [("used", 90, GREEN_L, GREEN), ("free", 50, LIGHT, MUTED),
            ("used", 60, GREEN_L, GREEN), ("free", 90, LIGHT, MUTED),
            ("used", 40, GREEN_L, GREEN), ("free", 100, LIGHT, MUTED)]
    xx = x0
    for name, w_, fill, tc in segs:
        c.saveState()
        c.setFillColor(fill); c.setStrokeColor(LINE); c.setLineWidth(1)
        if name == "free":
            c.setDash(3, 2)
        c.rect(xx, y, w_, hh, stroke=1, fill=1)
        c.restoreState()
        c.setFillColor(tc); c.setFont("Helvetica", 7.8)
        c.drawCentredString(xx + w_ / 2, y + hh / 2 - 3, name)
        xx += w_
    c.setFillColor(MUTED); c.setFont("Helvetica", 7.8)
    c.drawString(x0, y + hh + 12, "heap after many alloc / free cycles")
    c.setFillColor(RED); c.setFont("Helvetica-Bold", 8)
    c.drawString(x0, y - 18, "largest free block is 100 units; a request for 300 units fails")


# ---------------------------------------------------------------------------
# Content
# ---------------------------------------------------------------------------
def code(s):
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return '<font name="Courier" size="8.8">%s</font>' % s


def P(text, style=style_body):
    return Paragraph(text, style)


def bullet(text):
    return Paragraph(text, style_bullet, bulletText="\u2022")


def build_story():
    story = []

    # ---- Title block ------------------------------------------------------
    st_kicker = ParagraphStyle("kicker", fontName="Helvetica-Bold", fontSize=8,
                               leading=10, textColor=HexColor("#b9cdec"))
    st_title = ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=25,
                              leading=30, textColor=WHITE)
    st_sub = ParagraphStyle("sub", fontName="Helvetica", fontSize=11,
                            leading=15.5, textColor=HexColor("#e6eefb"))
    title_rows = [
        [Paragraph("SYSTEMS PROGRAMMING   \u00b7   MEMORY MODEL", st_kicker)],
        [Spacer(1, 8)],
        [Paragraph("How C Manages Memory", st_title)],
        [Spacer(1, 6)],
        [Paragraph("A plain-language guide to C's memory model, and the flaws "
                   "that come with it.", st_sub)],
        [Spacer(1, 10)],
        [Paragraph("PART 1   \u00b7   FOUNDATIONS", st_kicker)],
    ]
    title = Table(title_rows, colWidths=[CONTENT_W])
    title.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(Spacer(1, 6))
    story.append(title)
    story.append(Spacer(1, 18))

    story.append(P(
        "C gives you one of the simplest possible pictures of a computer's "
        "memory: a long row of bytes, and pointers that are just numbers "
        "pointing into that row. That simplicity is why C is fast, small, and "
        "still the language of operating systems, drivers, and embedded "
        "devices. It is also why C programs are famous for memory bugs that "
        "are silent, random, and sometimes dangerous. This guide explains how "
        "C's memory model works, then walks through the flaws one by one, in "
        "plain language and with pictures.", style_lead))

    story.append(Spacer(1, 10))
    story.append(P("WHAT IS INSIDE", style_h2mini))
    story.append(Spacer(1, 5))

    items = [
        ("01", "The one big idea"),
        ("02", "Where things live"),
        ("03", "Three lifetimes"),
        ("04", "The stack"),
        ("05", "The heap"),
        ("06", "Pointers"),
        ("07", "Aliasing"),
        ("08", "Undefined behavior"),
        ("09", "The catalog of flaws"),
        ("10", "Why C is built this way"),
        ("11", "What people do about it"),
        ("12", "Summary"),
    ]
    toc_rows = []
    for i in range(6):
        row = []
        for n, t in (items[i], items[i + 6]):
            row.append(Paragraph(
                '<font color="#2457a6"><b>%s</b></font>&nbsp;&nbsp;%s' % (n, t),
                style_toc))
        toc_rows.append(row)
    toc = Table(toc_rows, colWidths=[CONTENT_W / 2, CONTENT_W / 2])
    toc.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(toc)
    story.append(PageBreak())

    # ---- 1 ----------------------------------------------------------------
    story.append(h1("01", "The one big idea"))
    story.append(P(
        "C's memory model starts with a single idea: <b>memory is one long "
        "array of bytes.</b> Every byte has an address, and addresses are just "
        "integers. A variable is a name for some bytes. An array is a row of "
        "bytes. A struct is bytes arranged in a particular order. A pointer is "
        "a number that names an address."))
    story.append(P(
        "That is the whole model. There is no hidden object table, no garbage "
        "collector, no per-object metadata that the language tracks. A pointer "
        "does not know how big the thing it points to is, or whether that thing "
        "is still alive. It is just a number."))
    story.append(P(
        "This is the source of both C's power and its danger. Because a pointer "
        "is just a number, C can talk to hardware registers, memory-mapped "
        "devices, and memory shared with other languages. Because a pointer is "
        "just a number, it can also point at garbage."))
    story.append(figure(
        fig_flat, 122,
        "Figure 1. C's model of memory. A pointer is just an index into a flat "
        "array of bytes."))
    story.append(callout(
        "<b>The rule that is not enforced.</b> C says a pointer may only point "
        "inside a live object. Nothing in the language or the machine checks "
        "that. The rule is a convention between you and the compiler."))
    story.append(P(
        "One important detail: the C standard describes an <b>abstract "
        "machine</b>, not your actual CPU. The compiler can keep variables in "
        "registers, reorder operations, and delete code, as long as the "
        "observable behavior of a correct program stays the same. When your "
        "program breaks the rules, the compiler is allowed to assume it did "
        "not. That is where undefined behavior comes from, and we return to it "
        "in Section 8."))

    # ---- 2 ----------------------------------------------------------------
    story.append(h1("02", "Where things live"))
    story.append(P(
        "In practice, a running C program's address space is split into a few "
        "regions. The picture below is the conventional layout on Linux, "
        "Windows and macOS. The C standard does not require it, and embedded "
        "systems often look different, but the idea is the same everywhere."))
    story.append(bullet(
        "<b>Text</b> \u2014 the machine code of your program. Usually read-only."))
    story.append(bullet(
        "<b>Data</b> \u2014 global and static variables that you initialized "
        "with a value."))
    story.append(bullet(
        "<b>BSS</b> \u2014 global and static variables that start at zero."))
    story.append(bullet(
        "<b>Heap</b> \u2014 memory you request at run time with "
        + code("malloc") + ". It grows upward."))
    story.append(bullet(
        "<b>Stack</b> \u2014 memory for function calls and local variables. It "
        "grows downward, toward the heap."))
    story.append(P(
        "The empty space between the heap and the stack is free memory. The "
        "heap grows up into it as you allocate, and the stack grows down into "
        "it as you call deeper. If they meet, you are out of memory, or more "
        "likely you have recursed too far."))
    story.append(figure(
        fig_address_space, 258,
        "Figure 2. The conventional address space. The heap grows up, the "
        "stack grows down, and the gap between them is free memory."))

    # ---- 3 ----------------------------------------------------------------
    story.append(h1("03", "Three lifetimes"))
    story.append(P(
        "C groups memory by how long it lives. Three cases cover almost all "
        "code, and they answer the question \u201chow long does this memory "
        "live?\u201d"))
    story.append(Spacer(1, 2))
    story.append(data_table(
        ["Duration", "Where", "Created", "Destroyed", "Typical use"],
        [
            ["Automatic", "stack", "function is entered", "function returns",
             "local variables"],
            ["Static", "data / BSS", "program starts", "program exits",
             "globals and " + code("static") + " locals"],
            ["Dynamic", "heap", code("malloc()"), code("free()"),
             "anything you allocate"],
        ],
        [0.16, 0.14, 0.22, 0.20, 0.28]))
    story.append(Spacer(1, 8))
    story.append(P(
        "(The C standard also defines <b>thread</b> storage duration, which "
        "behaves like static storage but gives each thread its own copy, and "
        "it calls heap memory <b>allocated</b> storage. We ignore those "
        "details here.)"))
    story.append(P(
        "Automatic memory is the easiest: the compiler manages it, and it costs "
        "almost nothing. Static memory is nearly as easy: it exists for the "
        "whole run. Dynamic memory is the hard one, because <b>you</b> are the "
        "manager. Every " + code("malloc") + " needs a matching " + code("free")
        + ", at the right time, exactly once. Getting that right in a large "
        "program is genuinely difficult, and that is where most C memory bugs "
        "come from."))

    # ---- 4 ----------------------------------------------------------------
    story.append(h1("04", "The stack"))
    story.append(P(
        "Every time you call a function, the CPU pushes a <b>stack frame</b>. "
        "The frame holds the arguments, the return address (where to jump back "
        "to), saved registers, and the function's local variables. When the "
        "function returns, the frame is popped and the stack pointer moves "
        "back."))
    story.append(P(
        "The stack is fast because it is just a pointer bump: allocate by "
        "subtracting, free by adding. It is also safe in one specific sense: "
        "you cannot leak stack memory, because it is reclaimed automatically on "
        "return. But the stack has sharp edges:"))
    story.append(bullet(
        "<b>No bounds checks.</b> A local array can be written past its end, "
        "quietly overwriting the return address or a neighbor."))
    story.append(bullet(
        "<b>Stack overflow.</b> Deep recursion or a huge local array runs off "
        "the end of the stack and crashes, or worse, on systems without a "
        "guard page."))
    story.append(bullet(
        "<b>Dangling pointers to locals.</b> If you return a pointer to a local "
        "variable, the frame disappears when the function returns. The pointer "
        "still holds the old address, which the next call will soon reuse."))
    story.append(figure(
        fig_stack, 260,
        "Figure 3. Stack frames. Each call pushes a new frame; returning pops "
        "it. The current function's frame is at the lowest address."))

    # ---- 5 ----------------------------------------------------------------
    story.append(h1("05", "The heap"))
    story.append(P(
        "The heap is a large pool of memory that the program manages itself. "
        + code("malloc(n)") + " asks the allocator for at least <i>n</i> bytes "
        "and returns a pointer. " + code("free(p)") + " gives the block back."))
    story.append(P(
        "Behind the scenes, the allocator keeps <b>metadata</b>, usually a "
        "small header just before the pointer it returns, recording the block's "
        "size and whether it is free. It also keeps a <b>free list</b> of "
        "available blocks so it can reuse them. When you call " + code("free")
        + ", the block goes back on that list, and a later " + code("malloc")
        + " may hand the same bytes to someone else."))
    story.append(P("This design is fast and flexible, but every part of it trusts the program:"))
    story.append(bullet(
        "<b>Memory leaks.</b> Forget to free, and the block stays reserved "
        "forever."))
    story.append(bullet(
        "<b>Use-after-free.</b> Keep using a pointer after free, and you are "
        "reading or writing memory that now belongs to someone else."))
    story.append(bullet(
        "<b>Double free.</b> Free the same pointer twice, and the allocator's "
        "free list gets corrupted."))
    story.append(bullet(
        "<b>Fragmentation.</b> After many alloc/free cycles, free memory is "
        "split into small scattered pieces, so a large request fails even "
        "though enough total memory exists."))
    story.append(bullet(
        "<b>Metadata corruption.</b> A buffer overflow can overwrite the hidden "
        "header in front of the next block. Attackers use this to make the "
        "allocator write to an address of their choosing."))
    story.append(figure(
        fig_heap, 132,
        "Figure 4. A heap block. The allocator stores hidden metadata just "
        "before the address it returns to you."))

    # ---- 6 ----------------------------------------------------------------
    story.append(h1("06", "Pointers: address plus type"))
    story.append(P(
        "A pointer has two things: an address and a type. The type matters for "
        "arithmetic. If " + code("p") + " is an " + code("int *") + ", then "
        + code("p + 1") + " moves forward by " + code("sizeof(int)")
        + " bytes, usually 4, not by one byte. The compiler multiplies for you."))
    story.append(figure(
        fig_ptr_arith, 140,
        "Figure 5. Pointer arithmetic moves in whole objects. A pointer may be "
        "formed one past the end, but not dereferenced there."))
    story.append(P(
        "Pointer arithmetic is only <i>defined</i> inside a single array "
        "object, plus one position past the end. You may form a pointer to "
        + code("a[5]") + " for an array of five elements and compare it, but "
        "you may not dereference it. You may not compute a pointer that jumps "
        "from one object into another, even if the addresses happen to be "
        "adjacent."))
    story.append(P(
        "Arrays are laid out contiguously: a[0], a[1], and so on, with no gaps. "
        "Structs are different. The compiler may insert invisible <b>padding</b> "
        "between fields so that each field starts at an address the hardware "
        "likes (its alignment). So " + code("sizeof(struct)") + " can be larger "
        "than the sum of its fields. This is harmless for correctness, but it "
        "surprises people who assume C lays out bytes exactly as written, and it "
        "matters when you write a struct to disk or send it over a network."))
    story.append(callout(
        "Here is the problem: <b>C does not track which object a pointer came "
        "from.</b> The rule exists in the standard, but nothing in the language "
        "or the machine enforces it. You can add a thousand to a pointer and "
        "dereference it. You can cast an integer to a pointer. The hardware "
        "will happily read whatever bytes are at that address. This is a "
        "<b>provenance</b> problem: a pointer's right to access an object is not "
        "represented anywhere.", color=ORANGE, bg=ORANGE_L))

    # ---- 7 ----------------------------------------------------------------
    story.append(h1("07", "Aliasing"))
    story.append(P(
        "Two pointers can point at the same object. This is called "
        "<b>aliasing</b>, and it is completely legal:"))
    story.append(CodeBlock(
        "int  x = 42;\n"
        "int *p = &x;\n"
        "int *q = &x;   /* p and q alias: two names for the same bytes */"))
    story.append(Spacer(1, 6))
    story.append(P(
        "Aliasing is useful. It lets functions take pointers to the same "
        "buffer, lets data structures share nodes, and lets you write code that "
        "works on \u201csome memory\u201d without copying it."))
    story.append(figure(
        fig_aliasing, 88,
        "Figure 6. Aliasing. Both pointers reach the same object. This is legal "
        "and often useful."))
    story.append(P(
        "But aliasing makes optimization harder. If the compiler sees "
        + code("*p = 1;") + " followed by " + code("x = *q;") + ", it must "
        "assume " + code("*q") + " might be the memory that " + code("*p")
        + " just wrote, so it has to reload. If it knew " + code("p") + " and "
        + code("q") + " never alias, it could keep " + code("x") + " in a "
        "register."))
    story.append(P(
        "C's answer is " + code("restrict") + ": a promise from the programmer "
        "that a pointer is the <i>only</i> way to reach its object for the "
        "lifetime of the pointer. The compiler may then optimize aggressively. "
        "If you break that promise, the behavior is undefined."))
    story.append(P(
        "C also has the <b>strict aliasing rule</b>: you generally may not "
        "access an object through a pointer of an unrelated type. Casting an "
        + code("int *") + " to a " + code("float *") + " and reading through it "
        "is undefined even though it compiles. This rule lets the compiler "
        "assume that integer stores and floating-point loads do not interfere. "
        "It is also a classic source of bugs in code that \u201cjust casts\u201d."))

    # ---- 8 ----------------------------------------------------------------
    story.append(h1("08", "Undefined behavior"))
    story.append(P(
        "This is the most important idea in the whole document. The C standard "
        "defines what a correct program does. For many mistakes it says the "
        "behavior is <b>undefined</b>, which does not mean \u201cit crashes\u201d "
        "or \u201cit does something random\u201d. It means <b>the standard "
        "imposes no requirements at all.</b>"))
    story.append(callout(
        "<b>Undefined behavior (UB) is not a crash. It is a license.</b> If the "
        "source contains UB, the compiler may assume it never happens, and it "
        "may use that assumption to transform the program.",
        color=RED, bg=RED_L))
    story.append(Spacer(1, 8))
    story.append(P(
        "The result can be code that appears to work in a debug build and "
        "breaks in an optimized build; code that works for years and then "
        "breaks when the compiler is upgraded; or code where a security check "
        "is deleted entirely because the compiler \u201cproved\u201d the check "
        "is unnecessary. Common triggers include:"))
    story.append(bullet("signed integer overflow"))
    story.append(bullet("out-of-bounds access"))
    story.append(bullet("dereferencing null or a dangling pointer"))
    story.append(bullet("reading an uninitialized variable"))
    story.append(bullet("violating strict aliasing"))
    story.append(bullet("a data race between two threads"))
    story.append(P(
        "None of these are required to produce a useful error. Many build with "
        "no warning and no crash."))
    story.append(figure(
        fig_ub, 88,
        "Figure 7. The compiler's contract. Undefined behavior lets the "
        "optimizer assume your mistake never happened."))
    story.append(P(
        "This is the core flaw of C's memory model: <b>the rules that keep you "
        "safe are not enforced, and breaking them does not reliably fail.</b>"))

    # ---- 9 ----------------------------------------------------------------
    story.append(h1("09", "The catalog of flaws"))
    story.append(P(
        "Here is the full set, grouped by the kind of rule each one breaks. "
        "Every item is a direct consequence of the model we have just "
        "described: bytes with addresses, pointers without provenance, and "
        "lifetimes managed by hand."))

    story.append(P("<b>Spatial errors: touching memory you do not own.</b>", style_body))
    story.append(bullet(
        "<b>Buffer overflow / out-of-bounds access.</b> Writing or reading "
        "past the end of an array or allocated block. The bytes there belong to "
        "something else: another variable, a return address, or allocator "
        "metadata."))
    story.append(bullet(
        "<b>Stack overflow.</b> Too much recursion, or local variables larger "
        "than the stack, run past the end of the stack region."))
    story.append(figure(
        fig_overflow, 132,
        "Figure 8. A buffer overflow. Writing a[4] on a four-element array "
        "lands in whatever happens to sit next to it."))

    story.append(P("<b>Temporal errors: using memory at the wrong time.</b>", style_body))
    story.append(bullet(
        "<b>Use-after-free.</b> The block was returned to the allocator, but a "
        "pointer still refers to it. The allocator may have given those bytes "
        "to another object, so the old pointer now reads or writes someone "
        "else's data."))
    story.append(bullet(
        "<b>Double free.</b> The same block is freed twice, which corrupts the "
        "allocator's free list and can crash the program or hand an attacker "
        "control of a future allocation."))
    story.append(bullet(
        "<b>Dangling stack pointer.</b> A function returns a pointer to one of "
        "its locals. The frame is gone, but the address remains, and the next "
        "call will reuse it."))
    story.append(figure(
        fig_uaf, 72,
        "Figure 9. Use-after-free. The allocator may already have handed these "
        "same bytes to another object."))

    story.append(P("<b>Type and initialization errors.</b>", style_body))
    story.append(bullet(
        "<b>Type confusion / strict aliasing.</b> The same bytes are read "
        "through a pointer of the wrong type. The compiler may reorder or "
        "eliminate accesses because it assumed the types could not overlap."))
    story.append(bullet(
        "<b>Uninitialized reads.</b> " + code("malloc") + " does not zero "
        "memory. Reading a value before writing it gives you whatever the "
        "previous owner left behind, which is both a wrong-value bug and an "
        "information leak."))

    story.append(P("<b>Concurrency errors.</b>", style_body))
    story.append(bullet(
        "<b>Data race.</b> Two threads touch the same memory, at least one "
        "writes, and there is no synchronization. In C this is undefined "
        "behavior, not merely \u201cunpredictable\u201d. The compiler is allowed "
        "to assume it never happens."))
    story.append(figure(
        fig_race, 120,
        "Figure 10. A data race. Two threads write the same object with no "
        "synchronization, so the result is undefined."))

    story.append(P("<b>Resource errors.</b>", style_body))
    story.append(bullet(
        "<b>Memory leak.</b> A block is allocated and never freed. The program "
        "keeps growing until the system runs out of memory."))
    story.append(bullet(
        "<b>Fragmentation.</b> Free memory exists, but in pieces too small to "
        "satisfy the next request. The program fails even though total free "
        "memory is sufficient."))
    story.append(figure(
        fig_frag, 100,
        "Figure 11. Fragmentation. The holes add up to enough memory, but none "
        "of them is large enough."))

    story.append(P("<b>Provenance and arithmetic errors.</b>", style_body))
    story.append(bullet(
        "<b>Forged or out-of-object pointer.</b> Casting an integer to a "
        "pointer, or doing arithmetic that leaves the object, produces a "
        "pointer the standard never allowed. The machine still dereferences "
        "it."))
    story.append(bullet(
        "<b>Integer overflow in a size calculation.</b> "
        + code("malloc(n * sizeof(int))") + " can wrap around to a tiny number "
        "when <i>n</i> is huge. The allocation succeeds, and the program then "
        "writes far past its end."))
    story.append(CodeBlock(
        "size_t n = get_count();\n"
        "int *a = malloc(n * sizeof(int));   /* n * 4 can overflow */\n"
        "a[0] = 1;                           /* small block, huge index   */"))

    # ---- 10 ---------------------------------------------------------------
    story.append(h1("10", "Why C is built this way"))
    story.append(P(
        "It is worth being fair to C. The design is not an accident; it is a "
        "deliberate trade, made in the early 1970s for machines with a few "
        "kilobytes of memory."))
    story.append(bullet(
        "<b>Trust the programmer.</b> C assumes you know what you are doing. "
        "Checks cost time, and in kernels and embedded systems that time "
        "matters."))
    story.append(bullet(
        "<b>No hidden runtime.</b> There is no garbage collector, no runtime "
        "that pauses your program, and no background thread moving objects. A "
        "C program does exactly what the machine instructions say."))
    story.append(bullet(
        "<b>Predictable performance.</b> Allocation is a function call, a local "
        "variable is a stack slot, and a field access is an offset. You can "
        "reason about the cost of each line."))
    story.append(bullet(
        "<b>Small and portable.</b> The language is small enough to implement "
        "on almost any chip, and close enough to the hardware to serve as a "
        "\u201cportable assembler\u201d."))
    story.append(bullet(
        "<b>Full control.</b> You choose the layout, the lifetime, and the "
        "aliasing. That is what lets C write operating systems, device drivers, "
        "language runtimes, and databases."))
    story.append(P(
        "The price is that <b>every mistake is yours, and many mistakes are "
        "silent.</b> C gives you the control of assembly with the type system "
        "of a spreadsheet. That trade was reasonable when programs were small. "
        "It is much harder to justify for the multi-million-line programs we "
        "write today."))

    # ---- 11 ---------------------------------------------------------------
    story.append(h1("11", "What people do about it"))
    story.append(P(
        "None of this means C cannot be used safely. It means safety has to "
        "come from somewhere else. The main approaches:"))
    story.append(bullet(
        "<b>Discipline and review.</b> Coding standards, small functions, clear "
        "ownership rules, careful review. Cheap, but does not scale and misses "
        "subtle bugs."))
    story.append(bullet(
        "<b>Static analysis.</b> Tools that read the code and look for "
        "out-of-bounds access, leaks, and null dereferences. Catches some bugs "
        "before they run, at the cost of false positives."))
    story.append(bullet(
        "<b>Sanitizers.</b> Compiler instrumentation that checks at run time. "
        "AddressSanitizer catches out-of-bounds and use-after-free, "
        "UndefinedBehaviorSanitizer catches many UB cases, MemorySanitizer "
        "catches uninitialized reads, and ThreadSanitizer catches data races. "
        "Excellent for testing, too slow for production."))
    story.append(bullet(
        "<b>Hardening.</b> Stack canaries, address-space randomization, "
        "non-executable memory, and hardened allocators. Makes exploitation "
        "harder, but does not remove the bugs."))
    story.append(bullet(
        "<b>Memory tagging and capabilities.</b> New hardware can attach a tag "
        "or a capability to each pointer and check it on every access. Arm's "
        "MTE and CHERI-style capabilities are the leading examples. Fil-C shows "
        "that a memory-safe C can also be built in software, at a runtime "
        "cost."))
    story.append(bullet(
        "<b>Other languages.</b> Rust enforces ownership and borrowing at "
        "compile time and prevents most of the flaws in this document, at the "
        "cost of giving up some of C's freedom. Go, Java and others use garbage "
        "collection, trading control for automatic lifetime management."))

    # ---- 12 ---------------------------------------------------------------
    story.append(PageBreak())
    story.append(h1("12", "Summary"))
    story.append(P(
        "One table, one page, every flaw in this guide. Each defense trades "
        "something: speed, memory, compatibility, or control. That trade-off "
        "is the subject of the next part of this research."))
    story.append(Spacer(1, 2))
    story.append(data_table(
        ["Flaw", "Root cause", "What goes wrong", "Typical defense"],
        [
            ["Buffer overflow", "no bounds checks", "overwrites neighbors",
             "bounds checks, ASan, MTE"],
            ["Use-after-free", "pointer outlives object", "touches reused memory",
             "ownership, GC, generations"],
            ["Double free", "block freed twice", "corrupts the free list",
             "null after free, hardened allocator"],
            ["Memory leak", "missing free", "memory grows forever",
             "review, leak checkers, RAII"],
            ["Dangling stack pointer", "returning a local address",
             "points at a reused frame", "return by value, escape analysis"],
            ["Uninitialized read", "malloc does not zero", "garbage value, info leak",
             "calloc, MSan, init tags"],
            ["Type confusion", "unchecked casts", "bytes read as wrong type",
             "careful casts, type tags"],
            ["Data race", "shared memory, no sync", "undefined behavior",
             "locks, atomics, TSan"],
            ["Fragmentation", "scattered free blocks", "large allocation fails",
             "pools, arenas, better allocator"],
            ["Size overflow", "unchecked arithmetic", "too-small allocation",
             "checked math, safe-int helpers"],
            ["Forged pointer", "a pointer is just a number", "arbitrary access",
             "capabilities, provenance, ASLR"],
        ],
        [0.235, 0.225, 0.275, 0.265]))
    story.append(Spacer(1, 12))
    story.append(callout(
        "C's memory model is beautifully simple: bytes, addresses, and "
        "lifetimes you manage yourself. That simplicity is the reason C is "
        "still everywhere. It is also the reason the same three bugs \u2014 "
        "overflow, use-after-free, and uninitialized memory \u2014 have been "
        "exploited for forty years. C does not have a memory-safety mechanism. "
        "It has a memory-safety <b>convention</b>, and the machine is under no "
        "obligation to enforce it. Understanding exactly where the convention "
        "ends is the first step toward designing something better."))

    return story


def main():
    out = "/root/projects/Project1/C_Memory_Architecture.pdf"
    doc = make_doc(out)
    doc.build(build_story())
    print("wrote", out)


if __name__ == "__main__":
    main()
