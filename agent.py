import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.agents import create_agent

from agent_tools import traffic_tools


# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set.")


# ============================================================
# CREATE LLM
# ============================================================

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    api_key=GROQ_API_KEY
)


# ============================================================
# AGENT INSTRUCTIONS
# ============================================================

system_prompt = """
You are a Traffic Challan AI Agent.

You must process a traffic image using the tools available to you.

FOLLOW THESE STEPS IN EXACT ORDER:

STEP 1:
Call detect_violation_tool with the image path.

STEP 2:
Call get_fine_tool using the violation returned
from Step 1.

STEP 3:
Call detect_number_plate_tool using the same image path.

STEP 4:
Call get_user_tool using the number plate
returned from Step 3.

STEP 5:
If the owner is found, call generate_challan_tool
using all the information:

- violation
- fine
- number plate
- owner name
- vehicle type
- mobile number

IMPORTANT:

Do not invent information.

If the number plate is Unknown,
do not guess it.

If the owner is not found,
do not generate a challan.

Only generate the challan when the required
information is available.

At the end, show:

Challan ID
Violation
Fine
Number Plate
Owner Name
Vehicle Type
Mobile Number
Status
"""


# ============================================================
# CREATE AGENT
# ============================================================

agent = create_agent(
    model=llm,
    tools=traffic_tools,
    system_prompt=system_prompt
)


# ============================================================
# PROCESS IMAGE
# ============================================================

def process_traffic_image(image_path):

    result = agent.invoke({

        "messages": [

            {
                "role": "user",

                "content": f"""
Process this traffic image:

{image_path}

Follow all five steps.
Generate the challan if the owner is found.
"""
            }

        ]

    })

    return result


# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":

    image_path = "images/no_helmet.jpg"

    print()
    print("=" * 70)
    print("TRAFFIC CHALLAN AI AGENT")
    print("=" * 70)

    print()
    print(
        f"Processing image: {image_path}"
    )
    print()

    result = process_traffic_image(
        image_path
    )

    print()
    print("=" * 70)
    print("AGENT RESULT")
    print("=" * 70)

    messages = result.get(
        "messages",
        []
    )

    if messages:

        final_message = messages[-1]

        print(
            final_message.content
        )

    else:

        print(result)

    print()
    print("=" * 70)