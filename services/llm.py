from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_answer(question: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)

    prompt = f"""Answer the question based only on the context below.
If the answer cannot be found in the context, say that the information is not available in the document.

Context:
{context}

Question: {question}

Answer:"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    return response.text