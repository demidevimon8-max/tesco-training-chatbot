import json
import random
import datetime
import gradio as gr

# Load scenarios
with open("scenarios.json", "r") as f:
    scenarios = json.load(f)

# Performance tracking
def load_performance():
    try:
        with open("performance.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_performance(data):
    with open("performance.json", "w") as f:
        json.dump(data, f, indent=4)

def score_reply(user_reply, behaviours, keywords):
    reply = user_reply.lower()

    behaviour_score = 0
    knowledge_score = 0
    conversation_score = 0
    probing_score = 0
    compliance_score = 0
    rapport_score = 0
    confidence_score = 0
    accuracy_score = 0

    for behaviour in behaviours:
        if behaviour.lower() in reply:
            behaviour_score += 1

    for keyword in keywords:
        if keyword.lower() in reply:
            knowledge_score += 1

    if any(word in reply for word in ["happy", "help", "support"]):
        conversation_score += 1
    if any(word in reply for word in ["recommend", "suggest"]):
        conversation_score += 1
    if any(word in reply for word in ["anything else", "any other questions"]):
        conversation_score += 1

    if any(word in reply for word in ["why", "how often", "since when", "tell me more", "could you explain"]):
        probing_score += 1

    if any(word in reply for word in ["policy", "terms", "conditions", "id", "eligibility", "cooling off"]):
        compliance_score += 1

    if any(word in reply for word in ["thank", "appreciate", "no worries", "that's okay", "glad"]):
        rapport_score += 1

    if any(word in reply for word in ["definitely", "i recommend", "we can", "i can", "we'll"]):
        confidence_score += 1

    if any(word in reply for word in [
        "pac", "stac", "wifi calling", "volte", "apn", "clubcard",
        "cooling off", "24 month", "30 day"
    ]):
        accuracy_score += 1

    return (
        behaviour_score,
        knowledge_score,
        conversation_score,
        probing_score,
        compliance_score,
        rapport_score,
        confidence_score,
        accuracy_score
    )

def record_performance(
    name,
    scenario,
    behaviour,
    knowledge,
    conversation,
    probing,
    compliance,
    rapport,
    confidence,
    accuracy,
    total
):
    performance = load_performance()

    entry = {
        "name": name,
        "scenario_opening": scenario["opening"],
        "behaviour_score": behaviour,
        "knowledge_score": knowledge,
        "conversation_score": conversation,
        "probing_score": probing,
        "compliance_score": compliance,
        "rapport_score": rapport,
        "confidence_score": confidence,
        "accuracy_score": accuracy,
        "total_score": total,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    }

    performance.append(entry)
    save_performance(performance)

def start_chat(name):
    scenario = random.choice(scenarios)
    opening = scenario["opening"]

    chat_history = []
    chat_history.append(("System", f"Scenario started for {name}."))
    chat_history.append(("Customer", opening))

    scores = {
        "behaviour": 0,
        "knowledge": 0,
        "conversation": 0,
        "probing": 0,
        "compliance": 0,
        "rapport": 0,
        "confidence": 0,
        "accuracy": 0
    }

    step_index = 0
    finished = False

    return chat_history, scenario, step_index, scores, name, finished

def chat_step(user_reply, chat_history, scenario, step_index, scores, name, finished):
    if finished:
        chat_history.append(("System", "Scenario already finished. Start a new one to continue."))
        return chat_history, scenario, step_index, scores, name, finished

    user_reply = user_reply.strip()
    if not user_reply:
        return chat_history, scenario, step_index, scores, name, finished

    if step_index >= len(scenario["steps"]):
        if user_reply.lower() == "end":
            total = sum(scores.values())

            feedback_lines = [
                f"Behaviour: {scores['behaviour']}",
                f"Knowledge: {scores['knowledge']}",
                f"Conversation: {scores['conversation']}",
                f"Probing: {scores['probing']}",
                f"Compliance: {scores['compliance']}",
                f"Rapport: {scores['rapport']}",
                f"Confidence: {scores['confidence']}",
                f"Accuracy: {scores['accuracy']}",
                f"Total: {total}"
            ]

            if total < 10:
                summary = "Needs improvement — focus on empathy, ownership, and product knowledge."
            elif total < 20:
                summary = "Good effort — some strong behaviours, but room to grow."
            elif total < 30:
                summary = "Very good — confident, clear, and customer‑focused."
            else:
                summary = "Excellent — you handled this like a top‑tier Tesco Mobile colleague."

            feedback_text = "Feedback:\n" + "\n".join(feedback_lines) + "\n\n" + summary

            chat_history.append(("You", user_reply))
            chat_history.append(("System", feedback_text))

            record_performance(
                name,
                scenario,
                scores["behaviour"],
                scores["knowledge"],
                scores["conversation"],
                scores["probing"],
                scores["compliance"],
                scores["rapport"],
                scores["confidence"],
                scores["accuracy"],
                total
            )

            finished = True
            return chat_history, scenario, step_index, scores, name, finished
        else:
            (
                b, k, c,
                p, comp, r,
                conf, acc
            ) = score_reply(user_reply, [], [])

            scores["behaviour"] += b
            scores["knowledge"] += k
            scores["conversation"] += c
            scores["probing"] += p
            scores["compliance"] += comp
            scores["rapport"] += r
            scores["confidence"] += conf
            scores["accuracy"] += acc

            chat_history.append(("You", user_reply))
            chat_history.append(("Customer", "Thanks, keep going or type END to finish."))

            return chat_history, scenario, step_index, scores, name, finished

    step = scenario["steps"][step_index]

    (
        b, k, c,
        p, comp, r,
        conf, acc
    ) = score_reply(user_reply, step["behaviours"], step["keywords"])

    scores["behaviour"] += b
    scores["knowledge"] += k
    scores["conversation"] += c
    scores["probing"] += p
    scores["compliance"] += comp
    scores["rapport"] += r
    scores["confidence"] += conf
    scores["accuracy"] += acc

    chat_history.append(("You", user_reply))
    chat_history.append(("Customer", step["customer_response"]))

    step_index += 1

    if step_index == len(scenario["steps"]):
        chat_history.append(("System", "Structured steps complete. You are now in free conversation mode. Type END to finish."))

    return chat_history, scenario, step_index, scores, name, finished

def format_chat(chat_history):
    formatted = []
    for speaker, text in chat_history:
        if speaker == "You":
            formatted.append((text, None))
        else:
            formatted.append((None, f"{speaker}: {text}"))
    return formatted

with gr.Blocks() as demo:
    gr.Markdown("# Tesco Mobile Training Web App")

    name_input = gr.Textbox(label="Colleague name")
    start_button = gr.Button("Start scenario")

    chatbot = gr.Chatbot(label="Conversation")
    user_input = gr.Textbox(label="Your reply")
    send_button = gr.Button("Send")

    chat_state = gr.State([])
    scenario_state = gr.State(None)
    step_state = gr.State(0)
    scores_state = gr.State({})
    name_state = gr.State("")
    finished_state = gr.State(False)

    def on_start(name):
        chat_history, scenario, step_index, scores, name, finished = start_chat(name)
        return (
            format_chat(chat_history),
            chat_history,
            scenario,
            step_index,
            scores,
            name,
            finished
        )

    start_button.click(
        on_start,
        inputs=[name_input],
        outputs=[
            chatbot,
            chat_state,
            scenario_state,
            step_state,
            scores_state,
            name_state,
            finished_state
        ]
    )

    def on_send(user_reply, chat_history, scenario, step_index, scores, name, finished):
        if scenario is None:
            chat_history.append(("System", "Start a scenario first."))
            return format_chat(chat_history), chat_history, scenario, step_index, scores, name, finished

        chat_history, scenario, step_index, scores, name, finished = chat_step(
            user_reply, chat_history, scenario, step_index, scores, name, finished
        )
        return format_chat(chat_history), chat_history, scenario, step_index, scores, name, finished

    send_button.click(
        on_send,
        inputs=[user_input, chat_state, scenario_state, step_state, scores_state, name_state, finished_state],
        outputs=[chatbot, chat_state, scenario_state, step_state, scores_state, name_state, finished_state]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0")
