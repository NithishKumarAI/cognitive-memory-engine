import google.generativeai as genai

from app.core.config import GEMINI_API_KEY


genai.configure(api_key=GEMINI_API_KEY)


class LLMService:
    def __init__(self):
        self.model = genai.GenerativeModel(
            "gemini-2.5-flash"
        )

    def generate_response(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)

        return response.text.strip()


llm_service = LLMService()