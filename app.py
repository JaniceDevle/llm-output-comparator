from __future__ import annotations

from datetime import datetime

import pandas as pd
import streamlit as st

from src.llm_compare.diff_engine import compare_texts, segments_to_html
from src.llm_compare.mock_llm import mock_response
from src.llm_compare.settings import get_settings


st.set_page_config(
    page_title="LLM Output Comparator",
    page_icon="🤖",
    layout="wide",
)


CSS = """
<style>
.segment {
    display: inline-block;
    padding: 0.15rem 0.25rem;
    margin: 0.08rem;
    border-radius: 0.35rem;
    line-height: 1.6;
}

.agree {
    background-color: #d1fae5;
    border: 1px solid #10b981;
}

.partial {
    background-color: #fef3c7;
    border: 1px solid #f59e0b;
}

.disagree {
    background-color: #fee2e2;
    border: 1px solid #ef4444;
}

.output-box {
    border: 1px solid #dddddd;
    border-radius: 0.5rem;
    padding: 1rem;
    background-color: #ffffff;
    min-height: 260px;
}

.status-box {
    border: 1px solid #e5e7eb;
    border-radius: 0.5rem;
    padding: 0.85rem 1rem;
    background-color: #f9fafb;
    margin-bottom: 1rem;
}

.status-good {
    color: #065f46;
    font-weight: 600;
}

.status-warn {
    color: #991b1b;
    font-weight: 600;
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)


def escape_markdown_table_cell(value: object) -> str:
    """Escape values for a simple Markdown table."""
    text = str(value).replace("\n", " ").replace("|", "\\|")
    return text


def details_to_markdown_table(details: list[dict]) -> str:
    """Convert alignment details into a Markdown table without requiring tabulate."""
    if not details:
        return "_No alignment details available._"

    headers = ["left", "best_right_match", "score", "status"]
    rows = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]

    for row in details:
        rows.append(
            "| "
            + " | ".join(escape_markdown_table_cell(row.get(header, "")) for header in headers)
            + " |"
        )

    return "\n".join(rows)


def build_markdown_report(
    prompt: str,
    model_a: str,
    model_b: str,
    response_a: str,
    response_b: str,
    agreement_score: float,
    details: list[dict],
    mock_mode: bool,
) -> str:
    """Create a downloadable Markdown report."""

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_mode = "Mock mode" if mock_mode else "Real API mode"

    parts = [
        "# LLM Output Comparison Report",
        "",
        f"Generated at: {timestamp}",
        "",
        f"Run mode: {run_mode}",
        "",
        "## Prompt",
        "",
        "```text",
        prompt,
        "```",
        "",
        "## Models",
        "",
        f"- Model A: `{model_a}`",
        f"- Model B: `{model_b}`",
        "",
        "## Agreement Score",
        "",
        f"{agreement_score:.1%}",
        "",
        "## Model A Output",
        "",
        "```text",
        response_a,
        "```",
        "",
        "## Model B Output",
        "",
        "```text",
        response_b,
        "```",
        "",
        "## Alignment Details",
        "",
        details_to_markdown_table(details),
        "",
        "## Color Legend",
        "",
        "- Green: roughly common content / agreement",
        "- Yellow: partially similar content",
        "- Red: different or unmatched content",
        "",
    ]

    return "\n".join(parts)


def interpret_score(score: float) -> str:
    """Return a short explanation for the agreement score."""
    if score >= 0.75:
        return "High agreement: the two answers cover very similar content."
    if score >= 0.45:
        return "Medium agreement: the answers overlap, but each model also adds different points."
    return "Low agreement: the answers differ substantially or use very different structure."


def generate_responses(
    model_a: str,
    model_b: str,
    prompt: str,
    mock_mode: bool,
) -> tuple[str, str]:
    """
    Generate two model responses.

    Important design choice:
    Google ADK is imported lazily only when Real API mode is used.
    This keeps the Streamlit UI fast and avoids startup white-screen issues.
    """
    if mock_mode:
        return (
            mock_response(model_a, prompt),
            mock_response(model_b, prompt),
        )

    from src.llm_compare.adk_client import call_two_models

    return call_two_models(model_a, model_b, prompt)


settings = get_settings()

if "last_result" not in st.session_state:
    st.session_state.last_result = None


with st.sidebar:
    st.header("Model settings")

    model_options = [
        "deepseek/deepseek-chat",
        "deepseek/deepseek-reasoner",
    ]

    model_a = st.selectbox("Model A", model_options, index=0)
    model_b = st.selectbox("Model B", model_options, index=1)

    mock_mode = st.toggle(
        "Mock mode",
        value=True,
        help="Use deterministic local responses without calling the real API.",
    )

    st.divider()

    st.markdown("### Run status")

    if mock_mode:
        st.markdown("Mode: **Mock**")
    else:
        st.markdown("Mode: **Real API**")

    if settings.deepseek_api_key:
        st.markdown("API key: **Detected**")
    else:
        st.markdown("API key: **Missing**")

    st.divider()

    st.markdown("### Legend")
    st.markdown('<span class="segment agree">Agree</span>', unsafe_allow_html=True)
    st.markdown('<span class="segment partial">Partial</span>', unsafe_allow_html=True)
    st.markdown('<span class="segment disagree">Disagree</span>', unsafe_allow_html=True)

    st.divider()

    st.markdown("### Suggested prompts")

    selected_prompt = st.selectbox(
        "Choose an example",
        [
            "Give three advantages and three disadvantages of SQLite for a small web app.",
            "Compare REST APIs and GraphQL for a small startup project.",
            "Explain the risks and benefits of using generative AI in education.",
            "Summarize the pros and cons of microservices for a medium-sized company.",
        ],
    )


st.title("LLM Output Comparator")

st.caption(
    "Compare two LLM answers side by side and highlight where they agree, partially overlap, or disagree."
)

if mock_mode:
    st.markdown(
        """
<div class="status-box">
<span class="status-good">Current mode: Mock mode.</span><br>
The app uses deterministic local responses. This is useful for demos, development, and avoiding API cost.
</div>
""",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        """
<div class="status-box">
<span class="status-warn">Current mode: Real API mode.</span><br>
The app will call external LLM APIs. This may take longer and may consume API credits.
</div>
""",
        unsafe_allow_html=True,
    )

with st.expander("How the comparison works"):
    st.write(
        "The app splits both model outputs into readable chunks, aligns each chunk with the most similar "
        "chunk from the other answer, and computes an approximate similarity score."
    )
    st.markdown(
        """
- **Green**: high similarity / agreement
- **Yellow**: partial similarity
- **Red**: low similarity or unmatched content
"""
    )

prompt = st.text_area(
    "User prompt",
    value=selected_prompt,
    height=140,
)

run_button = st.button("Compare models", type="primary")


if run_button:
    if not prompt.strip():
        st.error("Please enter a prompt.")
        st.stop()

    if model_a == model_b:
        st.warning("You selected the same model twice. The comparison will still run, but it may be less informative.")

    if not mock_mode and not settings.deepseek_api_key:
        st.error("DEEPSEEK_API_KEY is missing. Add it to your .env file or enable Mock mode.")
        st.stop()

    with st.spinner("Generating model responses..."):
        try:
            response_a, response_b = generate_responses(
                model_a=model_a,
                model_b=model_b,
                prompt=prompt,
                mock_mode=mock_mode,
            )

        except Exception as exc:
            error_text = str(exc)

            if "Insufficient Balance" in error_text:
                st.error(
                    "DeepSeek API call failed: insufficient account balance. "
                    "Recharge the DeepSeek account or enable Mock mode for testing."
                )
            elif "authentication" in error_text.lower() or "api key" in error_text.lower():
                st.error(
                    "DeepSeek API authentication failed. "
                    "Check DEEPSEEK_API_KEY in the .env file."
                )
            elif "model" in error_text.lower():
                st.error(
                    "Model call failed. Check that model names are valid, for example "
                    "deepseek/deepseek-chat and deepseek/deepseek-reasoner."
                )
            else:
                st.error("Model call failed. Technical details:")
                st.exception(exc)

            st.stop()

    comparison = compare_texts(response_a, response_b)

    st.session_state.last_result = {
        "prompt": prompt,
        "model_a": model_a,
        "model_b": model_b,
        "response_a": response_a,
        "response_b": response_b,
        "comparison": comparison,
        "mock_mode": mock_mode,
    }


if st.session_state.last_result is None:
    st.info("Enter a prompt and click Compare models.")
else:
    result = st.session_state.last_result

    result_prompt = result["prompt"]
    result_model_a = result["model_a"]
    result_model_b = result["model_b"]
    response_a = result["response_a"]
    response_b = result["response_b"]
    comparison = result["comparison"]
    result_mock_mode = result["mock_mode"]

    st.subheader("Agreement score")

    score_col, explanation_col = st.columns([1, 3])

    with score_col:
        st.metric("Approximate agreement", f"{comparison.agreement_score:.1%}")

    with explanation_col:
        st.markdown(
            f"""
<div class="status-box">
<strong>Interpretation:</strong><br>
{interpret_score(comparison.agreement_score)}
</div>
""",
            unsafe_allow_html=True,
        )

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### {result_model_a}")
        st.markdown(
            f'<div class="output-box">{segments_to_html(comparison.left_segments)}</div>',
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(f"### {result_model_b}")
        st.markdown(
            f'<div class="output-box">{segments_to_html(comparison.right_segments)}</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Alignment details")

    details_df = pd.DataFrame(comparison.details)
    st.dataframe(details_df, use_container_width=True)

    report = build_markdown_report(
        prompt=result_prompt,
        model_a=result_model_a,
        model_b=result_model_b,
        response_a=response_a,
        response_b=response_b,
        agreement_score=comparison.agreement_score,
        details=comparison.details,
        mock_mode=result_mock_mode,
    )

    st.download_button(
        label="Download comparison report as Markdown",
        data=report,
        file_name="llm_comparison_report.md",
        mime="text/markdown",
    )

    with st.expander("Raw model outputs"):
        st.markdown(f"#### {result_model_a}")
        st.write(response_a)

        st.markdown(f"#### {result_model_b}")
        st.write(response_b)