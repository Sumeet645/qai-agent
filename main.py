import anthropic

client = anthropic.Anthropic()

FEW_SHOT_EXAMPLE = """
Example input: "User should be able to log in with valid credentials"

Example output:
| TC_ID | Type        | Steps                                                                 | Expected Result                          | Priority |
|-------|-------------|-----------------------------------------------------------------------|------------------------------------------|----------|
| TC_01 | Positive    | 1. Navigate to login page\n2. Enter valid username\n3. Enter valid password\n4. Click Login | User is redirected to dashboard          | High     |
| TC_02 | Negative    | 1. Navigate to login page\n2. Enter invalid username\n3. Enter valid password\n4. Click Login | Error message "Invalid credentials" shown | High     |
| TC_03 | Negative    | 1. Navigate to login page\n2. Leave username blank\n3. Enter valid password\n4. Click Login | Validation error "Username is required"  | Medium   |
| TC_04 | Boundary    | 1. Navigate to login page\n2. Enter username with 256 characters\n3. Click Login | Error message shown for max length exceeded | Medium   |
| TC_05 | Security    | 1. Navigate to login page\n2. Enter SQL injection in username field\n3. Click Login | Input is sanitized, login fails safely   | High     |
"""

SYSTEM_PROMPT = """You are a senior SDET with 10 years of experience writing test cases for enterprise applications.

Your job is to generate exactly 5 test cases for a given requirement.

Instructions:
- Think step by step: first understand the requirement, identify happy paths, edge cases, negative scenarios, and security concerns.
- Output ONLY a markdown table with these columns: TC_ID, Type, Steps, Expected Result, Priority.
- TC_ID format: TC_01, TC_02, ...
- Type must be one of: Positive, Negative, Boundary, Security, Performance
- Steps should be numbered within the cell (e.g. 1. Do X  2. Do Y)
- Priority must be one of: High, Medium, Low
- Do not include any text before or after the table.

Here is an example of the required format:
""" + FEW_SHOT_EXAMPLE


def generate_test_cases(requirement: str) -> str:
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


def print_banner(title: str) -> None:
    width = 70
    print("\n" + "=" * width)
    print(f"  {title}".center(width))
    print("=" * width)


def main() -> None:
    print_banner("AI Test Case Generator  |  Powered by Claude")
    requirement = input("\n  Enter your requirement:\n  > ").strip()

    if not requirement:
        print("\n  [Error] Requirement cannot be empty.\n")
        return

    print("\n  Generating test cases, please wait...\n")
    result = generate_test_cases(requirement)

    print_banner("Generated Test Cases")
    print()
    print(result)
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
