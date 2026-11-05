from pathlib import Path
p=Path('work/report-four.py');s=p.read_text(encoding='utf8');s=s.replace("t=d.add_table(rows=1,cols=len(head));t.autofit=False", "t=d.add_table(rows=1,cols=len(head));t.autofit=False\n if widths:\n  widths=[v*7/sum(widths) for v in widths]\n  for i,w in enumerate(widths):t.columns[i].width=Inches(w)")
s=s.replace(' return t\ndef pct'," gap=d.add_paragraph();gap.paragraph_format.space_before=Pt(0);gap.paragraph_format.space_after=Pt(0);gap.paragraph_format.line_spacing=Pt(3)\n return t\ndef pct")
s=s.replace("2026 年 11 月 3 日';foot.runs", "2026 年 11 月 3 日　|　第 ';foot.runs")
s=s.replace("foot._p.append(field)\npath=", "foot._p.append(field);foot.add_run(' 页').font.size=Pt(9);d.styles['Footer'].font.size=Pt(9)\npath=")
p.write_text(s,encoding='utf8')
