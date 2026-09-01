import flet as ft
import sqlite3
import datetime
import random

# ==========================================
# DATABASE INITIALIZATION & QUERIES
# ==========================================
DB_NAME = "ayu_mobile_center.db"

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 1. Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE,
            category TEXT,
            wholesale_price REAL,
            retail_price REAL,
            quantity INTEGER,
            low_stock_limit INTEGER DEFAULT 3
        )
    ''')
    
    # 2. Repair Job Cards Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_no TEXT UNIQUE,
            customer_name TEXT,
            customer_phone TEXT,
            device_model TEXT,
            imei TEXT,
            lock_info TEXT,
            fault_desc TEXT,
            status TEXT,
            spare_cost REAL,
            labor_fee REAL,
            total_cost REAL,
            created_at TEXT
        )
    ''')
    
    # 3. Expenses Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            category TEXT,
            amount REAL,
            date TEXT
        )
    ''')
    
    # 4. Sales Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_details TEXT,
            total_amount REAL,
            payment_method TEXT,
            ref_code TEXT,
            date TEXT
        )
    ''')
    
    # 5. Customer Debts Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS debts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT,
            customer_phone TEXT,
            amount REAL,
            paid_amount REAL,
            due_date TEXT,
            status TEXT,
            created_at TEXT
        )
    ''')
    
    # Insert Initial Demo Data if empty
    cursor.execute("SELECT COUNT(*) as count FROM inventory")
    if cursor.fetchone()['count'] == 0:
        cursor.executemany('''
            INSERT INTO inventory (name, sku, category, wholesale_price, retail_price, quantity, low_stock_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', [
            ("Samsung A12 LCD Screen", "SCR-A12", "የስክሪን ቅያሬ", 1200, 1800, 5, 2),
            ("Type-C Fast Charging Cable", "CBL-TC01", "ቻርጀርና ኬብል", 150, 300, 15, 5),
            ("Original Earphone 3.5mm", "ACC-EP01", "አክሰሰሪ", 100, 250, 2, 3),
            ("18W Fast Adapter", "CHG-18W", "ቻርጀርና ኬብል", 300, 500, 8, 4)
        ])
        
    cursor.execute("SELECT COUNT(*) as count FROM repairs")
    if cursor.fetchone()['count'] == 0:
        today = datetime.date.today().strftime("%Y-%m-%d")
        cursor.execute('''
            INSERT INTO repairs (ticket_no, customer_name, customer_phone, device_model, imei, lock_info, fault_desc, status, spare_cost, labor_fee, total_cost, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ("AYU-1001", "ካሳሁን አለሙ", "0911223344", "Tecno Spark 8", "358912345678901", "1254", "የስክሪን ስብራት እና የቻርጅ ፖርት ቅያሬ", "በጥገና ላይ", 800, 500, 1300, today))
        
    conn.commit()
    conn.close()

# ==========================================
# MAIN APPLICATION SETUP
# ==========================================
def main(page: ft.Page):
    init_db()
    
    page.title = "አዩ ሞባይል ሴንተር Pro (Ayu Mobile & Electronics Center)"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 10
    page.window_width = 1100
    page.window_height = 800
    
    # ------------------------------------------
    # ABOUT DEVELOPER MODAL
    # ------------------------------------------
    def open_about_dialog(e):
        about_dialog = ft.AlertDialog(
            title=ft.Text("ስለ ሶፍትዌሩ አዘጋጅ", weight=ft.FontWeight.BOLD, color="teal"),
            content=ft.Column(
                controls=[
                    ft.Divider(),
                    ft.Text("ድርጅት: አዩ ሞባይል ሴንተር", weight=ft.FontWeight.BOLD, size=16),
                    ft.Text("አዘጋጅ: አየነው ታደሰ (Ayenew Taddese)", size=15),
                    ft.Text("ስልክ ቁጥር: 0914711350 / 0944438488", color="blue_800", size=14),
                    ft.Text("አድራሻ: ሰቆጣ፣ ዋግ ኀምራ፣ ኢትዮጵያ", size=14),
                    ft.Divider(),
                    ft.Text("ለሞባይልና ኤሌክትሮኒክስ ቤቶች የተዘጋጀ የላቀ የሂሳብ፣ የጥገናና የዕቃ ክምችት ማስተዳደሪያ ሲስተም።", italic=True, size=12)
                ],
                tight=True,
                spacing=8
            ),
            actions=[
                ft.TextButton("ዝጋ", on_click=lambda e: page.close(about_dialog))
            ]
        )
        page.open(about_dialog)

    # ------------------------------------------
    # NOTIFICATION HELPERS
    # ------------------------------------------
    def show_snackbar(msg, color="green"):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(msg, color="white"),
            bgcolor=color,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    # ------------------------------------------
    # TAB 1: DASHBOARD (የቀን ገቢ፣ ወጪና አጠቃላይ ትርፍ)
    # ------------------------------------------
    sales_stat_text = ft.Text("0.00 ብር", size=20, weight=ft.FontWeight.BOLD, color="green_800")
    repair_stat_text = ft.Text("0.00 ብር", size=20, weight=ft.FontWeight.BOLD, color="blue_800")
    expense_stat_text = ft.Text("0.00 ብር", size=20, weight=ft.FontWeight.BOLD, color="red_800")
    net_profit_text = ft.Text("0.00 ብር", size=22, weight=ft.FontWeight.BOLD, color="teal_900")
    
    low_stock_listview = ft.ListView(expand=True, spacing=5)

    def load_dashboard_data():
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = get_db()
        cursor = conn.cursor()
        
        # Sales today
        cursor.execute("SELECT SUM(total_amount) as total FROM sales WHERE date = ?", (today,))
        sales_today = cursor.fetchone()['total'] or 0.0
        
        # Repair revenue today
        cursor.execute("SELECT SUM(total_cost) as total, SUM(labor_fee) as labor FROM repairs WHERE created_at = ?", (today,))
        repair_row = cursor.fetchone()
        repair_today = repair_row['total'] or 0.0
        repair_labor = repair_row['labor'] or 0.0
        
        # Expenses today
        cursor.execute("SELECT SUM(amount) as total FROM expenses WHERE date = ?", (today,))
        expense_today = cursor.fetchone()['total'] or 0.0
        
        # Net Profit (Sales + Repair Labor Fee - Expenses)
        net_profit = (sales_today + repair_labor) - expense_today
        
        sales_stat_text.value = f"{sales_today:,.2f} ብር"
        repair_stat_text.value = f"{repair_today:,.2f} ብር"
        expense_stat_text.value = f"{expense_today:,.2f} ብር"
        net_profit_text.value = f"{net_profit:,.2f} ብር"
        
        # Low Stock Alert list
        cursor.execute("SELECT * FROM inventory WHERE quantity <= low_stock_limit")
        low_stock_items = cursor.fetchall()
        
        low_stock_listview.controls.clear()
        if not low_stock_items:
            low_stock_listview.controls.append(ft.Text("ሁሉም እቃዎች በበቂ ሁኔታ በክምችት ላይ ይገኛሉ።", color="green"))
        else:
            for item in low_stock_items:
                low_stock_listview.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color="red"),
                            ft.Text(f"{item['name']} - ቀሪ ብዛት: ", weight=ft.FontWeight.BOLD),
                            ft.Text(f"{item['quantity']} ብቻ", color="red", weight=ft.FontWeight.BOLD),
                        ]),
                        padding=8,
                        bgcolor="red_50",
                        border_radius=5
                    )
                )
        conn.close()
        page.update()

    dashboard_tab = ft.Container(
        padding=15,
        content=ft.Column([
            ft.Text("የቀን ገቢ፣ ወጪና አጠቃላይ የትርፍ ዳሽቦርድ", size=18, weight=ft.FontWeight.BOLD, color="teal_800"),
            ft.Divider(),
            ft.Row([
                ft.Card(
                    content=ft.Container(
                        padding=15, width=230,
                        content=ft.Column([
                            ft.Text("አጠቃላይ የዕቃ ሽያጭ", color="grey_700"),
                            sales_stat_text,
                            ft.Icon(ft.Icons.SHOPPING_BAG, color="green", size=30)
                        ])
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        padding=15, width=230,
                        content=ft.Column([
                            ft.Text("የጥገና ገቢ (አጠቃላይ)", color="grey_700"),
                            repair_stat_text,
                            ft.Icon(ft.Icons.BUILD, color="blue", size=30)
                        ])
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        padding=15, width=230,
                        content=ft.Column([
                            ft.Text("የሱቅ ወጪዎች", color="grey_700"),
                            expense_stat_text,
                            ft.Icon(ft.Icons.MONEY_OFF, color="red", size=30)
                        ])
                    )
                ),
                ft.Card(
                    content=ft.Container(
                        padding=15, width=240,
                        bgcolor="teal_50",
                        border_radius=8,
                        content=ft.Column([
                            ft.Text("የቀን ንጹህ ትርፍ", color="teal_900", weight=ft.FontWeight.BOLD),
                            net_profit_text,
                            ft.Icon(ft.Icons.ACCOUNT_BALANCE_WALLET, color="teal", size=30)
                        ])
                    )
                ),
            ], wrap=True, spacing=15),
            ft.Container(height=20),
            ft.Text("አነስተኛ ክምችት ያላቸው እቃዎች (Low Stock Alerts)", size=16, weight=ft.FontWeight.BOLD, color="orange_900"),
            ft.Container(
                content=low_stock_listview,
                height=220,
                border=ft.border.all(1, "orange_200"),
                border_radius=8,
                padding=10
            )
        ])
    )

    # ------------------------------------------
    # TAB 2: REPAIR MANAGEMENT (የጥገና መዝገብ)
    # ------------------------------------------
    repairs_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ቲኬት ቁጥር")),
            ft.DataColumn(ft.Text("ደንበኛ")),
            ft.DataColumn(ft.Text("ስልክ")),
            ft.DataColumn(ft.Text("የስልክ ሞዴል")),
            ft.DataColumn(ft.Text("የብልሽት አይነት")),
            ft.DataColumn(ft.Text("ሁኔታ")),
            ft.DataColumn(ft.Text("አጠቃላይ ሂሳብ")),
            ft.DataColumn(ft.Text("ተግባራት")),
        ],
        rows=[]
    )

    def print_thermal_receipt(repair):
        receipt_text = f"""
================================
     አዩ ሞባይል ሴንተር (AYU MOBILE)
      ስልክ: 0914711350 / 0944438488
      አድራሻ: ሰቆጣ፣ ዋግ ኀምራ
================================
የጥገና ደረሰኝ ቲኬት: {repair['ticket_no']}
ቀን: {repair['created_at']}
የደንበኛ ስም: {repair['customer_name']}
ስልክ: {repair['customer_phone']}
--------------------------------
የስልክ ሞዴል: {repair['device_model']}
IMEI: {repair['imei']}
የቁልፍ ኮድ: {repair['lock_info']}
የብልሽት አይነት: {repair['fault_desc']}
--------------------------------
የዕቃ ዋጋ: {repair['spare_cost']:,.2f} ብር
የእጅ ዋጋ: {repair['labor_fee']:,.2f} ብር
አጠቃላይ ክፍያ: {repair['total_cost']:,.2f} ብር
--------------------------------
ሁኔታ: {repair['status']}
================================
   ስለጎበኙን እናመሰግናለን!
================================
        """
        dlg = ft.AlertDialog(
            title=ft.Text("የ58mm ደረሰኝ ማተሚያ ማሳያ (Thermal Print)", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Text(receipt_text, font_family="Courier", size=12),
                padding=10,
                bgcolor="grey_100",
                border_radius=5
            ),
            actions=[
                ft.ElevatedButton("አትም (Print)", icon=ft.Icons.PRINT, on_click=lambda e: (show_snackbar("ደረሰኙ ወደ ብሉቱዝ ፕሪንተር ተልኳል!"), page.close(dlg))),
                ft.TextButton("ዝጋ", on_click=lambda e: page.close(dlg))
            ]
        )
        page.open(dlg)

    def send_sms_notification(repair):
        sms_body = f"ውድ ደንበኛችን {repair['customer_name']}፡ የሞባይል ({repair['device_model']}) ጥገናዎ ስለተጠናቀቀ አዩ ሞባይል ሴንተር መጥተው መረከብ ይችላሉ። አጠቃላይ ሂሳብ: {repair['total_cost']} ብር።"
        dlg = ft.AlertDialog(
            title=ft.Text("የSMS መልእክት መላኪያ", weight=ft.FontWeight.BOLD, color="blue"),
            content=ft.Column([
                ft.Text(f"ለ: {repair['customer_phone']}", weight=ft.FontWeight.BOLD),
                ft.TextField(value=sms_body, multiline=True, rows=4, label="የጽሁፍ መልእክት")
            ], tight=True),
            actions=[
                ft.ElevatedButton("SMS ላክ (Send)", icon=ft.Icons.SEND, on_click=lambda e: (show_snackbar(f"SMS ወደ {repair['customer_phone']} በስኬት ተልኳል!"), page.close(dlg))),
                ft.TextButton("ሰርዝ", on_click=lambda e: page.close(dlg))
            ]
        )
        page.open(dlg)

    def update_repair_status(ticket_no, new_status):
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE repairs SET status = ? WHERE ticket_no = ?", (new_status, ticket_no))
        conn.commit()
        conn.close()
        show_snackbar(f"የቲኬት {ticket_no} ሁኔታ ወደ '{new_status}' ተቀይሯል!")
        load_repairs_data()

    def load_repairs_data(search_query=""):
        conn = get_db()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM repairs WHERE customer_name LIKE ? OR ticket_no LIKE ? OR customer_phone LIKE ? ORDER BY id DESC", 
                           (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT * FROM repairs ORDER BY id DESC")
        
        rows = cursor.fetchall()
        repairs_table.rows.clear()
        
        for r in rows:
            repairs_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(r['ticket_no'], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(r['customer_name'])),
                    ft.DataCell(ft.Text(r['customer_phone'])),
                    ft.DataCell(ft.Text(r['device_model'])),
                    ft.DataCell(ft.Text(r['fault_desc'])),
                    ft.DataCell(
                        ft.Dropdown(
                            value=r['status'],
                            options=[
                                ft.dropdown.Option("ተረክቧል"),
                                ft.dropdown.Option("በጥገና ላይ"),
                                ft.dropdown.Option("ፍላሽ/ሶፍትዌር ላይ"),
                                ft.dropdown.Option("ተጠናቋል/ለደንበኛ ዝግጁ"),
                                ft.dropdown.Option("ተሰጥቷል")
                            ],
                            width=160,
                            dense=True,
                            on_change=lambda e, t=r['ticket_no']: update_repair_status(t, e.control.value)
                        )
                    ),
                    ft.DataCell(ft.Text(f"{r['total_cost']:,.2f} ብር", color="green_900", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(ft.Icons.RECEIPT, tooltip="ደረሰኝ አትም", icon_color="teal", on_click=lambda e, rep=r: print_thermal_receipt(rep)),
                            ft.IconButton(ft.Icons.SMS, tooltip="SMS ላክ", icon_color="blue", on_click=lambda e, rep=r: send_sms_notification(rep)),
                        ])
                    )
                ])
            )
        conn.close()
        page.update()

    # New Job Card Modal Dialog
    name_field = ft.TextField(label="የደንበኛ ስም", dense=True)
    phone_field = ft.TextField(label="ስልክ ቁጥር", dense=True)
    device_field = ft.TextField(label="የስልክ ሞዴል (ምሳሌ: Samsung A12)", dense=True)
    imei_field = ft.TextField(label="IMEI / Serial", dense=True)
    lock_field = ft.TextField(label="የፓስወርድ / ፓተርን ኮድ", dense=True)
    fault_field = ft.TextField(label="የብልሽት ዝርዝር", multiline=True, rows=2, dense=True)
    spare_cost_field = ft.TextField(label="የመለዋወጫ እቃ ዋጋ (ብር)", value="0", dense=True)
    labor_fee_field = ft.TextField(label="የእጅ ዋጋ (ብር)", value="0", dense=True)

    def save_new_job_card(e):
        if not name_field.value or not device_field.value:
            show_snackbar("እባክዎን የደንበኛ ስም እና የስልክ ሞዴል ያስገቡ!", "red")
            return
            
        ticket_no = f"AYU-{random.randint(1000, 9999)}"
        spare = float(spare_cost_field.value or 0)
        labor = float(labor_fee_field.value or 0)
        total = spare + labor
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO repairs (ticket_no, customer_name, customer_phone, device_model, imei, lock_info, fault_desc, status, spare_cost, labor_fee, total_cost, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ticket_no, name_field.value, phone_field.value, device_field.value, imei_field.value, lock_field.value, fault_field.value, "ተረክቧል", spare, labor, total, today))
        conn.commit()
        conn.close()
        
        # Clear fields
        name_field.value = ""
        phone_field.value = ""
        device_field.value = ""
        imei_field.value = ""
        lock_field.value = ""
        fault_field.value = ""
        spare_cost_field.value = "0"
        labor_fee_field.value = "0"
        
        page.close(add_job_dialog)
        show_snackbar(f"የጥገና መዝገብ {ticket_no} በስኬት ተመዝግቧል!")
        load_repairs_data()
        load_dashboard_data()

    add_job_dialog = ft.AlertDialog(
        title=ft.Text("አዲስ የጥገና መዝገብ (Job Card Entry)", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=500,
            content=ft.Column([
                ft.Row([name_field, phone_field]),
                ft.Row([device_field, imei_field]),
                lock_field,
                fault_field,
                ft.Row([spare_cost_field, labor_fee_field]),
            ], tight=True, spacing=10)
        ),
        actions=[
            ft.ElevatedButton("መዝግብ (Save Ticket)", icon=ft.Icons.SAVE, on_click=save_new_job_card, bgcolor="teal", color="white"),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(add_job_dialog))
        ]
    )

    search_repair_input = ft.TextField(hint_text="በስም፣ ቲኬት ወይም ስልክ ፈልግ...", width=300, dense=True, on_change=lambda e: load_repairs_data(e.control.value))

    repairs_tab = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([
                ft.Text("የጥገናና ዲያግኖስቲክስ መዝገብ", size=18, weight=ft.FontWeight.BOLD, color="teal_800"),
                ft.Spacer(),
                search_repair_input,
                ft.ElevatedButton("+ አዲስ የጥገና ቲኬት", icon=ft.Icons.ADD, bgcolor="teal", color="white", on_click=lambda e: page.open(add_job_dialog))
            ]),
            ft.Divider(),
            ft.ListView(
                controls=[repairs_table],
                expand=True
            )
        ])
    )

    # ------------------------------------------
    # TAB 3: ACCESSORIES & POS INVENTORY VAULT
    # ------------------------------------------
    pos_items_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("SKU")),
            ft.DataColumn(ft.Text("የእቃ ስም")),
            ft.DataColumn(ft.Text("ምድብ")),
            ft.DataColumn(ft.Text("የጅምላ ዋጋ")),
            ft.DataColumn(ft.Text("የችርቻሮ ዋጋ")),
            ft.DataColumn(ft.Text("ክምችት")),
            ft.DataColumn(ft.Text("ተግባር")),
        ],
        rows=[]
    )

    # Add Product Dialog
    prod_name_input = ft.TextField(label="የእቃ ስም", dense=True)
    prod_sku_input = ft.TextField(label="SKU / ባርኮድ", dense=True)
    prod_cat_input = ft.Dropdown(
        label="ምድብ",
        options=[
            ft.dropdown.Option("ቻርጀርና ኬብል"),
            ft.dropdown.Option("የስክሪን ቅያሬ"),
            ft.dropdown.Option("አክሰሰሪ"),
            ft.dropdown.Option("ባትሪ"),
            ft.dropdown.Option("ብሉቱዝ ስፒከር"),
        ],
        dense=True
    )
    prod_wholesale_input = ft.TextField(label="የጅምላ ዋጋ (ብር)", dense=True)
    prod_retail_input = ft.TextField(label="የችርቻሮ ዋጋ (ብር)", dense=True)
    prod_qty_input = ft.TextField(label="ብዛት (Quantity)", dense=True)

    def save_new_product(e):
        if not prod_name_input.value or not prod_retail_input.value:
            show_snackbar("እባክዎን የእቃ ስም እና የችርቻሮ ዋጋ ያስገቡ!", "red")
            return
        
        conn = get_db()
        cursor = conn.cursor()
        sku = prod_sku_input.value or f"SKU-{random.randint(100,999)}"
        cursor.execute('''
            INSERT INTO inventory (name, sku, category, wholesale_price, retail_price, quantity, low_stock_limit)
            VALUES (?, ?, ?, ?, ?, ?, 3)
        ''', (prod_name_input.value, sku, prod_cat_input.value or "አክሰሰሪ", float(prod_wholesale_input.value or 0), float(prod_retail_input.value or 0), int(prod_qty_input.value or 1)))
        conn.commit()
        conn.close()
        
        page.close(add_prod_dialog)
        show_snackbar("አዲስ እቃ በስኬት ተመዝግቧል!")
        load_inventory_data()
        load_dashboard_data()

    add_prod_dialog = ft.AlertDialog(
        title=ft.Text("አዲስ እቃ መዝግብ", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=450,
            content=ft.Column([
                prod_name_input,
                ft.Row([prod_sku_input, prod_cat_input]),
                ft.Row([prod_wholesale_input, prod_retail_input]),
                prod_qty_input
            ], tight=True, spacing=10)
        ),
        actions=[
            ft.ElevatedButton("መዝግብ (Save)", icon=ft.Icons.SAVE, bgcolor="teal", color="white", on_click=save_new_product),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(add_prod_dialog))
        ]
    )

    # POS Sale Dialog
    sale_item_text = ft.Text("", weight=ft.FontWeight.BOLD, size=16)
    sale_qty_input = ft.TextField(label="የሽያጭ ብዛት", value="1", dense=True, width=100)
    sale_pay_method = ft.Dropdown(
        label="የክፍያ መንገድ",
        options=[
            ft.dropdown.Option("በካሽ (Cash)"),
            ft.dropdown.Option("ቴሌብር (Telebirr)"),
            ft.dropdown.Option("ሲቢኢ ብር (CBE Birr)"),
            ft.dropdown.Option("ባንክ ሂሳብ (Bank)"),
            ft.dropdown.Option("በብድር (Credit)"),
        ],
        value="በካሽ (Cash)",
        dense=True
    )
    sale_ref_input = ft.TextField(label="የዲጂታል ክፍያ ማጣቀሻ ኮድ (Ref Code)", dense=True)
    selected_prod_data = {}

    def open_checkout_dialog(item):
        nonlocal selected_prod_data
        selected_prod_data = item
        sale_item_text.value = f"እቃ: {item['name']} (ዋጋ: {item['retail_price']} ብር)"
        page.open(checkout_dialog)

    def process_pos_checkout(e):
        qty_to_sell = int(sale_qty_input.value or 1)
        if qty_to_sell > selected_prod_data['quantity']:
            show_snackbar("በቂ እቃ በክምችት ውስጥ የለም!", "red")
            return
            
        total_amount = selected_prod_data['retail_price'] * qty_to_sell
        today = datetime.date.today().strftime("%Y-%m-%d")
        
        conn = get_db()
        cursor = conn.cursor()
        
        # Deduct Stock
        cursor.execute("UPDATE inventory SET quantity = quantity - ? WHERE id = ?", (qty_to_sell, selected_prod_data['id']))
        
        # Record Sale
        cursor.execute('''
            INSERT INTO sales (item_details, total_amount, payment_method, ref_code, date)
            VALUES (?, ?, ?, ?, ?)
        ''', (f"{selected_prod_data['name']} (x{qty_to_sell})", total_amount, sale_pay_method.value, sale_ref_input.value or "N/A", today))
        
        # If Credit, Record in Debt Vault
        if "በብድር" in sale_pay_method.value:
            cursor.execute('''
                INSERT INTO debts (customer_name, customer_phone, amount, paid_amount, due_date, status, created_at)
                VALUES (?, ?, ?, 0, ?, 'Pending', ?)
            ''', (f"ከPOS ሽያጭ - {selected_prod_data['name']}", "N/A", total_amount, "ያልተወሰነ", today))
        
        conn.commit()
        conn.close()
        
        page.close(checkout_dialog)
        show_snackbar(f"ሽያጭ ተጠናቋል! አጠቃላይ: {total_amount:,.2f} ብር")
        load_inventory_data()
        load_dashboard_data()
        load_debts_data()

    checkout_dialog = ft.AlertDialog(
        title=ft.Text("POS ክፍያ ማጠናቀቂያ", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=400,
            content=ft.Column([
                sale_item_text,
                sale_qty_input,
                sale_pay_method,
                sale_ref_input
            ], tight=True, spacing=10)
        ),
        actions=[
            ft.ElevatedButton("ክፍያ ጨርስ (Checkout)", icon=ft.Icons.CHECK, bgcolor="green", color="white", on_click=process_pos_checkout),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(checkout_dialog))
        ]
    )

    def load_inventory_data(search_query=""):
        conn = get_db()
        cursor = conn.cursor()
        if search_query:
            cursor.execute("SELECT * FROM inventory WHERE name LIKE ? OR sku LIKE ? OR category LIKE ?", 
                           (f"%{search_query}%", f"%{search_query}%", f"%{search_query}%"))
        else:
            cursor.execute("SELECT * FROM inventory ORDER BY id DESC")
            
        items = cursor.fetchall()
        pos_items_table.rows.clear()
        
        for item in items:
            is_low = item['quantity'] <= item['low_stock_limit']
            pos_items_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item['sku'])),
                    ft.DataCell(ft.Text(item['name'], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(item['category'])),
                    ft.DataCell(ft.Text(f"{item['wholesale_price']:,.2f} ብር")),
                    ft.DataCell(ft.Text(f"{item['retail_price']:,.2f} ብር", color="blue_900", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(
                        ft.Container(
                            content=ft.Text(f"{item['quantity']}", color="white" if is_low else "black", weight=ft.FontWeight.BOLD),
                            bgcolor="red" if is_low else "green_100",
                            padding=5,
                            border_radius=5
                        )
                    ),
                    ft.DataCell(
                        ft.ElevatedButton("ሽጥ (Sell)", icon=ft.Icons.SHOPPING_CART, bgcolor="teal", color="white", on_click=lambda e, i=item: open_checkout_dialog(i))
                    )
                ])
            )
        conn.close()
        page.update()

    search_inv_input = ft.TextField(hint_text="እቃ በስም ወይም በSKU ፈልግ...", width=300, dense=True, on_change=lambda e: load_inventory_data(e.control.value))

    inventory_tab = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([
                ft.Text("የአክሰሰሪና ኤሌክትሮኒክስ POS Vault", size=18, weight=ft.FontWeight.BOLD, color="teal_800"),
                ft.Spacer(),
                search_inv_input,
                ft.ElevatedButton("+ አዲስ እቃ ጨምር", icon=ft.Icons.ADD, bgcolor="teal", color="white", on_click=lambda e: page.open(add_prod_dialog))
            ]),
            ft.Divider(),
            ft.ListView(
                controls=[pos_items_table],
                expand=True
            )
        ])
    )

    # ------------------------------------------
    # TAB 4: CUSTOMER CREDIT & DEBT LEDGER (የብድር ደብተር)
    # ------------------------------------------
    debts_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("የደንበኛ ስም")),
            ft.DataColumn(ft.Text("ስልክ")),
            ft.DataColumn(ft.Text("የብድር መጠን")),
            ft.DataColumn(ft.Text("የተከፈለ")),
            ft.DataColumn(ft.Text("ቀሪ ዕዳ")),
            ft.DataColumn(ft.Text("ቀን")),
            ft.DataColumn(ft.Text("ተግባር")),
        ],
        rows=[]
    )

    # Pay Debt Dialog
    debt_pay_input = ft.TextField(label="የክፍያ መጠን (ብር)", dense=True)
    selected_debt_data = {}

    def open_pay_debt_dialog(d):
        nonlocal selected_debt_data
        selected_debt_data = d
        page.open(pay_debt_dialog)

    def process_debt_payment(e):
        pay_amt = float(debt_pay_input.value or 0)
        remaining = selected_debt_data['amount'] - selected_debt_data['paid_amount']
        
        if pay_amt <= 0 or pay_amt > remaining:
            show_snackbar("ትክክለኛ ያልሆነ የክፍያ መጠን!", "red")
            return
            
        new_paid = selected_debt_data['paid_amount'] + pay_amt
        new_status = "Paid" if new_paid >= selected_debt_data['amount'] else "Pending"
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE debts SET paid_amount = ?, status = ? WHERE id = ?", (new_paid, new_status, selected_debt_data['id']))
        conn.commit()
        conn.close()
        
        debt_pay_input.value = ""
        page.close(pay_debt_dialog)
        show_snackbar("የብድር ክፍያው በስኬት ተመዝግቧል!")
        load_debts_data()

    pay_debt_dialog = ft.AlertDialog(
        title=ft.Text("የብድር ክፍያ መመዝገቢያ", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=350,
            content=ft.Column([
                debt_pay_input
            ], tight=True)
        ),
        actions=[
            ft.ElevatedButton("ክፍያ መዝግብ", icon=ft.Icons.CHECK, bgcolor="teal", color="white", on_click=process_debt_payment),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(pay_debt_dialog))
        ]
    )

    # Add Debt Dialog
    debt_cust_name = ft.TextField(label="የደንበኛ ስም", dense=True)
    debt_cust_phone = ft.TextField(label="ስልክ ቁጥር", dense=True)
    debt_amount_input = ft.TextField(label="የብድር መጠን (ብር)", dense=True)
    debt_date_input = ft.TextField(label="የመክፈያ ቀን (Due Date)", value="15 ቀናት", dense=True)

    def save_new_debt(e):
        if not debt_cust_name.value or not debt_amount_input.value:
            show_snackbar("እባክዎን የደንበኛ ስም እና የብድር መጠን ያስገቡ!", "red")
            return
            
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO debts (customer_name, customer_phone, amount, paid_amount, due_date, status, created_at)
            VALUES (?, ?, ?, 0, ?, 'Pending', ?)
        ''', (debt_cust_name.value, debt_cust_phone.value, float(debt_amount_input.value), debt_date_input.value, today))
        conn.commit()
        conn.close()
        
        page.close(add_debt_dialog)
        show_snackbar("አዲስ የብድር መዝገብ ተፈጥሯል!")
        load_debts_data()

    add_debt_dialog = ft.AlertDialog(
        title=ft.Text("አዲስ የብድር መዝገብ", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=400,
            content=ft.Column([
                debt_cust_name,
                debt_cust_phone,
                debt_amount_input,
                debt_date_input
            ], tight=True, spacing=10)
        ),
        actions=[
            ft.ElevatedButton("መዝግብ", icon=ft.Icons.SAVE, bgcolor="teal", color="white", on_click=save_new_debt),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(add_debt_dialog))
        ]
    )

    def load_debts_data():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM debts ORDER BY id DESC")
        debts = cursor.fetchall()
        debts_table.rows.clear()
        
        for d in debts:
            rem = d['amount'] - d['paid_amount']
            debts_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(d['customer_name'], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(d['customer_phone'])),
                    ft.DataCell(ft.Text(f"{d['amount']:,.2f} ብር")),
                    ft.DataCell(ft.Text(f"{d['paid_amount']:,.2f} ብር", color="green_800")),
                    ft.DataCell(ft.Text(f"{rem:,.2f} ብር", color="red_800", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(d['created_at'])),
                    ft.DataCell(
                        ft.ElevatedButton("ከፍል", icon=ft.Icons.PAYMENT, bgcolor="blue_700", color="white", on_click=lambda e, debt=d: open_pay_debt_dialog(debt)) if rem > 0 else ft.Text("ተጠናቋል", color="green", weight=ft.FontWeight.BOLD)
                    )
                ])
            )
        conn.close()
        page.update()

    debts_tab = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([
                ft.Text("የደንበኞች ብድርና የክፍያ መዝገብ ደብተር", size=18, weight=ft.FontWeight.BOLD, color="teal_800"),
                ft.Spacer(),
                ft.ElevatedButton("+ አዲስ የብድር መዝገብ", icon=ft.Icons.ADD, bgcolor="teal", color="white", on_click=lambda e: page.open(add_debt_dialog))
            ]),
            ft.Divider(),
            ft.ListView(
                controls=[debts_table],
                expand=True
            )
        ])
    )

    # ------------------------------------------
    # TAB 5: SHOP EXPENSES (የሱቅ ወጪዎች)
    # ------------------------------------------
    expenses_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("የወጪው ርዕስ")),
            ft.DataColumn(ft.Text("ምድብ")),
            ft.DataColumn(ft.Text("የገንዘብ መጠን")),
            ft.DataColumn(ft.Text("ቀን")),
        ],
        rows=[]
    )

    exp_title_input = ft.TextField(label="የወጪው ርዕስ (ምሳሌ: የሱቅ ኪራይ/ሻይ)", dense=True)
    exp_cat_input = ft.Dropdown(
        label="ምድብ",
        options=[
            ft.dropdown.Option("ኪራይ"),
            ft.dropdown.Option("መብራትና ኢንተርኔት"),
            ft.dropdown.Option("የሰራተኛ አበል"),
            ft.dropdown.Option("የቀን ምግብና ሻይ"),
            ft.dropdown.Option("ሌሎች ወጪዎች"),
        ],
        dense=True
    )
    exp_amount_input = ft.TextField(label="የገንዘብ መጠን (ብር)", dense=True)

    def save_new_expense(e):
        if not exp_title_input.value or not exp_amount_input.value:
            show_snackbar("እባክዎን የወጪውን ርዕስ እና መጠን ያስገቡ!", "red")
            return
            
        today = datetime.date.today().strftime("%Y-%m-%d")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO expenses (title, category, amount, date)
            VALUES (?, ?, ?, ?)
        ''', (exp_title_input.value, exp_cat_input.value or "ሌሎች", float(exp_amount_input.value), today))
        conn.commit()
        conn.close()
        
        exp_title_input.value = ""
        exp_amount_input.value = ""
        page.close(add_exp_dialog)
        show_snackbar("የሱቅ ወጪ በስኬት ተመዝግቧል!")
        load_expenses_data()
        load_dashboard_data()

    add_exp_dialog = ft.AlertDialog(
        title=ft.Text("አዲስ የሱቅ ወጪ መዝግብ", weight=ft.FontWeight.BOLD, color="teal"),
        content=ft.Container(
            width=400,
            content=ft.Column([
                exp_title_input,
                exp_cat_input,
                exp_amount_input
            ], tight=True, spacing=10)
        ),
        actions=[
            ft.ElevatedButton("መዝግብ", icon=ft.Icons.SAVE, bgcolor="teal", color="white", on_click=save_new_expense),
            ft.TextButton("ሰርዝ", on_click=lambda e: page.close(add_exp_dialog))
        ]
    )

    def load_expenses_data():
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY id DESC")
        expenses = cursor.fetchall()
        expenses_table.rows.clear()
        
        for exp in expenses:
            expenses_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(exp['title'], weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(exp['category'])),
                    ft.DataCell(ft.Text(f"{exp['amount']:,.2f} ብር", color="red_800", weight=ft.FontWeight.BOLD)),
                    ft.DataCell(ft.Text(exp['date'])),
                ])
            )
        conn.close()
        page.update()

    expenses_tab = ft.Container(
        padding=10,
        content=ft.Column([
            ft.Row([
                ft.Text("የሱቅ ወጪዎች መመዝገቢያ", size=18, weight=ft.FontWeight.BOLD, color="teal_800"),
                ft.Spacer(),
                ft.ElevatedButton("+ አዲስ ወጪ መዝግብ", icon=ft.Icons.ADD, bgcolor="red_700", color="white", on_click=lambda e: page.open(add_exp_dialog))
            ]),
            ft.Divider(),
            ft.ListView(
                controls=[expenses_table],
                expand=True
            )
        ])
    )

    # ------------------------------------------
    # MAIN NAVIGATION TABS & APP BAR
    # ------------------------------------------
    tabs = ft.Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            ft.Tab(text="ዳሽቦርድ", icon=ft.Icons.DASHBOARD, content=dashboard_tab),
            ft.Tab(text="ጥገና መዝገብ", icon=ft.Icons.BUILD, content=repairs_tab),
            ft.Tab(text="አክሰሰሪና POS", icon=ft.Icons.SHOPPING_CART, content=inventory_tab),
            ft.Tab(text="የብድር ደብተር", icon=ft.Icons.BOOK, content=debts_tab),
            ft.Tab(text="የሱቅ ወጪ", icon=ft.Icons.MONEY_OFF, content=expenses_tab),
        ],
        expand=True
    )

    def refresh_all_data(e):
        load_dashboard_data()
        load_repairs_data()
        load_inventory_data()
        load_debts_data()
        load_expenses_data()
        show_snackbar("መረጃዎች በሙሉ ታድሰዋል!")

    page.appbar = ft.AppBar(
        title=ft.Row([
            ft.Icon(ft.Icons.CELL_SETTINGS, color="white", size=28),
            ft.Text("አዩ ሞባይል ሴንተር Pro", size=20, weight=ft.FontWeight.BOLD, color="white"),
        ]),
        bgcolor="teal_800",
        actions=[
            ft.IconButton(ft.Icons.REFRESH, icon_color="white", tooltip="መረጃዎችን አድስ", on_click=refresh_all_data),
            ft.IconButton(ft.Icons.INFO_OUTLINE, icon_color="white", tooltip="ስለ አዘጋጁ", on_click=open_about_dialog),
        ]
    )

    page.add(tabs)
    
    # Load initial data on startup
    load_dashboard_data()
    load_repairs_data()
    load_inventory_data()
    load_debts_data()
    load_expenses_data()

if __name__ == "__main__":
    ft.app(target=main)
