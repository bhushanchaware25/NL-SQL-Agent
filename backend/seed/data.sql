-- NL2SQL Agent — E-Commerce Seed Data
-- Run AFTER schema.sql

-- Categories
INSERT INTO categories (name, description) VALUES
('Electronics',    'Gadgets, devices and tech accessories'),
('Clothing',       'Apparel for men, women and kids'),
('Home & Kitchen', 'Furniture, cookware and home décor'),
('Books',          'Fiction, non-fiction and educational'),
('Sports',         'Equipment, gear and activewear'),
('Beauty',         'Skincare, makeup and grooming'),
('Toys',           'Games and toys for all ages'),
('Automotive',     'Car accessories and tools')
ON CONFLICT DO NOTHING;

-- Products (40 products)
INSERT INTO products (name, description, price, stock_quantity, category_id, sku) VALUES
('Wireless Earbuds Pro',     'Premium noise-cancelling earbuds', 89.99,  150, 1, 'ELEC-001'),
('Smart Watch Series 5',     '1.4" AMOLED fitness tracker',      199.99, 75,  1, 'ELEC-002'),
('4K Webcam Ultra',          '3840x2160 USB-C webcam',           129.99, 60,  1, 'ELEC-003'),
('Mechanical Keyboard RGB',  'Compact TKL, blue switches',       79.99,  200, 1, 'ELEC-004'),
('Portable SSD 1TB',         'NVMe USB-C, 1000MB/s',             109.99, 90,  1, 'ELEC-005'),
('Bluetooth Speaker Boom',   '360° surround, waterproof IPX7',   59.99,  120, 1, 'ELEC-006'),
('Men''s Running Jacket',    'Lightweight, wind-resistant',       54.99,  300, 2, 'CLTH-001'),
('Women''s Yoga Pants',      'High-waist, 4-way stretch',        39.99,  450, 2, 'CLTH-002'),
('Classic Denim Shirt',      'Stone-washed cotton blend',        49.99,  180, 2, 'CLTH-003'),
('Wool Beanie Hat',          'Merino wool, one size',            19.99,  500, 2, 'CLTH-004'),
('Leather Sneakers',         'Full-grain leather, white sole',   119.99, 100, 2, 'CLTH-005'),
('Non-stick Cookware Set',   '10-piece aluminium set',           89.99,  80,  3, 'HOME-001'),
('Memory Foam Pillow',       'Contour cervical support',         34.99,  200, 3, 'HOME-002'),
('Air Fryer 5.5L',           'Digital, 1700W, 8 presets',       99.99,  65,  3, 'HOME-003'),
('Bamboo Cutting Board',     'Extra-large, juice groove',        24.99,  350, 3, 'HOME-004'),
('Smart LED Desk Lamp',      'Touch dimmer, USB charging port',  44.99,  130, 3, 'HOME-005'),
('Clean Code (Book)',        'Robert C. Martin classic',         35.99,  250, 4, 'BOOK-001'),
('Atomic Habits (Book)',     'James Clear bestseller',           18.99,  400, 4, 'BOOK-002'),
('Python Data Science',      'O''Reilly comprehensive guide',    54.99,  120, 4, 'BOOK-003'),
('The Lean Startup',         'Eric Ries entrepreneurship',       16.99,  310, 4, 'BOOK-004'),
('Yoga Mat Premium',         '6mm thick, anti-slip surface',     29.99,  220, 5, 'SPRT-001'),
('Adjustable Dumbbells',     '5-50 lbs, quick-lock system',     249.99, 40,  5, 'SPRT-002'),
('Cycling Helmet',           'MIPS certified, 17 vents',         79.99,  90,  5, 'SPRT-003'),
('Running Shoes Flex',       'Responsive cushioning, mesh',      109.99, 160, 5, 'SPRT-004'),
('Resistance Bands Set',     '5 levels, door anchor included',   19.99,  400, 5, 'SPRT-005'),
('Vitamin C Serum',          '20% L-ascorbic acid, 30ml',       32.99,  300, 6, 'BEAU-001'),
('Beard Grooming Kit',       'Oil, balm, comb and scissors',     24.99,  180, 6, 'BEAU-002'),
('Electric Face Brush',      'Silicone sonic cleansing',         49.99,  110, 6, 'BEAU-003'),
('LEGO Architecture Set',   '744 pieces, Eiffel Tower',         69.99,  95,  7, 'TOYS-001'),
('Remote Control Car',       '1:16 scale, 2.4GHz, 30km/h',      44.99,  140, 7, 'TOYS-002'),
('Board Game Catan',         'Classic strategy for 3-4 players', 39.99,  200, 7, 'TOYS-003'),
('Slime Kit Deluxe',         '35 colours, glitter and glows',    14.99,  260, 7, 'TOYS-004'),
('Car Phone Mount',          'Magnetic, 360° rotation',          14.99,  500, 8, 'AUTO-001'),
('Dash Cam 4K',              'Sony STARVIS sensor, WiFi GPS',    119.99, 70,  8, 'AUTO-002'),
('Portable Jump Starter',    '2000A peak, 20000mAh',             89.99,  55,  8, 'AUTO-003'),
('Car Vacuum Cleaner',       '12V DC, 7000Pa suction',           34.99,  120, 8, 'AUTO-004'),
('Tyre Inflator Digital',    'Cordless, auto-off pressure',      49.99,  95,  8, 'AUTO-005'),
('USB-C Hub 7-in-1',         '4K HDMI, 100W PD, SD reader',     39.99,  210, 1, 'ELEC-007'),
('Smart Plug WiFi 4-Pack',   'Alexa/Google, energy monitor',    29.99,  180, 1, 'ELEC-008'),
('Noise Machine Sleep',      '30 white noise sounds',            49.99,  90,  3, 'HOME-006')
ON CONFLICT (sku) DO NOTHING;

-- Customers (50 customers)
INSERT INTO customers (first_name, last_name, email, phone, city, state, country) VALUES
('Alice','Johnson','alice.johnson@email.com','555-0101','New York','NY','US'),
('Bob','Smith','bob.smith@email.com','555-0102','Los Angeles','CA','US'),
('Carol','Williams','carol.williams@email.com','555-0103','Chicago','IL','US'),
('David','Brown','david.brown@email.com','555-0104','Houston','TX','US'),
('Eva','Jones','eva.jones@email.com','555-0105','Phoenix','AZ','US'),
('Frank','Garcia','frank.garcia@email.com','555-0106','Philadelphia','PA','US'),
('Grace','Miller','grace.miller@email.com','555-0107','San Antonio','TX','US'),
('Henry','Davis','henry.davis@email.com','555-0108','San Diego','CA','US'),
('Iris','Rodriguez','iris.rodriguez@email.com','555-0109','Dallas','TX','US'),
('Jack','Martinez','jack.martinez@email.com','555-0110','San Jose','CA','US'),
('Karen','Hernandez','karen.hernandez@email.com','555-0111','Austin','TX','US'),
('Liam','Lopez','liam.lopez@email.com','555-0112','Jacksonville','FL','US'),
('Mia','Gonzalez','mia.gonzalez@email.com','555-0113','Seattle','WA','US'),
('Noah','Wilson','noah.wilson@email.com','555-0114','Denver','CO','US'),
('Olivia','Anderson','olivia.anderson@email.com','555-0115','Boston','MA','US'),
('Paul','Thomas','paul.thomas@email.com','555-0116','Nashville','TN','US'),
('Quinn','Taylor','quinn.taylor@email.com','555-0117','Portland','OR','US'),
('Rose','Moore','rose.moore@email.com','555-0118','Las Vegas','NV','US'),
('Sam','Jackson','sam.jackson@email.com','555-0119','Memphis','TN','US'),
('Tina','White','tina.white@email.com','555-0120','Louisville','KY','US'),
('Uma','Harris','uma.harris@email.com','555-0121','Baltimore','MD','US'),
('Victor','Martin','victor.martin@email.com','555-0122','Milwaukee','WI','US'),
('Wendy','Thompson','wendy.thompson@email.com','555-0123','Albuquerque','NM','US'),
('Xander','Garcia','xander.garcia@email.com','555-0124','Tucson','AZ','US'),
('Yara','Martinez','yara.martinez@email.com','555-0125','Fresno','CA','US'),
('Zoe','Robinson','zoe.robinson@email.com','555-0126','Sacramento','CA','US'),
('Aaron','Clark','aaron.clark@email.com','555-0127','Mesa','AZ','US'),
('Beth','Rodriguez','beth.rodriguez@email.com','555-0128','Atlanta','GA','US'),
('Chris','Lewis','chris.lewis@email.com','555-0129','Omaha','NE','US'),
('Diana','Lee','diana.lee@email.com','555-0130','Colorado Springs','CO','US'),
('Ethan','Walker','ethan.walker@email.com','555-0131','Raleigh','NC','US'),
('Fiona','Hall','fiona.hall@email.com','555-0132','Long Beach','CA','US'),
('George','Allen','george.allen@email.com','555-0133','Virginia Beach','VA','US'),
('Hannah','Young','hannah.young@email.com','555-0134','Minneapolis','MN','US'),
('Ian','Hernandez','ian.hernandez@email.com','555-0135','Tampa','FL','US'),
('Julia','King','julia.king@email.com','555-0136','New Orleans','LA','US'),
('Kevin','Wright','kevin.wright@email.com','555-0137','Arlington','TX','US'),
('Laura','Scott','laura.scott@email.com','555-0138','Bakersfield','CA','US'),
('Mike','Torres','mike.torres@email.com','555-0139','Honolulu','HI','US'),
('Nina','Nguyen','nina.nguyen@email.com','555-0140','Anaheim','CA','US'),
('Oscar','Hill','oscar.hill@email.com','555-0141','Aurora','CO','US'),
('Pam','Flores','pam.flores@email.com','555-0142','Santa Ana','CA','US'),
('Ray','Green','ray.green@email.com','555-0143','Corpus Christi','TX','US'),
('Sara','Adams','sara.adams@email.com','555-0144','Riverside','CA','US'),
('Tom','Nelson','tom.nelson@email.com','555-0145','Lexington','KY','US'),
('Ursula','Baker','ursula.baker@email.com','555-0146','Stockton','CA','US'),
('Vince','Carter','vince.carter@email.com','555-0147','Pittsburgh','PA','US'),
('Wanda','Mitchell','wanda.mitchell@email.com','555-0148','Anchorage','AK','US'),
('Ximena','Perez','ximena.perez@email.com','555-0149','Orlando','FL','US'),
('Yusuf','Roberts','yusuf.roberts@email.com','555-0150','Cincinnati','OH','US')
ON CONFLICT (email) DO NOTHING;

-- Orders (120 orders across past 12 months)
INSERT INTO orders (customer_id, status, total_amount, payment_method, created_at, shipped_at, delivered_at)
SELECT
    (1 + (gs % 50)) AS customer_id,
    CASE (gs % 6)
        WHEN 0 THEN 'delivered'
        WHEN 1 THEN 'delivered'
        WHEN 2 THEN 'shipped'
        WHEN 3 THEN 'processing'
        WHEN 4 THEN 'pending'
        ELSE 'cancelled'
    END AS status,
    ROUND((RANDOM() * 400 + 20)::numeric, 2) AS total_amount,
    CASE (gs % 5)
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'paypal'
        WHEN 2 THEN 'debit_card'
        WHEN 3 THEN 'bank_transfer'
        ELSE 'crypto'
    END AS payment_method,
    NOW() - (INTERVAL '1 day' * (gs * 3)) AS created_at,
    CASE WHEN (gs % 6) IN (0,1,2) THEN NOW() - (INTERVAL '1 day' * (gs * 3 - 2)) ELSE NULL END,
    CASE WHEN (gs % 6) IN (0,1)   THEN NOW() - (INTERVAL '1 day' * (gs * 3 - 5)) ELSE NULL END
FROM generate_series(0, 119) gs;

-- Order Items (2–4 items per order)
INSERT INTO order_items (order_id, product_id, quantity, unit_price)
SELECT
    o.id AS order_id,
    (1 + ((o.id + item_offset) % 40)) AS product_id,
    (1 + (o.id % 3)) AS quantity,
    p.price AS unit_price
FROM orders o
CROSS JOIN (SELECT generate_series(0, 2) AS item_offset) items
JOIN products p ON p.id = (1 + ((o.id + items.item_offset) % 40))
ON CONFLICT DO NOTHING;

-- Update order totals from items
UPDATE orders o
SET total_amount = (
    SELECT COALESCE(SUM(subtotal), 0)
    FROM order_items oi WHERE oi.order_id = o.id
);

-- Reviews (80 reviews)
INSERT INTO reviews (product_id, customer_id, rating, comment, created_at)
SELECT
    (1 + (gs % 40)) AS product_id,
    (1 + (gs % 50)) AS customer_id,
    (2 + (gs % 4))  AS rating,
    CASE (gs % 5)
        WHEN 0 THEN 'Excellent product, highly recommend!'
        WHEN 1 THEN 'Good value for money.'
        WHEN 2 THEN 'Decent quality, arrived on time.'
        WHEN 3 THEN 'Not what I expected, but usable.'
        ELSE 'Amazing! Will buy again.'
    END AS comment,
    NOW() - (INTERVAL '1 day' * gs * 4)
FROM generate_series(0, 79) gs
ON CONFLICT (product_id, customer_id) DO NOTHING;
