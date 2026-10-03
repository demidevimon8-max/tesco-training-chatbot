import gradio as gr
import json
import os
import statistics
from collections import defaultdict
import csv

PERFORMANCE_FILE = "performance.json"
MANAGER_PASSWORD = "tesco123"


# ---------- DATA LOADING ----------

def load_performance():
    if not os.path.exists(PERFORMANCE_FILE):
        return []
    try:
        with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            return []
    except Exception:
        return []


# ---------- SUMMARY & ANALYTICS ----------

def compute_summary(data):
    if not data:
        return "No performance data available yet."

    total_scores = [d.get("total_score", 0) for d in data]
    empathy_scores = [d.get("scores", {}).get("empathy", 0) for d in data]
    accuracy_scores = [d.get("scores", {}).get("accuracy", 0) for d in data]
    professionalism_scores = [d.get("scores", {}).get("professionalism", 0) for d in data]
    problem_scores = [d.get("scores", {}).get("problem_solving", 0) for d in data]
    deesc_scores = [d.get("scores", {}).get("de_escalation", 0) for d in data]
    tone_avgs = [d.get("tone_average", None) for d in data if d.get("tone_average") is not None]
    frustr_changes = [d.get("frustration_change", None) for d in data if d.get("frustration_change") is not None]

    most_weak = "N/A"
    most_strong = "N/A"

    skill_avgs = {
        "Empathy": statistics.mean(empathy_scores) if empathy_scores else 0,
        "Accuracy": statistics.mean(accuracy_scores) if accuracy_scores else 0,
        "Professionalism": statistics.mean(professionalism_scores) if professionalism_scores else 0,
        "Problem Solving": statistics.mean(problem_scores) if problem_scores else 0,
        "De-escalation": statistics.mean(deesc_scores) if deesc_scores else 0,
    }

    if skill_avgs:
        most_weak = min(skill_avgs, key=skill_avgs.get)
        most_strong = max(skill_avgs, key=skill_avgs.get)

    avg_score = statistics.mean(total_scores) if total_scores else 0
    highest = max(total_scores) if total_scores else 0
    lowest = min(total_scores) if total_scores else 0
    avg_tone = statistics.mean(tone_avgs) if tone_avgs else None
    avg_frustr = statistics.mean(frustr_changes) if frustr_changes else None

    endings = defaultdict(int)
    branches = defaultdict(int)
    keywords = defaultdict(int)

    for d in data:
        ending = d.get("ending")
        if ending:
            endings[ending] += 1
        for b in d.get("branches_triggered", []):
            branches[b] += 1
        for k in d.get("keywords_triggered", []):
            keywords[k] += 1

    most_common_ending = max(endings, key=endings.get) if endings else "N/A"
    most_common_branch = max(branches, key=branches.get) if branches else "N/A"
    most_common_keyword = max(keywords, key=keywords.get) if keywords else "N/A"

    summary = f"""
### Manager Dashboard Summary

- Total scenarios completed: **{len(data)}**
- Average total score: **{avg_score:.1f}**
- Highest score: **{highest}**
- Lowest score: **{lowest}**

- Most common weak skill: **{most_weak}**
- Most common strong skill: **{most_strong}**

- Average tone score: **{avg_tone:.1f}** if avg_tone is not None else "N/A"
- Average frustration change: **{avg_frustr:.2f}** if avg_frustr is not None else "N/A"

- Most common ending: **{most_common_ending}**
- Most common branch path: **{most_common_branch}**
- Most common keyword-triggered branch: **{most_common_keyword}**
"""
    return summary


def build_table(data):
    rows = []
    for d in data:
        scores = d.get("scores", {})
        rows.append({
            "Name": d.get("name", ""),
            "Scenario": d.get("scenario", ""),
            "Total Score": d.get("total_score", 0),
            "Empathy": scores.get("empathy", 0),
            "Accuracy": scores.get("accuracy", 0),
            "Professionalism": scores.get("professionalism", 0),
            "Problem Solving": scores.get("problem_solving", 0),
            "De-escalation": scores.get("de_escalation", 0),
            "Tone Avg": d.get("tone_average", ""),
            "Frustration Change": d.get("frustration_change", ""),
            "Branches": ", ".join(d.get("branches_triggered", [])),
            "Date": d.get("date", "")
        })
    return rows


def build_leaderboard(data):
    by_name = defaultdict(list)
    for d in data:
        by_name[d.get("name", "")].append(d.get("total_score", 0))

    rows = []
    for name, scores in by_name.items():
        if not name:
            continue
        avg = statistics.mean(scores) if scores else 0
        total = sum(scores)
        count = len(scores)
        rows.append({
            "Name": name,
            "Sessions": count,
            "Total Score": total,
            "Average Score": avg
        })

    rows.sort(key=lambda r: r["Average Score"], reverse=True)
    return rows


def colleague_profile(data, colleague):
    if not colleague:
        return "Select a colleague to view their profile."

    records = [d for d in data if d.get("name") == colleague]
    if not records:
        return f"No records found for **{colleague}**."

    total_scores = [d.get("total_score", 0) for d in records]
    scores_empathy = [d.get("scores", {}).get("empathy", 0) for d in records]
    scores_accuracy = [d.get("scores", {}).get("accuracy", 0) for d in records]
    scores_prof = [d.get("scores", {}).get("professionalism", 0) for d in records]
    scores_prob = [d.get("scores", {}).get("problem_solving", 0) for d in records]
    scores_deesc = [d.get("scores", {}).get("de_escalation", 0) for d in records]

    avg_total = statistics.mean(total_scores) if total_scores else 0
    best = max(total_scores) if total_scores else 0
    worst = min(total_scores) if total_scores else 0

    skill_avgs = {
        "Empathy": statistics.mean(scores_empathy) if scores_empathy else 0,
        "Accuracy": statistics.mean(scores_accuracy) if scores_accuracy else 0,
        "Professionalism": statistics.mean(scores_prof) if scores_prof else 0,
        "Problem Solving": statistics.mean(scores_prob) if scores_prob else 0,
        "De-escalation": statistics.mean(scores_deesc) if scores_deesc else 0,
    }

    strengths = sorted(skill_avgs.items(), key=lambda x: x[1], reverse=True)
    weaknesses = sorted(skill_avgs.items(), key=lambda x: x[1])

    branches = defaultdict(int)
    for d in records:
        for b in d.get("branches_triggered", []):
            branches[b] += 1

    total_branch = sum(branches.values()) or 1
    branch_lines = []
    for b, c in branches.items():
        pct = (c / total_branch) * 100
        branch_lines.append(f"- {b}: {pct:.1f}%")

    coaching = []
    if skill_avgs["Empathy"] < 5:
        coaching.append("• Needs stronger empathy early in conversations.")
    if skill_avgs["De-escalation"] < 5:
        coaching.append("• Struggles to reduce frustration when customers are upset.")
    if skill_avgs["Accuracy"] < 5:
        coaching.append("• Needs clearer, more accurate explanations of plans and billing.")
    if not coaching:
        coaching.append("• Overall performance is strong. Focus on maintaining consistency.")

    profile = f"""
### Colleague Profile — {colleague}

- Sessions completed: **{len(records)}**
- Average total score: **{avg_total:.1f}**
- Best score: **{best}**
- Worst score: **{worst}**

**Strengths:**
- {strengths[0][0]} ({strengths[0][1]:.1f})
- {strengths[1][0]} ({strengths[1][1]:.1f})

**Weaknesses:**
- {weaknesses[0][0]} ({weaknesses[0][1]:.1f})
- {weaknesses[1][0]} ({weaknesses[1][1]:.1f})

**Branching Paths Triggered:**
{chr(10).join(branch_lines) if branch_lines else "- No branching data recorded."}

**Coaching Suggestions:**
{chr(10).join(coaching)}
"""
    return profile


def scenario_profile(data, scenario_name):
    if not scenario_name:
        return "Select a scenario to view its analytics."

    records = [d for d in data if d.get("scenario") == scenario_name]
    if not records:
        return f"No records found for **{scenario_name}**."

    total_scores = [d.get("total_score", 0) for d in records]
    avg_score = statistics.mean(total_scores) if total_scores else 0
    failure_count = sum(1 for d in records if d.get("ending") == "fail")
    endings = defaultdict(int)
    branches = defaultdict(int)

    for d in records:
        ending = d.get("ending")
        if ending:
            endings[ending] += 1
        for b in d.get("branches_triggered", []):
            branches[b] += 1

    most_common_ending = max(endings, key=endings.get) if endings else "N/A"
    most_common_branch = max(branches, key=branches.get) if branches else "N/A"

    scenario_text = f"""
### Scenario Analytics — {scenario_name}

- Sessions completed: **{len(records)}**
- Average total score: **{avg_score:.1f}**
- Failure count: **{failure_count}**
- Most common ending: **{most_common_ending}**
- Most common branch path: **{most_common_branch}**
"""
    return scenario_text


def filter_data(data, colleague, scenario_name, min_score, max_score):
    filtered = []
    for d in data:
        if colleague and d.get("name") != colleague:
            continue
        if scenario_name and d.get("scenario") != scenario_name:
            continue
        ts = d.get("total_score", 0)
        if ts < min_score or ts > max_score:
            continue
        filtered.append(d)
    return filtered


def export_csv(data):
    if not data:
        return None
    filename = "manager_export.csv"
    fieldnames = [
        "name", "scenario", "total_score", "date",
        "scores", "tone_average", "frustration_change",
        "branches_triggered", "keywords_triggered", "ending"
    ]
    try:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for d in data:
                writer.writerow({
                    "name": d.get("name", ""),
                    "scenario": d.get("scenario", ""),
                    "total_score": d.get("total_score", 0),
                    "date": d.get("date", ""),
                    "scores": json.dumps(d.get("scores", {})),
                    "tone_average": d.get("tone_average", ""),
                    "frustration_change": d.get("frustration_change", ""),
                    "branches_triggered": ", ".join(d.get("branches_triggered", [])),
                    "keywords_triggered": ", ".join(d.get("keywords_triggered", [])),
                    "ending": d.get("ending", "")
                })
        return filename
    except Exception:
        return None


# ---------- LOGIN HANDLER ----------

def check_login(password):
    if password == MANAGER_PASSWORD:
        data = load_performance()
        colleagues = sorted({d.get("name", "") for d in data if d.get("name")})
        scenarios = sorted({d.get("scenario", "") for d in data if d.get("scenario")})

        summary = compute_summary(data)
        table = build_table(data)
        leaderboard = build_leaderboard(data)

        return (
            True,
            "Login successful. Manager dashboard unlocked.",
            gr.update(visible=True),
            gr.update(choices=colleagues, value=None),
            gr.update(choices=scenarios, value=None),
            table,
            summary,
            leaderboard,
            "Select a colleague to view their profile.",
            "Select a scenario to view its analytics."
        )
    else:
        return (
            False,
            "Incorrect password. Access denied.",
            gr.update(visible=False),
            gr.update(choices=[], value=None),
            gr.update(choices=[], value=None),
            [],
            "No data loaded.",
            [],
            "Not logged in.",
            "Not logged in."
        )


# ---------- FILTER HANDLER ----------

def apply_filters(colleague, scenario_name, min_score, max_score):
    data = load_performance()
    filtered = filter_data(data, colleague, scenario_name, min_score, max_score)

    summary = compute_summary(filtered) if filtered else "No records match the current filters."
    table = build_table(filtered)
    leaderboard = build_leaderboard(filtered)
    col_profile = colleague_profile(filtered, colleague) if colleague else "Select a colleague to view their profile."
    scen_profile = scenario_profile(filtered, scenario_name) if scenario_name else "Select a scenario to view its analytics."

    return table, summary, leaderboard, col_profile, scen_profile


# ---------- EXPORT HANDLER ----------

def on_export(colleague, scenario_name, min_score, max_score):
    data = load_performance()
    filtered = filter_data(data, colleague, scenario_name, min_score, max_score)
    path = export_csv(filtered)
    if path:
        return path
    return None


# ---------- UI ----------

with gr.Blocks() as demo:
    gr.Markdown(
        """
# Manager Portal — Training Analytics

Modern grey, data‑focused dashboard for colleague performance and scenario analytics.
"""
    )

    # Login section
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Manager Login")
            password_input = gr.Textbox(label="Password", type="password")
            login_button = gr.Button("Login")
            login_message = gr.Markdown("Enter the manager password to unlock the dashboard.")

    # Dashboard container (hidden until login)
    with gr.Column(visible=False) as dashboard_container:
        gr.Markdown("### Dashboard Home")

        summary_md = gr.Markdown("No data loaded yet.")

        with gr.Row():
            with gr.Column(scale=2):
                gr.Markdown("#### Performance Table")
                table_output = gr.Dataframe(headers=[
                    "Name", "Scenario", "Total Score", "Empathy", "Accuracy",
                    "Professionalism", "Problem Solving", "De-escalation",
                    "Tone Avg", "Frustration Change", "Branches", "Date"
                ], interactive=False)

            with gr.Column(scale=1):
                gr.Markdown("#### Leaderboard")
                leaderboard_output = gr.Dataframe(headers=[
                    "Name", "Sessions", "Total Score", "Average Score"
                ], interactive=False)

        gr.Markdown("### Filters")

        with gr.Row():
            colleague_dropdown = gr.Dropdown(label="Colleague", choices=[], value=None)
            scenario_dropdown = gr.Dropdown(label="Scenario", choices=[], value=None)
            min_score_slider = gr.Slider(0, 50, value=0, step=1, label="Min Total Score")
            max_score_slider = gr.Slider(0, 50, value=50, step=1, label="Max Total Score")
            apply_button = gr.Button("Apply Filters")

        with gr.Row():
            with gr.Column():
                gr.Markdown("### Colleague Profile")
                colleague_profile_md = gr.Markdown("Select a colleague to view their profile.")
            with gr.Column():
                gr.Markdown("### Scenario Analytics")
                scenario_profile_md = gr.Markdown("Select a scenario to view its analytics.")

        gr.Markdown("### Export")
        export_button = gr.Button("Export filtered data to CSV")
        export_file = gr.File(label="Download CSV", interactive=False)

    # Login wiring
    login_button.click(
        check_login,
        inputs=[password_input],
        outputs=[
            # state (not used directly, but could be)
            gr.State(False),
            login_message,
            dashboard_container,
            colleague_dropdown,
            scenario_dropdown,
            table_output,
            summary_md,
            leaderboard_output,
            colleague_profile_md,
            scenario_profile_md
        ]
    )

    # Filters wiring
    apply_button.click(
        apply_filters,
        inputs=[colleague_dropdown, scenario_dropdown, min_score_slider, max_score_slider],
        outputs=[table_output, summary_md, leaderboard_output, colleague_profile_md, scenario_profile_md]
    )

    # Export wiring
    export_button.click(
        on_export,
        inputs=[colleague_dropdown, scenario_dropdown, min_score_slider, max_score_slider],
        outputs=[export_file]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
