import gradio as gr
import json
import os

# -----------------------------
# Load Scenarios
# -----------------------------
def load_scenarios():
    try:
        with open("scenarios.json") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Could not load scenarios.json: {e}"}

# -----------------------------
# Save Performance
# -----------------------------
def save_performance(data):
    try:
        with open("performance.json", "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        return False

# -----------------------------
# Run Scenario Logic
# -----------------------------
def run_scenario(scenario_id, user_input):
    scenarios = load_scenarios()

    if "error" in scenarios:
        return scenarios["error"], 0

    if scenario_id not in scenarios:
        return "Scenario not found.", 0

    scenario = scenarios[scenario_id]

    system_response = scenario.get("response", "No response found.")
    score = scenario.get("score", 0)

    performance_record = {
        "scenario": scenario_id,
        "user_input": user_input,
        "score": score
    }

    save_performance(performance_record)

    return system_response, score

# -----------------------------
# Gradio UI
# -----------------------------
with gr.Blocks() as app:
    gr.Markdown("# 🧑‍💼 Tesco Mobile Colleague Training Simulator")
    gr.Markdown("Choose a scenario, enter your response, and receive feedback.")

    scenarios = load_scenarios()
    scenario_list = list(scenarios.keys()) if isinstance(scenarios, dict) else []

    scenario_id = gr.Dropdown(scenario_list, label="Choose Scenario")
    user_input = gr.Textbox(label="Your Response")

    response_output = gr.Textbox(label="System Response")
    score_output = gr.Number(label="Score")

    gr.Button("Submit").click(
        fn=run_scenario,
        inputs=[scenario_id, user_input],
        outputs=[response_output, score_output]
    )

app.launch()
