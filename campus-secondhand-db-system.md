# 1. 调研需求

## 1.1 应用领域

本系统选取的应用领域为**校园二手交易信息管理系统**。

在高校环境中，学生之间频繁进行教材、电子产品及生活用品的二手交易。目前主要依赖社交平台进行信息发布与沟通，存在信息分散、管理混乱、交易不透明等问题。因此，有必要构建一个统一的数据库管理系统，对相关数据进行集中管理。

---

## 1.2 系统目标

本系统旨在实现以下目标：

- 对用户信息、商品信息及交易信息进行统一管理  
- 提高商品信息查询与管理效率  
- 规范交易流程，保证数据一致性  
- 支持多种数据库操作（事务、触发器、存储过程、视图）  

---

## 1.3 功能需求

### （1）用户管理

系统需支持用户的基本管理功能，包括：

- 用户注册与登录  
- 用户信息维护（联系方式、地址等）  
- 用户角色区分（普通用户、管理员）  

---

### （2）商品管理

系统需支持商品信息的管理，包括：

- 商品发布（名称、价格、描述等）  
- 商品分类管理  
- 商品信息修改与删除  
- 商品状态管理（在售、已售）  

---

### （3）订单管理

系统需支持交易过程的管理，包括：

- 创建订单  
- 记录订单明细（商品、数量、价格）  
- 订单状态管理（未完成、已完成）  

---

### （4）收藏与评价管理

系统需支持用户行为数据的管理，包括：

- 收藏商品  
- 取消收藏  
- 对订单进行评价  
- 记录评价内容与评分  

---

### （5）管理员管理

系统需提供后台管理功能，包括：

- 用户管理  
- 商品审核与删除  
- 系统数据维护  

---

## 1.4 数据需求

系统需管理的主要数据对象包括：

- 用户（User）  
- 商品（Product）  
- 商品类别（Category）  
- 订单（OrderInfo）  
- 订单明细（OrderItem）  
- 收藏（Favorite）  
- 评价（Review）  

---

## 1.5 业务特点

本系统具有如下数据库特征：

- 存在多实体关联（用户、商品、订单）  
- 存在多对多关系（用户与商品通过收藏关联）  
- 存在继承关系（用户划分为普通用户与管理员）  
- 需要事务保证多表操作一致性  
- 需要触发器约束数据合法性  
- 需要存储过程封装更新逻辑  
- 需要视图支持复杂查询  

---

# 2. 数据库设计

## （a）ER 图设计

### 2.1 实体及属性

---

### 1. 用户（User）【超类】

- user_id（主键）
- username
- password
- phone
- email
- register_time
- user_type

---

### 2. 学生用户（StudentUser）【子类】

- user_id（主键，外键 → User.user_id）
- student_no
- dormitory
- major

---

### 3. 管理员（AdminUser）【子类】

- user_id（主键，外键 → User.user_id）
- admin_level
- job_no

---

### 4. 商品类别（Category）

- category_id（主键）
- category_name
- parent_id（外键 → Category.category_id）

---

### 5. 商品（Product）

- product_id（主键）
- seller_id（外键 → StudentUser.user_id）
- category_id（外键 → Category.category_id）
- product_name
- price
- stock
- status
- description
- publish_time

---

### 6. 订单（OrderInfo）

- order_id（主键）
- buyer_id（外键 → StudentUser.user_id）
- order_time
- total_amount
- status
- address

---

### 7. 订单明细（OrderItem）

- order_item_id（主键）
- order_id（外键 → OrderInfo.order_id）
- product_id（外键 → Product.product_id）
- quantity
- deal_price

---

### 8. 收藏（Favorite）

- favorite_id（主键）
- user_id（外键 → StudentUser.user_id）
- product_id（外键 → Product.product_id）
- create_time

---

### 9. 评价（Review）

- review_id（主键）
- order_id（外键 → OrderInfo.order_id）
- user_id（外键 → StudentUser.user_id）
- score
- content
- review_time

---

### 2.2 实体之间的联系

---

### （1）用户 —— 商品

- 关系：发布
- 类型：1 : N  
- 描述：一个用户可以发布多个商品，一个商品只能由一个用户发布

---

### （2）商品类别 —— 商品

- 关系：分类
- 类型：1 : N  
- 描述：一个类别下可以有多个商品，一个商品属于一个类别

---

### （3）用户 —— 订单

- 关系：购买
- 类型：1 : N  
- 描述：一个用户可以创建多个订单

---

### （4）订单 —— 订单明细

- 关系：包含
- 类型：1 : N  
- 描述：一个订单包含多个商品明细

---

### （5）商品 —— 订单明细

- 关系：被购买
- 类型：1 : N  
- 描述：一个商品可以出现在多个订单明细中

---

### （6）用户 —— 商品（收藏）

- 关系：收藏
- 类型：M : N  
- 实现方式：通过 Favorite 实体  
- 描述：一个用户可以收藏多个商品，一个商品也可以被多个用户收藏

---

### （7）订单 —— 评价

- 关系：评价
- 类型：1 : 1  
- 描述：一个订单最多对应一条评价

---

### （8）用户继承关系

- User → StudentUser
- User → AdminUser  
- 类型：泛化（Generalization）  
- 描述：用户分为普通用户和管理员，两者继承用户基本属性

---

### 2.3 ER 图说明

本系统 ER 模型包含：

- 实体数：9 个（满足 ≥5 要求）
- 含有子类结构（User 的泛化）
- 含有多对多关系（收藏）
- 含有层级结构（Category 自关联）

该模型结构清晰，能够支持后续关系模式转换及数据库实现。

## （b）关系模式设计

根据（a）中的 ER 模型，将各实体及联系转换为关系模式如下：

---

### 1. User（用户）

User(
    user_id PK,
    username,
    password,
    phone,
    email,
    register_time,
    user_type
)

---

### 2. StudentUser（学生用户）

StudentUser(
    user_id PK, FK → User.user_id,
    student_no,
    dormitory,
    major
)

---

### 3. AdminUser（管理员）

AdminUser(
    user_id PK, FK → User.user_id,
    admin_level,
    job_no
)

---

### 4. Category（商品类别）

Category(
    category_id PK,
    category_name,
    parent_id FK → Category.category_id
)

---

### 5. Product（商品）

Product(
    product_id PK,
    seller_id FK → StudentUser.user_id,
    category_id FK → Category.category_id,
    product_name,
    price,
    stock,
    status,
    description,
    publish_time
)

---

### 6. OrderInfo（订单）

OrderInfo(
    order_id PK,
    buyer_id FK → StudentUser.user_id,
    order_time,
    total_amount,
    status,
    address
)

---

### 7. OrderItem（订单明细）

OrderItem(
    order_item_id PK,
    order_id FK → OrderInfo.order_id,
    product_id FK → Product.product_id,
    quantity,
    deal_price
)

---

### 8. Favorite（收藏）

Favorite(
    favorite_id PK,
    user_id FK → StudentUser.user_id,
    product_id FK → Product.product_id,
    create_time
)

---

### 9. Review（评价）

Review(
    review_id PK,
    order_id FK → OrderInfo.order_id,
    user_id FK → StudentUser.user_id,
    score,
    content,
    review_time
)

---

### 关系模式说明

1. 所有实体均转化为关系表，并设置主键（PK）。
2. 一对多关系通过在“多”的一方设置外键（FK）实现。
3. 多对多关系（用户—商品收藏）通过中间表 Favorite 实现。
4. 继承关系（User → StudentUser / AdminUser）采用“主表 + 子表”方式实现。
5. Category 表通过 parent_id 实现层级（自引用）结构。
6. 各关系模式之间通过外键保持数据一致性与完整性。


## （c）SQL 建表语句

```sql
-- 1. User
CREATE TABLE User (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(100),
    register_time DATETIME,
    user_type VARCHAR(20)
);

-- 2. StudentUser
CREATE TABLE StudentUser (
    user_id INT PRIMARY KEY,
    student_no VARCHAR(50),
    dormitory VARCHAR(100),
    major VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- 3. AdminUser
CREATE TABLE AdminUser (
    user_id INT PRIMARY KEY,
    admin_level INT,
    job_no VARCHAR(50),
    FOREIGN KEY (user_id) REFERENCES User(user_id)
);

-- 4. Category
CREATE TABLE Category (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL,
    parent_id INT,
    FOREIGN KEY (parent_id) REFERENCES Category(category_id)
);

-- 5. Product
CREATE TABLE Product (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    seller_id INT,
    category_id INT,
    product_name VARCHAR(100),
    price DECIMAL(10,2),
    stock INT,
    status VARCHAR(20),
    description TEXT,
    publish_time DATETIME,
    FOREIGN KEY (seller_id) REFERENCES StudentUser(user_id),
    FOREIGN KEY (category_id) REFERENCES Category(category_id)
);

-- 6. OrderInfo
CREATE TABLE OrderInfo (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    buyer_id INT,
    order_time DATETIME,
    total_amount DECIMAL(10,2),
    status VARCHAR(20),
    address VARCHAR(200),
    FOREIGN KEY (buyer_id) REFERENCES StudentUser(user_id)
);

-- 7. OrderItem
CREATE TABLE OrderItem (
    order_item_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    product_id INT,
    quantity INT,
    deal_price DECIMAL(10,2),
    FOREIGN KEY (order_id) REFERENCES OrderInfo(order_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- 8. Favorite
CREATE TABLE Favorite (
    favorite_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    product_id INT,
    create_time DATETIME,
    FOREIGN KEY (user_id) REFERENCES StudentUser(user_id),
    FOREIGN KEY (product_id) REFERENCES Product(product_id)
);

-- 9. Review
CREATE TABLE Review (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT,
    user_id INT,
    score INT,
    content TEXT,
    review_time DATETIME,
    FOREIGN KEY (order_id) REFERENCES OrderInfo(order_id),
    FOREIGN KEY (user_id) REFERENCES StudentUser(user_id)
);
````

---

## （d）查询语句示例

### 1. 单表查询

查询所有在售商品的信息：

```sql
SELECT product_id, product_name, price, stock
FROM Product
WHERE status = '在售';
````

---

### 2. 多表连接查询

查询订单详情（包含买家、商品、数量、价格）：

```sql
SELECT 
    o.order_id,
    u.username AS buyer_name,
    p.product_name,
    oi.quantity,
    oi.deal_price
FROM OrderInfo o
JOIN User u ON o.buyer_id = u.user_id
JOIN OrderItem oi ON o.order_id = oi.order_id
JOIN Product p ON oi.product_id = p.product_id;
```

---

### 3. 多表嵌套查询

查询购买过“高等数学教材”的用户：

```sql
SELECT username
FROM User
WHERE user_id IN (
    SELECT buyer_id
    FROM OrderInfo
    WHERE order_id IN (
        SELECT order_id
        FROM OrderItem
        WHERE product_id = (
            SELECT product_id
            FROM Product
            WHERE product_name = '高等数学教材'
        )
    )
);
```

---

### 4. EXISTS 查询

查询至少发布过一个商品的用户：

```sql
SELECT username
FROM User u
WHERE EXISTS (
    SELECT 1
    FROM Product p
    WHERE p.seller_id = u.user_id
);
```

---

### 5. 聚合操作查询

查询每个用户发布商品的数量：

```sql
SELECT 
    u.username,
    COUNT(p.product_id) AS product_count
FROM User u
LEFT JOIN Product p ON u.user_id = p.seller_id
GROUP BY u.user_id, u.username;
```

---