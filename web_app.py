import gradio as gr
import json
import os
import random
from datetime import datetime

PERFORMANCE_FILE = "performance.json"
SCENARIOS_FILE = "scenarios.json"
ACCOUNTS_FILE = "accounts.json"

# ---------- LOAD PERFORMANCE ----------
def load_performance():
    if not os.path.exists(PERFORMANCE_FILE):
        return []
    try:
        with open(PERFORMANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []

def save_performance(entry):
    data = load_performance()
    data.append(entry)
    try:
        with open(PERFORMANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

# ---------- LOAD SCENARIOS ----------
def load_scenarios():
    if not os.path.exists(SCENARIOS_FILE):
        return {
            "Billing Issue – Data Overcharge": {
                "intro": "I’ve just checked my bill and there’s a huge data charge I wasn’t expecting.",
                "steps": ["step1", "step2", "step3", "step4", "step5"],
                "uses_account": True
            },
            "Lost SIM / Replacement": {
                "intro": "I’ve lost my SIM card and I need a replacement urgently.",
                "steps": ["step1", "step2", "step3", "step4"],
                "uses_account": False
            },
            "Upgrade Eligibility": {
                "intro": "I want to upgrade but the app says I’m not eligible. Why?",
                "steps": ["step1", "step2", "step3", "step4", "step5"],
                "uses_account": True
            }
        }
    try:
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

SCENARIOS = load_scenarios()

# ---------- LOAD ACCOUNTS ----------
def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    try:
        with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

ACCOUNTS = load_accounts()
# ---------- TONE ANALYSIS ----------
def analyse_tone(text):
    t = text.lower()
    score = 2

    if any(w in t for w in ["angry", "annoyed", "ridiculous", "furious"]):
        score = 1
    elif any(w in t for w in ["thank", "great", "helpful", "appreciate"]):
        score = 3

    if "!" in t and score == 2:
        score = 1

    if score == 1:
        label = "<b style='color:red;'>Negative / Frustrated</b>"
    elif score == 3:
        label = "<b style='color:green;'>Positive / Reassured</b>"
    else:
        label = "<b style='color:orange;'>Neutral / Unsure</b>"

    return score, f"<div>Customer tone: {label}</div>"

# ---------- COACHING ----------
def live_coaching(text):
    t = text.lower()
    tips = []

    if "sorry" in t or "apologise" in t:
        tips.append("Good empathy – you’re acknowledging their feelings.")
    else:
        tips.append("Try adding an apology to show empathy.")

    if any(w in t for w in ["check", "look into", "investigate", "review"]):
        tips.append("Nice – you’re taking ownership.")
    else:
        tips.append("Offer to check their account.")

    if any(w in t for w in ["option", "solution", "next step"]):
        tips.append("You’re moving towards solutions.")
    else:
        tips.append("Move towards a clear next step.")

    if "!" in t and not any(w in t for w in ["thank", "great", "appreciate"]):
        tips.append("Watch your tone — too many exclamation marks can feel sharp.")

    return "\n".join(f"• {tip}" for tip in tips)

# ---------- CUSTOMER IMAGE ----------
def get_customer_image(frustration, customer_type="adult_male"):
    base = f"characters/{customer_type}"
    if frustration <= 1.4:
        return f"{base}/happy.png"
    elif frustration <= 2.2:
        return f"{base}/neutral.png"
    else:
        return f"{base}/annoyed.png"

# ---------- SCORING ----------
def score_reply(user_text, scores, frustration):
    t = user_text.lower()

    if any(w in t for w in ["sorry", "apologise", "understand"]):
        scores["empathy"] += 1
        frustration -= 0.2
    else:
        scores["empathy"] -= 0.5
        frustration += 0.1

    if any(w in t for w in ["data", "usage", "allowance", "plan"]):
        scores["accuracy"] += 0.8
    else:
        scores["accuracy"] -= 0.3

    if any(w in t for w in ["please", "thank", "appreciate"]):
        scores["professionalism"] += 0.5
    if any(w in t for w in ["mate", "pal", "buddy"]):
        scores["professionalism"] -= 0.8

    if any(w in t for w in ["option", "solution", "credit", "review"]):
        scores["problem_solving"] += 1
    else:
        scores["problem_solving"] -= 0.4

    if any(w in t for w in ["i’ll sort", "let me check", "we can fix"]):
        scores["de_escalation"] += 0.8
        frustration -= 0.3
    else:
        scores["de_escalation"] -= 0.3

    frustration = max(1, min(3, frustration))

    for k in scores:
        scores[k] = max(0, min(10, scores[k]))

    return scores, frustration

# ---------- CUSTOMER REPLY WITH ACCOUNT LOGIC ----------
def customer_reply(node, frustration, chat_state, scenario_uses_account, account_data):
    last = ""
    for line in reversed(chat_state):
        if not line.startswith("Customer:"):
            last = line.lower()
            break

    # Account-based reactions only for Billing + Upgrade
    if scenario_uses_account:
        if "check" in last or "look" in last or "review" in last:
            used = account_data.get("used_data", "Unknown")
            plan = account_data.get("plan", "Unknown")
            extra = account_data.get("extra_charges", "£0.00")

            return (
                f"Customer: Okay… what does it say? My plan is {plan}, I used {used}, so why is there an extra charge of {extra}?",
                "step4"
            )

    # Normal branching
    if node == "step1":
        if frustration >= 2.5:
            return ("Customer: This isn’t acceptable.", "step2")
        return ("Customer: Can you help me understand why this happened?", "step2")

    if node == "step2":
        if frustration >= 2.5:
            return ("Customer: Are you actually checking my account?", "step3")
        return ("Customer: Thanks — what do you need from me?", "step3")

    if node == "step3":
        if frustration >= 2.5:
            return ("Customer: I just want a straight answer.", "step4")
        return ("Customer: Okay, what did you find?", "step4")

    if node == "step4":
        if frustration >= 2.5:
            return ("Customer: So you're saying this is my fault?", "step5")
        return ("Customer: Thanks — what can we do to fix it?", "step5")

    if node == "step5":
        if frustration >= 2.5:
            return ("Customer: Forget it — I’ll look at switching networks.", "end_bad")
        if frustration >= 1.8:
            return ("Customer: I get it… but I’m not fully convinced.", "end_neutral")
        return ("Customer: That sounds fair — thanks for your help.", "end_good")

    return ("Customer: Thanks for your help today.", "end_good")
# ---------- SCORE TOTAL ----------
def calculate_total_score(scores, frustration):
    base = sum(scores.values())
    penalty = (frustration - 1) * 3
    return max(0, min(50, base - penalty))

# ---------- START SCENARIO ----------
def on_start(name, scenario_name):
    if not name:
        name = "Colleague"

    scenario = SCENARIOS.get(scenario_name, list(SCENARIOS.values())[0])
    scenario_uses_account = scenario.get("uses_account", False)

    # Assign account only if scenario uses account
    if scenario_uses_account:
        account_id = random.choice(list(ACCOUNTS.keys()))
        account_data = ACCOUNTS[account_id]
    else:
        account_id = None
        account_data = {}

    intro = scenario["intro"]
    chat = [f"Customer: {intro}"]

    scores = {
        "empathy": 5,
        "accuracy": 5,
        "professionalism": 5,
        "problem_solving": 5,
        "de_escalation": 5,
    }

    frustration = 2

    tone_score, tone_html = analyse_tone(chat[0])

    coaching = (
        "Start by acknowledging how the customer feels.\n"
        "• Show empathy\n"
        "• Take ownership\n"
        "• Explain what you’ll do next\n"
    )

    image_path = get_customer_image(frustration)

    return (
        image_path,
        "\n".join(chat),
        chat,
        scenario_name,
        "step1",
        scores,
        name,
        False,
        frustration,
        "adult_male",
        0,
        coaching,
        tone_html,
        scenario_uses_account,
        account_id,
        account_data
    )

# ---------- SEND ----------
def on_send(
    user_text,
    chat_state,
    scenario_state,
    node_state,
    scores_state,
    name_state,
    finished_state,
    frustration_state,
    customer_type_state,
    score_bar_state,
    scenario_uses_account,
    account_id,
    account_data
):
    if finished_state:
        image_path = get_customer_image(frustration_state)
        return (
            image_path,
            "\n".join(chat_state),
            chat_state,
            scenario_state,
            node_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            calculate_total_score(scores_state, frustration_state),
            "Scenario finished.",
            analyse_tone(chat_state[-1])[1],
            scenario_uses_account,
            account_id,
            account_data
        )

    if not user_text.strip():
        coaching = "You need to reply to the customer."
        tone_score, tone_html = analyse_tone(chat_state[-1])
        image_path = get_customer_image(frustration_state)
        return (
            image_path,
            "\n".join(chat_state),
            chat_state,
            scenario_state,
            node_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            calculate_total_score(scores_state, frustration_state),
            coaching,
            tone_html,
            scenario_uses_account,
            account_id,
            account_data
        )

    chat_state.append(f"{name_state}: {user_text}")

    # Account investigation tools
    if scenario_uses_account:
        lower = user_text.lower()

        if "usage" in lower:
            chat_state.append(f"System: Customer used {account_data['used_data']} this month.")

        if "plan" in lower:
            chat_state.append(f"System: Customer plan is {account_data['plan']}.")

        if "charges" in lower:
            chat_state.append(f"System: Extra charges: {account_data['extra_charges']}.")

        if "upgrade" in lower:
            chat_state.append(f"System: Upgrade eligibility: {account_data['upgrade_eligibility']}.")

    scores_state, frustration_state = score_reply(user_text, scores_state, frustration_state)

    cust_text, new_node = customer_reply(
        node_state,
        frustration_state,
        chat_state,
        scenario_uses_account,
        account_data
    )

    chat_state.append(cust_text)

    tone_score, tone_html = analyse_tone(cust_text)

    total_score = calculate_total_score(scores_state, frustration_state)

    coaching = live_coaching(user_text)

    finished = new_node.startswith("end")

    if finished:
        ending = (
            "success" if new_node == "end_good"
            else "neutral" if new_node == "end_neutral"
            else "fail"
        )

        entry = {
            "name": name_state,
            "scenario": scenario_state,
            "total_score": round(total_score, 1),
            "date": datetime.utcnow().isoformat(),
            "scores": scores_state,
            "tone_average": tone_score,
            "frustration_change": round(frustration_state - 2, 2),
            "account_id": account_id,
            "account_data": account_data,
            "scenario_length": len(chat_state),
            "ending": ending,
        }
        save_performance(entry)

        coaching += "\n\nScenario finished. Your performance has been recorded."

    image_path = get_customer_image(frustration_state)

    return (
        image_path,
        "\n".join(chat_state),
        chat_state,
        scenario_state,
        new_node,
        scores_state,
        name_state,
        finished,
        frustration_state,
        customer_type_state,
        total_score,
        coaching,
        tone_html,
        scenario_uses_account,
        account_id,
        account_data
    )

# ---------- LIVE UPDATE ----------
def on_live_update(user_text):
    coaching = live_coaching(user_text)
    if not user_text.strip():
        tone_html = "<div>Type your reply to see live tone and coaching.</div>"
    else:
        _, tone_html = analyse_tone(user_text)
    return coaching, tone_html
# ---------- UI ----------
with gr.Blocks(css="""
@media (max-width: 768px) {
    .chatbox { height: 320px !important; }
    .avatar { width: 120px !important; height: 120px !important; }
    .inputbar {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 8px;
        border-top: 1px solid #ddd;
        z-index: 10;
    }
}
""") as demo:

    gr.Markdown("# Tesco Mobile Training Simulator")

    scenario_dropdown = gr.Dropdown(
        choices=list(SCENARIOS.keys()),
        value=list(SCENARIOS.keys())[0],
        label="Choose a scenario",
    )

    with gr.Row():
        with gr.Column(scale=1):
            image_output = gr.Image(
                type="filepath",
                label="Customer",
                height=120,
                width=120,
                elem_classes=["avatar"],
            )
        with gr.Column(scale=3):
            chat_output = gr.Textbox(
                label="Conversation",
                lines=15,
                interactive=False,
                elem_classes=["chatbox"],
            )

    gr.Markdown("### Live Training Dashboard")

    score_bar = gr.Slider(
        minimum=0,
        maximum=50,
        value=0,
        step=1,
        label="Total Performance Score",
        interactive=False,
    )

    tone_display = gr.HTML(label="Tone Meter")

    coaching_box = gr.Textbox(
        label="Real-Time Coaching",
        lines=6,
        interactive=False,
    )

    with gr.Box(elem_classes=["inputbar"]):
        with gr.Row():
            user_input = gr.Textbox(
                label="Your reply",
                placeholder="Type your message…",
            )
            send_button = gr.Button("Send", variant="primary")

    with gr.Row():
        name_input = gr.Textbox(label="Your name")
        start_button = gr.Button("Start Scenario")

    # ---------- STATES ----------
    chat_state = gr.State([])
    scenario_state = gr.State(None)
    node_state = gr.State("")
    scores_state = gr.State({})
    name_state = gr.State("")
    finished_state = gr.State(False)
    frustration_state = gr.State(2)
    customer_type_state = gr.State("adult_male")
    scenario_uses_account_state = gr.State(False)
    account_id_state = gr.State(None)
    account_data_state = gr.State({})

    # ---------- BUTTON LOGIC ----------
    start_button.click(
        on_start,
        inputs=[name_input, scenario_dropdown],
        outputs=[
            image_output,
            chat_output,
            chat_state,
            scenario_state,
            node_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            score_bar,
            coaching_box,
            tone_display,
            scenario_uses_account_state,
            account_id_state,
            account_data_state
        ],
    )

    send_button.click(
        on_send,
        inputs=[
            user_input,
            chat_state,
            scenario_state,
            node_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            score_bar,
            scenario_uses_account_state,
            account_id_state,
            account_data_state
        ],
        outputs=[
            image_output,
            chat_output,
            chat_state,
            scenario_state,
            node_state,
            scores_state,
