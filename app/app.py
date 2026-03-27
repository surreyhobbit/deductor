import os
from datetime import datetime
from flask import Flask, redirect, render_template, url_for
from db import add_deduction, ensure_month, get_history, get_summary, init_db

app = Flask(__name__)


@app.template_filter("format_dt")
def format_dt(value: str) -> str:
    """Convert ISO UTC timestamp to UK-style: '27 Mar 2025, 14:03'"""
    try:
        dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return dt.strftime("%-d %b %Y, %H:%M")
    except Exception:
        return value


def now():
    return datetime.now()


@app.route("/")
def index():
    today = now()
    summaries = get_summary(today.year, today.month)
    return render_template(
        "index.html",
        summaries=summaries,
        month_label=today.strftime("%B %Y"),
    )


@app.route("/deduct/<int:child_id>", methods=["POST"])
def deduct(child_id):
    today = now()
    ensure_month(child_id, today.year, today.month)
    add_deduction(child_id, today.year, today.month)
    return redirect(url_for("index"))


@app.route("/history")
def history():
    rows = get_history()
    return render_template("history.html", rows=rows)


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
