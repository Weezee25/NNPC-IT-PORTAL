import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
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

# Helper function to set base64 backgrounds dynamically with robust CSS overrides for Light & Dark mode
def set_background(image_path):
    if not os.path.exists(image_path):
        st.markdown("""<style>[data-testid="stAppViewContainer"], .stApp { background-color: var(--background-color) !important; }</style>""", unsafe_allow_html=True)
        return

    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    
    st.markdown(f"""
    <style>
    /* Light Mode Background Overlay */
    @media (prefers-color-scheme: light) {{
        [data-testid="stAppViewContainer"], .stApp {{
            background-image: linear-gradient(rgba(241, 245, 249, 0.90), rgba(241, 245, 249, 0.90)), url("data:image/jpeg;base64,{encoded}") !important;
        }}
    }}
    /* Dark Mode Background Overlay */
    @media (prefers-color-scheme: dark) {{
        [data-testid="stAppViewContainer"], .stApp {{
            background-image: linear-gradient(rgba(14, 17, 23, 0.92), rgba(14, 17, 23, 0.92)), url("data:image/jpeg;base64,{encoded}") !important;
        }}
    }}
    
    [data-testid="stAppViewContainer"], .stApp {{
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

# Deep CSS Overrides utilizing Streamlit's native CSS variables for seamless Light/Dark mode transitions
st.markdown("""
    <style>
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%) !important;
        padding: 26px 32px; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        margin-bottom: 20px; border-bottom: 4px solid #FFD100;
        color: #FFFFFF !important;
    }
    .hero-banner * { color: #FFFFFF !important; }
    .hero-banner h2 { color: #FFD100 !important; }
    
    .card-white {
        background-color: var(--secondary-background-color) !important; 
        border: 1px solid var(--border-color) !important;
        border-radius: 12px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        color: var(--text-color) !important;
    }
    .card-white h1, .card-white h2, .card-white h3, .card-white h4, 
    .card-white h5, .card-white p, .card-white span, .card-white div, 
    .card-white li, .card-white b, .card-white td, .card-white th { color: inherit !important; }
    
    .metric-card-white {
        background-color: var(--secondary-background-color) !important; 
        border: 1px solid var(--border-color) !important;
        border-radius: 12px; padding: 18px 20px; margin-bottom: 15px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        color: var(--text-color) !important;
    }
    .metric-card-white * { color: inherit !important; }
    
    .curr-box {
        background-color: var(--background-color) !important; 
        border: 1px solid var(--border-color) !important;
        padding: 12px; border-radius: 8px; min-height: 140px;
        color: var(--text-color) !important;
    }
    .curr-box p { color: inherit !important; }
    
    [data-testid="stSidebar"] { background-color: #002B15 !important; }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }
    [data-testid="stSidebar"] .stRadio label p { color: #FFFFFF !important; }
    
    .top-greeting * { color: var(--text-color) !important; }
    .top-greeting span.highlight { color: #00A859 !important; }
    
    .streamlit-expanderHeader { color: var(--text-color) !important; font-weight: bold; }
    [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p { color: var(--text-color) !important; font-weight: 600; }
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
        # Initialize Core Tables
        c.execute('''CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, department TEXT, email TEXT, start_date TEXT, end_date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS attendance (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, date TEXT, time TEXT, status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS submissions (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, week TEXT, topic TEXT, filename TEXT, filedata BLOB, date TEXT, status TEXT, grade TEXT, feedback TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, department TEXT, week TEXT, subtopic TEXT, score INTEGER, total INTEGER, date TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS announcements (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, date TEXT, author TEXT, department TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tickets (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, subject TEXT, message TEXT, status TEXT, reply TEXT, date TEXT, department TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS module_locks (department TEXT, week TEXT, is_locked INTEGER, PRIMARY KEY(department, week))''')
        
        # Migrations to safely add new columns to existing DB files without wiping
        try: c.execute("ALTER TABLE users ADD COLUMN start_date TEXT")
        except: pass
        try: c.execute("ALTER TABLE users ADD COLUMN end_date TEXT")
        except: pass
        try: c.execute("ALTER TABLE announcements ADD COLUMN department TEXT")
        except: pass
        try: c.execute("ALTER TABLE tickets ADD COLUMN department TEXT")
        except: pass
        conn.commit()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password, role, department, email, start_date, end_date):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password, role, department, email, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (username, hash_password(password), role, department, email, start_date, end_date))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False 

def authenticate_user(username, password):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("SELECT role, department, email, start_date, end_date FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
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
        {"week": "Week 1", "title": "Project Lifecycle & Regulations", "deliv": "Regulatory Intelligence Summary", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "NUPRC Regulatory Framework",
             "notes": "The Nigerian Upstream Petroleum Regulatory Commission (NUPRC) is the primary regulatory body for upstream operations. Compliance requires strict adherence to EGASPIN (Environmental Guidelines) and the Petroleum Industry Act (PIA) of 2021...",
             "quiz": [
                 {"q": "Which act restructured the Nigerian oil and gas fiscal terms in 2021?", "opts": ["OPEC Act", "Petroleum Industry Act (PIA)", "EGASPIN Act"], "ans": "Petroleum Industry Act (PIA)"},
             ],
             "assignment": "Read the PIA 2021 summary document. Write a 2-page report."
         }]},
        {"week": "Week 2", "title": "FEED & Costing Models", "deliv": "Facility Manifold Cost Model", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Front-End Engineering Design (FEED)",
             "notes": "FEED comes after the conceptual design and feasibility study...",
             "quiz": [{"q": "When does FEED occur in a project lifecycle?", "opts": ["Before conceptual design", "After conceptual design", "During construction"], "ans": "After conceptual design"}],
             "assignment": "Develop a Level 3 cost estimate for the installation of a 4-slot production manifold."
         }]}
    ],
    "Subsurface": [
        {"week": "Week 1", "title": "2D/3D Seismic Horizon Mapping", "deliv": "Seismic Horizon Report", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Seismic Interpretation Basics",
             "notes": "Seismic interpretation involves analyzing acoustic waves reflected from rock boundaries...",
             "quiz": [{"q": "What software is widely used for seismic interpretation?", "opts": ["Petrel", "Photoshop", "Primavera"], "ans": "Petrel"}],
             "assignment": "Analyze the provided seismic cross-section."
         }]},
        {"week": "Week 2", "title": "Petrophysical Log Evaluation", "deliv": "Net Pay & Water Saturation", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "Wireline Logging",
             "notes": "Logs measure physical properties of formations...",
             "quiz": [{"q": "High resistivity in a porous sandstone usually indicates:", "opts": ["Water", "Hydrocarbons", "Shale"], "ans": "Hydrocarbons"}],
             "assignment": "Calculate the Net-to-Gross ratio of the reservoir interval."
         }]}
    ],
    "ICT": [
        {"week": "Week 1", "title": "Network & Cybersecurity", "deliv": "Network Topology Audit", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Firewall & VLAN Configurations",
             "notes": "VLANs (Virtual Local Area Networks) segment network traffic...",
             "quiz": [{"q": "What does IT/OT separation protect?", "opts": ["Corporate emails", "Operational Technology (like field PLCs)", "Printer networks"], "ans": "Operational Technology (like field PLCs)"}],
             "assignment": "Draw a basic network topology diagram."
         }]},
        {"week": "Week 2", "title": "Enterprise Database Admin", "deliv": "Database Security Audit", "status": "⏳ In Progress", "color": "#D97706",
         "subtopics": [{
             "name": "SQL & Access Controls",
             "notes": "Database administration ensures data integrity and availability...",
             "quiz": [{"q": "Which SQL command gives user permissions?", "opts": ["GIVE", "GRANT", "ALLOW"], "ans": "GRANT"}],
             "assignment": "Write a SQL script that creates a 'ProductionData' table."
         }]}
    ],
    "Facility": [
        {"week": "Week 1", "title": "HVAC & Power Systems", "deliv": "Maintenance Log", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Uninterruptible Power Supply (UPS)",
             "notes": "Facility power stability is critical...",
             "quiz": [{"q": "What does UPS stand for?", "opts": ["Universal Power Source", "Uninterruptible Power Supply"], "ans": "Uninterruptible Power Supply"}],
             "assignment": "Perform a theoretical load calculation for a server room."
         }]}
    ],
    "Legal": [
        {"week": "Week 1", "title": "PIA Framework", "deliv": "PIA Impact Memo", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "PIA 2021 Overview",
             "notes": "The PIA overhauled Nigeria's oil and gas legal framework...",
             "quiz": [{"q": "Under the PIA, NNPC became a:", "opts": ["Government Ministry", "Limited Liability Company (NNPC Ltd)"], "ans": "Limited Liability Company (NNPC Ltd)"}],
             "assignment": "Draft a legal memo summarizing regulatory shifts."
         }]}
    ],
    "Finance": [
         {"week": "Week 1", "title": "Oil & Gas Cost Accounting", "deliv": "Cost Allocation Audit", "status": "✓ Completed", "color": "#059669",
         "subtopics": [{
             "name": "Successful Efforts vs Full Cost",
             "notes": "Two main accounting methods for exploration...",
             "quiz": [{"q": "Which method expenses dry holes immediately?", "opts": ["Full Cost", "Successful Efforts"], "ans": "Successful Efforts"}],
             "assignment": "Calculate total capitalized cost using both methods."
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
if "start_date" not in st.session_state: st.session_state["start_date"] = str(date.today())
if "end_date" not in st.session_state: st.session_state["end_date"] = str(date.today() + timedelta(days=120))

# ==========================================
# 6. LOGIN & REGISTRATION INTERFACE
# ==========================================
if not st.session_state["logged_in"]:
    set_background("ai-generated-aerial-view-offshore-drilling-rig-at-the-offshore-location-during-sunset-photo.jpg")
    
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
        else:
            st.title("🇳🇬 NNPC")
            
        st.markdown("""
            <div class="card-white" style="margin-top: 15px;">
                <h3 style="margin-top: 0;">NEOL Internship Portal Sign-In</h3>
                <p style="font-size: 0.88rem; color: var(--text-color) !important;">NNPC Eighteen Operating Limited — OML 18 Asset Operations</p>
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
                        # Fallback applied dynamically for legacy users missing dates
                        st.session_state["start_date"] = user_data[3] if user_data[3] else str(date.today())
                        st.session_state["end_date"] = user_data[4] if user_data[4] else str(date.today() + timedelta(days=120))
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
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    new_start = st.date_input("Internship Start Date", value=date.today())
                with col_d2:
                    new_end = st.date_input("Internship End Date", value=date.today() + timedelta(days=120))

                if st.form_submit_button("Register Account"):
                    if create_user(new_uname, new_pass, new_role, new_dept, new_email, str(new_start), str(new_end)):
                        st.success("Account created successfully! Please log in.")
                    else:
                        st.error("Username already exists.")
else:
    set_background("istockphoto-1457436123-612x612.jpg")

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
                <span style="font-size: 0.95rem; font-weight: 500;">Welcome back,</span><br>
                <span class="highlight" style="font-size: 1.6rem; font-weight: 700;">{st.session_state['username']} 👋</span><br>
                <span style="font-size: 0.85rem;">{st.session_state['role']} Portal</span>
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
        
        # Calculate dynamic individual dates
        start_d = datetime.strptime(st.session_state["start_date"], "%Y-%m-%d").date()
        end_d = datetime.strptime(st.session_state["end_date"], "%Y-%m-%d").date()
        today = date.today()

        days_left = max(0, (end_d - today).days)
        total_days = max(1, (end_d - start_d).days)
        days_passed = max(0, (today - start_d).days)
        progress_pct = max(0, min(int((days_passed / total_days) * 100), 100))

        if selected_nav == "Dashboard":
            # Fetch dynamic metrics from DB
            db_att = fetch_data("SELECT id FROM attendance WHERE username = ?", (st.session_state["username"],))
            att_count = len(db_att)
            # Estimate expected business days passed logic
            expected_att_days = max(1, (days_passed // 7) * 5)
            att_pct = min(100, int((att_count / expected_att_days) * 100))
            
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
                        <h3 style="margin: 8px 0 4px 0; font-size: 1.5rem; color: #FFFFFF !important;">{total_days // 7} Weeks</h3>
                        <p style="font-size: 0.78rem; color: #D0D0D0 !important; margin: 0;">{start_d.strftime('%b %d, %Y')} – {end_d.strftime('%b %d, %Y')}</p>
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
                        <span style="font-size: 0.75rem; font-weight: bold;">ATTENDANCE</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{att_pct}%</h3>
                        <span style="font-size: 0.72rem;">{att_count} days present</span>
                    </div>
                """, unsafe_allow_html=True)
            with m2:
                st.markdown(f"""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold;">DELIVERABLES</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{sub_count}</h3>
                        <span style="font-size: 0.72rem; color: #D97706 !important;">Total Uploaded</span>
                    </div>
                """, unsafe_allow_html=True)
            with m3:
                st.markdown("""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold;">ASSIGNMENTS</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">2 / 4</h3>
                        <span style="font-size: 0.72rem; color: #2563EB !important;">In Progress: 2</span>
                    </div>
                """, unsafe_allow_html=True)
            with m4:
                st.markdown("""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold;">COURSES</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">4 / 5</h3>
                        <span style="font-size: 0.72rem;">Completed: 4</span>
                    </div>
                """, unsafe_allow_html=True)
            with m5:
                st.markdown(f"""
                    <div class="metric-card-white">
                        <span style="font-size: 0.75rem; font-weight: bold;">DAYS LEFT</span>
                        <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">{days_left}</h3>
                        <span style="font-size: 0.72rem;">Until {end_d.strftime('%b %d')}</span>
                    </div>
                """, unsafe_allow_html=True)

            body_col1, body_col2 = st.columns([2.3, 1])

            with body_col1:
                current_dept = st.session_state['department']
                active_curr = department_curriculums.get(current_dept, department_curriculums["Projects"])

                st.markdown(f"""
                    <div class="card-white">
                        <div style="margin-bottom: 12px;">
                            <h4 style="margin: 0;">📖 My Curriculum</h4>
                            <p style="margin: 0; font-size: 0.8rem;">{total_days // 7}-Week Training Roadmap — <b style="color: #006837 !important;">{current_dept} Department</b></p>
                        </div>
                """, unsafe_allow_html=True)
                
                c_cols = st.columns(4)
                for i, phase in enumerate(active_curr):
                    col_idx = i % 4
                    with c_cols[col_idx]:
                        st.markdown(f"""
                            <div class="curr-box">
                                <span style="font-size: 0.72rem; color: #006837 !important; font-weight: bold;">{phase['week']}</span>
                                <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">{phase['title']}</p>
                                <hr style="margin: 6px 0; border-color: var(--border-color);">
                                <span style="font-size: 0.7rem;">{phase['deliv']}</span><br>
                                <span style="color: {phase['color']} !important; font-size: 0.72rem; font-weight: bold;">{phase['status']}</span>
                            </div>
                        """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

                ov_col1, ov_col2 = st.columns([1, 1.7])
                with ov_col1:
                    st.markdown(f"""
                        <div class="card-white">
                            <h4 style="margin: 0 0 10px 0; font-size: 1rem;">📌 Internship Overview</h4>
                            <div style="font-size: 0.8rem;">
                                <p style="margin: 6px 0;"><b>Duration:</b> {total_days // 7} Weeks</p>
                                <p style="margin: 6px 0;"><b>Start Date:</b> {start_d.strftime('%b %d, %Y')}</p>
                                <p style="margin: 6px 0;"><b>End Date:</b> {end_d.strftime('%b %d, %Y')}</p>
                                <p style="margin: 6px 0;"><b>Department:</b> {current_dept}</p>
                                <p style="margin: 6px 0;"><b>Supervisor:</b> To be assigned</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                with ov_col2:
                    st.markdown(f"""
                        <div class="card-white">
                            <h4 style="margin: 0 0 5px 0; font-size: 1rem;">📅 Your Tailored Milestones</h4>
                            <p style="margin: 0 0 8px 0; font-size: 0.75rem;">Dynamic Individual Roadmap</p>
                    """, unsafe_allow_html=True)
                    
                    # Dynamically offset based on start date
                    schedule_data = pd.DataFrame([
                        {"Task": "IT & HSE Briefing", "Start": start_d, "Finish": start_d + timedelta(days=7), "Category": "Milestone"},
                        {"Task": "Departmental Onboarding", "Start": start_d + timedelta(days=8), "Finish": start_d + timedelta(days=15), "Category": "Training"},
                        {"Task": "Phase 1 Progress Review", "Start": start_d + timedelta(days=28), "Finish": start_d + timedelta(days=30), "Category": "Assessment"},
                        {"Task": "Field Logistics Base Visit", "Start": start_d + timedelta(days=40), "Finish": start_d + timedelta(days=47), "Category": "Field Visit"},
                        {"Task": "Mid-Term Tech Presentation", "Start": start_d + timedelta(days=55), "Finish": start_d + timedelta(days=57), "Category": "Assessment"}
                    ])
                    fig_gantt = px.timeline(
                        schedule_data, x_start="Start", x_end="Finish", y="Task", color="Category",
                        color_discrete_map={"Milestone": "#FFD100", "Training": "#006837", "Assessment": "#00381C", "Field Visit": "#00A859"}
                    )
                    fig_gantt.update_yaxes(autorange="reversed")
                    fig_gantt.update_layout(
                        template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=11), height=240, margin=dict(t=5, b=5, l=5, r=5)
                    )
                    st.plotly_chart(fig_gantt, use_container_width=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            with body_col2:
                # Dynamic Announcement Banner filtered for this student's department or "All"
                latest_announcement = fetch_data("SELECT message, date, author FROM announcements WHERE department=? OR department='All' ORDER BY id DESC LIMIT 1", (current_dept,))
                if not latest_announcement.empty:
                    ann_msg = latest_announcement.iloc[0]['message']
                    ann_date = latest_announcement.iloc[0]['date']
                    ann_auth = latest_announcement.iloc[0]['author']
                else:
                    ann_msg = "Next Departmental Review is scheduled for next week. Ensure your logbooks are updated."
                    ann_date = "System Default"
                    ann_auth = "Admin"

                st.markdown(f"""
                    <div class="card-white" style="border-left: 4px solid #FFD100 !important;">
                        <h4 style="margin: 0 0 8px 0;">📢 Department Broadcast</h4>
                        <p style="font-size: 0.75rem; margin: 0 0 8px 0;">From {ann_auth} • {ann_date}</p>
                        <p style="font-size: 0.85rem; font-weight: 500; margin: 0;">{ann_msg}</p>
                    </div>
                """, unsafe_allow_html=True)

                st.markdown("""
                    <div class="card-white">
                        <h4 style="margin: 0 0 12px 0;">⚡ Quick Actions</h4>
                """, unsafe_allow_html=True)
                if st.button("➕ Add Attendance", use_container_width=True):
                    if record_attendance(st.session_state["username"], st.session_state["department"]):
                        st.success("Attendance marked for today!")
                    else:
                        st.warning("Already clocked in today.")
                if st.button("📤 Submit Deliverable", use_container_width=True):
                    st.info("Navigate to the Submissions page via sidebar.")
                st.markdown("</div>", unsafe_allow_html=True)

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
                                    st.markdown("#### 🎯 Quiz")
                                    with st.form(key=f"quiz_form_{phase_idx}_{sub_idx}"):
                                        user_answers = []
                                        for q_idx, q_data in enumerate(sub["quiz"]):
                                            st.write(f"**Q{q_idx+1}:** {q_data['q']}")
                                            ans = st.radio("Select:", q_data["opts"], key=f"q_{phase_idx}_{sub_idx}_{q_idx}", label_visibility="collapsed")
                                            user_answers.append((ans, q_data["ans"]))
                                            st.write("")
                                        submitted = st.form_submit_button("Submit Quiz to Supervisor")
                                        if submitted:
                                            score = sum([1 for user_ans, correct_ans in user_answers if user_ans == correct_ans])
                                            execute_query("INSERT INTO quiz_scores (username, department, week, subtopic, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                                          (st.session_state["username"], st.session_state["department"], phase['week'], sub['name'], score, len(sub["quiz"]), str(date.today())))
                                            if score == len(sub["quiz"]): st.success(f"🎉 Perfect Score! Saved.")
                                            else: st.warning(f"👍 Scored {score}/{len(sub['quiz'])}. Saved.")

                                with tab3:
                                    st.warning(f"**Task Instructions:**\n\n{sub['assignment']}")
                                    if st.button("📤 Upload Completed Assignment", key=f"btn_{phase_idx}_{sub_idx}"):
                                        st.success("Navigate to the **Submissions** tab to upload your file!")

        elif selected_nav == "Help Desk":
            st.subheader("🎫 IT / Supervisor Help Desk & Ticketing")
            with st.form("ticket_form"):
                st.markdown("#### Open a New Ticket")
                t_sub = st.text_input("Subject")
                t_msg = st.text_area("Message")
                if st.form_submit_button("Submit Ticket"):
                    execute_query("INSERT INTO tickets (username, subject, message, status, reply, date, department) VALUES (?, ?, ?, 'Open', '', ?, ?)",
                                  (st.session_state["username"], t_sub, t_msg, str(date.today()), st.session_state["department"]))
                    st.success("Ticket submitted to supervisors.")
            
            st.markdown("#### Your Ticket History")
            my_tickets = fetch_data("SELECT id AS ID, subject AS Subject, status AS Status, reply AS Supervisor_Reply, date AS Date FROM tickets WHERE username=? ORDER BY id DESC", (st.session_state["username"],))
            st.dataframe(my_tickets, use_container_width=True)

        elif selected_nav == "Master Schedule":
            st.subheader("📅 Your Personal Internship Roadmap")
            st.markdown("""<div class="card-white"><h4 style="margin-top: 0;">Dynamic Roadmap Timeline</h4><p style="font-size: 0.85rem;">Generated based on your personal start date.</p></div>""", unsafe_allow_html=True)
            
            schedule_data = pd.DataFrame([
                {"Task": "General IT Orientation & HSE Briefing", "Start": start_d, "Finish": start_d + timedelta(days=7), "Category": "Milestone"},
                {"Task": "Departmental Onboarding & System Setup", "Start": start_d + timedelta(days=8), "Finish": start_d + timedelta(days=15), "Category": "Training"},
                {"Task": "Phase 1 Progress Review & Logbook Check", "Start": start_d + timedelta(days=28), "Finish": start_d + timedelta(days=30), "Category": "Assessment"},
                {"Task": "Field Logistics Base Visit", "Start": start_d + timedelta(days=40), "Finish": start_d + timedelta(days=47), "Category": "Field Visit"},
                {"Task": "Mid-Term Technical Presentation", "Start": start_d + timedelta(days=55), "Finish": start_d + timedelta(days=57), "Category": "Assessment"},
                {"Task": "Advanced Technical Mentorship", "Start": start_d + timedelta(days=60), "Finish": start_d + timedelta(days=80), "Category": "Training"},
                {"Task": "Final Internship Capstone Defense", "Start": start_d + timedelta(days=105), "Finish": start_d + timedelta(days=108), "Category": "Milestone"},
                {"Task": "Logbook Submission & Exit Closeout", "Start": start_d + timedelta(days=110), "Finish": start_d + timedelta(days=115), "Category": "Deadline"}
            ])
            
            fig_gantt_full = px.timeline(
                schedule_data, x_start="Start", x_end="Finish", y="Task", color="Category",
                color_discrete_map={"Milestone": "#FFD100", "Training": "#006837", "Assessment": "#00381C", "Field Visit": "#00A859", "Deadline": "#D32F2F"}
            )
            fig_gantt_full.update_yaxes(autorange="reversed")
            fig_gantt_full.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=380)
            st.plotly_chart(fig_gantt_full, use_container_width=True)

        elif selected_nav in ["Submissions", "Deliverables"]:
            st.subheader(f"📤 Submissions & Logbook Portal")
            col_s1, col_s2 = st.columns([1, 1.2])
            with col_s1:
                st.markdown("""<div class="card-white"><h4 style="margin-top: 0;">Submit Weekly Deliverable</h4></div>""", unsafe_allow_html=True)
                with st.form("weekly_sub_form"):
                    week_num = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 17)])
                    rep_topic = st.text_input("Report Title / Topic")
                    rep_file = st.file_uploader("Upload Deliverable (PDF, PPTX)", type=['pdf', 'pptx', 'docx'])
                    if st.form_submit_button("Submit Deliverable 🚀") and rep_topic and rep_file:
                        execute_query("INSERT INTO submissions (username, department, week, topic, filename, filedata, date, status, grade, feedback) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                      (st.session_state["username"], st.session_state["department"], week_num, rep_topic, rep_file.name, rep_file.getvalue(), str(date.today()), "Pending Review", "Ungraded", ""))
                        st.success(f"Deliverable for {week_num} uploaded!")
                st.markdown("#### 📜 Submission History")
                db_subs = fetch_data("SELECT week AS Week, topic AS Topic, date AS Date, status AS Status, grade as Grade FROM submissions WHERE username = ?", (st.session_state["username"],))
                st.dataframe(db_subs if not db_subs.empty else pd.DataFrame({"Notice": ["No submissions yet."]}), use_container_width=True)
            with col_s2:
                st.markdown("""<div class="card-white"><h4 style="margin-top: 0;">👁️ Interactive Viewer</h4></div>""", unsafe_allow_html=True)
                if 'rep_file' in locals() and rep_file is not None and rep_file.name.endswith('.pdf'):
                    render_pdf_viewer(rep_file.getvalue())
                else:
                    st.info("Upload a PDF deliverable on the left to view it live.")

        elif selected_nav == "Onboarding Deck":
            st.subheader("🖼️ NEOL Employee Onboarding Deck")
            deck_file = st.file_uploader("Upload Handbook PDF", type=['pdf'])
            if deck_file and deck_file.name.endswith('.pdf'): render_pdf_viewer(deck_file.getvalue())

        elif selected_nav == "Attendance":
            st.subheader("⏰ Daily Clock-In")
            if st.button("📍 Clock In Now", use_container_width=True):
                if record_attendance(st.session_state["username"], st.session_state["department"]):
                    st.success("Attendance successfully recorded for today!")
                else:
                    st.warning("You have already clocked in today.")
            att_df = fetch_data("SELECT date AS Date, time AS Time, status AS Status FROM attendance WHERE username = ? ORDER BY id DESC", (st.session_state["username"],))
            st.dataframe(att_df, use_container_width=True)

        elif selected_nav == "Reports":
            st.info("Performance reports are processed at the end of the month.")

        elif selected_nav == "Export Official Logbook":
            st.subheader("📄 Generate Official NNPC IT Logbook")
            pdf_bytes = generate_logbook_pdf(st.session_state["username"], st.session_state["department"])
            st.download_button(label="📥 Download Logbook PDF", data=pdf_bytes, file_name=f"NNPC_Logbook_{st.session_state['username']}.pdf", mime="application/pdf")

        elif selected_nav == "Settings":
            st.subheader("⚙️ Settings")
            st.text_input("Full Name", value=st.session_state["username"], disabled=True)
            st.text_input("Department", value=st.session_state["department"], disabled=True)

    # ==========================================
    # 10. ROUTING PAGE VIEWS (SUPERVISOR) - STRICT ISOLATION APPLIED
    # ==========================================
    elif st.session_state["role"] == "Supervisor":
        dept = st.session_state["department"]
        
        if selected_nav == "Supervisor Dashboard":
            st.markdown(f"""
                <div class="hero-banner">
                    <h2 style="margin-top: 0;">Supervisor Control Center</h2>
                    <p>Managing Interns specifically for the <b>{dept}</b> Department.</p>
                </div>
            """, unsafe_allow_html=True)

            # Department Isolated Metrics
            total_students = fetch_data("SELECT COUNT(*) as count FROM users WHERE role='IT Student' AND department=?", (dept,)).iloc[0]['count']
            pending_actions = fetch_data("SELECT COUNT(*) as count FROM submissions WHERE status='Pending Review' AND department=?", (dept,)).iloc[0]['count']
            avg_score_df = fetch_data("SELECT AVG(score * 100.0 / total) as avg FROM quiz_scores WHERE department=?", (dept,))
            avg_score = round(avg_score_df.iloc[0]['avg'], 1) if not avg_score_df.empty and pd.notna(avg_score_df.iloc[0]['avg']) else 0

            c1, c2, c3 = st.columns(3)
            c1.markdown(f"""<div class="metric-card-white" style="border-left: 5px solid #2563EB !important;"><h4>Total Active Interns</h4><h2>{total_students}</h2></div>""", unsafe_allow_html=True)
            c2.markdown(f"""<div class="metric-card-white" style="border-left: 5px solid #D97706 !important;"><h4>Pending Deliverables</h4><h2>{pending_actions}</h2></div>""", unsafe_allow_html=True)
            c3.markdown(f"""<div class="metric-card-white" style="border-left: 5px solid #006837 !important;"><h4>Avg Cohort Quiz Score</h4><h2>{avg_score}%</h2></div>""", unsafe_allow_html=True)

        elif selected_nav == "Review Deliverables":
            st.subheader(f"👨‍💼 Grade {dept} Submissions")
            all_subs = fetch_data("SELECT id, username AS Student, week AS Week, topic AS Topic, status AS Status, grade AS Grade FROM submissions WHERE department=?", (dept,))
            st.dataframe(all_subs, use_container_width=True)
            
            if not all_subs.empty:
                st.markdown("### 📝 Grade a Submission")
                sub_id = st.selectbox("Select Submission ID", all_subs["id"].tolist())
                with st.form("grade_form"):
                    new_status = st.selectbox("Status", ["Approved", "Needs Revision", "Under Review"])
                    new_grade = st.selectbox("Grade", ["A", "B", "C", "Fail"])
                    new_feedback = st.text_area("Feedback Comments")
                    if st.form_submit_button("Save Grade"):
                        execute_query("UPDATE submissions SET status = ?, grade = ?, feedback = ? WHERE id = ?", (new_status, new_grade, new_feedback, sub_id))
                        st.success("Grade updated successfully!")
                        st.rerun()

        elif selected_nav == "Attendance & Risk":
            st.subheader(f"🚩 At-Risk Students — {dept}")
            
            all_users = fetch_data("SELECT username, department, start_date FROM users WHERE role='IT Student' AND department=?", (dept,))
            risk_data = []
            for _, row in all_users.iterrows():
                att = fetch_data("SELECT COUNT(*) as c FROM attendance WHERE username=?", (row['username'],)).iloc[0]['c']
                
                # Dynamic risk calculation based on their unique start date
                s_date_str = row['start_date'] if row['start_date'] else str(date.today())
                s_date = datetime.strptime(s_date_str, "%Y-%m-%d").date()
                days_passed = max(1, (date.today() - s_date).days)
                expected_days = max(1, (days_passed // 7) * 5) # Assume 5 business days a week expected
                
                att_pct = min(100, int((att / expected_days) * 100))
                risk_flag = "🚨 High Risk" if att_pct < 75 else "✅ Good"
                risk_data.append({"Student": row['username'], "Attendance %": att_pct, "Status": risk_flag})
            
            st.dataframe(pd.DataFrame(risk_data), use_container_width=True)

        elif selected_nav == "Quiz Analytics":
            st.subheader(f"🏆 {dept} Quiz Analytics & Leaderboard")
            leaderboard = fetch_data("SELECT username AS Student, SUM(score) AS Total_Score FROM quiz_scores WHERE department=? GROUP BY username ORDER BY Total_Score DESC", (dept,))
            if not leaderboard.empty:
                col1, col2 = st.columns([1, 1.5])
                col1.markdown("#### 🥇 Top Students")
                col1.dataframe(leaderboard, use_container_width=True)
                
                fig = px.bar(leaderboard, x="Student", y="Total_Score", color="Student")
                fig.update_layout(template="plotly_white", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                col2.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No quiz data available yet in your department.")

        elif selected_nav == "Broadcasts & Tickets":
            st.subheader("📢 Communications Center")
            tab1, tab2 = st.tabs(["Department Broadcast", "Student Tickets"])
            
            with tab1:
                with st.form("announcement_form"):
                    st.markdown(f"#### Broadcast to {dept} Interns")
                    msg = st.text_area("Message")
                    if st.form_submit_button("Broadcast"):
                        execute_query("INSERT INTO announcements (message, date, author, department) VALUES (?, ?, ?, ?)",
                                      (msg, str(date.today()), st.session_state["username"], dept))
                        st.success("Broadcast sent successfully!")
            
            with tab2:
                st.markdown(f"#### Manage {dept} Tickets")
                tickets_df = fetch_data("SELECT id, username, subject, message, status FROM tickets WHERE status='Open' AND department=?", (dept,))
                st.dataframe(tickets_df, use_container_width=True)
                
                if not tickets_df.empty:
                    with st.form("reply_form"):
                        t_id = st.selectbox("Select Ticket ID", tickets_df['id'].tolist())
                        reply = st.text_area("Resolution")
                        if st.form_submit_button("Close Ticket"):
                            execute_query("UPDATE tickets SET status='Closed', reply=? WHERE id=?", (reply, t_id))
                            st.success("Ticket closed.")
                            st.rerun()

        elif selected_nav == "Curriculum Controls":
            st.subheader(f"🔐 Curriculum Controls — {dept}")
            actual_weeks = [phase["week"] for phase in department_curriculums.get(dept, [])]
            with st.form("lock_form"):
                target_week = st.selectbox("Target Module", actual_weeks)
                action = st.radio("Action", ["Lock", "Unlock"])
                if st.form_submit_button("Apply Action"):
                    is_locked = 1 if action == "Lock" else 0
                    execute_query("INSERT OR REPLACE INTO module_locks (department, week, is_locked) VALUES (?, ?, ?)",
                                  (dept, target_week, is_locked))
                    st.success(f"{action}ed {target_week} for {dept}.")

        elif selected_nav == "Export Reports":
            st.subheader(f"📑 Export {dept} Cohort Data")
            users_csv = fetch_data("SELECT username, email, start_date, end_date FROM users WHERE role='IT Student' AND department=?", (dept,)).to_csv(index=False)
            st.download_button("📥 Export Student Roster (CSV)", users_csv, f"{dept}_interns.csv", "text/csv")
