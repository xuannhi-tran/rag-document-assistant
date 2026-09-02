from google import genai
import os
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_document_summary(full_text: str) -> str:
    """
    Generates a structured executive summary from the full extracted text of a document.
    Outputs in the same language as the document (English or Vietnamese).
    """
    prompt = f"""You are an expert multilingual document analyst. Provide a comprehensive, clear, and well-structured summary of the following document.
Write the summary in the primary language of the document (e.g. Vietnamese if the document is in Vietnamese, English if the document is in English).

Format your response in Markdown with:
- **Executive Overview / Tổng quan**: A concise 2-3 sentence overview of what the document is and its primary objective.
- **Key Findings & Main Points / Các điểm chính**: Bullet points highlighting critical concepts, data, facts, or findings.
- **Conclusions & Action Items / Kết luận & Hành động**: Key takeaways, recommendations, or conclusions outlined in the text.

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

    prompt = f"""You are a helpful, intelligent, and accurate multilingual AI assistant for document intelligence.
Answer the user's question accurately using the provided context from their uploaded documents.

Guidelines:
1. Always reply in the same language as the user's question (e.g., reply in fluent, natural Vietnamese if asked in Vietnamese, English if asked in English).
2. When the user uses first-person pronouns (e.g., 'tôi', 'của tôi', 'I', 'me', 'my'), they are referring to themselves as the subject of their uploaded document (e.g., the candidate/applicant in a CV or resume, the student in an academic record, or the tenant in an agreement).
3. If the user asks about programming languages ('ngôn ngữ lập trình'), tools, technical skills ('công nghệ / kĩ năng'), projects, or experience, extract and synthesize all relevant details from the context.
4. If the user asks generally about languages ('ngôn ngữ gì'), clarify and provide both spoken languages (e.g., Vietnamese, English IELTS 7.5) and programming languages (Python, Java, etc.) found in the document.
5. Only if the answer cannot be deduced or found in the context, state clearly (in the user's language) that the information is not mentioned in the documents.

Context:
{context}

Question: {question}

Answer:"""


    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt
    )
    return response.text

