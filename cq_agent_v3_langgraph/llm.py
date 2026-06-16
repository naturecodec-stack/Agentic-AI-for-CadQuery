import os
from google import genai
from google.genai import types

_client = None


def get_client(api_key: str):
    global _client
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client


def call_llm(api_key: str, model: str, system_prompt: str,
             user_prompt: str, image_path: str = "") -> str:
    client = get_client(api_key)

    if image_path and os.path.exists(image_path):
        with open(image_path, "rb") as f:
            image_bytes = f.read()
        ext = os.path.splitext(image_path)[1].lower()
        mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                    ".png": "image/png", ".webp": "image/webp"}
        mime_type = mime_map.get(ext, "image/png")
        contents = [
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            types.Part.from_text(text=user_prompt),
        ]
    else:
        contents = user_prompt

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            max_output_tokens=4096,
        ),
    )
    return response.text.strip()
