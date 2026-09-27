import json
import random
import datetime

# Load scenarios
with open("scenarios.json", "r") as f:
    scenarios = json.load(f)

# Load performance tracking file
def load_performance():
    try:
        with open("performance.json", "r") as f:
            return json.load(f)
    except:
        return []

def save_performance(data):
    with open("performance.json", "w") as f:
        json.dump(data, f, indent=4)

def start_scenario():
    scenario = random.choice(scenarios)
    print(f"\n📱 Customer: {scenario['opening']}")
    return scenario

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

    # Behaviour scoring from scenario behaviours
    for behaviour in behaviours:
        if behaviour.lower() in reply:
            behaviour_score += 1

    # Knowledge scoring from scenario keywords
    for keyword in keywords:
        if keyword.lower() in reply:
            knowledge_score += 1

    # Conversation scoring
    if any(word in reply for word in ["happy", "help", "support"]):
        conversation_score += 1
    if any(word in reply for word in ["recommend", "suggest"]):
        conversation_score += 1
    if any(word in reply for word in ["anything else", "any other questions"]):
        conversation_score += 1

    # Probing
    if any(word in reply for word in ["why", "how often", "since when", "tell me more", "could you explain"]):
        probing_score += 1

    # Compliance
    if any(word in reply for word in ["policy", "terms", "conditions", "id", "eligibility", "cooling off"]):
        compliance_score += 1

    # Rapport
    if any(word in reply for word in ["thank", "appreciate", "no worries", "that's okay", "glad"]):
        rapport_score += 1

    # Confidence
    if any(word in reply for word in ["definitely", "i recommend", "we can", "i can", "we'll"]):
        confidence_score += 1

    # Accuracy (simple keyword-based)
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

def run_chat(scenario):
    behaviour_score = 0
    knowledge_score = 0
    conversation_score = 0
    probing_score = 0
    compliance_score = 0
    rapport_score = 0
    confidence_score = 0
    accuracy_score = 0

    print("\n--- Training Scenario Started ---")

    # Structured 10-step scenario
    for step in scenario["steps"]:
        user_reply = input("\n👤 Your reply: ")

        (
            b, k, c,
            p, comp, r,
            conf, acc
        ) = score_reply(user_reply, step["behaviours"], step["keywords"])

        behaviour_score += b
        knowledge_score += k
        conversation_score += c
        probing_score += p
        compliance_score += comp
        rapport_score += r
        confidence_score += conf
        accuracy_score += acc

        print(f"\n📱 Customer: {step['customer_response']}")

    # Free-conversation mode
    print("\n--- Free conversation mode ---")
    print("You can continue chatting with the customer.")
    print("Type END to finish the scenario.\n")

    while True:
        user_reply = input("👤 Your reply (or type END): ")
        if user_reply.strip().lower() == "end":
            break

        (
            b, k, c,
            p, comp, r,
            conf, acc
        ) = score_reply(user_reply, [], [])

        behaviour_score += b
        knowledge_score += k
        conversation_score += c
        probing_score += p
        compliance_score += comp
        rapport_score += r
        confidence_score += conf
        accuracy_score += acc

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

def give_feedback(
    behaviour,
    knowledge,
    conversation,
    probing,
    compliance,
    rapport,
    confidence,
    accuracy
):
    total = (
        behaviour
        + knowledge
        + conversation
        + probing
        + compliance
        + rapport
        + confidence
        + accuracy
    )

    print("\n--- 📊 Training Feedback ---")
    print(f"Behaviour Score: {behaviour}")
    print(f"Knowledge Score: {knowledge}")
    print(f"Conversation Score: {conversation}")
    print(f"Probing Score: {probing}")
    print(f"Compliance Score: {compliance}")
    print(f"Rapport Score: {rapport}")
    print(f"Confidence Score: {confidence}")
    print(f"Accuracy Score: {accuracy}")
    print(f"\nTotal Score: {total}\n")

    if total < 10:
        print("Needs improvement — focus on empathy, ownership, and product knowledge.")
    elif total < 20:
        print("Good effort — some strong behaviours, but room to grow.")
    elif total < 30:
        print("Very good — confident, clear, and customer‑focused.")
    else:
        print("Excellent — you handled this like a top‑tier Tesco Mobile colleague!")

    return total

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

def show_leaderboard():
    performance = load_performance()

    if not performance:
        print("\n📉 No performance data yet.")
        return

    # Sort by total score (highest first)
    sorted_scores = sorted(performance, key=lambda x: x["total_score"], reverse=True)

    print("\n🏆 --- Tesco Mobile Training Leaderboard --- 🏆")
    rank = 1

    for entry in sorted_scores[:10]:  # Top 10
        print(f"\n#{rank}  {entry['name']}")
        print(f"   Score: {entry['total_score']}")
        print(f"   Scenario: {entry['scenario_opening'][:40]}...")
        print(f"   Date: {entry['date']}")
        rank += 1

    print("\nUse training regularly to climb the leaderboard!")

def main():
    print("\n📘 Tesco Mobile Training System")
    print("1. Start training scenario")
    print("2. View leaderboard")
    print("3. Exit")

    choice = input("\nSelect an option (1/2/3): ")

    if choice == "1":
        name = input("Enter colleague name: ")

        scenario = start_scenario()
        (
            behaviour,
            knowledge,
            conversation,
            probing,
            compliance,
            rapport,
            confidence,
            accuracy
        ) = run_chat(scenario)

        total = give_feedback(
            behaviour,
            knowledge,
            conversation,
            probing,
            compliance,
            rapport,
            confidence,
            accuracy
        )

        record_performance(
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
        )

        print("\n📁 Performance saved successfully.")

    elif choice == "2":
        show_leaderboard()

    else:
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
