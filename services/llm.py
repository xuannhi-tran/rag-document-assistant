from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_document_summary(full_text: str) -> str:
    """
    Generates a structured executive summary from the full extracted text of a document.
    """
    prompt = f"""You are an expert document analyst. Provide a comprehensive, clear, and well-structured summary of the following document.

Format your response in Markdown with:
- **Executive Overview**: A concise 2-3 sentence overview of what the document is and its primary objective.
- **Key Findings & Main Points**: Bullet points highlighting the critical concepts, data, facts, or findings.
- **Conclusions / Action Items**: Key takeaways, recommendations, or conclusions outlined in the text.

Document Content:
{full_text}

Structured Summary:"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    return response.text


def generate_answer(question: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)

    prompt = f"""You are a helpful and accurate AI assistant. Answer the user's question based on the provided context below.
If the answer cannot be found or deduced from the context, state clearly that the information is not mentioned in the document.

Context:
{context}

Question: {question}

Answer:"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    return response.text