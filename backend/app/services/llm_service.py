from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY, GEMINI_MODEL, GEMINI_TIMEOUT_MS, AI_ENABLED


class ProviderUnavailable(Exception):
    pass


class LLMService:
    def generate(self, contents, config=None):
        try:
            if not AI_ENABLED or not GEMINI_API_KEY:
                raise ProviderUnavailable("AI service unavailable; please retry")
            with genai.Client(api_key=GEMINI_API_KEY, vertexai=False,
                              http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS,
                                  retry_options=types.HttpRetryOptions(attempts=1))) as client:
                response = client.models.generate_content(model=GEMINI_MODEL,
                    contents=contents, config=config)
            if not response.text:
                raise ValueError("Empty provider response")
            return response.text.strip()
        except Exception:
            raise ProviderUnavailable("AI service unavailable; please retry") from None

    def generate_response(self, prompt: str) -> str:
        return self.generate(prompt, types.GenerateContentConfig(max_output_tokens=2048))


llm_service = LLMService()
