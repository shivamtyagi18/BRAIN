
import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from .core.orchestrator import BrainOrchestrator
from .personas.persona_registry import list_personas, get_persona

app = Flask(
    __name__,
    template_folder="web/templates",
    static_folder="web/static"
)

# Global brain instance
brain: BrainOrchestrator = None
current_config = {
    "provider": "ollama",
    "model_name": "mistral",
    "persona_name": None,
    "persona_active": False
}

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/init", methods=["POST"])
def init_brain():
    """Initialize the brain with a specific provider."""
    global brain, current_config
    data = request.json
    provider = data.get("provider", "ollama")
    model_name = data.get("model_name", None)

    try:
        brain = BrainOrchestrator(provider=provider, model_name=model_name)
        current_config["provider"] = provider
        current_config["model_name"] = model_name
        current_config["persona_name"] = None
        current_config["persona_active"] = False
        return jsonify({"status": "ok", "message": f"Brain initialized with {provider}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/persona", methods=["POST"])
def load_persona():
    """Upload a document and load persona."""
    global brain, current_config
    if brain is None:
        return jsonify({"status": "error", "message": "Brain not initialized"}), 400

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "No file selected"}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    try:
        brain.set_persona(filepath)
        current_config["persona_name"] = brain.persona.name
        current_config["persona_active"] = True
        return jsonify({
            "status": "ok",
            "persona_name": brain.persona.name,
            "profile": brain.persona.profile
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/persona/clear", methods=["POST"])
def clear_persona():
    """Clear active persona."""
    global brain, current_config
    if brain is None:
        return jsonify({"status": "error", "message": "Brain not initialized"}), 400

    # Clear persona context from all agents
    agents = [brain.sensory, brain.memory, brain.emotional, brain.logic, brain.executive]
    for agent in agents:
        agent.persona_context = ""
    brain.persona = None
    brain.vector_memory.clear()
    current_config["persona_name"] = None
    current_config["persona_active"] = False
    return jsonify({"status": "ok", "message": "Persona cleared"})


@app.route("/api/personas", methods=["GET"])
def list_available_personas():
    """Return list of available pre-curated personas."""
    return jsonify({"status": "ok", "personas": list_personas()})


@app.route("/api/persona/select", methods=["POST"])
def select_persona():
    """Select a pre-curated persona by ID."""
    global brain, current_config
    if brain is None:
        return jsonify({"status": "error", "message": "Brain not initialized"}), 400

    data = request.json
    persona_id = data.get("id", "")

    persona_data = get_persona(persona_id)
    if persona_data is None:
        return jsonify({"status": "error", "message": f"Unknown persona: {persona_id}"}), 404

    try:
        brain.set_persona_from_dict(persona_data)
        current_config["persona_name"] = brain.persona.name
        current_config["persona_active"] = True
        return jsonify({
            "status": "ok",
            "persona_name": brain.persona.name,
            "profile": brain.persona.profile
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/reset", methods=["POST"])
def reset_brain():
    """Full reset — destroy brain instance and return to setup."""
    global brain, current_config
    brain = None
    current_config = {
        "provider": "ollama",
        "model_name": "mistral",
        "persona_name": None,
        "persona_active": False
    }
    return jsonify({"status": "ok", "message": "Brain reset complete"})


@app.route("/api/memory/clear", methods=["POST"])
def clear_memory():
    """Clear conversation working memory."""
    global brain
    if brain is not None:
        brain.working_memory.clear()
    return jsonify({"status": "ok", "message": "Conversation memory cleared"})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Send a message to the brain and get a response."""
    global brain
    if brain is None:
        return jsonify({"status": "error", "message": "Brain not initialized"}), 400

    data = request.json
    user_input = data.get("message", "")

    if not user_input.strip():
        return jsonify({"status": "error", "message": "Empty message"}), 400

    try:
        result = brain.run(user_input)
        return jsonify({
            "status": "ok",
            "response": result["final_response"],
            "agent_outputs": result["agent_outputs"],
            "persona_active": current_config["persona_active"],
            "persona_name": current_config["persona_name"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current brain configuration."""
    return jsonify(current_config)


def run_server(host="0.0.0.0", port=5001, debug=True):
    print(f"\n🧠 Brain System Web UI running at http://localhost:{port}")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
