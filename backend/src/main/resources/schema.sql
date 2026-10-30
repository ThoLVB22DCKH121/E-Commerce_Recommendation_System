CREATE TABLE IF NOT EXISTS products (
    parent_asin VARCHAR(32) PRIMARY KEY,
    title TEXT,
    category TEXT,
    store TEXT,
    price DECIMAL(10, 2),
    image_url TEXT,
    description TEXT
);

