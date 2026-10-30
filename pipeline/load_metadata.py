import json
import os
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

# Tải biến môi trường từ file .env
load_dotenv()

DB_URL = os.getenv("DATABASE_URL", "postgresql://recsys:recsys@localhost:5432/recsys")
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "datalake", "raw", "meta_categories", "meta_Video_Games.jsonl")


def get_first_image(images):
    """
    Trích xuất đường dẫn URL của ảnh lớn (large image) đầu tiên từ mảng ảnh.
    
    Args:
        images (list): Mảng danh sách các dict ảnh từ dữ liệu Amazon gốc.
    Returns:
        str | None: URL ảnh kích thước lớn, hoặc None nếu không có ảnh.
    """
    if isinstance(images, list):
        for img in images:
            if isinstance(img, dict) and img.get("large"):
                return img["large"]
    return None


def get_deepest_category(categories):
    """
    Lấy tên danh mục cụ thể nhất (phần tử cuối cùng trong chuỗi phân cấp).
    Ví dụ: ['Video Games', 'PlayStation 4', 'Games'] -> 'Games'
    
    Args:
        categories (list): Mảng danh mục phân cấp từ Amazon.
    Returns:
        str: Tên danh mục lá, mặc định là 'Video Games' nếu mảng rỗng.
    """
    if isinstance(categories, list) and categories:
        return str(categories[-1])
    return "Video Games"


def parse_price(val):
    """
    Ép kiểu giá trị giá sản phẩm sang dạng số thực (float).
    
    Args:
        val (any): Giá trị giá gốc (có thể là float, int, None hoặc string).
    Returns:
        float | None: Giá trị số thực, hoặc None nếu không có giá hợp lệ.
    """
    try:
        return float(val) if val is not None else None
    except (ValueError, TypeError):
        return None


def run_pipeline(limit=0, batch_size=5000):
    """
    Đọc dữ liệu streaming từ file JSONL, làm sạch và nạp theo lô (batch) vào bảng products trong PostgreSQL.
    
    Args:
        limit (int): Số lượng bản ghi tối đa cần nạp (0 = nạp toàn bộ file).
        batch_size (int): Kích thước mỗi lô để nạp hàng loạt (mặc định: 5.000).
    """
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    batch = []

    # Câu lệnh thêm mới hoặc cập nhật nếu đã tồn tại parent_asin (tránh trùng lặp)
    sql = """
        INSERT INTO products (parent_asin, title, category, store, price, image_url, description)
        VALUES %s
        ON CONFLICT (parent_asin) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            image_url = EXCLUDED.image_url;
    """

    print(f"[*] Starting full pipeline to load ALL metadata into PostgreSQL...")
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if limit and idx > limit:
                break
            try:
                item = json.loads(line)
            except Exception:
                continue

            asin = item.get("parent_asin")
            if not asin:
                continue

            # Chuẩn hóa trường mô tả: nếu là mảng các đoạn thì nối lại thành văn bản
            desc = item.get("description")
            if isinstance(desc, list):
                desc = "\n".join(str(d) for d in desc)

            batch.append((
                asin,
                item.get("title"),
                get_deepest_category(item.get("categories")),
                item.get("store"),
                parse_price(item.get("price")),
                get_first_image(item.get("images")),
                desc
            ))

            # Nạp vào database theo từng lô batch_size dòng để tối ưu tốc độ
            if len(batch) >= batch_size:
                execute_values(cur, sql, batch)
                conn.commit()
                print(f"  -> Inserted {idx:,} lines...")
                batch.clear()

        # Nạp các bản ghi còn sót lại của batch cuối cùng
        if batch:
            execute_values(cur, sql, batch)
            conn.commit()

    cur.close()
    conn.close()
    print(f"[+] Full ingestion completed successfully! Total processed: {idx:,} lines.")


if __name__ == "__main__":
    run_pipeline()
