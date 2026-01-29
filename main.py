from flask import Flask, request, jsonify, render_template_string
import httpx
import time

app = Flask(__name__)
BASE_URL = "https://ai-song-generate.vercel.app"

# ---------------- Sync song generation ----------------
def generate_song_sync(prompt, lyrics, timeout=60):
    with httpx.Client(timeout=30.0) as client:
        try:
            # Step 1: Start generation
            response = client.post(f"{BASE_URL}/generate", json={
                "prompt": prompt,
                "lyrics": lyrics
            })
            data = response.json()

            if not data.get("success"):
                return {"success": False, "error": data.get("error", "Failed to start generation")}

            conversation_id = data.get("conversation_id")
            if data.get("completed"):
                return {
                    "success": True,
                    "completed": True,
                    "music_url": data.get("music_url"),
                    "short_music_url": data.get("short_music_url"),
                    "thumbnail_url": data.get("thumbnail_url")
                }

            # Step 2: Poll slower (0.5s)
            start_time = time.time()
            while time.time() - start_time < timeout:
                status_resp = client.post(f"{BASE_URL}/check_status", json={
                    "conversation_id": conversation_id
                })
                status_data = status_resp.json()

                if status_data.get("completed"):
                    return {
                        "success": True,
                        "completed": True,
                        "music_url": status_data.get("music_url"),
                        "short_music_url": status_data.get("short_music_url"),
                        "thumbnail_url": status_data.get("thumbnail_url")
                    }

                time.sleep(0.5)

            return {"success": False, "error": "Song generation timed out."}

        except Exception as e:
            return {"success": False, "error": str(e)}

# ---------------- Routes ----------------
@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    prompt = data.get("prompt", "")
    lyrics = data.get("lyrics", "")

    if not prompt:
        return jsonify({"success": False, "error": "Prompt is required."})

    result = generate_song_sync(prompt, lyrics)
    return jsonify(result)

@app.route("/check_status", methods=["POST"])
def check_status():
    # For demo only
    data = request.json
    conversation_id = data.get("conversation_id", "")
    if not conversation_id:
        return jsonify({"success": False, "error": "conversation_id is required."})

    return jsonify({"success": False, "error": "Status check not implemented in demo."})

# ---------------- HTML Template ----------------
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>JC MUSIC AI</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" />
<style>
  body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    margin: 0;
    padding: 30px 20px;
    min-height: 100vh;
    display: flex;
    justify-content: center;
    align-items: flex-start;
  }
  .container {
    max-width: 700px;
    width: 100%;
    background: #fff;
    color: #333;
    border-radius: 20px;
    padding: 40px 30px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.20);
  }
  .header {
    text-align: center;
    margin-bottom: 30px;
  }
  .header h1 {
    font-size: 3rem;
    margin-bottom: 0.25rem;
    color: #764ba2;
  }
  .header p {
    font-size: 1.2rem;
    color: #555;
  }
  form {
    display: flex;
    flex-direction: column;
  }
  input, textarea {
    width: 100%;
    padding: 14px 16px;
    margin-bottom: 24px;
    border-radius: 12px;
    border: 1.5px solid #ccc;
    font-size: 1rem;
    transition: border-color 0.3s ease;
  }
  input:focus, textarea:focus {
    border-color: #667eea;
    outline: none;
  }
  textarea {
    min-height: 120px;
    resize: vertical;
  }
  button.generate-btn {
    padding: 16px;
    background: linear-gradient(135deg, #667eea, #764ba2);
    border: none;
    border-radius: 12px;
    color: white;
    font-weight: 600;
    font-size: 1.1rem;
    cursor: pointer;
    transition: background 0.3s ease;
  }
  button.generate-btn:hover {
    background: linear-gradient(135deg, #5a6fcf, #5b3d87);
  }
  #statusMessage {
    margin: 15px 0 30px;
    padding: 14px 20px;
    border-radius: 12px;
    font-weight: 600;
    display: none;
  }
  .status-loading {
    background: #cde3fc;
    color: #1e40af;
  }
  .status-success {
    background: #d0f0d8;
    color: #2f855a;
  }
  .status-error {
    background: #fbdada;
    color: #c53030;
  }
  .result-container {
    text-align: center;
    display: none;
  }
  img.thumbnail {
    max-width: 250px;
    border-radius: 16px;
    box-shadow: 0 8px 16px rgb(118 75 162 / 0.35);
    margin-bottom: 20px;
    user-select: none;
  }
  h3#songTitle {
    font-size: 1.8rem;
    color: #764ba2;
    margin-bottom: 10px;
  }
  p#songStatus {
    font-size: 1.1rem;
    margin-bottom: 20px;
    color: #555;
  }
  a#songLink {
    display: inline-block;
    padding: 12px 28px;
    font-weight: 600;
    font-size: 1.1rem;
    background: #764ba2;
    color: white;
    border-radius: 16px;
    text-decoration: none;
    box-shadow: 0 4px 12px rgba(118, 75, 162, 0.5);
    transition: background 0.3s ease;
  }
  a#songLink:hover {
    background: #5b3d87;
  }
</style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1><i class="fas fa-music"></i> ABBAS MUSIC AI</h1>
      <p>Transform your ideas into music with AI</p>
    </div>
    <form id="songForm" autocomplete="off">
      <input type="text" id="prompt" placeholder="Song theme/prompt..." required />
      <textarea id="lyrics" placeholder="Enter lyrics..."></textarea>
      <button type="submit" class="generate-btn">Generate Song</button>
    </form>
    <div id="statusMessage" class="status-message"></div>
    <div class="result-container" id="resultContainer">
      <img id="thumbnail" class="thumbnail" src="" alt="Thumbnail" />
      <h3 id="songTitle"></h3>
      <p id="songStatus"></p>
      <a id="songLink" href="" target="_blank" rel="noopener">▶ Play Song</a>
    </div>
  </div>
<script>
const form = document.getElementById('songForm');
const statusMessage = document.getElementById('statusMessage');
const resultContainer = document.getElementById('resultContainer');
const thumbnail = document.getElementById('thumbnail');
const songTitle = document.getElementById('songTitle');
const songStatus = document.getElementById('songStatus');
const songLink = document.getElementById('songLink');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    statusMessage.style.display = 'block';
    statusMessage.className = 'status-message status-loading';
    statusMessage.innerText = 'Generating song...';
    resultContainer.style.display = 'none';

    const prompt = document.getElementById('prompt').value.trim();
    const lyrics = document.getElementById('lyrics').value.trim();

    if (!prompt) {
      statusMessage.className = 'status-message status-error';
      statusMessage.innerText = 'Please enter the song prompt.';
      return;
    }

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt, lyrics})
        });
        const result = await response.json();

        if (result.success) {
            thumbnail.src = result.thumbnail_url || '';
            songTitle.innerText = 'Your AI Song';
            songStatus.innerText = 'Song ready!';
            songLink.href = result.music_url || '#';
            songLink.innerText = '▶ Play Song';
            resultContainer.style.display = 'block';
            statusMessage.className = 'status-message status-success';
            statusMessage.innerText = 'Song generated successfully!';
        } else {
            throw new Error(result.error || "Unknown error");
        }
    } catch (err) {
        statusMessage.className = 'status-message status-error';
        statusMessage.innerText = err.message || "Failed to generate song.";
    }
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=False)
