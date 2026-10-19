import os
import re
import base64
import sqlite3
import json

import cv2
from dotenv import load_dotenv
from groq import Groq
from ultralytics import YOLO
from paddleocr import PaddleOCR


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set.")


# ============================================================
# GROQ CLIENT
# ============================================================

groq_client = Groq(
    api_key=GROQ_API_KEY
)


# ============================================================
# LOAD LICENSE PLATE YOLO MODEL
# ============================================================

print("Loading license plate YOLO model...")

plate_model = YOLO(
    "license_plate.pt"
)

print("License plate YOLO model loaded.")


# ============================================================
# LOAD PADDLE OCR
# ============================================================

print("Loading PaddleOCR...")

ocr = PaddleOCR(
    lang="en",
    enable_mkldnn=False
)

print("PaddleOCR loaded.")


# ============================================================
# 1. DETECT TRAFFIC VIOLATION
# ============================================================

def detect_violation(image_path):

    if not os.path.exists(image_path):
        print("Image not found:", image_path)
        return "Unknown"

    try:

        # Read image
        with open(
            image_path,
            "rb"
        ) as image_file:

            image_bytes = image_file.read()


        # Convert image to Base64
        base64_image = base64.b64encode(
            image_bytes
        ).decode("utf-8")


        # Send image to Groq Vision
        response = groq_client.chat.completions.create(

            model="qwen/qwen3.6-27b",

            messages=[
                {
                    "role": "user",

                    "content": [

                        {
                            "type": "text",

                            "text": """
Analyze this traffic image.

Identify the traffic violation visible in the image.

Choose ONLY one of these violations:

- No Helmet
- No Parking
- Triple Ride
- Overspeed
- Unknown

Return ONLY the violation name.

Do not provide explanation.
Do not guess.
"""
                        },

                        {
                            "type": "image_url",

                            "image_url": {
                                "url":
                                f"data:image/jpeg;base64,{base64_image}"
                            }
                        }

                    ]
                }
            ],

            temperature=0,

            max_tokens=300
        )


        # Get model response
        result = response.choices[0].message.content.strip()


        print()
        print("Raw Groq response:")
        print(result)
        print()


        # Valid violations
        valid_violations = [

            "No Helmet",
            "No Parking",
            "Triple Ride",
            "Overspeed"

        ]


        text = result.lower()


        # ----------------------------------------------------
        # No Helmet
        # ----------------------------------------------------

        if (
            "no helmet" in text
            or "not wearing a helmet" in text
            or "without a helmet" in text
        ):

            print(
                "Violation detected: No Helmet"
            )

            return "No Helmet"


        # ----------------------------------------------------
        # No Parking
        # ----------------------------------------------------

        if (
            "no parking" in text
            or "parked in a no parking" in text
        ):

            print(
                "Violation detected: No Parking"
            )

            return "No Parking"


        # ----------------------------------------------------
        # Triple Ride
        # ----------------------------------------------------

        if (
            "triple ride" in text
            or "three people" in text
            or "three persons" in text
        ):

            print(
                "Violation detected: Triple Ride"
            )

            return "Triple Ride"


        # ----------------------------------------------------
        # Overspeed
        # ----------------------------------------------------

        if (
            "overspeed" in text
            or "over speed" in text
            or "speeding" in text
        ):

            print(
                "Violation detected: Overspeed"
            )

            return "Overspeed"


        # ----------------------------------------------------
        # Exact matching
        # ----------------------------------------------------

        for violation in valid_violations:

            if violation.lower() in text:

                print(
                    "Violation detected:",
                    violation
                )

                return violation


        return "Unknown"


    except Exception as e:

        print(
            "Violation detection error:",
            e
        )

        return "Unknown"


# ============================================================
# 2. GET FINE FROM DATABASE
# ============================================================

def get_fine(violation):

    if not violation:
        return 0


    violation_clean = (
        violation.strip().lower()
    )


    try:

        conn = sqlite3.connect(
            "Chalan.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT fine
            FROM violations
            WHERE LOWER(violation_name) = ?
            """,
            (
                violation_clean,
            )
        )


        result = cursor.fetchone()


        conn.close()


        if result:

            print(
                f"Fine found: ₹{result[0]}"
            )

            return result[0]


        print(
            "Fine not found for:",
            violation
        )

        return 0


    except Exception as e:

        print(
            "Fine database error:",
            e
        )

        return 0


# ============================================================
# 3. NORMALIZE NUMBER PLATE
# ============================================================

def normalize_plate(text):

    if not text:
        return ""


    # Convert to uppercase
    text = text.upper()


    # Remove spaces, -, etc.
    text = re.sub(
        r"[^A-Z0-9]",
        "",
        text
    )


    return text


# ============================================================
# 4. EXTRACT OCR TEXT
# ============================================================

def extract_ocr_text(image):

    try:

        print()
        print("Running PaddleOCR...")


        # Run PaddleOCR
        results = ocr.predict(
            image
        )


        best_text = ""

        best_score = 0.0


        # ----------------------------------------------------
        # Process OCR data
        # ----------------------------------------------------

        def process_data(data):

            nonlocal best_text
            nonlocal best_score


            if data is None:
                return


            # ------------------------------------------------
            # If JSON string
            # ------------------------------------------------

            if isinstance(
                data,
                str
            ):

                try:

                    data = json.loads(
                        data
                    )

                except Exception:

                    return


            # ------------------------------------------------
            # If object has to_dict()
            # ------------------------------------------------

            if hasattr(
                data,
                "to_dict"
            ):

                try:

                    data = data.to_dict()

                except Exception:

                    pass


            # ------------------------------------------------
            # Dictionary
            # ------------------------------------------------

            if isinstance(
                data,
                dict
            ):

                texts = data.get(
                    "rec_texts",
                    []
                )

                scores = data.get(
                    "rec_scores",
                    []
                )


                # Convert one string to list
                if isinstance(
                    texts,
                    str
                ):

                    texts = [
                        texts
                    ]


                # Make scores list
                if not isinstance(
                    scores,
                    (list, tuple)
                ):

                    scores = [
                        scores
                    ] * len(texts)


                # --------------------------------------------
                # Read detected text
                # --------------------------------------------

                for i, text in enumerate(
                    texts
                ):

                    if not text:
                        continue


                    try:

                        score = float(
                            scores[i]
                        )

                    except Exception:

                        score = 0.0


                    print(
                        f"OCR detected: "
                        f"{text} "
                        f"(confidence: "
                        f"{score:.2f})"
                    )


                    if score >= best_score:

                        best_text = str(
                            text
                        )

                        best_score = score


                # --------------------------------------------
                # Check nested data
                # --------------------------------------------

                for value in data.values():

                    if isinstance(
                        value,
                        (
                            dict,
                            list,
                            tuple
                        )
                    ):

                        process_data(
                            value
                        )


            # ------------------------------------------------
            # List / Tuple
            # ------------------------------------------------

            elif isinstance(
                data,
                (
                    list,
                    tuple
                )
            ):

                for item in data:

                    process_data(
                        item
                    )


        # ====================================================
        # PROCESS RESULTS
        # ====================================================

        for res in results:


            # ------------------------------------------------
            # Process object directly
            # ------------------------------------------------

            try:

                process_data(
                    res
                )

            except Exception:

                pass


            # ------------------------------------------------
            # Try .json
            # ------------------------------------------------

            if hasattr(
                res,
                "json"
            ):

                try:

                    data = res.json


                    if callable(data):

                        data = data()


                    process_data(
                        data
                    )

                except Exception:

                    pass


            # ------------------------------------------------
            # Try .to_dict()
            # ------------------------------------------------

            if hasattr(
                res,
                "to_dict"
            ):

                try:

                    process_data(
                        res.to_dict()
                    )

                except Exception:

                    pass


        # ====================================================
        # FINAL OCR RESULT
        # ====================================================

        print()

        print(
            f"Best OCR text: "
            f"{best_text}"
        )

        print(
            f"Best OCR confidence: "
            f"{best_score:.2f}"
        )

        print()


        return best_text.strip()


    except Exception as e:

        print(
            "OCR error:",
            e
        )

        return ""


# ============================================================
# 5. GET ALL USERS FROM DATABASE
# ============================================================

def get_all_users():

    try:

        conn = sqlite3.connect(
            "user.db"
        )

        cursor = conn.cursor()


        cursor.execute(
            """
            SELECT
                name,
                vehicle_reg,
                vehicle_type,
                vehnum,
                mobile,
                driver_photo
            FROM users
            """
        )


        users = cursor.fetchall()


        conn.close()


        return users


    except Exception as e:

        print(
            "User database error:",
            e
        )

        return []


# ============================================================
# 6. FIND USER BY NUMBER PLATE
# ============================================================

def find_user_by_plate(
    ocr_plate
):

    if not ocr_plate:
        return None


    # Normalize OCR plate
    ocr_plate = normalize_plate(
        ocr_plate
    )


    print(
        "Searching database for:",
        ocr_plate
    )


    # Get users
    users = get_all_users()


    # ========================================================
    # EXACT MATCH
    # ========================================================

    for user in users:

        database_plate = normalize_plate(
            user[1]
        )


        if (
            ocr_plate
            == database_plate
        ):

            print(
                f"Database match found: "
                f"{ocr_plate} "
                f"-> "
                f"{database_plate}"
            )

            return user


    # ========================================================
    # OCR CHARACTER CORRECTIONS
    # ========================================================

    corrections = {

        "0": ["O"],
        "O": ["0"],

        "1": ["I"],
        "I": ["1"],

        "5": ["S"],
        "S": ["5"],

        "8": ["B"],
        "B": ["8"],

        "F": ["E"],
        "E": ["F"],

        "G": ["C", "6"],
        "C": ["G"],

        "D": ["O"]

    }


    # ========================================================
    # ONE CHARACTER DIFFERENCE
    # ========================================================

    for user in users:

        database_plate = normalize_plate(
            user[1]
        )


        # Different lengths cannot match
        if (
            len(ocr_plate)
            != len(database_plate)
        ):

            continue


        differences = []


        for i in range(
            len(ocr_plate)
        ):

            if (
                ocr_plate[i]
                != database_plate[i]
            ):

                differences.append(
                    (
                        ocr_plate[i],
                        database_plate[i]
                    )
                )


        # Only one character different
        if len(differences) == 1:

            ocr_char, database_char = (
                differences[0]
            )


            if (
                ocr_char in corrections
                and database_char
                in corrections[ocr_char]
            ):

                print(
                    f"OCR correction: "
                    f"{ocr_plate} "
                    f"-> "
                    f"{database_plate}"
                )


                return user


    return None


# ============================================================
# 7. DETECT NUMBER PLATE
# ============================================================

def detect_number_plate(
    image_path
):

    if not os.path.exists(
        image_path
    ):

        print(
            "Image not found:",
            image_path
        )

        return ""


    # Read image
    image = cv2.imread(
        image_path
    )


    if image is None:

        print(
            "Could not read image."
        )

        return ""


    print()
    print(
        "Detecting number plate..."
    )


    # ========================================================
    # YOLO PLATE DETECTION
    # ========================================================

    results = plate_model.predict(

        image,

        conf=0.25,

        iou=0.45,

        imgsz=1280,

        max_det=10,

        verbose=False
    )


    best_ocr = ""

    plate_number = 0


    # ========================================================
    # PROCESS DETECTED PLATES
    # ========================================================

    for result in results:

        boxes = result.boxes


        if boxes is None:
            continue


        for box in boxes:

            plate_number += 1


            # YOLO confidence
            confidence = float(
                box.conf[0]
            )


            print(
                f"Plate {plate_number} "
                f"YOLO confidence: "
                f"{confidence:.2f}"
            )


            # Bounding box
            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0].tolist()
            )


            # Image dimensions
            h, w = image.shape[:2]


            # =================================================
            # ADD PADDING
            # =================================================

            padding_x = int(
                (x2 - x1) * 0.10
            )

            padding_y = int(
                (y2 - y1) * 0.10
            )


            x1 = max(
                0,
                x1 - padding_x
            )

            y1 = max(
                0,
                y1 - padding_y
            )

            x2 = min(
                w,
                x2 + padding_x
            )

            y2 = min(
                h,
                y2 + padding_y
            )


            # =================================================
            # CROP NUMBER PLATE
            # =================================================

            crop = image[
                y1:y2,
                x1:x2
            ]


            if crop.size == 0:

                print(
                    "Empty plate crop."
                )

                continue


            # =================================================
            # SAVE PLATE CROP
            # =================================================

            os.makedirs(
                "plate_crops",
                exist_ok=True
            )


            crop_path = os.path.join(

                "plate_crops",

                f"agent_plate_{plate_number}.jpg"

            )


            cv2.imwrite(
                crop_path,
                crop
            )


            print(
                f"Saved: {crop_path}"
            )


            # =================================================
            # RUN OCR
            # =================================================

            ocr_text = extract_ocr_text(
                crop
            )


            print(
                f"OCR result: "
                f"{ocr_text}"
            )


            # =================================================
            # NORMALIZE OCR RESULT
            # =================================================

            clean_plate = normalize_plate(
                ocr_text
            )


            print(
                f"Clean plate: "
                f"{clean_plate}"
            )


            # =================================================
            # TRY UPSCALED IMAGE IF OCR FAILED
            # =================================================

            if not clean_plate:

                print(
                    "Original OCR failed."
                )

                print(
                    "Trying upscaled crop..."
                )


                upscaled = cv2.resize(

                    crop,

                    None,

                    fx=2,

                    fy=2,

                    interpolation=cv2.INTER_CUBIC

                )


                ocr_text = extract_ocr_text(
                    upscaled
                )


                print(
                    f"Upscaled OCR result: "
                    f"{ocr_text}"
                )


                clean_plate = normalize_plate(
                    ocr_text
                )


                print(
                    f"Upscaled clean plate: "
                    f"{clean_plate}"
                )


            # =================================================
            # IF STILL EMPTY
            # =================================================

            if not clean_plate:

                print(
                    "OCR could not read this plate."
                )

                continue


            # Save first OCR result
            if not best_ocr:

                best_ocr = clean_plate


            # =================================================
            # SEARCH DATABASE
            # =================================================

            user = find_user_by_plate(
                clean_plate
            )


            # =================================================
            # USER FOUND
            # =================================================

            if user:

                database_plate = normalize_plate(
                    user[1]
                )


                print()

                print(
                    "======================================"
                )

                print(
                    "VEHICLE FOUND"
                )

                print(
                    "======================================"
                )

                print(
                    f"Database plate: "
                    f"{database_plate}"
                )

                print(
                    f"Owner: "
                    f"{user[0]}"
                )

                print(
                    f"Vehicle type: "
                    f"{user[2]}"
                )

                print(
                    f"Mobile: "
                    f"{user[4]}"
                )

                print(
                    "======================================"
                )

                print()


                return database_plate


    # ========================================================
    # RETURN BEST OCR RESULT
    # ========================================================

    return best_ocr


# ============================================================
# 8. GET USER
# ============================================================

def get_user(
    number_plate
):

    if not number_plate:
        return None


    number_plate = normalize_plate(
        number_plate
    )


    return find_user_by_plate(
        number_plate
    )