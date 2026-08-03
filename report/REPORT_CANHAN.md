# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Tên sinh viên]
**Nhóm:** [Tên nhóm]
**Ngày:** [Ngày nộp]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là góc giữa hai vector biểu diễn từ/đoạn văn bản nhỏ, cho thấy hai văn bản đó có sự tương đồng lớn về mặt ngữ nghĩa hoặc ngữ cảnh sử dụng từ ngữ.

**Ví dụ có độ tương tự CAO:**
- Câu A: Làm thế nào để tôi có thể đổi trả sản phẩm đã mua?
- Câu B: Quy trình trả lại hàng và nhận hoàn tiền được thực hiện như thế nào?
- Tại sao tương đồng: Cả hai câu đều hỏi về cách thức trả lại hàng hóa đã mua và nhận lại tiền, mặc dù sử dụng các từ ngữ khác nhau nhưng mang cùng một ý nghĩa/ngữ cảnh.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Tôi muốn thanh toán đơn hàng này bằng thẻ tín dụng Visa.
- Câu B: Hôm nay thời tiết Hà Nội mát mẻ và có mưa rào nhẹ.
- Tại sao khác: Hai câu nói về hai chủ đề hoàn toàn khác biệt (giao dịch thanh toán TMĐT vs thời tiết), không chia sẻ chung bất kỳ ngữ cảnh hay từ ngữ liên quan nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo hướng của các vector thay vì độ lớn (độ dài). Trong văn bản, độ dài vector thường bị ảnh hưởng bởi độ dài ngắn của văn bản, do đó cosine similarity giúp so sánh ngữ nghĩa của hai văn bản một cách khách quan hơn mà không bị ảnh hưởng bởi số lượng từ trong đoạn văn.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* làm_tròn_lên((10000 - 50) / (500 - 50)) = làm_tròn_lên(9950 / 450) = làm_tròn_lên(22.111...)
> *Đáp án:* 23 chunks

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Phép tính mới: làm_tròn_lên((10000 - 100) / (500 - 100)) = làm_tròn_lên(9900 / 400) = làm_tròn_lên(24.75) = 25 chunks (số lượng chunk tăng lên).
> Ta muốn tăng độ chồng chéo để giữ nguyên vẹn ngữ cảnh của các câu/ý nằm ở ranh giới giữa các chunk, giúp hệ thống truy xuất (retrieval) không bị mất thông tin liên kết quan trọng của các đoạn văn.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi sử dụng biểu thức chính quy lookbehind `re.split(r'(?<=\. |! |\? |\.\n)', text)` để chia nhỏ văn bản thành các câu độc lập mà không bị mất đi dấu câu kết thúc câu. Tiếp đến, tôi loại bỏ khoảng trắng đầu/cuối của từng câu và lọc bỏ các chuỗi rỗng. Cuối cùng, tôi gom nhóm các câu lại theo nhóm có kích thước tối đa là `max_sentences_per_chunk` rồi nối lại bằng dấu cách.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán hoạt động theo nguyên tắc đệ quy với base case là khi độ dài văn bản nhỏ hơn hoặc bằng `chunk_size`. Khi văn bản dài hơn giới hạn, thuật toán duyệt qua danh sách các dấu phân cách theo thứ tự ưu tiên: `["\n\n", "\n", ". ", " ", ""]`. Nếu hết dấu phân cách mà đoạn văn vẫn vượt quá kích thước, tôi chia nhỏ đoạn văn theo ký tự thành các chunk bằng đúng `chunk_size`. Nếu còn dấu phân cách, tôi thực hiện tách, đệ quy chia nhỏ các phần vượt kích thước, và tiến hành gom các đoạn nhỏ liên tiếp lại với nhau bằng dấu phân cách nếu tổng kích thước của chúng không vượt quá `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Với cấu trúc in-memory, các tài liệu được chuyển đổi thông qua hàm `_make_record` (tính toán vector nhúng bằng `_embedding_fn`) và lưu vào danh sách `self._store`. Với ChromaDB, tôi sử dụng `collection.add(ids, documents, embeddings, metadatas)`. Khi `search`, tôi nhúng câu truy vấn, sử dụng hàm `compute_similarity` để tính độ tương tự cosine giữa câu truy vấn và tất cả các chunk lưu trữ, sau đó sắp xếp giảm dần và lấy ra top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Trong `search_with_filter`, tôi thực hiện pre-filtering (lọc trước) các bản ghi có metadata khớp với điều kiện lọc, sau đó mới gọi hàm `_search_records` để tìm kiếm và tính độ tương tự ngữ nghĩa trên tập đã lọc. Trong `delete_document`, tôi thực hiện lọc bỏ tất cả các chunk có ID bằng `doc_id`, bắt đầu bằng `doc_id::chunk_` hoặc trường `doc_id` trong metadata bằng `doc_id`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tôi gọi phương thức `store.search` để lấy ra top_k chunk có độ tương tự cao nhất với câu hỏi. Sau đó, tôi ghép các chunk này lại với nhau để tạo thành ngữ cảnh (context) và đưa vào prompt cùng câu hỏi theo định dạng: `Context:\n{context}\n\nQuestion: {question}\n\nAnswer:`. Cuối cùng, tôi chuyển prompt này sang hàm LLM `llm_fn` để lấy câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts =============================
platform win32 -- Python 3.12.3, pytest-9.1.1, pluggy-1.6.0 -- D:\Document\AI20K\Project\K4-Day07-Data-Foundations\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Document\AI20K\Project\K4-Day07-Data-Foundations
configfile: pyproject.toml
collecting ... collected 42 items

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

============================= 42 passed in 0.18s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Làm cách nào để tôi yêu cầu hoàn tiền cho đơn hàng bị lỗi? | Tôi muốn trả lại sản phẩm hỏng và nhận lại tiền. | cao | -0.1700 | Sai |
| 2 | Chính sách bảo mật thông tin cá nhân của cửa hàng là gì? | Làm thế nào để tôi đăng ký làm người bán trên sàn? | thấp | 0.0256 | Đúng |
| 3 | Thời gian giao hàng dự kiến của đơn hàng là bao lâu? | Khi nào tôi nhận được sản phẩm tôi đã mua? | cao | 0.2057 | Sai (điểm quá thấp) |
| 4 | Tôi có thể thanh toán qua ví điện tử MoMo không? | Phương thức thanh toán bằng thẻ tín dụng Visa có khả dụng không? | cao / trung bình | 0.0435 | Sai |
| 5 | Làm thế nào để hủy đơn hàng đã đặt? | Tôi muốn thay đổi địa chỉ nhận hàng của mình. | trung bình / thấp | -0.1091 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là các cặp câu có độ tương đồng ngữ nghĩa cực kỳ cao (Cặp 1 và Cặp 3) lại nhận được điểm số rất thấp hoặc thậm chí âm (-0.1700 và 0.2057). Điều này chỉ ra rằng `MockEmbedder` chỉ băm (hash) văn bản bằng MD5 rồi tạo ngẫu nhiên một vector đơn vị, hoàn toàn không biểu diễn được ý nghĩa thực sự của từ ngữ. Một embedding thực thụ cần phải sử dụng mạng nơ-ron được huấn luyện để ánh xạ các từ/câu có ngữ cảnh tương tự lại gần nhau trong không gian vector đa chiều.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. (Do đang ở Giai đoạn 1 nên các câu hỏi này được chạy thử nghiệm trên bộ tài liệu starter `data/k4_ecommerce/` với `MockEmbedder`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Làm thế nào để đổi trả hàng khi bị lỗi? | hoặc không đúng mô tả. Người bán có trách nhiệm phản hồi... | 0.0230 | Có | [Agent] Tra lời dựa trên context. |
| 2 | Người bán có trách nhiệm gì khi đăng bán sản phẩm? | hoặc không đúng mô tả. Người bán có trách nhiệm phản hồi... | 0.1269 | Không | [Agent] Tra lời dựa trên context. |
| 3 | Có được đăng bán sản phẩm bị cấm không? | > Khối metadata phía trên là template mẫu cho K4 — thay... | 0.1841 | Có | [Agent] Tra lời dựa trên context. |
| 4 | Yêu cầu đổi trả của người mua cần kèm theo tài liệu gì? | > Khối metadata phía trên là template mẫu cho K4 (bắt buộc... | 0.0303 | Có | [Agent] Tra lời dựa trên context. |
| 5 | Quy định đăng bán dành cho ai? | > Khối metadata phía trên là template mẫu cho K4 — thay... | -0.0072 | Có | [Agent] Tra lời dựa trên context. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5
*(Giải thích: Vì cơ sở dữ liệu starter hiện tại chỉ có tổng cộng 3 chunk, nên toàn bộ 3 chunk đều nằm trong danh sách top-3 trả về của mọi câu hỏi, dẫn đến tỷ lệ chứa chunk liên quan trong top-3 là 5/5. Tuy nhiên, nếu xét Top-1 thì độ chính xác bị sai lệch lớn ở Câu 2 do mô hình nhúng giả lập không thể hiện được sự tương đồng ngữ nghĩa thực).*

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Tôi nhận thấy việc phân mảnh đệ quy (RecursiveChunker) kết hợp với thiết kế metadata thông minh giúp tối ưu hóa kết quả tìm kiếm rất nhiều. Việc gán các thẻ metadata cụ thể như `customer_role` cho phép chúng ta lọc (filter) bớt nhiễu hiệu quả trước khi tiến hành tính toán độ tương tự cosine, tăng tốc độ và độ chính xác của câu trả lời.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
