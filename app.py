import re
from flask import Flask, render_template, request, jsonify
import anthropic

app = Flask(__name__)
client = anthropic.Anthropic()

FEW_SHOT_EXAMPLE = """
Example input: "User should be able to log in with valid credentials"

Example output:
| TC_ID | Name                        | Type     | Steps                                                              | Expected Result                           | Priority |
|-------|-----------------------------|----------|--------------------------------------------------------------------|-------------------------------------------|----------|
| TC_01 | Valid Login Success          | Positive | 1. Navigate to login page 2. Enter valid username 3. Enter valid password 4. Click Login | User is redirected to dashboard           | High     |
| TC_02 | Invalid Password Rejection   | Negative | 1. Navigate to login page 2. Enter invalid password 3. Click Login | Error message "Invalid credentials" shown | High     |
| TC_03 | Empty Username Validation    | Negative | 1. Navigate to login page 2. Leave username blank 3. Click Login   | Validation error "Username is required"   | Medium   |
| TC_04 | Max Length Username Boundary | Boundary | 1. Navigate to login page 2. Enter username with 256 characters 3. Click Login | Error shown for max length exceeded | Medium |
| TC_05 | SQL Injection Prevention     | Security | 1. Navigate to login page 2. Enter SQL injection in username 3. Click Login | Input is sanitized, login fails safely  | High     |
"""

SYSTEM_PROMPT = (
    "You are a senior SDET with 10 years of experience writing test cases for enterprise applications.\n\n"
    "Your job is to generate exactly 5 test cases for a given requirement.\n\n"
    "Instructions:\n"
    "- Think step by step: understand the requirement, identify happy paths, edge cases, negative scenarios, and security concerns.\n"
    "- Output ONLY a markdown table with these exact columns: TC_ID, Name, Type, Steps, Expected Result, Priority.\n"
    "- TC_ID format: TC_01, TC_02, ...\n"
    "- Name should be a short descriptive title (4-6 words) for the test case.\n"
    "- Type must be one of: Positive, Negative, Boundary, Security, Performance\n"
    "- Steps should be numbered inline (e.g. 1. Open page 2. Click button 3. Verify result)\n"
    "- Priority must be one of: High, Medium, Low\n"
    "- Do not include any text before or after the table.\n\n"
    "Here is an example of the required format:\n"
    + FEW_SHOT_EXAMPLE
)


def call_claude(requirement: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Requirement: {requirement}\n\n"
                    "Think step by step:\n"
                    "1. What is the core functionality being tested?\n"
                    "2. What are the happy path scenarios?\n"
                    "3. What can go wrong (negative cases)?\n"
                    "4. Are there boundary or security concerns?\n\n"
                    "Now generate the 5 test cases in the exact table format shown."
                ),
            }
        ],
    )
    return message.content[0].text


def parse_markdown_table(text: str) -> list[dict]:
    lines = [l.strip() for l in text.strip().splitlines() if l.strip().startswith("|")]
    # Need at least header + separator + 1 data row
    if len(lines) < 3:
        return []

    rows = []
    for line in lines[2:]:  # skip header and separator
        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]  # remove empty edge splits
        if len(cells) >= 6:
            rows.append({
                "tc_id": cells[0],
                "name": cells[1],
                "type": cells[2],
                "steps": cells[3],
                "expected": cells[4],
                "priority": cells[5],
            })
    return rows


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    requirement = request.json.get("requirement", "").strip()
    if not requirement:
        return jsonify({"error": "Requirement cannot be empty."}), 400

    try:
        raw = call_claude(requirement)
        rows = parse_markdown_table(raw)
        if not rows:
            return jsonify({"error": "Could not parse response. Please try again."}), 500
        return jsonify({"rows": rows})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
