# Hướng dẫn crawl dữ liệu Shopee

Chạy từ thư mục gốc repository:

```bash
uv sync
uv run python data/crawl_data.py
uv run python data/preprocess.py
```

Mặc định, script tải 7 bài viết công khai về chính sách Trả hàng / Hoàn tiền từ Trung tâm trợ giúp Shopee Việt Nam.

Dữ liệu HTML và metadata nguồn được lưu tại:

```text
.crawl_cache/shopee-returns/
```

Thư mục `.crawl_cache/` đã được thêm vào `.gitignore` và không được commit lên repository.

## Crawl URL khác

Dùng `--url` nhiều lần để crawl danh sách bài viết riêng:

```bash
uv run python data/crawl_data.py \
  --url "https://help.shopee.vn/portal/4/article/ARTICLE_ID_1" \
  --url "https://help.shopee.vn/portal/4/article/ARTICLE_ID_2"
```

Các tùy chọn:

```text
--output-dir PATH   Thư mục lưu HTML và metadata
--delay SECONDS     Thời gian chờ giữa các request, tối thiểu 1 giây
--timeout SECONDS   Thời gian chờ tối đa cho mỗi request
```

Ví dụ:

```bash
uv run python data/crawl_data.py --delay 2 --timeout 45
```

Crawler kiểm tra `robots.txt`, dùng User-Agent của lớp và chỉ tải các trang công khai. Không sử dụng script cho nội dung yêu cầu đăng nhập, CAPTCHA hoặc nguồn không cho phép crawl.

## Chạy benchmark sau khi xử lý dữ liệu

Sau khi đã có các file Markdown trong `data/k4_ecommerce/`, mọi thành viên dùng cùng 5 query trong `benchmark_queries.py` nhưng thay đổi chunker/parameter của mình:

```bash
uv run --group local python - <<'PY'
from data.benchmark_queries import BENCHMARK_QUERIES
from ingest import build_knowledge_base
from src import LocalEmbedder, RecursiveChunker

embedder = LocalEmbedder()
store = build_knowledge_base(
    "data/k4_ecommerce",
    embedding_fn=embedder,
    chunker=RecursiveChunker(chunk_size=500),
    collection_name="benchmark-recursive-500",
)

for item in BENCHMARK_QUERIES:
    results = store.search_with_filter(
        item["query"],
        top_k=3,
        metadata_filter=item["metadata_filter"],
    )
    print(f"\n{item['id']}: {item['query']}")
    for rank, result in enumerate(results, 1):
        print(
            f"{rank}. score={result['score']:.4f} "
            f"doc={result['metadata'].get('doc_id')}"
        )
        print(result["content"][:300].replace("\n", " "))
PY
```

Mỗi thành viên nên đổi `chunker`, `chunk_size`, `overlap` hoặc chunker tùy chỉnh, nhưng giữ nguyên 5 query. Ghi lại top-3, score, chunk liên quan và mức độ đúng với `gold_answer` trong `REPORT_CANHAN.md`; nhóm tổng hợp kết quả vào `REPORT_NHOM.md`.
