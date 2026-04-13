-- now my AI and backend can immediately run analytics

INSERT INTO stores (name, location)
VALUES ('Smart Retail Store', 'Downtown');


INSERT INTO zones (store_id, zone_name)
VALUES
(1, 'Entrance'),
(1, 'Electronics'),
(1, 'Groceries'),
(1, 'Checkout');


INSERT INTO products (name, category, price, shelf_zone)
VALUES
('Milk', 'Dairy', 2.50, 3),
('Bread', 'Bakery', 1.50, 3),
('Headphones', 'Electronics', 45.00, 2);