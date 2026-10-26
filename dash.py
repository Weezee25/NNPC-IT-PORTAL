import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import os
import base64
import sqlite3
import hashlib
from io import BytesIO

# --- ReportLab Imports for PDF Generation ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# ==========================================
# 1. PAGE CONFIG & UNIVERSAL THEME STYLING
# ==========================================
st.set_page_config(
    page_title="NNPC Internship Portal Dashboard",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Helper function to set base64 backgrounds dynamically with robust CSS overrides
def set_background(image_path, overlay_color="rgba(241, 245, 249, 0.85)"):
    if not os.path.exists(image_path):
        # Fallback to standard color if image is missing so the app doesn't break
        st.markdown("""<style>[data-testid="stAppViewContainer"], .stApp { background-color: #F1F5F9 !important; }</style>""", unsafe_allow_html=True)
        return

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <style>
    /* Apply background to the main app containers */
    [data-testid="stAppViewContainer"], .stApp {{
        background-image: linear-gradient({overlay_color}, {overlay_color}), url("data:image/jpeg;base64,{encoded}") !important;
        background-size: cover !important;
        background-position: center !important;
        background-attachment: fixed !important;
    }}
    /* Force transparency on any solid layers that sit on top of the background */
    [data-testid="stHeader"] {{ background: transparent !important; }}
    [data-testid="stApp"] {{ background: transparent !important; }}
    main {{ background: transparent !important; }}
    </style>
    """, unsafe_allow_html=True)

# Deep CSS Overrides to lock card text & backgrounds across light & dark browser modes
st.markdown("""
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%) !important;
        padding: 26px 32px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        margin-bottom: 20px; border-bottom: 4px solid #FFD100;
    }
    .hero-banner * { color: #FFFFFF !important; }
    .hero-banner h2 { color: #FFD100 !important; }
    .card-white {
        background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important;
        border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-white, .card-white h1, .card-white h2, .card-white h3, .card-white h4, 
    .card-white h5, .card-white p, .card-white span, .card-white div, 
    .card-white li, .card-white b, .card-white td, .card-white th { color: #0F172A !important; }
    .metric-card-white {
        background-color: #FFFFFF !important; border: 1px solid #CBD5E1 !important;
        border-radius: 12px; padding: 18px 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .metric-card-white * { color: #0F172A !important; }
    .curr-box {
        background-color: #F8FAFC !important; border: 1px solid #CBD5E1 !important;
        padding: 12px; border-radius: 8px; min-height: 140px;
    }
    .curr-box * { color: #0F172A !important; }
    [data-testid="stSidebar"] { background-color: #002B15 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stRadio label p { color: #FFFFFF !important; }
    .top-greeting * { color: #0F172A !important; }
    .streamlit-expanderHeader { color: #002B15 !important; font-weight: bold; }
    [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { color: #0F172A !important; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "nnpc.jpeg"

def render_pdf_viewer(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="520" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==========================================
# 2. PERSISTENT SQLITE DATABASE ENGINE & AUTH
# ==========================================
DB_NAME = "nnpc_portal.db"

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, department TEXT, email TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, date TEXT, time TEXT, status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, week TEXT, topic TEXT, filename TEXT, filedata BLOB, date TEXT, status TEXT, grade TEXT, feedback TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, week TEXT, subtopic TEXT, score INTEGER, total INTEGER, date TEXT)''')
        
        # New tables for supervisor functionality
        c.execute('''CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, date TEXT, author TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, subject TEXT, message TEXT, status TEXT, reply TEXT, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS module_locks (department TEXT, week TEXT, is_locked INTEGER, PRIMARY KEY(department, week))''')
        conn.commit()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role, department, email):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role, department, email) VALUES (?, ?, ?, ?, ?)",
                      (username, hash_password(password), role, department, email))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False 

def authenticate_user(username, password):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT role, department, email FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
        return c.fetchone()

def record_attendance(username, department):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        now = datetime.now()
        c.execute("SELECT id FROM attendance WHERE username = ? AND date = ?", (username, str(now.date())))
        if c.fetchone(): return False
        c.execute("INSERT INTO attendance (username, department, date, time, status) VALUES (?, ?, ?, ?, ?)",
                  (username, department, str(now.strftime("%Y-%m-%d")), str(now.strftime("%I:%M %p")), "On Time"))
        conn.commit()
        return True

def fetch_data(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        return pd.read_sql_query(query, conn, params=params)

def execute_query(query, params=()):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(query, params)
        conn.commit()

# ==========================================
# 3. PDF LOGBOOK GENERATOR (REPORTLAB)
# ==========================================
def generate_logbook_pdf(username, department):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("<b>NNPC Eighteen Operating Limited (NEOL)</b>", styles['Title']))
    elements.append(Paragraph("Official Internship Logbook & Performance Report", styles['Heading2']))
    elements.append(Spacer(1, 15))
    elements.append(Paragraph(f"<b>Student Name:</b> {username}", styles['Normal']))
    elements.append(Paragraph(f"<b>Department:</b> {department}", styles['Normal']))
    elements.append(Paragraph(f"<b>Generated On:</b> {date.today().strftime('%B %d, %Y')}", styles['Normal']))
    elements.append(Spacer(1, 20))

    att_df = fetch_data("SELECT date, time, status FROM attendance WHERE username = ?", (username,))
    sub_df = fetch_data("SELECT week, topic, status, grade FROM submissions WHERE username = ?", (username,))
    quiz_df = fetch_data("SELECT week, subtopic, score, total FROM quiz_scores WHERE username = ?", (username,))

    def create_pdf_table(title, df):
        elements.append(Paragraph(f"<b>{title}</b>", styles['Heading3']))
        if df.empty:
            elements.append(Paragraph("No records found.", styles['Normal']))
        else:
            data = [df.columns.tolist()] + df.values.tolist()
            table = Table(data, colWidths=[120]*len(df.columns))
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#006837")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F1F5F9")),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            elements.append(table)
        elements.append(Spacer(1, 15))

    create_pdf_table("1. Attendance Register", att_df)
    create_pdf_table("2. Deliverables & Grades", sub_df)
    create_pdf_table("3. Assessment Scores", quiz_df)

    elements.append(Spacer(1, 40))
    elements.append(Paragraph("_____________________________         _____________________________", styles['Normal']))
    elements.append(Paragraph("Student Signature & Date                 Supervisor Signature & Date", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# ==========================================
# 4. MASSIVE INTERACTIVE DEPARTMENT CURRICULUM DATA
# ==========================================
department_curriculums = {
    "Projects": [
        {"week": "Week 1 – 4", "title": "Project Lifecycle & Regulations", "deliv": "Regulatory Intelligence Summary", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "NUPRC Regulatory Framework",
             "notes": "The Nigerian Upstream Petroleum Regulatory Commission (NUPRC) is the primary regulatory body for upstream operations. Compliance requires strict adherence to EGASPIN (Environmental Guidelines) and the Petroleum Industry Act (PIA) of 2021, which dictates fiscal frameworks and host community development trusts.",
             "quiz": [
                 {"q": "What does NUPRC stand for?", "opts": ["Nigerian Upstream Petroleum Regulatory Commission", "National Union of Petroleum Refining", "Nigerian United Petroleum Resources"], "ans": "Nigerian Upstream Petroleum Regulatory Commission"},
                 {"q": "Which act restructured the Nigerian oil and gas fiscal terms in 2021?", "opts": ["OPEC Act", "Petroleum Industry Act (PIA)", "EGASPIN Act"], "ans": "Petroleum Industry Act (PIA)"},
                 {"q": "What does EGASPIN regulate?", "opts": ["Taxation", "Environmental Standards", "Pipeline scheduling"], "ans": "Environmental Standards"},
                 {"q": "Which sector does NUPRC primarily oversee?", "opts": ["Downstream", "Midstream", "Upstream"], "ans": "Upstream"},
                 {"q": "Under the PIA, what must be established for local areas?", "opts": ["Host Community Development Trusts", "Local Refineries", "Free Fuel Depots"], "ans": "Host Community Development Trusts"}
             ],
             "assignment": "Read the PIA 2021 summary document. Write a 2-page report on how the Host Community Development Trust impacts project OPEX budgeting."
         }]},
        {"week": "Week 5 – 8", "title": "FEED & Costing Models", "deliv": "Facility Manifold Cost Model", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Front-End Engineering Design (FEED)",
             "notes": "FEED comes after the conceptual design and feasibility study. It focuses on technical requirements, identifying project risks, and estimating rough investment costs (usually accurate to +/- 15%). Deliverables include P&IDs, equipment data sheets, and project execution plans.",
             "quiz": [
                 {"q": "When does FEED occur in a project lifecycle?", "opts": ["Before conceptual design", "After conceptual design", "During construction"], "ans": "After conceptual design"},
                 {"q": "What is the typical cost estimate accuracy during FEED?", "opts": ["+/- 5%", "+/- 15%", "+/- 50%"], "ans": "+/- 15%"},
                 {"q": "Which is a standard FEED deliverable?", "opts": ["As-built drawings", "Piping and Instrumentation Diagrams (P&IDs)", "Final decommissioning plan"], "ans": "Piping and Instrumentation Diagrams (P&IDs)"},
                 {"q": "What is a primary goal of FEED?", "opts": ["Procure all materials", "Identify project risks", "Hire construction workers"], "ans": "Identify project risks"},
                 {"q": "FEED stands for:", "opts": ["Front-End Engineering Design", "Field Environmental Engineering Data", "Final Execution Evaluation Document"], "ans": "Front-End Engineering Design"}
             ],
             "assignment": "Using the provided template, develop a Level 3 cost estimate for the installation of a 4-slot production manifold."
         }]},
        {"week": "Week 9 – 12", "title": "Primavera P6 Scheduling", "deliv": "Baseline Master Schedule", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Critical Path Method (CPM)",
             "notes": "The Critical Path Method identifies the longest stretch of dependent activities and measures the time required to complete them. In Primavera P6, activities on the critical path have zero 'Total Float'. Delaying these delays the entire project.",
             "quiz": [
                 {"q": "What does CPM stand for?", "opts": ["Cost Planning Model", "Critical Path Method", "Core Project Metrics"], "ans": "Critical Path Method"},
                 {"q": "What is 'Total Float' on the critical path?", "opts": ["Zero", "10 days", "Infinite"], "ans": "Zero"},
                 {"q": "Delaying an activity on the critical path will:", "opts": ["Save money", "Delay the project", "Have no effect"], "ans": "Delay the project"},
                 {"q": "Which software is industry standard for oil & gas CPM?", "opts": ["MS Paint", "Primavera P6", "AutoCAD"], "ans": "Primavera P6"},
                 {"q": "Activities dependent on the completion of others are called:", "opts": ["Predecessors", "Successors", "Floaters"], "ans": "Successors"}
             ],
             "assignment": "Create a 20-activity schedule in Primavera P6 (or MS Project) for a flowline replacement. Identify the critical path and submit the Gantt PDF."
         }]},
        {"week": "Week 13 – 16", "title": "Site Inspections", "deliv": "Final Project Report", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Pre-Commissioning Audits",
             "notes": "Pre-commissioning involves verifying that equipment installation complies with design data. Key steps include hydro-testing pipelines, loop checking instruments, and verifying P&ID line walks to ensure mechanical completion.",
             "quiz": [
                 {"q": "What test is commonly done on pipelines during pre-commissioning?", "opts": ["Hydro-testing", "Seismic testing", "Tensile testing"], "ans": "Hydro-testing"},
                 {"q": "What is 'Line Walking'?", "opts": ["Checking pipe length", "Tracing physical lines against P&IDs", "Painting the pipes"], "ans": "Tracing physical lines against P&IDs"},
                 {"q": "Pre-commissioning confirms what type of completion?", "opts": ["Financial", "Mechanical", "Decommissioning"], "ans": "Mechanical"},
                 {"q": "Loop checking applies primarily to:", "opts": ["Structural beams", "Instrumentation and Control", "Valves"], "ans": "Instrumentation and Control"},
                 {"q": "Who typically signs off on Mechanical Completion?", "opts": ["The CEO", "QA/QC and Project Engineers", "The HR Manager"], "ans": "QA/QC and Project Engineers"}
             ],
             "assignment": "Write a step-by-step pre-commissioning checklist for a newly installed centrifugal pump."
         }]}
    ],
    "Subsurface": [
        {"week": "Week 1 – 4", "title": "2D/3D Seismic Horizon Mapping", "deliv": "Seismic Horizon Report", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Seismic Interpretation Basics",
             "notes": "Seismic interpretation involves analyzing acoustic waves reflected from rock boundaries to map sub-surface structures. Horizons represent geological time boundaries. Faults appear as discontinuities in these horizons.",
             "quiz": [
                 {"q": "What do seismic waves reflect off of?", "opts": ["Ocean surface", "Rock boundaries / acoustic impedance changes", "Drill bits"], "ans": "Rock boundaries / acoustic impedance changes"},
                 {"q": "What does a 'Horizon' represent?", "opts": ["Geological time boundary", "A type of well", "Surface elevation"], "ans": "Geological time boundary"},
                 {"q": "How do faults typically appear in seismic data?", "opts": ["Continuous bright lines", "Discontinuities/breaks in horizons", "Perfect circles"], "ans": "Discontinuities/breaks in horizons"},
                 {"q": "Which provides better spatial resolution?", "opts": ["2D Seismic", "3D Seismic", "Gravity survey"], "ans": "3D Seismic"},
                 {"q": "What software is widely used for seismic interpretation?", "opts": ["Petrel", "Photoshop", "Primavera"], "ans": "Petrel"}
             ],
             "assignment": "Analyze the provided seismic cross-section. Map the primary horizon and identify at least two major fault lines."
         }]},
        {"week": "Week 5 – 8", "title": "Petrophysical Log Evaluation", "deliv": "Net Pay & Water Saturation", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Wireline Logging",
             "notes": "Logs measure physical properties of formations. Gamma Ray logs identify lithology (shale vs sand). Resistivity logs differentiate between hydrocarbons (high resistivity) and formation water (low resistivity).",
             "quiz": [
                 {"q": "What does a Gamma Ray log primarily identify?", "opts": ["Temperature", "Lithology (shale vs sand)", "Pressure"], "ans": "Lithology (shale vs sand)"},
                 {"q": "High resistivity in a porous sandstone usually indicates:", "opts": ["Water", "Hydrocarbons", "Shale"], "ans": "Hydrocarbons"},
                 {"q": "Low resistivity usually indicates the presence of:", "opts": ["Oil", "Gas", "Formation Water"], "ans": "Formation Water"},
                 {"q": "What calculates formation porosity?", "opts": ["Density/Neutron logs", "Caliper log", "Mud log"], "ans": "Density/Neutron logs"},
                 {"q": "The Archie equation is used to calculate:", "opts": ["Drilling speed", "Water Saturation (Sw)", "Seismic velocity"], "ans": "Water Saturation (Sw)"}
             ],
             "assignment": "Use the provided well log data (Gamma Ray and Resistivity) to calculate the Net-to-Gross ratio of the reservoir interval."
         }]},
        {"week": "Week 9 – 12", "title": "Reservoir Material Balance", "deliv": "Reserves Estimation Analysis", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Drive Mechanisms",
             "notes": "Reservoir drive mechanisms dictate how oil is pushed to the surface. Common types include Water Drive (aquifer expansion), Solution Gas Drive (gas bubbling out of oil), and Gas Cap Drive (expanding gas cap).",
             "quiz": [
                 {"q": "Which drive mechanism maintains reservoir pressure best?", "opts": ["Solution Gas Drive", "Active Water Drive", "Compaction Drive"], "ans": "Active Water Drive"},
                 {"q": "What drives oil in a Solution Gas Drive?", "opts": ["Water below the oil", "Gas expanding out of the oil phase", "Gravity"], "ans": "Gas expanding out of the oil phase"},
                 {"q": "A rapidly expanding gas cap above the oil zone is a:", "opts": ["Water drive", "Gas Cap Drive", "Artificial lift"], "ans": "Gas Cap Drive"},
                 {"q": "What does MBAL software primarily do?", "opts": ["Material Balance calculations", "Seismic mapping", "Drilling design"], "ans": "Material Balance calculations"},
                 {"q": "What happens to pressure in a closed depletion drive?", "opts": ["Remains constant", "Drops rapidly", "Increases"], "ans": "Drops rapidly"}
             ],
             "assignment": "Write a brief report comparing the expected recovery factors of a Water Drive reservoir vs. a Solution Gas Drive reservoir."
         }]},
        {"week": "Week 13 – 16", "title": "Reservoir Simulation", "deliv": "Integrated Subsurface Model", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Dynamic Modeling",
             "notes": "Dynamic models simulate fluid flow over time using grid blocks. It combines static geological properties (porosity/permeability) with PVT fluid data and relative permeability curves to predict future production.",
             "quiz": [
                 {"q": "What does a dynamic model simulate?", "opts": ["Static rock volume", "Fluid flow over time", "Drilling rig structure"], "ans": "Fluid flow over time"},
                 {"q": "What fluid data is required for simulation?", "opts": ["PVT (Pressure-Volume-Temperature) data", "Water chemistry only", "Drilling mud weight"], "ans": "PVT (Pressure-Volume-Temperature) data"},
                 {"q": "Eclipse and tNavigator are software for:", "opts": ["Reservoir Simulation", "Accounting", "HR Management"], "ans": "Reservoir Simulation"},
                 {"q": "What dictates how two fluids flow together in pores?", "opts": ["Absolute permeability", "Relative permeability curves", "Porosity"], "ans": "Relative permeability curves"},
                 {"q": "History matching involves:", "opts": ["Matching simulation output to historical production data", "Matching logs to seismic", "Reading old company reports"], "ans": "Matching simulation output to historical production data"}
             ],
             "assignment": "Review the provided Eclipse history matching plot. Identify periods of mismatch and suggest two parameters you could adjust to fix it."
         }]}
    ],
    "ICT": [
        {"week": "Week 1 – 4", "title": "Network & Cybersecurity", "deliv": "Network Topology Audit", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Firewall & VLAN Configurations",
             "notes": "VLANs (Virtual Local Area Networks) segment network traffic for security and performance. Firewalls control incoming/outgoing traffic based on rules. NNPC uses strict IT/OT separation to protect field operational tech from corporate networks.",
             "quiz": [
                 {"q": "What is the purpose of a VLAN?", "opts": ["To increase internet speed", "To segment network traffic", "To replace cables"], "ans": "To segment network traffic"},
                 {"q": "What device enforces traffic rules between networks?", "opts": ["Switch", "Firewall", "Hub"], "ans": "Firewall"},
                 {"q": "What does IT/OT separation protect?", "opts": ["Corporate emails", "Operational Technology (like field PLCs)", "Printer networks"], "ans": "Operational Technology (like field PLCs)"},
                 {"q": "A DMZ in networking stands for:", "opts": ["Demilitarized Zone", "Data Management Zone", "Direct MAC Zone"], "ans": "Demilitarized Zone"},
                 {"q": "Which port is standard for HTTPS?", "opts": ["80", "443", "22"], "ans": "443"}
             ],
             "assignment": "Draw a basic network topology diagram showing an IT corporate network separated from an OT field network by a firewall."
         }]},
        {"week": "Week 5 – 8", "title": "Enterprise Database Admin", "deliv": "Database Security Audit", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "SQL & Access Controls",
             "notes": "Database administration ensures data integrity and availability. Role-Based Access Control (RBAC) ensures users only access data necessary for their jobs. SQL commands like GRANT and REVOKE manage these permissions.",
             "quiz": [
                 {"q": "What does RBAC stand for?", "opts": ["Role-Based Access Control", "Rule-Based Action Center", "Remote Backup And Control"], "ans": "Role-Based Access Control"},
                 {"q": "Which SQL command gives user permissions?", "opts": ["GIVE", "GRANT", "ALLOW"], "ans": "GRANT"},
                 {"q": "Which SQL command removes permissions?", "opts": ["DELETE", "DROP", "REVOKE"], "ans": "REVOKE"},
                 {"q": "CIA triad in security stands for:", "opts": ["Confidentiality, Integrity, Availability", "Central, Internal, Authorized", "Cost, IT, Administration"], "ans": "Confidentiality, Integrity, Availability"},
                 {"q": "A primary key in a database must be:", "opts": ["A number", "Unique and not null", "Shared across tables"], "ans": "Unique and not null"}
             ],
             "assignment": "Write a SQL script that creates a 'ProductionData' table and GRANTS read-only access to a 'JuniorEngineer' role."
         }]},
        {"week": "Week 9 – 12", "title": "Software Engineering & ITIL", "deliv": "Service Desk Automation", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "ITIL Incident Management",
             "notes": "ITIL is a framework for IT service management. Incident management aims to restore normal service operation as quickly as possible. SLAs (Service Level Agreements) define the acceptable resolution time based on ticket priority.",
             "quiz": [
                 {"q": "What is the goal of Incident Management?", "opts": ["Find who caused the error", "Restore service quickly", "Buy new hardware"], "ans": "Restore service quickly"},
                 {"q": "What does SLA stand for?", "opts": ["Software Licensing Agreement", "Service Level Agreement", "System Log Analysis"], "ans": "Service Level Agreement"},
                 {"q": "An incident that affects the entire organization is a:", "opts": ["P4 / Low Priority", "P1 / Major Incident", "Change Request"], "ans": "P1 / Major Incident"},
                 {"q": "ITIL focuses on aligning IT services with:", "opts": ["Coding standards", "Business needs", "Hardware specs"], "ans": "Business needs"},
                 {"q": "A workaround is used to:", "opts": ["Permanently fix a bug", "Temporarily restore service", "Bypass security"], "ans": "Temporarily restore service"}
             ],
             "assignment": "Draft an automated email response template for a P1 Major Incident regarding an Enterprise ERP server crash."
         }]},
        {"week": "Week 13 – 16", "title": "Cloud Infrastructure", "deliv": "Cloud System Deployment", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Cloud Deployment Models",
             "notes": "Cloud computing offers IaaS, PaaS, and SaaS. A Public Cloud is shared infrastructure (AWS, Azure). A Private Cloud is dedicated to one organization. A Hybrid cloud combines both, often used in Oil & Gas for data sovereignty.",
             "quiz": [
                 {"q": "What does SaaS stand for?", "opts": ["Software as a Service", "Storage as a System", "Security and System"], "ans": "Software as a Service"},
                 {"q": "AWS and Azure are examples of:", "opts": ["Private Clouds", "Public Clouds", "Local Servers"], "ans": "Public Clouds"},
                 {"q": "A mix of public and private cloud is called:", "opts": ["Mixed Cloud", "Hybrid Cloud", "Multi-Cloud"], "ans": "Hybrid Cloud"},
                 {"q": "IaaS provides:", "opts": ["Fully managed apps", "Virtual machines and storage", "Development frameworks"], "ans": "Virtual machines and storage"},
                 {"q": "Why do Oil & Gas companies use Hybrid clouds?", "opts": ["It is cheapest", "For Data Sovereignty and security of core assets", "To get free software"], "ans": "For Data Sovereignty and security of core assets"}
             ],
             "assignment": "Write a 1-page proposal evaluating whether the department should migrate legacy applications to a Public Cloud vs a Private Cloud."
         }]}
    ],
    "Facility": [
        {"week": "Week 1 – 4", "title": "HVAC & Power Systems", "deliv": "Maintenance Log & Safety Check", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Uninterruptible Power Supply (UPS)",
             "notes": "Facility power stability is critical. UPS systems provide emergency power to loads when the input power source fails, preventing data loss in server rooms and keeping critical control systems online until generators start.",
             "quiz": [
                 {"q": "What does UPS stand for?", "opts": ["Universal Power Source", "Uninterruptible Power Supply", "Unified Phase System"], "ans": "Uninterruptible Power Supply"},
                 {"q": "What is the primary function of a UPS?", "opts": ["Generate power permanently", "Bridge power gap until generators start", "Cool down servers"], "ans": "Bridge power gap until generators start"},
                 {"q": "What type of batteries are commonly used in industrial UPS?", "opts": ["AA Alkaline", "VRLA (Lead-Acid) or Lithium-ion", "Silver oxide"], "ans": "VRLA (Lead-Acid) or Lithium-ion"},
                 {"q": "A UPS prevents what during a blackout?", "opts": ["Data loss and control system failure", "Water leaks", "Fire"], "ans": "Data loss and control system failure"},
                 {"q": "What does an Inverter do in a UPS?", "opts": ["Converts AC to DC", "Converts DC to AC", "Stores energy"], "ans": "Converts DC to AC"}
             ],
             "assignment": "Perform a theoretical load calculation for a server room. Determine the kVA rating required for a UPS to sustain a 15kW load for 30 minutes."
         }]},
        {"week": "Week 5 – 8", "title": "HSE & Emergency Protocols", "deliv": "Hazard Identification Assessment", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Permit To Work (PTW) Systems",
             "notes": "PTW is a formal written system used to control certain types of potentially hazardous work. Hot Work permits are for tasks that generate heat/sparks (welding). Cold Work is for non-sparking tasks.",
             "quiz": [
                 {"q": "What does PTW stand for?", "opts": ["Permit To Work", "Plan The Work", "Pre-Task Warning"], "ans": "Permit To Work"},
                 {"q": "Welding requires what kind of permit?", "opts": ["Cold Work", "Hot Work", "Confined Space"], "ans": "Hot Work"},
                 {"q": "Who issues a PTW?", "opts": ["Any worker", "The Authorized Facility Manager / Supervisor", "HR"], "ans": "The Authorized Facility Manager / Supervisor"},
                 {"q": "What must be done before issuing a Confined Space permit?", "opts": ["Gas testing", "Painting", "Water flooding"], "ans": "Gas testing"},
                 {"q": "LOTO stands for:", "opts": ["Lock Out, Tag Out", "Leave Open, Turn Off", "Log Of Task Operations"], "ans": "Lock Out, Tag Out"}
             ],
             "assignment": "Fill out a sample Job Hazard Analysis (JHA) and Hot Work Permit template for welding a broken pipe bracket in the utility room."
         }]},
        {"week": "Week 9 – 12", "title": "Asset Integrity Mgmt", "deliv": "Preventive Maintenance Schedule", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Preventive vs Corrective Maintenance",
             "notes": "Corrective maintenance fixes things after they break (run-to-failure). Preventive Maintenance (PM) performs regular checks to prevent failures. Predictive maintenance uses sensors (vibration, temp) to predict failures before they happen.",
             "quiz": [
                 {"q": "Fixing a pump only after it stops working is:", "opts": ["Preventive", "Predictive", "Corrective / Reactive"], "ans": "Corrective / Reactive"},
                 {"q": "Changing oil every 3 months is an example of:", "opts": ["Preventive Maintenance", "Corrective Maintenance", "Design change"], "ans": "Preventive Maintenance"},
                 {"q": "Using vibration sensors to alert for bearing wear is:", "opts": ["Predictive Maintenance", "Corrective Maintenance", "Reactive Maintenance"], "ans": "Predictive Maintenance"},
                 {"q": "CMMS stands for:", "opts": ["Computerized Maintenance Management System", "Central Mechanical Monitor System", "Core Material Management Software"], "ans": "Computerized Maintenance Management System"},
                 {"q": "High MTBF (Mean Time Between Failures) indicates:", "opts": ["Poor reliability", "High reliability", "High cost"], "ans": "High reliability"}
             ],
             "assignment": "Create a 6-month Preventive Maintenance schedule in Excel for an industrial HVAC Chiller unit."
         }]},
        {"week": "Week 13 – 16", "title": "Energy Efficiency & Auditing", "deliv": "Energy Optimization Strategy", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Lighting and HVAC Optimization",
             "notes": "Energy audits identify waste. Replacing fluorescent lights with LEDs reduces lighting load. Installing Variable Frequency Drives (VFDs) on HVAC fan motors allows them to slow down when full cooling isn't needed, saving massive amounts of power.",
             "quiz": [
                 {"q": "What does a VFD do?", "opts": ["Creates cooling gas", "Varies the speed of an electric motor", "Measures water pressure"], "ans": "Varies the speed of an electric motor"},
                 {"q": "Which lighting technology is most energy-efficient?", "opts": ["Incandescent", "Fluorescent", "LED"], "ans": "LED"},
                 {"q": "HVAC stands for:", "opts": ["Heating, Ventilation, and Air Conditioning", "High Voltage Alternating Current", "Heavy Volume Air Compressor"], "ans": "Heating, Ventilation, and Air Conditioning"},
                 {"q": "Reducing energy waste directly impacts:", "opts": ["CAPEX", "OPEX (Operating Expenses)", "Taxes"], "ans": "OPEX (Operating Expenses)"},
                 {"q": "An energy audit measures:", "opts": ["Employee attendance", "Energy consumption and waste points", "Oil flow rate"], "ans": "Energy consumption and waste points"}
             ],
             "assignment": "Write a proposal to management calculating the ROI of replacing 500 fluorescent tubes with LED panels in the main office."
         }]}
    ],
    "Legal": [
        {"week": "Week 1 – 4", "title": "PIA Framework", "deliv": "PIA Impact Analysis Memo", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Petroleum Industry Act 2021 Overview",
             "notes": "The PIA overhauled Nigeria's oil and gas legal framework. It established two main regulators: NUPRC (Upstream) and NMDPRA (Midstream/Downstream). It transitioned NNPC from a corporation to a limited liability company (NNPC Ltd).",
             "quiz": [
                 {"q": "Under the PIA, NNPC became a:", "opts": ["Government Ministry", "Limited Liability Company (NNPC Ltd)", "Foreign Entity"], "ans": "Limited Liability Company (NNPC Ltd)"},
                 {"q": "Which agency regulates the Upstream sector under PIA?", "opts": ["DPR", "NUPRC", "NMDPRA"], "ans": "NUPRC"},
                 {"q": "Which agency regulates Midstream/Downstream?", "opts": ["NUPRC", "NMDPRA", "CBN"], "ans": "NMDPRA"},
                 {"q": "The PIA mandates the creation of funds for:", "opts": ["Host Communities", "Space Exploration", "Elections"], "ans": "Host Communities"},
                 {"q": "When was the PIA signed into law?", "opts": ["1999", "2015", "2021"], "ans": "2021"}
             ],
             "assignment": "Draft a legal memo summarizing the shift of regulatory powers from the old DPR to the new NUPRC and NMDPRA."
         }]},
        {"week": "Week 5 – 8", "title": "Joint Venture Contracts", "deliv": "JV Legal Contract Brief", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Production Sharing Contracts (PSC) vs JV",
             "notes": "In a Joint Venture (JV), partners share exploration costs and oil produced based on equity stakes. In a Production Sharing Contract (PSC), the IOC bears the exploration cost/risk; if oil is found, they recover costs ('Cost Oil') and share the remaining ('Profit Oil') with the state.",
             "quiz": [
                 {"q": "Who bears the exploration financial risk in a PSC?", "opts": ["The State", "The International Oil Company (IOC)", "The Host Community"], "ans": "The International Oil Company (IOC)"},
                 {"q": "Oil used to pay back the IOC's expenses in a PSC is called:", "opts": ["Profit Oil", "Tax Oil", "Cost Oil"], "ans": "Cost Oil"},
                 {"q": "In a JV, how are costs shared?", "opts": ["IOC pays all", "Based on equity percentage", "Government pays all"], "ans": "Based on equity percentage"},
                 {"q": "What does JOA stand for in Joint Ventures?", "opts": ["Joint Operating Agreement", "Judicial Order of Action", "Joint Oil Allocation"], "ans": "Joint Operating Agreement"},
                 {"q": "Who is usually the non-operating partner in a Nigerian JV?", "opts": ["Shell", "Chevron", "NNPC"], "ans": "NNPC"}
             ],
             "assignment": "Compare the financial risks for NNPC under a standard JV agreement versus a PSC deepwater agreement."
         }]},
        {"week": "Week 9 – 12", "title": "Corporate Governance", "deliv": "Arbitration & Legal Case Study", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Dispute Resolution & Arbitration",
             "notes": "Oil and Gas disputes avoid local courts when possible to ensure neutrality and speed. Arbitration is a binding process where an independent arbitrator rules on the dispute. Clauses for arbitration locations (e.g., London, Paris) are baked into JOAs.",
             "quiz": [
                 {"q": "Why is arbitration preferred over local litigation?", "opts": ["It is cheaper", "Neutrality, confidentiality, and speed", "Local courts do not exist"], "ans": "Neutrality, confidentiality, and speed"},
                 {"q": "Is an arbitral award legally binding?", "opts": ["Yes", "No", "Only if the government agrees"], "ans": "Yes"},
                 {"q": "Where are dispute resolution procedures defined?", "opts": ["In the daily news", "In the contract/JOA clauses", "By the UN"], "ans": "In the contract/JOA clauses"},
                 {"q": "Mediation differs from arbitration because mediation is:", "opts": ["Non-binding", "Binding", "More expensive"], "ans": "Non-binding"},
                 {"q": "A force majeure clause relieves liability for:", "opts": ["Poor financial planning", "Unforeseeable, unavoidable events (e.g., acts of God)", "Employee strikes"], "ans": "Unforeseeable, unavoidable events (e.g., acts of God)"}
             ],
             "assignment": "Review the provided Force Majeure case study. Write a legal opinion on whether a drop in global oil prices qualifies as a Force Majeure event."
         }]},
        {"week": "Week 13 – 16", "title": "Environmental Energy Law", "deliv": "Compliance Checklist", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Gas Flaring Regulations",
             "notes": "Nigeria has stringent laws against routine gas flaring to reduce carbon emissions. The Nigerian Gas Flare Commercialization Programme (NGFCP) aims to eliminate flaring by charging heavy penalties and offering flare sites to third-party investors for commercialization.",
             "quiz": [
                 {"q": "What is the primary purpose of the NGFCP?", "opts": ["Increase gas flaring", "Eliminate routine gas flaring via commercialization", "Export crude oil"], "ans": "Eliminate routine gas flaring via commercialization"},
                 {"q": "What is the penalty for routine flaring?", "opts": ["Warning letters", "Fines per thousand standard cubic feet flared", "No penalty"], "ans": "Fines per thousand standard cubic feet flared"},
                 {"q": "Which environmental guideline governs oil spills?", "opts": ["EGASPIN", "PIA", "Constitution"], "ans": "EGASPIN"},
                 {"q": "Flared gas is primarily composed of:", "opts": ["Oxygen", "Methane", "Nitrogen"], "ans": "Methane"},
                 {"q": "Environmental Impact Assessments (EIA) must be done:", "opts": ["Before project approval", "After project completion", "During decommissioning"], "ans": "Before project approval"}
             ],
             "assignment": "Draft a legal compliance checklist for a flowstation manager outlining the penalties and reporting requirements for gas flaring."
         }]}
    ],
    "Finance": [
        {"week": "Week 1 – 4", "title": "Oil & Gas Cost Accounting", "deliv": "Cost Allocation Audit Report", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Successful Efforts vs Full Cost",
             "notes": "Two main accounting methods for exploration. 'Successful Efforts' capitalizes only the costs of successful wells; dry holes are expensed immediately. 'Full Cost' capitalizes all exploration costs (both successful and dry holes) into the asset pool.",
             "quiz": [
                 {"q": "Which method expenses dry holes immediately?", "opts": ["Full Cost", "Successful Efforts", "Depreciation"], "ans": "Successful Efforts"},
                 {"q": "Which method capitalizes all exploration costs?", "opts": ["Successful Efforts", "Full Cost", "Amortization"], "ans": "Full Cost"},
                 {"q": "Capitalizing a cost means putting it on the:", "opts": ["Income Statement", "Balance Sheet", "Cash Flow Statement"], "ans": "Balance Sheet"},
                 {"q": "Expensing a cost immediately lowers:", "opts": ["Current year profit", "Future depreciation", "Liabilities"], "ans": "Current year profit"},
                 {"q": "DD&A in oil accounting stands for:", "opts": ["Drilling, Design & Analysis", "Depreciation, Depletion & Amortization", "Direct Debt & Assets"], "ans": "Depreciation, Depletion & Amortization"}
             ],
             "assignment": "Given a dataset of 3 drilled wells (2 dry, 1 successful), calculate the total capitalized cost using both the Successful Efforts and Full Cost methods."
         }]},
        {"week": "Week 5 – 8", "title": "JV Cash Calls & Billing", "deliv": "Cash Call Reconciliation Sheet", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Cash Call Operations",
             "notes": "A Cash Call is a request for payment issued by the Joint Venture operator to non-operating partners. It funds upcoming approved OPEX and CAPEX. Failure to pay cash calls results in default, affecting the partner's equity lifting rights.",
             "quiz": [
                 {"q": "Who issues the Cash Call?", "opts": ["The Operator", "The Non-Operator", "The Bank"], "ans": "The Operator"},
                 {"q": "What does a Cash Call fund?", "opts": ["Dividends", "Approved JV OPEX and CAPEX operations", "Employee bonuses"], "ans": "Approved JV OPEX and CAPEX operations"},
                 {"q": "What happens if a partner fails to pay a cash call?", "opts": ["They get a discount", "They enter default status", "Nothing"], "ans": "They enter default status"},
                 {"q": "Joint Interest Billing (JIB) is used to:", "opts": ["Bill the government", "Invoice partners for their share of costs", "Sell oil"], "ans": "Invoice partners for their share of costs"},
                 {"q": "Cash calls are usually based on:", "opts": ["Random estimates", "Approved Work Program and Budget (WP&B)", "Past year profits"], "ans": "Approved Work Program and Budget (WP&B)"}
             ],
             "assignment": "Review a simulated Joint Interest Billing statement and reconcile the Operator's cash call request against the approved quarterly budget."
         }]},
        {"week": "Week 9 – 12", "title": "CAPEX & OPEX Budgeting", "deliv": "Quarterly Budget Forecast Model", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Capital vs Operating Expenditure",
             "notes": "CAPEX refers to money spent acquiring or upgrading physical assets (e.g., building a rig). OPEX refers to day-to-day operational costs (e.g., maintenance, salaries, chemicals). CAPEX is depreciated over time; OPEX is deducted in the current tax year.",
             "quiz": [
                 {"q": "Building a new flowstation is classed as:", "opts": ["OPEX", "CAPEX", "Revenue"], "ans": "CAPEX"},
                 {"q": "Paying monthly salaries to rig workers is:", "opts": ["CAPEX", "OPEX", "Equity"], "ans": "OPEX"},
                 {"q": "Which expenditure is depreciated over the life of the asset?", "opts": ["CAPEX", "OPEX", "Dividends"], "ans": "CAPEX"},
                 {"q": "Routine pump maintenance falls under:", "opts": ["CAPEX", "OPEX", "Capital gains"], "ans": "OPEX"},
                 {"q": "Purchasing a new offshore drilling vessel is:", "opts": ["OPEX", "CAPEX", "Overhead"], "ans": "CAPEX"}
             ],
             "assignment": "Categorize a provided list of 20 expense items into CAPEX and OPEX, and calculate the total projected OPEX budget for the quarter."
         }]},
        {"week": "Week 13 – 16", "title": "Tax Compliance & Audit", "deliv": "Tax Compliance Summary", "status": "🔒 Not Started", "color": "#64748B",
         "subtopics": [{
             "name": "Hydrocarbon Tax & Royalty",
             "notes": "Under the PIA, taxation changed from PPT (Petroleum Profits Tax) to a dual system: Hydrocarbon Tax (HT) and Company Income Tax (CIT). Royalties are paid to the government based on production volume and price, acting as a direct cost before profit calculations.",
             "quiz": [
                 {"q": "What tax replaced PPT for upstream operations under the PIA?", "opts": ["Value Added Tax", "Hydrocarbon Tax (HT)", "Sales Tax"], "ans": "Hydrocarbon Tax (HT)"},
                 {"q": "Royalties are calculated based on:", "opts": ["Net profit", "Production volume and price", "Employee count"], "ans": "Production volume and price"},
                 {"q": "Are royalties paid before or after calculating taxable profit?", "opts": ["Before (it is a deductible expense)", "After", "At the same time"], "ans": "Before (it is a deductible expense)"},
                 {"q": "What does CIT stand for?", "opts": ["Company Income Tax", "Corporate Investment Tariff", "Cash In Transit"], "ans": "Company Income Tax"},
                 {"q": "Who collects royalties in Nigeria?", "opts": ["CBN", "NUPRC", "Commercial Banks"], "ans": "NUPRC"}
             ],
             "assignment": "Using the provided daily production data and global crude price, calculate the monthly Royalty payment owed to the NUPRC."
         }]}
    ]
}

# ==========================================
# 5. SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "department" not in st.session_state: st.session_state["department"] = "Projects"
if "role" not in st.session_state: st.session_state["role"] = ""

# ==========================================
# 6. LOGIN & REGISTRATION INTERFACE
# ==========================================
if not st.session_state["logged_in"]:
    # ---> APPLY LOGIN BACKGROUND HERE <---
    set_background("ai-generated-aerial-view-offshore-drilling-rig-at-the-offshore-location-during-sunset-photo.jpg", "rgba(241, 245, 249, 0.80)")
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
        else:
            st.title("🇳🇬 NNPC")
            
        st.markdown("""
            <div class="card-white" style="margin-top: 15px;">
                <h3 style="margin-top: 0; color: #006837 !important;">NEOL Internship Portal Sign-In</h3>
                <p style="font-size: 0.88rem; color: #64748B !important;">NNPC Eighteen Operating Limited — OML 18 Asset Operations</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab_login, tab_reg = st.tabs(["🔒 Secure Login", "📝 Register User"])
        
        with tab_login:
            with st.form("login_visual_form"):
                uname = st.text_input("Username")
                upass = st.text_input("Password", type="password")
                sub = st.form_submit_button("Launch Dashboard 🚀")
                
                if sub:
                    user_data = authenticate_user(uname, upass)
                    if user_data:
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = uname
                        st.session_state["role"] = user_data[0]
                        st.session_state["department"] = user_data[1]
                        st.session_state["email"] = user_data[2]
                        st.rerun()
                    else:
                        st.error("Invalid Username or Password.")

        with tab_reg:
            with st.form("reg_form"):
                new_uname = st.text_input("Choose Username")
                new_pass = st.text_input("Choose Password", type="password")
                new_email = st.text_input("Corporate Email (@nnpcgroup.com)")
                new_role = st.selectbox("Role", ["IT Student", "Supervisor"])
                new_dept = st.selectbox("Department", list(department_curriculums.keys()))
                if st.form_submit_button("Register Account"):
                    if create_user(new_uname, new_pass, new_role, new_dept, new_email):
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Username already exists.")
else:
    # ---> APPLY DASHBOARD BACKGROUND HERE <---
    set_background("istockphoto-1457436123-612x612.jpg", "rgba(241, 245, 249, 0.90)")

    # ==========================================
    # 7. SIDEBAR NAVIGATION
    # ==========================================
    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
        else:
            st.markdown("### 🇳🇬 NNPC")
            
        st.markdown(f"**👤 {st.session_state['username']}**<br><span style='font-size: 0.8rem;'>{st.session_state['role']} | {st.session_state['department']}</span>", unsafe_allow_html=True)
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        if st.session_state["role"] == "IT Student":
            nav_options = [
                "Dashboard", "Curriculum", "Master Schedule", "Submissions", 
                "Help Desk", "Onboarding Deck", "Attendance", "Reports", "Export Official Logbook", "Settings"
            ]
        else:
            nav_options = [
                "Supervisor Dashboard", "Review Deliverables", "Attendance & Risk", 
                "Quiz Analytics", "Broadcasts & Tickets", "Curriculum Controls", "Export Reports"
            ]
            
        selected_nav = st.radio("Navigation", nav_options, label_visibility="collapsed")
        
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="background-color: rgba(255,255,255,0.08); padding: 15px; border-radius: 10px; border-left: 3px solid #FFD100;">
                <p style="color: #FFFFFF !important; font-size: 0.85rem; font-style: italic; margin: 0;">
                "Empowering Young Minds, Building a Greater Energy Future."
                </p>
                <p style="color: #FFD100 !important; font-size: 0.75rem; margin-top: 5px; margin-bottom: 0;">— NNPC</p>
            </div>
        """, unsafe_allow_html=True)
        
        if st.button("🚪 Secure Logout", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    # ==========================================
    # 8. TOP NAVBAR
    # ==========================================
    top_col1, top_col2, top_col3, top_col4 = st.columns([3.5, 1, 1, 1.5])
    with top_col1:
        st.markdown(f"""
            <div class="top-greeting" style="margin-top: 5px;">
                <span style="font-size: 0.95rem; color: #475569 !important;">Welcome back,</span><br>
                <span style="font-size: 1.6rem; font-weight: 700; color: #006837 !important;">{st.session_state['username']} 👋</span><br>
                <span style="font-size: 0.85rem; color: #64748B !important;">{st.session_state['role']} Portal</span>
            </div>
        """, unsafe_allow_html=True)
    with top_col3:
        st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='font-size: 1.3rem;'>🔔 🌙</span></div>", unsafe_allow_html=True)
    with top_col4:
        if st.session_state["role"] == "IT Student":
            selected_dept_dropdown = st.selectbox("Profile Dept", list(department_curriculums.keys()), index=list(department_curriculums.keys()).index(st.session_state['department']), label_visibility="collapsed")
            st.session_state['department'] = selected_dept_dropdown

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 9. ROUTING PAGE VIEWS (STUDENT)
    # ==========================================
    if st.session_state["role"] == "IT Student":
        if selected_nav == "Dashboard":
            start_date = date(2026, 10, 1)
            end_date = date(2027, 1, 25)
            today = date.today()

            days_left = max(0, (end_date - today).days)
            total_days = (end_date - start_date).days
            days_passed = (today - start_date).days
            progress_pct = max(0, min(int((days_passed / total_days) * 100), 100))

            # Fetch dynamic metrics from DB
            db_att = fetch_data("SELECT id FROM attendance WHERE username = ?", (st.session_state["username"],))
            att_count = len(db_att)
            att_pct = int((att_count/16)*100) if att_count > 0 else 0
            
            db_subs = fetch_data("SELECT id FROM submissions WHERE username = ?", (st.session_state["username"],))
            sub_count = len(db_subs)

            col_hb1, col_hb2 = st.columns([3.2, 1.8])
            with col_hb1:
                st.markdown("""
                    <div class="hero-banner">
                        <h2 style="margin-top: 0; font-size: 1.8rem;">NNPC Eighteen Operating Limited (NEOL)</h2>
                        <p style="font-size: 1.05rem; margin-bottom: 20px;">Internship Portal — OML 18 Asset Operations</p>
                        <span style="background-color: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">
                        Learn &nbsp;|&nbsp; Contribute &nbsp;|&nbsp; Build Your Future
                        </span>
                    </div>
                """, unsafe_allow_html=True)
            with col_hb2:
                st.markdown(f"""
                    <div class="hero-banner" style="padding: 20px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-size: 0.85rem; color: #FFD100 !important; font-weight: bold;">📅 Internship Duration</span>
                            <span style="font-size: 0.85rem; background: #006837; padding: 2px 8px; border-radius: 10px; color: white !important;">Active</span>
                        </div>
                        <h3 style="margin: 8px 0 4px 0; font-size: 1.5rem; color: #FFFFFF !important;">16 Weeks</h3>
                        <p style="font-size: 0.78rem; color: #D0D0D0 !important; margin: 0;">Oct 1, 2026 – Jan 25, 2027</p>
                        <hr style="border-color: rgba(255,255,255,0.2); margin: 10px 0;">
                        <div style="font-size: 0.78rem; display: flex; justify-content: space-between;">
                            <span style="color: #FFFFFF !important;">Overall Progress</span>
                            <span style="color: #FFD100 !important; font-weight: bold;">{progress_pct}%</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

            m1, m2, m3, m4, m5 = st.columns(5)
            with m1:
                st.markdown(f"""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">ATTENDANCE</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{att_pct}%</h3>
                        <span style="font-size: 0.72rem; color: #64748B !important;">{att_count} days</span>
                    </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">DELIVERABLES</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{sub_count}</h3>
                        <span style="font-size: 0.72rem; color: #D97706 !important;">Total Uploaded</span>
                    </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown("""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">ASSIGNMENTS</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">2 / 4</h3>
                        <span style="font-size: 0.72rem; color: #2563EB !important;">In Progress: 2</span>
                    </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown("""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">COURSES</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">4 / 5</h3>
                        <span style="font-size: 0.72rem; color: #64748B !important;">Completed: 4</span>
                    </div>
                """, unsafe_allow_html=True)
            with m5:
                st.markdown(f"""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">DAYS LEFT</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{days_left}</h3>
                        <span style="font-size: 0.72rem; color: #64748B !important;">Until Jan 25, 2027</span>
                    </div>
                """, unsafe_allow_html=True)

            body_col1, body_col2 = st.columns([2.3, 1])

            with body_col1:
                current_dept = st.session_state['department']
                active_curr = department_curriculums.get(current_dept, department_curriculums["Projects"])

                st.markdown(f"""
                    <div class="card-white">
                        <div style="margin-bottom: 12px;">
                            <h4 style="margin: 0; color: #002B15 !important;">📖 My Curriculum</h4>
                            <p style="margin: 0; font-size: 0.8rem; color: #475569 !important;">16-Week Training Roadmap — <b style="color: #006837 !important;">{current_dept} Department</b></p>
                        </div>
                """, unsafe_allow_html=True)
                
                c_cols = st.columns(4)
                for i, phase in enumerate(active_curr):
                    with c_cols[i]:
                        st.markdown(f"""
                            <div class="curr-box">
                                <span style="font-size: 0.72rem; color: #006837 !important; font-weight: bold;">{phase['week']}</span>
                                <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0; color: #0F172A !important;">{phase['title']}</p>
                                <hr style="margin: 6px 0; border-color: #CBD5E1;">
                                <span style="font-size: 0.7rem; color: #334155 !important;">{phase['deliv']}</span><br>
                                <span style="color: {phase['color']} !important; font-size: 0.72rem; font-weight: bold;">{phase['status']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                ov_col1, ov_col2 = st.columns([1, 1.7])
                with ov_col1:
                    st.markdown(f"""
                        <div class="card-white">
                            <h4 style="margin: 0 0 10px 0; font-size: 1rem; color: #002B15 !important;">📌 Internship Overview</h4>
                            <div style="font-size: 0.8rem;">
                                <p style="margin: 6px 0;"><b style="color: #0F172A !important;">Duration:</b> 16 Weeks</p>
                                <p style="margin: 6px 0;"><b style="color: #0F172A !important;">Start Date:</b> Oct 1, 2026</p>
                                <p style="margin: 6px 0;"><b style="color: #0F172A !important;">End Date:</b> Jan 25, 2027</p>
                                <p style="margin: 6px 0;"><b style="color: #0F172A !important;">Department:</b> {current_dept}</p>
                                <p style="margin: 6px 0;"><b style="color: #0F172A !important;">Supervisor:</b> To be assigned</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with ov_col2:
                    st.markdown("""
                        <div class="card-white">
                            <h4 style="margin: 0 0 5px 0; font-size: 1rem; color: #002B15 !important;">📅 Master Schedule & Milestones</h4>
                            <p style="margin: 0 0 8px 0; font-size: 0.75rem; color: #64748B !important;">16-Week OML 18 Roadmap</p>
                    """, unsafe_allow_html=True)
                    
                    schedule_data = pd.DataFrame([
                        {"Task": "General IT Orientation & HSE Briefing", "Start": "2026-10-01", "Finish": "2026-10-07", "Category": "Milestone"},
                        {"Task": "Departmental Onboarding & System Setup", "Start": "2026-10-08", "Finish": "2026-10-15", "Category": "Training"},
                        {"Task": "Phase 1 Progress Review & Logbook Check", "Start": "2026-10-28", "Finish": "2026-10-30", "Category": "Assessment"},
                        {"Task": "Field Logistics Base Visit (Alakiri/Cawthorne)", "Start": "2026-11-10", "Finish": "2026-11-17", "Category": "Field Visit"},
                        {"Task": "Mid-Term Technical Presentation", "Start": "2026-11-25", "Finish": "2026-11-27", "Category": "Assessment"},
                        {"Task": "Advanced Technical Mentorship", "Start": "2026-12-01", "Finish": "2026-12-20", "Category": "Training"},
                        {"Task": "Final Internship Capstone Defense", "Start": "2027-01-15", "Finish": "2027-01-18", "Category": "Milestone"},
                        {"Task": "Logbook Submission & Exit Closeout", "Start": "2027-01-20", "Finish": "2027-01-25", "Category": "Deadline"}
                    ])
                    fig_gantt = px.timeline(
                        schedule_data, x_start="Start", x_end="Finish", y="Task", color="Category",
                        color_discrete_map={"Milestone": "#FFD100", "Training": "#006837", "Assessment": "#00381C", "Field Visit": "#00A859", "Deadline": "#D32F2F"}
                    )
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(
                        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(color='#0F172A', size=11), height=260, margin=dict(t=5, b=5, l=5, r=5)
                    )
                    st.plotly_chart(fig_gantt, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.markdown("""
                        <div class="card-white">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; font-size: 0.95rem; color: #002B15 !important;">Attendance Overview</h4>
                                <span style="font-size: 0.75rem; color: #006837 !important; font-weight: bold;">View Details →</span>
                            </div>
                    """, unsafe_allow_html=True)
                    att_col1, att_col2 = st.columns([1, 1.5])
                    with att_col1:
                        st.markdown(f"""
                            <div style="text-align: center; padding-top: 15px;">
                                <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">{att_pct}%</h2>
                                <p style="font-size: 0.72rem; margin: 0; color: #475569 !important;">🟢 Present</p>
                                <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px; color: #0F172A !important;">{att_count} days</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with att_col2:
                        att_chart_data = pd.DataFrame({
                            "Week": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
                            "Days": [5, 5, 4, 5, 4, 5, 5, 4]
                        })
                        fig_att = px.bar(att_chart_data, x="Week", y="Days", color_discrete_sequence=["#006837"])
                        fig_att.update_layout(
                            template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#0F172A'), height=130, margin=dict(t=5, b=5, l=5, r=5), 
                            xaxis_title=None, yaxis_title=None
                        )
                        st.plotly_chart(fig_att, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

                with b_col2:
                    st.markdown("""
                        <div class="card-white">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <h4 style="margin: 0; font-size: 0.95rem; color: #002B15 !important;">Deliverables Progress</h4>
                                <span style="font-size: 0.75rem; color: #006837 !important; font-weight: bold;">View All →</span>
                            </div>
                    """, unsafe_allow_html=True)
                    del_col1, del_col2 = st.columns([1, 1.4])
                    with del_col1:
                        st.markdown(f"""
                            <div style="text-align: center; padding-top: 15px;">
                                <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">{sub_count}</h2>
                                <p style="font-size: 0.72rem; margin: 0; color: #475569 !important;">✓ Uploaded</p>
                            </div>
                        """, unsafe_allow_html=True)
                    with del_col2:
                        st.markdown("""
                            <div style="font-size: 0.75rem; padding-top: 5px;">
                                <p style="margin: 4px 0; color: #0F172A !important;">✔️ Regulatory Summary</p>
                                <p style="margin: 4px 0; color: #0F172A !important;">✔️ Cost Model</p>
                                <p style="margin: 4px 0; color: #D97706 !important;">🟡 Schedule Report</p>
                                <p style="margin: 4px 0; color: #94A3B8 !important;">⚪ Final Report</p>
                            </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            with body_col2:
                # Dynamic Announcement Banner
                latest_announcement = fetch_data("SELECT message, date, author FROM announcements ORDER BY id DESC LIMIT 1")
                if not latest_announcement.empty:
                    ann_msg = latest_announcement.iloc[0]['message']
                    ann_date = latest_announcement.iloc[0]['date']
                    ann_auth = latest_announcement.iloc[0]['author']
                else:
                    ann_msg = "Next Departmental Review is scheduled for Oct 28 – Oct 30. Ensure your logbooks are updated."
                    ann_date = "System Default"
                    ann_auth = "Admin"

                st.markdown(f"""
                    <div class="card-white" style="border-left: 4px solid #FFD100 !important;">
                        <h4 style="margin: 0 0 8px 0; color: #002B15 !important;">📢 Global Broadcast</h4>
                        <p style="font-size: 0.75rem; color: #64748B !important; margin: 0 0 8px 0;">From {ann_auth} • {ann_date}</p>
                        <p style="font-size: 0.85rem; font-weight: 500; margin: 0; color: #0F172A !important;">{ann_msg}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin: 0 0 12px 0; color: #002B15 !important;">⚡ Quick Actions</h4>
                """, unsafe_allow_html=True)
                if st.button("➕ Add Attendance", use_container_width=True):
                    if record_attendance(st.session_state["username"], st.session_state["department"]):
                        st.success("Attendance marked for today!")
                    else:
                        st.warning("Already clocked in today.")
                if st.button("📤 Submit Deliverable", use_container_width=True):
                    st.info("Navigate to the Submissions page via sidebar.")
                if st.button("📊 View Reports", use_container_width=True):
                    st.info("Loading weekly report analytics...")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin: 0 0 10px 0; color: #002B15 !important;">🕒 Recent DB Activity</h4>
                        <ul style="padding-left: 15px; font-size: 0.8rem; margin: 0;">
                            <li><b style="color: #0F172A !important;">System Updated</b><br><span style="color: #64748B !important;">Live DB Connected</span></li>
                            <hr style="margin: 6px 0; border-color: #CBD5E1;">
                            <li><b style="color: #0F172A !important;">Profile Active</b><br><span style="color: #64748B !important;">Online</span></li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                    <div style="background: linear-gradient(135deg, #002B15 0%, #004D25 100%); padding: 18px; border-radius: 12px; color: white !important; text-align: center;">
                        <p style="font-size: 0.82rem; font-weight: bold; color: #FFD100 !important; margin: 0 0 5px 0;">Grow. Learn. Make an Impact.</p>
                        <p style="font-size: 0.72rem; color: #E0E0E0 !important; margin: 0 0 10px 0;">Your skills today power the energy of tomorrow.</p>
                        <span style="font-size: 0.68rem; color: #CBD5E1 !important;">— NNPC</span>
                    </div>
                """, unsafe_allow_html=True)

        elif selected_nav == "Curriculum":
            current_dept = st.session_state['department']
            st.subheader(f"📖 Interactive Learning Module — {current_dept} Department")

            active_curr = department_curriculums.get(current_dept, [])

            for phase_idx, phase in enumerate(active_curr):
                # Verify lock status
                lock_status = fetch_data("SELECT is_locked FROM module_locks WHERE department=? AND week=?", (current_dept, phase['week']))
                is_locked = lock_status.iloc[0]['is_locked'] if not lock_status.empty else 0

                if is_locked:
                    with st.expander(f"🔒 {phase['week']}: {phase['title']} (Locked by Supervisor)"):
                        st.warning("This module is currently locked by your supervisor to prevent skipping ahead in the curriculum.")
                else:
                    with st.expander(f"📍 {phase['week']}: {phase['title']} ({phase['status']})"):
                        st.markdown(f"**Main Weekly Deliverable:** `{phase['deliv']}`")
                        st.markdown("---")

                        if "subtopics" in phase:
                            for sub_idx, sub in enumerate(phase["subtopics"]):
                                st.markdown(f"<h4 style='color: #006837 !important;'>🔹 Subtopic: {sub['name']}</h4>", unsafe_allow_html=True)

                                tab1, tab2, tab3 = st.tabs(["📝 Lecture Notes", "🧠 Knowledge Check Quiz", "📋 Assignment"])

                                with tab1:
                                    st.info(f"**Study Notes:**\n\n{sub['notes']}")

                                with tab2:
                                    st.markdown("#### 🎯 5-Question Quiz")
                                    with st.form(key=f"quiz_form_{phase_idx}_{sub_idx}"):
                                        user_answers = []
                                        for q_idx, q_data in enumerate(sub["quiz"]):
                                            st.write(f"**Q{q_idx+1}:** {q_data['q']}")
                                            ans = st.radio("Select:", q_data["opts"], key=f"q_{phase_idx}_{sub_idx}_{q_idx}", label_visibility="collapsed")
                                            user_answers.append((ans, q_data["ans"]))
                                            st.write("")

                                        submitted = st.form_submit_button("Submit Quiz to Supervisor Server")
                                        if submitted:
                                            score = sum([1 for user_ans, correct_ans in user_answers if user_ans == correct_ans])
                                            execute_query("INSERT INTO quiz_scores (username, department, week, subtopic, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                                          (st.session_state["username"], st.session_state["department"], phase['week'], sub['name'], score, len(sub["quiz"]), str(date.today())))
                                            if score == len(sub["quiz"]):
                                                st.success(f"🎉 Perfect Score! {score}/{len(sub['quiz'])}. Saved to Database.")
                                                st.balloons()
                                            elif score >= (len(sub["quiz"])/2):
                                                st.warning(f"👍 Good job! You scored {score}/{len(sub['quiz'])}. Saved to Database.")
                                            else:
                                                st.error(f"📉 You scored {score}/{len(sub['quiz'])}. Saved to Database. Please review notes.")

                                with tab3:
                                    st.warning(f"**Task Instructions:**\n\n{sub['assignment']}")
                                    if st.button("📤 Upload Completed Assignment", key=f"btn_{phase_idx}_{sub_idx}"):
                                        st.success("Navigate to the **Submissions** tab to upload your file!")

        elif selected_nav == "Help Desk":
            st.subheader("🎫 IT / Supervisor Help Desk & Ticketing")
            
            with st.form("ticket_form"):
                st.markdown("#### Open a New Ticket")
                t_sub = st.text_input("Subject (e.g., 'Need help with Primavera assignment')")
                t_msg = st.text_area("Message")
                if st.form_submit_button("Submit Ticket"):
                    execute_query("INSERT INTO tickets (username, subject, message, status, reply, date) VALUES (?, ?, ?, 'Open', '', ?)",
                                  (st.session_state["username"], t_sub, t_msg, str(date.today())))
                    st.success("Ticket submitted to supervisors.")
            
            st.markdown("#### Your Ticket History")
            my_tickets = fetch_data("SELECT id AS ID, subject AS Subject, status AS Status, reply AS Supervisor_Reply, date AS Date FROM tickets WHERE username=? ORDER BY id DESC", (st.session_state["username"],))
            st.dataframe(my_tickets, use_container_width=True)

        elif selected_nav == "Master Schedule":
            st.subheader("📅 OML 18 Master Internship Schedule & Roadmap")
            st.markdown("""
                <div class="card-white">
                    <h4 style="margin-top: 0;">16-Week Master Roadmap Timeline</h4>
                    <p style="font-size: 0.85rem;">Interactive Gantt Chart tracking orientation, milestones, assessments, and field visits across the 16-week cycle.</p>
                </div>
            """, unsafe_allow_html=True)
            
            schedule_data = pd.DataFrame([
                {"Task": "General IT Orientation & HSE Briefing", "Start": "2026-10-01", "Finish": "2026-10-07", "Category": "Milestone"},
                {"Task": "Departmental Onboarding & System Setup", "Start": "2026-10-08", "Finish": "2026-10-15", "Category": "Training"},
                {"Task": "Phase 1 Progress Review & Logbook Check", "Start": "2026-10-28", "Finish": "2026-10-30", "Category": "Assessment"},
                {"Task": "Field Logistics Base Visit (Alakiri/Cawthorne)", "Start": "2026-11-10", "Finish": "2026-11-17", "Category": "Field Visit"},
                {"Task": "Mid-Term Technical Presentation", "Start": "2026-11-25", "Finish": "2026-11-27", "Category": "Assessment"},
                {"Task": "Advanced Technical Mentorship", "Start": "2026-12-01", "Finish": "2026-12-20", "Category": "Training"},
                {"Task": "Final Internship Capstone Defense", "Start": "2027-01-15", "Finish": "2027-01-18", "Category": "Milestone"},
                {"Task": "Logbook Submission & Exit Closeout", "Start": "2027-01-20", "Finish": "2027-01-25", "Category": "Deadline"}
            ])
            
            fig_gantt_full = px.timeline(
                schedule_data, x_start="Start", x_end="Finish", y="Task", color="Category",
                color_discrete_map={"Milestone": "#FFD100", "Training": "#006837", "Assessment": "#00381C", "Field Visit": "#00A859", "Deadline": "#D32F2F"}
            )
            fig_gantt_full.update_yaxes(autorange="reversed")
            fig_gantt_full.update_layout(
                template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#0F172A', size=12), height=380
            )
            st.plotly_chart(fig_gantt_full, use_container_width=True)

        elif selected_nav in ["Submissions", "Deliverables"]:
            st.subheader(f"📤 {selected_nav} & Logbook Submission Portal")
            
            col_s1, col_s2 = st.columns([1, 1.2])
            with col_s1:
                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin-top: 0;">Submit Weekly Report / Deliverable</h4>
                        <p style="font-size: 0.85rem;">Upload your weekly task summary, code, or PDF reports for supervisor review.</p>
                    </div>
                """, unsafe_allow_html=True)
                
                with st.form("weekly_sub_form"):
                    week_num = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 17)])
                    rep_topic = st.text_input("Report Title / Topic", placeholder="e.g. FEED & Costing Analysis")
                    rep_file = st.file_uploader("Upload Deliverable Document (PDF, PPTX)", type=['pdf', 'pptx', 'docx'])
                    submit_btn = st.form_submit_button("Submit Deliverable 🚀")
                    
                    if submit_btn and rep_topic and rep_file:
                        execute_query("INSERT INTO submissions (username, department, week, topic, filename, filedata, date, status, grade, feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (st.session_state["username"], st.session_state["department"], week_num, rep_topic, rep_file.name, rep_file.getvalue(), str(date.today()), "Pending Review", "Ungraded", ""))
                        st.success(f"Deliverable for {week_num} successfully uploaded to DB!")

                st.markdown("#### 📜 Submitted Logbook History")
                db_subs = fetch_data("SELECT week AS Week, topic AS Topic, date AS Date, status AS Status, grade as Grade FROM submissions WHERE username = ?", (st.session_state["username"],))
                st.dataframe(db_subs if not db_subs.empty else pd.DataFrame({"Notice": ["No submissions yet."]}), use_container_width=True)

            with col_s2:
                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin-top: 0;">👁️ Interactive PDF Live Viewer</h4>
                    </div>
                """, unsafe_allow_html=True)
                if 'rep_file' in locals() and rep_file is not None:
                    if rep_file.name.endswith('.pdf'):
                        st.info(f"Previewing `{rep_file.name}`:")
                        render_pdf_viewer(rep_file.getvalue())
                    else:
                        st.warning("Inline preview is optimized for PDF files.")
                else:
                    st.info("Upload a PDF deliverable on the left to view it live in this window.")

        elif selected_nav == "Onboarding Deck":
            st.subheader("🖼️ NEOL Employee Onboarding & Orientation Handbook")
            col_o1, col_o2 = st.columns([1, 1.2])
            with col_o1:
                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin-top: 0;">OML 18 Orientation Deck</h4>
                        <p style="font-size: 0.85rem;">Review standard operating guidelines, HSE rules, STAT-P core values, and organizational contacts.</p>
                    </div>
                """, unsafe_allow_html=True)
                deck_file = st.file_uploader("Upload Handbook PDF / Slide Deck", type=['pdf', 'pptx'])
                st.markdown("""
                    <div class="card-white">
                        <h4>📞 Key Support Contacts</h4>
                        <ul style="font-size: 0.85rem; padding-left: 15px;">
                            <li><b>Human Capital:</b> Mrs. Terdoo Ajayi (0806 890 8317)</li>
                            <li><b>IT Support:</b> Mr. Oghenetejiri Okoro (0909 347 8095)</li>
                            <li><b>HSSE Officer:</b> Mrs. Doris Osuji (0813 359 3746)</li>
                            <li><b>Facility Mgmt:</b> Mr. David Amaju (0812 751 9856)</li>
                        </ul>
                    </div>
                """, unsafe_allow_html=True)

            with col_o2:
                if deck_file is not None and deck_file.name.endswith('.pdf'):
                    st.info(f"Previewing `{deck_file.name}`:")
                    render_pdf_viewer(deck_file.getvalue())
                else:
                    st.info("Upload a PDF handbook on the left to preview slides here.")

        elif selected_nav == "Attendance":
            st.subheader("⏰ Daily Attendance & Clock-In Register")
            col_a1, col_a2 = st.columns([1, 1.5])
            with col_a1:
                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin-top: 0;">Clock In for Today</h4>
                        <p style="font-size: 0.85rem;">Punctuality Rule: Head office resume time is 07:30 AM WAT.</p>
                    </div>
                """, unsafe_allow_html=True)
                if st.button("📍 Clock In Now", use_container_width=True):
                    if record_attendance(st.session_state["username"], st.session_state["department"]):
                        st.success("Attendance successfully recorded for today!")
                    else:
                        st.warning("You have already clocked in today.")

            with col_a2:
                st.markdown("#### DB Attendance Log History")
                att_df = fetch_data("SELECT date AS Date, time AS Time, status AS Status FROM attendance WHERE username = ? ORDER BY id DESC", (st.session_state["username"],))
                st.dataframe(att_df if not att_df.empty else pd.DataFrame({"Notice": ["No records found."]}), use_container_width=True)

        elif selected_nav == "Reports":
            st.subheader("📊 Analytics & Weekly Performance Reports")
            rep_df = pd.DataFrame({
                "Department": ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"],
                "Avg Completion (%)": [39, 72, 20, 85, 45, 65]
            })
            fig_rep = px.bar(rep_df, x="Department", y="Avg Completion (%)", color="Department", color_discrete_sequence=["#006837", "#FFD100", "#00A859", "#00381C", "#0B6623", "#2563EB"])
            fig_rep.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#0F172A'), height=350)
            st.plotly_chart(fig_rep, use_container_width=True)

        elif selected_nav == "Export Official Logbook":
            st.subheader("📄 Generate Official NNPC IT Logbook")
            st.markdown("""<div class="card-white"><p>Compile your DB attendance, quiz scores, and deliverable grades into an official PDF ready for university submission.</p></div>""", unsafe_allow_html=True)
            
            pdf_bytes = generate_logbook_pdf(st.session_state["username"], st.session_state["department"])
            st.download_button(label="📥 Download Official Logbook PDF", data=pdf_bytes, file_name=f"NNPC_Logbook_{st.session_state['username']}.pdf", mime="application/pdf", use_container_width=True)

        elif selected_nav == "Settings":
            st.subheader("⚙️ Portal Settings & User Preferences")
            st.markdown("""
                <div class="card-white">
                    <h4 style="margin-top: 0;">User Profile Configuration</h4>
                </div>
            """, unsafe_allow_html=True)
            st.text_input("Full Name", value=st.session_state["username"], disabled=True)
            st.text_input("Assigned Department", value=st.session_state["department"], disabled=True)
            st.text_input("Official Corporate Email", value=f"{st.session_state['username'].lower().replace(' ', '.')}@nnpcgroup.com")
            if st.button("Save Profile Settings"):
                st.success("Profile updated successfully!")

    # ==========================================
    # 10. ROUTING PAGE VIEWS (SUPERVISOR)
    # ==========================================
    elif st.session_state["role"] == "Supervisor":
        if selected_nav == "Supervisor Dashboard":
            st.markdown("""
                <div class="hero-banner">
                    <h2 style="margin-top: 0;">Supervisor Control Center</h2>
                    <p>Manage student deliverables, audit attendance, and monitor performance analytics.</p>
                </div>
            """, unsafe_allow_html=True)

            # AT-A-GLANCE METRICS
            total_students = fetch_data("SELECT COUNT(*) as count FROM users WHERE role='IT Student'").iloc[0]['count']
            pending_actions = fetch_data("SELECT COUNT(*) as count FROM submissions WHERE status='Pending Review'").iloc[0]['count']
            avg_score_df = fetch_data("SELECT AVG(score * 100.0 / total) as avg FROM quiz_scores")
            avg_score = round(avg_score_df.iloc[0]['avg'], 1) if not avg_score_df.empty and pd.notna(avg_score_df.iloc[0]['avg']) else 0

            c1, c2, c3 = st.columns(3)
            c1.markdown(f"""
                <div class="metric-card-white" style="border-left: 5px solid #2563EB !important;">
                    <h4 style="margin:0; color:#64748B;">Total Active Interns</h4>
                    <h2 style="margin:5px 0; color:#0F172A;">{total_students}</h2>
                </div>
            """, unsafe_allow_html=True)
            c2.markdown(f"""
                <div class="metric-card-white" style="border-left: 5px solid #D97706 !important;">
                    <h4 style="margin:0; color:#64748B;">Pending Deliverables</h4>
                    <h2 style="margin:5px 0; color:#0F172A;">{pending_actions}</h2>
                </div>
            """, unsafe_allow_html=True)
            c3.markdown(f"""
                <div class="metric-card-white" style="border-left: 5px solid #006837 !important;">
                    <h4 style="margin:0; color:#64748B;">Avg Cohort Quiz Score</h4>
                    <h2 style="margin:5px 0; color:#0F172A;">{avg_score}%</h2>
                </div>
            """, unsafe_allow_html=True)

        elif selected_nav == "Review Deliverables":
            st.subheader("👨‍💼 Grade Student Submissions")
            all_subs = fetch_data("SELECT id, username AS Student, department AS Dept, week AS Week, topic AS Topic, status AS Status, grade AS Grade FROM submissions")
            st.dataframe(all_subs, use_container_width=True)
            
            st.markdown("### 📝 Grade a Submission")
            if not all_subs.empty:
                sub_id = st.selectbox("Select Submission ID", all_subs["id"].tolist())
                with st.form("grade_form"):
                    new_status = st.selectbox("Status", ["Approved", "Needs Revision", "Under Review"])
                    new_grade = st.selectbox("Grade", ["A", "B", "C", "Fail"])
                    new_feedback = st.text_area("Feedback Comments")
                    if st.form_submit_button("Save Grade"):
                        execute_query("UPDATE submissions SET status = ?, grade = ?, feedback = ? WHERE id = ?", (new_status, new_grade, new_feedback, sub_id))
                        st.success("Grade updated successfully!")
                        st.rerun()
            else:
                st.info("No deliverables submitted yet.")

        elif selected_nav == "Attendance & Risk":
            st.subheader("🚩 At-Risk Students & Global Attendance Audit")
            st.markdown("Identifies students with less than 75% attendance relative to the 16-week cycle expectation.")
            
            all_users = fetch_data("SELECT username, department FROM users WHERE role='IT Student'")
            risk_data = []
            for _, row in all_users.iterrows():
                att = fetch_data("SELECT COUNT(*) as c FROM attendance WHERE username=?", (row['username'],)).iloc[0]['c']
                # Assume 16 total days for testing algorithm
                att_pct = min(100, int((att / 16) * 100))
                risk_flag = "🚨 High Risk" if att_pct < 75 else "✅ Good"
                risk_data.append({"Student": row['username'], "Dept": row['department'], "Attendance %": att_pct, "Status": risk_flag})
            
            st.dataframe(pd.DataFrame(risk_data), use_container_width=True)

        elif selected_nav == "Quiz Analytics":
            st.subheader("🏆 Global Quiz Analytics & Leaderboard")
            leaderboard = fetch_data("SELECT username AS Student, department AS Dept, SUM(score) AS Total_Score FROM quiz_scores GROUP BY username ORDER BY Total_Score DESC")
            if not leaderboard.empty:
                col1, col2 = st.columns([1, 1.5])
                with col1:
                    st.markdown("#### 🥇 Top Students")
                    st.dataframe(leaderboard, use_container_width=True)
                with col2:
                    st.markdown("#### 📈 Scores by Department")
                    fig = px.bar(leaderboard, x="Dept", y="Total_Score", color="Student", barmode="group", color_discrete_sequence=px.colors.sequential.Greens_r)
                    fig.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='#0F172A'))
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quiz data available yet.")

        elif selected_nav == "Broadcasts & Tickets":
            st.subheader("📢 Communications Center")
            tab1, tab2 = st.tabs(["Global Broadcasts", "Student Tickets"])
            
            with tab1:
                with st.form("announcement_form"):
                    st.markdown("#### Post an Announcement Banner")
                    msg = st.text_area("Message to Broadcast (Shows on student dashboard)")
                    if st.form_submit_button("Broadcast to All Students"):
                        execute_query("INSERT INTO announcements (message, date, author) VALUES (?, ?, ?)",
                                      (msg, str(date.today()), st.session_state["username"]))
                        st.success("Broadcast sent successfully!")
            
            with tab2:
                st.markdown("#### Manage Student Tickets")
                tickets_df = fetch_data("SELECT id, username, subject, message, status FROM tickets WHERE status='Open'")
                st.dataframe(tickets_df, use_container_width=True)
                
                if not tickets_df.empty:
                    with st.form("reply_form"):
                        t_id = st.selectbox("Select Ticket ID to Resolve", tickets_df['id'].tolist())
                        reply = st.text_area("Reply / Resolution")
                        if st.form_submit_button("Close Ticket"):
                            execute_query("UPDATE tickets SET status='Closed', reply=? WHERE id=?", (reply, t_id))
                            st.success("Ticket updated and closed.")
                            st.rerun()

        elif selected_nav == "Curriculum Controls":
            st.subheader("🔐 Administrative Curriculum Lock/Unlock")
            st.markdown("Prevent students from rushing ahead by locking future weekly modules.")
            
            dept_select = st.selectbox("Select Department", list(department_curriculums.keys()))
            actual_weeks = [phase["week"] for phase in department_curriculums.get(dept_select, [])]
            
            with st.form("lock_form"):
                target_week = st.selectbox("Target Module", actual_weeks)
                action = st.radio("Action", ["Lock", "Unlock"])
                
                if st.form_submit_button("Apply Action"):
                    is_locked = 1 if action == "Lock" else 0
                    execute_query("INSERT OR REPLACE INTO module_locks (department, week, is_locked) VALUES (?, ?, ?)",
                                  (dept_select, target_week, is_locked))
                    st.success(f"{action}ed {target_week} for {dept_select} Department.")

        elif selected_nav == "Export Reports":
            st.subheader("📑 Generate & Export Cohort Data")
            st.markdown("Export SQLite tables to Excel-compatible CSV files.")
            
            users_csv = fetch_data("SELECT username, department, email FROM users WHERE role='IT Student'").to_csv(index=False)
            st.download_button("📥 Export Student Roster (CSV)", users_csv, "nnpc_interns.csv", "text/csv")
            
            att_csv = fetch_data("SELECT * FROM attendance").to_csv(index=False)
            st.download_button("📥 Export Global Attendance Log (CSV)", att_csv, "nnpc_attendance.csv", "text/csv")
            
            grades_csv = fetch_data("SELECT username, department, week, topic, grade FROM submissions").to_csv(index=False)
            st.download_button("📥 Export Deliverable Grades (CSV)", grades_csv, "nnpc_grades.csv", "text/csv")
