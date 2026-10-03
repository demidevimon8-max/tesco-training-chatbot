import gradio as gr
import json
import os
import random
from datetime import datetime

PERFORMANCE_FILE = "performance.json"
SCENARIOS_FILE = "scenarios.json"

# ---------- SIMPLE SCENARIO DEFINITION ----------

DEFAULT_SCENARIO_NAME = "Billing Issue – Data Overcharge"

# ---------- CUSTOMER PERSONALITY PROFILES ----------

CUSTOMER_PROFILES = {
    "polite": {
        "intro": "Hi, sorry to bother you… I’ve just noticed a strange charge on my bill.",
        "tone_bias": -0.3,
    },
    "angry": {
        "intro": "Right, what’s going on with my bill? This is ridiculous.",
        "tone_bias": 0.5,
    },
    "confused": {
        "intro": "Um… I’m not sure what this charge is. Can you help me understand it?",
        "tone_bias": 0.0,
    },
    "rushed": {
        "intro": "I don’t have much time — what’s this charge on my bill?",
        "tone_bias": 0.2,
    },
}

# ---------- FILE HELPERS ----------

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


def save_performance(entry):
    data = load_performance()
    data.append(entry)
    try:
        with open(PERFORMANCE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def load_scenarios():
    if not os.path.exists(SCENARIOS_FILE):
        # Fallback: single default scenario
        return {
            DEFAULT_SCENARIO_NAME: {
                "intro": "I’ve just checked my bill and there’s a huge data charge I wasn’t expecting.",
                "steps": ["step1", "step2", "step3", "step4", "step5"],
            },
            "Lost SIM / Replacement": {
                "intro": "I’ve lost my SIM card and I need a replacement urgently.",
                "steps": ["step1", "step2", "step3", "step4"],
            },
            "Upgrade Eligibility": {
                "intro": "I want to upgrade but the app says I’m not eligible. Why?",
                "steps": ["step1", "step2", "step3", "step4", "step5"],
            },
        }
    try:
        with open(SCENARIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
    except Exception:
        return {}


SCENARIOS = load_scenarios()

# ---------- TONE & COACHING HELPERS ----------

def analyse_tone(text):
    text_lower = text.lower()
    score = 2  # 1 = negative, 2 = neutral, 3 = positive

    if any(w in text_lower for w in ["angry", "annoyed", "ridiculous", "useless", "furious"]):
        score = 1
    elif any(w in text_lower for w in ["thank", "great", "helpful", "appreciate", "brilliant"]):
        score = 3

    if "!" in text and score == 2:
        score = 1

    if score == 1:
        label = "Customer tone: <b style='color:red;'>Negative / Frustrated</b>"
    elif score == 3:
        label = "Customer tone: <b style='color:green;'>Positive / Reassured</b>"
    else:
        label = "Customer tone: <b style='color:orange;'>Neutral / Unsure</b>"

    return score, f"<div>{label}</div>"


def live_coaching(text):
    t = text.lower()
    tips = []

    if "sorry" in t or "apologise" in t:
        tips.append("Good empathy – you’re acknowledging their feelings.")
    else:
        tips.append("Try adding an apology to show empathy (e.g. 'I’m really sorry this happened').")

    if any(w in t for w in ["check", "look into", "investigate", "review", "have a look"]):
        tips.append("Nice – you’re taking ownership and checking the account.")
    else:
        tips.append("Offer to check their account and explain what you’ll do.")

    if any(w in t for w in ["option", "solution", "can do", "what we can", "next step"]):
        tips.append("You’re moving towards solutions – keep it practical and clear.")
    else:
        tips.append("Move towards a clear solution or next step, not just explanation.")

    if "!" in t and not any(w in t for w in ["thank", "great", "appreciate"]):
        tips.append("Watch your tone – too many exclamation marks can feel sharp or defensive.")

    return "\n".join(f"• {tip}" for tip in tips)


# ---------- DYNAMIC CUSTOMER IMAGE ----------

def get_customer_image(frustration, customer_type="adult_male"):
    base_path = f"characters/{customer_type}"
    if frustration <= 1.4:
        return f"{base_path}/happy.png"
    elif frustration <= 2.2:
        return f"{base_path}/neutral.png"
    else:
        return f"{base_path}/annoyed.png"


# ---------- CORE SCORING & EMOTIONAL MEMORY ----------

def score_reply(user_text, scores, frustration):
    t = user_text.lower()

    # Empathy
    if any(w in t for w in ["sorry", "apologise", "understand", "frustrating", "appreciate"]):
        scores["empathy"] += 1.0
        frustration = max(1, frustration - 0.2)
    else:
        scores["empathy"] -= 0.5
        frustration = min(3, frustration + 0.1)

    # Accuracy
    if any(w in t for w in ["data", "usage", "allowance", "plan", "tariff", "bill"]):
        scores["accuracy"] += 0.8
    else:
        scores["accuracy"] -= 0.3

    # Professionalism
    if any(w in t for w in ["please", "thank", "appreciate", "happy to help"]):
        scores["professionalism"] += 0.5
    if any(w in t for w in ["mate", "pal", "buddy", "ridiculous", "joke"]):
        scores["professionalism"] -= 0.8

    # Problem solving
    if any(w in t for w in ["option", "solution", "credit", "adjust", "review", "investigate", "fix"]):
        scores["problem_solving"] += 1.0
    else:
        scores["problem_solving"] -= 0.4

    # De-escalation
    if any(w in t for w in ["i’ll sort", "i’ll look", "let me check", "we can fix", "i’ll do my best"]):
        scores["de_escalation"] += 0.8
        frustration = max(1, frustration - 0.3)
    else:
        scores["de_escalation"] -= 0.3

    # Emotional memory
    if "thank" in t or "appreciate" in t:
        frustration -= 0.1
    if "why" in t or "explain" in t:
        frustration += 0.1

    frustration = max(1, min(3, frustration))

    for k in scores:
        scores[k] = max(0.0, min(10.0, scores[k]))

    return scores, frustration


# ---------- EXTENDED BRANCHING & HIDDEN KEYWORDS ----------

def customer_reply(node, frustration, chat_state):
    # Hidden keyword triggers based on last colleague message
    last_text = ""
    for line in reversed(chat_state):
        if not line.startswith("Customer:"):
            last_text = line.lower()
            break

    # Hidden branches
    if "credit" in last_text or "refund" in last_text:
        return (
            "Customer: Oh… okay, that actually helps. I wasn’t expecting that.",
            "step4_relief",
        )

    if "complaint" in last_text or "ombudsman" in last_text:
        return (
            "Customer: I didn’t want it to get formal… I just want this sorted.",
            "step4_defensive",
        )

    if "upgrade" in last_text or "new phone" in last_text:
        return (
            "Customer: I mean… I *have* been thinking about upgrading.",
            "step4_distraction",
        )

    # Main linear branching
    if node == "step1":
        if frustration >= 2.5:
            return (
                "Customer: This really isn’t acceptable. I didn’t use anything close to that amount of data.",
                "step2",
            )
        else:
            return (
                "Customer: Okay… can you help me understand why this happened?",
                "step2",
            )

    elif node == "step2":
        if frustration >= 2.5:
            return (
                "Customer: I feel like nobody ever explains this properly. Are you actually checking my account?",
                "step3",
            )
        else:
            return (
                "Customer: Thanks for looking into it. What do you need from me?",
                "step3",
            )

    elif node == "step3":
        if frustration >= 2.5:
            return (
                "Customer: This is taking ages… I just want a straight answer.",
                "step4",
            )
        else:
            return (
                "Customer: Okay, that makes sense. What did you find?",
                "step4",
            )

    elif node == "step4":
        if frustration >= 2.5:
            return (
                "Customer: So you're saying this is basically my fault? That doesn’t sound right.",
                "step5",
            )
        else:
            return (
                "Customer: Thanks for explaining it clearly. What can we do to fix it?",
                "step5",
            )

    elif node == "step4_relief":
        return (
            "Customer: Honestly, that makes a big difference. I was worried I’d be stuck with the full amount.",
            "step5",
        )

    elif node == "step4_defensive":
        return (
            "Customer: I just don’t want this to turn into a big argument. I just want it sorted fairly.",
            "step5",
        )

    elif node == "step4_distraction":
        return (
            "Customer: If I did upgrade, would that change how my data is charged?",
            "step5",
        )

    elif node == "step5":
        if frustration >= 2.5:
            return (
                "Customer: You know what… forget it. I’ll look at switching networks.",
                "end_bad",
            )
        elif frustration >= 1.8:
            return (
                "Customer: I mean… I get it, but I’m still not totally convinced.",
                "end_neutral",
            )
        else:
            return (
                "Customer: That sounds fair. I appreciate your help today.",
                "end_good",
            )

    else:
        return (
            "Customer: Thanks for your help today.",
            "end_good",
        )


def calculate_total_score(scores, frustration):
    base = (
        scores["empathy"]
        + scores["accuracy"]
        + scores["professionalism"]
        + scores["problem_solving"]
        + scores["de_escalation"]
    )
    penalty = (frustration - 1) * 3.0
    total = max(0.0, min(50.0, base - penalty))
    return total


# ---------- START & SEND HANDLERS ----------

def on_start(name, scenario_name):
    if not name:
        name = "Colleague"

    if scenario_name not in SCENARIOS:
        scenario_name = DEFAULT_SCENARIO_NAME

    scenario = SCENARIOS[scenario_name]

    profile_name = random.choice(list(CUSTOMER_PROFILES.keys()))
    profile = CUSTOMER_PROFILES[profile_name]

    intro = scenario.get("intro", profile["intro"])
    chat = [f"Customer: {intro}"]

    scores = {
        "empathy": 5.0,
        "accuracy": 5.0,
        "professionalism": 5.0,
        "problem_solving": 5.0,
        "de_escalation": 5.0,
    }

    frustration = 2 + profile["tone_bias"]
    frustration = max(1, min(3, frustration))

    tone_score, tone_html = analyse_tone(chat[0])

    coaching = (
        "Start by acknowledging how the customer feels.\n"
        "• Show empathy\n"
        "• Take ownership\n"
        "• Explain what you’ll do next\n"
    )

    image_path = get_customer_image(frustration, customer_type="adult_male")

    return (
        image_path,          # image_output
        "\n".join(chat),     # chat_output
        chat,                # chat_state
        scenario_name,       # scenario_state
        "step1",             # node_state
        scores,              # scores_state
        name,                # name_state
        False,               # finished_state
        frustration,         # frustration_state
        "adult_male",        # customer_type_state
        0,                   # score_bar
        coaching,            # coaching_box
        tone_html,           # tone_display
        profile_name,        # customer_profile_state
        [],                  # hidden_branches_state
    )


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
    customer_profile_state,
    hidden_branches_state,
):
    if finished_state:
        image_path = get_customer_image(frustration_state, customer_type_state)
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
            "Scenario already finished. Start a new one to continue training.",
            analyse_tone(chat_state[-1])[1],
            customer_profile_state,
            hidden_branches_state,
        )

    if not user_text.strip():
        coaching = "You need to reply to the customer. Try acknowledging their feelings first."
        tone_score, tone_html = analyse_tone(chat_state[-1])
        image_path = get_customer_image(frustration_state, customer_type_state)
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
            customer_profile_state,
            hidden_branches_state,
        )

    chat_state.append(f"{name_state}: {user_text}")

    scores_state, frustration_state = score_reply(user_text, scores_state, frustration_state)

    cust_text, new_node = customer_reply(node_state, frustration_state, chat_state)
    chat_state.append(cust_text)

    tone_score, tone_html = analyse_tone(cust_text)

    total_score = calculate_total_score(scores_state, frustration_state)

    coaching = live_coaching(user_text)

    finished = new_node.startswith("end")
    if finished:
        ending = "success" if new_node == "end_good" else ("neutral" if new_node == "end_neutral" else "fail")

        entry = {
            "name": name_state,
            "scenario": scenario_state,
            "total_score": round(total_score, 1),
            "date": datetime.utcnow().isoformat(),
            "scores": scores_state,
            "tone_average": tone_score,
            "frustration_change": round(frustration_state - 2, 2),
            "branches_triggered": [node_state, new_node],
            "hidden_branches": hidden_branches_state,
            "customer_profile": customer_profile_state,
            "scenario_length": len(chat_state),
            "ending": ending,
        }
        save_performance(entry)
        coaching += "\n\nScenario finished. Your performance has been recorded for the Manager Portal."

    image_path = get_customer_image(frustration_state, customer_type_state)

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
        customer_profile_state,
        hidden_branches_state,
    )


def on_live_update(user_text):
    coaching = live_coaching(user_text)
    if not user_text.strip():
        tone_html = "<div>Type your reply to see live tone and coaching.</div>"
    else:
        _, tone_html = analyse_tone(user_text)
    return coaching, tone_html


# ---------- MOBILE-OPTIMISED UI (CHAT + FULL DASHBOARD + SCENARIO SELECT) ----------

with gr.Blocks(
    css="""
/* MOBILE OPTIMISATION */
@media (max-width: 768px) {
    .chatbox {
        height: 320px !important;
    }
    .avatar {
        width: 120px !important;
        height: 120px !important;
    }
    .inputbar {
        position: sticky;
        bottom: 0;
        background: white;
        padding: 8px;
        border-top: 1px solid #ddd;
        z-index: 10;
    }
}
"""
) as demo:

    gr.Markdown("# Tesco Mobile Training Simulator")

    # Scenario selection
    scenario_dropdown = gr.Dropdown(
        choices=list(SCENARIOS.keys()),
        value=DEFAULT_SCENARIO_NAME if DEFAULT_SCENARIO_NAME in SCENARIOS else None,
        label="Choose a scenario",
    )

    # --- TOP SECTION: Avatar + Chat ---
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
                elem_classes=["chatbox"],
                interactive=False,
            )

    # --- FULL DASHBOARD: Score + Coaching + Tone ---
    gr.Markdown("### Live Training Dashboard")

    with gr.Row():
        with gr.Column(scale=2):
            score_bar = gr.Slider(
                minimum=0,
                maximum=50,
                value=0,
                step=1,
                label="Total Performance Score",
                interactive=False,
            )
        with gr.Column(scale=2):
            tone_display = gr.HTML(label="Tone Meter")

    coaching_box = gr.Textbox(
        label="Real-Time Coaching",
        lines=6,
        interactive=False,
    )

    # --- INPUT BAR (BOTTOM) ---
    with gr.Box(elem_classes=["inputbar"]):
        with gr.Row():
            user_input = gr.Textbox(
                label="Your reply",
                placeholder="Type your message…",
            )
            send_button = gr.Button("Send", variant="primary")

    # --- START BUTTON + NAME ---
    with gr.Row():
        name_input = gr.Textbox(label="Your name")
        start_button = gr.Button("Start Scenario")

    # --- STATES ---
    chat_state = gr.State([])
    scenario_state = gr.State(None)
    node_state = gr.State("")
    scores_state = gr.State({})
    name_state = gr.State("")
    finished_state = gr.State(False)
    frustration_state = gr.State(2)
    customer_type_state = gr.State("adult_male")
    customer_profile_state = gr.State("")
    hidden_branches_state = gr.State([])

    # --- BUTTON LOGIC ---
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
            customer_profile_state,
            hidden_branches_state,
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
            customer_profile_state,
            hidden_branches_state,
        ],
        outputs[
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
            customer_profile_state,
            hidden_branches_state,
        ],
    )

    user_input.change(
        on_live_update,
        inputs=[user_input],
        outputs=[coaching_box, tone_display],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
