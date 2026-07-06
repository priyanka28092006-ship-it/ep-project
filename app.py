# app.py

from flask import Flask, request, jsonify, render_template
from logic import register_key, authenticate_key

app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["POST"])
def register():

    try:
        location = request.form.get("location", "").strip()

        if location == "":
            return jsonify({
                "status": "error",
                "message": "Location required"
            })

        result = register_key(location)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })


@app.route("/authenticate", methods=["POST"])
def authenticate():

    try:
        location = request.form.get("location", "").strip()

        if location == "":
            return jsonify({
                "status": "error",
                "message": "Location required"
            })

        result = authenticate_key(location)

        return jsonify(result)

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })


if __name__ == "__main__":
    app.run(debug=True)