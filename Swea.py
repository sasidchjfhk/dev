
from gevent import monkey
monkey.patch_all()
from src.init import init_devika
init_devika()


from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from src.socket_instance import socketio, emit_agent
import os
import logging
from threading import Thread
import tiktoken

from src.apis.project import project_bp
from src.config import Config
from src.logger import Logger, route_logger
from src.project import ProjectManager
from src.state import AgentState
from src.agents import Agent
from src.llm import LLM


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": # Change the origin to your frontend URL
                             [
                                 "https://localhost:3000",
                                 "http://localhost:3000",
                                 ]}}) 
app.register_blueprint(project_bp)
socketio.init_app(app)


log = logging.getLogger("werkzeug")
log.disabled = True


TIKTOKEN_ENC = tiktoken.get_encoding("cl100k_base")

os.environ["TOKENIZERS_PARALLELISM"] = "false"

manager = ProjectManager()
AgentState = AgentState()
config = Config()
logger = Logger()


# initial socket
@socketio.on('socket_connect')
def test_connect(data):
    print("Socket connected :: ", data)
    emit_agent("socket_response", {"data": "Server Connected"})


@app.route("/api/data", methods=["GET"])
@route_logger(logger)
def data():
    project = manager.get_project_list()
    models = LLM().list_models()
    search_engines = ["Bing", "Google", "DuckDuckGo"]
    return jsonify({"projects": project, "models": models, "search_engines": search_engines})


@app.route("/api/messages", methods=["POST"])
def get_messages():
    import logging
    from src.llm.llm import LLM
    data = request.json
    logging.info(f"[DEBUG] /api/messages received data: {data}")
    project_name = data.get("project_name")
    user_message = data.get("message")
    base_model = data.get("base_model", "gpt-4o-mini")
    search_engine = data.get("search_engine", "google")

    if not project_name or not user_message:
        logging.error("[ERROR] project_name or message missing in request data")
        return jsonify({"error": "project_name and message are required"}), 400

    # Save user message
    manager.add_message_from_user(project_name, user_message)

    # Generate AI response using LLM
    try:
        llm = LLM(model_id=base_model)
        ai_response = llm.inference(user_message, project_name)
    except Exception as e:
        logging.error(f"[ERROR] LLM inference failed: {e}")
        ai_response = "[AI Error] Could not generate a response."

    # Save AI message
    from datetime import datetime
    ai_message = {
        "from_devika": True,
        "message": ai_response,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    manager.add_message_to_project(project_name, ai_message)

    messages = manager.get_messages(project_name) or []
    logging.info(f"[DEBUG] /api/messages returning messages: {messages}")
    return jsonify({"messages": messages})


# Main socket
@socketio.on('user-message')
def handle_message(data):
    logger.info(f"User message: {data}")
    message = data.get('message')
    base_model = data.get('base_model')
    project_name = data.get('project_name')
    search_engine = data.get('search_engine')
    
    # Set default search engine if not provided
    if not search_engine or search_engine.lower() == 'select search engine':
        from src.config.defaults import DEFAULT_SEARCH_ENGINE
        search_engine = DEFAULT_SEARCH_ENGINE
    
    logger.info(f"Using search engine: {search_engine}")
    agent = Agent(base_model=base_model, search_engine=search_engine.lower())

    state = AgentState.get_latest_state(project_name)
    if not state:
        thread = Thread(target=lambda: agent.execute(message, project_name))
        thread.start()
    else:
        if AgentState.is_agent_completed(project_name):
            thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
            thread.start()
        else:
            emit_agent("info", {"type": "warning", "message": "previous agent doesn't completed it's task."})
            last_state = AgentState.get_latest_state(project_name)
            if last_state["agent_is_active"] or not last_state["completed"]:
                thread = Thread(target=lambda: agent.execute(message, project_name))
                thread.start()
            else:
                thread = Thread(target=lambda: agent.subsequent_execute(message, project_name))
                thread.start()

@app.route("/api/is-agent-active", methods=["POST"])
@route_logger(logger)
def is_agent_active():
    data = request.json
    project_name = data.get("project_name")
    is_active = AgentState.is_agent_active(project_name)
    return jsonify({"is_active": is_active})


@app.route("/api/get-agent-state", methods=["POST"])
@route_logger(logger)
def get_agent_state():
    data = request.json
    project_name = data.get("project_name")
    agent_state = AgentState.get_latest_state(project_name)
    return jsonify({"state": agent_state})


@app.route("/api/get-browser-snapshot", methods=["GET"])
@route_logger(logger)
def browser_snapshot():
    snapshot_path = request.args.get("snapshot_path")
    return send_file(snapshot_path, as_attachment=True)


@app.route("/api/get-browser-session", methods=["GET"])
@route_logger(logger)
def get_browser_session():
    project_name = request.args.get("project_name")
    agent_state = AgentState.get_latest_state(project_name)
    if not agent_state:
        return jsonify({"session": None})
    else:
        browser_session = agent_state["browser_session"]
        return jsonify({"session": browser_session})


@app.route("/api/get-terminal-session", methods=["GET"])
@route_logger(logger)
def get_terminal_session():
    project_name = request.args.get("project_name")
    agent_state = AgentState.get_latest_state(project_name)
    if not agent_state:
        return jsonify({"terminal_state": None})
    else:
        terminal_state = agent_state["terminal_session"]
        return jsonify({"terminal_state": terminal_state})


@app.route("/api/run-code", methods=["POST"])
@route_logger(logger)
def run_code():
    data = request.json
    project_name = data.get("project_name")
    code = data.get("code")
    # TODO: Implement code execution logic
    return jsonify({"message": "Code execution started"})


@app.route("/api/calculate-tokens", methods=["POST"])
@route_logger(logger)
def calculate_tokens():
    data = request.json
    prompt = data.get("prompt")
    tokens = len(TIKTOKEN_ENC.encode(prompt))
    return jsonify({"token_usage": tokens})


@app.route("/api/token-usage", methods=["GET"])
@route_logger(logger)
def token_usage():
    project_name = request.args.get("project_name")
    token_count = AgentState.get_latest_token_usage(project_name)
    return jsonify({"token_usage": token_count})


@app.route("/api/logs", methods=["GET"])
def real_time_logs():
    log_file = logger.read_log_file()
    return jsonify({"logs": log_file})


@app.route("/api/settings", methods=["POST"])
@route_logger(logger)
def set_settings():
    data = request.json
    config.update_config(data)
    return jsonify({"message": "Settings updated"})


@app.route("/api/settings", methods=["GET"])
@route_logger(logger)
def get_settings():
    configs = config.get_config()
    return jsonify({"settings": configs})


@app.route("/api/status", methods=["GET"])
@route_logger(logger)
def status():
    return jsonify({"status": "server is running!"})

if __name__ == "__main__":
    logger.info("Swea is up and running!")
    socketio.run(app, debug=False, port=1337, host="0.0.0.0")
