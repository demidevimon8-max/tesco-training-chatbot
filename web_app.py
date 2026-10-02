import gradio as gr
import json
import os
from datetime import datetime

PERFORMANCE_FILE = "performance.json"

# ---------- SIMPLE SCENARIO DEFINITION ----------

SCENARIO_NAME = "Billing Issue – Data Overcharge"


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


# ---------- TONE & COACHING HELPERS ----------

def analyse_tone(text):
    text_lower = text.lower()
    score = 2  # 1 = negative, 2 = neutral, 3 = positive

    if any(w in text_lower for w in ["angry", "annoyed", "ridiculous", "useless"]):
        score = 1
    elif any(w in text_lower for w in ["thank", "great", "helpful", "appreciate"]):
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

    if any(w in t for w in ["check", "look into", "investigate", "review"]):
        tips.append("Nice – you’re taking ownership and checking the account.")
    else:
        tips.append("Offer to check their account and explain what you’ll do.")

    if any(w in t for w in ["option", "solution", "can do", "what we can"]):
        tips.append("You’re moving towards solutions – keep it practical and clear.")
    else:
        tips.append("Move towards a clear solution or next step, not just explanation.")

    if "!" in t and not any(w in t for w in ["thank", "great", "appreciate"]):
        tips.append("Watch your tone – too many exclamation marks can feel sharp or defensive.")

    return "\n".join(f"• {tip}" for tip in tips)


# ---------- CORE SIMULATOR LOGIC ----------

def on_start(name):
    if not name:
        name = "Colleague"

    # Initial customer message
    chat = [
        "Customer: Hi, I’ve just checked my bill and there’s a huge data charge I wasn’t expecting. "
        "I’m really annoyed – this doesn’t feel fair."
    ]

    # Initial scores
    scores = {
        "empathy": 5.0,
        "accuracy": 5.0,
        "professionalism": 5.0,
        "problem_solving": 5.0,
        "de_escalation": 5.0,
    }

    # Initial tone
    tone_score, tone_html = analyse_tone(chat[0])

    coaching = (
        "Start by acknowledging how the customer feels.\n"
        "• Show empathy\n"
        "• Take ownership\n"
        "• Explain what you’ll do next\n"
    )

    # Image path (you can change this to match your repo)
    image_path = "characters/adult_male.png"

    return (
        image_path,          # image_output
        "\n".join(chat),     # chat_output
        chat,                # chat_state
        SCENARIO_NAME,       # scenario_state
        "step1",             # node_state
        scores,              # scores_state
        name,                # name_state
        False,               # finished_state
        2,                   # frustration_state (2 = medium)
        "adult_male",        # customer_type_state
        0,                   # score_bar
        coaching,            # coaching_box
        tone_html            # tone_display
    )


def score_reply(user_text, scores, frustration):
    t = user_text.lower()

    # Empathy
    if any(w in t for w in ["sorry", "apologise", "understand", "frustrating"]):
        scores["empathy"] += 1.0
        frustration = max(1, frustration - 0.2)
    else:
        scores["empathy"] -= 0.5
        frustration = min(3, frustration + 0.1)

    # Accuracy
    if any(w in t for w in ["data", "usage", "allowance", "plan", "tariff"]):
        scores["accuracy"] += 0.8
    else:
        scores["accuracy"] -= 0.3

    # Professionalism
    if any(w in t for w in ["please", "thank", "appreciate"]):
        scores["professionalism"] += 0.5
    if any(w in t for w in ["mate", "pal", "buddy", "ridiculous"]):
        scores["professionalism"] -= 0.8

    # Problem solving
    if any(w in t for w in ["option", "solution", "credit", "adjust", "review", "investigate"]):
        scores["problem_solving"] += 1.0
    else:
        scores["problem_solving"] -= 0.4

    # De-escalation
    if any(w in t for w in ["i’ll sort", "i’ll look", "let me check", "we can fix"]):
        scores["de_escalation"] += 0.8
        frustration = max(1, frustration - 0.3)
    else:
        scores["de_escalation"] -= 0.3

    # Clamp scores
    for k in scores:
        scores[k] = max(0.0, min(10.0, scores[k]))

    return scores, frustration


def customer_reply(node, frustration):
    if node == "step1":
        if frustration >= 2.5:
            return (
                "Customer: I just don’t see how this is my fault. "
                "I’ve been with you for years and this feels like you’re taking advantage.",
                "step2",
            )
        else:
            return (
                "Customer: Okay, thanks for looking into it. "
                "I just want to understand what happened and make sure it doesn’t happen again.",
                "step2",
            )
    elif node == "step2":
        if frustration >= 2.5:
            return (
                "Customer: Honestly, if this is how it’s going to be, "
                "I might have to look at other networks.",
                "end_bad",
            )
        else:
            return (
                "Customer: That sounds fair. I appreciate you explaining it and helping me out.",
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
    # Frustration penalty
    penalty = (frustration - 1) * 3.0
    total = max(0.0, min(50.0, base - penalty))
    return total


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
):
    if finished_state:
        # Scenario already finished
        return (
            "characters/adult_male.png",
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
        )

    if not user_text.strip():
        coaching = "You need to reply to the customer. Try acknowledging their feelings first."
        tone_score, tone_html = analyse_tone(chat_state[-1])
        return (
            "characters/adult_male.png",
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
        )

    # Add colleague reply
    chat_state.append(f"{name_state}: {user_text}")

    # Update scores and frustration
    scores_state, frustration_state = score_reply(user_text, scores_state, frustration_state)

    # Customer reply + node advance
    cust_text, new_node = customer_reply(node_state, frustration_state)
    chat_state.append(cust_text)

    # Tone based on latest customer message
    tone_score, tone_html = analyse_tone(cust_text)

    # Total score
    total_score = calculate_total_score(scores_state, frustration_state)

    # Coaching text
    coaching = live_coaching(user_text)

    # Check ending
    finished = new_node.startswith("end")
    ending = "success" if new_node == "end_good" else "fail"

    if finished:
        # Save performance entry
        entry = {
            "name": name_state,
            "scenario": scenario_state,
            "total_score": round(total_score, 1),
            "date": datetime.utcnow().isoformat(),
            "scores": scores_state,
            "tone_average": tone_score,
            "frustration_change": round(frustration_state - 2, 2),
            "branches_triggered": [node_state, new_node],
            "keywords_triggered": [],
            "ending": ending,
        }
        save_performance(entry)
        coaching += "\n\nScenario finished. Your performance has been recorded for the Manager Portal."

    # Image (you can later vary by customer_type_state)
    image_path = "characters/adult_male.png"

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
    )


def on_live_update(user_text):
    coaching = live_coaching(user_text)
    # Tone preview based on your reply (rough)
    if not user_text.strip():
        tone_html = "<div>Type your reply to see live tone and coaching.</div>"
    else:
        _, tone_html = analyse_tone(user_text)
    return coaching, tone_html


# ---------- MOBILE-OPTIMISED UI (CHAT + FULL DASHBOARD) ----------

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

    # --- BUTTON LOGIC ---
    start_button.click(
        on_start,
        inputs=[name_input],
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
        ],
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
        ],
    )

    user_input.change(
        on_live_update,
        inputs=[user_input],
        outputs=[coaching_box, tone_display],
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
