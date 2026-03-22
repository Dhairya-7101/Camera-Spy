print("Use this command after ssh -R 80:localhost:8080 nokey@localhost.run  to make it public ")

# =========================
# PRO CAMERA CONTROL SYSTEM
# =========================

from flask import Flask, request, Response, redirect, session
import os, time, base64

app = Flask(__name__)
app.secret_key = "pro_secret"

USERNAME = "admin"
PASSWORD = "1234"

latest_frame = None
logs = []
last_seen = None

if not os.path.exists("captures"):
    os.makedirs("captures")

# =========================
# LOGIN
# =========================

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["login"] = True
            logs.append("Admin logged in")
            return redirect("/dashboard")

    return """
    <h2>🔐 Admin Login</h2>
    <form method="POST">
        <input name="username"><br><br>
        <input name="password" type="password"><br><br>
        <button>Login</button>
    </form>
    """

# =========================
# DASHBOARD
# =========================

@app.route("/dashboard")
def dashboard():
    if not session.get("login"):
        return redirect("/")

    status = "🟢 Online" if last_seen and time.time() - last_seen < 3 else "🔴 Offline"

    return f"""
    <h2>📡 Control Panel</h2>

    <p>Status: {status}</p>

    <img src="/frame" width="400"><br><br>

    <a href="/capture"><button>📸 Capture</button></a>
    <a href="/gallery"><button>🖼️ Gallery</button></a>
    <a href="/logs"><button>📜 Logs</button></a>
    <a href="/logout"><button>🚪 Logout</button></a>
    """

# =========================
# CAMERA (PHONE)
# =========================

@app.route("/camera")
def camera():
    return """
    <h2>📱 Camera Sender</h2>
    <video id="video" autoplay playsinline width="300"></video>
    <canvas id="canvas" style="display:none;"></canvas>

    <script>
    let video = document.getElementById("video");

    navigator.mediaDevices.getUserMedia({ video: true })
    .then(stream => {
        video.srcObject = stream;
    });

    setInterval(() => {
        let canvas = document.getElementById("canvas");
        let ctx = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        ctx.drawImage(video, 0, 0);

        let data = canvas.toDataURL("image/jpeg");

        fetch("/upload", {
            method: "POST",
            body: data
        });
    }, 150);
    </script>
    """

# =========================
# RECEIVE FRAME
# =========================

@app.route("/upload", methods=["POST"])
def upload():
    global latest_frame, last_seen

    data = request.data.decode()

    if "base64," in data:
        img = data.split("base64,")[1]
        latest_frame = base64.b64decode(img)

    last_seen = time.time()
    return "OK"

# =========================
# STREAM
# =========================

@app.route("/frame")
def frame():
    if latest_frame:
        return Response(latest_frame, mimetype='image/jpeg')
    return ""

# =========================
# CAPTURE
# =========================

@app.route("/capture")
def capture():
    if latest_frame:
        filename = f"captures/img_{int(time.time())}.jpg"
        with open(filename, "wb") as f:
            f.write(latest_frame)
        logs.append(f"Captured {filename}")
    return redirect("/dashboard")

# =========================
# GALLERY
# =========================

@app.route("/gallery")
def gallery():
    files = os.listdir("captures")
    html = "<h2>🖼️ Gallery</h2>"

    for f in files[::-1]:
        html += f'<img src="/img/{f}" width="200"><br>'

    html += '<br><a href="/dashboard">Back</a>'
    return html

@app.route("/img/<name>")
def img(name):
    return open(f"captures/{name}", "rb").read()

# =========================
# LOGS
# =========================

@app.route("/logs")
def show_logs():
    return "<br>".join(logs)

# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# =========================
# RUN
# =========================

if __name__ == "__main__":
    app.run(host="localhost", port=8080)
