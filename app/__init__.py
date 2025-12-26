from flask import Flask

app = Flask(__name__)
app.secret_key = "eea_super_secret_key_2025"  # required for sessions

from app import routes
