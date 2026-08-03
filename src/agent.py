from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        res = self.answer_with_retrieval(question, top_k=top_k)
        return res["answer"]

    def answer_with_retrieval(self, question: str, top_k: int = 3) -> dict:
        results = self.store.search(question, top_k=top_k)
        context = "\n\n".join(
            f"[Context {index}]\n{result['content']}"
            for index, result in enumerate(results, start=1)
        )
        if not context:
            context = "No relevant context was found."

        prompt = (
            "Dưới đây là các đoạn văn bản (Context) được trích xuất từ cơ sở dữ liệu chính sách:\n\n"
            f"{context}\n\n"
            f"Câu hỏi của người dùng: {question}\n\n"
            "Yêu cầu:\n"
            "- Trả lời câu hỏi DỰA HOÀN TOÀN vào phần Context ở trên.\n"
            "- Nếu thông tin trong Context không chứa câu trả lời cho câu hỏi này hoặc câu hỏi không liên quan, hãy từ chối trả lời và thông báo không tìm thấy thông tin trong cơ sở dữ liệu."
        )
        answer_text = self.llm_fn(prompt)
        return {
            "answer": answer_text,
            "retrieved_chunks": results,
            "prompt": prompt,
        }

