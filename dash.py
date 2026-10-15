import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os
import base64

# ==========================================
# 1. PAGE CONFIG & THEME-COMPATIBLE CSS
# ==========================================
st.set_page_config(
    page_title="NNPC Internship Portal Dashboard",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    /* App Canvas Adaptation */
    .stApp {
        background-color: var(--background-color);
    }
    
    /* Hero Banner (Locked Dark Green Theme) */
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%);
        padding: 28px 35px;
        border-radius: 14px;
        color: #FFFFFF !important;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        margin-bottom: 20px;
        border-bottom: 4px solid #FFD100;
    }
    .hero-banner h2 { color: #FFD100 !important; }
    .hero-banner p { color: #EFEFEF !important; }
    .hero-banner span { color: #FFFFFF !important; }

    /* Metric Cards (Locked Light Theme with Explicit Dark Text) */
    .metric-card {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        padding: 18px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #CBD5E1;
        margin-bottom: 15px;
    }
    .metric-card span { color: #475569 !important; }
    .metric-card h3 { color: #006837 !important; }

    /* Content Cards (Locked Light Theme with Explicit Dark Text) */
    .content-card {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.06);
        border: 1px solid #CBD5E1;
        margin-bottom: 20px;
    }
    .content-card h4 { color: #002B15 !important; }
    .content-card p, .content-card span, .content-card li, .content-card div, .content-card b {
        color: #1E293B !important;
    }

    /* Sidebar Theme Lock (Always Dark Green with White Text) */
    [data-testid="stSidebar"] {
        background-color: #002B15 !important;
    }
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    [data-testid="stSidebar"] .stRadio label p {
        color: #FFFFFF !important;
    }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "nnpc.jpeg"

# ==========================================
# HELPER FUNCTION: INLINE PDF VIEWER
# ==========================================
def render_pdf_viewer(file_bytes):
    """Embeds an interactive PDF viewer using HTML iframe."""
    base64_pdf = base64.b64encode(file_bytes).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="550" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# ==========================================
# 2. DEPARTMENT CURRICULUM DATA DICTIONARY
# ==========================================
department_curriculums = {
    "Projects": [
        {"week": "Week 1 – 4", "title": "Project Lifecycle & NUPRC Regulations", "deliv": "Regulatory Intelligence Framework Summary", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "FEED & Costing Models", "deliv": "Facility Manifold Engineering Cost Model", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Primavera P6 / MS Project Scheduling", "deliv": "Baseline Master Schedule for Pipeline Upgrade", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Site Inspections & Commissioning", "deliv": "Final Comprehensive Internship Project Report", "status": "🔒 Not Started", "color": "#6B7280"}
    ],
    "Subsurface": [
        {"week": "Week 1 – 4", "title": "2D/3D Seismic Horizon Mapping", "deliv": "Seismic Horizon Mapping & Structural Framework Report", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Petrophysical Log Evaluation", "deliv": "Net Pay & Water Saturation Determination Sheet", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Reservoir Material Balance Calculations", "deliv": "Reserves Estimation & Decline Curve Analysis", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Static & Dynamic Reservoir Modeling", "deliv": "Integrated Subsurface Reservoir Simulation Model", "status": "🔒 Not Started", "color": "#6B7280"}
    ],
    "ICT": [
        {"week": "Week 1 – 4", "title": "Network Infrastructure & Cybersecurity", "deliv": "Network Configuration Topology & Security Audit", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Enterprise Systems & Database Admin", "deliv": "User Management & Database Audit Report", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Software Engineering & ITIL Service Desk", "deliv": "Internal Service Desk Automation Script", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Cloud Infrastructure & Deployment", "deliv": "Final Cloud Application System Deployment", "status": "🔒 Not Started", "color": "#6B7280"}
    ],
    "Facility": [
        {"week": "Week 1 – 4", "title": "HVAC & Power Distribution Systems", "deliv": "Facility Equipment Maintenance Log & Safety Check", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "HSE & Emergency Response Protocols", "deliv": "Departmental Hazard Identification Assessment", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Asset Integrity & Building Management", "deliv": "Preventive Facility Maintenance Schedule", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Energy Efficiency & Auditing", "deliv": "Facility Energy Optimization Strategy Report", "status": "🔒 Not Started", "color": "#6B7280"}
    ],
    "Legal": [
        {"week": "Week 1 – 4", "title": "Petroleum Industry Act (PIA) Framework", "deliv": "PIA Regulatory Impact Analysis Memo", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Production Sharing Contracts & Joint Ventures", "deliv": "Joint Venture Legal Contract Review Brief", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "Corporate Governance & Dispute Resolution", "deliv": "Arbitration & Legal Dispute Case Study", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Environmental & Energy Law Compliance", "deliv": "Regulatory Environmental Compliance Checklist", "status": "🔒 Not Started", "color": "#6B7280"}
    ],
    "Finance": [
        {"week": "Week 1 – 4", "title": "Oil & Gas Cost Accounting Fundamentals", "deliv": "Cost Allocation & Financial Audit Report", "status": "✓ Completed", "color": "#059669"},
        {"week": "Week 5 – 8", "title": "Joint Venture Cash Calls & Billing", "deliv": "Joint Venture Cash Call Reconciliation Sheet", "status": "⏳ In Progress", "color": "#D97706"},
        {"week": "Week 9 – 12", "title": "CAPEX & OPEX Budget Forecasting", "deliv": "Quarterly Financial Forecast & Budget Model", "status": "🔒 Not Started", "color": "#6B7280"},
        {"week": "Week 13 – 16", "title": "Tax Compliance & Financial Auditing", "deliv": "Final Corporate Tax Compliance Summary", "status": "🔒 Not Started", "color": "#6B7280"}
    ]
}

# ==========================================
# 3. SESSION STATE & NAVIGATION
# ==========================================
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = "Alex"
if "department" not in st.session_state:
    st.session_state["department"] = "Projects"

if not st.session_state["logged_in"]:
    col_l1, col_l2, col_l3 = st.columns([1, 1.5, 1])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        if os.path.exists(LOGO_PATH):
            st.image(LOGO_PATH, width=180)
        else:
            st.title("🇳🇬 NNPC")
            
        st.markdown("### NEOL Internship Portal Sign-In")
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
    # 4. SIDEBAR NAVIGATION
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
    # 5. TOP NAVBAR
    # ==========================================
    top_col1, top_col2, top_col3, top_col4 = st.columns([3.5, 1, 1, 1.5])
    with top_col1:
        st.markdown(f"""
            <div style="margin-top: 5px;">
                <span style="color: var(--text-color, #475569); font-size: 0.95rem;">Good Morning,</span><br>
                <span style="color: #006837; font-size: 1.6rem; font-weight: 700;">{st.session_state['username']} 👋</span><br>
                <span style="color: var(--text-color, #64748B); font-size: 0.85rem;">Welcome to your NEOL Internship Portal</span>
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
    # 6. MAIN DASHBOARD CONTENT AREA
    # ==========================================
    if selected_nav == "Dashboard":
        
        # Dynamic Date Math
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
                <div class="metric-card" style="background: linear-gradient(135deg, #00381C 0%, #004D25 100%) !important; color: white !important; border: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.85rem; color: #FFD100 !important; font-weight: bold;">📅 Internship Duration</span>
                        <span style="font-size: 0.85rem; background: #006837; padding: 2px 8px; border-radius: 10px; color: white !important;">Active</span>
                    </div>
                    <h3 style="margin: 8px 0 4px 0; font-size: 1.5rem; color: #FFFFFF !important;">16 Weeks</h3>
                    <p style="font-size: 0.78rem; color: #D0D0D0 !important; margin: 0;">Oct 1, 2026 – Jan 25, 2027</p>
                    <hr style="border-color: rgba(255,255,255,0.15); margin: 10px 0;">
                    <div style="font-size: 0.78rem; display: flex; justify-content: space-between;">
                        <span style="color: #FFFFFF !important;">Overall Progress</span>
                        <span style="color: #FFD100 !important; font-weight: bold;">{progress_pct}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Top Metric Cards Row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; font-weight: bold;">ATTENDANCE</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem;">87%</h3>
                    <span style="font-size: 0.72rem;">14 / 16 days</span>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; font-weight: bold;">DELIVERABLES</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem;">3 / 4</h3>
                    <span style="font-size: 0.72rem; color: #D97706 !important;">Pending: 1</span>
                </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; font-weight: bold;">ASSIGNMENTS</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem;">2 / 4</h3>
                    <span style="font-size: 0.72rem; color: #2563EB !important;">In Progress: 2</span>
                </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; font-weight: bold;">COURSES</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem;">4 / 5</h3>
                    <span style="font-size: 0.72rem;">Completed: 4</span>
                </div>
            """, unsafe_allow_html=True)
        with m5:
            st.markdown(f"""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; font-weight: bold;">DAYS LEFT</span>
                    <h3 style="margin: 5px 0; font-size: 1.4rem;">{days_left}</h3>
                    <span style="font-size: 0.72rem;">Until Jan 25, 2027</span>
                </div>
            """, unsafe_allow_html=True)

        body_col1, body_col2 = st.columns([2.3, 1])

        with body_col1:
            # Dynamic Curriculum Section
            current_dept = st.session_state['department']
            active_curr = department_curriculums.get(current_dept, department_curriculums["Projects"])

            st.markdown(f"""
                <div class="content-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <h4 style="margin: 0;">📖 My Curriculum</h4>
                            <p style="margin: 0; font-size: 0.8rem;">16-Week Training Roadmap — <b style="color: #006837 !important;">{current_dept} Department</b></p>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            c_cols = st.columns(4)
            for i, phase in enumerate(active_curr):
                with c_cols[i]:
                    st.markdown(f"""
                        <div style="background: #F8FAFC; border: 1px solid #CBD5E1; padding: 12px; border-radius: 8px; min-height: 140px;">
                            <span style="font-size: 0.72rem; color: #006837 !important; font-weight: bold;">{phase['week']}</span>
                            <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0; color: #0F172A !important;">{phase['title']}</p>
                            <hr style="margin: 6px 0; border-color: #CBD5E1;">
                            <span style="font-size: 0.7rem; color: #334155 !important;">{phase['deliv']}</span><br>
                            <span style="color: {phase['color']} !important; font-size: 0.72rem; font-weight: bold;">{phase['status']}</span>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Overview & Master Schedule
            ov_col1, ov_col2 = st.columns([1, 1.7])
            with ov_col1:
                st.markdown(f"""
                    <div class="content-card">
                        <h4 style="margin: 0 0 10px 0; font-size: 1rem;">📌 Internship Overview</h4>
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
                    <div class="content-card">
                        <h4 style="margin: 0 0 5px 0; font-size: 1rem;">📅 Master Schedule & Milestones</h4>
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
                fig_gantt.update_layout(template="plotly_white", height=195, margin=dict(t=5, b=5, l=5, r=5))
                st.plotly_chart(fig_gantt, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Bottom Analytics Panels
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown("""
                    <div class="content-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; font-size: 0.95rem;">Attendance Overview</h4>
                            <span style="font-size: 0.75rem; color: #006837 !important; font-weight: bold; cursor: pointer;">View Details →</span>
                        </div>
                """, unsafe_allow_html=True)
                att_col1, att_col2 = st.columns([1, 1.5])
                with att_col1:
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">87%</h2>
                            <p style="font-size: 0.72rem; margin: 0;">🟢 Present</p>
                            <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px;">14 / 16 days</p>
                        </div>
                    """, unsafe_allow_html=True)
                with att_col2:
                    att_chart_data = pd.DataFrame({
                        "Week": ["W1", "W2", "W3", "W4", "W5", "W6", "W7", "W8"],
                        "Days": [5, 5, 4, 5, 4, 5, 5, 4]
                    })
                    fig_att = px.bar(att_chart_data, x="Week", y="Days", color_discrete_sequence=["#006837"])
                    fig_att.update_layout(template="plotly_white", height=130, margin=dict(t=5, b=5, l=5, r=5), xaxis_title=None, yaxis_title=None)
                    st.plotly_chart(fig_att, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with b_col2:
                st.markdown("""
                    <div class="content-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; font-size: 0.95rem;">Deliverables Progress</h4>
                            <span style="font-size: 0.75rem; color: #006837 !important; font-weight: bold; cursor: pointer;">View All →</span>
                        </div>
                """, unsafe_allow_html=True)
                del_col1, del_col2 = st.columns([1, 1.4])
                with del_col1:
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837 !important; margin: 0; font-size: 2rem;">75%</h2>
                            <p style="font-size: 0.72rem; margin: 0;">✓ Completed</p>
                            <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px;">3 / 4</p>
                        </div>
                    """, unsafe_allow_html=True)
                with del_col2:
                    st.markdown("""
                        <div style="font-size: 0.75rem; padding-top: 5px;">
                            <p style="margin: 4px 0;">✔️ Regulatory Summary</p>
                            <p style="margin: 4px 0;">✔️ Cost Model</p>
                            <p style="margin: 4px 0; color: #D97706 !important;">🟡 Schedule Report</p>
                            <p style="margin: 4px 0; color: #94A3B8 !important;">⚪ Final Report</p>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with body_col2:
            st.markdown("""
                <div class="content-card">
                    <h4 style="margin: 0 0 12px 0;">⚡ Quick Actions</h4>
            """, unsafe_allow_html=True)
            if st.button("➕ Add Attendance", use_container_width=True):
                st.success("Attendance marked for today!")
            if st.button("📤 Submit Deliverable", use_container_width=True):
                st.info("Opening deliverable submission upload form...")
            if st.button("📊 View Reports", use_container_width=True):
                st.info("Loading weekly report analytics...")
            if st.button("📥 Download Logbook", use_container_width=True):
                st.success("Logbook summary file downloaded successfully!")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""
                <div class="content-card" style="border-left: 4px solid #FFD100 !important;">
                    <h4 style="margin: 0 0 8px 0;">📢 Important Notice</h4>
                    <p style="font-size: 0.85rem; font-weight: bold; margin: 0;">Next Departmental Review</p>
                    <p style="font-size: 0.78rem; color: #64748B !important; margin: 2px 0 8px 0;">📅 Oct 28 – Oct 30, 2026</p>
                    <p style="font-size: 0.75rem; margin: 0;">Ensure your logbook and deliverables are up to date before review.</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="content-card">
                    <h4 style="margin: 0 0 10px 0;">🕒 Recent Activity</h4>
                    <ul style="padding-left: 15px; font-size: 0.8rem; margin: 0;">
                        <li><b style="color: #0F172A !important;">Week 6 Report Submitted</b><br><span style="color: #64748B !important;">2 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <li><b style="color: #0F172A !important;">Attendance Marked</b><br><span style="color: #64748B !important;">3 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <li><b style="color: #0F172A !important;">New Course Unlocked</b><br><span style="color: #64748B !important;">5 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <li><b style="color: #0F172A !important;">Deliverable Updated</b><br><span style="color: #64748B !important;">FEED & Costing Document</span></li>
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

    # ==========================================
    # 7. ONBOARDING & DELIVERABLE FILE VIEWER PAGE
    # ==========================================
    elif selected_nav in ["Onboarding Deck", "Submissions", "Deliverables"]:
        st.subheader(f"📄 {selected_nav} Document Viewer & Upload Portal")
        
        col_up1, col_up2 = st.columns([1, 1.2])
        
        with col_up1:
            st.markdown("""
                <div class="content-card">
                    <h4 style="margin-top: 0;">📤 Upload & View Documents</h4>
                    <p style="font-size: 0.85rem;">Upload PDF reports, slides (.pptx), or logbooks. PDFs will render directly inside the interactive viewer on the right.</p>
                </div>
            """, unsafe_allow_html=True)
            
            uploaded_doc = st.file_uploader(
                "Select File to Upload & Preview", 
                type=['pdf', 'pptx', 'docx', 'xlsx'],
                key="doc_uploader"
            )
            
            if uploaded_doc:
                st.success(f"File `{uploaded_doc.name}` uploaded successfully!")
                st.write(f"**File Type:** `{uploaded_doc.type}` | **Size:** `{uploaded_doc.size / 1024:.2f} KB`")
                
                st.download_button(
                    label=f"📥 Download {uploaded_doc.name}",
                    data=uploaded_doc.getvalue(),
                    file_name=uploaded_doc.name,
                    mime=uploaded_doc.type
                )
        
        with col_up2:
            st.markdown("""
                <div class="content-card">
                    <h4 style="margin-top: 0;">👁️ Document Live Previewer</h4>
                </div>
            """, unsafe_allow_html=True)
            
            if uploaded_doc is not None:
                if uploaded_doc.name.endswith(".pdf"):
                    st.info(f"Rendering PDF preview for `{uploaded_doc.name}`:")
                    render_pdf_viewer(uploaded_doc.getvalue())
                else:
                    st.warning("Inline rendering is supported for PDF files. For PPTX, DOCX, and XLSX files, use the download button to open in your system viewer.")
            else:
                st.info("No file uploaded yet. Upload a PDF file using the uploader on the left to preview it directly on this screen.")

    else:
        st.subheader(f"📂 {selected_nav} Portal Module")
        st.info(f"You are currently viewing the **{selected_nav}** module for the **{st.session_state['department']} Department**.")
