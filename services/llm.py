import os

from dotenv import load_dotenv
from google import genai

load_dotenv()

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Create one long-lived Gemini client after configuration is available."""
    global _client

    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured")
        _client = genai.Client(api_key=api_key)

    return _client


def generate_document_summary(full_text: str) -> str:
    """Generate a structured summary in the document's primary language."""
    prompt = f"""You are an expert multilingual document analyst. Provide a comprehensive, clear, and well-structured summary of the following document.
Write the summary in the primary language of the document (e.g. Vietnamese if the document is in Vietnamese, English if the document is in English).

Format your response in Markdown with:
- **Executive Overview / Tổng quan**: A concise 2-3 sentence overview of what the document is and its primary objective.
- **Key Findings & Main Points / Các điểm chính**: Bullet points highlighting critical concepts, data, facts, or findings.
- **Conclusions & Action Items / Kết luận & Hành động**: Key takeaways, recommendations, or conclusions outlined in the text.

Document Content:
{full_text}

Structured Summary:"""

    response = get_client().models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )
    return response.text


def generate_answer(question: str, context_chunks: list) -> str:
    context = "\n\n".join(context_chunks)
    prompt = f"""You are a helpful, intelligent, and accurate multilingual AI assistant for document intelligence.
Answer the user's question accurately using the provided context from their uploaded documents.

Guidelines:
1. Always reply in the same language as the user's question.
2. When the user uses first-person pronouns, they are referring to themselves as the subject of their uploaded document.
3. Extract and synthesise relevant skills, projects, experience, and other details from the context.
4. If the answer cannot be deduced from the context, state clearly that the information is not mentioned in the documents.

Context:
{context}

Question: {question}

Answer:"""

    response = get_client().models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )
    return response.text
