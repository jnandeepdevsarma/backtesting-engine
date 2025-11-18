# pdf_helpers.py
# Requires: reportlab, PyPDF2, pandas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from PyPDF2 import PdfReader
import math
import os

# --------- Helper: safe text for PDF (sanitization) ----------
def _safe_str(x):
    return "" if x is None else str(x)

# --------- Manual PDF with radio buttons (interactive-like) ----------
def manual_pdf_from_df(df, month, year, filename="01_Manual_Backtest_Sample_portfolio_safe.pdf"):
    """
    df must contain columns: Date, Area, Peak, Trend, AvgTrend (or avg_trend), Rally, Overview, Decision, SL, TG
    Produces a portfolio-safe interactive-like PDF with radio buttons for CE/PE and Target/SL.
    """
    # normalize column names
    col_map = {c.lower(): c for c in df.columns}
    # rename common variants
    rename_map = {}
    if "avg_trend" in col_map: rename_map[col_map["avg_trend"]] = "AvgTrend"
    if "avgtrend" in col_map: rename_map[col_map["avgtrend"]] = "AvgTrend"
    if "avg_trand" in col_map: rename_map[col_map["avg_trand"]] = "AvgTrend"
    df = df.rename(columns=rename_map)

    # ensure columns
    required = ["Date","Area","Peak","Trend","AvgTrend","Rally","Overview","Decision","SL","TG"]
    for r in required:
        if r not in df.columns:
            df[r] = ""

    # layout params
    row_height = 0.45 * inch
    data_cols = ["Date","Area","Peak","Trend","AvgTrend","Rally","Overview"]
    # we'll add Decision as radio group and two action columns (Trade1/Trade2)
    base_col_width = 1.05 * inch
    radio_col_width = 1.5 * inch
    col_widths = [base_col_width]*len(data_cols) + [radio_col_width, radio_col_width, radio_col_width] 
    # The last three: Decision (radio CE/PE), Trade1 (Target/SL), Trade2 (Target/SL)
    page_width = sum(col_widths) + 2*inch
    # compute page height depending on rows
    num_rows = len(df) + 2  # header + rows + some padding
    page_height = max(11*inch, (num_rows * row_height) + 2*inch)

    doc = SimpleDocTemplate(filename, pagesize=(page_width, page_height),
                            leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    elements = []

    header = Paragraph(f"<b>Manual Backtest — {month} {year} (Sanitized Demo)</b>", styles["Title"])
    elements.append(header)
    elements.append(Spacer(1, 0.2*inch))

    # build table data (header row)
    header_row = data_cols + ["Decision","1st Trade","2nd Trade"]
    table_data = [header_row]
    for _, row in df.iterrows():
        cells = [ _safe_str(row[c]) for c in data_cols ]
        # placeholders for radio columns (visual only)
        cells += ["   CE           PE", " Target       SL"," Target       SL"]
        table_data.append(cells)

    table = Table(table_data, colWidths=col_widths, rowHeights=[row_height]*len(table_data))
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2E7D32")),  # header green
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ])
    table.setStyle(style)
    elements.append(table)

    # Build PDF while injecting radio fields later via onFirstPage/onLaterPages callbacks
    def _add_radios(canv: canvas.Canvas, doc, table, df, col_widths, row_height):
        canv.saveState()

        # Set font to bold and color to white for labels
        canv.setFont("Helvetica-Bold", 10)
        canv.setFillColor(colors.whitesmoke)  # white-ish color for better contrast

        x_start = doc.leftMargin
        y_start = doc.height + doc.bottomMargin  # top margin from bottom

        header_height = row_height * 1.5

        button_size = 16
        x_offset = 0
        button_y_offset = 0.8 * inch # vertical offset to lower buttons inside row
        label_y_offset = button_y_offset-15  # label slightly below button center
        label_color = colors.black
        for i, row in enumerate(df.itertuples()):
            y = y_start - header_height - (i * row_height) - button_y_offset

            option_type_x = x_start + sum(col_widths[:-3]) + x_offset
            action_x = option_type_x + col_widths[-3]
            action2_x = action_x + col_widths[-2]
            
            
            option_group = f"option_type_{i}"
            action_group = f"action_{i}"
            action_group2 = f"action2_{i}"
            option_group = f"option_type_{i}"
            action_group = f"action_{i}"
            action_group2 = f"action2_{i}"
            
            
            # Determine selection from "Overview"
            overview_value = getattr(row, "Overview", "")
            if overview_value in ["Long 2", "Long 3"]:
                option_selected = "CE"
                fillcolor_remark =colors.green 
            elif overview_value in ["Short 2", "Short 3"]:
                option_selected = "PE"
                fillcolor_remark =colors.maroon 
            else:
                option_selected = None
                fillcolor_remark =colors.purple 
            # CE radio button + label
            canv.acroForm.radio(
                name=option_group, value='CE',
                x=option_type_x + 5, y=y,
                buttonStyle='check', size=button_size,
                borderWidth=1, fillColor=colors.white, borderColor=colors.black,
                selected=(option_selected == "CE")
            
            )
            canv.setFillColor(label_color)
            # canv.drawString(option_type_x + 5 + button_size + 4, y + label_y_offset, "CE")

            # PE radio button + label
            canv.acroForm.radio(
                name=option_group, value='PE',
                x=option_type_x + 60, y=y,
                buttonStyle='check',  size=button_size,
                borderWidth=1,fillColor=colors.white, borderColor=colors.black,
                selected=(option_selected == "PE")
            
            )
            canv.setFillColor(label_color)
            # canv.drawString(option_type_x + 60 + button_size + 4, y + label_y_offset, "PE")

            # Target radio button + label
            canv.acroForm.radio(
                name=action_group, value='Target',
                x=action_x + 5, y=y,
                buttonStyle='check',  size=button_size,
                borderWidth=1,fillColor=colors.white, borderColor=colors.black,
                
            )
            canv.setFillColor(label_color)
            # canv.drawString(action_x + 5 + button_size + 4, y + label_y_offset, "Target")

            # SL radio button + label
            canv.acroForm.radio(
                name=action_group, value='SL',
                x=action_x + 60, y=y,
                buttonStyle='check', 
                size=button_size,
                borderWidth=1,fillColor=colors.white, borderColor=colors.black,
            
            )
            canv.acroForm.radio(
                name=action_group2, value='Target',
                x=action2_x + 5, y=y,
                buttonStyle='check',  size=button_size,
                borderWidth=1,fillColor=colors.white, borderColor=colors.black,
                
            )
            canv.setFillColor(label_color)
            # canv.drawString(action_x + 5 + button_size + 4, y + label_y_offset, "Target")

            # SL radio button + label
            canv.acroForm.radio(
                name=action_group2, value='SL',
                x=action2_x + 60, y=y,
                buttonStyle='check', 
                size=button_size,
                borderWidth=1,fillColor=colors.white, borderColor=colors.black,
            
            )
            
            
        
        canv.restoreState()
    doc.build(elements, onFirstPage=lambda canv, doc: _add_radios(canv, doc, table, df, col_widths, row_height),
                    onLaterPages=lambda canv, doc: _add_radios(canv, doc, table, df, col_widths, row_height))
    print("Manual PDF created:", filename)
    return filename

# --------- Automated PDF output ----------
def automated_pdf_from_df(df, month, year, filename="02_Automated_Algo_Sample_portfolio_safe.pdf"):
    """
    df should contain columns like Date, EntryTime, ExitTime, Direction, EntryPrice, SL, Target, RiskReward, Result
    Produces a sanitized automated-backtest PDF with summary stats and colored rows.
    """
    # ensure required cols
    required = ["Date","Entry Time","Exit Time","Direction","Entry Price","SL","Target","Risk, Reward","Result"]
    for r in required:
        if r not in df.columns:
            df[r] = ""

    # compute summary
    total_trades = len(df)
    wins = df['Result'].str.lower().eq('win').sum() if 'Result' in df.columns else 0
    losses = df['Result'].str.lower().eq('loss').sum() if 'Result' in df.columns else 0
    accuracy = (wins / total_trades * 100) if total_trades else 0

    # create document
    col_order = ["Date","Entry Time","Exit Time","Direction","Entry Price","SL","Target","Risk, Reward","Result"]
    col_width = 1.0 * inch
    col_widths = [col_width]*len(col_order)
    num_rows = len(df) + 2
    page_height = max(11*inch, (num_rows * 0.45*inch) + 2*inch)
    page_width = sum(col_widths) + 2*inch

    doc = SimpleDocTemplate(filename, pagesize=(page_width, page_height), leftMargin=inch, rightMargin=inch,
                            topMargin=inch, bottomMargin=inch)
    styles = getSampleStyleSheet()
    elements = []

    header = Paragraph(f"<b>Automated Algo Backtest — {month} {year} (Sanitized Demo)</b>", styles["Title"])
    elements.append(header)
    elements.append(Spacer(1,0.1*inch))

    summary = Paragraph(f"<b>Accuracy:</b> {accuracy:.2f}%  &nbsp;&nbsp; <b>Wins:</b> {wins}  &nbsp;&nbsp; <b>Losses:</b> {losses}", styles["Normal"])
    elements.append(summary)
    elements.append(Spacer(1,0.15*inch))

    table_data = [col_order]
    for _, row in df.iterrows():
        table_data.append([ _safe_str(row[c]) if c in df.columns else "" for c in col_order ])

    table = Table(table_data, colWidths=col_widths, rowHeights=[0.45*inch]*len(table_data))
    style = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.4, colors.black),
    ])
    # color rows by Result
    if "Result" in df.columns:
        for i, row in enumerate(df.itertuples(index=False), start=1):
            res = getattr(row, "Result", "") or getattr(row, "Result", "")
            res_l = _safe_str(res).lower()
            if "win" in res_l or "profit" in res_l:
                style.add('BACKGROUND', (0,i), (-1,i), colors.HexColor("#2E7D32"))  # green
                style.add('TEXTCOLOR', (0,i), (-1,i), colors.whitesmoke)
            elif "loss" in res_l or "loss" == res_l:
                style.add('BACKGROUND', (0,i), (-1,i), colors.HexColor("#B71C1C"))  # red
                style.add('TEXTCOLOR', (0,i), (-1,i), colors.whitesmoke)
    table.setStyle(style)
    elements.append(table)
    doc.build(elements)
    print("Automated PDF created:", filename)
    return filename

# --------- Readback function: calculate accuracy from filled interactive PDF ----------
def calculate_accuracy_from_filled_pdf(pdf_path):
    """
    Reads a user-filled interactive manual PDF (with radio fields named option_type_i, action_i, action2_i)
    and computes counts + accuracy for Target vs SL selections.
    Returns dictionary with set1, set2, combined values.
    """
    reader = PdfReader(pdf_path)
    # PyPDF2 stores fields differently across versions; use get_fields() where available
    try:
        fields = reader.get_fields()
    except Exception:
        # fallback: try reader.fields
        fields = getattr(reader, "fields", None)

    # Normalize fields dict to simple mapping name -> value
    flat = {}
    if fields:
        # fields can be dict(name: FieldObject) or list; attempt to extract values safely
        if isinstance(fields, dict):
            for name, obj in fields.items():
                try:
                    # PyPDF2 Field object can contain /V key or get('/V')
                    v = obj.get("/V") if hasattr(obj, "get") else obj
                    # normalize boolean-like or byte values
                    if isinstance(v, (list, tuple)):
                        v = v[0]
                    flat[name] = _safe_str(v)
                except Exception:
                    flat[name] = _safe_str(obj)
        else:
            # unknown structure: dump as-is
            for f in fields:
                try:
                    n = f.get("/T") or f.get("T")
                    v = f.get("/V") or f.get("V")
                    flat[n] = _safe_str(v)
                except Exception:
                    pass

    # Helper to count radio groups by prefix
    def count_actions(prefix):
        target = 0
        sl = 0
        total = 0
        for name, val in flat.items():
            if not name or not name.startswith(prefix):
                continue
            # Normalize value strings like '/Target', 'Target', ' /Target'
            v = _safe_str(val).strip().strip('/')
            if v.lower() == "target":
                target += 1
                total += 1
            elif v.lower() == "sl":
                sl += 1
                total += 1
        acc = (target / total * 100) if total else 0.0
        return round(acc,2), target, sl, total

    acc1, tgt1, sl1, total1 = count_actions("action_")   # first trade radios
    acc2, tgt2, sl2, total2 = count_actions("action2_")  # second trade radios
    # decision radios (CE/PE) not counted for accuracy but could be
    # Combined
    total_target = tgt1 + tgt2
    total_sl = sl1 + sl2
    total = total1 + total2
    combined_acc = (total_target / total * 100) if total else 0.0

    return {
        "set1": {"accuracy": acc1, "target": tgt1, "sl": sl1, "total": total1},
        "set2": {"accuracy": acc2, "target": tgt2, "sl": sl2, "total": total2},
        "combined": {"accuracy": round(combined_acc,2), "target": total_target, "sl": total_sl, "total": total}
    }

# ---------------- Example usage ----------------
if __name__ == "__main__":
    import pandas as pd
    # small demo dataframes (sanitized)
    manual_demo = pd.DataFrame([
        {"Date":"2024-XX-01","Area":"SignalA","Peak":"SignalA","Trend":"SignalB","AvgTrend":"SignalC","Rally":"SignalD","Overview":"Long 2","Decision":""},
        {"Date":"2024-XX-02","Area":"SignalB","Peak":"SignalA","Trend":"SignalB","AvgTrend":"SignalC","Rally":"SignalD","Overview":"Short 2","Decision":""},
    ])
    auto_demo = pd.DataFrame([
        {"Date":"2024-XX-01","Entry Time":"09:35","Exit Time":"09:58","Direction":"Short","Entry Price":"--","SL":"--","Target":"--","Risk":"10", "Reward":"20","Result":"Win"},
        {"Date":"2024-XX-02","Entry Time":"10:10","Exit Time":"10:42","Direction":"Short","Entry Price":"--","SL":"--","Target":"--","Risk":"15", "Reward":"30","Result":"Win"},
    ])
#load from sample if needed
    manual_pdf_from_df(manual_demo, "Feb", 2024, filename="demo_manual.pdf")
    automated_pdf_from_df(auto_demo, "Feb", 2024, filename="demo_auto.pdf")
    # After user edits demo_manual.pdf and selects radios, call:
    # print(calculate_accuracy_from_filled_pdf("user_filled_demo_manual.pdf"))
