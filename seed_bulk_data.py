from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pymysql

import app


def main():
    conn = app.db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM `User` WHERE username LIKE 'stu_bulk_%'")
            if cur.fetchone()["total"] > 0:
                print("bulk data already exists, skipped")
                return

            now = datetime.now()

            # 1. 10 rows in User + 10 rows in StudentUser = 20
            student_ids = []
            for i in range(1, 11):
                username = f"stu_bulk_{i:02d}"
                register_time = now - timedelta(days=30 - i)
                cur.execute(
                    """
                    INSERT INTO `User` (username, password, phone, email, register_time, user_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        "123456",
                        f"1391000{i:04d}",
                        f"{username}@example.com",
                        register_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "student",
                    ),
                )
                user_id = cur.lastrowid
                student_ids.append(user_id)
                cur.execute(
                    """
                    INSERT INTO StudentUser (user_id, student_no, dormitory, major)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (
                        user_id,
                        f"2024{i:04d}",
                        f"{(i % 8) + 1}舍{100 + i}",
                        ["计算机", "软件工程", "通信工程", "数学"][i % 4],
                    ),
                )

            # 2. 2 rows in User + 2 rows in AdminUser = 4
            for i in range(1, 3):
                username = f"admin_bulk_{i:02d}"
                cur.execute(
                    """
                    INSERT INTO `User` (username, password, phone, email, register_time, user_type)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        username,
                        "admin123",
                        f"1379000{i:04d}",
                        f"{username}@example.com",
                        now.strftime("%Y-%m-%d %H:%M:%S"),
                        "admin",
                    ),
                )
                user_id = cur.lastrowid
                cur.execute(
                    """
                    INSERT INTO AdminUser (user_id, admin_level, job_no)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, i + 1, f"BULK-A{i:03d}"),
                )

            # 3. 6 rows in Category = 6
            category_names = ["考研资料", "手机配件", "宿舍收纳", "运动器材", "数码外设", "服饰鞋包"]
            category_ids = []
            for name in category_names:
                cur.execute(
                    "INSERT INTO Category (category_name, parent_id) VALUES (%s, %s)",
                    (name, None),
                )
                category_ids.append(cur.lastrowid)

            # 4. 30 rows in Product = 30
            product_ids = []
            product_templates = [
                "高数笔记",
                "英语真题",
                "机械键盘",
                "鼠标",
                "篮球",
                "羽毛球拍",
                "收纳箱",
                "台灯",
                "耳机",
                "移动硬盘",
            ]
            for i in range(30):
                seller_id = student_ids[i % len(student_ids)]
                category_id = category_ids[i % len(category_ids)]
                product_name = f"{product_templates[i % len(product_templates)]}{i + 1}"
                price = Decimal("12.00") + Decimal(i * 3)
                stock = 1 if i % 3 else 2
                status = "在售"
                description = f"演示商品{i + 1}，用于数据库课程展示。"
                publish_time = (now - timedelta(days=i % 12, hours=i % 8)).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """
                    INSERT INTO Product (
                        seller_id, category_id, product_name, price, stock, status, description, publish_time
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        seller_id,
                        category_id,
                        product_name,
                        str(price),
                        stock,
                        status,
                        description,
                        publish_time,
                    ),
                )
                product_ids.append(cur.lastrowid)

            # 5. 15 rows in OrderInfo + 15 rows in OrderItem = 30
            order_ids = []
            review_candidates = []
            for i in range(15):
                buyer_id = student_ids[(i + 3) % len(student_ids)]
                product_id = product_ids[i]

                cur.execute(
                    "SELECT seller_id, price, product_name FROM Product WHERE product_id = %s",
                    (product_id,),
                )
                product_row = cur.fetchone()

                # Ensure buyer and seller are not the same.
                if buyer_id == product_row["seller_id"]:
                    buyer_id = student_ids[(i + 5) % len(student_ids)]

                order_time = (now - timedelta(days=i % 10)).strftime("%Y-%m-%d %H:%M:%S")
                total_amount = product_row["price"]
                status = "已完成"
                address = f"{(i % 8) + 1}舍{300 + i}"
                cur.execute(
                    """
                    INSERT INTO OrderInfo (buyer_id, order_time, total_amount, status, address)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (buyer_id, order_time, total_amount, status, address),
                )
                order_id = cur.lastrowid
                order_ids.append(order_id)
                review_candidates.append((order_id, buyer_id, product_row["product_name"]))

                cur.execute(
                    """
                    INSERT INTO OrderItem (order_id, product_id, quantity, deal_price)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (order_id, product_id, 1, product_row["price"]),
                )

                cur.execute(
                    "UPDATE Product SET stock = 0, status = '已售' WHERE product_id = %s",
                    (product_id,),
                )

            # 6. 5 rows in Favorite = 5
            for i in range(5):
                user_id = student_ids[(i + 1) % len(student_ids)]
                product_id = product_ids[20 + i]
                create_time = (now - timedelta(days=i)).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """
                    INSERT INTO Favorite (user_id, product_id, create_time)
                    VALUES (%s, %s, %s)
                    """,
                    (user_id, product_id, create_time),
                )

            # 7. 5 rows in Review = 5
            review_texts = [
                "商品与描述一致，交易顺利。",
                "成色不错，性价比很高。",
                "沟通顺畅，推荐购买。",
                "发货很快，物品保存完好。",
                "整体满意，适合课程展示。",
            ]
            for i in range(5):
                order_id, user_id, product_name = review_candidates[i]
                review_time = (now - timedelta(hours=i * 3)).strftime("%Y-%m-%d %H:%M:%S")
                cur.execute(
                    """
                    INSERT INTO Review (order_id, user_id, score, content, review_time)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        order_id,
                        user_id,
                        5 - (i % 2),
                        f"{review_texts[i]} 商品：{product_name}",
                        review_time,
                    ),
                )

        conn.commit()
        print("inserted 100 rows of demo data")
    except pymysql.MySQLError:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
