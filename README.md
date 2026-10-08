# AI Priority Recommender for Campus Information

A beginner-friendly Streamlit prototype that helps students decide which authorized campus announcements to act on first. It accepts pasted text, TXT files, or text-based PDFs. Its explainable rules work without an external AI service or API key.

## Files

Create these three files in the same project folder, `ai planner`:

- `app.py` contains the Streamlit interface, announcement extraction, and scoring rules.
- `requirements.txt` lists the Python packages needed to run the app.
- `README.md` explains setup and the scoring behavior.

## Run in VS Code

1. Open the `ai planner` folder in VS Code.
2. Open **Terminal > New Terminal**.
3. (Recommended) Create and activate a virtual environment:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

4. Install the packages:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

Streamlit prints a local URL, usually `http://localhost:8501`, which you can open in a browser.

## How to use it

Choose a department, year, and section in the sidebar. Optionally enter comma-separated interests. Paste an announcement, upload a TXT/PDF, or click a sample button, then select **Analyze Announcement**. The result shows the extracted audience, category, action, deadline, each score component, total, and an explanation. The history table can be filtered or cleared.

## Scoring rules

The total is always calculated as urgency (maximum 40) + student relevance (maximum 35) + action importance (maximum 25), for a maximum of 100.

| Component | Rule | Points |
| --- | --- | ---: |
| Urgency | Deadline today, tomorrow, or overdue | 40 |
| Urgency | Within 3 days | 30 |
| Urgency | Within 7 days | 20 |
| Urgency | More than 7 days away | 10 |
| Urgency | No deadline found | 5 |
| Relevance | Exact department, year, and section match | 35 |
| Relevance | Department and year match | 30 |
| Relevance | Department matches | 20 |
| Relevance | General or partially specified audience matches | 10 |
| Relevance | Explicit target does not match the profile | 0 |
| Action | Mandatory registration/submission or exam/academic requirement | 25 |
| Action | Important application | 20 |
| Action | Event participation | 10 |
| Action | General information | 5 |

Scores of 75–100 are **HIGH PRIORITY**, 50–74 **MEDIUM PRIORITY**, and 0–49 **LOW PRIORITY**. A relevance score of 0 is displayed as **NOT RELEVANT**, regardless of the other component scores. When deadlines are equally near, ties follow the ranges above: 1 day or less is 40, 2–3 days is 30, 4–7 days is 20, and more than 7 days is 10. Overdue items receive 40 urgency points so a missed deadline is surfaced for review.

The category, target, deadline, and action are extracted using simple Python keyword and date rules. These are estimates, not guaranteed AI understanding. Dates without a year use the current year. Always verify extracted details against the original announcement.

## Responsible use and limitations

- Use only manual text, sample announcements, or documents you are authorized to process.
- This app does not connect to or read private WhatsApp groups or conversations.
- Real deployment would require authorized data access and institutional approval.
- Only the selected department, year, section, and optional interests are used for relevance checks in this local prototype.
- Ambiguous announcements, dates, and subjective priority judgments need human verification. AI-style recommendations support decisions; they do not replace them.

No external AI API is used, so no API key is needed. PDF upload support uses `pypdf`; scanned/image-only PDFs may not yield readable text.