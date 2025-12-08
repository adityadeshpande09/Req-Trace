#     entities, relationships = nlp_service.process_conversation(convo.text)
#     neo4j_service.add_entities_and_relationships(entities, relationships)
#     return {"entities": entities, "relationships": relationships}

# app/api/v1/routes_conversation.py

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel
import os
import app.services.vector_service as vector_service
from dotenv import load_dotenv
from openai import OpenAI

# ✅ Load environment variables before creating client
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

print(f"✅ Loaded .env from: {os.path.abspath(dotenv_path)}")
# Replace line 19 in app/api/v1/routes_conversation.py with:

api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ OPENAI_API_KEY starts with: {api_key[:10]}")
else:
    print("⚠️  OPENAI_API_KEY is not set")
    
# ✅ Initialize OpenAI client using loaded API key
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

router = APIRouter()



@router.post("/chat")
async def chat_with_context(payload: dict = Body(...)):
    """
    Handles chat queries using FAISS context + OpenAI (new SDK).
    """
    try:
        query = payload.get("query", "")
        if not query:
            raise HTTPException(status_code=400, detail="Query text is required.")

        # 🔍 Retrieve similar transcript chunks from FAISS
        similar_chunks = vector_service.search_similar_transcripts(query)
        context_text = "\n\n".join(
            [chunk["text"] for chunk in similar_chunks]
        )

        # 🧠 Build prompt
        prompt = f"""
        You are a helpful assistant analyzing transcriptions.
        Use the provided context to answer the user's question concisely.
        
        CONTEXT:
        {context_text}

        QUESTION:
        {query}
        """

        # 💬 New OpenAI client interface
        try:
            completion = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a transcript analysis assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            answer = completion.choices[0].message.content.strip()
        except Exception as openai_error:
            # Handle OpenAI API errors (rate limits, etc.)
            error_msg = str(openai_error)
            if "rate limit" in error_msg.lower() or "429" in error_msg:
                raise HTTPException(
                    status_code=503,
                    detail="OpenAI API rate limit exceeded. Please try again in a moment."
                )
            elif "authentication" in error_msg.lower() or "401" in error_msg:
                raise HTTPException(
                    status_code=500,
                    detail="OpenAI API authentication error. Please check API key configuration."
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"OpenAI API error: {error_msg}"
                )

        # Identify which files were used (for user feedback)
        files_analyzed = []
        conversation_ids_used = set()
        for chunk in similar_chunks:
            filename = chunk.get("filename", "Unknown")
            conv_id = chunk.get("conversation_id")
            if filename not in files_analyzed:
                files_analyzed.append(filename)
            if conv_id:
                conversation_ids_used.add(conv_id)

        return {
            "query": query,
            "answer": answer,
            "context_used": similar_chunks,
            "files_analyzed": files_analyzed,
            "conversation_count": len(conversation_ids_used),
        }

    except Exception as e:
        import traceback
        traceback.print_exc()  # 🔥 prints the full stack trace to your terminal
        raise HTTPException(status_code=500, detail=str(e))

