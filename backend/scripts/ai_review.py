import os
import requests
import json
import google.generativeai as genai

# =========================
# CONFIG
# =========================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("REPO")
PR_NUMBER = os.getenv("PR_NUMBER")

genai.configure(api_key=GEMINI_API_KEY)

# =========================
# MODEL SELECTION
# =========================

def choose_model(diff: str, filename: str):
    """
    Smart routing:
    - Flash = default fast review
    - Pro = important Django logic files
    """

    critical_files = ["models.py", "views.py", "serializers.py", "services.py"]

    if any(f in filename for f in critical_files):
        return "gemini-1.5-pro"

    if len(diff) > 10000:
        return "gemini-1.5-flash"

    return "gemini-1.5-flash"


# =========================
# GITHUB API
# =========================

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}


def get_pr_files():
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/files"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()


def post_comment(body):
    url = f"https://api.github.com/repos/{REPO}/issues/{PR_NUMBER}/comments"
    requests.post(url, headers=HEADERS, json={"body": body})


def post_inline_comment(file, comment):
    url = f"https://api.github.com/repos/{REPO}/pulls/{PR_NUMBER}/comments"

    payload = {
        "body": f"[{comment['severity'].upper()}] {comment['comment']}",
        "path": file["filename"],
        "line": comment["line"],
        "side": "RIGHT"
    }

    requests.post(url, headers=HEADERS, json=payload)


# =========================
# FILE FILTERING
# =========================

def is_valid_file(filename: str):
    ignored = (".md", ".json", ".lock", ".txt", ".yml", ".png")
    return not filename.endswith(ignored)


# =========================
# AI CALL
# =========================

def call_gemini(prompt: str, model_name: str):
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text


# =========================
# ANALYZE FILE
# =========================

def analyze_file(file):
    patch = file.get("patch")
    filename = file["filename"]

    if not patch:
        return []

    model_name = choose_model(patch, filename)

    prompt = f"""
You are a senior Django backend engineer performing a strict code review.

Return ONLY valid JSON:

[
  {{
    "line": int,
    "severity": "low|medium|high|critical",
    "type": "bug|security|performance|style",
    "comment": "short clear explanation"
  }}
]

Focus on:
- Django ORM efficiency (N+1 queries)
- Serializer validation issues
- Fat views (move logic to services)
- Security vulnerabilities
- Performance bottlenecks
- Clean architecture violations

Be strict but accurate.

CODE DIFF:
{patch[:8000]}
"""

    try:
        raw = call_gemini(prompt, model_name)

        # safe JSON parsing
        return json.loads(raw)

    except Exception as e:
        print(f"AI error in {filename}:", e)
        return []


# =========================
# MAIN PIPELINE
# =========================

def main():
    files = get_pr_files()

    total_critical = 0
    review_summary = []

    for file in files:
        filename = file["filename"]

        if not is_valid_file(filename):
            continue

        comments = analyze_file(file)

        for c in comments:
            severity = c.get("severity", "low")

            if severity == "critical":
                total_critical += 1

            post_inline_comment(file, c)

            review_summary.append(
                f"- [{severity.upper()}] {filename}: {c.get('comment')}"
            )

    # =========================
    # SUMMARY COMMENT
    # =========================

    summary = "## 🤖 AI Code Review\n\n"

    if review_summary:
        summary += "\n".join(review_summary)
    else:
        summary += "No issues detected."

    post_comment(summary)

    # =========================
    # BLOCK PR IF CRITICAL
    # =========================

    if total_critical > 0:
        print("Critical issues found. Blocking merge.")
        exit(1)

    print("Review completed successfully.")


if __name__ == "__main__":
    main()