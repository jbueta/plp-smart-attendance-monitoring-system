import cv2
import numpy as np
from datetime import datetime
import json
import re
import urllib.parse


# ─────────────────────────────────────────────
#  NOISE REDUCTION & IMAGE ENHANCEMENT
# ─────────────────────────────────────────────

def preprocess_for_qr(frame: np.ndarray) -> np.ndarray:
    """
    Multi-stage preprocessing pipeline to improve QR detection in noisy,
    low-light, blurry, or high-glare conditions.
    Returns a grayscale enhanced image.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 1. Denoise — fast Non-Local Means (good for camera sensor noise)
    denoised = cv2.fastNlMeansDenoising(gray, h=10, templateWindowSize=7, searchWindowSize=21)

    # 2. CLAHE — contrast-limited adaptive histogram equalization
    #    Boosts local contrast so dark/washed-out QR modules become crisp
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    enhanced = clahe.apply(denoised)

    # 3. Sharpening kernel — recovers edge detail lost to blur / compression
    kernel = np.array([[ 0, -1,  0],
                        [-1,  5, -1],
                        [ 0, -1,  0]], dtype=np.float32)
    sharpened = cv2.filter2D(enhanced, -1, kernel)

    # 4. Adaptive threshold — binarise for max QR contrast
    #    (detector internally converts anyway, but pre-binarising helps noisy frames)
    binary = cv2.adaptiveThreshold(
        sharpened, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    return binary


def try_detect(detector, frame: np.ndarray):
    """
    Try QR detection on multiple versions of the frame:
      1. Raw colour frame (fastest path)
      2. Preprocessed (denoised + enhanced) grayscale
      3. Preprocessed at 1.5× upscale (helps tiny / distant QRs)
    Returns (data, bbox, straight_qrcode) from the first successful attempt.
    """
    # Attempt 1 — original frame
    data, bbox, straight = detector.detectAndDecode(frame)
    if data:
        return data, bbox, straight

    # Attempt 2 — preprocessed grayscale
    processed = preprocess_for_qr(frame)
    data, bbox, straight = detector.detectAndDecode(processed)
    if data:
        return data, bbox, straight

    # Attempt 3 — upscaled preprocessed (for small/distant QR codes)
    h, w = processed.shape[:2]
    upscaled = cv2.resize(processed, (int(w * 1.5), int(h * 1.5)),
                          interpolation=cv2.INTER_CUBIC)
    data, bbox, straight = detector.detectAndDecode(upscaled)
    if data and bbox is not None:
        # Scale bbox coordinates back to original frame size
        bbox = (bbox / 1.5).astype(np.float32)
        return data, bbox, straight

    return "", None, None

# ─────────────────────────────────────────────
#  ID / QR DATA PARSERS
# ─────────────────────────────────────────────

def parse_vcard(data: str) -> dict:
    """Parse vCard 2.1 / 3.0 format."""
    fields = {}
    for line in data.splitlines():
        line = line.strip()
        if line.upper().startswith("FN:"):
            fields["Full Name"] = line[3:]
        elif line.upper().startswith("N:"):
            parts = line[2:].split(";")
            name_parts = [p for p in parts if p]
            fields["Name (Last, First)"] = ", ".join(name_parts)
        elif line.upper().startswith("TEL"):
            fields.setdefault("Phone", []).append(re.sub(r".*:", "", line))
        elif line.upper().startswith("EMAIL"):
            fields.setdefault("Email", []).append(re.sub(r".*:", "", line))
        elif line.upper().startswith("ORG:"):
            fields["Organization"] = line[4:]
        elif line.upper().startswith("TITLE:"):
            fields["Title"] = line[6:]
        elif line.upper().startswith("ADR"):
            fields["Address"] = re.sub(r".*:", "", line).replace(";", ", ").strip(", ")
        elif line.upper().startswith("BDAY:"):
            fields["Birthday"] = line[5:]
        elif line.upper().startswith("URL:"):
            fields["Website"] = line[4:]
        elif line.upper().startswith("NOTE:"):
            fields["Note"] = line[5:]
    return fields


def parse_mecard(data: str) -> dict:
    """Parse MECARD format (used by many Asian ID/business card QRs)."""
    fields = {}
    inner = re.sub(r"^MECARD:", "", data, flags=re.IGNORECASE).rstrip(";")
    for part in inner.split(";"):
        if ":" not in part:
            continue
        key, _, val = part.partition(":")
        key = key.strip().upper()
        val = val.strip()
        mapping = {
            "N": "Name", "TEL": "Phone", "EMAIL": "Email",
            "ADR": "Address", "BDAY": "Birthday", "URL": "Website",
            "NOTE": "Note", "NICKNAME": "Nickname",
        }
        if key in mapping:
            fields[mapping[key]] = val
    return fields


def parse_ph_national_id(data: str) -> dict:
    """
    Parse Philippine National ID (PhilSys) QR.
    Format varies — try JSON first, then pipe-delimited.
    """
    fields = {}
    # Attempt JSON
    try:
        obj = json.loads(data)
        label_map = {
            "PCN": "PhilSys Card Number (PCN)",
            "PSN": "PhilSys Number (PSN)",
            "lname": "Last Name", "fname": "First Name", "mname": "Middle Name",
            "suffix": "Suffix", "sex": "Sex", "dob": "Date of Birth",
            "pob": "Place of Birth", "address": "Address",
            "mobile": "Mobile Number", "email": "Email",
        }
        for k, v in obj.items():
            label = label_map.get(k, k)
            if v:
                fields[label] = v
        if fields:
            return fields
    except (json.JSONDecodeError, TypeError):
        pass

    # Pipe-delimited (some PhilSys QR versions)
    parts = data.split("|")
    if len(parts) >= 5:
        labels = ["PCN/PSN", "Last Name", "First Name", "Middle Name",
                  "Date of Birth", "Sex", "Address", "Mobile"]
        for i, label in enumerate(labels):
            if i < len(parts) and parts[i].strip():
                fields[label] = parts[i].strip()
        if fields:
            return fields

    return {}


def parse_url(data: str) -> dict:
    """Parse URL and extract components."""
    try:
        parsed = urllib.parse.urlparse(data)
        fields = {"Type": "URL / Web Link", "Full URL": data, "Domain": parsed.netloc}
        if parsed.path and parsed.path != "/":
            fields["Path"] = parsed.path
        if parsed.query:
            params = urllib.parse.parse_qs(parsed.query)
            for k, v in params.items():
                fields[f"Param: {k}"] = ", ".join(v)
        return fields
    except Exception:
        return {"Type": "URL", "URL": data}


def parse_wifi(data: str) -> dict:
    """Parse WIFI: QR format."""
    fields = {"Type": "Wi-Fi Credentials"}
    for part in re.findall(r'([A-Z]+):([^;]*)', data):
        key, val = part
        mapping = {"S": "SSID (Network Name)", "P": "Password",
                   "T": "Security Type", "H": "Hidden Network"}
        if key in mapping:
            fields[mapping[key]] = val or "(none)"
    return fields


def parse_geo(data: str) -> dict:
    """Parse geo: URI."""
    m = re.match(r"geo:([0-9.\-]+),([0-9.\-]+)", data, re.IGNORECASE)
    if m:
        return {
            "Type": "Geographic Location",
            "Latitude": m.group(1),
            "Longitude": m.group(2),
            "Maps Link": f"https://maps.google.com/?q={m.group(1)},{m.group(2)}",
        }
    return {}


def parse_email(data: str) -> dict:
    """Parse mailto: URI."""
    data = data[7:]  # strip mailto:
    to, _, query = data.partition("?")
    fields = {"Type": "Email", "To": to}
    for part in query.split("&"):
        if "=" in part:
            k, _, v = part.partition("=")
            fields[k.capitalize()] = urllib.parse.unquote(v)
    return fields


def parse_sms(data: str) -> dict:
    """Parse sms: / smsto: format."""
    inner = re.sub(r"^smsto?:", "", data, flags=re.IGNORECASE)
    number, _, msg = inner.partition(":")
    return {"Type": "SMS", "Phone Number": number, "Message": msg or "(blank)"}


def parse_event(data: str) -> dict:
    """Parse VEVENT / iCal QR."""
    fields = {"Type": "Calendar Event"}
    for line in data.splitlines():
        line = line.strip()
        if line.upper().startswith("SUMMARY:"):
            fields["Event Title"] = line[8:]
        elif line.upper().startswith("DTSTART"):
            fields["Start"] = re.sub(r".*:", "", line)
        elif line.upper().startswith("DTEND"):
            fields["End"] = re.sub(r".*:", "", line)
        elif line.upper().startswith("LOCATION:"):
            fields["Location"] = line[9:]
        elif line.upper().startswith("DESCRIPTION:"):
            fields["Description"] = line[12:]
        elif line.upper().startswith("ORGANIZER"):
            fields["Organizer"] = re.sub(r".*:", "", line)
    return fields


def detect_and_parse(data: str) -> tuple[str, dict]:
    """Detect QR type and return (type_label, parsed_fields)."""
    d = data.strip()
    du = d.upper()

    if du.startswith("BEGIN:VCARD"):
        return "📇 vCard (Contact)", parse_vcard(d)
    if du.startswith("MECARD:"):
        return "📇 MECARD (Contact)", parse_mecard(d)
    if du.startswith("WIFI:") or du.startswith("WIFI;"):
        return "📶 Wi-Fi", parse_wifi(d)
    if du.startswith("GEO:"):
        return "📍 Location", parse_geo(d)
    if du.startswith("MAILTO:"):
        return "📧 Email", parse_email(d)
    if du.startswith("SMSTO:") or du.startswith("SMS:"):
        return "💬 SMS", parse_sms(d)
    if du.startswith("BEGIN:VEVENT"):
        return "📅 Calendar Event", parse_event(d)
    if du.startswith("HTTP://") or du.startswith("HTTPS://"):
        return "🌐 URL", parse_url(d)
    if d.startswith("{") or "|" in d:
        ph = parse_ph_national_id(d)
        if ph:
            return "🇵🇭 Philippine National ID", ph
    # Try JSON anyway
    try:
        obj = json.loads(d)
        if isinstance(obj, dict):
            return "📦 JSON Data", {k: str(v) for k, v in obj.items()}
    except Exception:
        pass
    # Plain text / unknown
    return "🔤 Plain Text / Unknown", {"Data": d}


# ─────────────────────────────────────────────
#  OVERLAY RENDERER
# ─────────────────────────────────────────────

def draw_info_panel(frame, qr_type: str, fields: dict, anchor: tuple):
    """Draw a semi-transparent info panel near the QR code."""
    x, y = anchor
    lines = [f"  TYPE : {qr_type}  ", "─" * 38]
    for k, v in fields.items():
        val = v if isinstance(v, str) else ", ".join(v)
        # Wrap long values
        full = f"  {k}: {val}"
        while len(full) > 42:
            lines.append(full[:42])
            full = "      " + full[42:]
        lines.append(full)

    font = cv2.FONT_HERSHEY_SIMPLEX
    fscale, fthick = 0.48, 1
    line_h = 20
    pad = 8
    panel_w = 340
    panel_h = len(lines) * line_h + pad * 2

    # Keep panel inside frame
    h, w = frame.shape[:2]
    px = min(x, w - panel_w - 5)
    py = max(5, y - panel_h - 10)

    # Semi-transparent background
    overlay = frame.copy()
    cv2.rectangle(overlay, (px, py), (px + panel_w, py + panel_h), (20, 20, 20), -1)
    cv2.addWeighted(overlay, 0.80, frame, 0.20, 0, frame)

    # Border
    cv2.rectangle(frame, (px, py), (px + panel_w, py + panel_h), (0, 255, 100), 1)

    # Text
    for i, line in enumerate(lines):
        ty = py + pad + (i + 1) * line_h - 4
        color = (0, 255, 120) if i == 0 else (200, 200, 200) if i == 1 else (255, 255, 255)
        cv2.putText(frame, line, (px + 4, ty), font, fscale, color, fthick, cv2.LINE_AA)


# ─────────────────────────────────────────────
#  MAIN SCANNER LOOP
# ─────────────────────────────────────────────

def main():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    scanned: dict[str, tuple] = {}   # data → (qr_type, fields, timestamp)

    print("=" * 50)
    print("   QR / ID Scanner  –  Enhanced Detail View")
    print("   Press 'q' to quit  |  's' to save snapshot")
    print("=" * 50)

    last_data = None
    last_type = ""
    last_fields: dict = {}
    miss_frames = 0          # consecutive frames without a QR → dims the indicator
    MISS_THRESHOLD = 30      # ~1 s at 30 fps before "searching" state

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera not found!")
            break

        data, bbox, _ = try_detect(detector, frame)

        if data and bbox is not None:
            miss_frames = 0
            bbox = np.int32(bbox)
            points = bbox[0]

            # Draw bounding box
            for i in range(4):
                pt1 = tuple(points[i])
                pt2 = tuple(points[(i + 1) % 4])
                cv2.line(frame, pt1, pt2, (0, 255, 80), 3)

            # Corner dots
            for pt in points:
                cv2.circle(frame, tuple(pt), 5, (0, 200, 255), -1)

            # Parse
            qr_type, fields = detect_and_parse(data)
            last_data, last_type, last_fields = data, qr_type, fields

            # Draw info panel near top-left QR corner
            ax, ay = int(points[:, 0].min()), int(points[:, 1].min())
            draw_info_panel(frame, qr_type, fields, (ax, ay))

            # Log new scans
            if data not in scanned:
                ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                scanned[data] = (qr_type, fields, ts)
                print(f"\n[{ts}] {qr_type}")
                for k, v in fields.items():
                    print(f"   {k}: {v}")
                # Save to file
                with open("scanned_results.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n[{ts}] {qr_type}\n")
                    for k, v in fields.items():
                        f.write(f"   {k}: {v}\n")
                    f.write("-" * 40 + "\n")

        else:
            miss_frames += 1
            # Keep showing the last info panel for ~1 s after losing the QR
            if last_fields and miss_frames < MISS_THRESHOLD:
                draw_info_panel(frame, last_type, last_fields, (10, frame.shape[0] // 2))

        # ── Status bar ──────────────────────────────────────────────────
        count = len(scanned)
        if miss_frames == 0:
            signal = "● LOCKED"
            sig_color = (0, 255, 80)
        elif miss_frames < MISS_THRESHOLD:
            signal = "◑ HOLD..."
            sig_color = (0, 200, 255)
        else:
            signal = "○ Searching"
            sig_color = (80, 80, 255)

        status = f"  Scanned: {count}  |  {signal}  "
        (sw, sh), _ = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        cv2.rectangle(frame, (0, 0), (sw + 10, sh + 14), (30, 30, 30), -1)
        cv2.putText(frame, f"  Scanned: {count}  |  ", (5, sh + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 255), 1, cv2.LINE_AA)
        # Signal badge in its own colour
        prefix_w, _ = cv2.getTextSize(f"  Scanned: {count}  |  ",
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)[0], None
        cv2.putText(frame, signal, (5 + prefix_w[0], sh + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, sig_color, 1, cv2.LINE_AA)

        cv2.imshow("QR / ID Scanner", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            fname = f"snapshot_{datetime.now().strftime('%H%M%S')}.png"
            cv2.imwrite(fname, frame)
            print(f"Snapshot saved: {fname}")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone!  Total unique scans: {len(scanned)}")
    print("Results saved to: scanned_results.txt")


if __name__ == "__main__":
    main()