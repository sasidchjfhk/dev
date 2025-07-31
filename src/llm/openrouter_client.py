import requests
import logging
from src.config import Config

logger = logging.getLogger(__name__)

class OpenRouter:
    def __init__(self):
        config = Config()
        self.api_key = config.config['API_KEYS'].get('OPENROUTER') or config.config['API_KEYS'].get('OPENROUTER_API_KEY')
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"
        if not self.api_key:
            raise ValueError("OpenRouter API key not found in config.toml [API_KEYS] section.")

    def inference(self, model_id: str, prompt: str) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model_id,
            "messages": [
                {"role": "user", "content": prompt.strip()}
            ],
            "max_tokens": 512  # Lowered to fit free-tier allowance
        }
        try:
            logger.info(f"Sending request to OpenRouter: {data}")
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=10  # 10-second timeout
            )
            logger.info(f"OpenRouter response status: {response.status_code}")
            logger.info(f"OpenRouter response: {response.text}")
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            logger.error(f"OpenRouter API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response content: {e.response.text}")
            raise
