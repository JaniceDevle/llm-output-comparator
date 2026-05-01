def mock_response(model_name: str, prompt: str) -> str:
    """
    Deterministic mock responses for UI and diff testing.

    This lets us demonstrate the app without spending API credits.
    """

    prompt_lower = prompt.lower()
    model_lower = model_name.lower()

    if "sqlite" in prompt_lower:
        if "reasoner" in model_lower:
            return (
                "SQLite is an embedded database that can work very well for a small web application. "
                "Its advantages are simple deployment, low operational overhead, and good performance for read-heavy workloads. "
                "It is suitable for prototypes, internal tools, and low-traffic services. "
                "However, it can become a poor fit when the application needs high write concurrency, complex user permissions, or horizontal scaling."
            )

        return (
            "SQLite is lightweight and easy to use in small web applications. "
            "It does not require a separate database server, which makes deployment simple. "
            "It works well for prototypes and low-traffic apps. "
            "For large multi-user systems with many concurrent writes, PostgreSQL or MySQL may be a better choice."
        )

    if "python" in prompt_lower:
        if "reasoner" in model_lower:
            return (
                "Python is popular because it optimizes developer productivity. "
                "Its strengths include readable syntax, a large package ecosystem, and strong support for automation, data analysis, and AI. "
                "Its weaknesses include slower runtime speed and occasional dependency-management problems."
            )

        return (
            "Python is readable, productive, and supported by many libraries. "
            "It is commonly used for scripting, backend development, data science, and machine learning. "
            "Compared with compiled languages, it can be slower and packaging can become difficult."
        )

    return (
        f"{model_name} mock answer: This is a generated demo response for the prompt. "
        "It contains some shared ideas and some model-specific phrasing so that the comparison interface can be tested."
    )