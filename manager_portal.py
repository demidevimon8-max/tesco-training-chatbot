import gradio as gr
import json

def load_performance():
    with open("performance.json") as f:
        data = json.load(f)
    return data

def load_scenarios():
    with open("scenarios.json") as f:
        data = json.load(f)
    return data

def manager_dashboard():
    performance = load_performance()
    scenarios = load_scenarios()

    return {
        "performance": performance,
        "scenarios": scenarios
    }

with gr.Blocks() as app:
    gr.Markdown("# 📊 Manager Portal")
    gr.Markdown("View colleague performance and training scenarios.")

    with gr.Tab("Performance"):
        perf_output = gr.JSON(label="Performance Data")
        gr.Button("Load Performance").click(fn=load_performance, outputs=perf_output)

    with gr.Tab("Scenarios"):
        scen_output = gr.JSON(label="Scenarios")
        gr.Button("Load Scenarios").click(fn=load_scenarios, outputs=scen_output)

app.launch()
