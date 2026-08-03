# -*- coding: utf-8 -*-
"""Test CustomChunker với dữ liệu tiếng Việt."""

import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.chunking import CustomChunker


def test_headings():
    print("=== Test 1: Heading Markdown ===")
    c = CustomChunker(min_chunk_size=20)
    text = """# Chính sách đổi trả
Người mua cần gửi yêu cầu đổi trả trong 7 ngày.

## Điều kiện đổi trả
Sản phẩm còn nguyên tem mác, chưa qua sử dụng.
Có hóa đơn mua hàng kèm theo.

## Quy trình đổi trả
Bước 1: Liên hệ CSKH qua hotline hoặc chat.
Bước 2: Gửi hàng về kho theo hướng dẫn.
Bước 3: Nhận hàng mới hoặc hoàn tiền.

## Ngoại lệ
Hàng giảm giá trên 50% không được đổi trả.
Hàng đã qua sử dụng không được hoàn tiền."""
    chunks = c.chunk(text)
    for i, ch in enumerate(chunks):
        print(f"--- Chunk {i} [{len(ch)} chars] ---")
        print(ch)
    print(f"\nTổng: {len(chunks)} chunks\n")


def test_clauses():
    print("=== Test 2: Điều khoản pháp lý ===")
    c = CustomChunker(min_chunk_size=20)
    text = """Điều 1. Phạm vi áp dụng
Chính sách này áp dụng cho tất cả người mua trên sàn thương mại điện tử.
Bao gồm cả giao dịch qua ứng dụng di động.

Điều 2. Quyền của người mua
Người mua có quyền đổi trả hàng trong vòng 7 ngày kể từ khi nhận hàng.
Người mua được hoàn tiền nếu hàng không đúng mô tả.

Điều 3. Nghĩa vụ của người bán
Người bán phải hoàn tiền trong 5 ngày làm việc kể từ khi nhận lại hàng.
Người bán chịu phí vận chuyển nếu hàng bị lỗi."""
    chunks = c.chunk(text)
    for i, ch in enumerate(chunks):
        print(f"--- Chunk {i} [{len(ch)} chars] ---")
        print(ch)
    print(f"\nTổng: {len(chunks)} chunks\n")


def test_faq():
    print("=== Test 3: FAQ (Hỏi/Đáp) ===")
    c = CustomChunker(min_chunk_size=20)
    text = """Câu hỏi thường gặp về chính sách đổi trả:

Hỏi: Tôi có thể đổi trả hàng không?
Đáp: Có, bạn có thể đổi trả trong 7 ngày kể từ khi nhận hàng.

Hỏi: Phí vận chuyển do ai chịu?
Đáp: Phí vận chuyển do người bán chịu nếu hàng bị lỗi hoặc không đúng mô tả.

Hỏi: Bao lâu thì được hoàn tiền?
Đáp: Hoàn tiền trong 5-7 ngày làm việc sau khi xác nhận yêu cầu hoàn trả."""
    chunks = c.chunk(text)
    for i, ch in enumerate(chunks):
        print(f"--- Chunk {i} [{len(ch)} chars] ---")
        print(ch)
    print(f"\nTổng: {len(chunks)} chunks\n")


def test_with_real_data():
    print("=== Test 4: Dữ liệu thật (returns-policy.md) ===")
    c = CustomChunker()
    with open("data/k4_ecommerce/returns-policy.md", encoding="utf-8") as f:
        text = f.read()
    # Bỏ front matter
    from ingest import parse_front_matter
    meta, body = parse_front_matter(text)
    print(f"Metadata: {meta}")
    print(f"Body length: {len(body)} chars")
    chunks = c.chunk(body)
    for i, ch in enumerate(chunks):
        print(f"--- Chunk {i} [{len(ch)} chars] ---")
        print(ch)
    print(f"\nTổng: {len(chunks)} chunks\n")


if __name__ == "__main__":
    test_headings()
    test_clauses()
    test_faq()
    test_with_real_data()
    print("✓ Tất cả tests chạy thành công!")
