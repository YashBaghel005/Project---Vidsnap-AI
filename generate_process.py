import os
import requests
import subprocess
import shutil
from mutagen.mp3 import MP3
from murf import Murf
import time

# -------------------------------
# TEXT → AUDIO (MURF)
# -------------------------------
def text_to_audio(folder):
    import chardet  # pip install chardet first if not installed
    print("Processing folder:", folder)
    client = Murf(api_key="ap2_c450009b-e06d-4692-ad20-2b0226f37191")

    folder_path = os.path.join("user_uploads", folder)
    file_path = os.path.join(folder_path, "description")

    if not os.path.exists(file_path):
        print("❌ Missing description.txt in:", folder_path)
        return

    # ✅ Auto-detect encoding
    with open(file_path, "rb") as raw_file:
        raw_data = raw_file.read()
        detected = chardet.detect(raw_data)
        encoding = detected.get("encoding", "utf-8")

    # ✅ Read file using detected encoding (fallback to utf-8 if fails)
    try:
        text_content = raw_data.decode(encoding).strip()
    except Exception:
        text_content = raw_data.decode("utf-8", errors="replace").strip()

    # ✅ Continue as normal
    res = client.text_to_speech.generate(
        text=text_content,
        voice_id="en-IN-alia",
        format="MP3"
    )

    audio_url = None
    if hasattr(res, "audio_file"):
        audio_url = res.audio_file
    elif isinstance(res, str):
        audio_url = res
    elif isinstance(res, dict) and "encodedAudio" in res:
        import base64
        audio_bytes = base64.b64decode(res["encodedAudio"])
        output_file = os.path.join(folder_path, "description.mp3")
        with open(output_file, "wb") as audio_file:
            audio_file.write(audio_bytes)
        print("✅ Audio saved at:", output_file)
        return
    else:
        raise RuntimeError(f"Unexpected response from Murf: {res}")

    if audio_url:
        print("Downloading from URL:", audio_url)
        r = requests.get(audio_url)
        r.raise_for_status()
        output_file = os.path.join(folder_path, "description.mp3")
        with open(output_file, "wb") as audio_file:
            audio_file.write(r.content)
        print("✅ Audio saved at:", output_file)



# -------------------------------
# CREATE VIDEO REEL
# -------------------------------
def create_reel(folder):
    print("🎬 Creating reel for:", folder)

    folder_path = os.path.join("user_uploads", folder)
    static_folder = "static/reels"
    os.makedirs(static_folder, exist_ok=True)

    audio_path = os.path.join(folder_path, "description.mp3")
    if not os.path.exists(audio_path):
        print("❌ Missing audio file:", audio_path)
        return

    output_video = os.path.join(static_folder, f"{folder}.mp4")

    # Collect images
    images = sorted(
        [f for f in os.listdir(folder_path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    )

    if not images:
        print("❌ No images found in folder:", folder_path)
        return

    # ✅ Calculate audio duration
    audio = MP3(audio_path)
    audio_duration = audio.info.length
    print(f"🎵 Audio duration: {audio_duration:.2f} seconds")

    # ✅ Calculate per-image duration
    image_duration = audio_duration / len(images)
    print(f"🖼️ Each image duration: {image_duration:.2f} seconds")

    # ✅ Prepare temporary folder for FFmpeg
    tmp_dir = os.path.join(folder_path, "tmp_seq")
    os.makedirs(tmp_dir, exist_ok=True)

    # Copy and rename images sequentially
    for i, img in enumerate(images):
        src = os.path.join(folder_path, img)
        dst = os.path.join(tmp_dir, f"img{i:03d}.jpg")
        shutil.copy2(src, dst)

    # ✅ Create FFmpeg concat input.txt
    input_txt_path = os.path.join(tmp_dir, "input.txt")
    with open(input_txt_path, "w", encoding="utf-8") as f:
        for i in range(len(images)):
            f.write(f"file 'img{i:03d}.jpg'\n")
            f.write(f"duration {image_duration}\n")
        # 👇 Keep last image a bit longer so video ends smoothly
        f.write(f"file 'img{len(images)-1:03d}.jpg'\n")

    # ✅ FFmpeg command for synced video
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", input_txt_path,
        "-i", audio_path,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_video,
    ]

    print("▶️ Running FFmpeg for synced video...")
    try:
        subprocess.run(cmd, check=True)
        print(f"✅ Reel created successfully: {output_video}")
    except subprocess.CalledProcessError as e:
        print("❌ FFmpeg failed:", e)
    finally:
        # Cleanup temporary files
        shutil.rmtree(tmp_dir, ignore_errors=True)


# -------------------------------
# MAIN EXECUTION
# -------------------------------
if __name__ == "__main__":
    while(1):
        print("processing queue")
        done_file = "done.txt"
        if not os.path.exists(done_file):
            open(done_file, "w").close()

        with open(done_file, "r") as f:
            done_folders = [line.strip() for line in f.readlines() if line.strip()]

        folders = os.listdir("user_uploads")
        print(folders, done_folders)

        for folder in folders:
            if folder not in done_folders:
                text_to_audio(folder)
                create_reel(folder)

                with open(done_file, "a") as f:
                    f.write(folder + "\n")
        time.sleep(5)
