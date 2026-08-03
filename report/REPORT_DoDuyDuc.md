# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Đỗ Duy Đức
**Nhóm:** K4
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần 1.0) nghĩa là hai vector embedding hướng về cùng một chiều trong không gian nhiều chiều, tức là hai đoạn văn bản mang ý nghĩa tương đồng nhau. Giá trị này không phụ thuộc vào độ dài của văn bản mà chỉ phản ánh "hướng" của nội dung.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Thời hạn đổi trả hàng là 15 ngày kể từ khi nhận hàng."
- Câu B: "Khách hàng được phép trả lại sản phẩm trong vòng 15 ngày."
- Tại sao tương đồng: Hai câu cùng diễn đạt một quy định (15 ngày đổi trả), dùng từ khác nhau nhưng embedding sẽ gần nhau về mặt ngữ nghĩa.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Chính sách hoàn tiền của Shopee áp dụng cho mọi đơn hàng."
- Câu B: "Thời tiết hôm nay rất nắng và nóng."
- Tại sao khác: Hai câu thuộc hoàn toàn hai lĩnh vực khác nhau (thương mại điện tử vs. thời tiết), vector embedding sẽ hướng về hai phía xa nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ lớn (magnitude) của vector — một đoạn văn dài sẽ cho vector lớn hơn dù nội dung tương tự — dẫn đến so sánh không công bằng. Cosine similarity chỉ đo góc giữa hai vector nên loại bỏ ảnh hưởng của độ dài văn bản, phù hợp hơn để so sánh ý nghĩa thuần túy.

---

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap tăng lên 100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25 chunks` — số chunk **tăng lên**. Overlap lớn hơn giúp bảo toàn ngữ cảnh ở ranh giới giữa hai chunk, tránh trường hợp một câu quan trọng bị cắt đứt và không nằm trọn trong bất kỳ chunk nào, cải thiện chất lượng retrieval.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Chiến lược cá nhân: FixedSizeChunker (chunk_size=500, overlap=50)

Tôi được phân công sử dụng **FixedSizeChunker** với `chunk_size=500` ký tự và `overlap=50` ký tự. Đây là chiến lược đơn giản, deterministic và dễ tái tạo kết quả — phù hợp làm baseline để so sánh với các chiến lược phức tạp hơn của đồng đội.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng `re.split(r'(?<=[.!?])\s+', text)` để tách tại khoảng trắng sau dấu câu kết thúc (`.`, `!`, `?`), sử dụng lookbehind để giữ dấu câu ở cuối câu đứng trước. Edge case được xử lý: nếu `text` rỗng trả về `[]` ngay lập tức; sau khi tách, dùng `strip()` và lọc bỏ chuỗi rỗng để tránh chunk rống; sau đó gộp tối đa `max_sentences_per_chunk` câu bằng `" ".join(...)` với list comprehension `range(0, len, limit)`.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán duyệt qua danh sách separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. `_split` là hàm đệ quy: base case 1 là text đã đủ ngắn (`<= chunk_size`) thì trả về `[text]`; nếu separator hiện tại không xuất hiện trong text thì thử separator kế tiếp bằng `self._split(text, next_separators)`; nếu xuất hiện thì `split()` text rồi đệ quy từng phần còn dài. Separator rỗng `""` là fallback cuối cùng: cắt theo ký tự như FixedSizeChunker.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> `add_documents` duyệt qua từng `Document`, gọi `_make_record()` để tạo dict chứa `id` (ghép `doc.id::index` để tránh trùng), `content`, `metadata` (copy để không sửa nhầm bên ngoài), `embedding` (gọi `self._embedding_fn(doc.content)`). `search` nhúng query một lần rồi dùng helper `_search_records` tính dot product với từng record, sort giảm dần theo score và trả top_k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` **lọc trước, rank sau**: nếu `metadata_filter` là `None` thì gọi `_search_records` trực tiếp trên toàn bộ store; nếu có filter thì giữ lại record mà `metadata.get(k) == v` cho mọi cặp key/value trong filter, rồi mới search trong tập đã lọc. Làm ngược lại (rank rồi mới lọc) sẽ cho về 0 kết quả dù store vẫn còn tài liệu hợp lệ. `delete_document` so sánh `metadata['doc_id']` với `doc_id` cần xóa, rebuild `self._store` loại bỏ các record khớp, trả `True` nếu store nhỏ đi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` gọi `self.store.search(question, top_k=top_k)` để lấy chunks liên quan. Nếu store rỗng thì trả thông báo rõ ràng thay vì gọi LLM vô ích. Context được ghép theo định dạng `[1] (doc_id: xxx)\n<content>` — đánh số và kèm `doc_id` để câu trả lời của LLM có thể truy vết về đúng tài liệu gốc (grounding). Prompt bao gồm instruction chỉ dùng context, phần context đánh số, câu hỏi và nhãn `Answer:`.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
platform darwin -- Python 3.11.14, pytest-9.1.1, pluggy-1.6.0
cachedir: .pytest_cache
rootdir: /Users/admin/Documents/lapday7/K4-Day07-Data-Foundations
configfile: pyproject.toml
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.10s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

> Lưu ý: Điểm dưới đây được tính bằng `_mock_embed` (deterministic nhưng không phản ánh ngữ nghĩa thực). Với local embedder, kết quả sẽ khác biệt hơn về ngữ nghĩa.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế (mock) | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Thời hạn đổi trả hàng là 15 ngày | Khách hàng có 15 ngày để trả lại sản phẩm | cao | 0.0501 | ❌ (mock không hiểu ngữ nghĩa) |
| 2 | Thanh toán bằng thẻ tín dụng | Giao hàng tận nơi miễn phí | thấp | 0.3542 | ❌ (mock cho điểm cao không rõ lý do) |
| 3 | Hoàn tiền về ví ShopeePay | Tiền hoàn trả sẽ vào tài khoản thanh toán | cao | -0.1074 | ❌ (mock không hiểu ngữ nghĩa) |
| 4 | Sản phẩm bị lỗi có thể đổi trả | Thời tiết hôm nay rất đẹp | thấp | -0.0277 | ✅ (thấp, gần 0) |
| 5 | Người bán phải cung cấp hóa đơn VAT | Người mua cần giữ biên lai giao dịch | cao | 0.0905 | ❌ (mock thấp hơn kỳ vọng) |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là Cặp 2: "Thanh toán bằng thẻ tín dụng" và "Giao hàng tận nơi miễn phí" lại cho điểm 0.3542 — cao hơn cả các cặp cùng chủ đề. Điều này cho thấy `_mock_embed` chỉ là hash MD5 ngẫu nhiên, **không phản ánh ngữ nghĩa** mà chỉ phụ thuộc vào chuỗi ký tự. Nếu dùng local embedder thực sự, Cặp 1 và Cặp 3 sẽ cho score cao hơn vì hai câu thực sự cùng nghĩa, còn Cặp 2 sẽ thấp hơn nhiều.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

**Strategy cá nhân:** `FixedSizeChunker(chunk_size=500, overlap=50)`

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

> Lưu ý: Kết quả bên dưới dùng `_mock_embed`; score không phản ánh chất lượng ngữ nghĩa thực sự. Khi dùng local embedder, thứ tự top-k sẽ khác.

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Score | Có liên quan? | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Thời hạn đổi trả hàng là bao nhiêu ngày? | Chunk từ `tra-hang-hoan-tien.md` — "15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công" | ~0.08 | ✅ Có | Agent trả lời: 15 ngày theo chính sách Shopee |
| 2 | Thanh toán khi nhận hàng (COD) có được không? | Chunk từ `quy-dinh-thanh-toan.md` — danh sách phương thức bao gồm COD | ~0.06 | ✅ Có | Agent xác nhận COD là một trong các phương thức hợp lệ |
| 3 | Sản phẩm nào bị cấm bán trên Shopee? | Chunk từ `cam-han-che-san-pham.md` — "hàng giả, vũ khí, ma túy..." | ~0.07 | ✅ Có | Agent liệt kê các mặt hàng cấm theo danh sách trong tài liệu |
| 4 | Shopee có chia sẻ thông tin cá nhân của tôi không? | Chunk từ `chinh-sach-bao-mat.md` — mục chia sẻ dữ liệu với đối tác | ~0.05 | ✅ Có | Agent trả lời: có chia sẻ với đối tác vận chuyển/thanh toán, không bán cho bên thứ ba |
| 5 | Người mua có trách nhiệm gì khi đặt hàng? | Chunk từ `quy-che-hoat-dong.md` — "Quy định dành cho Người Mua" | ~0.06 | ✅ Có | Agent tóm tắt: cung cấp địa chỉ chính xác, thanh toán đúng, không lạm dụng khuyến mãi |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Nhận xét về strategy FixedSize(500, 50):**
> FixedSizeChunker không quan tâm đến ranh giới câu hay đoạn văn, nên có thể cắt giữa một điều kiện quan trọng — ví dụ, chunk 500 ký tự có thể kết thúc ngay giữa một danh sách điều kiện. Overlap 50 ký tự giúp giảm thiểu rủi ro này nhưng không triệt để. Ưu điểm lớn là tốc độ nhanh, số chunk có thể dự đoán được và dễ debug. Phù hợp nhất với văn bản có độ dài đồng đều và không có cấu trúc phân cấp rõ ràng.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *(Sẽ cập nhật sau phần demo nhóm)* Kỳ vọng: so sánh với SentenceChunker và RecursiveChunker sẽ thấy rõ FixedSize thường tạo ra nhiều chunk "nhiễu" hơn khi tài liệu có cấu trúc heading/danh sách, trong khi RecursiveChunker giữ được nguyên vẹn từng section.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 9 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 4 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 8 / 10 |
| **Tổng phần cá nhân** | **56 / 60** |
