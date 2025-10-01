# Saved examples for fast lookup in orchestrate()
examples = [
    # 2 examples that return GeneralQAAgent only
    {
        "user_request": "What does the Dashboard page show?",
        "filtered_output": {
            "GeneralQAAgent": "The Dashboard page provides real‑time insights into all budget transfer activities, including summary metrics (approved, rejected, pending, total), type breakdowns (FAR/AFR/FAD), approval pipeline monitoring, and interactive visualizations for deeper analysis."
        },
    },
    {
        "user_request": "How do I view and delete my notifications?",
        "filtered_output": {
            "GeneralQAAgent": "On the Notifications page you can see a list of all system messages. To delete one, click the trash icon next to the message; unread notifications are highlighted until you either read or delete them."
        },
    },
    {
        "user_request": "What is the Tanfeez App?",
        "filtered_output": {
            "GeneralQAAgent": "The Tanfeez App is a smart finance management tool that allows employees and managers to submit, approve, and track budget transfers and adjustments between departments or cost centers."
        },
    },
    {
        "user_request": "What are the features and functions of this app?",
        "filtered_output": {
            "GeneralQAAgent": "Key features include budget transfer requests, adjustment submissions, multi-level approval workflows, real-time tracking, notifications, role-based access, and downloadable reports."
        },
    },
    {
        "user_request": "How can I request a budget transfer?",
        "filtered_output": {
            "GeneralQAAgent": "Go to Transfers, select the source and target cost centers, enter amount and reason, then submit. Track it from your dashboard."
        },
    },
    {
        "user_request": "How can I submit a budget adjustment?",
        "filtered_output": {
            "GeneralQAAgent": "Navigate to Adjustments, choose the cost center, enter the new amount with explanation, and click Submit to begin approval."
        },
    },
    {
        "user_request": "Can you guide me through a sample transfer?",
        "filtered_output": {
            "GeneralQAAgent": "Sure! Go to Transfers, choose source (e.g., Marketing), target (e.g., Sales), enter 5,000 EGP and a reason like 'Campaign support', then submit."
        },
    },
    {
        "user_request": "What actions can employees perform?",
        "filtered_output": {
            "GeneralQAAgent": "Employees can submit budget transfer/adjustment requests, view their request history, and monitor approval statuses."
        },
    },
    {
        "user_request": "What are the capabilities of finance managers?",
        "filtered_output": {
            "GeneralQAAgent": "Finance managers can review and approve/reject requests, access detailed reports, and manage budget limits for cost centers."
        },
    },
    {
        "user_request": "How does the approval process work?",
        "filtered_output": {
            "GeneralQAAgent": "It flows as follows: employee submits → department head reviews → finance manager finalizes. Notifications are sent at each stage."
        },
    },
    {
        "user_request": "Will I receive notifications for status updates?",
        "filtered_output": {
            "GeneralQAAgent": "Yes, you’ll receive in-app and optional email notifications for status changes: submitted, approved, rejected, or canceled."
        },
    },
    {
        "user_request": "How can I check the status of my request?",
        "filtered_output": {
            "GeneralQAAgent": "Go to Dashboard > My Requests to view all your current and past requests along with their status indicators."
        },
    },
    {
        "user_request": "Can I download a report of my transfers or adjustments?",
        "filtered_output": {
            "GeneralQAAgent": "Yes. Visit the Reports section, choose your desired date range, and click Export to download in Excel or PDF."
        },
    },
    {
        "user_request": "Can the app provide me with a summary of my budget activity?",
        "filtered_output": {
            "GeneralQAAgent": "Yes. Ask the assistant for a summary and you’ll get insights like total transfers, top cost centers, and pending items."
        },
    },
    {
        "user_request": "What is a cost center?",
        "filtered_output": {
            "GeneralQAAgent": "A cost center is a department or unit (e.g., HR, IT, Marketing) responsible for managing its own budget within the organization."
        },
    },
    {
        "user_request": "Can I cancel a submitted request?",
        "filtered_output": {
            "GeneralQAAgent": "Yes, but only before it’s approved. Go to My Requests, find the item, and click Cancel."
        },
    },
    {
        "user_request": "Can I request multiple transfers at once?",
        "filtered_output": {
            "GeneralQAAgent": "Currently, each transfer must be submitted individually. A batch transfer feature may be added in future updates."
        },
    },
    {
        "user_request": "What can the assistant help me with?",
        "filtered_output": {
            "GeneralQAAgent": "The assistant can guide you through transfers, answer finance-related questions, summarize your activities, and help with cost center info."
        },
    },
    {
        "user_request": "How do I ask the assistant for a summary?",
        "filtered_output": {
            "GeneralQAAgent": "Just say something like: 'Summarize my activities for the last 30 days' or 'What are my pending approvals?'"
        },
    },
    # 2 examples that return GeneralQAAgent + PageNavigatorAgent
    {
        "user_request": "Take me to the User Management section.",
        "filtered_output": {
            "PageNavigatorAgent": "/admin/user-management",
            "GeneralQAAgent": "Sure—navigating you to the User Management interface where you can create, edit, or remove user accounts and assign roles.",
        },
    },
    {
        "user_request": "Open the Dashboard for me.",
        "filtered_output": {
            "PageNavigatorAgent": "/dashboard",
            "GeneralQAAgent": "Opening the main Dashboard—here you’ll find executive metrics, transfer flow charts, and performance indicators at a glance.",
        },
    },
    # 2 examples that return GeneralQAAgent + SQLBuilderAgent
    {
        "user_request": "List all active administrators.",
        "filtered_output": {
            "SQLBuilderAgent": """
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr><th>ID</th><th>Username</th><th>Role</th><th>Is Active</th></tr></thead>
  <tbody>
    <tr><td>1</td><td>admin</td><td>admin</td><td>true</td></tr>
    <tr><td>4</td><td>j.smith</td><td>admin</td><td>true</td></tr>
  </tbody>
</table>
""".strip(),
            "GeneralQAAgent": "Here are all users with the ‘admin’ role who are currently active in the system.",
        },
    },
    {
        "user_request": "Show me pending budget transfers.",
        "filtered_output": {
            "SQLBuilderAgent": """
<table border="1" cellpadding="4" cellspacing="0">
  <thead><tr><th>Transaction ID</th><th>Requested By</th><th>Amount</th><th>Status</th></tr></thead>
  <tbody>
    <tr><td>1001</td><td>alice</td><td>5000.00</td><td>pending</td></tr>
    <tr><td>1005</td><td>bob</td><td>7500.00</td><td>pending</td></tr>
  </tbody>
</table>
""".strip(),
            "GeneralQAAgent": "Here’s the list of all budget-transfer records currently in ‘pending’ status.",
        },
    },
    {
        "user_request": "What is the Capex for Last Year?",
        "filtered_output": {
            "GeneralQAAgent": "The Capital Expenditure (Capex) for last year was 20,000,000"
        },
    },
    {
        "user_request": "What is the Capex for current Year?",
        "filtered_output": {
            "GeneralQAAgent": "The Capital Expenditure (Capex) for current year is 20,000,000"
        },
    },
    {
        "user_request": "What is the current status of our budget envelopes?",
        "filtered_output": {
            "GeneralQAAgent": "Initial Envelope: 3,825,657,203.85 EGP\nProjected Envelope: 3,825,675,603.85 EGP\nFinal Envelope: 3,825,674,553.85 EGP\n📊 Analysis: The budget shows minimal variation with a slight projected increase of 18,400 EGP from initial envelope, while the final envelope indicates a marginal decrease of 1,050 EGP from projected figures. Overall budget stability is maintained with variations less than 0.001% of total envelope."
        },
    },
    {
        "user_request": "How many transactions are still pending vs approved?",
        "filtered_output": {
            "GeneralQAAgent": "Total Transfers: 130\nApproved Transfers: 7\nPending Transfers: 104\n📊 Analysis: Currently 80% of transfers are pending approval, while only 5.4% have been approved. This indicates a significant number of transfers in the approval pipeline that need processing."
        },
    },
    {
        "user_request": "What is the breakdown of transfers vs additional budget?",
        "filtered_output": {
            "GeneralQAAgent": "Transfers: 92\nAdditional Budget: 22\nTotal Transactions: 114\n📊 Analysis: Transfers represent 80.7% of all transactions, while additional budget requests make up 19.3%. This distribution indicates that most financial activities are focused on reallocating existing budgets rather than requesting new funds."
        },
    },
    {
        "user_request": "What percentage of total transactions are still pending?",
        "filtered_output": {
            "GeneralQAAgent": "Pending: 104 out of 130\nPercentage: 80%\n📊 Analysis: With 80% of transactions pending, the current approval process requires attention. This high pending rate suggests a need to review and potentially optimize the approval workflow to improve processing efficiency."
        },
    },
]



import difflib
import string
from typing import Optional, Dict


def normalize(text: str) -> str:
    """Lowercase and remove punctuation and extra whitespace from text."""
    return "".join(c for c in text.lower() if c not in string.punctuation).strip()


def similarity_ratio(a: str, b: str) -> float:
    """Return a similarity ratio between two strings."""
    return difflib.SequenceMatcher(None, a, b).ratio()


def match_example_request(
    user_request: str, examples: list, threshold: float = 0.5
) -> Optional[Dict]:
    """Match user request to example if similarity is above threshold."""
    user_normalized = normalize(user_request)
    best_match = None
    best_ratio = 0.0

    for ex in examples:
        ex_normalized = normalize(ex["user_request"])
        ratio = similarity_ratio(user_normalized, ex_normalized)
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = ex

    if best_ratio >= threshold:
        return best_match
    return None
