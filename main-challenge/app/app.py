from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
import datetime
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# ✅ Setup limiter (limit based on IP address)
limiter = Limiter(get_remote_address, app=app, default_limits=["200 per day", "50 per hour"])


# Database setup
def init_db():
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                access TEXT DEFAULT 'user' NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                content TEXT NOT NULL CHECK (LENGTH(content) <= 255),
                profile_pic TEXT,
                date TEXT NOT NULL,
                score INTEGER NOT NULL CHECK (score BETWEEN 0 AND 5),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('products', 0)")
        
        conn.commit()

        # Add example products if the table is empty
        cursor.execute("SELECT COUNT(*) FROM products")
        product_count = cursor.fetchone()[0]
        
        if product_count == 0:
            example_products = [
                ('تی شرت بردان', 'تی‌شرتی سبک و راحت با طراحی مدرن که از پارچه باکیفیت و ضدحساسیت تهیه شده است. مناسب برای استفاده روزمره، ورزش و استایل کژوال. دارای دوخت مقاوم و رنگ‌بندی متنوع برای سلیقه‌های مختلف. به‌راحتی شسته شده و کیفیت پارچه پس از شستشو حفظ می‌شود. انتخابی عالی برای افرادی که به استایل و راحتی اهمیت می‌دهند.', 21000),
                ('کوله پشتی', 'یک کوله‌پشتی مدرن با طراحی ارگونومیک و فضای کافی برای حمل وسایل روزانه. دارای چندین جیب مجزا برای نظم‌دهی بهتر و حمل لپ‌تاپ، کتاب و لوازم شخصی. ساخته‌شده از مواد مقاوم در برابر آب و سایش برای دوام بیشتر. دارای بندهای قابل تنظیم و پدگذاری شده برای راحتی بیشتر در حمل. گزینه‌ای عالی برای دانشجویان، مسافران و افراد پرمشغله.', 250000),
                ('ساعت الگنت', 'یک ساعت شیک و مدرن که زیبایی و کارایی را در کنار هم ارائه می‌دهد. طراحی ظریف و منحصر‌به‌فرد آن مناسب برای استفاده روزمره و موقعیت‌های رسمی است. دارای صفحه‌ای خوانا و بند مقاوم برای استفاده طولانی‌مدت. موتور باکیفیت و دقیق که زمان را با دقت بالا نمایش می‌دهد. انتخابی عالی برای افرادی که به استایل و دقت اهمیت می‌دهند.', 50000),
                ('کوله سبک', 'یک کوله‌پشتی فوق سبک و کم‌حجم که برای حمل آسان طراحی شده است. مناسب برای افرادی که به دنبال راحتی بیشتر و آزادی حرکت هستند. ساخته‌شده از پارچه مقاوم و ضدآب، ایده‌آل برای استفاده روزانه و سفرهای کوتاه. دارای زیپ‌های روان و جیب‌های کاربردی برای حمل وسایل ضروری. بهترین انتخاب برای افرادی که به مینیمالیسم و کارایی اهمیت می‌دهند.', 180000),
                ('لباس چرم', 'یک لباس چرم باکیفیت که ظاهری شیک و کلاسیک را به استایل شما می‌بخشد. تهیه‌شده از چرم طبیعی یا مصنوعی مقاوم، مناسب برای فصول سرد سال. دارای طراحی مدرن با جزئیات خاص که ظاهری جذاب و لوکس ایجاد می‌کند. دوخت محکم و دقیق که دوام و ماندگاری لباس را تضمین می‌کند. مناسب برای موقعیت‌های رسمی و نیمه‌رسمی، ایده‌آل برای علاقه‌مندان به مد.', 200000),
                ('لباس کودک', 'یک لباس نرم و راحت برای کودکان، ساخته‌شده از الیاف ضدحساسیت. طراحی زیبا و رنگ‌های جذاب که برای کودکان دلنشین و دوست‌داشتنی است. دارای دوخت بادوام که امکان شستشوی مکرر بدون آسیب به بافت پارچه را فراهم می‌کند. سبک و انعطاف‌پذیر، مناسب برای فعالیت‌های روزانه کودک. انتخابی ایده‌آل برای راحتی و سلامت پوست حساس کودکان.', 300000),
                ('هدفون سونی', 'یک هدفون باکیفیت که تجربه‌ای عالی از موسیقی و تماس‌های صوتی را فراهم می‌کند. دارای قابلیت حذف نویز برای ایجاد صدایی واضح و شفاف در محیط‌های شلوغ. طراحی ارگونومیک و سبک که راحتی را برای استفاده طولانی‌مدت تضمین می‌کند. مجهز به باتری بادوام و قابلیت اتصال بی‌سیم برای آزادی حرکت بیشتر. مناسب برای گوش دادن به موسیقی، گیمینگ و استفاده روزمره.', 100000),
                ('کیف چرم', 'یک کیف چرم شیک و باکیفیت که استایل لوکس و حرفه‌ای را به شما می‌بخشد. ساخته‌شده از چرم طبیعی یا مصنوعی مقاوم، مناسب برای استفاده روزانه و رسمی. دارای بخش‌های مجزا برای حمل لپ‌تاپ، مدارک و وسایل شخصی. زیپ‌های مقاوم و دوخت بادوام که طول عمر کیف را افزایش می‌دهد. گزینه‌ای ایده‌آل برای افراد شیک‌پوش و حرفه‌ای که به کیفیت اهمیت می‌دهند.', 1300000)
            ]
            cursor.executemany("INSERT INTO products (name, description, price) VALUES (?, ?, ?)", example_products)
            conn.commit()
            example_comments = [
                (1, 'علی رضایی', 'تی‌شرت خیلی راحت و سبک بود، کیفیتش هم خیلی خوبه.', '/static/images/user/default.png', '2025-02-08', 5),
                (1, 'مریم احمدی', 'پارچه خیلی لطیف و خوش دوخت، ولی رنگش کمی متفاوت بود.', '/static/images/user/default.png', '2025-02-07', 4),
                (2, 'حسن کریمی', 'کوله‌پشتی جاداره و جنس خوبی داره، ولی زیپ‌هاش یکم سفته.', '/static/images/user/default.png', '2025-02-06', 4),
                (3, 'سارا بهرامی', 'ساعت خیلی شیک و سبک هست، از خریدش خیلی راضیم.', '/static/images/user/default.png', '2025-02-05', 5),
                (4, 'رضا معتمدی', 'کوله‌پشتی خیلی سبکه و حملش راحته، ولی میتونست جیب بیشتری داشته باشه.', '/static/images/user/default.png', '2025-02-04', 3),
                (5, 'نرگس صادقی', 'کیفیت چرم عالیه، خیلی خوش‌دوخت و زیباست.', '/static/images/user/default.png', '2025-02-03', 5),
                (6, 'امیر فراهانی', 'لباس کودک نرم و راحت، ولی سایزش کمی بزرگ‌تر از حد انتظار بود.', '/static/images/user/default.png', '2025-02-02', 4),
                (7, 'زهرا محمدی', 'هدفون صدای خیلی خوبی داره، ولی باتریش میتونست بهتر باشه.', '/static/images/user/default.png', '2025-02-01', 4),
                (8, 'کامران کاظمی', 'کیف چرم بسیار زیبا و شیک، ولی کمی گرونه.', '/static/images/user/default.png', '2025-01-31', 4)
            ]
            cursor.executemany("INSERT INTO comments (product_id, name, content, profile_pic, date, score) VALUES (?, ?, ?, ?, ?, ?)", example_comments)
            conn.commit()
        


@app.route('/')
def home():
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
    return render_template('home.html', products=products)

@app.route('/products')
def product_list():
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products")
        products = cursor.fetchall()
    return render_template('product_list.html', products=products)


@app.route('/product/<product_id>')
def product_detail(product_id):
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()

        # INSECURE: Direct string formatting into SQL query
        query = f"SELECT * FROM products WHERE id = {product_id}"
        cursor.execute(query)
        product = cursor.fetchone()

        # Simulate time-based injection (example attack: 1 OR RANDOM() < 1.000001)
        query = f"SELECT name, content, profile_pic, date, score FROM comments WHERE product_id = {product_id}"
        cursor.execute(query)
        comments = cursor.fetchall()

        query = f"SELECT * FROM products WHERE id != {product_id} ORDER BY RANDOM() LIMIT 5"
        cursor.execute(query)
        other_products = cursor.fetchall()

    return render_template('product_detail.html', product=product, comments=comments, other_products=other_products)


@app.route('/product/<int:product_id>/comment', methods=['POST'])
def submit_comment(product_id):
    name = session.get('username', 'Anonymous')
    content = request.form.get('message')
    score = request.form.get('star', 0)  # Default to 0 if not provided
    profile_pic = "/static/images/user/default.png"  # You can replace this with an actual profile image path
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO comments (product_id, name, content, profile_pic, date, score) VALUES (?, ?, ?, ?, ?, ?)", 
                       (product_id, name, content, profile_pic, date, score))
        conn.commit()

    return redirect(url_for('product_detail', product_id=product_id))


@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("تعداد درخواست بیش از حد")
def login():
    login_failed = False
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = cursor.fetchone()
            if user:
                session['username'] = user[1]  # Assuming the second column is the username
                flash('Login successful!', 'success')
                return redirect(url_for('profile'))
            else:
                login_failed = True
    return render_template('login.html', login_failed=login_failed)

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("تعداد درخواست بیش از حد")  # ✅ Apply rate limit
def register():
    user_exists = False
    registration_successful = False

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        with sqlite3.connect("app.db") as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
                conn.commit()
                registration_successful = True
            except sqlite3.IntegrityError:
                # Username exists, but we won't explicitly tell the user
                user_exists = True  # We won't show this to prevent enumeration

        # ✅ Show generic message
        if registration_successful:
            flash('Registration completed.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Registration could not be completed.', 'danger')

    return render_template('register.html',user_exists=user_exists)


@app.route('/profile')
def profile():
    if 'username' not in session:
        flash('You need to log in first.', 'warning')
        return redirect(url_for('login'))
    
    username = session['username']
    with sqlite3.connect("app.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
    
    if user:
        user_data = {
            'id': user[0],         # Assuming ID is the first column
            'username': user[1],   # Username
            'access': user[3]
        }
    else:
        user_data = None

    return render_template('profile.html', user=user_data)

@app.route("/about-us")
def about_us():
    return render_template('about-us.html')

@app.route('/logout')
def logout():
    # Clear the user session
    session.pop('username', None)
    # Redirect to the home page
    return redirect('/')

if __name__ == '__main__':
    init_db()  # Initialize database
    app.run(host='0.0.0.0', port=8081, debug=True)
