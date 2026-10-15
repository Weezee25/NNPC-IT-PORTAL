import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
import os

# ==========================================
# 1. PAGE CONFIG & EXECUTIVE UI STYLING
# ==========================================
st.set_page_config(
    page_title="NNPC Internship Portal Dashboard",
    page_icon="🇳🇬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .stApp {
        background-color: #F4F6F8;
    }
    .hero-banner {
        background: linear-gradient(135deg, #002B15 0%, #004D25 50%, #006837 100%);
        padding: 28px 35px;
        border-radius: 14px;
        color: white;
        box-shadow: 0 6px 20px rgba(0,0,0,0.12);
        margin-bottom: 20px;
        border-bottom: 4px solid #FFD100;
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 18px 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        border: 1px solid #E5E9EC;
        margin-bottom: 15px;
    }
    .content-card {
        background-color: #FFFFFF;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.04);
        border: 1px solid #E5E9EC;
        margin-bottom: 20px;
    }
    [data-testid="stSidebar"] {
        background-color: #002B15;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

LOGO_PATH = "nnpc.jpeg"

# ==========================================
# 2. SESSION STATE & NAVIGATION INITIALIZATION
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
    # 3. SIDEBAR NAVIGATION
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
            <div style="background-color: rgba(255,255,255,0.06); padding: 15px; border-radius: 10px; border-left: 3px solid #FFD100;">
                <p style="color: #E0E0E0; font-size: 0.85rem; font-style: italic; margin: 0;">
                "Empowering Young Minds, Building a Greater Energy Future."
                </p>
                <p style="color: #FFD100; font-size: 0.75rem; margin-top: 5px; margin-bottom: 0;">— NNPC</p>
            </div>
        """, unsafe_allow_html=True)

    # ==========================================
    # 4. TOP NAVBAR & HEADER BANNER
    # ==========================================
    top_col1, top_col2, top_col3, top_col4 = st.columns([4, 1, 1, 1])
    with top_col1:
        st.markdown(f"""
            <div style="margin-top: 5px;">
                <span style="color: #666; font-size: 0.95rem;">Good Morning,</span><br>
                <span style="color: #002B15; font-size: 1.6rem; font-weight: 700;">{st.session_state['username']} 👋</span><br>
                <span style="color: #777; font-size: 0.85rem;">Welcome to your NEOL Internship Portal</span>
            </div>
        """, unsafe_allow_html=True)
    with top_col3:
        st.markdown("<div style='text-align: right; padding-top: 10px;'><span style='font-size: 1.3rem;'>🔔 🌙</span></div>", unsafe_allow_html=True)
    with top_col4:
        st.selectbox("Profile Dept", ["Projects Department", "ICT Dept", "Subsurface Dept"], label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)

    # ==========================================
    # 5. MAIN DASHBOARD CONTENT AREA
    # ==========================================
    if selected_nav == "Dashboard":
        
        # --- DYNAMIC DATE CALCULATIONS ADDED HERE ---
        start_date = date(2026, 08, 3)
        end_date = date(2026, 11, 30)
        today = date.today()

        days_left = max(0, (end_date - today).days)
        total_days = (end_date - start_date).days
        days_passed = (today - start_date).days
        progress_pct = max(0, min(int((days_passed / total_days) * 100), 100))
        # --------------------------------------------

        col_hb1, col_hb2 = st.columns([3.2, 1.8])
        with col_hb1:
            st.markdown("""
                <div class="hero-banner">
                    <h2 style="color: #FFD100; margin-top: 0; font-size: 1.8rem;">NNPC Eighteen Operating Limited (NEOL)</h2>
                    <p style="font-size: 1.05rem; color: #EFEFEF; margin-bottom: 20px;">Internship Portal — OML 18 Asset Operations</p>
                    <span style="background-color: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 0.85rem; font-weight: 500;">
                    Learn &nbsp;|&nbsp; Contribute &nbsp;|&nbsp; Build Your Future
                    </span>
                </div>
            """, unsafe_allow_html=True)
        with col_hb2:
            # Updated to an f-string to inject {progress_pct}
            st.markdown(f"""
                <div class="metric-card" style="background: linear-gradient(135deg, #00381C 0%, #004D25 100%); color: white; border: none;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 0.85rem; color: #FFD100; font-weight: bold;">📅 Internship Duration</span>
                        <span style="font-size: 0.85rem; background: #006837; padding: 2px 8px; border-radius: 10px;">Active</span>
                    </div>
                    <h3 style="margin: 8px 0 4px 0; font-size: 1.5rem; color: #FFFFFF;">16 Weeks</h3>
                    <p style="font-size: 0.78rem; color: #D0D0D0; margin: 0;">Aug 3, 2026 – Nov 30, 2026</p>
                    <hr style="border-color: rgba(255,255,255,0.15); margin: 10px 0;">
                    <div style="font-size: 0.78rem; display: flex; justify-content: space-between;">
                        <span>Overall Progress</span>
                        <span style="color: #FFD100; font-weight: bold;">{progress_pct}%</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        # Top Metric Cards Row
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; color: #666; font-weight: bold;">ATTENDANCE</span>
                    <h3 style="margin: 5px 0; color: #006837; font-size: 1.4rem;">87%</h3>
                    <span style="font-size: 0.72rem; color: #888;">14 / 16 days</span>
                </div>
            """, unsafe_allow_html=True)
        with m2:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; color: #666; font-weight: bold;">DELIVERABLES</span>
                    <h3 style="margin: 5px 0; color: #006837; font-size: 1.4rem;">3 / 4</h3>
                    <span style="font-size: 0.72rem; color: #D97706;">Pending: 1</span>
                </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; color: #666; font-weight: bold;">ASSIGNMENTS</span>
                    <h3 style="margin: 5px 0; color: #006837; font-size: 1.4rem;">2 / 4</h3>
                    <span style="font-size: 0.72rem; color: #2563EB;">In Progress: 2</span>
                </div>
            """, unsafe_allow_html=True)
        with m4:
            st.markdown("""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; color: #666; font-weight: bold;">COURSES</span>
                    <h3 style="margin: 5px 0; color: #006837; font-size: 1.4rem;">4 / 5</h3>
                    <span style="font-size: 0.72rem; color: #888;">Completed: 4</span>
                </div>
            """, unsafe_allow_html=True)
        with m5:
            # Updated to an f-string to inject {days_left}
            st.markdown(f"""
                <div class="metric-card">
                    <span style="font-size: 0.75rem; color: #666; font-weight: bold;">DAYS LEFT</span>
                    <h3 style="margin: 5px 0; color: #006837; font-size: 1.4rem;">{days_left}</h3>
                    <span style="font-size: 0.72rem; color: #888;">Until Jan 25, 2027</span>
                </div>
            """, unsafe_allow_html=True)

        body_col1, body_col2 = st.columns([2.3, 1])

        with body_col1:
            # Curriculum Card
            st.markdown("""
                <div class="content-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <div>
                            <h4 style="margin: 0; color: #002B15;">📖 My Curriculum</h4>
                            <p style="margin: 0; font-size: 0.8rem; color: #666;">16-Week Training Roadmap — Projects Department</p>
                        </div>
                    </div>
            """, unsafe_allow_html=True)
            
            c_col1, c_col2, c_col3, c_col4 = st.columns(4)
            with c_col1:
                st.markdown("""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px;">
                        <span style="font-size: 0.72rem; color: #006837; font-weight: bold;">Week 1 – 4</span>
                        <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">Project Lifecycle & NUPRC/DPR Regulations</p>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <span style="font-size: 0.7rem; color: #666;">Regulatory Intelligence Framework Summary</span><br>
                        <span style="color: #059669; font-size: 0.72rem; font-weight: bold;">✓ Completed</span>
                    </div>
                """, unsafe_allow_html=True)
            with c_col2:
                st.markdown("""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px;">
                        <span style="font-size: 0.72rem; color: #D97706; font-weight: bold;">Week 5 – 8</span>
                        <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">FEED & Costing</p>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <span style="font-size: 0.7rem; color: #666;">Facility Manifold Engineering Cost Model</span><br>
                        <span style="color: #D97706; font-size: 0.72rem; font-weight: bold;">⏳ In Progress</span>
                    </div>
                """, unsafe_allow_html=True)
            with c_col3:
                st.markdown("""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px;">
                        <span style="font-size: 0.72rem; color: #2563EB; font-weight: bold;">Week 9 – 12</span>
                        <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">Primavera P6 / MS Project Scheduling</p>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <span style="font-size: 0.7rem; color: #666;">Baseline Master Schedule for Pipeline Upgrade</span><br>
                        <span style="color: #6B7280; font-size: 0.72rem; font-weight: bold;">🔒 Not Started</span>
                    </div>
                """, unsafe_allow_html=True)
            with c_col4:
                st.markdown("""
                    <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px; border-radius: 8px;">
                        <span style="font-size: 0.72rem; color: #7C3AED; font-weight: bold;">Week 13 – 16</span>
                        <p style="font-size: 0.8rem; font-weight: bold; margin: 4px 0;">Site Inspections & Commissioning</p>
                        <hr style="margin: 6px 0; border-color: #E2E8F0;">
                        <span style="font-size: 0.7rem; color: #666;">Final Comprehensive Internship Project Report</span><br>
                        <span style="color: #6B7280; font-size: 0.72rem; font-weight: bold;">🔒 Not Started</span>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            # Internship Overview & Master Schedule Side-by-Side
            ov_col1, ov_col2 = st.columns([1, 1.7])
            with ov_col1:
                st.markdown("""
                    <div class="content-card">
                        <h4 style="margin: 0 0 10px 0; color: #002B15; font-size: 1rem;">📌 Internship Overview</h4>
                        <div style="font-size: 0.8rem; color: #444;">
                            <p style="margin: 6px 0;"><b>Duration:</b> 16 Weeks</p>
                            <p style="margin: 6px 0;"><b>Start Date:</b> Oct 1, 2026</p>
                            <p style="margin: 6px 0;"><b>End Date:</b> Jan 25, 2027</p>
                            <p style="margin: 6px 0;"><b>Department:</b> Projects</p>
                            <p style="margin: 6px 0;"><b>Supervisor:</b> To be assigned</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with ov_col2:
                st.markdown("""
                    <div class="content-card">
                        <h4 style="margin: 0 0 5px 0; color: #002B15; font-size: 1rem;">📅 Master Schedule & Milestones</h4>
                        <p style="margin: 0 0 8px 0; font-size: 0.75rem; color: #666;">16-Week OML 18 Roadmap</p>
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

            # --- BOTTOM ANALYTICS PANELS (ATTENDANCE & DELIVERABLES PROGRESS) ---
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown("""
                    <div class="content-card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #002B15; font-size: 0.95rem;">Attendance Overview</h4>
                            <span style="font-size: 0.75rem; color: #006837; font-weight: bold; cursor: pointer;">View Details →</span>
                        </div>
                """, unsafe_allow_html=True)
                att_col1, att_col2 = st.columns([1, 1.5])
                with att_col1:
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837; margin: 0; font-size: 2rem;">87%</h2>
                            <p style="font-size: 0.72rem; color: #666; margin: 0;">🟢 Present</p>
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
                            <h4 style="margin: 0; color: #002B15; font-size: 0.95rem;">Deliverables Progress</h4>
                            <span style="font-size: 0.75rem; color: #006837; font-weight: bold; cursor: pointer;">View All →</span>
                        </div>
                """, unsafe_allow_html=True)
                del_col1, del_col2 = st.columns([1, 1.4])
                with del_col1:
                    st.markdown("""
                        <div style="text-align: center; padding-top: 15px;">
                            <h2 style="color: #006837; margin: 0; font-size: 2rem;">75%</h2>
                            <p style="font-size: 0.72rem; color: #666; margin: 0;">✓ Completed</p>
                            <p style="font-size: 0.75rem; font-weight: bold; margin-top: 5px;">3 / 4</p>
                        </div>
                    """, unsafe_allow_html=True)
                with del_col2:
                    st.markdown("""
                        <div style="font-size: 0.75rem; color: #444; padding-top: 5px;">
                            <p style="margin: 4px 0;">✔️ Regulatory Summary</p>
                            <p style="margin: 4px 0;">✔️ Cost Model</p>
                            <p style="margin: 4px 0;">🟡 Schedule Report</p>
                            <p style="margin: 4px 0; color: #888;">⚪ Final Report</p>
                        </div>
                    """, unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)

        with body_col2:
            st.markdown("""
                <div class="content-card">
                    <h4 style="margin: 0 0 12px 0; color: #002B15;">⚡ Quick Actions</h4>
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
                <div class="content-card" style="border-left: 4px solid #FFD100;">
                    <h4 style="margin: 0 0 8px 0; color: #002B15;">📢 Important Notice</h4>
                    <p style="font-size: 0.85rem; font-weight: bold; margin: 0;">Next Departmental Review</p>
                    <p style="font-size: 0.78rem; color: #555; margin: 2px 0 8px 0;">📅 Oct 28 – Oct 30, 2026</p>
                    <p style="font-size: 0.75rem; color: #666; margin: 0;">Ensure your logbook and deliverables are up to date before review.</p>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div class="content-card">
                    <h4 style="margin: 0 0 10px 0; color: #002B15;">🕒 Recent Activity</h4>
                    <ul style="padding-left: 15px; font-size: 0.8rem; color: #444; margin: 0;">
                        <li><b>Week 6 Report Submitted</b><br><span style="color: #888;">2 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #F0F0F0;">
                        <li><b>Attendance Marked</b><br><span style="color: #888;">3 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #F0F0F0;">
                        <li><b>New Course Unlocked</b><br><span style="color: #888;">5 days ago</span></li>
                        <hr style="margin: 6px 0; border-color: #F0F0F0;">
                        <li><b>Deliverable Updated</b><br><span style="color: #888;">FEED & Costing Document</span></li>
                    </ul>
                </div>
            """, unsafe_allow_html=True)

            st.markdown("""
                <div style="background: linear-gradient(135deg, #002B15 0%, #004D25 100%); padding: 18px; border-radius: 12px; color: white; text-align: center;">
                    <p style="font-size: 0.82rem; font-weight: bold; color: #FFD100; margin: 0 0 5px 0;">Grow. Learn. Make an Impact.</p>
                    <p style="font-size: 0.72rem; color: #E0E0E0; margin: 0 0 10px 0;">Your skills today power the energy of tomorrow.</p>
                    <span style="font-size: 0.68rem; color: #AAA;">— NNPC</span>
                </div>
            """, unsafe_allow_html=True)

    else:
        st.subheader(f"📂 {selected_nav} Portal Module")
        st.info(f"You are currently viewing the **{selected_nav}** module for the **{st.session_state['department']} Department**.")
