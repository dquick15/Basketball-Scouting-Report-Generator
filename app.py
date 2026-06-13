from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
import streamlit.components.v1 as components
from streamlit.errors import StreamlitSecretNotFoundError

from prompts import REPORT_MODES
from report_generator import ScoutingReportGenerator, create_docx_bytes, create_pdf_bytes


st.set_page_config(page_title="AI Basketball Scouting Report Generator", layout="wide")


REQUIRED_COLUMNS = [
    "Player Name",
    "Team",
    "Grade",
    "Position",
    "Strengths",
    "Development Areas",
    "Notable Game Moments",
    "Projection",
    "Skill Score",
    "Athleticism Score",
    "Basketball IQ Score",
    "Growth Upside Score",
]

NUMERIC_COLUMNS = [
    "Skill Score",
    "Athleticism Score",
    "Basketball IQ Score",
    "Growth Upside Score",
]

DEFAULT_DATA_FILES = [
    Path("scouting_report_gen/scouting_report_input.csv"),
    Path("scouting_report_gen/AAU_Scouting_System.xlsx"),
]


def extract_event_start_date(value: object) -> pd.Timestamp:
    if pd.isna(value):
        return pd.NaT

    text = str(value).strip()
    if not text:
        return pd.NaT

    return pd.to_datetime(text.split(" - ", maxsplit=1)[0].strip(), errors="coerce")


def normalize_workbook(sheets: dict[str, pd.DataFrame]) -> pd.DataFrame:
    evaluations = sheets["Player_Evaluations"].copy()
    events = sheets["Event_Log"].copy()
    evaluations.columns = [str(column).strip() for column in evaluations.columns]
    events.columns = [str(column).strip() for column in events.columns]

    merged = evaluations.merge(events[["Event ID", "Event Name", "Date"]], on="Event ID", how="left")
    notable_moments = (
        merged["Event Name"].fillna("Unknown Event").astype(str).str.strip()
        + " | "
        + merged["Date"].map(lambda value: str(value).split(" - ", maxsplit=1)[0] if pd.notna(value) else "Unknown Date")
    )

    return pd.DataFrame(
        {
            "Player Name": merged["Player Name"],
            "Team": merged["Team"],
            "Grade": merged["Level"],
            "Position": merged["Position"],
            "Strengths": merged["Strengths"],
            "Development Areas": merged["Development Areas"],
            "Notable Game Moments": notable_moments,
            "Projection": merged["Projection"],
            "Skill Score": merged["Skill (1-5)"],
            "Athleticism Score": merged["Athleticism (1-5)"],
            "Basketball IQ Score": merged["IQ (1-5)"],
            "Growth Upside Score": merged["Growth Upside (1-5)"],
            "Event Date": merged["Date"].map(extract_event_start_date),
        }
    )


def read_dataframe(source) -> pd.DataFrame:
    source_name = getattr(source, "name", str(source))
    suffix = Path(source_name).suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(source)

    if suffix in {".xlsx", ".xls"}:
        sheets = pd.read_excel(source, sheet_name=None)
        normalized_sheets = {str(name).strip(): df for name, df in sheets.items()}

        if "Player_Evaluations" in normalized_sheets and "Event_Log" in normalized_sheets:
            return normalize_workbook(normalized_sheets)

        for dataframe in normalized_sheets.values():
            candidate = dataframe.copy()
            candidate.columns = [str(column).strip() for column in candidate.columns]
            if all(column in candidate.columns for column in REQUIRED_COLUMNS):
                return candidate

    raise ValueError("Unsupported file type. Upload a CSV or Excel file with scouting report fields.")


def prepare_dataframe(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = raw_df.copy()
    df.columns = [str(column).strip() for column in df.columns]

    missing_columns = [column for column in REQUIRED_COLUMNS if column not in df.columns]
    if missing_columns:
        missing_text = ", ".join(missing_columns)
        raise ValueError(f"Missing required columns: {missing_text}")

    for column in REQUIRED_COLUMNS:
        if column not in NUMERIC_COLUMNS:
            df[column] = df[column].fillna("").astype(str).str.strip()

    for column in NUMERIC_COLUMNS:
        df[column] = pd.to_numeric(df[column], errors="coerce")

    df = df.dropna(subset=NUMERIC_COLUMNS)
    df = df[df["Player Name"].astype(bool)].copy()
    df = df.sort_values(["Player Name", "Team", "Grade"]).reset_index(drop=True)
    return df


@st.cache_data(show_spinner=False)
def load_data_from_path(path: str) -> pd.DataFrame:
    return prepare_dataframe(read_dataframe(path))


def load_data_from_upload(uploaded_file) -> pd.DataFrame:
    return prepare_dataframe(read_dataframe(uploaded_file))


def find_default_data_file() -> Path | None:
    for path in DEFAULT_DATA_FILES:
        if path.exists():
            return path
    return None


def load_app_data() -> tuple[pd.DataFrame, str]:
    uploaded_file = st.sidebar.file_uploader(
        "Upload scouting report input",
        type=["csv", "xlsx", "xls"],
        help="Upload a CSV export with the scouting report fields, or use the bundled default workbook.",
    )

    if uploaded_file is not None:
        return load_data_from_upload(uploaded_file), uploaded_file.name

    default_file = find_default_data_file()
    if default_file is not None:
        return load_data_from_path(str(default_file)), default_file.name

    raise FileNotFoundError("No default data file found. Upload a scouting report CSV to continue.")


def get_api_key() -> str | None:
    secret_key = None
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY")
    except StreamlitSecretNotFoundError:
        secret_key = None

    return secret_key or os.getenv("OPENAI_API_KEY")


def render_profile_card(player_record: pd.Series) -> None:
    st.subheader("Player Profile")
    info_one, info_two, info_three, info_four = st.columns(4)
    info_one.metric("Team", player_record["Team"])
    info_two.metric("Grade", player_record["Grade"])
    info_three.metric("Position", player_record["Position"])
    info_four.metric("Projection", player_record["Projection"])

    notes_one, notes_two, notes_three = st.columns(3)
    notes_one.markdown(f"**Strengths**\n\n{player_record['Strengths']}")
    notes_two.markdown(f"**Development Areas**\n\n{player_record['Development Areas']}")
    notes_three.markdown(f"**Notable Game Moments**\n\n{player_record['Notable Game Moments']}")


def render_scores_visual(player_record: pd.Series) -> None:
    st.subheader("Scores Visualization")
    score_df = pd.DataFrame(
        {
            "Category": [
                "Skill Score",
                "Athleticism Score",
                "Basketball IQ Score",
                "Growth Upside Score",
            ],
            "Score": [
                player_record["Skill Score"],
                player_record["Athleticism Score"],
                player_record["Basketball IQ Score"],
                player_record["Growth Upside Score"],
            ],
        }
    )

    fig = px.bar(
        score_df,
        x="Category",
        y="Score",
        text="Score",
        color="Category",
        color_discrete_sequence=["#0f4c5c", "#e36414", "#5f0f40", "#6a994e"],
        range_y=[0, 5],
    )
    fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, width="stretch")


def render_copy_button(report_text: str) -> None:
    escaped_report = json.dumps(report_text)
    components.html(
        f"""
        <div style=\"margin-top:0.5rem;\">
          <button
            style=\"background:#0f4c5c;color:white;border:none;border-radius:8px;padding:0.65rem 1rem;cursor:pointer;font-weight:600;\"
            onclick='navigator.clipboard.writeText({escaped_report}).then(() => {{ this.innerText = "Copied"; }});'
          >Copy to clipboard</button>
        </div>
        """,
        height=56,
    )


def render_generated_report(player_name: str, mode: str, report_text: str) -> None:
    st.subheader("Generated Report")
    st.write(report_text)
    render_copy_button(report_text)

    docx_bytes = create_docx_bytes(player_name, mode, report_text)
    pdf_bytes = create_pdf_bytes(player_name, mode, report_text)
    export_one, export_two = st.columns(2)
    export_one.download_button(
        "Download DOCX",
        data=docx_bytes,
        file_name=f"{player_name.lower().replace(' ', '_')}_{mode.lower().replace(' ', '_')}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        width="stretch",
    )
    export_two.download_button(
        "Download PDF",
        data=pdf_bytes,
        file_name=f"{player_name.lower().replace(' ', '_')}_{mode.lower().replace(' ', '_')}.pdf",
        mime="application/pdf",
        width="stretch",
    )


def main() -> None:
    st.title("AI Basketball Scouting Report Generator")
    st.write("Generate polished, recruiter-ready scouting reports from player evaluation data.")

    try:
        df, source_name = load_app_data()
    except (FileNotFoundError, ValueError) as exc:
        st.error(str(exc))
        st.stop()

    st.sidebar.success(f"Loaded data source: {source_name}")
    st.sidebar.caption("Set OPENAI_API_KEY in your environment or Streamlit secrets to enable report generation.")

    selected_player = st.selectbox("Select a player", options=sorted(df["Player Name"].unique()))
    selected_mode = st.radio("Report mode", options=list(REPORT_MODES.keys()), horizontal=False)
    player_rows = df[df["Player Name"] == selected_player].reset_index(drop=True)
    player_record = player_rows.iloc[0]

    left_col, right_col = st.columns([1.1, 1.2])
    with left_col:
        render_profile_card(player_record)
    with right_col:
        render_scores_visual(player_record)

    generator_disabled = not get_api_key()
    if generator_disabled:
        st.info("Add an OpenAI API key to generate reports. The player profile and score visualization remain available without it.")

    if st.button("Generate Scouting Report", type="primary", width="stretch", disabled=generator_disabled):
        try:
            generator = ScoutingReportGenerator(api_key=get_api_key())
            with st.spinner("Generating report..."):
                report_text = generator.generate_report(player_record.to_dict(), selected_mode)
            st.session_state["generated_report"] = report_text
            st.session_state["generated_player"] = selected_player
            st.session_state["generated_mode"] = selected_mode
        except Exception as exc:
            st.error(f"Report generation failed: {exc}")

    if st.session_state.get("generated_report") and st.session_state.get("generated_player") == selected_player:
        render_generated_report(
            player_name=st.session_state["generated_player"],
            mode=st.session_state.get("generated_mode", selected_mode),
            report_text=st.session_state["generated_report"],
        )


if __name__ == "__main__":
    main()
