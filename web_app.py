import gradio as gr
import random

# ---------- SCENARIOS ----------
SCENARIOS = [
    {
        "name": "Billing Issue – Overcharge",
        "customer_type": "adult_male",
        "steps": [
            {"customer": "Hi, I've just checked my bill and it's way higher than usual. What's going on?"},
            {"customer": "I don't remember agreeing to any extra charges. This is really frustrating."},
            {"customer": "So what are you going to do about it?"}
        ]
    },
    {
        "name": "Upgrade Confusion – Contract",
        "customer_type": "adult_female",
        "steps": [
            {"customer": "I was told I could upgrade early, but now I'm being told I can't. Which is it?"},
            {"customer": "I've been with you for years, this feels really unfair."},
            {"customer": "Can you explain clearly what my options are?"}
        ]
    }
]

# ---------- HELPER FUNCTIONS ----------
def format_chat(chat_history):
    text = ""
    for msg in chat_history:
        if msg["role"] == "assistant":
            text += f"Customer: {msg['content']}\n\n"
        else:
            text += f"You: {msg['content']}\n\n"
    return text.strip()


def start_chat(name):
    scenario = random.choice(SCENARIOS)
    chat_history = []

    chat_history.append({
        "role": "assistant",
        "content": f"Scenario: {scenario['name']}\n\nCustomer: {scenario['steps'][0]['customer']}"
    })

    step_index = 1
    scores = {
        "empathy": 0,
        "accuracy": 0,
        "professionalism": 0,
        "problem_solving": 0,
        "de_escalation": 0
    }
    finished = False
    frustration = 2
    customer_type = scenario["customer_type"]

    customer_image = f"characters/{customer_type}/neutral.png"
    current_score = 0

    return chat_history, scenario, step_index, scores, name, finished, frustration, customer_type, customer_image, current_score

# ---------- SCORING ENGINE ----------
def score_reply(user_reply, customer_message, frustration_before, frustration_after):
    score = {
        "empathy": 0,
        "accuracy": 0,
        "professionalism": 0,
        "problem_solving": 0,
        "de_escalation": 0
    }

    text = user_reply.lower()

    if any(word in text for word in ["sorry", "understand", "appreciate", "thanks for your patience"]):
        score["empathy"] = 2
    elif any(word in text for word in ["okay", "alright"]):
        score["empathy"] = 1

    if any(word in text for word in ["plan", "contract", "upgrade", "billing", "coverage"]):
        score["accuracy"] = 2
    else:
        score["accuracy"] = 1

    if user_reply.strip().endswith("."):
        score["professionalism"] = 2
    else:
        score["professionalism"] = 1

    if any(word in text for word in ["let me", "i can", "here's what", "next step", "we can"]):
        score["problem_solving"] = 2
    else:
        score["problem_solving"] = 1

    if frustration_after < frustration_before:
        score["de_escalation"] = 2
    elif frustration_after == frustration_before:
        score["de_escalation"] = 1
    else:
        score["de_escalation"] = 0

    return score


def generate_feedback(scores):
    feedback = []

    if scores["empathy"] < 5:
        feedback.append("Try showing more empathy early in the conversation.")
    else:
        feedback.append("Great empathy — you acknowledged the customer's feelings well.")

    if scores["accuracy"] < 5:
        feedback.append("Some information was unclear or incomplete.")
    else:
        feedback.append("Your information was accurate and helpful.")

    if scores["professionalism"] < 5:
        feedback.append("Work on tone and clarity for a more professional feel.")
    else:
        feedback.append("Professional tone throughout — well done.")

    if scores["problem_solving"] < 5:
        feedback.append("You could offer more concrete steps or solutions.")
    else:
        feedback.append("Strong problem-solving — you guided the customer well.")

    if scores["de_escalation"] < 5:
        feedback.append("Try using calming language to reduce frustration.")
    else:
        feedback.append("Excellent de-escalation — you kept frustration under control.")

    return "\n".join(feedback)

# ---------- REAL-TIME COACHING ----------
def live_coaching(user_reply):
    text = user_reply.lower()
    tips = []

    if not any(w in text for w in ["sorry", "understand", "appreciate", "thanks for your patience"]):
        tips.append("Add empathy: e.g. \"I'm sorry about this\" or \"I understand this is frustrating.\"")

    if "!" in text:
        tips.append("Avoid exclamation marks — keep tone calm and professional.")
    if len(user_reply.strip()) < 10:
        tips.append("Give a fuller reply with clear steps or reassurance.")

    if not any(w in text for w in ["let me", "i can", "we can", "here's what", "next step"]):
        tips.append("Offer a next step: e.g. \"Let me check your account\" or \"Here's what we can do.\"")

    if not any(w in text for w in ["help", "support", "resolve", "sort this"]):
        tips.append("Use calming language: \"I'll do my best to resolve this for you.\"")

    if not tips:
        return "✅ This reply looks strong: empathetic, professional, and solution-focused."

    return "Live coaching:\n\n- " + "\n- ".join(tips)

# ---------- TONE METER ----------
def tone_score(text: str) -> int:
    text = text.lower()
    if not text.strip():
        return 50

    score = 50

    positive_words = ["sorry", "understand", "appreciate", "thanks", "help", "support", "resolve",
                      "happy", "glad", "no problem", "absolutely", "let me", "i can", "we can"]
    negative_words = ["no", "can't", "won't", "not possible", "this is wrong", "you need to"]

    for w in positive_words:
        if w in text:
            score += 5

    for w in negative_words:
        if w in text:
            score -= 7

    if "!" in text:
        score -= 5
    if text.isupper() and len(text) > 5:
        score -= 10
    if len(text.strip()) < 10:
        score -= 5
    if text.strip().endswith("."):
        score += 3

    return max(0, min(score, 100))


def tone_badge(score: int) -> str:
    if score >= 76:
        color = "#2ecc71"
        label = "Calm & Empathetic"
    elif score >= 51:
        color = "#f1c40f"
        label = "Neutral / Safe"
    elif score >= 26:
        color = "#e67e22"
        label = "Needs Softening"
    else:
        color = "#e74c3c"
        label = "Risky / Sharp"

    return f"""
    <div style="
        display:inline-block;
        padding:6px 10px;
        border-radius:999px;
        background:{color};
        color:#ffffff;
        font-weight:bold;
        font-size:13px;
    ">
        Tone: {score} — {label}
    </div>
    """

# ---------- CHARACTER SIZE ----------
def resize_character(size):
    return gr.update(height=size, width=size)

# ---------- CORE CHAT LOGIC ----------
def chat_step(user_reply, chat_history, scenario, step_index, scores, name, finished, frustration, customer_type):
    if finished:
        return chat_history, scenario, step_index, scores, name, finished, frustration, None

    customer_message = scenario["steps"][step_index]["customer"]

    chat_history.append({"role": "user", "content": user_reply})

    frustration_before = frustration

    text = user_reply.lower()
    if any(word in text for word in ["no", "can't", "won't", "not possible"]):
        frustration += 1
    elif any(word in text for word in ["sure", "absolutely", "happy", "help"]):
        frustration -= 1

    frustration = max(0, min(frustration, 10))

    score = score_reply(user_reply, customer_message, frustration_before, frustration)
    for k, v in score.items():
        scores[k] = scores.get(k, 0) + v

    chat_history.append({"role": "assistant", "content": customer_message})

    step_index += 1
    finished = step_index >= len(scenario["steps"])

    if frustration < 2:
        emotion = "happy"
    elif frustration < 4:
        emotion = "neutral"
    else:
        emotion = "annoyed"

    customer_image = f"characters/{customer_type}/{emotion}.png"

    return chat_history, scenario, step_index, scores, name, finished, frustration, customer_image

# ---------- GRADIO HANDLERS ----------
def on_start(name):
    chat_history, scenario, step_index, scores, name, finished, frustration, customer_type, customer_image, current_score = start_chat(name)

    coaching_text = "Start typing your reply to see live coaching tips."
    tone_html = tone_badge(50)

    return (
        customer_image,
        format_chat(chat_history),
        chat_state,
        scenario,
        step_index,
        scores,
        name,
        finished,
        frustration,
        customer_type,
        current_score,
        coaching_text,
        tone_html
    )


def on_send(user_reply, chat_history, scenario, step_index, scores, name, finished, frustration, customer_type):
    chat_history, scenario, step_index, scores, name, finished, frustration, customer_image = chat_step(
        user_reply, chat_history, scenario, step_index, scores, name, finished, frustration, customer_type
    )

    if finished:
        final_score = sum(scores.values())
        feedback = generate_feedback(scores)

        chat_history.append({
            "role": "assistant",
            "content": f"### Final Score: {final_score}\n\n{feedback}"
        })

    current_score = sum(scores.values())
    coaching_text = live_coaching(user_reply)
    tone = tone_score(user_reply)
    tone_html = tone_badge(tone)

    return (
        customer_image,
        format_chat(chat_history),
        chat_history,
        scenario,
        step_index,
        scores,
        name,
        finished,
        frustration,
        customer_type,
        current_score,
        coaching_text,
        tone_html
    )


def on_live_update(user_reply):
    coaching_text = live_coaching(user_reply)
    tone = tone_score(user_reply)
    tone_html = tone_badge(tone)
    return coaching_text, tone_html

# ---------- UI ----------
with gr.Blocks() as demo:
    gr.Markdown("# Tesco Mobile Training Simulator")

    with gr.Row():
        image_output = gr.Image(type="filepath", label="Customer", height=350, width=350)
        chat_output = gr.Textbox(label="Conversation", lines=20)

    size_slider = gr.Slider(
        minimum=150,
        maximum=600,
        value=350,
        step=10,
        label="Character Size"
    )

    size_slider.change(
        resize_character,
        inputs=size_slider,
        outputs=image_output
    )

    score_bar = gr.Slider(
        minimum=0,
        maximum=50,
        value=0,
        step=1,
        label="Score Progress",
        interactive=False
    )

    coaching_box = gr.Textbox(
        label="Real-Time Coaching",
        lines=6,
        interactive=False
    )

    tone_display = gr.HTML(label="Tone Meter")

    with gr.Row():
        name_input = gr.Textbox(label="Your name")
        start_button = gr.Button("Start Scenario")

    with gr.Row():
        user_input = gr.Textbox(label="Your reply")
        send_button = gr.Button("Send")

    chat_state = gr.State([])
    scenario_state = gr.State(None)
    step_state = gr.State(0)
    scores_state = gr.State({})
    name_state = gr.State("")
    finished_state = gr.State(False)
    frustration_state = gr.State(2)
    customer_type_state = gr.State("adult_male")

    start_button.click(
        on_start,
        inputs=[name_input],
        outputs=[
            image_output,
            chat_output,
            chat_state,
            scenario_state,
            step_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            score_bar,
            coaching_box,
            tone_display
        ]
    )

    send_button.click(
        on_send,
        inputs=[
            user_input,
            chat_state,
            scenario_state,
            step_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state
        ],
        outputs=[
            image_output,
            chat_output,
            chat_state,
            scenario_state,
            step_state,
            scores_state,
            name_state,
            finished_state,
            frustration_state,
            customer_type_state,
            score_bar,
            coaching_box,
            tone_display
        ]
    )

    user_input.change(
        on_live_update,
        inputs=[user_input],
        outputs=[coaching_box, tone_display]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
