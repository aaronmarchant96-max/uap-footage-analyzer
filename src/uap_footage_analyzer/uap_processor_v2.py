import cv2
import os
import json
from datetime import datetime

# =========================
# PromptHound UAP Processor
# =========================

# --- Paths ---
FOOTAGE_DIR = os.path.expanduser("~/uap_footage")

OUTPUT_DIR = os.path.expanduser("~/uap_results")

KEYFRAMES_DIR = os.path.join(
    OUTPUT_DIR,
    "keyframes"
)

LOG_FILE = os.path.join(
    OUTPUT_DIR,
    "anomalies.jsonl"
)

REPORT_FILE = os.path.join(
    OUTPUT_DIR,
    "summary.txt"
)

# --- Detection Settings ---
THRESHOLD = 300000
FRAME_SKIP = 10
MIN_SECONDS_BETWEEN_EVENTS = 5

# --- Setup ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

os.makedirs(
    KEYFRAMES_DIR,
    exist_ok=True
)

# Clear previous logs
open(LOG_FILE, "w").close()

# Remove old keyframes
for f in os.listdir(KEYFRAMES_DIR):
    try:
        os.remove(
            os.path.join(KEYFRAMES_DIR, f)
        )
    except:
        pass

video_files = sorted([
    f for f in os.listdir(FOOTAGE_DIR)
    if f.lower().endswith((
        ".mp4",
        ".mov",
        ".avi",
        ".mkv"
    ))
])

print("\n==============================")
print(" UAP Batch Processor")
print(" PromptHound")
print("==============================")

print(
    f"Started: "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

print(f"Files: {len(video_files)}")

print(f"Threshold: {THRESHOLD}")

print(
    f"Frame Skip: every "
    f"{FRAME_SKIP} frames"
)

print(
    f"Cooldown: "
    f"{MIN_SECONDS_BETWEEN_EVENTS}s"
)

print("==============================\n")

total_anomalies = 0
summary_lines = []

# =========================
# Main Processing Loop
# =========================

for video_file in video_files:

    video_path = os.path.join(
        FOOTAGE_DIR,
        video_file
    )

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():

        print(
            f"[SKIP] "
            f"Could not open "
            f"{video_file}"
        )

        continue

    fps = cap.get(
        cv2.CAP_PROP_FPS
    ) or 30

    frame_total = cap.get(
        cv2.CAP_PROP_FRAME_COUNT
    ) or 0

    duration = (
        frame_total / fps
        if fps else 0
    )

    print(
        f"[PROCESSING] "
        f"{video_file} "
        f"({duration:.1f}s)"
    )

    ret, prev_frame = cap.read()

    if not ret:

        print(
            "[SKIP] "
            "Could not read "
            "first frame"
        )

        cap.release()
        continue

    file_anomalies = []
    frame_num = 1

    while True:

        ret, frame = cap.read()

        if not ret:
            break

        frame_num += 1

        # Frame skipping
        if (
            frame_num %
            FRAME_SKIP
        ) != 0:

            prev_frame = frame
            continue

        # Frame difference
        diff = cv2.absdiff(
            prev_frame,
            frame
        )

        gray = cv2.cvtColor(
            diff,
            cv2.COLOR_BGR2GRAY
        )

        blur = cv2.GaussianBlur(
            gray,
            (5, 5),
            0
        )

        _, thresh = cv2.threshold(
            blur,
            20,
            255,
            cv2.THRESH_BINARY
        )

        score = cv2.countNonZero(
            thresh
        )

        if score > THRESHOLD:

            timestamp = (
                cap.get(
                    cv2.CAP_PROP_POS_MSEC
                ) / 1000
            )

            # Cooldown filter
            if file_anomalies:

                last_timestamp = (
                    file_anomalies[-1][0]
                )

                if (
                    timestamp -
                    last_timestamp
                ) < MIN_SECONDS_BETWEEN_EVENTS:

                    prev_frame = frame
                    continue

            frame_id = (
                f"{os.path.splitext(video_file)[0]}"
                f"_t{timestamp:.2f}"
                f"_s{score}"
            )

            keyframe_path = os.path.join(
                KEYFRAMES_DIR,
                f"{frame_id}.png"
            )

            cv2.imwrite(
                keyframe_path,
                frame
            )

            entry = {
                "file": video_file,
                "timestamp_sec": round(
                    timestamp,
                    2
                ),
                "frame": frame_num,
                "score": int(score),
                "threshold": THRESHOLD,
                "frame_skip": FRAME_SKIP,
                "cooldown_sec": MIN_SECONDS_BETWEEN_EVENTS,
                "keyframe": keyframe_path,
                "processed_at": datetime.now().isoformat()
            }

            with open(
                LOG_FILE,
                "a"
            ) as log:

                log.write(
                    json.dumps(entry)
                    + "\n"
                )

            file_anomalies.append(
                (timestamp, score)
            )

            total_anomalies += 1

        prev_frame = frame

    cap.release()

    if file_anomalies:

        top = max(
            file_anomalies,
            key=lambda x: x[1]
        )

        line = (
            f"{video_file}: "
            f"{len(file_anomalies)} anomalies | "
            f"top spike: "
            f"{top[1]} "
            f"at "
            f"{top[0]:.2f}s"
        )

        print(f"[FOUND] {line}")

    else:

        line = (
            f"{video_file}: "
            f"no anomalies detected"
        )

        print(f"[CLEAN] {video_file}")

    summary_lines.append(line)

# =========================
# Summary Report
# =========================

with open(REPORT_FILE, "w") as r:

    r.write(
        "UAP FOOTAGE ANALYSIS "
        "— PromptHound\n"
    )

    r.write(
        f"Date: "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    r.write(
        f"Files processed: "
        f"{len(video_files)}\n"
    )

    r.write(
        f"Total anomalies flagged: "
        f"{total_anomalies}\n"
    )

    r.write(
        f"Threshold used: "
        f"{THRESHOLD}\n"
    )

    r.write(
        f"Frame skip: "
        f"{FRAME_SKIP}\n"
    )

    r.write(
        f"Cooldown: "
        f"{MIN_SECONDS_BETWEEN_EVENTS}s\n\n"
    )

    r.write(
        "Per-file results:\n"
    )

    for line in summary_lines:
        r.write(line + "\n")

print("\n==============================")
print(
    f"DONE — "
    f"{total_anomalies} anomalies "
    f"across "
    f"{len(video_files)} files"
)

print(
    f"Keyframes: "
    f"{KEYFRAMES_DIR}"
)

print(
    f"JSONL: "
    f"{LOG_FILE}"
)

print(
    f"Summary: "
    f"{REPORT_FILE}"
)

print("==============================\n")
