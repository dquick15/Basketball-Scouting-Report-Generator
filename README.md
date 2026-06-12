# AI Basketball Scouting Report Generator

Streamlit application for generating AI-assisted basketball scouting reports from CSV or Excel scouting exports.

## Features

- Player selector with reusable prompt templates for multiple evaluation modes.
- AI-generated 150-250 word scouting reports with a positive developmental tone.
- Modes for Standard Report, High-Upside Prospect, Defensive Specialist, Lead Guard Evaluation, and College Recruiter Version.
- Player profile card and score visualization.
- Export support for copy to clipboard, DOCX, and PDF.
- Support for both the requested CSV schema and the bundled AAU workbook format.

## File Structure

```text
scouting_report_gen/
|-- app.py
|-- prompts.py
|-- report_generator.py
|-- requirements.txt
`-- README.md
```

## Expected Input Columns

- Player Name
- Team
- Grade
- Position
- Strengths
- Development Areas
- Notable Game Moments
- Projection
- Skill Score
- Athleticism Score
- Basketball IQ Score
- Growth Upside Score

## Setup

1. Install dependencies:

```bash
pip install -r scouting_report_gen/requirements.txt
```

2. Set your OpenAI API key:

```bash
set OPENAI_API_KEY=your_key_here
```

3. Start the app:

```bash
streamlit run scouting_report_gen/app.py
```

## Notes

- If no file is uploaded, the app falls back to `scouting_report_gen/AAU_Scouting_System.xlsx` when present.
- The bundled workbook is normalized into the scouting report schema automatically.
- Report generation is disabled until an OpenAI API key is available through environment variables or Streamlit secrets.
