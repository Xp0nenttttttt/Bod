from flask import Flask, request, render_template, send_file, Response
import requests
from io import BytesIO
import re

app = Flask(__name__)

k_tag_map = [
    ("kCEK", "static", 4),
    ("k1", "1"),
    ("k23", "15"),
    ("k2", "2"),
    ("k4", "4"),
    ("k3", "3"),
    ("k21", "static", 3),
    ("k16", "5"),
    ("k17", "13"),
    ("k80", "46"),
    ("k81", "47"),
    ("k64", "37"),
    ("k42", "30"),
    ("k45", "35"),
    ("k50", "static", 45),
    ("k48", "45")
]

def parse_level_data(data: str):
    pairs = {}
    parts = data.strip().split(":")
    for i in range(0, len(parts) - 1, 2):
        key = parts[i]
        value = parts[i + 1].split(";")[0]
        pairs[key] = value
    return pairs

def make_gmd(level_id, pairs):
    xml = ['<?xml version="1.0"?><plist version="1.0" gjver="2.0"><dict>']
    for ktag, rawkey, *staticval in k_tag_map:
        if rawkey == "static":
            v = staticval[0]
        else:
            v = pairs.get(rawkey)
        if not v:
            continue
        tagtype = "s" if ktag in ("k2", "k3", "k4") else "i"
        xml.append(f'<k>{ktag}</k><{tagtype}>{v}</{tagtype}>')
    xml.append('</dict></plist>')
    return ''.join(xml)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["GET", "POST"])
def download():
    if request.method == "GET":
        return render_template("download.html")

    level_id = request.form.get("level_id")
    if not level_id:
        return Response("ID manquant", status=400)

    url = "http://www.boomlings.com/database/downloadGJLevel22.php"
    data = {"secret": "Wmfd2893gb7", "levelID": level_id}
    headers = {"User-Agent": "GeometryDash"}

    r = requests.post(url, data=data, headers=headers)
    print("Réponse brute GD :", r.text[:200])

    if r.text.strip() == "-1":
        return Response("Niveau introuvable", status=404)

    pairs = parse_level_data(r.text)
    gmd_content = make_gmd(level_id, pairs)

    level_name = pairs.get("2", f"level_{level_id}")
    safe_name = re.sub(r'[^a-zA-Z0-9_\- ]', "_", level_name)

    buf = BytesIO(gmd_content.encode("utf-8"))
    buf.seek(0)

    return send_file(
        buf,
        as_attachment=True,
        download_name=f"{level_id} - {safe_name}.gmd",
        mimetype="application/octet-stream"
    )


if __name__ == "__main__":
    app.run(debug=True)
