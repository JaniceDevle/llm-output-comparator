import pandas as pd
import streamlit as st

from src.llm_compare.adk_client import call_two_models
from src.llm_compare.diff_engine import compare_texts, segments_to_html
from src.llm_compare.mock_llm import mock_response
from src.llm_compare.settings import get_settings


st.set_page_config(
    page_title="LLM Output Comparator",
    page_icon="🤖",
    layout="wide",
)


st.markdown(
    """
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
    min-height: 250px;
}
</style>
""",
    unsafe_allow_html=True,
)


settings = get_settings()

st.title("LLM Output Comparator")

st.caption(
    "Compare two LLM answers and highlight roughly common, partially similar, and different parts."
)


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
        help="Use deterministic fake responses. Useful for demo without API cost.",
    )

    st.divider()

    st.markdown("### Legend")
    st.markdown('<span class="segment agree">Agree</span>', unsafe_allow_html=True)
    st.markdown('<span class="segment partial">Partial</span>', unsafe_allow_html=True)
    st.markdown('<span class="segment disagree">Disagree</span>', unsafe_allow_html=True)


prompt = st.text_area(
    "User prompt",
    value="Explain the pros and cons of using SQLite for a small web application.",
    height=140,
)

run_button = st.button("Compare models", type="primary")


if run_button:
    if not prompt.strip():
        st.error("Please enter a prompt.")
        st.stop()

    if not mock_mode and not settings.deepseek_api_key:
        st.error("DEEPSEEK_API_KEY is missing. Add it to your .env file or enable Mock mode.")
        st.stop()

    with st.spinner("Generating model responses..."):
        try:
            if mock_mode:
                response_a = mock_response(model_a, prompt)
                response_b = mock_response(model_b, prompt)
            else:
                response_a, response_b = call_two_models(model_a, model_b, prompt)
        except Exception as exc:
            error_text = str(exc)

            if "Insufficient Balance" in error_text:
                st.error(
                    "DeepSeek API call failed: insufficient account balance. "
                    "Please recharge the DeepSeek account or enable Mock mode for demo testing."
                )
            elif "authentication" in error_text.lower() or "api key" in error_text.lower():
                st.error(
                    "DeepSeek API authentication failed. "
                    "Please check DEEPSEEK_API_KEY in the .env file."
                )
            elif "model" in error_text.lower():
                st.error(
                    "Model call failed. Please check that the model names are valid, "
                    "for example deepseek/deepseek-chat and deepseek/deepseek-reasoner."
                )
            else:
                st.error("Model call failed. See technical details below.")
                with st.expander("Technical error details"):
                    st.exception(exc)

            st.stop()

    comparison = compare_texts(response_a, response_b)

    st.subheader("Agreement score")
    st.metric("Approximate agreement", f"{comparison.agreement_score:.1%}")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(f"### {model_a}")
        st.markdown(
            f'<div class="output-box">{segments_to_html(comparison.left_segments)}</div>',
            unsafe_allow_html=True,
        )

    with col_b:
        st.markdown(f"### {model_b}")
        st.markdown(
            f'<div class="output-box">{segments_to_html(comparison.right_segments)}</div>',
            unsafe_allow_html=True,
        )

    st.subheader("Alignment details")

    details_df = pd.DataFrame(comparison.details)
    st.dataframe(details_df, use_container_width=True)

    with st.expander("Raw model outputs"):
        st.markdown(f"#### {model_a}")
        st.write(response_a)

        st.markdown(f"#### {model_b}")
        st.write(response_b)

else:
    st.info("Enter a prompt and click Compare models.")