from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import pymysql
from pymysql.cursors import DictCursor

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / 'schema.sql'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'campus_secondhand'


def server_conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False,
    )


def db_conn():
    return pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4',
        cursorclass=DictCursor,
        autocommit=False,
    )


def exec_script(conn, text: str):
    with conn.cursor() as cur:
        for stmt in [s.strip() for s in text.split(';') if s.strip()]:
            cur.execute(stmt)


def init_database():
    conn = server_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.commit()
    finally:
        conn.close()

    conn = db_conn()
    try:
        exec_script(conn, SCHEMA_PATH.read_text(encoding='utf-8-sig'))
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM `User`")
            if cur.fetchone()['total'] == 0:
                seed_demo_data(conn)
            ensure_demo_orders(conn)
        conn.commit()
    finally:
        conn.close()


def seed_demo_data(conn):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO `User` '
            '(username,password,phone,email,register_time,user_type) '
            'VALUES (%s,%s,%s,%s,%s,%s)',
            ('alice', '123456', '13800000001', 'alice@example.com', now, 'student'),
        )
        alice_id = cur.lastrowid
        cur.execute(
            'INSERT INTO StudentUser '
            '(user_id,student_no,dormitory,major) '
            'VALUES (%s,%s,%s,%s)',
            (alice_id, '20230001', '1舍101', '计算机科学与技术'),
        )
        cur.execute(
            'INSERT INTO `User` '
            '(username,password,phone,email,register_time,user_type) '
            'VALUES (%s,%s,%s,%s,%s,%s)',
            ('bob', '123456', '13800000002', 'bob@example.com', now, 'student'),
        )
        bob_id = cur.lastrowid
        cur.execute(
            'INSERT INTO StudentUser '
            '(user_id,student_no,dormitory,major) '
            'VALUES (%s,%s,%s,%s)',
            (bob_id, '20230002', '2舍305', '软件工程'),
        )
        cur.execute(
            'INSERT INTO `User` '
            '(username,password,phone,email,register_time,user_type) '
            'VALUES (%s,%s,%s,%s,%s,%s)',
            ('admin', 'admin123', '13900000000', 'admin@example.com', now, 'admin'),
        )
        admin_id = cur.lastrowid
        cur.execute("INSERT INTO AdminUser (user_id,admin_level,job_no) VALUES (%s,%s,%s)", (admin_id, 1, 'A001'))
        cur.executemany(
            'INSERT INTO Category (category_name,parent_id) VALUES (%s,%s)',
            [('教材书籍', None), ('电子产品', None), ('生活用品', None)],
        )
        cur.execute("SELECT category_id, category_name FROM Category")
        cmap = {r['category_name']: r['category_id'] for r in cur.fetchall()}
        cur.executemany(
            'INSERT INTO Product '
            '(seller_id,category_id,product_name,price,stock,status,'
            'description,publish_time) '
            'VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',
            [
                (alice_id, cmap['教材书籍'], '高等数学教材', 25.00, 3, '在售', '九成新，适合大一课程使用。', now),
                (bob_id, cmap['电子产品'], '二手蓝牙耳机', 88.00, 1, '在售', '功能正常，带充电盒。', now),
                (alice_id, cmap['生活用品'], '台灯', 30.00, 1, '已售', '宿舍常用台灯。', now),
            ],
        )


def ensure_demo_orders(conn):
    with conn.cursor() as cur:
        cur.execute('SELECT COUNT(*) AS total FROM OrderInfo')
        if cur.fetchone()['total'] > 0:
            return
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        cur.execute("SELECT user_id, username FROM `User` WHERE username IN (%s,%s)", ('alice', 'bob'))
        users = {r['username']: r['user_id'] for r in cur.fetchall()}
        cur.execute(
            'SELECT product_id, product_name, price '
            'FROM Product WHERE product_name IN (%s,%s)',
            ('高等数学教材', '二手蓝牙耳机'),
        )
        products = {r['product_name']: r for r in cur.fetchall()}
        if 'alice' in users and '二手蓝牙耳机' in products:
            p = products['二手蓝牙耳机']
            cur.execute(
                'INSERT INTO OrderInfo '
                '(buyer_id,order_time,total_amount,status,address) '
                'VALUES (%s,%s,%s,%s,%s)',
                (users['alice'], now, p['price'], '已完成', '1舍101'),
            )
            oid = cur.lastrowid
            cur.execute(
                'INSERT INTO OrderItem '
                '(order_id,product_id,quantity,deal_price) '
                'VALUES (%s,%s,%s,%s)',
                (oid, p['product_id'], 1, p['price']),
            )
        if 'bob' in users and '高等数学教材' in products:
            p = products['高等数学教材']
            cur.execute(
                'INSERT INTO OrderInfo '
                '(buyer_id,order_time,total_amount,status,address) '
                'VALUES (%s,%s,%s,%s,%s)',
                (users['bob'], now, p['price'], '已完成', '2舍305'),
            )
            oid = cur.lastrowid
            cur.execute(
                'INSERT INTO OrderItem '
                '(order_id,product_id,quantity,deal_price) '
                'VALUES (%s,%s,%s,%s)',
                (oid, p['product_id'], 1, p['price']),
            )


class GridWindow(tk.Toplevel):
    def __init__(self, parent, title, columns, rows, widths, actions=None):
        super().__init__(parent)
        self.title(title)
        self.geometry('860x380')
        self.actions = actions or []
        box = ttk.Frame(self, padding=12)
        box.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(box, columns=columns, show='headings')
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=widths.get(c, 120), anchor='center')
        sy = ttk.Scrollbar(box, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(box, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        box.columnconfigure(0, weight=1)
        box.rowconfigure(0, weight=1)
        for row in rows:
            self.tree.insert('', 'end', values=row)
        if self.actions:
            bar = ttk.Frame(self, padding=(12, 0, 12, 12))
            bar.pack(fill='x')
            for action in self.actions:
                ttk.Button(bar, text=action['text'], command=action['command']).pack(side='left', padx=(0, 8))

    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请先选中一条记录。', parent=self)
            return None
        return self.tree.item(sel[0], 'values')

class ReviewDialog(tk.Toplevel):
    def __init__(self, parent, current_user, order_id, product_name):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.order_id = order_id
        self.title('商品评价')
        self.geometry('420x280')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        box = ttk.Frame(self, padding=16)
        box.pack(fill='both', expand=True)
        ttk.Label(
            box,
            text=f'评价商品：{product_name}',
            font=('Microsoft YaHei UI', 11, 'bold'),
        ).pack(anchor='w', pady=(0, 12))
        row = ttk.Frame(box)
        row.pack(fill='x', pady=(0, 10))
        ttk.Label(row, text='评分').pack(side='left')
        self.score_var = tk.StringVar(value='5')
        ttk.Combobox(
            row,
            textvariable=self.score_var,
            state='readonly',
            width=8,
            values=['5', '4', '3', '2', '1'],
        ).pack(side='left', padx=(8, 0))
        ttk.Label(box, text='评价内容').pack(anchor='w')
        self.content = tk.Text(box, height=7)
        self.content.pack(fill='both', expand=True, pady=(6, 12))
        btn = ttk.Frame(box)
        btn.pack(fill='x')
        ttk.Button(btn, text='提交评价', command=self.save).pack(side='left', expand=True, fill='x', padx=(0, 6))
        ttk.Button(btn, text='取消', command=self.destroy).pack(side='left', expand=True, fill='x', padx=(6, 0))

    def save(self):
        text = self.content.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning('提示', '请填写评价内容。', parent=self)
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT review_id FROM Review WHERE order_id = %s', (self.order_id,))
                if cur.fetchone():
                    messagebox.showinfo('提示', '该订单已经评价过了。', parent=self)
                    return
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute(
                    'INSERT INTO Review '
                    '(order_id,user_id,score,content,review_time) '
                    'VALUES (%s,%s,%s,%s,%s)',
                    (
                        self.order_id,
                        self.current_user['user_id'],
                        int(self.score_var.get()),
                        text,
                        now,
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        self.parent.show_my_reviews()
        messagebox.showinfo('成功', '评价已保存到 MySQL。', parent=self)
        self.destroy()


class BuyDialog(tk.Toplevel):
    def __init__(self, parent, current_user, product):
        super().__init__(parent)
        self.parent = parent
        self.current_user = current_user
        self.product = product
        self.title('购买商品')
        self.geometry('420x260')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        box = ttk.Frame(self, padding=16)
        box.pack(fill='both', expand=True)
        ttk.Label(
            box,
            text=f"购买商品：{product['product_name']}",
            font=('Microsoft YaHei UI', 11, 'bold'),
        ).pack(anchor='w', pady=(0, 12))
        ttk.Label(
            box,
            text=f"单价：{float(product['price']):.2f}    当前库存：{product['stock']}",
        ).pack(anchor='w', pady=(0, 10))
        r1 = ttk.Frame(box)
        r1.pack(fill='x', pady=(0, 10))
        ttk.Label(r1, text='购买数量').pack(side='left')
        self.qty_var = tk.StringVar(value='1')
        ttk.Entry(r1, textvariable=self.qty_var, width=12).pack(side='left', padx=(8, 0))
        r2 = ttk.Frame(box)
        r2.pack(fill='x', pady=(0, 12))
        ttk.Label(r2, text='收货地址').pack(side='left')
        self.addr_var = tk.StringVar(value='校园宿舍')
        ttk.Entry(r2, textvariable=self.addr_var, width=24).pack(side='left', padx=(8, 0))
        self.total = ttk.Label(box, text='预计金额：0.00')
        self.total.pack(anchor='w', pady=(0, 12))
        self.qty_var.trace_add('write', self.refresh_total)
        self.refresh_total()
        btn = ttk.Frame(box)
        btn.pack(fill='x')
        ttk.Button(btn, text='确认购买', command=self.submit).pack(side='left', expand=True, fill='x', padx=(0, 6))
        ttk.Button(btn, text='取消', command=self.destroy).pack(side='left', expand=True, fill='x', padx=(6, 0))

    def refresh_total(self, *_args):
        try:
            qty = int(self.qty_var.get().strip() or '0')
        except ValueError:
            qty = 0
        self.total.config(text=f"预计金额：{qty * float(self.product['price']):.2f}")

    def submit(self):
        try:
            qty = int(self.qty_var.get().strip())
        except ValueError:
            messagebox.showerror('输入错误', '购买数量必须是整数。', parent=self)
            return
        addr = self.addr_var.get().strip()
        if qty <= 0:
            messagebox.showwarning('提示', '购买数量必须大于 0。', parent=self)
            return
        if not addr:
            messagebox.showwarning('提示', '请填写收货地址。', parent=self)
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT product_id, product_name, seller_id, price, stock, status '
                    'FROM Product WHERE product_id = %s FOR UPDATE',
                    (self.product['product_id'],),
                )
                p = cur.fetchone()
                if not p:
                    messagebox.showerror('购买失败', '商品不存在。', parent=self)
                    return
                if p['status'] != '在售':
                    messagebox.showerror('购买失败', '该商品当前不是在售状态。', parent=self)
                    return
                if qty > p['stock']:
                    messagebox.showerror('购买失败', '库存不足。', parent=self)
                    return
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                total = qty * float(p['price'])
                cur.execute(
                    'INSERT INTO OrderInfo '
                    '(buyer_id,order_time,total_amount,status,address) '
                    'VALUES (%s,%s,%s,%s,%s)',
                    (self.current_user['user_id'], now, total, '已完成', addr),
                )
                oid = cur.lastrowid
                cur.execute(
                    'INSERT INTO OrderItem '
                    '(order_id,product_id,quantity,deal_price) '
                    'VALUES (%s,%s,%s,%s)',
                    (oid, p['product_id'], qty, p['price']),
                )
                cur.execute('CALL update_product_after_order(%s)', (oid,))
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('购买失败', f'写入订单失败：{exc}', parent=self)
            return
        finally:
            conn.close()
        self.parent.refresh_products()
        messagebox.showinfo('成功', '订单已创建，购买完成。', parent=self)
        self.destroy()


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('校园二手交易系统 - MySQL 登录')
        self.root.geometry('380x240')
        self.root.resizable(False, False)
        box = ttk.Frame(root, padding=20)
        box.pack(fill='both', expand=True)
        ttk.Label(box, text='MySQL 数据库功能演示', font=('Microsoft YaHei UI', 16, 'bold')).pack(pady=(0, 18))
        form = ttk.Frame(box)
        form.pack(fill='x')
        ttk.Label(form, text='用户名').grid(row=0, column=0, sticky='w', pady=8)
        self.user_var = tk.StringVar(value='alice')
        ttk.Entry(form, textvariable=self.user_var, width=25).grid(row=0, column=1, sticky='ew', pady=8)
        ttk.Label(form, text='密码').grid(row=1, column=0, sticky='w', pady=8)
        self.pass_var = tk.StringVar(value='123456')
        ttk.Entry(form, textvariable=self.pass_var, show='*', width=25).grid(row=1, column=1, sticky='ew', pady=8)
        form.columnconfigure(1, weight=1)
        ttk.Button(box, text='登录', command=self.login).pack(fill='x', pady=(18, 8))
        ttk.Label(box, text='演示账号: alice / 123456    管理员: admin / admin123', foreground='#666666').pack()
        ttk.Label(box, text=f'MySQL: {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}', foreground='#666666').pack(pady=(6, 0))

    def login(self):
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT user_id, username, user_type '
                    'FROM `User` WHERE username = %s AND password = %s',
                    (self.user_var.get().strip(), self.pass_var.get().strip()),
                )
                row = cur.fetchone()
        finally:
            conn.close()
        if not row:
            messagebox.showerror('登录失败', '用户名或密码错误。')
            return
        self.root.destroy()
        nxt = tk.Tk()
        ProductWindow(nxt, row)
        nxt.mainloop()

class AddProductDialog(tk.Toplevel):
    def __init__(self, owner, current_user):
        super().__init__(owner.root)
        self.owner = owner
        self.current_user = current_user
        self.title('添加商品')
        self.geometry('420x340')
        self.resizable(False, False)
        self.transient(owner.root)
        self.grab_set()
        if current_user['user_type'] != 'student':
            messagebox.showinfo('提示', '只有学生用户可以发布商品。', parent=self)
            self.destroy()
            return
        self.cmap = owner.load_categories()
        box = ttk.Frame(self, padding=16)
        box.pack(fill='both', expand=True)
        self.name_var = tk.StringVar()
        self.cat_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar(value='1')
        self.status_var = tk.StringVar(value='在售')
        ttk.Label(box, text='商品名称').grid(row=0, column=0, sticky='w', pady=6)
        ttk.Entry(box, textvariable=self.name_var, width=28).grid(row=0, column=1, sticky='ew', pady=6)
        ttk.Label(box, text='商品类别').grid(row=1, column=0, sticky='w', pady=6)
        combo = ttk.Combobox(box, textvariable=self.cat_var, state='readonly', values=list(self.cmap.keys()))
        combo.grid(row=1, column=1, sticky='ew', pady=6)
        if self.cmap:
            combo.current(0)
        ttk.Label(box, text='价格').grid(row=2, column=0, sticky='w', pady=6)
        ttk.Entry(box, textvariable=self.price_var, width=28).grid(row=2, column=1, sticky='ew', pady=6)
        ttk.Label(box, text='库存').grid(row=3, column=0, sticky='w', pady=6)
        ttk.Entry(box, textvariable=self.stock_var, width=28).grid(row=3, column=1, sticky='ew', pady=6)
        ttk.Label(box, text='状态').grid(row=4, column=0, sticky='w', pady=6)
        sc = ttk.Combobox(box, textvariable=self.status_var, state='readonly', values=['在售', '已售'])
        sc.grid(row=4, column=1, sticky='ew', pady=6)
        sc.current(0)
        ttk.Label(box, text='商品描述').grid(row=5, column=0, sticky='nw', pady=6)
        self.desc = tk.Text(box, height=6, width=28)
        self.desc.grid(row=5, column=1, sticky='ew', pady=6)
        btn = ttk.Frame(box)
        btn.grid(row=6, column=0, columnspan=2, sticky='ew', pady=(14, 0))
        ttk.Button(btn, text='保存', command=self.save).pack(side='left', expand=True, fill='x', padx=(0, 6))
        ttk.Button(btn, text='取消', command=self.destroy).pack(side='left', expand=True, fill='x', padx=(6, 0))
        box.columnconfigure(1, weight=1)

    def save(self):
        try:
            price = float(self.price_var.get().strip())
            stock = int(self.stock_var.get().strip())
        except ValueError:
            messagebox.showerror('输入错误', '价格必须是数字，库存必须是整数。', parent=self)
            return
        name = self.name_var.get().strip()
        cat = self.cat_var.get().strip()
        if not name or not cat:
            messagebox.showwarning('提示', '请填写商品名称并选择类别。', parent=self)
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'INSERT INTO Product '
                    '(seller_id, category_id, product_name, price, stock, '
                    'status, description, publish_time) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (
                        self.current_user['user_id'],
                        self.cmap[cat],
                        name,
                        price,
                        stock,
                        self.status_var.get(),
                        self.desc.get('1.0', 'end').strip(),
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    )
                )
            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('保存失败', f'写入 MySQL 失败：{exc}', parent=self)
            return
        finally:
            conn.close()
        self.owner.refresh_products()
        messagebox.showinfo('成功', '商品已添加到 MySQL。', parent=self)
        self.destroy()


class ProductWindow:
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user
        self.cart_items = []
        root.title('校园二手交易系统 - 商品列表')
        root.geometry('1160x580')
        top = ttk.Frame(root, padding=16)
        top.pack(fill='x')
        ttk.Label(
            top,
            text=f"当前用户：{current_user['username']}  ({current_user['user_type']})",
            font=('Microsoft YaHei UI', 11, 'bold'),
        ).pack(side='left')
        search = ttk.Frame(root, padding=(16, 0, 16, 10))
        search.pack(fill='x')
        self.keyword_var = tk.StringVar()
        self.status_var = tk.StringVar(value='全部')
        ttk.Label(search, text='商品名').pack(side='left')
        ttk.Entry(search, textvariable=self.keyword_var, width=24).pack(side='left', padx=(8, 12))
        ttk.Label(search, text='状态').pack(side='left')
        sc = ttk.Combobox(search, textvariable=self.status_var, state='readonly', width=10, values=['全部', '在售', '已售'])
        sc.pack(side='left', padx=(8, 12))
        sc.current(0)
        ttk.Button(search, text='查询', command=self.refresh_products).pack(side='left')
        ttk.Button(search, text='重置', command=self.reset_filters).pack(side='left', padx=(8, 0))
        bar = ttk.Frame(root, padding=(16, 0, 16, 10))
        bar.pack(fill='x')
        for text, cmd in [
            ('添加商品', lambda: AddProductDialog(self, self.current_user)),
            ('购买选中商品', self.buy_product),
            ('加入待下单列表', self.add_to_cart),
            ('查看待下单列表', self.show_cart),
            ('收藏选中商品', self.favorite_product),
            ('查看选中商品评价', self.view_product_reviews),
            ('删除选中商品', self.delete_product),
            ('我的收藏', self.show_my_favorites),
            ('我的评价', self.show_my_reviews),
            ('我的订单', self.show_my_orders),
            ('刷新列表', self.refresh_products),
        ]:
            ttk.Button(bar, text=text, command=cmd).pack(side='left', padx=(0, 10))
        frame = ttk.Frame(root, padding=(16, 0, 16, 16))
        frame.pack(fill='both', expand=True)
        cols = (
            'product_id', 'product_name', 'category_name', 'seller_name',
            'price', 'stock', 'status', 'publish_time', 'description',
        )
        heads = {
            'product_id': 'ID',
            'product_name': '商品名称',
            'category_name': '类别',
            'seller_name': '卖家',
            'price': '价格',
            'stock': '库存',
            'status': '状态',
            'publish_time': '发布时间',
            'description': '描述',
        }
        widths = {
            'product_id': 60,
            'product_name': 150,
            'category_name': 100,
            'seller_name': 100,
            'price': 80,
            'stock': 60,
            'status': 70,
            'publish_time': 150,
            'description': 320,
        }
        self.tree = ttk.Treeview(frame, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=heads[c])
            self.tree.column(c, width=widths[c], anchor='center')
        sy = ttk.Scrollbar(frame, orient='vertical', command=self.tree.yview)
        sx = ttk.Scrollbar(frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self.tree.grid(row=0, column=0, sticky='nsew')
        sy.grid(row=0, column=1, sticky='ns')
        sx.grid(row=1, column=0, sticky='ew')
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        self.refresh_products()

    def is_student(self):
        return self.current_user['user_type'] == 'student'

    def load_categories(self):
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT category_id, category_name FROM Category ORDER BY category_id')
                return {r['category_name']: r['category_id'] for r in cur.fetchall()}
        finally:
            conn.close()

    def reset_filters(self):
        self.keyword_var.set('')
        self.status_var.set('全部')
        self.refresh_products()

    def selected_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请先选中一条商品记录。')
            return None
        pid = int(self.tree.item(sel[0], 'values')[0])
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT product_id, product_name, seller_id, status '
                    'FROM Product WHERE product_id = %s',
                    (pid,),
                )
                return cur.fetchone()
        finally:
            conn.close()

    def refresh_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        params = []
        kw = self.keyword_var.get().strip()
        st = self.status_var.get().strip()

        if st == '在售':
            sql = (
                'SELECT product_id, product_name, category_name, seller_name, '
                'price, stock, status, publish_time, description '
                'FROM v_available_product WHERE 1=1'
            )
            if kw:
                sql += ' AND product_name LIKE %s'
                params.append(f'%{kw}%')
            sql += ' ORDER BY product_id DESC'
        else:
            sql = (
                'SELECT p.product_id,p.product_name,c.category_name,'
                'u.username AS seller_name,p.price,p.stock,p.status,'
                'p.publish_time,p.description '
                'FROM Product p '
                'LEFT JOIN Category c ON p.category_id = c.category_id '
                'LEFT JOIN `User` u ON p.seller_id = u.user_id '
                'WHERE 1=1'
            )
            if kw:
                sql += ' AND p.product_name LIKE %s'
                params.append(f'%{kw}%')
            if st == '已售':
                sql += ' AND p.status = %s'
                params.append(st)
            sql += ' ORDER BY p.product_id DESC'

        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        finally:
            conn.close()
        for r in rows:
            self.tree.insert(
                '',
                'end',
                values=(
                    r['product_id'],
                    r['product_name'],
                    r['category_name'] or '',
                    r['seller_name'] or '',
                    f"{float(r['price']):.2f}",
                    r['stock'],
                    r['status'],
                    r['publish_time'] or '',
                    r['description'] or '',
                ),
            )

    def buy_product(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以购买商品。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            messagebox.showinfo('提示', '不能购买自己发布的商品。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT product_id, product_name, seller_id, price, stock, status '
                    'FROM Product WHERE product_id = %s',
                    (p['product_id'],),
                )
                detail = cur.fetchone()
        finally:
            conn.close()
        if not detail:
            messagebox.showerror('提示', '商品不存在。')
            return
        if detail['status'] != '在售' or detail['stock'] <= 0:
            messagebox.showinfo('提示', '该商品当前不可购买。')
            return
        BuyDialog(self.root, self.current_user, detail)

    def add_to_cart(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以下单。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            messagebox.showinfo('提示', '不能购买自己发布的商品。')
            return

        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT product_id, product_name, seller_id, price, stock, status '
                    'FROM Product WHERE product_id = %s',
                    (p['product_id'],),
                )
                detail = cur.fetchone()
        finally:
            conn.close()

        if not detail:
            messagebox.showerror('提示', '商品不存在。')
            return
        if detail['status'] != '在售' or detail['stock'] <= 0:
            messagebox.showinfo('提示', '该商品当前不可加入待下单列表。')
            return
        if any(item['product_id'] == detail['product_id'] for item in self.cart_items):
            messagebox.showinfo('提示', '这个商品已经在待下单列表里了。')
            return

        self.cart_items.append(
            {
                'product_id': detail['product_id'],
                'product_name': detail['product_name'],
                'price': float(detail['price']),
                'quantity': 1,
            }
        )
        messagebox.showinfo('成功', f"已加入待下单列表：{detail['product_name']}")

    def show_cart(self):
        if not self.cart_items:
            messagebox.showinfo('提示', '待下单列表为空。')
            return

        rows = [
            (
                item['product_id'],
                item['product_name'],
                item['quantity'],
                f"{item['price']:.2f}",
                f"{item['price'] * item['quantity']:.2f}",
            )
            for item in self.cart_items
        ]

        win = GridWindow(
            self.root,
            '待下单列表',
            ('商品ID', '商品名称', '数量', '单价', '小计'),
            rows,
            {'商品名称': 220},
            actions=[
                {'text': '移除选中商品', 'command': lambda: self.remove_cart_item(win)},
                {'text': '结算生成订单', 'command': lambda: self.checkout_cart(win)},
                {'text': '清空待下单列表', 'command': lambda: self.clear_cart(win)},
            ],
        )

    def remove_cart_item(self, win):
        values = win.selected()
        if not values:
            return
        product_id = int(values[0])
        self.cart_items = [item for item in self.cart_items if item['product_id'] != product_id]
        messagebox.showinfo('成功', '已从待下单列表移除。', parent=win)
        win.destroy()

    def clear_cart(self, win):
        if not messagebox.askyesno('确认清空', '确定清空待下单列表吗？', parent=win):
            return
        self.cart_items = []
        messagebox.showinfo('成功', '待下单列表已清空。', parent=win)
        win.destroy()

    def checkout_cart(self, win):
        if not self.cart_items:
            messagebox.showinfo('提示', '待下单列表为空。', parent=win)
            return

        address = simpledialog.askstring('结算订单', '请输入收货地址：', parent=win)
        if address is None:
            return
        address = address.strip()
        if not address:
            messagebox.showwarning('提示', '收货地址不能为空。', parent=win)
            return

        conn = db_conn()
        try:
            product_rows = []
            total_amount = 0.0
            with conn.cursor() as cur:
                for item in self.cart_items:
                    cur.execute(
                        'SELECT product_id, product_name, price, stock, status '
                        'FROM Product WHERE product_id = %s FOR UPDATE',
                        (item['product_id'],),
                    )
                    row = cur.fetchone()
                    if not row:
                        messagebox.showerror('结算失败', f"商品不存在：{item['product_name']}", parent=win)
                        return
                    if row['status'] != '在售' or row['stock'] <= 0:
                        messagebox.showerror('结算失败', f"商品不可购买：{row['product_name']}", parent=win)
                        return
                    product_rows.append(row)
                    total_amount += float(row['price'])

                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute(
                    'INSERT INTO OrderInfo '
                    '(buyer_id,order_time,total_amount,status,address) '
                    'VALUES (%s,%s,%s,%s,%s)',
                    (self.current_user['user_id'], now, total_amount, '已完成', address),
                )
                order_id = cur.lastrowid

                for row in product_rows:
                    cur.execute(
                        'INSERT INTO OrderItem '
                        '(order_id,product_id,quantity,deal_price) '
                        'VALUES (%s,%s,%s,%s)',
                        (order_id, row['product_id'], 1, row['price']),
                    )

                cur.execute('CALL update_product_after_order(%s)', (order_id,))

            conn.commit()
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('结算失败', f'写入订单失败：{exc}', parent=win)
            return
        finally:
            conn.close()

        self.cart_items = []
        self.refresh_products()
        messagebox.showinfo('成功', '已生成一个包含多个商品明细的订单。', parent=win)
        win.destroy()

    def favorite_product(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以收藏商品。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            messagebox.showinfo('提示', '不能收藏自己发布的商品。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'SELECT favorite_id FROM Favorite '
                    'WHERE user_id = %s AND product_id = %s',
                    (self.current_user['user_id'], p['product_id']),
                )
                if cur.fetchone():
                    messagebox.showinfo('提示', '你已经收藏过这个商品了。')
                    return
                cur.execute(
                    'INSERT INTO Favorite '
                    '(user_id,product_id,create_time) '
                    'VALUES (%s,%s,%s)',
                    (
                        self.current_user['user_id'],
                        p['product_id'],
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    ),
                )
            conn.commit()
        finally:
            conn.close()
        messagebox.showinfo('成功', '商品已收藏到 MySQL。')

    def show_my_favorites(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有收藏记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        f.favorite_id AS 收藏ID,
                        p.product_name AS 商品名称,
                        c.category_name AS 商品类别,
                        u.username AS 卖家,
                        p.price AS 价格,
                        f.create_time AS 收藏时间
                    FROM Favorite f
                    JOIN Product p ON f.product_id = p.product_id
                    LEFT JOIN Category c ON p.category_id = c.category_id
                    LEFT JOIN `User` u ON p.seller_id = u.user_id
                    WHERE f.user_id = %s
                    ORDER BY f.favorite_id DESC
                    """,
                    (self.current_user['user_id'],),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        win = GridWindow(
            self.root,
            '我的收藏',
            ('收藏ID', '商品名称', '商品类别', '卖家', '价格', '收藏时间'),
            [tuple(r.values()) for r in rows],
            {'商品名称': 180, '商品类别': 120, '卖家': 100, '收藏时间': 180},
            actions=[{'text': '取消选中收藏', 'command': lambda: self.cancel_favorite(win)}],
        )

    def cancel_favorite(self, win):
        values = win.selected()
        if not values:
            return
        if not messagebox.askyesno('确认取消', '确定取消这条收藏记录吗？', parent=win):
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'DELETE FROM Favorite WHERE favorite_id = %s AND user_id = %s',
                    (int(values[0]), self.current_user['user_id']),
                )
            conn.commit()
        finally:
            conn.close()
        messagebox.showinfo('成功', '已取消收藏。', parent=win)
        win.destroy()

    def review_product(self):
        messagebox.showinfo(
            '提示',
            '当前系统按“订单 —— 评价 = 1:1”设计，请到“我的订单”中对选中的订单进行评价。',
        )

    def view_product_reviews(self):
        p = self.selected_product()
        if not p:
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        r.review_id AS 评价ID,
                        u.username AS 评价用户,
                        r.score AS 评分,
                        r.content AS 评价内容,
                        r.review_time AS 评价时间
                    FROM Review r
                    JOIN `User` u ON r.user_id = u.user_id
                    JOIN OrderItem oi ON r.order_id = oi.order_id
                    WHERE oi.product_id = %s
                    ORDER BY r.review_time DESC, r.review_id DESC
                    """,
                    (p['product_id'],),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        if not rows:
            messagebox.showinfo('提示', f"商品“{p['product_name']}”暂时还没有评价。")
            return

        GridWindow(
            self.root,
            f"{p['product_name']} - 商品评价",
            ('评价ID', '评价用户', '评分', '评价内容', '评价时间'),
            [tuple(r.values()) for r in rows],
            {'评价用户': 120, '评价内容': 320, '评价时间': 180},
        )

    def show_my_reviews(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有评价记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        r.review_id AS 评价ID,
                        p.product_name AS 商品名称,
                        r.score AS 评分,
                        r.content AS 评价内容,
                        r.review_time AS 评价时间
                    FROM Review r
                    JOIN OrderInfo o ON r.order_id = o.order_id
                    JOIN OrderItem oi ON oi.order_id = o.order_id
                    JOIN Product p ON oi.product_id = p.product_id
                    WHERE r.user_id = %s
                    ORDER BY r.review_id DESC
                    """,
                    (self.current_user['user_id'],),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        win = GridWindow(
            self.root,
            '我的评价',
            ('评价ID', '商品名称', '评分', '评价内容', '评价时间'),
            [tuple(r.values()) for r in rows],
            {'商品名称': 180, '评价内容': 280, '评价时间': 180},
            actions=[{'text': '删除选中评价', 'command': lambda: self.delete_review(win)}],
        )

    def delete_review(self, win):
        values = win.selected()
        if not values:
            return
        if not messagebox.askyesno('确认删除', '确定删除这条评价吗？', parent=win):
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    'DELETE FROM Review WHERE review_id = %s AND user_id = %s',
                    (int(values[0]), self.current_user['user_id']),
                )
            conn.commit()
        finally:
            conn.close()
        messagebox.showinfo('成功', '评价已删除。', parent=win)
        win.destroy()

    def show_my_orders(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有订单记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        o.order_id AS 订单ID,
                        COUNT(oi.order_item_id) AS 明细数,
                        SUM(oi.quantity) AS 商品总数,
                        GROUP_CONCAT(p.product_name ORDER BY oi.order_item_id SEPARATOR '、') AS 商品概览,
                        o.total_amount AS 总金额,
                        o.status AS 订单状态,
                        o.address AS 收货地址,
                        o.order_time AS 下单时间,
                        CASE WHEN r.review_id IS NULL THEN '未评价' ELSE '已评价' END AS 评价状态
                    FROM OrderInfo o
                    JOIN OrderItem oi ON o.order_id = oi.order_id
                    JOIN Product p ON oi.product_id = p.product_id
                    LEFT JOIN Review r ON r.order_id = o.order_id
                    WHERE o.buyer_id = %s
                    GROUP BY
                        o.order_id,
                        o.total_amount,
                        o.status,
                        o.address,
                        o.order_time,
                        r.review_id
                    ORDER BY o.order_id DESC
                    """,
                    (self.current_user['user_id'],),
                )
                rows = cur.fetchall()
        finally:
            conn.close()
        win = GridWindow(
            self.root,
            '我的订单',
            ('订单ID', '明细数', '商品总数', '商品概览', '总金额', '订单状态', '收货地址', '下单时间', '评价状态'),
            [tuple(r.values()) for r in rows],
            {'商品概览': 260, '收货地址': 160, '下单时间': 180},
            actions=[
                {'text': '评价选中订单', 'command': lambda: self.review_order_from_window(win)},
                {'text': '查看订单明细', 'command': lambda: self.view_order_items(win)},
            ],
        )

    def review_order_from_window(self, win):
        values = win.selected()
        if not values:
            return

        order_id = int(values[0])
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT order_id, status
                    FROM OrderInfo
                    WHERE order_id = %s AND buyer_id = %s
                    """,
                    (order_id, self.current_user['user_id']),
                )
                order_row = cur.fetchone()
                if not order_row:
                    messagebox.showerror('提示', '订单不存在。', parent=win)
                    return
                if order_row['status'] not in ('已支付', '已完成'):
                    messagebox.showinfo('提示', '只有已支付或已完成订单才可以评价。', parent=win)
                    return

                cur.execute('SELECT review_id FROM Review WHERE order_id = %s', (order_id,))
                if cur.fetchone():
                    messagebox.showinfo('提示', '该订单已经评价过了。', parent=win)
                    return

                cur.execute(
                    """
                    SELECT p.product_name
                    FROM OrderItem oi
                    JOIN Product p ON oi.product_id = p.product_id
                    WHERE oi.order_id = %s
                    ORDER BY oi.order_item_id
                    """,
                    (order_id,),
                )
                names = [row['product_name'] for row in cur.fetchall()]
        finally:
            conn.close()

        summary = f"订单#{order_id}"
        if names:
            summary += "：" + "、".join(names[:3])
            if len(names) > 3:
                summary += " 等"
        ReviewDialog(self.root, self.current_user, order_id, summary)

    def view_order_items(self, win):
        values = win.selected()
        if not values:
            return

        order_id = int(values[0])
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        oi.order_item_id AS 明细ID,
                        p.product_id AS 商品ID,
                        p.product_name AS 商品名称,
                        c.category_name AS 商品类别,
                        u.username AS 卖家,
                        oi.quantity AS 数量,
                        oi.deal_price AS 成交单价,
                        oi.quantity * oi.deal_price AS 明细小计,
                        p.description AS 商品描述,
                        o.total_amount AS 订单总金额,
                        o.status AS 订单状态,
                        o.address AS 收货地址,
                        o.order_time AS 下单时间
                    FROM OrderItem oi
                    JOIN OrderInfo o ON oi.order_id = o.order_id
                    JOIN Product p ON oi.product_id = p.product_id
                    LEFT JOIN Category c ON p.category_id = c.category_id
                    LEFT JOIN `User` u ON p.seller_id = u.user_id
                    WHERE oi.order_id = %s
                      AND o.buyer_id = %s
                    ORDER BY oi.order_item_id
                    """,
                    (order_id, self.current_user['user_id']),
                )
                rows = cur.fetchall()
        finally:
            conn.close()

        GridWindow(
            self.root,
            f'订单 {order_id} 的明细',
            (
                '明细ID', '商品ID', '商品名称', '商品类别', '卖家', '数量',
                '成交单价', '明细小计', '商品描述', '订单总金额', '订单状态',
                '收货地址', '下单时间',
            ),
            [tuple(r.values()) for r in rows],
            {
                '商品名称': 180,
                '商品类别': 110,
                '卖家': 100,
                '商品描述': 260,
                '收货地址': 180,
                '下单时间': 180,
            },
        )

    def delete_product(self):
        p = self.selected_product()
        if not p:
            return
        if not messagebox.askyesno('确认删除', f"确定删除商品“{p['product_name']}”吗？"):
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT 1 FROM OrderItem WHERE product_id = %s LIMIT 1', (p['product_id'],))
                if cur.fetchone():
                    raise ValueError('product_has_order_items')
                cur.execute('DELETE FROM Favorite WHERE product_id = %s', (p['product_id'],))
                cur.execute('DELETE FROM Product WHERE product_id = %s', (p['product_id'],))
            conn.commit()
        except ValueError as exc:
            conn.rollback()
            if str(exc) == 'product_has_order_items':
                messagebox.showerror('删除失败', '该商品已被订单明细引用，无法删除；事务已回滚。')
            else:
                messagebox.showerror('删除失败', f'删除商品时发生错误，事务已回滚。\n\n{exc}')
            return
        except pymysql.IntegrityError:
            conn.rollback()
            messagebox.showerror('删除失败', '删除商品时发生数据完整性错误，事务已回滚。')
            return
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('删除失败', f'删除商品时发生数据库错误，事务已回滚。\n\n{exc}')
            return
        finally:
            conn.close()
        self.refresh_products()
        messagebox.showinfo('成功', '商品及其收藏记录已删除。')


def main():
    try:
        init_database()
    except pymysql.MySQLError as exc:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            'MySQL 连接失败',
            f'无法连接 MySQL 或初始化数据库。\n\n{exc}\n\n'
            f'当前配置：{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}',
        )
        root.destroy()
        return
    root = tk.Tk()
    style = ttk.Style()
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    LoginWindow(root)
    root.mainloop()


if __name__ == '__main__':
    main()
