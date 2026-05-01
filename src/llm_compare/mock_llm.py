def mock_response(model_name: str, prompt: str) -> str:
    """
    Deterministic mock responses for UI and diff testing.

    This lets us demonstrate the app without spending API credits.
    """

    prompt_lower = prompt.lower()

    if "sqlite" in prompt_lower:
        if "4.1" in model_name:
            return (
                "SQLite is lightweight and easy to embed in small web applications. "
                "It requires almost no server administration. "
                "It is a good choice for prototypes, local tools, and low-traffic apps. "
                "However, it is not ideal for heavy concurrent writes or complex multi-user workloads."
            )

        return (
            "SQLite is a simple embedded database that works well for small applications. "
            "It is easy to deploy because there is no separate database server. "
            "It is suitable for prototypes and low-traffic web apps. "
            "For high write concurrency or large multi-user systems, PostgreSQL may be safer."
        )

    if "python" in prompt_lower:
        if "4.1" in model_name:
            return (
                "Python is readable, productive, and supported by a large ecosystem. "
                "It is widely used for web development, automation, data analysis, and AI. "
                "Its disadvantages include slower runtime performance and occasional packaging complexity."
            )

        return (
            "Python is popular because it has clear syntax and many libraries. "
            "It is useful for automation, backend services, data science, and machine learning. "
            "Compared with compiled languages, it can be slower and dependency management can become difficult."
        )

    if "climate" in prompt_lower:
        return (
            f"{model_name} mock answer: Climate change is driven mainly by greenhouse gas emissions. "
            "Common mitigation strategies include renewable energy, energy efficiency, electrification, and better land use."
        )

    return (
        f"{model_name} mock answer: This is a generated demo response for the prompt. "
        "It contains some shared ideas and some model-specific phrasing so that the comparison interface can be tested."
    )