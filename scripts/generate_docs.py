import os
import subprocess
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

def set_cell_background(cell, fill_hex):
    tcPr = cell._element.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill_hex)
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._element.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
        node = OxmlElement(f'w:{m}')
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def create_word_document(docx_path):
    doc = Document()
    
    # Page Margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

    # Styles
    navy = RGBColor(30, 58, 138)       # #1e3a8a
    dark_gray = RGBColor(55, 65, 81)   # #374151
    light_blue = RGBColor(14, 116, 144) # #0e7490

    # Header Badge / Tagline
    p_tag = doc.add_paragraph()
    r_tag = p_tag.add_run("SMART INDIA HACKATHON (SIH) 2026  |  MINISTRY OF RAILWAYS, GOVT. OF INDIA")
    r_tag.font.name = "Calibri"
    r_tag.font.size = Pt(9.5)
    r_tag.font.bold = True
    r_tag.font.color.rgb = light_blue
    p_tag.paragraph_format.space_after = Pt(2)

    # Document Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run("Project Brief & Requirements Specification")
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(22)
    r_title.font.bold = True
    r_title.font.color.rgb = navy
    p_title.paragraph_format.space_after = Pt(4)

    # Subtitle
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run("Problem Statement 26027: AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways")
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(11)
    r_sub.font.italic = True
    r_sub.font.color.rgb = dark_gray
    p_sub.paragraph_format.space_after = Pt(14)

    # Metadata Table
    table = doc.add_table(rows=4, cols=2)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False

    meta = [
        ("Problem Statement ID:", "26027 (Ministry of Railways — SIH 2026)"),
        ("Project Domain / Category:", "Smart Railways, AI & Optimization, Cyber-Physical Systems"),
        ("Primary Beneficiaries:", "Indian Railways Section Controllers, Operating & Maintenance Departments"),
        ("Key Technologies:", "Python (FastAPI, Google OR-Tools CP-SAT, XGBoost), React 19, Open-Meteo API")
    ]

    for i, (k, v) in enumerate(meta):
        row = table.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.5)
        
        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = navy
        p0.paragraph_format.space_after = Pt(0)
        
        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(9.5)
        p1.paragraph_format.space_after = Pt(0)

        bg = "F3F4F6" if i % 2 == 0 else "FFFFFF"
        set_cell_background(c0, bg)
        set_cell_background(c1, bg)
        set_cell_margins(c0, top=70, bottom=70, left=100, right=100)
        set_cell_margins(c1, top=70, bottom=70, left=100, right=100)

    doc.add_paragraph().paragraph_format.space_after = Pt(8)

    # Helper for adding sections
    def add_section(heading, text_paragraphs):
        h = doc.add_paragraph()
        r = h.add_run(heading)
        r.font.name = "Calibri"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = navy
        h.paragraph_format.space_before = Pt(10)
        h.paragraph_format.space_after = Pt(4)

        for text in text_paragraphs:
            p = doc.add_paragraph()
            p.paragraph_format.line_spacing = 1.15
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(text)
            run.font.name = "Calibri"
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(31, 41, 55)

    # 1. Introduction
    add_section(
        "1. Introduction",
        ["Indian Railways operates one of the world's most congested rail networks, running over 21,000 passenger and freight trains daily across 68,000 route kilometers. To maintain strict safety standards and prevent derailments, regular maintenance of tracks, signaling systems, and overhead electrical lines is mandatory. However, maintenance requires 'traffic and power blocks'—dedicated windows where train traffic is halted or regulated along a track section. Currently, these blocks are negotiated manually through inter-departmental meetings. Without automated coordination, maintenance demands conflict with train timetables, leading to severe passenger delays, underutilized rail capacity, and repeated corridor shutdowns."]
    )

    # 2. Problem Statement
    add_section(
        "2. Problem Statement",
        ["In Indian Railways, maintenance demands from the Track (Civil/TMS), Signalling (S&T/SMMS), and Electrical (TRD/TDMS) departments reside in isolated, independent systems. Because each department schedules work separately without real-time alignment with the Control Office Application (COA) train timetable, the same track section is often shut down repeatedly on consecutive days. This lack of coordination throttles line capacity, causes cascading delays to high-priority trains like Vande Bharat and Rajdhani, and prevents rapid dynamic rescheduling when unexpected rail defects or severe weather events strike in real time."]
    )

    # 3. Aim of the Project
    add_section(
        "3. Aim of the Project",
        ["The primary aim of this project is to develop an AI-powered automated block scheduling and real-time digital twin system for Indian Railways. The platform coordinates multi-departmental maintenance demands, maximizes track availability for commercial train operations, eliminates scheduling conflicts, and dynamically reschedules maintenance windows within seconds during real-time track disruptions or severe weather emergencies."]
    )

    # 4. Project Description
    add_section(
        "4. Project Description",
        [
            "This project provides an end-to-end decision-support platform for railway section controllers by combining machine learning, spatial clustering, and mathematical constraint programming. The system ingests defect records across Track, Signal, and Electrical departments and ranks their urgency using an AI Criticality Scoring engine (XGBoost blended with safety heuristics) based on defect severity, speed restrictions, and passenger traffic density. It then applies spatial clustering (DBSCAN) to group overlapping tasks along the same corridor (within 2.0 km), allowing multiple departments to execute repairs simultaneously under a single integrated block.",
            "The scheduling core employs Google OR-Tools CP-SAT to calculate mathematically conflict-free weekly block schedules that respect all train headways, crew limits, and maintenance machinery availability. Furthermore, the platform incorporates a Real-Time Railway Digital Twin that ingests live weather conditions via the Open-Meteo API and streams IoT track vibration telemetry. When an anomaly or emergency defect is detected, the system calculates the cascading blast radius and generates an updated schedule within 60 seconds. The entire platform is accessible through an interactive React 19 Web GIS dashboard featuring live track maps, Gantt timelines, and one-click PDF Block Sanction Order generation with QR verification."
        ]
    )

    # 5. Key Objectives
    add_section(
        "5. Key Objectives",
        [
            "• Automated Conflict-Free Planning: Replace days of manual coordination by automatically computing conflict-free corridor block schedules in under 2 minutes.",
            "• Maximize Track Availability: Elevate active track availability for train operations on high-density corridors to over 88.5% while adhering to all safety protocols.",
            "• Multi-Department Integration: Achieve a cross-departmental integration rate of over 70%, bundling track, signal, and electrical maintenance into joint windows.",
            "• Real-Time Anomaly Resilience: Detect rail vibration and thermal anomalies and dynamically generate conflict-free replacement schedules in under 60 seconds.",
            "• Controller Decision Support: Equip Section Controllers with an interactive GIS map, schedule timeline, and instant export of official block sanction permits."
        ]
    )

    # 6. References
    add_section(
        "6. References",
        [
            "[1] Ministry of Railways, Government of India (2020). Indian Railways Permanent Way Manual (IRPWM). Railway Board, New Delhi. (Standard operating procedures for track maintenance, speed restrictions, and traffic block possessions).",
            "[2] Ministry of Railways, Government of India (2021). Indian Railways Signal Engineering Manual (IRSEM) & AC Traction Manual (ACTM). (Protocols for signaling maintenance, points testing, and OHE power block shutdowns).",
            "[3] Smart India Hackathon (SIH) 2026. Problem Statement 26027: 'AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways', Ministry of Railways / AICTE, Govt. of India.",
            "[4] Lidén, T., & Joborn, M. (2016). 'Dimensioning maintenance windows on railway networks with integer programming.' Transportation Research Part C: Emerging Technologies, 69, 442-458.",
            "[5] Vansteenwegen, P., et al. (2016). 'The railway track maintenance scheduling problem: A review of models and solution methods.' European Journal of Operational Research, 254(3), 693-708.",
            "[6] Perron, L., & Didier, F. 'Google Optimization Tools (OR-Tools) CP-SAT Solver for Constraint Programming and Discrete Optimization.' Google LLC.",
            "[7] Chen, T., & Guestrin, C. (2016). 'XGBoost: A Scalable Tree Boosting System.' Proceedings of the 22nd ACM SIGKDD International Conference on Knowledge Discovery and Data Mining, 785-794.",
            "[8] Ester, M., Kriegel, H. P., Sander, J., & Xu, X. (1996). 'A density-based algorithm for discovering clusters in large spatial databases with noise (DBSCAN).' KDD-96 Proceedings, 226-231.",
            "[9] Zippenfenig, P. (2023). 'Open-Meteo: Open-Source High-Resolution Weather API and Meteorological Data Pipeline.'"
        ]
    )

    # Footer note
    doc.add_paragraph().paragraph_format.space_after = Pt(10)
    p_foot = doc.add_paragraph()
    r_foot = p_foot.add_run("Submitted for Academic & Institutional Evaluation — Capstone Project 2026")
    r_foot.font.size = Pt(9)
    r_foot.font.italic = True
    r_foot.font.color.rgb = RGBColor(107, 114, 128)
    p_foot.alignment = WD_ALIGN_PARAGRAPH.CENTER

    try:
        doc.save(docx_path)
        print(f"Word Document successfully saved to: {docx_path}")
    except PermissionError:
        alt_docx = docx_path.replace(".docx", "_v2.docx")
        doc.save(alt_docx)
        print(f"Original file was open in Word. Saved updated document to: {alt_docx}")

def create_pdf_from_html(html_path, pdf_path):
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Project Brief - SIH 26027</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
  }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #1f2937;
    line-height: 1.5;
    font-size: 10.5pt;
    margin: 0;
    padding: 0;
  }
  .badge {
    color: #0e7490;
    font-size: 8.5pt;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 4px;
  }
  h1 {
    color: #1e3a8a;
    font-size: 18pt;
    margin: 0 0 6px 0;
    font-weight: 800;
    line-height: 1.2;
  }
  .subtitle {
    color: #4b5563;
    font-size: 9.5pt;
    font-style: italic;
    margin-bottom: 12px;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 8px;
  }
  .meta-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 8px 12px;
    margin-bottom: 14px;
    display: grid;
    grid-template-columns: 140px 1fr;
    gap: 4px 10px;
    font-size: 9pt;
  }
  .meta-label {
    font-weight: bold;
    color: #1e3a8a;
  }
  .meta-val {
    color: #334155;
  }
  h2 {
    color: #1e3a8a;
    font-size: 11.5pt;
    margin: 12px 0 4px 0;
    font-weight: 700;
    border-left: 3px solid #1e3a8a;
    padding-left: 8px;
  }
  p {
    margin: 0 0 8px 0;
    text-align: justify;
  }
  ul {
    margin: 4px 0 10px 18px;
    padding: 0;
  }
  li {
    margin-bottom: 4px;
  }
  .footer {
    margin-top: 16px;
    border-top: 1px solid #e5e7eb;
    padding-top: 8px;
    text-align: center;
    font-size: 8.5pt;
    color: #6b7280;
    font-style: italic;
  }
</style>
</head>
<body>

<div class="badge">Smart India Hackathon (SIH) 2026 &bull; Ministry of Railways, Govt. of India</div>
<h1>AI-Powered Automatic Block Planning System</h1>
<div class="subtitle">Problem Statement 26027: To Maximize Asset Availability for Train Operations on Indian Railways</div>

<div class="meta-box">
  <div class="meta-label">Problem Statement ID:</div>
  <div class="meta-val">26027 (Ministry of Railways / AICTE)</div>
  <div class="meta-label">Category / Domain:</div>
  <div class="meta-val">Smart Transportation, AI &amp; Operations Research, Real-Time Digital Twin</div>
  <div class="meta-label">Core Architecture:</div>
  <div class="meta-val">TMS/SMMS/TDMS &rarr; AI Criticality &rarr; DBSCAN Clustering &rarr; OR-Tools CP-SAT &rarr; FastAPI &rarr; React 19</div>
  <div class="meta-label">Target Beneficiaries:</div>
  <div class="meta-val">Section Controllers, Divisional Operations &amp; Engineering Maintenance Wings</div>
</div>

<h2>1. Introduction</h2>
<p>
Indian Railways operates one of the world's largest and most congested rail networks, running over 21,000 passenger and freight trains daily across 68,000 route kilometers. To maintain uncompromising safety standards and prevent catastrophic derailments, regular maintenance of tracks, signaling systems, and overhead electrical (OHE) lines is mandatory. However, maintenance requires "traffic and power blocks" during which train movements on specific tracks must be halted or diverted. Currently, block planning across Indian Railways divisions is largely managed through manual, negotiation-heavy meetings. Without automated coordination against live train timetables, maintenance requests conflict with high-priority traffic, causing severe train delays, underutilized block windows, and repeated corridor shutdowns.
</p>

<h2>2. Problem Statement</h2>
<p>
In Indian Railways, maintenance demands from the Track (Civil/TMS), Signalling (S&amp;T/SMMS), and Electrical (TRD/TDMS) departments reside in isolated, independent systems. Because these departments schedule work separately without real-time alignment with the Control Office Application (COA) train timetables, the same track section is often shut down repeatedly on consecutive days by different teams. This lack of coordination throttles line capacity, causes cascading delays to high-priority trains like Vande Bharat and Rajdhani, and prevents rapid dynamic rescheduling when unexpected rail defects or severe weather events strike in real time.
</p>

<h2>3. Aim of the Project</h2>
<p>
The primary aim of this project is to develop an intelligent, automated block scheduling and real-time digital twin platform for Indian Railways. The platform coordinates multi-departmental maintenance demands, maximizes track availability for commercial train operations, eliminates scheduling conflicts, and dynamically reschedules maintenance windows within seconds during real-time track disruptions or adverse weather conditions.
</p>

<h2>4. Project Description</h2>
<p>
This project provides an end-to-end decision-support platform for railway section controllers by combining machine learning, spatial clustering, and mathematical constraint programming. The system ingests defect records across Track, Signal, and Electrical departments and ranks their urgency using an AI Criticality Scoring engine (XGBoost blended with safety heuristics) based on defect severity, speed restrictions, and passenger traffic density. It then applies spatial clustering (DBSCAN) to group overlapping tasks along the same corridor (within 2.0 km), allowing multiple departments to execute repairs simultaneously under a single integrated block.
</p>
<p>
The scheduling core employs Google OR-Tools CP-SAT to calculate mathematically conflict-free weekly block schedules that respect all train headways, crew limits, and maintenance machinery availability. Furthermore, the platform incorporates a Real-Time Railway Digital Twin that ingests live weather conditions via the Open-Meteo API and streams simulated IoT track vibration telemetry. When an anomaly or emergency defect is detected, the system calculates the cascading blast radius and generates an updated schedule within 60 seconds. The entire platform is accessible through an interactive React 19 Web GIS dashboard featuring live track maps, Gantt timelines, and one-click PDF Block Sanction Order generation with QR verification.
</p>

<h2>5. Key Objectives</h2>
<ul>
  <li><strong>Automated Conflict-Free Planning:</strong> Replace days of manual coordination by automatically computing conflict-free corridor block schedules in under 2 minutes.</li>
  <li><strong>Maximize Track Availability:</strong> Elevate active track availability for train operations on high-density corridors to over 88.5% while adhering to all safety protocols.</li>
  <li><strong>Multi-Department Integration:</strong> Achieve a cross-departmental integration rate of over 70%, bundling track, signal, and electrical maintenance into joint windows.</li>
  <li><strong>Real-Time Anomaly Resilience:</strong> Detect rail vibration and thermal anomalies and dynamically generate conflict-free replacement schedules in under 60 seconds.</li>
  <li><strong>Controller Decision Support:</strong> Equip Section Controllers with an interactive GIS map, schedule timeline, and instant export of official block sanction permits.</li>
</ul>

<h2>6. References</h2>
<ul style="font-size: 8.8pt; line-height: 1.4; color: #374151;">
  <li><strong>[1] Ministry of Railways, Government of India (2020).</strong> <em>Indian Railways Permanent Way Manual (IRPWM)</em>. Railway Board, New Delhi. (Procedures for track maintenance, speed restrictions, and block possessions).</li>
  <li><strong>[2] Ministry of Railways, Government of India (2021).</strong> <em>Indian Railways Signal Engineering Manual (IRSEM) &amp; AC Traction Manual (ACTM)</em>. (Protocols for signaling maintenance and OHE power block shutdowns).</li>
  <li><strong>[3] Smart India Hackathon (SIH) 2026.</strong> Problem Statement 26027: <em>"AI-Powered Automatic Block Planning to Maximize Asset Availability for Train Operations on Indian Railways"</em>, Ministry of Railways / AICTE.</li>
  <li><strong>[4] Lid&eacute;n, T., &amp; Joborn, M. (2016).</strong> Dimensioning maintenance windows on railway networks with integer programming. <em>Transportation Research Part C: Emerging Technologies</em>, 69, 442&ndash;458.</li>
  <li><strong>[5] Vansteenwegen, P., et al. (2016).</strong> The railway track maintenance scheduling problem: A review of models and solution methods. <em>European Journal of Operational Research</em>, 254(3), 693&ndash;708.</li>
  <li><strong>[6] Perron, L., &amp; Didier, F.</strong> <em>Google Optimization Tools (OR-Tools) CP-SAT Solver for Constraint Programming and Discrete Optimization</em>. Google LLC.</li>
  <li><strong>[7] Chen, T., &amp; Guestrin, C. (2016).</strong> XGBoost: A Scalable Tree Boosting System. <em>ACM SIGKDD International Conference on Knowledge Discovery and Data Mining</em>, 785&ndash;794.</li>
  <li><strong>[8] Ester, M., Kriegel, H. P., Sander, J., &amp; Xu, X. (1996).</strong> A density-based algorithm for discovering clusters in large spatial databases with noise (DBSCAN). <em>KDD-96 Proceedings</em>, 226&ndash;231.</li>
  <li><strong>[9] Zippenfenig, P. (2023).</strong> Open-Meteo: Open-Source High-Resolution Weather API and Meteorological Data Pipeline.</li>
</ul>

<div class="footer">
  Smart India Hackathon 2026 &bull; Problem Statement 26027 &bull; Capstone Project Submission &bull; Academic Year 2026
</div>

</body>
</html>
"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    # Use Chrome or Edge headless to generate PDF
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    browser = chrome_path if os.path.exists(chrome_path) else edge_path
    
    target_pdf = pdf_path
    cmd = [
        browser,
        "--headless",
        "--disable-gpu",
        f"--print-to-pdf={target_pdf}",
        "--no-pdf-header-footer",
        html_path
    ]
    try:
        subprocess.run(cmd, check=True)
        print(f"PDF Document successfully created at: {target_pdf}")
    except Exception as e:
        alt_pdf = pdf_path.replace(".pdf", "_v2.pdf")
        cmd[3] = f"--print-to-pdf={alt_pdf}"
        subprocess.run(cmd, check=True)
        print(f"Original PDF locked. Saved updated PDF to: {alt_pdf}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    reports_dir = os.path.join(base_dir, "reports")
    os.makedirs(reports_dir, exist_ok=True)

    docx_file = os.path.join(reports_dir, "AI_Railway_Block_Planning_SIH26027_Project_Brief.docx")
    html_file = os.path.join(reports_dir, "project_brief.html")
    pdf_file = os.path.join(reports_dir, "AI_Railway_Block_Planning_SIH26027_Project_Brief.pdf")
    
    create_word_document(docx_file)
    create_pdf_from_html(html_file, pdf_file)

