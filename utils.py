"""Data helpers for the Youth Unemployment dashboard (pure pandas - no UI code).

Every number shown in the Streamlit app comes from these functions, so they can
be unit-tested and reused (e.g. for the report screenshots).
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "youth_unemployment_india_plfs.csv"

PERIOD_ORDER = ["2020-21", "2021-22", "2022-23", "2023-24", "2024", "2025"]
EDU_ORDER = [
    "Not literate",
    "Literate, without formal schooling",
    "Below primary",
    "Primary",
    "Middle",
    "Secondary",
    "Higher secondary",
    "Diploma or certificate",
    "Graduate",
    "Postgraduate and above",
]
EDU_AGGREGATE = "Secondary and above"      # roll-up row, not an education level
ALL_LEVELS = "All levels"
STATE_EDU_LABEL = "All levels (state x education not published)"
SECTORS = ["Rural+Urban", "Rural", "Urban"]
SEXES = ["Everyone", "Male", "Female"]
LATEST = "2025"
STATE_PERIOD = "2023-24"


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["Period"] = df["Period"].astype(str)
    df["Period"] = pd.Categorical(df["Period"], categories=PERIOD_ORDER, ordered=True)
    df["Value_Percent"] = pd.to_numeric(df["Value_Percent"], errors="coerce")
    return df


# --------------------------------------------------------------------------- #
# Slices
# --------------------------------------------------------------------------- #
def national_trend(df: pd.DataFrame, start: str = PERIOD_ORDER[0], end: str = PERIOD_ORDER[-1]) -> pd.DataFrame:
    """All-India, all-levels, everyone, rural+urban headline series."""
    t = df[
        (df.Geography == "All India")
        & (df.Education_Level == ALL_LEVELS)
        & (df.Sex == "Everyone")
        & (df.Sector == "Rural+Urban")
    ].sort_values("Period")
    lo, hi = PERIOD_ORDER.index(start), PERIOD_ORDER.index(end)
    t = t[t.Period.astype(str).map(PERIOD_ORDER.index).between(lo, hi)].copy()
    t["Period"] = t["Period"].astype(str)
    t["Change_pp"] = t["Value_Percent"].diff().round(1)
    return t[["Period", "Period_Basis", "Value_Percent", "Change_pp"]].reset_index(drop=True)


def education_rates(df, sector="Rural+Urban", sex="Everyone", levels=None, period=LATEST) -> pd.DataFrame:
    """Rate by education level (ordered low -> high) for one sex / sector."""
    levels = EDU_ORDER if levels is None else levels
    e = df[
        (df.Geography == "All India")
        & (df.Period.astype(str) == period)
        & (df.Sector == sector)
        & (df.Sex == sex)
        & (df.Education_Level.isin(levels))
    ].copy()
    e["order"] = e.Education_Level.map({k: i for i, k in enumerate(EDU_ORDER)})
    return e.sort_values("order")[["Education_Level", "Value_Percent"]].reset_index(drop=True)


def education_by_sex(df, sector="Rural+Urban", levels=None, period=LATEST) -> pd.DataFrame:
    """Wide table: one row per education level, columns Male / Female / Everyone + gap."""
    levels = EDU_ORDER if levels is None else levels
    e = df[
        (df.Geography == "All India")
        & (df.Period.astype(str) == period)
        & (df.Sector == sector)
        & (df.Education_Level.isin(levels))
    ]
    w = e.pivot_table(index="Education_Level", columns="Sex", values="Value_Percent", aggfunc="first")
    w = w.reindex([x for x in EDU_ORDER if x in w.index])
    for c in SEXES:
        if c not in w:
            w[c] = float("nan")
    w["Gap_F_minus_M"] = (w["Female"] - w["Male"]).round(1)
    return w[["Male", "Female", "Everyone", "Gap_F_minus_M"]].reset_index()


def heat_matrix(df, levels=None, period=LATEST) -> pd.DataFrame:
    """Education level x (Sex . Sector) matrix for the heat-map."""
    levels = EDU_ORDER if levels is None else levels
    e = df[
        (df.Geography == "All India")
        & (df.Period.astype(str) == period)
        & (df.Education_Level.isin(levels))
    ].copy()
    e["col"] = e.Sex + " | " + e.Sector
    cols = [f"{s} | {c}" for s in SEXES for c in SECTORS]
    m = e.pivot_table(index="Education_Level", columns="col", values="Value_Percent", aggfunc="first")
    m = m.reindex(index=[x for x in EDU_ORDER if x in m.index], columns=[c for c in cols if c in m.columns])
    return m


def sector_compare(df, period=LATEST) -> pd.DataFrame:
    s = df[
        (df.Geography == "All India")
        & (df.Period.astype(str) == period)
        & (df.Education_Level == ALL_LEVELS)
        & (df.Sex == "Everyone")
    ]
    s = s.set_index("Sector").reindex(SECTORS)["Value_Percent"].dropna().reset_index()
    return s


def state_rates(df, states=None) -> pd.DataFrame:
    s = df[(df.Geography != "All India") & (df.Period.astype(str) == STATE_PERIOD)]
    if states is not None:
        s = s[s.Geography.isin(states)]
    return s.sort_values("Value_Percent", ascending=False)[["Geography", "Value_Percent"]].reset_index(drop=True)


def national_reference(df, period=STATE_PERIOD) -> float:
    r = national_trend(df)
    r = r[r.Period == period]
    return float(r.Value_Percent.iloc[0]) if len(r) else float("nan")


def all_states(df) -> list[str]:
    return sorted(df[df.Geography != "All India"].Geography.unique())


# --------------------------------------------------------------------------- #
# KPIs
# --------------------------------------------------------------------------- #
def kpis(df, start, end, sector="Rural+Urban") -> list[dict]:
    t = national_trend(df, start, end)
    out = []
    if len(t):
        last, first = t.iloc[-1], t.iloc[0]
        out.append(dict(label="LATEST YOUTH UNEMPLOYMENT", value=f"{last.Value_Percent:.1f}%",
                        sub=f"{last.Period} ({last.Period_Basis}), all India"))
        if len(t) > 1:
            d = last.Value_Percent - first.Value_Percent
            out.append(dict(label=f"CHANGE SINCE {first.Period}", value=f"{d:+.1f} pp",
                            sub="Percentage-point change", good=d < 0))
        else:
            out.append(dict(label="CHANGE OVER RANGE", value="n/a", sub="Select 2+ periods"))
    else:
        out += [dict(label="LATEST YOUTH UNEMPLOYMENT", value="n/a", sub="No data in range"),
                dict(label="CHANGE OVER RANGE", value="n/a", sub="No data in range")]
    sc = sector_compare(df).set_index("Sector")["Value_Percent"]
    if {"Urban", "Rural"} <= set(sc.index):
        out.append(dict(label="URBAN - RURAL GAP (2025)", value=f"{sc['Urban'] - sc['Rural']:+.1f} pp",
                        sub=f"Urban {sc['Urban']:.1f}% vs rural {sc['Rural']:.1f}%"))
    else:
        out.append(dict(label="URBAN - RURAL GAP (2025)", value="n/a", sub=""))
    g = education_rates(df, sector=sector, levels=["Graduate"])
    ov = sector_compare(df).set_index("Sector")["Value_Percent"].get(sector, float("nan"))
    if len(g):
        out.append(dict(label="GRADUATE UNEMPLOYMENT (2025)", value=f"{g.Value_Percent.iloc[0]:.1f}%",
                        sub=f"vs {ov:.1f}% for all youth ({sector})"))
    else:
        out.append(dict(label="GRADUATE UNEMPLOYMENT (2025)", value="n/a", sub=""))
    return out


# --------------------------------------------------------------------------- #
# Story statements (computed from data so they stay true when filters change)
# --------------------------------------------------------------------------- #
def story_overview(df, sector="Rural+Urban", levels=None) -> str:
    e = education_rates(df, sector=sector, levels=levels)
    if len(e) < 2:
        return "Select at least two education levels to compare them."
    hi, lo = e.loc[e.Value_Percent.idxmax()], e.loc[e.Value_Percent.idxmin()]
    return (f"Among the selected groups ({sector}, 2025), youth unemployment is highest for "
            f"{hi.Education_Level.lower()} ({hi.Value_Percent:.1f}%) and lowest for "
            f"{lo.Education_Level.lower()} ({lo.Value_Percent:.1f}%).")


def story_trend(df, start, end) -> str:
    t = national_trend(df, start, end)
    if len(t) < 2:
        return "Select a wider period range to see the direction of travel."
    d = t.Change_pp.dropna()
    big = t.loc[d.idxmin()]
    prev = t.loc[d.idxmin() - 1]
    return (f"The rate moved from {t.Value_Percent.iloc[0]:.1f}% ({t.Period.iloc[0]}) to "
            f"{t.Value_Percent.iloc[-1]:.1f}% ({t.Period.iloc[-1]}). The sharpest fall was "
            f"{big.Change_pp:+.1f} pp between {prev.Period} and {big.Period}.")


def story_education(df, sector="Rural+Urban", levels=None) -> str:
    e = education_rates(df, sector=sector, levels=levels)
    if len(e) < 2:
        return "Select at least two education levels to see the pattern."
    return (f"The rate rises with schooling: {e.Education_Level.iloc[0].lower()} "
            f"{e.Value_Percent.iloc[0]:.1f}% -> {e.Education_Level.iloc[-1].lower()} "
            f"{e.Value_Percent.iloc[-1]:.1f}% ({sector}, 2025).")


def story_gender(df, sector="Rural+Urban", levels=None) -> str:
    w = education_by_sex(df, sector=sector, levels=levels).dropna(subset=["Gap_F_minus_M"])
    if w.empty:
        return "No male/female comparison available for this selection."
    r = w.loc[w.Gap_F_minus_M.idxmax()]
    n_f = int((w.Gap_F_minus_M > 0).sum())
    return (f"Women's unemployment exceeds men's in {n_f} of {len(w)} education groups; the widest gap is "
            f"{r.Education_Level.lower()} - {r.Female:.1f}% for women vs {r.Male:.1f}% for men "
            f"({r.Gap_F_minus_M:+.1f} pp).")


def story_state(df, states=None) -> str:
    s = state_rates(df, states)
    if len(s) < 2:
        return "Select at least two states to compare."
    nat = national_reference(df)
    above = int((s.Value_Percent > nat).sum())
    return (f"{s.Geography.iloc[0]} ({s.Value_Percent.iloc[0]:.1f}%) is {s.Value_Percent.iloc[0] / s.Value_Percent.iloc[-1]:.0f}x "
            f"{s.Geography.iloc[-1]} ({s.Value_Percent.iloc[-1]:.1f}%); {above} of {len(s)} states sit above the "
            f"national rate of {nat:.1f}% (2023-24).")


# --------------------------------------------------------------------------- #
# Explorer
# --------------------------------------------------------------------------- #
def filter_records(df, periods=None, geographies=None, levels=None, sexes=None, sectors=None) -> pd.DataFrame:
    f = df.copy()
    for col, vals in [("Period", periods), ("Geography", geographies), ("Education_Level", levels),
                      ("Sex", sexes), ("Sector", sectors)]:
        if vals:
            f = f[f[col].astype(str).isin([str(v) for v in vals])]
    f = f.copy()
    f["Period"] = f["Period"].astype(str)
    return f.reset_index(drop=True)
