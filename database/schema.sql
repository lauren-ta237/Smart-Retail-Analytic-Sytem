 -- this schema allows you to answer real business questions

-- Stores table
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    location VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Zones inside the store
CREATE TABLE zones (
    id SERIAL PRIMARY KEY,
    store_id INT REFERENCES stores(id),
    zone_name VARCHAR(100),
    description TEXT
);


-- Products in the store
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    price DECIMAL,
    shelf_zone INT REFERENCES zones(id)
);


-- Customers detected by vision system
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    tracking_id VARCHAR(100),
    first_seen TIMESTAMP,
    last_seen TIMESTAMP
);


-- Customer movement between zones
CREATE TABLE zone_events (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    zone_id INT REFERENCES zones(id),
    entry_time TIMESTAMP,
    exit_time TIMESTAMP
);


-- Product interactions
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    customer_id INT REFERENCES customers(id),
    product_id INT REFERENCES products(id),
    interaction_type VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- Heatmap data
CREATE TABLE heatmap_points (
    id SERIAL PRIMARY KEY,
    x INT,
    y INT,
    zone_id INT REFERENCES zones(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- AI generated insights
CREATE TABLE ai_insights (
    id SERIAL PRIMARY KEY,
    insight_type VARCHAR(100),
    content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);