from datetime import date, timedelta
import re

import streamlit as st


DEPARTMENTS = ["AIDS", "CSE", "ECE", "EEE", "Mechanical", "Civil"]
YEARS = ["1st", "2nd", "3rd", "4th"]
SECTIONS = ["A", "B", "C"]
CATEGORIES = [
    "Academics",
    "Assignments",
    "Exams",
    "Fees",
    "Registrations",
    "Events",
    "Opportunities",
    "General",
]


def extract_category(text):
    """Choose a category from useful words in the announcement."""
    content = text.lower()
    category_words = {
        "Exams": ["exam", "examination", "hall ticket", "timetable"],
        "Assignments": ["assignment", "submit", "submission", "lab record"],
        "Fees": ["fee", "fees", "tuition", "payment"],
        "Registrations": ["registration", "register", "enroll", "enrol"],
        "Events": ["event", "cultural", "meeting", "workshop", "seminar"],
        "Opportunities": ["internship", "scholarship", "opportunity", "apply", "application"],
        "Academics": ["academic", "class", "lecture", "course", "nptel", "syllabus"],
    }

    for category in (
        "Exams",
        "Assignments",
        "Fees",
        "Events",
        "Registrations",
        "Opportunities",
        "Academics",
    ):
        if any(word in content for word in category_words.get(category, [])):
            return category
    return "General"


def extract_target(text):
    """Find department, year, and section mentions, if present."""
    content = text.lower()
    department = None
    department_patterns = {
        "AIDS": r"\b(?:aids|ai\s*&\s*ds|ai\s+and\s+ds)\b",
        "CSE": r"\b(?:cse|computer science(?: and engineering)?)\b",
        "ECE": r"\b(?:ece|electronics and communication)\b",
        "EEE": r"\b(?:eee|electrical and electronics)\b",
        "Mechanical": r"\bmechanical\b",
        "Civil": r"\bcivil\b",
    }
    for name, pattern in department_patterns.items():
        if re.search(pattern, content):
            department = name
            break

    year = None
    year_patterns = [
        ("1st", r"\b(?:1st|first)(?:\s*[- ]?\s*year)?\b"),
        ("2nd", r"\b(?:2nd|second)(?:\s*[- ]?\s*year)?\b"),
        ("3rd", r"\b(?:3rd|third)(?:\s*[- ]?\s*year)?\b"),
        ("4th", r"\b(?:4th|fourth)(?:\s*[- ]?\s*year)?\b"),
    ]
    for label, pattern in year_patterns:
        if re.search(pattern, content):
            year = label
            break

    section_match = re.search(r"\b(?:section|sec\.? )\s*([abc])\b", content)
    section = section_match.group(1).upper() if section_match else None
    return {"department": department, "year": year, "section": section}


def extract_deadline(text, today=None):
    """Extract a recognizable date or relative day; return None if absent."""
    reference_day = today or date.today()
    content = text.lower()

    if re.search(r"\btoday\b", content):
        return reference_day
    if re.search(r"\btomorrow\b", content):
        return reference_day + timedelta(days=1)

    relative_match = re.search(r"\b(?:in|within)\s+(\d{1,2})\s+days?\b", content)
    if relative_match:
        return reference_day + timedelta(days=int(relative_match.group(1)))

    for weekday, weekday_number in (
        ("monday", 0),
        ("tuesday", 1),
        ("wednesday", 2),
        ("thursday", 3),
        ("friday", 4),
        ("saturday", 5),
        ("sunday", 6),
    ):
        if re.search(rf"\b{weekday}\b", content):
            day_offset = (weekday_number - reference_day.weekday()) % 7
            if day_offset == 0 and re.search(rf"\bnext\s+{weekday}\b", content):
                day_offset = 7
            return reference_day + timedelta(days=day_offset)

    date_patterns = [
        re.compile(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b"),
        re.compile(
            r"\b(january|february|march|april|may|june|july|august|september|october|"
            r"november|december)\s+(\d{1,2})(?:st|nd|rd|th)?(?:,?\s+(20\d{2}))?\b"
        ),
        re.compile(
            r"\b(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|"
            r"july|august|september|october|november|december)(?:\s+(20\d{2}))?\b"
        ),
    ]
    month_numbers = {
        month.lower(): number
        for number, month in enumerate(
            ("January", "February", "March", "April", "May", "June", "July", "August",
             "September", "October", "November", "December"),
            start=1,
        )
    }

    match = date_patterns[0].search(content)
    if match:
        year, month, day = (int(part) for part in match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None

    for pattern, month_first in ((date_patterns[1], True), (date_patterns[2], False)):
        match = pattern.search(content)
        if not match:
            continue
        if month_first:
            month_name, day_text, year_text = match.groups()
        else:
            day_text, month_name, year_text = match.groups()
        year = int(year_text) if year_text else reference_day.year
        try:
            return date(year, month_numbers[month_name], int(day_text))
        except ValueError:
            return None
    return None


def calculate_urgency(deadline, today=None):
    """Return the urgency score and a short explanation label."""
    if deadline is None:
        return 5, "No deadline"
    days_left = (deadline - (today or date.today())).days
    if days_left <= 1:
        return 40, "Today, tomorrow, or overdue"
    if days_left <= 3:
        return 30, "Within 3 days"
    if days_left <= 7:
        return 20, "Within 7 days"
    return 10, "More than 7 days away"


def calculate_relevance(target, profile):
    """Score how closely the announcement audience matches the student."""
    department = target["department"]
    year = target["year"]
    section = target["section"]

    if department and department != profile["department"]:
        return 0
    if year and year != profile["year"]:
        return 0
    if section and section != profile["section"]:
        return 0

    if department and year and section:
        return 35
    if department and year:
        return 30
    if department:
        return 20
    return 10


def calculate_action_importance(text, category):
    """Score actions using the project's fixed action-importance tiers."""
    content = text.lower()
    required = re.search(r"\b(must|required|mandatory|compulsory|have to)\b", content)
    exam_or_academic_requirement = category in {"Exams", "Assignments", "Academics"} and (
        required or re.search(r"\b(submit|submission|exam|examination)\b", content)
    )
    mandatory_registration_or_submission = required and re.search(
        r"\b(register|registration|submit|submission|enroll|enrol)\b", content
    )
    if mandatory_registration_or_submission or exam_or_academic_requirement:
        return 25, "Mandatory or academic requirement"
    if re.search(r"\b(apply|application|scholarship|internship)\b", content):
        return 20, "Important application"
    if category == "Events" or re.search(r"\b(event|workshop|seminar|meeting)\b", content):
        return 10, "Event participation"
    return 5, "General information"


def calculate_priority(urgency, relevance, action_importance):
    """Add the three weighted components and assign the required label."""
    score = urgency + relevance + action_importance
    if relevance == 0:
        return score, "NOT RELEVANT"
    if score >= 75:
        return score, "HIGH PRIORITY"
    if score >= 50:
        return score, "MEDIUM PRIORITY"
    return score, "LOW PRIORITY"


def extract_action(text, category):
    """Create a short action sentence from common campus announcement verbs."""
    content = text.lower()
    if re.search(r"\b(register|registration|enroll|enrol)\b", content):
        course = re.search(r"\b(nptel|[a-z0-9]+ course)\b", content, re.IGNORECASE)
        if course:
            return f"Register for {course.group(0).upper() if course.group(0).lower() == 'nptel' else course.group(0)}."
        return "Check the announcement and complete registration if it applies to you."
    if re.search(r"\b(submit|submission)\b", content):
        return "Submit the required assignment or document."
    if re.search(r"\b(attend|participate)\b", content):
        return "Attend or participate in the announced activity."
    if re.search(r"\b(apply|application)\b", content):
        return "Review the eligibility details and submit an application if interested."
    if category == "Events":
        return "Review the event details and decide whether to participate."
    return "Read the announcement and follow any instructions that apply to you."


def generate_explanation(target, urgency_label, action_label, relevance):
    """Explain the result using the same factors that produced the score."""
    if relevance == 0:
        return "The announcement names a department, year, or section that does not match your selected profile."

    reasons = []
    if target["department"] or target["year"] or target["section"]:
        reasons.append("the stated audience matches your profile")
    else:
        reasons.append("it appears to be a general college announcement")
    if urgency_label == "No deadline":
        reasons.append("no deadline was found")
    elif urgency_label == "Today, tomorrow, or overdue":
        reasons.append("the deadline is today, tomorrow, or has passed")
    else:
        reasons.append(f"the deadline is {urgency_label.lower()}")
    if action_label == "Mandatory or academic requirement":
        reasons.append("it includes a required academic action")
    elif action_label == "Important application":
        reasons.append("it includes an application action")
    elif action_label == "Event participation":
        reasons.append("it concerns event participation")
    else:
        reasons.append("it contains general information rather than a required action")
    return "This announcement received this priority because " + ", ".join(reasons) + ". Please verify the announcement details."


def analyze_announcement(text, profile, interests="", today=None):
    """Extract announcement details and calculate the transparent priority score."""
    category = extract_category(text)
    target = extract_target(text)
    deadline = extract_deadline(text, today=today)
    urgency, urgency_label = calculate_urgency(deadline, today=today)
    relevance = calculate_relevance(target, profile)
    action_importance, action_label = calculate_action_importance(text, category)
    score, priority = calculate_priority(urgency, relevance, action_importance)
    deadline_text = f"{deadline.strftime('%B')} {deadline.day}, {deadline.year}" if deadline else "Not found"

    audience_parts = []
    if target["year"]:
        audience_parts.append(f"{target['year']} Year")
    if target["department"]:
        audience_parts.append(target["department"])
    if target["section"]:
        audience_parts.append(f"Section {target['section']}")
    audience = " ".join(audience_parts) if audience_parts else "General college audience"

    interest_match = bool(interests.strip()) and any(
        interest.lower() in text.lower() for interest in interests.split(",") if interest.strip()
    )
    if deadline and deadline < (today or date.today()):
        next_step = "The listed deadline has passed. Check with the college whether late action is possible."
    elif deadline:
        next_step = f"{extract_action(text, category)} Complete it by {deadline_text}."
    else:
        next_step = f"{extract_action(text, category)} Check the source announcement for any timing details."
    return {
        "announcement": text,
        "category": category,
        "target": target,
        "audience": audience,
        "deadline": deadline,
        "deadline_text": deadline_text,
        "urgency": urgency,
        "urgency_label": urgency_label,
        "relevance": relevance,
        "action_importance": action_importance,
        "action_label": action_label,
        "score": score,
        "priority": priority,
        "required_action": extract_action(text, category),
        "next_step": next_step,
        "explanation": generate_explanation(target, urgency_label, action_label, relevance),
        "interest_match": interest_match,
    }


def read_uploaded_announcement(upload):
    """Read a TXT or PDF upload and return its text."""
    if upload is None:
        return ""
    if upload.name.lower().endswith(".txt"):
        return upload.getvalue().decode("utf-8", errors="replace")
    try:
        from pypdf import PdfReader

        reader = PdfReader(upload)
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception as error:
        st.error(f"Could not read this PDF: {error}")
        return ""


def load_sample(text):
    st.session_state["announcement_input"] = text


st.set_page_config(
    page_title="AI Priority Recommender",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root {
        --ink: #eff2ff;
        --muted: #a8b4d2;
        --line: rgba(177, 194, 236, 0.15);
        --panel: rgba(20, 31, 61, 0.78);
        --cyan: #5ee7df;
        --blue: #6c8cff;
        --violet: #ad8cff;
    }
    html, body, [class*="css"] { font-family: 'DM Sans', 'Segoe UI', sans-serif; }
    .stApp { background: radial-gradient(ellipse at 90% 0%, #29366c 0%, transparent 37%), linear-gradient(135deg, #0a1022 0%, #111b36 56%, #17152f 100%); color: var(--ink); }
    [data-testid="stSidebar"] { background: rgba(8, 14, 31, 0.96); border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] * { color: var(--ink); }
    h1, h2, h3 { font-family: 'Space Grotesk', 'Segoe UI', sans-serif !important; color: var(--ink) !important; letter-spacing: 0 !important; }
    p, li, label, [data-testid="stCaptionContainer"] { color: var(--muted); }
    .hero { padding: 14px 0 22px; border-bottom: 1px solid var(--line); margin-bottom: 22px; }
    .eyebrow { color: var(--cyan); font-size: 0.78rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; }
    .hero h1 { font-size: 2.35rem; margin: 8px 0 2px; }
    .hero p { color: #c1cbe3; font-size: 1.05rem; margin: 0; }
    .panel { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 20px; margin: 8px 0 16px; }
    .priority-card { border-radius: 8px; border: 1px solid var(--line); padding: 22px; margin: 8px 0 16px; background: linear-gradient(135deg, rgba(45, 61, 105, .85), rgba(27, 31, 67, .9)); }
    .priority-high { border-left: 5px solid #ff637d; }
    .priority-medium { border-left: 5px solid #ffca66; }
    .priority-low { border-left: 5px solid #64d6b0; }
    .priority-none { border-left: 5px solid #8c9ab7; }
    .score { font: 700 2.5rem 'Space Grotesk', sans-serif; color: white; }
    .score-label { color: var(--muted); font-size: .9rem; }
    .metric { color: var(--cyan); font-weight: 700; }
    .footer { border-top: 1px solid var(--line); margin-top: 36px; padding: 18px 0 4px; color: #929fbd; font-size: .84rem; }
    .stButton > button { border: 1px solid rgba(128, 157, 255, .38); border-radius: 6px; background: rgba(90, 111, 191, .18); color: #eff2ff; font-weight: 600; }
    .stButton > button:hover { border-color: var(--cyan); color: white; background: rgba(94, 231, 223, .12); }
    .stTextArea textarea, .stTextInput input, .stSelectbox [data-baseweb="select"] > div { background-color: rgba(10, 17, 37, .8); color: var(--ink); border-color: var(--line); }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 6px; }
    @media (max-width: 700px) { .hero h1 { font-size: 1.8rem; } .panel, .priority-card { padding: 15px; } }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### 🎓 Student Profile")
    st.caption("Used only to compare your profile with each announcement.")
    student_profile = {
        "department": st.selectbox("Department", DEPARTMENTS),
        "year": st.selectbox("Year", YEARS, index=1),
        "section": st.selectbox("Section", SECTIONS),
    }
    student_interests = st.text_input("Optional interests", placeholder="robotics, design, research")
    st.markdown("---")
    st.markdown("### 🛡 Responsible AI")
    st.caption(
        "Uses authorized information sources and does not access private WhatsApp conversations. "
        "Only your selected profile and optional interests are used in this local prototype."
    )
    st.caption("Recommendations include an explanation and should be checked by a person.")

st.markdown(
    '<div class="hero"><div class="eyebrow">Campus information, made clearer</div>'
    '<h1>AI Priority Recommender</h1>'
    '<p>Helping students know what to act on first.</p></div>',
    unsafe_allow_html=True,
)

st.markdown("### 📥 Add an announcement")
sample_announcements = [
    "NPTEL registration is open for 2nd-year AIDS students. Last date: September 15. Students must register before the deadline.",
    "All second-year students must submit the assignment before Friday.",
    "College cultural event will be conducted next month. Interested students can register.",
    "ECE first-year students are required to attend the department meeting tomorrow.",
]
sample_labels = ["NPTEL registration", "Assignment due Friday", "Cultural event", "ECE department meeting"]
sample_columns = st.columns(4)
for column, label, sample in zip(sample_columns, sample_labels, sample_announcements):
    with column:
        st.button(label, key=f"sample_{label}", use_container_width=True, on_click=load_sample, args=(sample,))

announcement_text = st.text_area(
    "Paste College Announcement",
    key="announcement_input",
    height=180,
    placeholder="Paste an authorized college announcement here...",
)
uploaded_file = st.file_uploader("Or upload an announcement", type=["txt", "pdf"], help="Text PDFs work best; scanned PDFs may not contain extractable text.")

left_button, right_hint = st.columns([1, 3])
with left_button:
    analyze_clicked = st.button("✨ Analyze Announcement", type="primary", use_container_width=True)
with right_hint:
    st.caption("Use manual text, a TXT/PDF file, or one of the sample announcements. Do not upload private conversations.")

if analyze_clicked:
    uploaded_text = read_uploaded_announcement(uploaded_file)
    source_text = announcement_text.strip() or uploaded_text.strip()
    if not source_text:
        st.warning("Paste an announcement or upload a readable TXT/PDF file before analyzing.")
    else:
        result = analyze_announcement(source_text, student_profile, student_interests)
        st.session_state["latest_result"] = result
        if "announcement_history" not in st.session_state:
            st.session_state["announcement_history"] = []
        st.session_state["announcement_history"].insert(0, result)

result = st.session_state.get("latest_result")
if result and "next_step" not in result:
    result = analyze_announcement(
        result["announcement"], student_profile, student_interests
    )
    st.session_state["latest_result"] = result
if result:
    st.markdown("### 📊 Recommendation")
    priority_class = {
        "HIGH PRIORITY": "priority-high",
        "MEDIUM PRIORITY": "priority-medium",
        "LOW PRIORITY": "priority-low",
        "NOT RELEVANT": "priority-none",
    }[result["priority"]]
    st.markdown(
        f'<div class="priority-card {priority_class}"><div class="eyebrow">{result["priority"]}</div>'
        f'<div class="score">{result["score"]}<span class="score-label"> / 100</span></div>'
        '<div class="score-label">Priority score</div></div>',
        unsafe_allow_html=True,
    )

    detail_columns = st.columns(3)
    details = [
        ("Category", result["category"]),
        ("Target", result["audience"]),
        ("Deadline", result["deadline_text"]),
        ("Required action", result["required_action"]),
        ("Urgency", f"{result['urgency']}/40 · {result['urgency_label']}"),
        ("Student relevance", f"{result['relevance']}/35"),
        ("Action importance", f"{result['action_importance']}/25 · {result['action_label']}"),
        ("Interest match", "Matched" if result["interest_match"] else "No match noted"),
    ]
    for index, (label, value) in enumerate(details):
        with detail_columns[index % 3]:
            st.markdown(f"**{label}**  \n<span class='metric'>{value}</span>", unsafe_allow_html=True)

    st.markdown("#### Why this priority?")
    st.markdown(f'<div class="panel">{result["explanation"]}<br><br><b>What should I do?</b><br>{result["next_step"]}</div>', unsafe_allow_html=True)
    st.caption(
        f"Score calculation: urgency {result['urgency']}/40 + relevance {result['relevance']}/35 "
        f"+ action importance {result['action_importance']}/25 = {result['score']}/100."
    )

st.markdown("### 🗂 Announcement history")
history = st.session_state.get("announcement_history", [])
filter_choice = st.selectbox("Filter announcements", ["All", "High", "Medium", "Low", "Not Relevant"])
filter_priority = {
    "High": "HIGH PRIORITY",
    "Medium": "MEDIUM PRIORITY",
    "Low": "LOW PRIORITY",
    "Not Relevant": "NOT RELEVANT",
}
filtered_history = [
    item for item in history
    if filter_choice == "All" or item["priority"] == filter_priority[filter_choice]
]
if filtered_history:
    history_rows = [
        {
            "Announcement": item["announcement"],
            "Category": item["category"],
            "Deadline": item["deadline_text"],
            "Score": f"{item['score']}/100",
            "Priority": item["priority"],
            "Action": item["required_action"],
        }
        for item in filtered_history
    ]
    st.dataframe(history_rows, use_container_width=True, hide_index=True)
else:
    st.caption("No announcements match this filter yet.")

if history and st.button("Clear history", key="clear_history"):
    st.session_state["announcement_history"] = []
    st.session_state.pop("latest_result", None)
    st.rerun()

with st.expander("ℹ️ Limitations and responsible use"):
    st.markdown(
        "- AI-style keyword rules may misunderstand ambiguous announcements.\n"
        "- Extracted deadlines should be verified against the original source.\n"
        "- Priority can be subjective; a recommendation is not an unquestionable decision.\n"
        "- This prototype uses manual text, uploaded documents, and sample announcements.\n"
        "- Real deployment requires authorized data access and institutional approval.\n"
        "- It does not automatically access private WhatsApp groups or conversations."
    )

st.markdown(
    '<div class="footer">AI Priority Recommender for Campus Information<br>'
    'Prototype — AI Immersion Programme Task 01 (C29)</div>',
    unsafe_allow_html=True,
)