import os
import re
import cv2
import sqlite3

from ultralytics import YOLO
from paddleocr import PaddleOCR


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_PATH = "images/no_helmet.jpg"
MODEL_PATH = "license_plate.pt"
DATABASE_PATH = "user.db"

CROP_DIR = "plate_crops"

os.makedirs(CROP_DIR, exist_ok=True)


# ============================================================
# LOAD YOLO MODEL
# ============================================================

print("Loading YOLO model...")

model = YOLO(MODEL_PATH)

print("YOLO model loaded.")


# ============================================================
# LOAD PADDLEOCR
# ============================================================

print("Loading PaddleOCR...")

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

print("PaddleOCR loaded.")


# ============================================================
# NORMALIZE NUMBER PLATE
# ============================================================

def normalize_plate(text):

    if not text:
        return ""

    # Convert to uppercase
    text = text.upper()

    # Remove spaces, -, /, etc.
    text = re.sub(r"[^A-Z0-9]", "", text)

    return text


# ============================================================
# EXTRACT TEXT USING PADDLEOCR
# ============================================================

def extract_ocr_text(image):

    try:

        results = ocr.predict(image)

        for result in results:

            data = result.json

            # Some PaddleOCR versions return a callable json
            if callable(data):
                data = data()

            if not isinstance(data, dict):
                continue

            # Get "res"
            res = data.get("res", data)

            # Get recognized texts
            texts = res.get("rec_texts", [])

            if texts:

                # Return first recognized text
                return texts[0]

    except Exception as e:

        print("OCR error:", e)

    return ""


# ============================================================
# GET USERS FROM DATABASE
# ============================================================

def get_all_users():

    conn = sqlite3.connect(DATABASE_PATH)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            name,
            vehicle_reg,
            vehicle_type,
            vehnum,
            mobile,
            driver_photo
        FROM users
    """)

    users = cursor.fetchall()

    conn.close()

    return users


# ============================================================
# FIND USER BY NUMBER PLATE
# ============================================================

def find_user_by_plate(ocr_plate):

    # Normalize OCR result
    ocr_plate = normalize_plate(ocr_plate)

    if not ocr_plate:
        return None

    # Get all users
    users = get_all_users()

    # ========================================================
    # 1. EXACT MATCH
    # ========================================================

    for user in users:

        db_plate = normalize_plate(user[1])

        if ocr_plate == db_plate:

            return user

    # ========================================================
    # 2. COMMON OCR CORRECTIONS
    # ========================================================

    corrections = {

        # Number ↔ Letter
        "0": ["O"],
        "O": ["0"],

        "1": ["I"],
        "I": ["1"],

        "5": ["S"],
        "S": ["5"],

        "8": ["B"],
        "B": ["8"],

        # Common character confusion
        "F": ["E"],
        "E": ["F"],

        "G": ["C", "6"],
        "C": ["G"],

        "D": ["O"],
    }

    # ========================================================
    # 3. TRY ONE CHARACTER CORRECTION
    # ========================================================

    for i in range(len(ocr_plate)):

        char = ocr_plate[i]

        if char not in corrections:
            continue

        possible_replacements = corrections[char]

        for replacement in possible_replacements:

            candidate = (
                ocr_plate[:i]
                + replacement
                + ocr_plate[i + 1:]
            )

            # Compare corrected candidate
            # with database plates
            for user in users:

                db_plate = normalize_plate(user[1])

                if candidate == db_plate:

                    print(
                        f"OCR correction: "
                        f"{ocr_plate} -> {candidate}"
                    )

                    return user

    return None


# ============================================================
# PRINT USER DETAILS
# ============================================================

def print_user_details(user):

    if not user:
        print()
        print("No matching vehicle found in database.")
        return

    print()
    print("DATABASE MATCH FOUND")
    print("-" * 45)

    print(f"Name         : {user[0]}")
    print(f"Vehicle Reg  : {user[1]}")
    print(f"Vehicle Type : {user[2]}")
    print(f"Vehicle No   : {user[3]}")
    print(f"Mobile       : {user[4]}")
    print(f"Driver Photo : {user[5]}")


# ============================================================
# MAIN PROGRAM
# ============================================================

print()
print("=" * 60)
print("NUMBER PLATE DETECTION")
print("=" * 60)

# ============================================================
# CHECK IMAGE
# ============================================================

if not os.path.exists(IMAGE_PATH):

    print()
    print(f"Image not found: {IMAGE_PATH}")
    exit()


# ============================================================
# READ IMAGE
# ============================================================

image = cv2.imread(IMAGE_PATH)

if image is None:

    print()
    print("Could not read image.")

    exit()


# ============================================================
# RUN YOLO
# ============================================================

print()
print("Running YOLO...")

results = model.predict(
    IMAGE_PATH,
    conf=0.25,
    iou=0.45,
    imgsz=1280,
    max_det=10
)

result = results[0]

boxes = result.boxes

total_plates = len(boxes)


# ============================================================
# NO PLATE DETECTED
# ============================================================

if total_plates == 0:

    print()
    print("No license plates detected.")

    print()
    print("=" * 60)
    print("TOTAL PLATES DETECTED: 0")
    print("=" * 60)

    exit()


# ============================================================
# PROCESS EACH PLATE
# ============================================================

for i, box in enumerate(boxes):

    print()
    print("=" * 60)
    print(f"PLATE {i + 1}")
    print("=" * 60)

    # --------------------------------------------------------
    # YOLO CONFIDENCE
    # --------------------------------------------------------

    confidence = float(box.conf[0])

    print(
        f"YOLO confidence: {confidence:.2f}"
    )

    # --------------------------------------------------------
    # GET BOUNDING BOX
    # --------------------------------------------------------

    x1, y1, x2, y2 = map(
        int,
        box.xyxy[0].tolist()
    )

    height, width = image.shape[:2]

    # --------------------------------------------------------
    # ADD 10% PADDING
    # --------------------------------------------------------

    pad_x = int((x2 - x1) * 0.10)
    pad_y = int((y2 - y1) * 0.10)

    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)

    x2 = min(width, x2 + pad_x)
    y2 = min(height, y2 + pad_y)

    # --------------------------------------------------------
    # CROP PLATE
    # --------------------------------------------------------

    plate_crop = image[
        y1:y2,
        x1:x2
    ]

    crop_path = os.path.join(
        CROP_DIR,
        f"plate_{i + 1}.jpg"
    )

    cv2.imwrite(
        crop_path,
        plate_crop
    )

    print(
        f"Saved: {crop_path}"
    )

    # ========================================================
    # PADDLEOCR
    # ========================================================

    raw_text = extract_ocr_text(
        plate_crop
    )

    print(
        f"OCR raw result: {raw_text}"
    )

    # ========================================================
    # NORMALIZE OCR
    # ========================================================

    clean_plate = normalize_plate(
        raw_text
    )

    print(
        f"Clean plate: {clean_plate}"
    )

    # ========================================================
    # DATABASE MATCH
    # ========================================================

    user = find_user_by_plate(
        clean_plate
    )

    # ========================================================
    # DISPLAY OWNER
    # ========================================================

    print_user_details(user)


# ============================================================
# FINAL RESULT
# ============================================================

print()
print("=" * 60)
print(
    f"TOTAL PLATES DETECTED: {total_plates}"
)
print("=" * 60)