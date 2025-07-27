CREATE TABLE watch_list_watchlists (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE watch_list_stocks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    watchlist_id INT NOT NULL,
    ticker VARCHAR(20) NOT NULL,
    company_name VARCHAR(255),
    latest_pe_ratio DECIMAL(10, 4),
    note TEXT, -- Using TEXT for rich text content (e.g., HTML)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_AT
    FOREIGN KEY (watchlist_id) REFERENCES watch_list_watchlists(id) ON DELETE CASCADE,
    UNIQUE (watchlist_id, ticker) -- Ensure unique ticker per watchlist
);

CREATE TABLE watch_list_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE watch_list_stock_tags (
    stock_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (stock_id, tag_id),
    FOREIGN KEY (stock_id) REFERENCES watch_list_stocks(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES watch_list_tags(id) ON DELETE CASCADE
);