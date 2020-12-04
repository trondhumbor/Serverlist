from flask import render_template
from flask import current_app as app

from . import cache

@app.route("/")
def index():
    return render_template("index.html", servers=cache.get("servers"), timestamp=cache.get("timestamp"))
