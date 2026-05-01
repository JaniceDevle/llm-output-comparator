from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AppSettings:
    """Application-level configuration."""

    openai_api_key: str | None
    google_genai_use_vertexai: str
    default_temperature: float
    default_max_tokens: int


def get_settings() -> AppSettings:
    return AppSettings(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        google_genai_use_vertexai=os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "False"),
        default_temperature=float(os.getenv("DEFAULT_TEMPERATURE", "0.2")),
        default_max_tokens=int(os.getenv("DEFAULT_MAX_TOKENS", "700")),
    )