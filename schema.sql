CREATE TABLE IF NOT EXISTS `User` (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    register_time DATETIME,
    user_type VARCHAR(20) NOT NULL,
    CONSTRAINT chk_user_type CHECK (user_type IN ('student', 'admin'))
);

CREATE TABLE IF NOT EXISTS StudentUser (
    user_id INT PRIMARY KEY,
    student_no VARCHAR(50),
    dormitory VARCHAR(100),
    major VARCHAR(100),
    CONSTRAINT fk_student_user FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

CREATE TABLE IF NOT EXISTS AdminUser (
    user_id INT PRIMARY KEY,
    admin_level INT,
    job_no VARCHAR(50),
    CONSTRAINT fk_admin_user FOREIGN KEY (user_id) REFERENCES `User`(user_id)
);

CREATE TABLE IF NOT EXISTS Category (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    parent_id INT NULL,
    CONSTRAINT fk_category_parent FOREIGN KEY (parent_id) REFERENCES Category(category_id)
);

CREATE TABLE IF NOT EXISTS Product (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT,
    category_id INT,
    product_name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 1,
    status VARCHAR(20) NOT NULL,
    description TEXT,
    publish_time DATETIME,
    CONSTRAINT fk_product_seller FOREIGN KEY (seller_id) REFERENCES StudentUser(user_id),
    CONSTRAINT fk_product_category FOREIGN KEY (category_id) REFERENCES Category(category_id),
    CONSTRAINT chk_product_price CHECK (price >= 0),
    CONSTRAINT chk_product_stock CHECK (stock >= 0),
    CONSTRAINT chk_product_status CHECK (status IN ('在售', '已售'))
);

CREATE TABLE IF NOT EXISTS OrderInfo (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT,
    order_time DATETIME,
    total_amount DECIMAL(10,2),
    status VARCHAR(20),
    address VARCHAR(200),
    CONSTRAINT fk_order_buyer FOREIGN KEY (buyer_id) REFERENCES StudentUser(user_id),
    CONSTRAINT chk_order_total CHECK (total_amount >= 0)
);

CREATE TABLE IF NOT EXISTS OrderItem (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    deal_price DECIMAL(10,2),
    CONSTRAINT fk_order_item_order FOREIGN KEY (order_id) REFERENCES OrderInfo(order_id),
    CONSTRAINT fk_order_item_product FOREIGN KEY (product_id) REFERENCES Product(product_id),
    CONSTRAINT chk_order_item_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_item_price CHECK (deal_price >= 0)
);

CREATE TABLE IF NOT EXISTS Favorite (
    favorite_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_id INT,
    create_time DATETIME,
    CONSTRAINT fk_favorite_user FOREIGN KEY (user_id) REFERENCES StudentUser(user_id),
    CONSTRAINT fk_favorite_product FOREIGN KEY (product_id) REFERENCES Product(product_id),
    CONSTRAINT uq_favorite UNIQUE (user_id, product_id)
);

CREATE TABLE IF NOT EXISTS Review (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    user_id INT,
    score INT,
    content TEXT,
    review_time DATETIME,
    CONSTRAINT fk_review_order FOREIGN KEY (order_id) REFERENCES OrderInfo(order_id),
    CONSTRAINT fk_review_user FOREIGN KEY (user_id) REFERENCES StudentUser(user_id),
    CONSTRAINT chk_review_score CHECK (score BETWEEN 1 AND 5),
    CONSTRAINT uq_review_order UNIQUE (order_id)
);

CREATE OR REPLACE VIEW v_available_product AS
SELECT p.product_id,p.product_name,c.category_name,u.username AS seller_name,p.price,p.stock,p.status,p.description,p.publish_time
FROM Product p
LEFT JOIN Category c ON p.category_id = c.category_id
LEFT JOIN `User` u ON p.seller_id = u.user_id
WHERE p.status = '在售';
