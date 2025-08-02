from flask import Flask, render_template, request
import pandas as pd
import os
from utils.sla_logic import process_sla_data
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        uploaded_file = request.files["file"]
        date_filter = request.form.get("filter_date")
        if uploaded_file and date_filter:
            filename = secure_filename(uploaded_file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            uploaded_file.save(file_path)
            try:
                # Removed deprecated `error_bad_lines` — replaced with on_bad_lines
                df = pd.read_csv(file_path, encoding='utf-8', engine='python', on_bad_lines='skip')
            except Exception as e:
                return f"<h3>Error reading CSV file: {e}</h3>"
            result = process_sla_data(df, date_filter)
            return render_template("report.html", tables=[result.to_html(classes="data", index=False)], date=date_filter)
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
