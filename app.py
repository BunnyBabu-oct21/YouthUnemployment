"""Youth Unemployment in India - storytelling dashboard (Streamlit + Pandas + Plotly).

Run:  streamlit run app.py
Data: data/youth_unemployment_india_plfs.csv (bundled; there is deliberately no upload widget).
"""
import plotly.graph_objects as go
import streamlit as st

import utils as u

# --------------------------------------------------------------------------- #
# Page setup, theme and responsive CSS
# --------------------------------------------------------------------------- #
st.set_page_config(page_title="Youth Unemployment | Storytelling Dashboard",
                   page_icon="📊", layout="wide", initial_sidebar_state="auto")

NAVY, BLUE, MID, LIGHT, ACCENT, GREEN, GREY = "#1B2A4A", "#2F5DA8", "#5B8DD6", "#A9C4EC", "#E4572E", "#2E9E6B", "#6B7A90"

st.markdown(f"""
<style>
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
[data-testid="stSidebar"] {{ background: {NAVY}; }}
[data-testid="stSidebar"] * {{ color: #E8EEF8 !important; }}
[data-testid="stSidebar"] [data-baseweb="select"] * {{ color: {NAVY} !important; }}
h1.page-title {{ color:{NAVY}; font-size:clamp(1.3rem,3.2vw,2rem); margin:0 0 .15rem 0; font-weight:800; }}
.page-sub {{ color:{GREY}; font-size:.95rem; margin-bottom:1rem; }}
.kpi-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr)); gap:12px; margin-bottom:1rem; }}
.kpi {{ background:#fff; border:1px solid #DCE4F0; border-radius:10px; padding:20px 16px; }}
.kpi .l {{ color:{GREY}; font-size:.72rem; letter-spacing:.05em; font-weight:600; }}
.kpi .v {{ color:{NAVY}; font-size:clamp(1.4rem,3vw,1.9rem); font-weight:800; line-height:1.2; }}
.kpi .v.good {{ color:{GREEN}; }}
.kpi .s {{ color:{GREY}; font-size:.75rem; }}
.chart-title {{ color:{NAVY}; font-weight:700; font-size:1.02rem; margin:.4rem 0 0 0; }}
.story {{ background:#fff; border-left:5px solid {BLUE}; border-radius:6px; padding:12px 16px; margin:.6rem 0; }}
.story b.tag {{ color:{BLUE}; letter-spacing:.03em; }}
.story .head {{ color:{BLUE}; font-weight:800; font-size:1.05rem; }}
.story .obs {{ color:{NAVY}; margin-top:.25rem; }}
.story .act {{ color:{GREY}; margin-top:.25rem; font-size:.92rem; }}
.note {{ background:#EAF0FA; border-radius:8px; padding:10px 14px; margin:.4rem 0; color:{NAVY}; font-size:.9rem; }}
.note .t {{ font-weight:700; font-size:.72rem; letter-spacing:.06em; color:{GREY}; display:block; }}
.foot {{ color:#8A97AB; font-size:.78rem; margin-top:1.2rem; }}
.mini-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:8px; }}
.mini {{ background:#fff; border:1px solid #DCE4F0; border-radius:8px; padding:8px 12px; color:{NAVY}; }}
.mini small {{ color:{GREY}; display:block; }}
@media (max-width: 640px) {{
  .block-container {{ padding-left:.8rem; padding-right:.8rem; }}
  .story, .note {{ padding:10px 12px; }}
}}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
@st.cache_data
def get_data():
    return u.load_data()


def show(fig, height=380):
    """Render a Plotly figure full-width (works on old and new Streamlit versions)."""
    fig.update_layout(
        height=height, margin=dict(l=8, r=12, t=28, b=8), paper_bgcolor="#fff", plot_bgcolor="#fff",
        font=dict(family="Inter, Segoe UI, Arial", color=NAVY, size=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    try:
        st.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, theme=None)


def chart_title(text):
    st.markdown(f'<div class="chart-title">{text}</div>', unsafe_allow_html=True)


def kpi_row(items):
    cards = "".join(
        f'<div class="kpi"><div class="l">{k["label"]}</div>'
        f'<div class="v {"good" if k.get("good") else ""}">{k["value"]}</div>'
        f'<div class="s">{k.get("sub", "")}</div></div>' for k in items)
    st.markdown(f'<div class="kpi-grid">{cards}</div>', unsafe_allow_html=True)


def story(n, head, obs, action):
    st.markdown(
        f'<div class="story"><span class="head"><b class="tag">STORY {n:02d}</b> &nbsp;|&nbsp; {head}</span>'
        f'<div class="obs">{obs}</div><div class="act"><b>Action:</b> {action}</div></div>',
        unsafe_allow_html=True)


def note(title, text):
    st.markdown(f'<div class="note"><span class="t">{title}</span>{text}</div>', unsafe_allow_html=True)


def header(title, sub="A guided story from headline numbers to the groups and places that need attention"):
    st.markdown(f'<h1 class="page-title">{title}</h1><div class="page-sub">{sub}</div>', unsafe_allow_html=True)


def blue_scale(vals):
    """Map values to shades of blue (darker = higher)."""
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    shades = ["#A9C4EC", "#7DA6E0", "#5B8DD6", "#3E70BD", "#2F5DA8", "#244B8C", "#1B3A70"]
    return [shades[int((v - lo) / span * (len(shades) - 1))] for v in vals]


def add_basis_breaks(fig, t):
    """Mark where the survey reference period changes (Jul-Jun -> Jan-Dec)."""
    for i in range(1, len(t)):
        if t.Period_Basis.iloc[i] != t.Period_Basis.iloc[i - 1]:
            fig.add_shape(type="line", x0=i - 0.5, x1=i - 0.5, y0=0, y1=1, xref="x", yref="paper",
                          line=dict(color=ACCENT, width=1.5, dash="dot"))
            fig.add_annotation(x=i - 0.5, y=1, xref="x", yref="paper", text="Basis changes: Jul-Jun to Jan-Dec",
                               showarrow=False, font=dict(size=10, color=ACCENT), yanchor="bottom")


def edu_bar(e, height=380):
    d = e.iloc[::-1]  # lowest education at the top when read downwards
    fig = go.Figure(go.Bar(
        x=d.Value_Percent, y=d.Education_Level, orientation="h", marker_color=blue_scale(list(d.Value_Percent)),
        text=[f"{v:.1f}%" for v in d.Value_Percent], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>"))
    fig.update_xaxes(title="Youth unemployment rate (%)", gridcolor="#EEF2F8", range=[0, max(d.Value_Percent.max() * 1.18, 1)])
    fig.update_yaxes(automargin=True)
    show(fig, height)


# --------------------------------------------------------------------------- #
# Sidebar: navigation + filters
# --------------------------------------------------------------------------- #
df = get_data()

st.sidebar.markdown("## YOUTH\n## JOBS STORY")
PAGES = ["Overview", "Trends", "Education Insights", "Gender & Sector", "State Analysis", "Data Explorer"]
page = st.sidebar.radio("DASHBOARD", PAGES, label_visibility="visible")

st.sidebar.markdown("---")
st.sidebar.markdown("**Filters**")
start, end = st.sidebar.select_slider("Period range (trend views)", options=u.PERIOD_ORDER,
                                      value=(u.PERIOD_ORDER[0], u.PERIOD_ORDER[-1]))
sector = st.sidebar.selectbox("Sector (education views)", u.SECTORS, index=0)
levels = st.sidebar.multiselect("Education levels", u.EDU_ORDER, default=u.EDU_ORDER)
states = st.sidebar.multiselect("States (state view)", u.all_states(df), default=u.all_states(df))
st.sidebar.caption("Filters apply wherever the data supports them. PLFS publishes education and "
                   "rural/urban detail for 2025 and state detail for 2023-24 only.")

if page != "Data Explorer":
    kpi_row(u.kpis(df, start, end, sector))

# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
if page == "Overview":
    header("Youth Unemployment | Executive Overview")
    left, right = st.columns([3, 2])
    with left:
        chart_title("1. National trend, youth (15-29) unemployment rate")
        t = u.national_trend(df, start, end)
        if t.empty:
            st.info("No data for this period range.")
        else:
            fig = go.Figure(go.Scatter(
                x=t.Period, y=t.Value_Percent, mode="lines+markers+text", line=dict(color=BLUE, width=3),
                marker=dict(size=9), fill="tozeroy", fillcolor="rgba(47,93,168,0.10)",
                text=[f"{v:.1f}" for v in t.Value_Percent], textposition="top center",
                hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>"))
            add_basis_breaks(fig, t)
            fig.update_yaxes(title="Unemployment rate (%)", range=[0, max(t.Value_Percent.max() * 1.25, 1)], gridcolor="#EEF2F8")
            fig.update_xaxes(type="category")
            show(fig, 380)
    with right:
        chart_title(f"2. Rate by education level, 2025 ({sector})")
        e = u.education_rates(df, sector=sector, levels=levels)
        if e.empty:
            st.info("Select at least one education level.")
        else:
            edu_bar(e, 380)
    story(1, "Headline unemployment is easing, but it is not evenly shared.",
          u.story_overview(df, sector, levels),
          "Look beyond the national average: target skilling and job-matching at the groups with the highest rates.")
    note("HOW TO READ THIS", "Start with the KPIs, check whether the trend line is falling or flat, then compare "
         "education groups. The dotted line marks a change in the survey reference period, so treat comparisons "
         "across it with care.")

elif page == "Trends":
    header("Youth Unemployment Trends | Is It Getting Better?")
    t = u.national_trend(df, start, end)
    if t.empty:
        st.info("No data for this period range.")
    else:
        chart_title("Youth unemployment rate over time")
        fig = go.Figure(go.Scatter(
            x=t.Period, y=t.Value_Percent, mode="lines+markers+text", line=dict(color=BLUE, width=3),
            marker=dict(size=10), text=[f"{v:.1f}%" for v in t.Value_Percent], textposition="top center",
            hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>"))
        add_basis_breaks(fig, t)
        fig.update_yaxes(title="Unemployment rate (%)", range=[0, max(t.Value_Percent.max() * 1.25, 1)], gridcolor="#EEF2F8")
        fig.update_xaxes(type="category")
        show(fig, 360)

        left, right = st.columns([3, 2])
        with left:
            chart_title("Change vs previous period (percentage points)")
            c = t.dropna(subset=["Change_pp"])
            if c.empty:
                st.info("Select two or more periods to see changes.")
            else:
                fig = go.Figure(go.Bar(
                    x=c.Period, y=c.Change_pp, marker_color=[GREEN if v < 0 else ACCENT for v in c.Change_pp],
                    text=[f"{v:+.1f}" for v in c.Change_pp], textposition="outside", cliponaxis=False,
                    hovertemplate="%{x}<br>%{y:+.1f} pp<extra></extra>"))
                fig.update_yaxes(title="pp change", gridcolor="#EEF2F8", zeroline=True, zerolinecolor=GREY)
                fig.update_xaxes(type="category")
                show(fig, 320)
        with right:
            chart_title("Rural vs urban, 2025")
            s = u.sector_compare(df)
            fig = go.Figure(go.Bar(
                x=s.Sector, y=s.Value_Percent, marker_color=[MID, LIGHT, BLUE][: len(s)],
                text=[f"{v:.1f}%" for v in s.Value_Percent], textposition="outside", cliponaxis=False))
            fig.update_yaxes(title="Rate (%)", gridcolor="#EEF2F8", range=[0, s.Value_Percent.max() * 1.25])
            show(fig, 320)
    story(2, "The big improvement came early, and progress has since flattened.",
          u.story_trend(df, start, end),
          "Check which policies or economic events coincide with the fall, and ask why recent years move by tenths of a point.")
    note("DECISION PROMPT", "Is a rate near 10% a new normal? Compare with job-creation data before deciding whether the recovery has stalled.")
    note("DATA CAUTION", "2020-21 to 2023-24 are July-June survey years; 2024 and 2025 are January-December. "
         "Small changes across that boundary may partly reflect the change in reference period.")

elif page == "Education Insights":
    header("Education Insights | Does More Schooling Mean More Jobs?")
    e = u.education_rates(df, sector=sector, levels=levels)
    w = u.education_by_sex(df, sector=sector, levels=levels)
    if e.empty:
        st.info("Select at least one education level in the sidebar.")
    else:
        left, right = st.columns([2, 3])
        with left:
            chart_title(f"Rate by education level, 2025 ({sector})")
            edu_bar(e, 420)
        with right:
            chart_title("The education ladder: male vs female")
            fig = go.Figure()
            for sex, colr in [("Male", BLUE), ("Female", ACCENT), ("Everyone", GREY)]:
                fig.add_trace(go.Scatter(x=w.Education_Level, y=w[sex], mode="lines+markers", name=sex,
                                         line=dict(color=colr, width=3 if sex != "Everyone" else 2,
                                                   dash="solid" if sex != "Everyone" else "dot"),
                                         hovertemplate="%{x}<br>" + sex + ": %{y:.1f}%<extra></extra>"))
            fig.update_yaxes(title="Unemployment rate (%)", gridcolor="#EEF2F8")
            fig.update_xaxes(tickangle=-35, automargin=True)
            show(fig, 420)
    story(3, "Higher education is not shielding young people from unemployment.",
          u.story_education(df, sector, levels),
          "Prioritise graduate-level employability: industry-linked curricula, apprenticeships and diploma-to-job pathways.")
    note("DECISION PROMPT", "Are graduates unemployed because jobs are scarce, or because they are waiting for better-matched work? "
         "This dataset cannot tell; pair it with vacancy and wage data.")
    note("DATA CAUTION", "'Literate, without formal schooling' shows 0.0% in every cut. Very small sample sizes are a likely reason; avoid reading too much into it.")

elif page == "Gender & Sector":
    header("Gender & Sector | Who Is Hardest Hit?")
    w = u.education_by_sex(df, sector=sector, levels=levels)
    if w.empty:
        st.info("Select at least one education level in the sidebar.")
    else:
        left, right = st.columns(2)
        with left:
            chart_title(f"Male vs female rate by education ({sector})")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=w.Education_Level, y=w.Male, name="Male", marker_color=BLUE))
            fig.add_trace(go.Bar(x=w.Education_Level, y=w.Female, name="Female", marker_color=ACCENT))
            fig.update_layout(barmode="group")
            fig.update_yaxes(title="Rate (%)", gridcolor="#EEF2F8")
            fig.update_xaxes(tickangle=-35, automargin=True)
            show(fig, 400)
        with right:
            chart_title("Gender gap: female minus male (pp)")
            g = w.dropna(subset=["Gap_F_minus_M"])
            fig = go.Figure(go.Bar(
                x=g.Education_Level, y=g.Gap_F_minus_M,
                marker_color=[ACCENT if v > 0 else BLUE for v in g.Gap_F_minus_M],
                text=[f"{v:+.1f}" for v in g.Gap_F_minus_M], textposition="outside", cliponaxis=False))
            fig.update_yaxes(title="pp (above 0 = women higher)", gridcolor="#EEF2F8", zeroline=True, zerolinecolor=GREY)
            fig.update_xaxes(tickangle=-35, automargin=True)
            show(fig, 400)

        chart_title("Heat-map: every education x sex x sector combination (2025)")
        m = u.heat_matrix(df, levels=levels)
        fig = go.Figure(go.Heatmap(
            z=m.values, x=[c.replace(" | ", " · ") for c in m.columns], y=list(m.index),
            colorscale="Blues", text=m.values, texttemplate="%{text:.1f}", xgap=2, ygap=2,
            colorbar=dict(title="%"), hovertemplate="%{y}<br>%{x}: %{z:.1f}%<extra></extra>"))
        fig.update_yaxes(autorange="reversed", automargin=True)
        fig.update_xaxes(side="top", tickangle=-30)
        show(fig, 460)
    story(4, "The gender gap reverses with education: women face far higher rates at graduate level.",
          u.story_gender(df, sector, levels),
          "Investigate barriers for educated women (job availability, location, safety, work-hour flexibility) before designing programmes.")
    note("DECISION PROMPT", "Should skilling programmes for women focus on matching existing qualifications to jobs rather than adding more credentials?")

elif page == "State Analysis":
    header("State Analysis | Where Is the Pressure?")
    s = u.state_rates(df, states)
    nat = u.national_reference(df)
    if s.empty:
        st.info("Select at least one state in the sidebar.")
    else:
        left, right = st.columns([3, 2])
        with left:
            chart_title("Youth unemployment by state, 2023-24")
            d = s.iloc[::-1]
            fig = go.Figure(go.Bar(
                x=d.Value_Percent, y=d.Geography, orientation="h",
                marker_color=[ACCENT if v > nat else MID for v in d.Value_Percent],
                text=[f"{v:.1f}%" for v in d.Value_Percent], textposition="outside", cliponaxis=False,
                hovertemplate="%{y}<br>%{x:.1f}%<extra></extra>"))
            fig.add_shape(type="line", x0=nat, x1=nat, y0=0, y1=1, xref="x", yref="paper",
                          line=dict(color=NAVY, width=1.5, dash="dash"))
            fig.add_annotation(x=nat, y=0, xref="x", yref="paper", text=f"All India {nat:.1f}%", showarrow=False,
                               yanchor="top", font=dict(size=10, color=NAVY))
            fig.update_xaxes(title="Rate (%)", gridcolor="#EEF2F8", range=[0, d.Value_Percent.max() * 1.15])
            fig.update_yaxes(automargin=True)
            show(fig, max(380, 22 * len(d) + 80))
        with right:
            chart_title("States above vs below the national rate")
            above = int((s.Value_Percent > nat).sum())
            fig = go.Figure(go.Pie(labels=["Above national rate", "At or below national rate"],
                                   values=[above, len(s) - above], hole=0.55,
                                   marker=dict(colors=[ACCENT, MID]), textinfo="value+percent"))
            show(fig, 300)
            top, bot = s.head(5), s.tail(5).iloc[::-1]
            st.markdown("**Highest 5**")
            st.markdown('<div class="mini-grid">' + "".join(
                f'<div class="mini"><small>{r.Geography}</small><b>{r.Value_Percent:.1f}%</b></div>'
                for r in top.itertuples()) + "</div>", unsafe_allow_html=True)
            st.markdown("**Lowest 5**")
            st.markdown('<div class="mini-grid">' + "".join(
                f'<div class="mini"><small>{r.Geography}</small><b>{r.Value_Percent:.1f}%</b></div>'
                for r in bot.itertuples()) + "</div>", unsafe_allow_html=True)
    story(5, "State outcomes vary enormously, so a single national policy will not fit all.",
          u.story_state(df, states),
          "Direct state-specific schemes to the high-rate states, and study what the low-rate states do differently.")
    note("DATA CAUTION", "State figures are for 2023-24 (July-June) only and are not broken down by education. "
         "Very low and very high values can partly reflect sample size and local labour-force participation.")

else:  # Data Explorer
    header("Data Explorer | Evidence Behind the Story", "Filter the source records and download exactly what you see")
    c1, c2, c3 = st.columns(3)
    with c1:
        p = st.multiselect("Period", u.PERIOD_ORDER, default=u.PERIOD_ORDER)
        sx = st.multiselect("Sex", u.SEXES, default=u.SEXES)
    with c2:
        gg = st.multiselect("Geography", ["All India"] + u.all_states(df), default=["All India"] + u.all_states(df))
        sc = st.multiselect("Sector", u.SECTORS, default=u.SECTORS)
    with c3:
        edu_all = sorted(df.Education_Level.unique())
        ed = st.multiselect("Education level", edu_all, default=edu_all)
    f = u.filter_records(df, p, gg, ed, sx, sc)
    kpi_row([dict(label="RECORDS SHOWN", value=f"{len(f):,}", sub=f"of {len(df):,} total"),
             dict(label="AVERAGE RATE", value=f"{f.Value_Percent.mean():.1f}%" if len(f) else "n/a", sub="Simple mean of shown rows"),
             dict(label="HIGHEST RATE", value=f"{f.Value_Percent.max():.1f}%" if len(f) else "n/a", sub=""),
             dict(label="LOWEST RATE", value=f"{f.Value_Percent.min():.1f}%" if len(f) else "n/a", sub="")])
    try:
        st.dataframe(f, width="stretch", hide_index=True)
    except TypeError:
        st.dataframe(f, use_container_width=True, hide_index=True)
    st.download_button("⬇ Download filtered records (CSV)", f.to_csv(index=False).encode("utf-8"),
                       file_name="youth_unemployment_filtered.csv", mime="text/csv", disabled=f.empty)
    note("SOURCES", "PLFS (MoSPI) annual reports and Lok Sabha Q.3232 (2020-21 to 2023-24 headline and state data); "
         "MoSPI PLFS Annual Report 2025 press note; PLFS 2025 unit-level records computed by India Labour Observatory (CC BY 4.0).")

st.markdown('<div class="foot">Source: Periodic Labour Force Survey (PLFS), MoSPI. Youth = age 15-29, usual status (ps+ss). '
            'Always state the selected period and filters when presenting these results.</div>', unsafe_allow_html=True)
