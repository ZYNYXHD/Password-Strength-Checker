from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import math
import re
import webbrowser
import threading
import random
import string
import os
import sys

def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

app = Flask(__name__, template_folder=get_resource_path("templates"))
CORS(app)

# 🔢 Calculate entropy
def calculate_entropy(password):
    charset = 0
    if re.search(r"[a-z]", password):
        charset += 26
    if re.search(r"[A-Z]", password):
        charset += 26
    if re.search(r"[0-9]", password):
        charset += 10
    if re.search(r"[!@#$%^&*()]", password):
        charset += 32

    if charset == 0:
        return 0

    return len(password) * math.log2(charset)


# 🏠 Home route → serves your UI
@app.route('/')
def home():
    return render_template("index.html")   # put index.html in /templates


# 🔍 Detect weak patterns
def detect_patterns(password):
    issues = []

    if "123" in password:
        issues.append("Contains sequential numbers")

    if "password" in password.lower():
        issues.append("Contains common word 'password'")

    if password.lower() in ["qwerty", "abc123"]:
        issues.append("Common weak password")

    if len(set(password)) < len(password) / 2:
        issues.append("Too many repeated characters")

    if password.islower() or password.isupper():
        issues.append("Lacks character variety")

    return issues


def generate_suggestion(password):
    """Builds a stronger version of the provided password."""
    if not password:
        # If no password provided, generate a completely random strong one
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return ''.join(random.choice(chars) for _ in range(16))

    suggestion = list(password)
    
    # Ensure character variety by adding missing types
    if not re.search(r"[a-z]", password):
        suggestion.append(random.choice(string.ascii_lowercase))
    if not re.search(r"[A-Z]", password):
        suggestion.append(random.choice(string.ascii_uppercase))
    if not re.search(r"[0-9]", password):
        suggestion.append(random.choice(string.digits))
    if not re.search(r"[!@#$%^&*()]", password):
        suggestion.append(random.choice("!@#$%^&*()"))

    # Extend length to ensure high entropy (aiming for at least 14 characters)
    while len(suggestion) < 14:
        suggestion.append(random.choice(string.ascii_letters + string.digits + "!@#$%^&*()"))
    
    return "".join(suggestion)


# 🔐 Check password API
@app.route('/check', methods=['POST'])
def check():
    data = request.json

    password = data.get("password", "")
    if not password:
        return jsonify({"strength": "N/A", "entropy": 0, "issues": ["Please enter a password"], "suggestion": generate_suggestion("")})

    entropy = calculate_entropy(password)
    issues = detect_patterns(password)

    # 💡 Better strength logic
    if entropy < 35:
        strength = "Weak"
    elif entropy < 60:
        strength = "Medium"
    elif entropy < 80 or issues:
        strength = "Moderate"
    else:
        strength = "Strong"

    # Generate a suggestion if the password isn't strong yet
    suggestion = generate_suggestion(password) if strength != "Strong" else None

    return jsonify({
        "strength": strength,
        "entropy": round(entropy, 2),
        "issues": issues,
        "suggestion": suggestion
    })


# 🌐 Auto open browser (makes it feel like app)
def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


# ▶️ Run server
if __name__ == '__main__':
    threading.Timer(1, open_browser).start()
    app.run(host='127.0.0.1', port=5000, debug=False)