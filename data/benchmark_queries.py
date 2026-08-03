"""Shared benchmark queries for comparing K4 chunking strategies."""

BENCHMARK_QUERIES = [
    {
        "id": "q1_return_deadline",
        "query": "Thời hạn tối đa để người mua gửi yêu cầu Trả hàng/Hoàn tiền là bao lâu đối với thực phẩm tươi sống, đơn do người bán tự vận chuyển và các đơn hàng khác?",
        "gold_answer": (
            "Thực phẩm tươi sống/đông lạnh: 24 giờ từ khi giao thành công (trừ lý do chưa nhận được hàng). "
            "Đơn do người bán tự vận chuyển: 15 ngày từ khi bấm Đã nhận được hàng, hoặc 20 ngày từ khi lấy hàng thành công nếu chưa bấm nhận hàng. "
            "Các đơn khác: 15 ngày từ khi giao hàng thành công."
        ),
        "metadata_filter": {"customer_role": "buyer"},
        "relevant_doc_id": "shopee-returns-01",
        "relevant_section": "1.2. Thời gian tối đa để gửi yêu cầu trả hàng hoàn tiền",
    },
    {
        "id": "q2_restricted_products",
        "query": "Sản phẩm hạn chế trả hàng là gì và Shopee không áp dụng lý do trả hàng nào cho nhóm sản phẩm này? Hãy nêu ba ví dụ.",
        "gold_answer": (
            "Đây là sản phẩm có tính đặc thù cao, dễ hư hỏng hoặc cần bảo quản nghiêm ngặt. "
            "Shopee không áp dụng lý do 'Hàng nguyên vẹn nhưng không còn nhu cầu'. "
            "Ví dụ gồm cây cảnh, thực phẩm tươi sống/đông lạnh và găng tay hoặc khẩu trang y tế."
        ),
        "metadata_filter": None,
        "relevant_doc_id": "shopee-returns-03",
        "relevant_section": "Sản phẩm hạn chế trả hàng",
    },
    {
        "id": "q3_evidence_video",
        "query": "Video mở kiện dùng làm bằng chứng khi hàng bị lỗi hoặc khác mô tả phải đáp ứng những yêu cầu nào, và nếu video vượt dung lượng cho phép thì xử lý ra sao?",
        "gold_answer": (
            "Video phải quay liên tục, không cắt ghép; góc quay rõ, chất lượng không mờ; thể hiện 6 mặt kiện hàng, mã vận đơn, quá trình mở kiện và tình trạng/số lượng/tem nhãn sản phẩm. "
            "Video tối đa 100 MB và 1 phút; nếu lớn hơn thì tải lên YouTube hoặc Google Drive ở chế độ công khai và gửi liên kết trong chú thích."
        ),
        "metadata_filter": None,
        "relevant_doc_id": "shopee-returns-04",
        "relevant_section": "2. Đã nhận được hàng, khiếu nại hàng có vấn đề; 4. Quy định về bằng chứng",
    },
    {
        "id": "q4_track_request",
        "query": "Người mua cần thực hiện các bước nào trên ứng dụng Shopee để xem tình trạng xử lý yêu cầu Trả hàng/Hoàn tiền?",
        "gold_answer": (
            "Vào Tôi > Đơn Mua; mở ô Trả hàng rồi chọn Trả hàng/Hoàn tiền; chọn sản phẩm cần theo dõi và bấm Chi Tiết Trả Hàng/Hoàn Tiền; xem trạng thái ở phía trên màn hình. "
            "Ngoài ra có thể xem tại Thông báo > Cập nhật Đơn hàng."
        ),
        "metadata_filter": None,
        "relevant_doc_id": "shopee-returns-05",
        "relevant_section": "1. Trên ứng dụng Shopee",
    },
    {
        "id": "q5_refund_time",
        "query": "Sau khi Shopee chấp nhận hoàn tiền, thời gian nhận tiền đối với Ví ShopeePay, thẻ Napas và thẻ tín dụng/ghi nợ khác nhau như thế nào?",
        "gold_answer": (
            "Ví ShopeePay: 24 giờ nếu ví hoạt động bình thường; thẻ nội địa Napas: 2-5 ngày làm việc tùy ngân hàng; thẻ tín dụng/ghi nợ: 7-14 ngày làm việc tùy ngân hàng."
        ),
        "metadata_filter": None,
        "relevant_doc_id": "shopee-returns-06",
        "relevant_section": "Bảng 1: Phương thức hoàn tiền và thời gian hoàn tiền",
    },
]
