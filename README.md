# LLM Output Comparator

A Streamlit demo application for comparing the outputs of two large language models.

The user enters a prompt and selects two models. The application generates both model responses, displays them side by side, and highlights parts that are approximately common, partially similar, or different.

## Features

- Select two LLM models from the sidebar
- Generate both responses from the same user prompt
- Display the responses side by side
- Highlight agreement, partial similarity, and disagreement
- Show an approximate agreement score
- Show an alignment details table
- Support mock mode for offline or low-cost demonstration
- Support real model calls through Google ADK, LiteLLM, and DeepSeek API

## Technology

- Python
- Streamlit
- Google ADK
- LiteLLM
- DeepSeek API
- OpenAI-compatible SDK for DeepSeek reasoner handling
- pytest

## Model calling design

The normal model call path uses Google ADK with LiteLLM.

For `deepseek/deepseek-chat`, the application calls the model through:

```text
Streamlit -> Google ADK Agent -> LiteLLM -> DeepSeek API