from flask import Flask, render_template, request, jsonify
from agent import run_agent

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json["message"]
    response = run_agent(user_input)
    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(debug=True)