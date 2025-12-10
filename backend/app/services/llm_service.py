from openai import OpenAI
from app.core.config import settings
import os

# Fallback to environment variable if settings not loaded
api_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key) if api_key else None

def extract_entities_and_relationships(text: str):
    if client is None:
        raise RuntimeError("OpenAI API key not configured. Please set OPENAI_API_KEY in your .env file.")
    
    prompt = f"""
    You are a requirements engineer. Extract the following from the conversation:
    - Entities: features, stakeholders, constraints
    - Relationships: DEPENDS_ON, IMPACTS, CONTAINS, CONFLICTS_WITH
    Return JSON with keys: entities and relationships.
    Text: {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "Extract structured information."},
                  {"role": "user", "content": prompt}]
    )

    try:
        result = response.choices[0].message.content
        return result
    except Exception as e:
        print("Error:", e)
        return {"entities": [], "relationships": []}
