import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime
import os
import base64
import sqlite3

# ==========================================
# 1. PAGE CONFIG & UNIVERSAL THEME STYLING
# ==========================================
st.set_page_config(
    page_title="NNPC Internship Portal Dashboard",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9 !important; }
    
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%) !important;
        padding: 26px 32px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        margin-bottom: 20px;
        border-bottom: 4px solid #FFD100;
    }
    .hero-banner * { color: #FFFFFF !important; }
    .hero-banner h2 { color: #FFD100 !important; }

    .card-white {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .card-white, .card-white h1, .card-white h2, .card-white h3, .card-white h4, 
    .card-white h5, .card-white p, .card-white span, .card-white div, 
    .card-white li, .card-white b, .card-white td, .card-white th {
        color: #0F172A !important;
    }

    .metric-card-white {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .metric-card-white * { color: #0F172A !important; }

    .curr-box {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        padding: 12px;
        border-radius: 8px;
        min-height: 140px;
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

# ==========================================
# 2. PERSISTENT SQLITE DATABASE ENGINE
# ==========================================
DB_NAME = "nnpc_portal.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    department TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS submissions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    department TEXT,
                    week TEXT,
                    topic TEXT,
                    filename TEXT,
                    filedata BLOB,
                    date TEXT,
                    status TEXT,
                    grade TEXT,
                    feedback TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS quiz_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    department TEXT,
                    week TEXT,
                    subtopic TEXT,
                    score INTEGER,
                    total INTEGER,
                    date TEXT
                )''')
    conn.commit()
    conn.close()

init_db()

def record_attendance(username, department, status="On Time"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    now = datetime.now()
    c.execute("INSERT INTO attendance (username, department, date, time, status) VALUES (?, ?, ?, ?, ?)",
              (username, department, str(now.strftime("%Y-%m-%d")), str(now.strftime("%I:%M %p")), status))
    conn.commit()
    conn.close()

def fetch_attendance(username=None, department=None):
    conn = sqlite3.connect(DB_NAME)
    if username:
        df = pd.read_sql_query("SELECT date AS Date, time AS Time, status AS Status FROM attendance WHERE username = ? ORDER BY id DESC", conn, params=(username,))
    elif department and department != "All":
        df = pd.read_sql_query("SELECT username AS Student, department AS Dept, date AS Date, time AS Time, status AS Status FROM attendance WHERE department = ? ORDER BY id DESC", conn, params=(department,))
    else:
        df = pd.read_sql_query("SELECT username AS Student, department AS Dept, date AS Date, time AS Time, status AS Status FROM attendance ORDER BY id DESC", conn)
    conn.close()
    return df

def save_submission(username, department, week, topic, filename, filebytes):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""INSERT INTO submissions 
                 (username, department, week, topic, filename, filedata, date, status, grade, feedback) 
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
              (username, department, week, topic, filename, filebytes, str(date.today()), "Pending Review", "Ungraded", "Awaiting review"))
    conn.commit()
    conn.close()

def fetch_submissions(username=None, department=None):
    conn = sqlite3.connect(DB_NAME)
    if username:
        df = pd.read_sql_query("SELECT id, week AS Week, topic AS Topic, date AS Date, status AS Status, grade AS Grade, feedback AS Feedback FROM submissions WHERE username = ? ORDER BY id DESC", conn, params=(username,))
    elif department and department != "All":
        df = pd.read_sql_query("SELECT id, username AS Student, department AS Dept, week AS Week, topic AS Topic, filename AS File, date AS Date, status AS Status, grade AS Grade, feedback AS Feedback FROM submissions WHERE department = ? ORDER BY id DESC", conn, params=(department,))
    else:
        df = pd.read_sql_query("SELECT id, username AS Student, department AS Dept, week AS Week, topic AS Topic, filename AS File, date AS Date, status AS Status, grade AS Grade, feedback AS Feedback FROM submissions ORDER BY id DESC", conn)
    conn.close()
    return df

def update_submission_grade(sub_id, status, grade, feedback):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE submissions SET status = ?, grade = ?, feedback = ? WHERE id = ?", (status, grade, feedback, sub_id))
    conn.commit()
    conn.close()

def save_quiz_score(username, department, week, subtopic, score, total):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO quiz_scores (username, department, week, subtopic, score, total, date) VALUES (?, ?, ?, ?, ?, ?, ?)",
              (username, department, week, subtopic, score, total, str(date.today())))
    conn.commit()
    conn.close()

def fetch_quiz_scores(department=None):
    conn = sqlite3.connect(DB_NAME)
    if department and department != "All":
        df = pd.read_sql_query("SELECT username AS Student, department AS Dept, week AS Week, subtopic AS Topic, score AS Score, total AS OutOf, date AS Date FROM quiz_scores WHERE department = ? ORDER BY id DESC", conn, params=(department,))
    else:
        df = pd.read_sql_query("SELECT username AS Student, department AS Dept, week AS Week, subtopic AS Topic, score AS Score, total AS OutOf, date AS Date FROM quiz_scores ORDER BY id DESC", conn)
    conn.close()
    return df

def render_pdf_viewer(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="520" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==========================================
# 3. QUESTION GENERATOR (100 QUESTIONS PER DEPT)
# ==========================================
def generate_dept_questions(dept_name):
    questions = []
    
    topics_map = {
        "Projects": [
            ("NUPRC & PIA Regulations", ["PIA 2021", "NUPRC", "Host Community", "EGASPIN", "Deepwater Terms"]),
            ("FEED & Cost Models", ["P&IDs", "Level 3 Estimate", "CAPEX/OPEX", "WBS", "Risk Register"]),
            ("Primavera P6 Scheduling", ["Critical Path", "Total Float", "Predecessor", "Gantt Chart", "Baseline"]),
            ("Site Pre-Commissioning", ["Hydrotest", "Line Walk", "Loop Check", "Mechanical Completion", "Punchlist"])
        ],
        "Subsurface": [
            ("Seismic Interpretation", ["Acoustic Impedance", "Reflection", "Fault Horizon", "Petrel", "3D Grid"]),
            ("Wireline Log Evaluation", ["Gamma Ray", "Resistivity", "Neutron-Density", "Archie Eq", "Net Pay"]),
            ("Material Balance", ["Water Drive", "Solution Gas", "Gas Cap", "MBAL", "Recovery Factor"]),
            ("Reservoir Simulation", ["Dynamic Model", "Grid Block", "PVT Data", "Eclipse", "History Match"])
        ],
        "ICT": [
            ("Network & Cyber Security", ["VLAN", "Firewall", "IT/OT Split", "DMZ", "HTTPS Port 443"]),
            ("Database Administration", ["SQL Grant/Revoke", "RBAC", "Primary Key", "ACID", "Index"]),
            ("Software & ITIL", ["ITIL Incident", "SLA P1-P4", "CI/CD Pipeline", "DevOps", "Version Control"]),
            ("Cloud Infrastructure", ["IaaS/PaaS/SaaS", "Hybrid Cloud", "Data Sovereignty", "Docker", "AWS/Azure"])
        ],
        "Facility": [
            ("HVAC & Power Systems", ["UPS Inverter", "Generator", "VRLA Battery", "kVA Load", "Chiller"]),
            ("HSE & Work Permits", ["PTW System", "Hot/Cold Work", "LOTO Protocol", "JHA", "Gas Test"]),
            ("Asset Integrity", ["Preventive Maintenance", "Predictive Vibration", "CMMS", "MTBF", "RBI"]),
            ("Energy Optimization", ["VFD Drive", "LED Retrofit", "Energy Audit", "Power Factor", "OPEX Savings"])
        ],
        "Legal": [
            ("PIA Legal Framework", ["NNPC Ltd", "NUPRC Role", "NMDPRA Role", "Host Community Fund", "Fiscal Terms"]),
            ("JV & PSC Contracts", ["Production Sharing", "Cost Oil vs Profit Oil", "JOA", "Cash Call Default", "Lifting"]),
            ("Arbitration & Governance", ["Dispute Clause", "Arbitral Award", "LCIA/ICC", "Force Majeure", "Indemnity"]),
            ("Environmental Law", ["Gas Flare Penalty", "NGFCP", "EGASPIN", "EIA Permit", "Spill Liability"])
        ],
        "Finance": [
            ("Cost Accounting", ["Successful Efforts", "Full Cost Method", "Dry Hole Expense", "DD&A", "Capitalization"]),
            ("JV Billing & Cash Calls", ["Cash Call Reconciliation", "JIB Statement", "WP&B Budget", "Operator Audit", "Default"]),
            ("CAPEX/OPEX Budgeting", ["CAPEX Asset", "OPEX Expense", "NPV Analysis", "IRR Metric", "Variance"]),
            ("Taxation & Audit", ["Hydrocarbon Tax", "Company Income Tax", "Royalty Volume", "NUPRC Fiscal", "PPT Shift"])
        ]
    }

    subtopic_list = topics_map.get(dept_name, topics_map["Projects"])

    q_counter = 1
    for phase_idx, (phase_title, keywords) in enumerate(subtopic_list):
        for i in range(25):  # 25 questions per subtopic * 4 = 100 questions per department
            kw = keywords[i % len(keywords)]
            q_text = f"[{dept_name} Q{q_counter}] Regarding {phase_title}: What is the primary role or function of '{kw}'?"
            opts = [
                f"Standard industry procedure for {kw} in {dept_name} operations.",
                f"Secondary administrative guideline unrelated to {kw}.",
                f"Deprecated legacy protocol replaced by manual checks.",
                f"Optional third-party audit metric."
            ]
            ans = opts[0]
            questions.append({"q": q_text, "opts": opts, "ans": ans, "phase": phase_idx})
            q_counter += 1

    return questions

# ==========================================
# 4. DEPARTMENT CURRICULUM STRUCTURE
# ==========================================
department_names = ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"]
department_curriculums = {}

for dname in department_names:
    all_q = generate_dept_questions(dname)
    department_curriculums[dname] = [
        {
            "week": "Week 1 – 4",
            "title": "Module 1: Foundations & Regulations",
            "deliv": "Phase 1 Compliance Summary",
            "status": "✓ Completed",
            "color": "#059669",
            "subtopics": [{
                "name": f"{dname} Core Principles (Questions 1-25)",
                "notes": f"Study notes for {dname} Phase 1: Focus on foundational concepts, standards, and regulatory compliance.",
                "quiz": [q for q in all_q if q["phase"] == 0],
                "assignment": f"Prepare a technical report covering Phase 1 topics for {dname}."
            }]
        },
        {
            "week": "Week 5 – 8",
            "title": "Module 2: Applied Engineering & Models",
            "deliv": "Phase 2 Analytical Model",
            "status": "⏳ In Progress",
            "color": "#D97706",
            "subtopics": [{
                "name": f"{dname} Execution Models (Questions 26-50)",
                "notes": f"Study notes for {dname} Phase 2: Applied technical workflows, modeling, and execution.",
                "quiz": [q for q in all_q if q["phase"] == 1],
                "assignment": f"Develop an operational spreadsheet for Phase 2 {dname} workflows."
            }]
        },
        {
            "week": "Week 9 – 12",
            "title": "Module 3: Advanced Optimization & Controls",
            "deliv": "Phase 3 Optimization Schedule",
            "status": "🔒 Not Started",
            "color": "#64748B",
            "subtopics": [{
                "name": f"{dname} Control Frameworks (Questions 51-75)",
                "notes": f"Study notes for {dname} Phase 3: Risk management, scheduling, and control systems.",
                "quiz": [q for q in all_q if q["phase"] == 2],
                "assignment": f"Draft a risk mitigation matrix for {dname} operations."
            }]
        },
        {
            "week": "Week 13 – 16",
            "title": "Module 4: Field Audits & Closeout Defense",
            "deliv": "Final Internship Capstone Report",
            "status": "🔒 Not Started",
            "color": "#64748B",
            "subtopics": [{
                "name": f"{dname} Capstone Defense (Questions 76-100)",
                "notes": f"Study notes for {dname} Phase 4: Final audits, pre-commissioning, and capstone presentation.",
                "quiz": [q for q in all_q if q["phase"] == 3],
                "assignment": f"Submit your final 16-week logbook and capstone defense deck for {dname}."
            }]
        }
    ]

# ==========================================
# 5. SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = "Alex"
if "role" not in st.session_state:
    st.session_state["role"] = "IT Student"
if "department" not in st.session_state:
    st.session_state["department"] = "Projects"

# ==========================================
# 6. LOGIN INTERFACE
# ==========================================
if not st.session_state["logged_in"]:
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
        else:
            st.title("🇳🇬 NNPC")
            
        st.markdown("""
            <div class="card-white" style="margin-top: 15px;">
                <h3 style="margin-top: 0; color: #006837 !important;">NEOL Portal Sign-In</h3>
                <p style="font-size: 0.88rem; color: #64748B !important;">NNPC Eighteen Operating Limited — OML 18 Asset Operations</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_visual_form"):
            uname = st.text_input("Full Name", value="Alex")
            urole = st.selectbox("Portal Account Role", ["IT Student", "Supervisor / Manager"])
            udept = st.selectbox("Department", department_names)
            sub = st.form_submit_button("Launch Dashboard 🚀")
            
            if sub:
                st.session_state["logged_in"] = True
                st.session_state["username"] = uname
                st.session_state["role"] = urole
                st.session_state["department"] = udept
                st.rerun()
else:
    # ==========================================
    # 7. SIDEBAR NAVIGATION
    # ==========================================
    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
        else:
            st.markdown("### 🇳🇬 NNPC")
            
        st.markdown(f"**User:** `{st.session_state['username']}`")
        st.markdown(f"**Role:** `{st.session_state['role']}`")
        st.markdown("<br>", unsafe_allow_html=True)

        if st.session_state["role"] == "IT Student":
            nav_options = ["Dashboard", "Curriculum", "Master Schedule", "Submissions", "Attendance"]
        else:
            nav_options = ["Supervisor Dashboard", "Review Submissions", "Student Attendance", "Quiz Analytics"]

        selected_nav = st.radio("Navigation", nav_options, label_visibility="collapsed")
        
        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # ==========================================
    # 8. TOP NAVBAR
    # ==========================================
    top_col1, top_col2 = st.columns([3.5, 1.5])
    with top_col1:
        st.markdown(f"""
            <div class="top-greeting" style="margin-top: 5px;">
                <span style="font-size: 0.95rem; color: #475569 !important;">Welcome back,</span><br>
                <span style="font-size: 1.6rem; font-weight: 700; color: #006837 !important;">{st.session_state['username']} ({st.session_state['role']}) 👋</span>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 9. ROUTING PAGE VIEWS
    # ==========================================

    # --- STUDENT DASHBOARD ---
    if selected_nav == "Dashboard" and st.session_state["role"] == "IT Student":
        st.subheader("🇳🇬 Student Overview Dashboard")
        col_hb1, col_hb2 = st.columns([3.2, 1.8])
        with col_hb1:
            st.markdown("""
                <div class="hero-banner">
                    <h2 style="margin-top: 0; font-size: 1.8rem;">NNPC Eighteen Operating Limited (NEOL)</h2>
                    <p style="font-size: 1.05rem;">OML 18 Asset Operations — 100-Question Interactive Curriculum Portal</p>
                </div>
            """, unsafe_allow_html=True)
        with col_hb2:
            st.markdown("""
                <div class="hero-banner" style="padding: 20px;">
                    <span style="font-size: 0.85rem; color: #FFD100 !important; font-weight: bold;">📅 Active Internship</span>
                    <h3 style="margin: 8px 0; color: #FFFFFF !important;">16 Weeks Cycle</h3>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("### 📜 Live Submission & Grading Status")
        student_subs = fetch_submissions(username=st.session_state["username"])
        if not student_subs.empty:
            st.dataframe(student_subs, use_container_width=True)
        else:
            st.info("No deliverables submitted yet. Navigate to 'Submissions' to upload your work.")

    # --- STUDENT CURRICULUM WITH 100 QUESTIONS PAGINATED ---
    elif selected_nav == "Curriculum" and st.session_state["role"] == "IT Student":
        current_dept = st.session_state['department']
        st.subheader(f"📖 Interactive Learning Module — {current_dept} Department (100 Questions Total)")
        active_curr = department_curriculums.get(current_dept, department_curriculums["Projects"])

        for phase_idx, phase in enumerate(active_curr):
            with st.expander(f"📍 {phase['week']}: {phase['title']} ({phase['status']})"):
                st.markdown(f"**Main Deliverable:** `{phase['deliv']}`")
                if "subtopics" in phase:
                    for sub_idx, sub in enumerate(phase["subtopics"]):
                        st.markdown(f"#### 🔹 {sub['name']}")
                        tab1, tab2, tab3 = st.tabs(["📝 Notes", "🧠 Quiz Engine (25 Qs)", "📋 Assignment"])
                        
                        with tab1:
                            st.info(sub['notes'])
                            
                        with tab2:
                            q_list = sub["quiz"]
                            batch_size = 5
                            total_batches = (len(q_list) + batch_size - 1) // batch_size
                            
                            batch_page = st.selectbox(
                                f"Select Question Set for {phase['week']}", 
                                [f"Questions {p*batch_size + 1} - {min((p+1)*batch_size, len(q_list))}" for p in range(total_batches)],
                                key=f"pselect_{phase_idx}_{sub_idx}"
                            )
                            selected_page_idx = int(batch_page.split()[1]) - 1
                            current_batch = q_list[selected_page_idx*batch_size : (selected_page_idx+1)*batch_size]

                            with st.form(key=f"qform_{phase_idx}_{sub_idx}_{selected_page_idx}"):
                                user_answers = []
                                for q_i, q_data in enumerate(current_batch):
                                    st.write(f"**{q_data['q']}**")
                                    ans = st.radio("Option:", q_data["opts"], key=f"q_{phase_idx}_{sub_idx}_{selected_page_idx}_{q_i}")
                                    user_answers.append((ans, q_data["ans"]))
                                sub_q = st.form_submit_button("Submit Batch Answers")
                                if sub_q:
                                    score = sum([1 for u, c in user_answers if u == c])
                                    save_quiz_score(st.session_state["username"], current_dept, phase['week'], sub['name'], score, len(current_batch))
                                    st.success(f"Batch Score Saved to Database: {score}/{len(current_batch)}")

                        with tab3:
                            st.warning(sub['assignment'])

    # --- STUDENT SUBMISSIONS ---
    elif selected_nav == "Submissions" and st.session_state["role"] == "IT Student":
        st.subheader("📤 Submit Weekly Deliverables & Logbook")
        col1, col2 = st.columns([1, 1])
        with col1:
            with st.form("sub_form"):
                week_num = st.selectbox("Select Week", [f"Week {i}" for i in range(1, 17)])
                topic = st.text_input("Topic Title")
                uploaded_file = st.file_uploader("Upload PDF / Document", type=['pdf', 'docx'])
                btn = st.form_submit_button("Submit Deliverable")
                if btn and uploaded_file:
                    save_submission(st.session_state["username"], st.session_state["department"], week_num, topic, uploaded_file.name, uploaded_file.getvalue())
                    st.success("Deliverable saved to database successfully!")
                    st.rerun()
        with col2:
            st.markdown("#### Your Submissions")
            df_sub = fetch_submissions(username=st.session_state["username"])
            st.dataframe(df_sub, use_container_width=True)

    # --- STUDENT ATTENDANCE ---
    elif selected_nav == "Attendance" and st.session_state["role"] == "IT Student":
        st.subheader("⏰ Daily Attendance Register")
        if st.button("📍 Clock In Now", use_container_width=True):
            record_attendance(st.session_state["username"], st.session_state["department"])
            st.success("Clock-in recorded in database!")
        st.markdown("#### Attendance Log")
        st.dataframe(fetch_attendance(username=st.session_state["username"]), use_container_width=True)

    # --- SUPERVISOR DASHBOARD & REVIEW ---
    elif selected_nav == "Review Submissions" and st.session_state["role"] == "Supervisor / Manager":
        st.subheader("👨‍💼 Supervisor Review & Grading Portal")
        dept_filter = st.selectbox("Filter by Department", ["All"] + department_names)
        
        all_subs = fetch_submissions(department=dept_filter)
        if not all_subs.empty:
            st.dataframe(all_subs, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### 📝 Grade Student Submission")
            sub_id_to_grade = st.selectbox("Select Submission ID to Grade", all_subs["id"].tolist())
            
            with st.form("grade_form"):
                new_status = st.selectbox("Review Status", ["Approved", "Needs Revision", "Under Review"])
                new_grade = st.selectbox("Grade", ["A (Excellent)", "B (Good)", "C (Satisfactory)", "Re-submit Required"])
                new_feedback = st.text_area("Written Feedback for Student")
                submit_grade = st.form_submit_button("Save Grade & Send Feedback")
                
                if submit_grade:
                    update_submission_grade(sub_id_to_grade, new_status, new_grade, new_feedback)
                    st.success(f"Submission #{sub_id_to_grade} updated successfully!")
                    st.rerun()
        else:
            st.info("No student submissions found in database.")

    # --- SUPERVISOR ATTENDANCE ---
    elif selected_nav == "Student Attendance" and st.session_state["role"] == "Supervisor / Manager":
        st.subheader("📊 All Student Attendance Records")
        dept_filter = st.selectbox("Filter Department", ["All"] + department_names)
        st.dataframe(fetch_attendance(department=dept_filter), use_container_width=True)

    # --- SUPERVISOR QUIZ METRICS ---
    elif selected_nav == "Quiz Analytics" and st.session_state["role"] == "Supervisor / Manager":
        st.subheader("🧠 Student Quiz Performance Analytics (100 Questions Benchmark)")
        quiz_df = fetch_quiz_scores()
        if not quiz_df.empty:
            st.dataframe(quiz_df, use_container_width=True)
            fig_quiz = px.histogram(quiz_df, x="Dept", y="Score", color="Dept", barmode="group", title="Quiz Score Distribution Across Departments")
            st.plotly_chart(fig_quiz, use_container_width=True)
        else:
            st.info("No quiz records available in database yet.")
