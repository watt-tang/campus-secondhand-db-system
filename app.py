# 本文件是“校园二手交易信息管理系统”的 Python 主程序，使用 Tkinter 做桌面界面，使用 pymysql 操作 MySQL。

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import pymysql
from pymysql.cursors import DictCursor
# 系统配置区，
# BASE_DIR 表示当前代码所在目录；SCHEMA_PATH 指向同目录下 schema.sql，用于初始化数据库结构。
# DB_HOST、DB_PORT、DB_USER、DB_PASSWORD、DB_NAME 分别是连接 MySQL 所需的主机、端口、用户名、密码和数据库名。

BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / 'schema.sql'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = '123456'
DB_NAME = 'campus_secondhand'


# 连接 MySQL 服务器，不指定具体 database，主要用于初始化阶段创建 campus_secondhand 数据库。
# charset=utf8mb4 支持中文；DictCursor 让结果按字段名读取；autocommit=False 用于手动控制事务。
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


# 连接具体业务数据库 campus_secondhand。
# 登录、商品、订单、收藏、评价等所有业务功能都通过该连接访问数据库。
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


# 执行 schema.sql 脚本中的 SQL 语句。
# 该脚本一般包含建表、建视图、建触发器、建存储过程等内容，是程序自动初始化数据库的核心。
def exec_script(conn, text: str):
    with conn.cursor() as cur:
        for stmt in [s.strip() for s in text.split(';') if s.strip()]:
            cur.execute(stmt)


# 初始化数据库：先建库，再建表/视图/触发器/存储过程，最后准备演示数据。
# 该函数保证运行程序时可以直接进入演示，不需要手工创建数据库对象。
def init_database():
    conn = server_conn()
    try:
        with conn.cursor() as cur:
            # 创建业务数据库，并统一使用 utf8mb4 字符集，避免中文乱码。
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
        # 执行 schema.sql，创建报告中涉及的 User、StudentUser、AdminUser、Category、Product、OrderInfo、OrderItem、Favorite、Review 等对象。
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total FROM `User`")
            # 检查 User 表是否为空；如果为空，说明是首次运行，需要插入演示账号和基础数据。
            if cur.fetchone()['total'] == 0:
                seed_demo_data(conn)
            ensure_demo_orders(conn)
        conn.commit()
    finally:
        conn.close()


# 插入演示数据。
# 这里构造学生用户 alice、bob 和管理员 admin，体现报告中的用户继承关系 User -> StudentUser / AdminUser。
# 同时插入商品类别和商品，为商品查询、购买、收藏、评价等功能提供测试数据。
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


# 补充演示订单和订单明细。
# 这些数据用于证明 Product 被 OrderItem 引用后不能直接删除，服务于第 4 部分“事务删除”的演示。
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


# 通用表格弹窗类。
# 系统中“我的收藏”“我的订单”“订单明细”“商品评价”等窗口都复用这个类显示数据。
class GridWindow(tk.Toplevel):
    # 构造一个带滚动条的 Treeview 表格，并可根据 actions 动态生成操作按钮。
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

    # 获取表格当前选中行；若未选中，则提示用户先选择记录。
    def selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请先选中一条记录。', parent=self)
            return None
        return self.tree.item(sel[0], 'values')

# 评价弹窗类，用于把订单评价写入 Review 表。
# 评价功能体现订单与评价的关联关系：本系统按“一个订单对应一条评价”的方式设计。
class ReviewDialog(tk.Toplevel):
    # 初始化评价窗口，显示订单/商品摘要，并提供评分和评价内容输入区域。
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

    # 保存评价：先校验评价内容，再检查该订单是否已经评价，最后插入 Review 表并提交事务。
    def save(self):
        text = self.content.get('1.0', 'end').strip()
        if not text:
            messagebox.showwarning('提示', '请填写评价内容。', parent=self)
            return
        conn = db_conn()
        try:
            # 检查当前订单是否已有评价，防止同一个订单重复评价。
            with conn.cursor() as cur:
                cur.execute('SELECT review_id FROM Review WHERE order_id = %s', (self.order_id,))
                if cur.fetchone():
                    messagebox.showinfo('提示', '该订单已经评价过了。', parent=self)
                    return
                # 插入评价记录，字段包括 order_id、user_id、score、content、review_time。
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


# 购买商品弹窗类。
# 单个商品购买成功后会生成 OrderInfo 和 OrderItem，并调用存储过程更新 Product 库存和状态。
# 该部分对应报告第 6 部分“存储过程控制下的更新操作”。
class BuyDialog(tk.Toplevel):
    # 初始化购买窗口，展示商品名称、单价、库存，并让用户填写购买数量和收货地址。
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

    # 根据购买数量实时计算预计金额。
    def refresh_total(self, *_args):
        try:
            qty = int(self.qty_var.get().strip() or '0')
        except ValueError:
            qty = 0
        self.total.config(text=f"预计金额：{qty * float(self.product['price']):.2f}")

    # 提交单个商品购买操作。
    # 核心流程：校验输入 -> 锁定商品 -> 写订单主表 -> 写订单明细 -> 调用存储过程 -> 提交事务。
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
        # 建立数据库连接；由于 db_conn 的 autocommit=False，后续 SQL 默认处于同一事务中。
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 使用 SELECT ... FOR UPDATE 锁定商品行，避免并发购买导致库存扣减错误。
                cur.execute(
                    'SELECT product_id, product_name, seller_id, price, stock, status '
                    'FROM Product WHERE product_id = %s FOR UPDATE',
                    (self.product['product_id'],),
                )
                p = cur.fetchone()
                # 如果商品不存在，直接终止购买。
                if not p:
                    messagebox.showerror('购买失败', '商品不存在。', parent=self)
                    return
                # 只有“在售”状态的商品允许购买。
                if p['status'] != '在售':
                    messagebox.showerror('购买失败', '该商品当前不是在售状态。', parent=self)
                    return
                # 购买数量不能超过当前库存。
                if qty > p['stock']:
                    messagebox.showerror('购买失败', '库存不足。', parent=self)
                    return
                # 生成订单时间并计算订单总金额。
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                total = qty * float(p['price'])
                # 插入 OrderInfo 订单主表，保存买家、下单时间、总金额、状态和收货地址。
                cur.execute(
                    'INSERT INTO OrderInfo '
                    '(buyer_id,order_time,total_amount,status,address) '
                    'VALUES (%s,%s,%s,%s,%s)',
                    (self.current_user['user_id'], now, total, '已完成', addr),
                )
                oid = cur.lastrowid
                # 插入 OrderItem 订单明细表，保存订单和商品之间的对应关系。
                cur.execute(
                    'INSERT INTO OrderItem '
                    '(order_id,product_id,quantity,deal_price) '
                    'VALUES (%s,%s,%s,%s)',
                    (oid, p['product_id'], qty, p['price']),
                )
                # 调用存储过程 update_product_after_order，由数据库根据订单明细扣减库存并更新商品/订单状态。
                cur.execute('CALL update_product_after_order(%s)', (oid,))
            # 全部 SQL 成功后提交事务。
            conn.commit()
        # 捕获 MySQL 异常并回滚事务，防止订单、明细、库存之间出现不一致。
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('购买失败', f'写入订单失败：{exc}', parent=self)
            return
        finally:
            conn.close()
        self.parent.refresh_products()
        messagebox.showinfo('成功', '订单已创建，购买完成。', parent=self)
        self.destroy()


# 登录窗口类。
# 用户通过 User 表中的 username 和 password 登录，登录后根据 user_type 区分学生和管理员。
class LoginWindow:
    # 初始化登录界面，默认填入演示账号 alice / 123456，便于现场演示。
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

    # 执行登录查询，验证用户名和密码是否匹配。
    def login(self):
        conn = db_conn()
        # 从 User 表读取当前登录用户的 user_id、username、user_type。
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
            # 登录成功后关闭登录窗口，并打开商品列表主界面。
            return
        self.root.destroy()
        nxt = tk.Tk()
        ProductWindow(nxt, row)
        nxt.mainloop()

# 添加商品弹窗类。
# 该功能对应报告第 5 部分“触发器控制下的添加操作”。
# 程序执行 INSERT INTO Product 时，数据库中的插入前触发器会自动检查商品名称、价格、库存、状态是否合法。
class AddProductDialog(tk.Toplevel):
    # 初始化添加商品窗口，只有学生用户可以发布商品。
    def __init__(self, owner, current_user):
        super().__init__(owner.root)
        self.owner = owner
        self.current_user = current_user
        self.title('添加商品')
        self.geometry('420x340')
        self.resizable(False, False)
        self.transient(owner.root)
        self.grab_set()
        # 权限限制：非学生用户不能发布商品。
        if current_user['user_type'] != 'student':
            messagebox.showinfo('提示', '只有学生用户可以发布商品。', parent=self)
            self.destroy()
            return
        # 从 Category 表读取类别，用于商品类别下拉框。
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

    # 保存新增商品。
    # 先做 Python 层输入格式检查，再插入 Product 表；如果违反触发器规则，MySQL 会抛出异常并阻止插入。
    def save(self):
        # 价格必须能转为数字，库存必须能转为整数。
        try:
            price = float(self.price_var.get().strip())
            stock = int(self.stock_var.get().strip())
        except ValueError:
            messagebox.showerror('输入错误', '价格必须是数字，库存必须是整数。', parent=self)
            return
        name = self.name_var.get().strip()
        cat = self.cat_var.get().strip()
        # 商品名称和类别不能为空。
        if not name or not cat:
            messagebox.showwarning('提示', '请填写商品名称并选择类别。', parent=self)
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 插入 Product 表。这里会触发数据库层 before_product_insert 触发器，实现报告中的触发器约束检查。
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
            # 商品插入成功后提交事务。
            conn.commit()
        # 如果触发器或数据库返回错误，则回滚事务并提示错误信息。
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('保存失败', f'写入 MySQL 失败：{exc}', parent=self)
            return
        finally:
            conn.close()
        self.owner.refresh_products()
        messagebox.showinfo('成功', '商品已添加到 MySQL。', parent=self)
        self.destroy()


# 商品列表主窗口类，是系统的核心界面。
# 集中实现商品查询、添加、购买、待下单列表、收藏、评价、订单记录、订单明细、事务删除等功能。
class ProductWindow:
    # 初始化主界面：上方显示当前用户，中间是查询条件和功能按钮，下方是商品表格。
    def __init__(self, root, current_user):
        self.root = root
        self.current_user = current_user
        # cart_items 是内存中的待下单列表，用于暂存准备一起结算的商品。
        self.cart_items = []
        root.title('校园二手交易系统 - 商品列表')
        root.geometry('1160x580')
        top = ttk.Frame(root, padding=16)
        top.pack(fill='x')
        ttk.Label(
            top,
            text=f"当前用户：{current_user['username']}  ({current_user['user_type']})",
            font=('Microsoft YaHei UI', 11, 'bold'),
        # 商品查询条件：支持按商品名称模糊查询，并按状态“全部/在售/已售”筛选。
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
        # 功能按钮区，覆盖报告中需要演示的添加、查询、删除、更新、收藏、评价、订单等操作。
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
            # 商品表格字段，和后续 SQL 查询结果字段一一对应。
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

    # 判断当前用户是否为学生用户；购买、收藏、评价、发布商品等操作需要学生身份。
    def is_student(self):
        return self.current_user['user_type'] == 'student'

    # 读取商品类别，返回“类别名称 -> 类别编号”的映射。
    def load_categories(self):
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute('SELECT category_id, category_name FROM Category ORDER BY category_id')
                return {r['category_name']: r['category_id'] for r in cur.fetchall()}
        finally:
            conn.close()

    # 重置商品查询条件，并重新刷新商品列表。
    def reset_filters(self):
        self.keyword_var.set('')
        self.status_var.set('全部')
        self.refresh_products()

    # 获取当前选中的商品，并回表查询 Product 的真实数据，防止界面缓存数据过期。
    def selected_product(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning('提示', '请先选中一条商品记录。')
            return None
        pid = int(self.tree.item(sel[0], 'values')[0])
        conn = db_conn()
        # 根据 product_id 查询 Product 表中的商品编号、名称、卖家和状态。
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

    # 刷新商品列表。
    # 当状态选择“在售”时查询视图 v_available_product；当查询“全部/已售”时使用 Product、Category、User 多表连接。
    # 该方法对应报告第 7 部分“含有视图的查询操作”。
    def refresh_products(self):
        # 刷新前清空旧的表格数据。
        for item in self.tree.get_children():
            self.tree.delete(item)
        params = []
        kw = self.keyword_var.get().strip()
        st = self.status_var.get().strip()

        # 查询在售商品时直接使用视图 v_available_product，视图已封装 Product、Category、User 的连接。
        if st == '在售':
            sql = (
                'SELECT product_id, product_name, category_name, seller_name, '
                'price, stock, status, publish_time, description '
                'FROM v_available_product WHERE 1=1'
            )
            # 如果输入商品名关键字，则在视图查询上追加 LIKE 模糊查询条件。
            if kw:
                sql += ' AND product_name LIKE %s'
                params.append(f'%{kw}%')
            sql += ' ORDER BY product_id DESC'
        # 查询“全部”或“已售”时直接写多表连接 SQL，以便包含已售商品。
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
            # 追加商品名称模糊查询条件。
            if kw:
                sql += ' AND p.product_name LIKE %s'
                params.append(f'%{kw}%')
            # 当筛选状态为“已售”时，追加 p.status 条件。
            if st == '已售':
                sql += ' AND p.status = %s'
                params.append(st)
            sql += ' ORDER BY p.product_id DESC'

        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 执行参数化 SQL，避免把用户输入直接拼接进 SQL。
                cur.execute(sql, params)
                rows = cur.fetchall()
        finally:
            conn.close()
        # 把数据库查询结果逐行插入 Treeview 表格。
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

    # 购买选中商品：进行权限、卖家、状态、库存检查后，打开 BuyDialog。
    def buy_product(self):
        # 只有学生用户可以购买商品。
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以购买商品。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            # 不能购买自己发布的商品。
            messagebox.showinfo('提示', '不能购买自己发布的商品。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    # 重新查询商品详情，确保商品状态和库存是最新的。
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
            # 商品必须在售且库存大于 0 才能进入购买流程。
            return
        BuyDialog(self.root, self.current_user, detail)

    # 加入待下单列表，用于一次性生成包含多个商品明细的订单。
    def add_to_cart(self):
        # 只有学生用户可以下单。
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以下单。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            # 不能把自己发布的商品加入待下单列表。
            messagebox.showinfo('提示', '不能购买自己发布的商品。')
            return

        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 重新查询商品详情，确保待下单商品仍然存在且状态有效。
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
            # 已售或库存不足的商品不能加入待下单列表。
            messagebox.showinfo('提示', '这个商品已经在待下单列表里了。')
            return

        # 避免同一商品重复加入待下单列表。
        self.cart_items.append(
            {
                'product_id': detail['product_id'],
                'product_name': detail['product_name'],
                # 把商品编号、名称、单价、数量暂存到 cart_items。
                'price': float(detail['price']),
                'quantity': 1,
            }
        )
        messagebox.showinfo('成功', f"已加入待下单列表：{detail['product_name']}")

    # 显示待下单列表窗口，并提供移除、结算、清空三个操作。
    def show_cart(self):
        if not self.cart_items:
            messagebox.showinfo('提示', '待下单列表为空。')
            return

        # 把 cart_items 转换成表格行，并计算每个商品的小计。
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

    # 移除待下单列表中的选中商品。
    def remove_cart_item(self, win):
        values = win.selected()
        if not values:
            return
        product_id = int(values[0])
        self.cart_items = [item for item in self.cart_items if item['product_id'] != product_id]
        messagebox.showinfo('成功', '已从待下单列表移除。', parent=win)
        win.destroy()

    # 清空待下单列表，清空前要求用户确认。
    def clear_cart(self, win):
        if not messagebox.askyesno('确认清空', '确定清空待下单列表吗？', parent=win):
            return
        self.cart_items = []
        messagebox.showinfo('成功', '待下单列表已清空。', parent=win)
        win.destroy()

    # 结算待下单列表。
    # 生成一个 OrderInfo 订单主表，并为每个商品生成一条 OrderItem 明细，最后调用存储过程扣减库存。
    def checkout_cart(self, win):
        if not self.cart_items:
            messagebox.showinfo('提示', '待下单列表为空。', parent=win)
            return

        # 结算时输入收货地址，地址为空则不允许提交订单。
        address = simpledialog.askstring('结算订单', '请输入收货地址：', parent=win)
        if address is None:
            return
        address = address.strip()
        if not address:
            messagebox.showwarning('提示', '收货地址不能为空。', parent=win)
            return

        conn = db_conn()
        try:
            # product_rows 保存锁定后查到的商品数据，total_amount 用于累计订单总金额。
            product_rows = []
            total_amount = 0.0
            with conn.cursor() as cur:
                for item in self.cart_items:
                    # 逐个使用 SELECT ... FOR UPDATE 锁定商品，保证结算过程中库存不会被并发修改。
                    cur.execute(
                        'SELECT product_id, product_name, price, stock, status '
                        'FROM Product WHERE product_id = %s FOR UPDATE',
                        (item['product_id'],),
                    )
                    row = cur.fetchone()
                    # 如果商品不存在，则终止结算。
                    if not row:
                        messagebox.showerror('结算失败', f"商品不存在：{item['product_name']}", parent=win)
                        return
                    # 如果商品不可购买，则终止结算。
                    if row['status'] != '在售' or row['stock'] <= 0:
                        messagebox.showerror('结算失败', f"商品不可购买：{row['product_name']}", parent=win)
                        return
                    product_rows.append(row)
                    total_amount += float(row['price'])

                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                # 写入订单主表 OrderInfo。
                cur.execute(
                    'INSERT INTO OrderInfo '
                    '(buyer_id,order_time,total_amount,status,address) '
                    'VALUES (%s,%s,%s,%s,%s)',
                    (self.current_user['user_id'], now, total_amount, '已完成', address),
                )
                order_id = cur.lastrowid

                # 循环写入订单明细 OrderItem，体现一个订单对应多条明细。
                for row in product_rows:
                    cur.execute(
                        'INSERT INTO OrderItem '
                        '(order_id,product_id,quantity,deal_price) '
                        'VALUES (%s,%s,%s,%s)',
                        (order_id, row['product_id'], 1, row['price']),
                    )

                # 调用存储过程 update_product_after_order，统一扣减商品库存并更新状态。
                cur.execute('CALL update_product_after_order(%s)', (order_id,))

            # 所有明细和库存更新都成功后提交事务。
            conn.commit()
        # 出现数据库错误时回滚，避免订单、明细和库存状态不一致。
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('结算失败', f'写入订单失败：{exc}', parent=win)
            return
        finally:
            conn.close()

        # 结算成功后清空待下单列表。
        self.cart_items = []
        self.refresh_products()
        messagebox.showinfo('成功', '已生成一个包含多个商品明细的订单。', parent=win)
        win.destroy()

    # 收藏选中商品。
    # Favorite 表连接学生用户和商品，体现多对多关系。
    def favorite_product(self):
        # 只有学生用户可以收藏商品。
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户可以收藏商品。')
            return
        p = self.selected_product()
        if not p:
            return
        if p['seller_id'] == self.current_user['user_id']:
            # 不能收藏自己发布的商品。
            messagebox.showinfo('提示', '不能收藏自己发布的商品。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    # 先检查当前用户是否已经收藏过该商品，防止重复收藏。
                    'SELECT favorite_id FROM Favorite '
                    'WHERE user_id = %s AND product_id = %s',
                    (self.current_user['user_id'], p['product_id']),
                )
                if cur.fetchone():
                    messagebox.showinfo('提示', '你已经收藏过这个商品了。')
                    return
                # 插入 Favorite 收藏记录。
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
        # 提交收藏事务。
        messagebox.showinfo('成功', '商品已收藏到 MySQL。')

    # 显示“我的收藏”。
    # 通过 Favorite、Product、Category、User 多表连接展示收藏商品信息。
    def show_my_favorites(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有收藏记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 查询当前用户收藏的商品列表。
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

    # 取消收藏：根据 favorite_id 和当前 user_id 删除 Favorite 记录。
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
                    # 执行删除收藏，附加 user_id 条件保证只能删除自己的收藏。
                    'DELETE FROM Favorite WHERE favorite_id = %s AND user_id = %s',
                    (int(values[0]), self.current_user['user_id']),
                )
            conn.commit()
        finally:
            conn.close()
        messagebox.showinfo('成功', '已取消收藏。', parent=win)
        win.destroy()

    # 提示评价入口在“我的订单”中，因为本系统按订单进行评价。
    def review_product(self):
        messagebox.showinfo(
            '提示',
            '当前系统按“订单 —— 评价 = 1:1”设计，请到“我的订单”中对选中的订单进行评价。',
        )

    # 查看选中商品的评价。
    # 通过 Review、User、OrderItem 连接，找出购买该商品的订单评价。
    def view_product_reviews(self):
        p = self.selected_product()
        if not p:
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 查询某个商品对应的所有评价记录。
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

    # 显示“我的评价”，查询当前用户已经提交过的评价。
    def show_my_reviews(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有评价记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 连接 Review、OrderInfo、OrderItem、Product，显示评价对应的商品名称。
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

    # 删除选中评价，根据 review_id 和 user_id 删除 Review 记录。
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
                    # 执行评价删除，附加当前 user_id 防止删除他人评价。
                    'DELETE FROM Review WHERE review_id = %s AND user_id = %s',
                    (int(values[0]), self.current_user['user_id']),
                )
            conn.commit()
        finally:
            conn.close()
        messagebox.showinfo('成功', '评价已删除。', parent=win)
        win.destroy()

    # 显示“我的订单”。
    # 通过 OrderInfo、OrderItem、Product、Review 统计订单明细数、商品总数、商品概览、评价状态等信息。
    def show_my_orders(self):
        if not self.is_student():
            messagebox.showinfo('提示', '只有学生用户有订单记录。')
            return
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 订单列表查询：GROUP_CONCAT 汇总商品名称，LEFT JOIN Review 判断是否已评价。
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

    # 从订单窗口发起评价。
    # 检查订单归属、订单状态和是否已评价，然后打开 ReviewDialog。
    def review_order_from_window(self, win):
        values = win.selected()
        if not values:
            return

        order_id = int(values[0])
        conn = db_conn()
        # 确认订单存在并且属于当前登录用户。
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
                    # 检查该订单是否已经存在评价记录。
                    return
                if order_row['status'] not in ('已支付', '已完成'):
                    messagebox.showinfo('提示', '只有已支付或已完成订单才可以评价。', parent=win)
                    return

                # 查询订单明细中的商品名称，用于生成评价窗口摘要。
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

    # 查看订单明细。
    # 连接 OrderItem、OrderInfo、Product、Category、User，显示订单中每个商品的详细信息。
    def view_order_items(self, win):
        values = win.selected()
        if not values:
            return

        order_id = int(values[0])
        conn = db_conn()
        try:
            # 订单明细多表连接查询，同时展示商品信息和订单信息。
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

    # 删除选中商品。
    # 该功能对应报告第 4 部分“含有事务应用的删除操作”。
    # 涉及 Product、Favorite、OrderItem 三张表：若商品被 OrderItem 引用则回滚；否则先删 Favorite 再删 Product。
    def delete_product(self):
        # 获取当前选中的商品。
        p = self.selected_product()
        if not p:
            return
        # 删除前二次确认，避免误删。
        if not messagebox.askyesno('确认删除', f"确定删除商品“{p['product_name']}”吗？"):
            return
        # 建立数据库连接；删除检查、删除收藏、删除商品会处于同一事务。
        conn = db_conn()
        try:
            with conn.cursor() as cur:
                # 先查 OrderItem：如果该商品已经出现在订单明细中，说明它是历史交易数据，不能删除。
                cur.execute('SELECT 1 FROM OrderItem WHERE product_id = %s LIMIT 1', (p['product_id'],))
                if cur.fetchone():
                    # 主动抛出业务异常，让程序进入 except 并 rollback，实现“检测到订单引用就回滚”。
                    raise ValueError('product_has_order_items')
                # 如果没有订单引用，先删除 Favorite 中该商品的收藏记录。
                cur.execute('DELETE FROM Favorite WHERE product_id = %s', (p['product_id'],))
                # 再删除 Product 商品主记录。
                cur.execute('DELETE FROM Product WHERE product_id = %s', (p['product_id'],))
            # 两步删除全部成功后提交事务。
            conn.commit()
        # 捕获业务异常并回滚事务。
        except ValueError as exc:
            conn.rollback()
            if str(exc) == 'product_has_order_items':
                messagebox.showerror('删除失败', '该商品已被订单明细引用，无法删除；事务已回滚。')
            else:
                messagebox.showerror('删除失败', f'删除商品时发生错误，事务已回滚。\n\n{exc}')
            return
        # 捕获数据完整性异常，例如外键约束导致的删除失败，并回滚事务。
        except pymysql.IntegrityError:
            conn.rollback()
            messagebox.showerror('删除失败', '删除商品时发生数据完整性错误，事务已回滚。')
            return
        # 捕获其他 MySQL 异常，并回滚事务。
        except pymysql.MySQLError as exc:
            conn.rollback()
            messagebox.showerror('删除失败', f'删除商品时发生数据库错误，事务已回滚。\n\n{exc}')
            return
        finally:
            conn.close()
        # 删除成功后刷新商品列表。
        self.refresh_products()
        # 提示用户商品及其收藏记录已经删除。
        messagebox.showinfo('成功', '商品及其收藏记录已删除。')


# 程序入口函数。
# 启动时先初始化数据库，再创建 Tkinter 登录窗口。
def main():
    try:
        # 自动初始化数据库结构和演示数据。
        init_database()
    # 如果 MySQL 连接或初始化失败，弹出错误框并显示当前配置，便于排查。
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
    # 创建 Tkinter 根窗口。
    root = tk.Tk()
    # 设置界面主题，Windows 环境下优先使用 vista 主题。
    style = ttk.Style()
    if 'vista' in style.theme_names():
        style.theme_use('vista')
    LoginWindow(root)
    root.mainloop()


# 只有直接运行该 Python 文件时才启动 main。
if __name__ == '__main__':
    main()
