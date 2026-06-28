"""
App web minima para exponer el Alura Agente.
Pensada para correr local (python app.py) y luego en una instancia de OCI Compute.
"""
import os
from flask import Flask, request, jsonify, render_template_string
from agent import build_agent, ask

app = Flask(__name__)
_agent = None  # se construye una sola vez, al recibir la primera request


def get_agent():
    global _agent
    if _agent is None:
        _agent = build_agent()
    return _agent


PAGE = """
<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>Alura Agente</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 16px; }
    textarea { width: 100%; height: 70px; font-size: 16px; }
    button { padding: 8px 20px; font-size: 16px; cursor: pointer; }
    .respuesta { margin-top: 20px; padding: 16px; background: #f4f4f4; border-radius: 8px; white-space: pre-wrap; }
  </style>
</head>
<body>
  <h1>🤖 Alura Agente</h1>
  <p>Hacé una pregunta sobre el documento cargado.</p>
  <form method="post" action="/preguntar">
    <textarea name="pregunta" placeholder="Ej: ¿Cuántos días de vacaciones tengo por año?"></textarea><br><br>
    <button type="submit">Preguntar</button>
  </form>
  {% if respuesta %}
    <div class="respuesta"><b>Pregunta:</b> {{ pregunta }}<br><br><b>Respuesta:</b> {{ respuesta }}</div>
  {% endif %}
</body>
</html>
"""


@app.route("/", methods=["GET"])
def home():
    return render_template_string(PAGE)


@app.route("/preguntar", methods=["POST"])
def preguntar():
    pregunta = request.form.get("pregunta", "").strip()
    if not pregunta:
        return render_template_string(PAGE)
    respuesta = ask(get_agent(), pregunta)
    return render_template_string(PAGE, pregunta=pregunta, respuesta=respuesta)


@app.route("/api/preguntar", methods=["POST"])
def api_preguntar():
    """Endpoint JSON: POST {"pregunta": "..."} -> {"respuesta": "..."}"""
    data = request.get_json(silent=True) or {}
    pregunta = data.get("pregunta", "").strip()
    if not pregunta:
        return jsonify({"error": "Falta el campo 'pregunta'"}), 400
    respuesta = ask(get_agent(), pregunta)
    return jsonify({"pregunta": pregunta, "respuesta": respuesta})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    # host 0.0.0.0 es necesario para que sea accesible desde fuera de la instancia OCI
    app.run(host="0.0.0.0", port=port)
