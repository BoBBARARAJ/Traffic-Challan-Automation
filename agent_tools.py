from langchain_core.tools import tool

from violation_detection import (
    detect_violation,
    detect_number_plate,
    get_fine,
    get_user
)

from challan_generator import generate_challan


# ============================================================
# 1. DETECT VIOLATION TOOL
# ============================================================

@tool
def detect_violation_tool(
    image_path: str
) -> str:
    """
    Detect the traffic violation from a traffic image.

    Returns:
    No Helmet
    Triple Ride
    No Parking
    Overspeed
    Unknown
    """

    return detect_violation(
        image_path
    )


# ============================================================
# 2. DETECT NUMBER PLATE TOOL
# ============================================================

@tool
def detect_number_plate_tool(
    image_path: str
) -> str:
    """
    Detect and recognize the vehicle number plate
    from a traffic image.
    """

    plate = detect_number_plate(
        image_path
    )

    if not plate:
        return "Unknown"

    return plate


# ============================================================
# 3. GET FINE TOOL
# ============================================================

@tool
def get_fine_tool(
    violation: str
) -> int:
    """
    Get the fine amount for a traffic violation.
    """

    return get_fine(
        violation
    )


# ============================================================
# 4. GET USER TOOL
# ============================================================

@tool
def get_user_tool(
    number_plate: str
) -> dict:
    """
    Find vehicle owner details using
    the vehicle number plate.
    """

    user = get_user(
        number_plate
    )


    if not user:

        return {
            "found": False
        }


    return {

        "found": True,

        "name": user[0],

        "vehicle_reg": user[1],

        "vehicle_type": user[2],

        "vehnum": user[3],

        "mobile": user[4],

        "driver_photo": user[5]

    }


# ============================================================
# 5. GENERATE CHALLAN TOOL
# ============================================================

@tool
def generate_challan_tool(
    violation: str,
    fine: int,
    number_plate: str,
    owner_name: str,
    vehicle_type: str,
    mobile: str
) -> str:
    """
    Generate and save a traffic challan
    after violation, fine, number plate,
    and owner details are available.
    """

    challan = generate_challan(

        violation=violation,

        fine=fine,

        number_plate=number_plate,

        owner_name=owner_name,

        vehicle_type=vehicle_type,

        mobile=mobile

    )


    return challan


# ============================================================
# ALL TRAFFIC TOOLS
# ============================================================

traffic_tools = [

    detect_violation_tool,

    get_fine_tool,

    detect_number_plate_tool,

    get_user_tool,

    generate_challan_tool

]