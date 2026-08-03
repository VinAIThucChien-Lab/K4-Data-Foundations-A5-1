# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** A5-1
**Thành viên:** Lê Mai Việt Hoàng, Nguyễn Đức Đạt, Đỗ Duy Đức, Kiều Hồng Phong, Vũ Ngọc Bảo Sơn
**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách Trả hàng/Hoàn tiền dành cho người mua trên Shopee Việt Nam: điều kiện, thời hạn, bằng chứng, theo dõi yêu cầu và thời gian nhận tiền hoàn.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy định chung về Trả hàng/Hoàn tiền | `https://help.shopee.vn/portal/4/article/188931` | 2026-08-03 / not-stated | 6,260 | buyer, returns-refunds, vi |
| 2 | Hướng dẫn gửi yêu cầu Trả hàng/Hoàn tiền | `https://help.shopee.vn/portal/4/article/79233?seo=1` | 2026-08-03 / not-stated | 2,553 | buyer, returns-refunds, vi |
| 3 | Sản phẩm hạn chế trả hàng | `https://help.shopee.vn/portal/4/article/79465` | 2026-08-03 / not-stated | 2,043 | buyer, returns-refunds, vi |
| 4 | Hướng dẫn chuẩn bị bằng chứng | `https://help.shopee.vn/portal/4/article/79467` | 2026-08-03 / not-stated | 3,503 | buyer, returns-refunds, vi |
| 5 | Theo dõi tình trạng Trả hàng/Hoàn tiền | `https://help.shopee.vn/portal/4/article/79298?seo=1` | 2026-08-03 / not-stated | 1,582 | buyer, returns-refunds, vi |
| 6 | Thời gian nhận và kiểm tra tiền hoàn | `https://help.shopee.vn/portal/4/article/189473` | 2026-08-03 / not-stated | 3,892 | buyer, returns-refunds, vi |
| 7 | Quy trình Shopee xử lý yêu cầu | `https://help.shopee.vn/portal/4/article/190242` | 2026-08-03 / not-stated | 8,025 | buyer, returns-refunds, vi |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-returns-01` | Định danh tài liệu và đối chiếu gold document. |
| `source_url` | string | URL bài viết Shopee | Truy vết và kiểm chứng câu trả lời. |
| `retrieved_at` | date string | `2026-08-03` | Kiểm tra độ mới của corpus. |
| `document_version` | string | `not-stated` | Theo dõi phiên bản/ngày hiệu lực khi nguồn công bố. |
| `customer_role` | enum | `buyer` | Lọc tài liệu theo vai trò khách hàng. |
| `category` | string | `returns-refunds` | Giới hạn retrieval theo chủ đề. |
| `language` | string | `vi` | Chọn embedder và corpus đúng ngôn ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `shopee-returns-01` | FixedSizeChunker (`fixed_size`) | 13 | 481.54 | Có thể cắt giữa danh sách/điều kiện. |
| `shopee-returns-01` | SentenceChunker (`by_sentences`) | 10 | 623.30 | Giữ câu nhưng có chunk vượt 500 ký tự. |
| `shopee-returns-01` | RecursiveChunker (`recursive`) | 14 | 445.29 | Giữ ranh giới đoạn tốt hơn. |
| `shopee-returns-04` | FixedSizeChunker (`fixed_size`) | 8 | 437.88 | Có thể tách tiêu chí video khỏi giới hạn dung lượng. |
| `shopee-returns-04` | SentenceChunker (`by_sentences`) | 11 | 315.64 | Các yêu cầu ngắn, dễ đọc. |
| `shopee-returns-04` | RecursiveChunker (`recursive`) | 9 | 387.44 | Giữ các cụm bằng chứng theo đoạn. |
| `shopee-returns-06` | FixedSizeChunker (`fixed_size`) | 8 | 486.50 | Có nguy cơ cắt ngang bảng hoàn tiền. |
| `shopee-returns-06` | SentenceChunker (`by_sentences`) | 4 | 970.25 | Chunk quá dài do dữ liệu bảng ít dấu kết câu. |
| `shopee-returns-06` | RecursiveChunker (`recursive`) | 10 | 387.40 | Tách bảng thành các nhóm nhỏ hơn. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Nguyễn Đức Đạt — branch `datnd`**
- **Loại chiến lược thực tế trong `run_benchmark.py`:** SentenceChunker (`max_sentences_per_chunk=3`), do branch đổi mặc định của `build_knowledge_base()`.
- **Mô tả & lý do chọn:** Giữ ranh giới câu và phù hợp tài liệu chính sách/FAQ; implementation của branch dùng regex giữ delimiter theo câu. Một số câu dài làm chunk vượt kích thước mục tiêu.

**Đỗ Duy Đức — branch `ducdd`**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=500`, `overlap=50`).
- **Mô tả & lý do chọn:** Là baseline có tốc độ cao và số chunk dễ dự đoán; overlap 50 giữ lại một phần thông tin khi câu bị cắt.

**Kiều Hồng Phong — branch `phong`**
- **Loại chiến lược thực tế trong `bench.py`:** SentenceChunker (`max_sentences_per_chunk=3`); branch cũng có lớp thử nghiệm `LangChainSentenceChunker`.
- **Mô tả & lý do chọn:** Ưu tiên ranh giới câu để context dễ đọc; runner đã lưu kết quả embedding Hugging Face thật trong `real_benchmark_output.txt`.

**Vũ Ngọc Bảo Sơn — branch `vnbson`**
- **Loại chiến lược:** CustomChunker (`max_chunk_size=1000`) theo heading, điều khoản, mục đánh số và FAQ; fallback RecursiveChunker.
- **Mô tả & lý do chọn:** Giữ cấu trúc ngữ nghĩa của văn bản chính sách và prefix heading vào sub-chunk; gộp chunk quá nhỏ để giảm phân mảnh.

**Lê Mai Việt Hoàng — branch `hoanglmv`**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=500`).
- **Mô tả & lý do chọn:** Giữ đoạn/câu tự nhiên trước khi cắt theo từ/ký tự, cân bằng giữa độ mạch lạc và kích thước context.

> Kiểm tra commit mới nhất cho thấy Đạt và Phong đều chạy SentenceChunker 3 câu, nhưng dùng hai implementation regex khác nhau; Đức dùng Fixed, Sơn dùng Custom và Hoàng dùng Recursive. Vì vậy nhóm có bốn họ chiến lược thực tế, trong đó Sentence có hai biến thể.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Nguyễn Đức Đạt | Sentence 3 câu | 5/5 Top-3 | Giữ ranh giới câu; score lexical tốt ở Q4. | Có chunk dài tới 2,527 ký tự. |
| Đỗ Duy Đức | Fixed 500/50 | 5/5 Top-3 | Baseline nhanh, overlap giảm mất ngữ cảnh. | Cắt theo ký tự; ít giữ cấu trúc. |
| Kiều Hồng Phong | Sentence 3 câu | 5/5 Top-3 | Giữ ranh giới câu; có runner benchmark và output HF. | Có chunk dài tới 2,607 ký tự. |
| Vũ Ngọc Bảo Sơn | Custom 1000 | 5/5 Top-3 | Chỉ 47 chunk; mạnh ở Q3 và Q5; giữ heading. | Chunk dài tới khoảng 1,004 ký tự, có thể chứa thêm nhiễu. |
| Lê Mai Việt Hoàng | Recursive 500 | 5/5 Top-3 | Cân bằng độ dài và tính mạch lạc; phù hợp văn bản nhiều đoạn. | 69 chunk, nhiều hơn Custom. |

### Thống kê chạy cùng corpus

| Branch / thành viên | Cấu hình runner | Tổng chunk | Trung bình | Min | Max |
|---|---|---:|---:|---:|---:|
| `datnd` / Nguyễn Đức Đạt | Sentence 3 câu | 48 | 577.81 | 52 | 2,527 |
| `ducdd` / Đỗ Duy Đức | Fixed 500/50 | 64 | 479.81 | 232 | 500 |
| `phong` / Kiều Hồng Phong | Sentence 3 câu | 53 | 522.98 | 55 | 2,607 |
| `vnbson` / Vũ Ngọc Bảo Sơn | Custom 1000 | 47 | 592.04 | 55 | 1,004 |
| `hoanglmv` / Lê Mai Việt Hoàng | Recursive 500 | 69 | 401.93 | 55 | 499 |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Cả năm runner đều tìm đúng gold document trong Top-3 cho 5/5 câu khi dùng cùng phép xếp hạng lexical cosine. CustomChunker 1000 tạo ít chunk nhất (47) và mạnh ở câu cần gom bằng chứng/bảng hoàn tiền; Recursive 500 có chunk ngắn, ổn định nhất và không vượt 500 ký tự. Hai implementation Sentence của Đạt và Phong giữ câu nhưng có chunk cực dài do câu/bảng trong chính sách không có đủ dấu kết thúc; vì vậy cần chấm thêm grounding bằng local multilingual embedder trước khi kết luận.

**Phương pháp so sánh:** Checkout logic chunker trực tiếp từ từng remote branch bằng `git show`, chạy trên cùng 7 tài liệu Shopee và 5 query. Do local Sentence Transformers không cài hoàn tất trong môi trường tổng hợp, bảng trên dùng cosine của vector tần suất từ để so sánh công bằng tương đối; không trộn các score này với score Hugging Face đã lưu riêng trên branch `phong`.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Thời hạn tối đa để người mua gửi yêu cầu Trả hàng/Hoàn tiền là bao lâu đối với thực phẩm tươi sống, đơn do người bán tự vận chuyển và các đơn hàng khác? | Tươi sống/đông lạnh: 24 giờ sau giao thành công; người bán tự vận chuyển: 15 ngày sau khi bấm đã nhận, hoặc 20 ngày sau lấy hàng thành công nếu chưa bấm nhận; đơn khác: 15 ngày sau giao thành công. Dùng filter `customer_role=buyer`. | `shopee-returns-01`, mục 1.2 |
| 2 | Sản phẩm hạn chế trả hàng là gì và Shopee không áp dụng lý do trả hàng nào cho nhóm này? Hãy nêu ba ví dụ. | Sản phẩm đặc thù, dễ hư hỏng hoặc cần bảo quản nghiêm ngặt; không áp dụng lý do “Hàng nguyên vẹn nhưng không còn nhu cầu”; ví dụ cây cảnh, thực phẩm tươi sống/đông lạnh, găng tay hoặc khẩu trang y tế. | `shopee-returns-03`, mục Sản phẩm hạn chế trả hàng |
| 3 | Video mở kiện dùng làm bằng chứng khi hàng bị lỗi hoặc khác mô tả phải đáp ứng yêu cầu nào, và nếu vượt dung lượng thì xử lý ra sao? | Video liên tục, không cắt ghép, rõ nét; có 6 mặt kiện, mã vận đơn, quá trình mở và tình trạng sản phẩm. Tối đa 100 MB/1 phút; nếu lớn hơn, tải YouTube/Google Drive công khai và gửi link. | `shopee-returns-04`, mục 2 và 4 |
| 4 | Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu Trả hàng/Hoàn tiền? | Tôi > Đơn Mua > Trả hàng > Trả hàng/Hoàn tiền > chọn sản phẩm > Chi Tiết Trả Hàng/Hoàn Tiền; cũng có thể xem Thông báo > Cập nhật Đơn hàng. | `shopee-returns-05`, mục 1 |
| 5 | Sau khi Shopee chấp nhận hoàn tiền, thời gian nhận tiền đối với Ví ShopeePay, thẻ Napas và thẻ tín dụng/ghi nợ khác nhau thế nào? | Ví ShopeePay: 24 giờ; Napas: 2–5 ngày làm việc; thẻ tín dụng/ghi nợ: 7–14 ngày làm việc, tùy ngân hàng. | `shopee-returns-06`, Bảng 1 |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn yêu cầu | Fixed 500/50 | Có, 5/5 branch | Fixed có score lexical Top-1 cao nhất 0.5482; Sentence Đạt 0.5392 và Sentence Phong 0.5390. |
| 2 | Sản phẩm hạn chế | Fixed 500/50 | Có, 5/5 branch | Fixed 0.7536; Recursive 0.7448; Sentence Phong 0.7484; tất cả Top-1 đúng. |
| 3 | Video bằng chứng | Custom 1000 | Có, 5/5 branch | Custom 0.3628 giữ nhiều tiêu chí trong cùng section; Fixed/Recursive vẫn Top-1 đúng. |
| 4 | Theo dõi yêu cầu | Sentence Đạt | Có, 5/5 branch | Sentence Đạt đạt lexical Top-1 0.5992; Fixed 0.5652, Sentence Phong 0.5514 và Recursive 0.5509. |
| 5 | Thời gian hoàn tiền | Custom 1000 | Có, 5/5 branch | Custom 0.5196 giữ phần bảng dài tốt hơn; output HF trên branch Phong tìm đúng doc nhưng context Top-1 chưa đủ mọi dòng bảng. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Q1 dùng `metadata_filter={"customer_role": "buyer"}` đúng yêu cầu K4. Tuy nhiên cả 7 tài liệu hiện đều mang vai trò `buyer`, nên filter chưa làm giảm tập ứng viên và chưa chứng minh được lợi ích thực tế. Nhóm cần bổ sung ít nhất một tài liệu `seller` hoặc `both` cùng chủ đề để đo mức cải thiện trước/sau filter có ý nghĩa.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Cấu trúc chunk tác động khác nhau theo dạng dữ liệu: Fixed tốt với đoạn ngắn, Custom tốt với section/bảng dài, Recursive cân bằng hai trường hợp.
> - Ít chunk không đồng nghĩa luôn tốt hơn: Custom giảm số vector nhưng context dài hơn và có thể chứa nhiễu.
> - Q4 và Q5 là failure cases hữu ích: nhiều tài liệu dùng từ giống nhau và bảng hoàn tiền dễ bị tách, khiến đúng document nhưng context chưa đủ gold answer.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus, Sentence Đạt tạo 48 chunk, Fixed 64, Sentence Phong 53, Custom 47 và Recursive 69. Các chiến lược đều tìm đúng gold document trong phép đo lexical, nhưng vị trí ranh giới quyết định một chunk có chứa đủ điều kiện/ngoại lệ để LLM trả lời trọn vẹn hay không; vì vậy cần đánh giá cả grounding, không chỉ document hit.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thống nhất runner chung ngay từ đầu, bắt buộc mỗi thành viên truyền chunker rõ ràng để tránh cấu hình trùng nhau. Corpus cũng sẽ bỏ hai tài liệu template `example.com`, bổ sung tài liệu vai trò `seller/both`, và chạy lại mọi chiến lược bằng cùng phiên bản local multilingual embedder trước khi chấm LLM answer.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10/ 10 |
| Thiết kế chiến lược (Strategy Design) | 15/ 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10/ 10 |
| Thuyết trình (Demo) | 5/ 5 |
| **Tổng phần nhóm** | **40/ 40** |
