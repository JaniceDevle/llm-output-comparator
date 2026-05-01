from __future__ import annotations

import asyncio
import os
import uuid

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from openai import OpenAI


load_dotenv()


SYSTEM_INSTRUCTION = """
You are an assistant in an LLM output comparison application.

Your task is to answer the user's actual question.

Rules:
- Return only the final answer.
- Do not show reasoning steps.
- Do not write planning text such as "we need to answer".
- Do not mention this comparison application.
- Do not mention implementation details.
- Use clear, concise English.
- Prefer a structured answer with short bullet points when appropriate.
- Keep the answer between 120 and 220 words unless the user asks otherwise.
"""


def _safe_agent_name(model_name: str) -> str:
    return (
        "compare_agent_"
        + model_name.replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(":", "_")
    )


def _wrap_prompt(prompt: str) -> str:
    return f"""
Answer the following user question.

Important:
Return only the final answer.
Do not include hidden reasoning, planning, or meta-commentary.
Do not say "we need to answer".
Do not mention model comparison.
Keep the answer concise and useful.

User question:
{prompt}
"""


async def call_adk_agent_async(model_name: str, prompt: str) -> str:
    """
    Call a model through Google ADK + LiteLLM.

    This path is stable for deepseek-chat.
    """

    agent = Agent(
        name=_safe_agent_name(model_name),
        model=LiteLlm(model=model_name),
        description="Produces an answer for an LLM output comparison application.",
        instruction=SYSTEM_INSTRUCTION,
    )

    app_name = "llm_output_comparator"
    user_id = "demo_user"
    session_id = f"session_{uuid.uuid4().hex}"

    session_service = InMemorySessionService()

    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
    )

    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=_wrap_prompt(prompt))],
    )

    final_response = ""

    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=user_message,
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                final_response = event.content.parts[0].text or ""

    return final_response.strip()


def call_deepseek_direct(model_name: str, prompt: str) -> str:
    """
    Call DeepSeek directly through its OpenAI-compatible API.

    This is used for deepseek-reasoner because the final answer is stored
    in message.content while reasoning is stored separately.
    """

    api_key = os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        raise RuntimeError("DEEPSEEK_API_KEY is missing.")

    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com",
    )

    # DeepSeek direct API expects model names without the LiteLLM provider prefix.
    raw_model_name = model_name.replace("deepseek/", "")

    response = client.chat.completions.create(
        model=raw_model_name,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_INSTRUCTION,
            },
            {
                "role": "user",
                "content": _wrap_prompt(prompt),
            },
        ],
        temperature=0.2,
        max_tokens=700,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("DeepSeek returned an empty final answer.")

    return content.strip()


async def call_model_async(model_name: str, prompt: str) -> str:
    """
    Route each model through the most reliable call path.
    """

    if model_name == "deepseek/deepseek-reasoner":
        return await asyncio.to_thread(call_deepseek_direct, model_name, prompt)

    return await call_adk_agent_async(model_name, prompt)


async def call_two_models_async(
    model_a: str,
    model_b: str,
    prompt: str,
) -> tuple[str, str]:
    response_a, response_b = await asyncio.gather(
        call_model_async(model_a, prompt),
        call_model_async(model_b, prompt),
    )

    return response_a, response_b


def call_two_models(
    model_a: str,
    model_b: str,
    prompt: str,
) -> tuple[str, str]:
    return asyncio.run(call_two_models_async(model_a, model_b, prompt))