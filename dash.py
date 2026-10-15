import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import base64

# ==========================================
# 1. PAGE CONFIG & UNIVERSAL THEME STYLING
# ==========================================
st.set_page_config(
    page_title="NNPC Internship Portal Dashboard",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Deep CSS Overrides to lock card text & backgrounds across light & dark browser modes
st.markdown("""
    <style>
    /* Force main app canvas background */
    .stApp {
        background-color: #F1F5F9 !important;
    }
    
    /* HERO BANNER (Always Dark Green + White/Gold Text) */
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%) !important;
        padding: 26px 32px;
        border-radius: 14px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
        margin-bottom: 20px;
        border-bottom: 4px solid #FFD100;
    }
    .hero-banner * {
        color: #FFFFFF !important;
    }
    .hero-banner h2 {
        color: #FFD100 !important;
    }

    /* WHITE CONTENT CARDS (Locked White Background + Dark Slate Text) */
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

    /* METRIC CARDS */
    .metric-card-white {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    .metric-card-white * {
        color: #0F172A !important;
    }

    /* CURRICULUM BOXES */
    .curr-box {
        background-color: #F8FAFC !important;
        border: 1px solid #CBD5E1 !important;
        padding: 12px;
        border-radius: 8px;
        min-height: 140px;
    }
    .curr-box * {
        color: #0F172A !important;
    }

    /* SIDEBAR LOCK (Always Dark Green) */
    [data-testid="stSidebar"] {
        background-color: #002B15 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio label p {
        color: #FFFFFF !important;
    }

    /* GREETING TEXT OVERRIDE */
    .top-greeting * {
        color: #0F172A !important;
    }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "nnpc.jpeg"

# Helper function for inline PDF Preview
def render_pdf_viewer(file_bytes):
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="520" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==========================================
# 2. DEPARTMENT CURRICULUM DATA
# ==========================================
department_curriculums = {
    "Projects": [
        {"week": "Week 1 – 4", "title": "Project Lifecycle & Regulations", "deliv": "Regulatory Intelligence Summary", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "FEED & Costing Models", "deliv": "Facility Manifold Cost Model", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Primavera P6 Scheduling", "deliv": "Baseline Master Schedule", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Site Inspections", "deliv": "Final Project Report", "status": "🔒 Not Started", "color": "#64748B"}
    ],
    "Subsurface": [
        {"week": "Week 1 – 4", "title": "2D/3D Seismic Horizon Mapping", "deliv": "Seismic Horizon Report", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Petrophysical Log Evaluation", "deliv": "Net Pay & Water Saturation", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Reservoir Material Balance", "deliv": "Reserves Estimation Analysis", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Reservoir Simulation", "deliv": "Integrated Subsurface Model", "status": "🔒 Not Started", "color": "#64748B"}
    ],
    "ICT": [
        {"week": "Week 1 – 4", "title": "Network & Cybersecurity", "deliv": "Network Topology Audit", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Enterprise Database Admin", "deliv": "Database Security Audit", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Software Engineering & ITIL", "deliv": "Service Desk Automation", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Cloud Infrastructure", "deliv": "Cloud System Deployment", "status": "🔒 Not Started", "color": "#64748B"}
    ],
    "Facility": [
        {"week": "Week 1 – 4", "title": "HVAC & Power Systems", "deliv": "Maintenance Log & Safety Check", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "HSE & Emergency Protocols", "deliv": "Hazard Identification Assessment", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Asset Integrity Mgmt", "deliv": "Preventive Maintenance Schedule", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Energy Efficiency & Auditing", "deliv": "Energy Optimization Strategy", "status": "🔒 Not Started", "color": "#64748B"}
    ],
    "Legal": [
        {"week": "Week 1 – 4", "title": "PIA Framework", "deliv": "PIA Impact Analysis Memo", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Joint Venture Contracts", "deliv": "JV Legal Contract Brief", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Corporate Governance", "deliv": "Arbitration & Legal Case Study", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Environmental Energy Law", "deliv": "Compliance Checklist", "status": "🔒 Not Started", "color": "#64748B"}
    ],
    "Finance": [
        {"week": "Week 1 – 4", "title": "Oil & Gas Cost Accounting", "deliv": "Cost Allocation Audit Report", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "JV Cash Calls & Billing", "deliv": "Cash Call Reconciliation Sheet", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "CAPEX & OPEX Budgeting", "deliv": "Quarterly Budget Forecast Model", "status": "🔒 Not Started", "color": "#64748B"},
        {"week": "Week 13 – 16", "title": "Tax Compliance & Audit", "deliv": "Tax Compliance Summary", "status": "🔒 Not Started", "color": "#64748B"}
    ]
}

# ==========================================
# 3. SESSION STATE INITIALIZATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = "Alex"
if "department" not in st.session_state:
    st.session_state["department"] = "Projects"
if "submitted_reports" not in st.session_state:
    st.session_state["submitted_reports"] = [
        {"Week": "Week 1", "Topic": "Project Lifecycle & Regulations", "Date": "2026-10-05", "Status": "Approved"},
        {"Week": "Week 5", "Topic": "FEED & Costing Document", "Date": "2026-10-14", "Status": "Pending Review"}
    ]
if "attendance_records" not in st.session_state:
    st.session_state["attendance_records"] = [
        {"Date": "2026-10-13", "Time": "07:28 AM", "Status": "On Time"},
        {"Date": "2026-10-14", "Time": "07:25 AM", "Status": "On Time"},
        {"Date": "2026-10-15", "Time": "07:31 AM", "Status": "On Time"}
    ]

# ==========================================
# 4. LOGIN INTERFACE
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
                <h3 style="margin-top: 0; color: #006837 !important;">NEOL Internship Portal Sign-In</h3>
                <p style="font-size: 0.88rem; color: #64748B !important;">NNPC Eighteen Operating Limited — OML 18 Asset Operations</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_visual_form"):
            uname = st.text_input("Full Name", value="Alex")
            udept = st.selectbox("Department", ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"])
            sub = st.form_submit_button("Launch Dashboard 🚀")
            
            if sub:
                st.session_state["logged_in"] = True
                st.session_state["username"] = uname
                st.session_state["department"] = udept
                st.rerun()
else:
    # ==========================================
    # 5. SIDEBAR NAVIGATION
    # ==========================================
    with st.sidebar:
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=150)
        else:
            st.markdown("### 🇳🇬 NNPC")
            
        st.markdown("<br>", unsafe_allow_html=True)
        nav_options = [
            "Dashboard", "Curriculum", "Master Schedule", "Submissions", 
            "Onboarding Deck", "Attendance", "Deliverables", "Reports", "Settings"
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

    # ==========================================
    # 6. TOP NAVBAR
    # ==========================================
    top_col1, top_col2, top_col3, top_col4 = st.columns([3.5, 1, 1, 1.5])
    with top_col1:
        st.markdown(f"""
            <div class="top-greeting" style="margin-top: 5px;">
                <span style="font-size: 0.95rem; color: #475569 !important;">Good Morning,</span><br>
                <span style="font-size: 1.6rem; font-weight: 700; color: #006837 !important;">{st.session_state['username']} 👋</span><br>
                <span style="font-size: 0.85rem; color: #64748B !important;">Welcome to your NEOL Internship Portal</span>
            </div>
        """, unsafe_allow_html=True)
    with top_col3:
        st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='font-size: 1.3rem;'>🔔 🌙</span></div>", unsafe_allow_html=True)
    with top_col4:
        selected_dept_dropdown = st.selectbox(
            "Profile Dept", 
            ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"],
            index=["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"].index(st.session_state['department']),
            label_visibility="collapsed"
        )
        st.session_state['department'] = selected_dept_dropdown

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 7. ROUTING PAGE VIEWS
    # ==========================================

    # --- DASHBOARD PAGE ---
    if selected_nav == "Dashboard":
        start_date = date(2026, 10, 1)
        end_date = date(2027, 1, 25)
        today = date.today()

        days_left = max(0, (end_date - today).days)
        total_days = (end_date - start_date).days
        days_passed = (today - start_date).days
        progress_pct = max(0, min(int((days_passed / total_days) * 100), 100))

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
            st.markdown("""
                <div class="metric-card-white">
                    <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">ATTENDANCE</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">87%</h3>
                    <span style="font-size: 0.72rem; color: #64748B !important;">14 / 16 days</span>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown("""
                <div class="metric-card-white">
                    <span style="font-size: 0.75rem; font-weight: bold; color: #64748B !important;">DELIVERABLES</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem; color: #006837 !important;">3 / 4</h3>
                    <span style="font-size: 0.72rem; color: #D97706 !important;">Pending: 1</span>
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
                    template="plotly_white", 
                    paper_bgcolor='#FFFFFF',
                    plot_bgcolor='#F8FAFC',
                    font=dict(color='#0F172A', size=11),
                    height=260, 
                    margin=dict(t=5, b=5, l=5, r=5)
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
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">87%</h2>
                            <p style="font-size: 0.72rem; margin: 0; color: #475569 !important;">🟢 Present</p>
                            <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px; color: #0F172A !important;">14 / 16 days</p>
                        </div>
                    """, unsafe_allow_html=True)
                with att_col2:
                    att_chart_data = pd.DataFrame({
                        "Week": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
                        "Days": [5, 5, 4, 5, 4, 5, 5, 4]
                    })
                    fig_att = px.bar(att_chart_data, x="Week", y="Days", color_discrete_sequence=["#006837"])
                    fig_att.update_layout(
                        template="plotly_white", 
                        paper_bgcolor='#FFFFFF',
                        plot_bgcolor='#F8FAFC',
                        font=dict(color='#0F172A'),
                        height=130, 
                        margin=dict(t=5, b=5, l=5, r=5), 
                        xaxis_title=None, 
                        yaxis_title=None
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
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">75%</h2>
                            <p style="font-size: 0.72rem; margin: 0; color: #475569 !important;">✓ Completed</p>
                            <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px; color: #0F172A !important;">3 / 4</p>
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
            st.markdown("""
                <div class="card-white">
                    <h4 style="margin: 0 0 12px 0; color: #002B15 !important;">⚡ Quick Actions</h4>
            """, unsafe_allow_html=True)
            if st.button("➕ Add Attendance", use_container_width=True):
                st.success("Attendance marked for today!")
            if st.button("📤 Submit Deliverable", use_container_width=True):
                st.info("Navigating to Submissions page...")
            if st.button("📊 View Reports", use_container_width=True):
                st.info("Loading weekly report analytics...")
            if st.button("📥 Download Logbook", use_container_width=True):
                st.success("Logbook summary file downloaded successfully!")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""
                <div class="card-white" style="border-left: 4px solid #FFD100 !important;">
                    <h4 style="margin: 0 0 8px 0; color: #002B15 !important;">📢 Important Notice</h4>
                    <p style="font-size: 0.85rem; font-weight: bold; margin: 0; color: #0F172A !important;">Next Departmental Review</p>
                    <p style="font-size: 0.78rem; color: #64748B !important; margin: 2px 0 8px 0;">📅 Oct 28 – Oct 30, 2026</p>
                    <p style="font-size: 0.75rem; margin: 0; color: #334155 !important;">Ensure your logbook and deliverables are up to date before review.</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="card-white">
                    <h4 style="margin: 0 0 10px 0; color: #002B15 !important;">🕒 Recent Activity</h4>
                    <ul style="padding-left: 15px; font-size: 0.8rem; margin: 0;">
                        <li><b style="color: #0F172A !important;">Week 6 Report Submitted</b><br><span style="color: #64748B !important;">2 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #CBD5E1;">
                        <li><b style="color: #0F172A !important;">Attendance Marked</b><br><span style="color: #64748B !important;">3 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #CBD5E1;">
                        <li><b style="color: #0F172A !important;">New Course Unlocked</b><br><span style="color: #64748B !important;">5 days ago</span></li>
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

    # --- CURRICULUM PAGE ---
    elif selected_nav == "Curriculum":
        current_dept = st.session_state['department']
        st.subheader(f"📖 16-Week Detailed Curriculum — {current_dept} Department")
        
        active_curr = department_curriculums.get(current_dept, department_curriculums["Projects"])
        
        for item in active_curr:
            st.markdown(f"""
                <div class="card-white" style="border-left: 5px solid #006837 !important;">
                    <span style="font-size: 0.8rem; color: #006837 !important; font-weight: bold;">{item['week']}</span>
                    <h3 style="margin: 4px 0 8px 0; color: #0F172A !important;">{item['title']}</h3>
                    <p style="font-size: 0.88rem; color: #475569 !important;"><b>Key Deliverable:</b> {item['deliv']}</p>
                    <span style="background: #F1F5F9; color: {item['color']} !important; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">Status: {item['status']}</span>
                </div>
            """, unsafe_allow_html=True)

    # --- MASTER SCHEDULE PAGE ---
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
            template="plotly_white", paper_bgcolor='#FFFFFF', plot_bgcolor='#F8FAFC',
            font=dict(color='#0F172A', size=12), height=380
        )
        st.plotly_chart(fig_gantt_full, use_container_width=True)

    # --- SUBMISSIONS & DELIVERABLES PAGE ---
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
                
                if submit_btn and rep_topic:
                    st.session_state["submitted_reports"].append({
                        "Week": week_num,
                        "Topic": rep_topic,
                        "Date": str(date.today()),
                        "Status": "Pending Review"
                    })
                    st.success(f"Deliverable for {week_num} successfully uploaded!")

            st.markdown("#### 📜 Submitted Logbook History")
            st.dataframe(pd.DataFrame(st.session_state["submitted_reports"]), use_container_width=True)

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
                    st.warning("Inline preview is optimized for PDF files. Use the download button to open other file types.")
            else:
                st.info("Upload a PDF deliverable on the left to view it live in this window.")

    # --- ONBOARDING DECK PAGE ---
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

    # --- ATTENDANCE PAGE ---
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
                st.session_state["attendance_records"].append({
                    "Date": str(date.today()),
                    "Time": "07:29 AM",
                    "Status": "On Time"
                })
                st.success("Attendance successfully recorded for today!")

        with col_a2:
            st.markdown("#### Attendance Log History")
            st.dataframe(pd.DataFrame(st.session_state["attendance_records"]), use_container_width=True)

    # --- REPORTS PAGE ---
    elif selected_nav == "Reports":
        st.subheader("📊 Analytics & Weekly Performance Reports")
        
        rep_df = pd.DataFrame({
            "Department": ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"],
            "Avg Completion (%)": [75, 80, 70, 85, 65, 90]
        })
        
        fig_rep = px.bar(rep_df, x="Department", y="Avg Completion (%)", color="Department", color_discrete_sequence=["#006837", "#FFD100", "#00A859", "#00381C", "#0B6623", "#2563EB"])
        fig_rep.update_layout(template="plotly_white", paper_bgcolor='#FFFFFF', plot_bgcolor='#F8FAFC', font=dict(color='#0F172A'), height=350)
        st.plotly_chart(fig_rep, use_container_width=True)

    # --- SETTINGS PAGE ---
    elif selected_nav == "Settings":
        st.subheader("⚙️ Portal Settings & User Preferences")
        
        st.markdown("""
            <div class="card-white">
                <h4 style="margin-top: 0;">User Profile Configuration</h4>
            </div>
        """, unsafe_allow_html=True)
        
        st.text_input("Full Name", value=st.session_state["username"])
        st.selectbox("Assigned Department", ["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"], index=["Projects", "Subsurface", "ICT", "Facility", "Legal", "Finance"].index(st.session_state['department']))
        st.text_input("Official Corporate Email", value=f"{st.session_state['username'].lower().replace(' ', '.')}@nnpcgroup.com")
        
        if st.button("Save Profile Settings"):
            st.success("Profile updated successfully!")
