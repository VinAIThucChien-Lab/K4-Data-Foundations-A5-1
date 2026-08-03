from __future__ import annotations

import argparse
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

from ingest import chunk_document, load_documents
from src import (
    EmbeddingStore,
    FixedSizeChunker,
    KnowledgeBaseAgent,
    LocalEmbedder,
    MockEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    SentenceChunker,
)
from src.demo_chunkers import SonCustomChunker
from src.models import Document


ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
DATA_DIR = ROOT / "data" / "k4_ecommerce"
load_dotenv(ROOT / ".env", override=False)

AVAILABLE_MODELS = [
    {"id": "gpt-4o-mini", "name": "GPT-4o Mini (Nhanh & Tối ưu)", "default": True},
    {"id": "gpt-4o", "name": "GPT-4o (Chính xác cao)"},
    {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
]


def call_openai_chat(prompt: str, model: str = "gpt-4o-mini") -> str:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("OPENAI_API_KEY chưa được cấu hình trong file .env")

    payload_data = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Bạn là trợ lý RAG chuyên nghiệp trả lời các câu hỏi dựa trên cơ sở dữ liệu tài liệu Shopee Returns.\n"
                    "QUY TẮC BẮT BUỘC:\n"
                    "1. CHỈ sử dụng thông tin trong phần Context được cung cấp để trả lời.\n"
                    "2. Nếu câu hỏi không liên quan đến tài liệu hoặc phần Context không chứa câu trả lời cho câu hỏi đó, bạn BẮT BUỘC phải từ chối trả lời và phản hồi chính xác: "
                    "'Xin lỗi, câu hỏi này không có thông tin trong cơ sở dữ liệu chính sách Shopee Returns. Tôi chỉ có thể hỗ trợ giải đáp các thắc mắc về chính sách Trả hàng/Hoàn tiền Shopee.'\n"
                    "3. TỰ ĐỘNG KHÔNG TRẢ LỜI các câu hỏi chung chung, không liên quan như chào hỏi xã giao, thời tiết, tin tức hoặc kiến thức ngoài Context."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        data=payload_data,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            resp_body = json.loads(response.read().decode("utf-8"))
            return resp_body["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8")
        try:
            err_json = json.loads(err_body)
            msg = err_json.get("error", {}).get("message", str(exc))
        except Exception:
            msg = err_body
        raise RuntimeError(f"OpenAI API Error ({exc.code}): {msg}")
    except Exception as exc:
        raise RuntimeError(f"Lỗi kết nối OpenAI API: {exc}")


def rag_chat_payload(
    question: str,
    method: str = "recursive",
    parameters: dict | None = None,
    top_k: int = 3,
    model: str = "gpt-4o-mini",
    document_id: str | None = None,
    custom_text: str | None = None,
) -> dict:
    if not question or not question.strip():
        raise ValueError("Câu hỏi không được để trống")

    parameters = parameters or {}
    chunker = build_chunker(method, parameters)

    # 1. Determine documents to index
    if custom_text and custom_text.strip():
        docs = [Document(id=document_id or "custom-input", content=custom_text, metadata={"title": "Văn bản chỉnh sửa"})]
    else:
        all_docs = load_documents(DATA_DIR)
        if document_id:
            docs = [d for d in all_docs if d.id == document_id]
        else:
            docs = [d for d in all_docs if d.id.startswith("shopee-returns-")]

    if not docs:
        raise ValueError("Không tìm thấy tài liệu nguồn để thực hiện retrieval")

    # 2. Chunk documents
    chunk_docs: list[Document] = []
    for doc in docs:
        chunk_docs.extend(chunk_document(doc, chunker))

    if not chunk_docs:
        raise ValueError("Không tạo được chunk nào từ tài liệu")

    # 3. Embedding store setup
    api_key_configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    if api_key_configured:
        try:
            embedder = OpenAIEmbedder(model_name=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
        except Exception:
            embedder = MockEmbedder()
    else:
        embedder = MockEmbedder()

    store = EmbeddingStore(collection_name="web_rag_chat", embedding_fn=embedder)
    store.add_documents(chunk_docs)

    # 4. KnowledgeBaseAgent execution
    def llm_fn(prompt: str) -> str:
        return call_openai_chat(prompt, model=model)

    agent = KnowledgeBaseAgent(store=store, llm_fn=llm_fn)
    result = agent.answer_with_retrieval(question, top_k=top_k)

    # 5. Format retrieved chunks for frontend inspector
    retrieved = []
    max_score = 0.0
    for item in result["retrieved_chunks"]:
        meta = dict(item.get("metadata", {}))
        score = round(float(item.get("score", 0.0)), 4)
        if score > max_score:
            max_score = score
        retrieved.append({
            "id": item.get("id"),
            "content": item.get("content"),
            "score": score,
            "doc_id": meta.get("doc_id", "unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "title": meta.get("title", meta.get("doc_id", "Tài liệu")),
        })

    # Guard: If max similarity score is below 0.28, enforce refusal message
    final_answer = result["answer"]
    if max_score < 0.28:
        final_answer = "Xin lỗi, câu hỏi này không có thông tin trong cơ sở dữ liệu chính sách Shopee Returns. Tôi chỉ có thể hỗ trợ giải đáp các thắc mắc liên quan đến chính sách Trả hàng/Hoàn tiền Shopee."

    return {
        "question": question,
        "answer": final_answer,
        "model": model,
        "top_k": top_k,
        "method": method,
        "total_chunks_indexed": store.get_collection_size(),
        "retrieved_chunks": retrieved,
    }


def build_chunker(method: str, parameters: dict):
    if method == "fixed":
        return FixedSizeChunker(
            chunk_size=int(parameters.get("chunk_size", 500)),
            overlap=int(parameters.get("overlap", 50)),
        )
    if method == "sentence":
        return SentenceChunker(max_sentences_per_chunk=int(parameters.get("sentences", 3)))
    if method == "recursive":
        return RecursiveChunker(chunk_size=int(parameters.get("chunk_size", 500)))
    if method in {"custom", "structured"}:
        return SonCustomChunker(
            max_chunk_size=int(parameters.get("max_chunk_size", 1000)),
            min_chunk_size=int(parameters.get("min_chunk_size", 50)),
        )
    raise ValueError(f"Unknown chunking method: {method}")


STRATEGIES = [
    {"id": "fixed", "label": "Fixed", "family": "FixedSize", "description": "500 ký tự, overlap 50."},
    {"id": "sentence", "label": "Sentence", "family": "Sentence", "description": "Gộp tối đa 3 câu trong mỗi chunk."},
    {"id": "recursive", "label": "Recursive", "family": "Recursive", "description": "500 ký tự; ưu tiên đoạn, dòng, câu rồi từ."},
    {"id": "custom", "label": "Custom", "family": "Custom", "description": "1000 ký tự; ưu tiên heading, điều khoản, mục đánh số và FAQ."},
]


def runtime_status() -> dict:
    api_key_configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
    return {
        "mode": "openai" if api_key_configured else "local",
        "api_key_configured": api_key_configured,
        "embedding_model": os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
    }


def chunk_payload(text: str, method: str, parameters: dict) -> dict:
    chunks = build_chunker(method, parameters).chunk(text)
    lengths = [len(chunk) for chunk in chunks]
    return {
        "method": method,
        "parameters": parameters,
        "source_length": len(text),
        "source_words": len(text.split()),
        "stats": {
            "count": len(chunks),
            "average": round(sum(lengths) / len(lengths), 2) if lengths else 0,
            "minimum": min(lengths, default=0),
            "maximum": max(lengths, default=0),
        },
        "chunks": [
            {"index": index, "length": len(content), "words": len(content.split()), "content": content}
            for index, content in enumerate(chunks, start=1)
        ],
    }


def corpus_documents() -> list[dict]:
    if not DATA_DIR.exists():
        return []
    return [
        {
            "id": doc.id,
            "title": doc.metadata.get("title", doc.id),
            "content": doc.content,
            "characters": len(doc.content),
            "role": doc.metadata.get("customer_role", "unknown"),
        }
        for doc in load_documents(DATA_DIR)
        if doc.id.startswith("shopee-returns-")
    ]


class ChunkLabHandler(BaseHTTPRequestHandler):
    server_version = "ChunkLab/1.0"

    def do_GET(self) -> None:
        path = unquote(urlparse(self.path).path)
        if path == "/api/documents":
            self.send_json({"documents": corpus_documents()})
            return
        if path == "/api/strategies":
            self.send_json({"strategies": STRATEGIES})
            return
        if path == "/api/models":
            self.send_json({"models": AVAILABLE_MODELS})
            return
        if path == "/api/health":
            self.send_json({"status": "ok", **runtime_status()})
            return
        if path == "/api/status":
            self.send_json(runtime_status())
            return
        self.serve_static(path)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/chunk":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 2_000_000:
                    raise ValueError("Text is too large; maximum request size is 2 MB")
                body = json.loads(self.rfile.read(length) or b"{}")
                text = str(body.get("text", ""))
                if not text.strip():
                    raise ValueError("Text cannot be empty")
                result = chunk_payload(text, str(body.get("method", "recursive")), body.get("parameters") or {})
                self.send_json(result)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        if path == "/api/chat":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length > 2_000_000:
                    raise ValueError("Payload is too large")
                body = json.loads(self.rfile.read(length) or b"{}")
                question = str(body.get("question", ""))
                method = str(body.get("method", "recursive"))
                parameters = body.get("parameters") or {}
                top_k = int(body.get("top_k", 3))
                model = str(body.get("model", "gpt-4o-mini"))
                document_id = body.get("document_id")
                custom_text = body.get("custom_text")

                res = rag_chat_payload(
                    question=question,
                    method=method,
                    parameters=parameters,
                    top_k=top_k,
                    model=model,
                    document_id=document_id,
                    custom_text=custom_text,
                )
                self.send_json(res)
            except Exception as exc:
                self.send_json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
            return

        self.send_error(HTTPStatus.NOT_FOUND)


    def serve_static(self, path: str) -> None:
        clean_path = path.lstrip("/")
        if clean_path in {"chatbot", "chatbot.html"}:
            relative = "chatbot.html"
        else:
            relative = "index.html" if path in {"", "/"} else clean_path
        target = (WEB_DIR / relative).resolve()
        if WEB_DIR.resolve() not in target.parents and target != WEB_DIR.resolve():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        if not target.is_file():
            target = WEB_DIR / "index.html"
        content = target.read_bytes()
        mime = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{mime}; charset=utf-8" if mime.startswith("text/") else mime)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, fmt: str, *args) -> None:
        print(f"[chunk-lab] {self.address_string()} {fmt % args}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the local Chunk Lab web interface")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), ChunkLabHandler)
    print(f"Chunk Lab: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
