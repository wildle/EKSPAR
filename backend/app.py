from flask import Flask
from api.config_api import config_api
from flask_cors import CORS

app = Flask(__name__)
app.register_blueprint(config_api)
CORS(app) 

@app.route("/")
def home():
    return "Flask Backend läuft!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
 