from google import genai
from google.genai import types

from .models import Candidate
from .prompts import SYSTEM_PROMPT, USER_PROMPT

from aiohttp import ClientSession

async def verify_gemini_api_key(api_key):
    API_VERSION = 'v1'
    api_url = f'https://generativelanguage.googleapis.com/{API_VERSION}/models'
    
    headers = {
        'Content-Type': 'application/json',
        'x-goog-api-key': api_key,
    }
    
    async with ClientSession() as session:
        async with session.get(api_url, headers=headers) as response:
            if response.status != 200:
                error_message = (await response.json()).get('error', {}).get('message', 'Invalid API key')
                raise Exception(error_message)
            return True

async def get_candidate_info(
    cv_text: str,
    jd_text: str,
    client: genai.Client,
    model: str,
    temperature: float,
) -> Candidate:
    """
    Get candidate information from Gemini.
    """
    
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=Candidate,
        temperature=temperature,
        system_instruction=SYSTEM_PROMPT,
    )

    contents = USER_PROMPT.format(
        cv_text=cv_text,
        jd_text=jd_text,
    )

    response = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=config,
    )

    return response.parsed