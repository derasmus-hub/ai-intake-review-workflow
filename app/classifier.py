from app.models import AIClassification, Category, Priority


CATEGORY_KEYWORDS: tuple[tuple[Category, tuple[str, ...]], ...] = (
    (Category.FINANCE, ("invoice", "payment", "purchase order", "expense")),
    (Category.IT, ("computer", "login", "software", "password")),
    (Category.HR, ("employee", "hiring", "vacation", "payroll")),
    (Category.SALES, ("customer", "quote", "lead")),
    (Category.OPERATIONS, ("warehouse", "production", "delivery")),
)

HIGH_PRIORITY_KEYWORDS = ("urgent", "critical", "immediately", "outage", "blocked")
LOW_PRIORITY_KEYWORDS = ("when possible", "information", "question", "minor")

RECOMMENDED_ACTIONS = {
    Category.FINANCE: "Route to the finance team for review.",
    Category.IT: "Route to the IT support team for review.",
    Category.HR: "Route to the HR team for review.",
    Category.SALES: "Route to the sales team for review.",
    Category.OPERATIONS: "Route to the operations team for review.",
    Category.OTHER: "Route to the appropriate business owner for review.",
}


def classify_request(subject: str, details: str) -> AIClassification:
    """Return a deterministic recommendation without changing workflow state."""
    text = f"{subject} {details}".lower()

    category = Category.OTHER
    for candidate, keywords in CATEGORY_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            category = candidate
            break

    if any(keyword in text for keyword in HIGH_PRIORITY_KEYWORDS):
        priority = Priority.HIGH
    elif any(keyword in text for keyword in LOW_PRIORITY_KEYWORDS):
        priority = Priority.LOW
    else:
        priority = Priority.MEDIUM

    normalized_details = " ".join(details.split())
    summary = normalized_details[:197] + "..." if len(normalized_details) > 200 else normalized_details

    return AIClassification(
        category=category,
        priority=priority,
        summary=summary,
        recommended_action=RECOMMENDED_ACTIONS[category],
    )
