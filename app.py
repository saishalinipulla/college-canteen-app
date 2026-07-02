import os
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Student, Admin, MenuItem, Order, OrderItem

# -----------------------------------------------------------------
# App & database setup
# -----------------------------------------------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'change-this-secret-key')
basedir = os.path.abspath(os.path.dirname(__file__))
db_url = os.environ.get('DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'canteen.db'))
# Render (and some other hosts) hand out URLs starting with "postgres://",
# but SQLAlchemy 2.x requires "postgresql://" — fix it up automatically.
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

CATEGORIES = {
    'tiffins':  'Tiffins (Dosa Varieties)',
    'idlis':    'Idlis',
    'lunch':    'Lunch',
    'snacks':   'Snacks',
    'biryanis': 'Biryanis',
    'fastfood': 'Fast Food',
}


@app.context_processor
def inject_categories():
    # Makes `categories` available in every template automatically (used by the navbar)
    return {'categories': CATEGORIES}


# -----------------------------------------------------------------
# Helpers / decorators
# -----------------------------------------------------------------
def student_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('student_id'):
            flash('Please login with your name and phone number first.', 'warning')
            return redirect(url_for('student_login', next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please login as admin first.', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper


def get_cart():
    return session.setdefault('cart', [])


# -----------------------------------------------------------------
# Public / student routes
# -----------------------------------------------------------------
@app.route('/')
def home():
    return render_template('index.html', categories=CATEGORIES)


@app.route('/menu/<category>')
def menu(category):
    if category not in CATEGORIES:
        flash('Unknown category.', 'danger')
        return redirect(url_for('home'))
    items = MenuItem.query.filter_by(category=category, available=True).all()
    return render_template('category.html', items=items,
                            category=category, category_label=CATEGORIES[category])


@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    item = MenuItem.query.get_or_404(item_id)
    qty = max(1, int(request.form.get('quantity', 1)))

    cart = get_cart()
    for line in cart:
        if line['item_id'] == item_id:
            line['quantity'] += qty
            break
    else:
        cart.append({
            'item_id': item.id,
            'name': item.name,
            'price': item.price,
            'quantity': qty,
        })
    session['cart'] = cart
    session.modified = True
    flash(f'Added {item.name} to your cart.', 'success')
    return redirect(url_for('menu', category=item.category))


@app.route('/cart')
def cart():
    cart = get_cart()
    total = sum(line['price'] * line['quantity'] for line in cart)
    return render_template('cart.html', cart=cart, total=total)


@app.route('/update_cart/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    action = request.form.get('action')
    cart = get_cart()
    if action == 'remove':
        cart = [line for line in cart if line['item_id'] != item_id]
    else:
        for line in cart:
            if line['item_id'] == item_id:
                if action == 'increase':
                    line['quantity'] += 1
                elif action == 'decrease':
                    line['quantity'] = max(1, line['quantity'] - 1)
    session['cart'] = cart
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/checkout', methods=['POST'])
@student_login_required
def checkout():
    cart = get_cart()
    if not cart:
        flash('Your cart is empty.', 'warning')
        return redirect(url_for('cart'))

    order = Order(
        student_id=session['student_id'],
        student_name=session['student_name'],
        student_phone=session['student_phone'],
        status='Pending',
    )
    for line in cart:
        order.items.append(OrderItem(
            item_name=line['name'],
            price=line['price'],
            quantity=line['quantity'],
        ))
    db.session.add(order)
    db.session.commit()

    session['cart'] = []
    session.modified = True
    # This flash is shown as a pop-up alert() box by base.html
    flash(f'Order #{order.id} placed successfully! The canteen will confirm it shortly.', 'popup')
    return redirect(url_for('my_orders'))


@app.route('/my_orders')
@student_login_required
def my_orders():
    orders = Order.query.filter_by(student_id=session['student_id']) \
                         .order_by(Order.created_at.desc()).all()
    return render_template('my_orders.html', orders=orders)


# -----------------------------------------------------------------
# Student login (name + phone number) / logout
# -----------------------------------------------------------------
@app.route('/login', methods=['GET', 'POST'])
def student_login():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name or not phone:
            flash('Please enter both name and phone number.', 'danger')
            return redirect(url_for('student_login'))

        student = Student.query.filter_by(phone=phone).first()
        if student:
            student.name = name  # keep name up to date
        else:
            student = Student(name=name, phone=phone)
            db.session.add(student)
        db.session.commit()

        session['student_id'] = student.id
        session['student_name'] = student.name
        session['student_phone'] = student.phone

        flash(f'Welcome, {student.name}!', 'success')
        next_url = request.args.get('next') or url_for('home')
        return redirect(next_url)

    return render_template('login.html')


@app.route('/logout')
def student_logout():
    session.pop('student_id', None)
    session.pop('student_name', None)
    session.pop('student_phone', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))


# -----------------------------------------------------------------
# Admin routes
# -----------------------------------------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')

        admin = Admin.query.filter_by(phone=phone).first()
        if admin and admin.check_password(password):
            session['admin_id'] = admin.id
            flash('Welcome back, admin.', 'success')
            return redirect(url_for('admin_dashboard'))

        flash('Invalid phone number or password.', 'danger')
        return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_id', None)
    flash('Admin logged out.', 'info')
    return redirect(url_for('home'))


@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    pending = Order.query.filter_by(status='Pending').order_by(Order.created_at).all()
    accepted = Order.query.filter_by(status='Accepted').order_by(Order.created_at).all()
    return render_template('admin_dashboard.html', pending=pending, accepted=accepted)


@app.route('/admin/order/<int:order_id>/accept', methods=['POST'])
@admin_login_required
def accept_order(order_id):
    order = Order.query.get_or_404(order_id)
    order.status = 'Accepted'
    db.session.commit()
    flash(f'Order #{order.id} accepted.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/order/<int:order_id>/reject', methods=['POST'])
@admin_login_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)  # rejected orders are removed
    db.session.commit()
    flash(f'Order #{order_id} rejected and removed.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/order/<int:order_id>/complete', methods=['POST'])
@admin_login_required
def complete_order(order_id):
    order = Order.query.get_or_404(order_id)
    db.session.delete(order)  # completed orders are removed from the DB
    db.session.commit()
    flash(f'Order #{order_id} marked completed and removed.', 'success')
    return redirect(url_for('admin_dashboard'))


# -----------------------------------------------------------------
# One-time DB setup + a few sample menu items (safe to run every start)
# -----------------------------------------------------------------
def seed_menu_if_empty():
    if MenuItem.query.first():
        return
    sample_items = [
        ('Plain Dosa', 'tiffins', 40),
        ('Masala Dosa', 'tiffins', 50),
        ('Onion Dosa', 'tiffins', 50),
        ('Rava Dosa', 'tiffins', 60),
        ('Idli (2 pcs)', 'idlis', 30),
        ('Idli Sambar', 'idlis', 35),
        ('Veg Meals', 'lunch', 80,),
        ('Curd Rice', 'lunch', 50),
        ('Samosa', 'snacks', 20),
        ('French Fries', 'snacks', 60),
        ('Chicken Biryani', 'biryanis', 150),
        ('Veg Biryani', 'biryanis', 100),
        ('Burger', 'fastfood', 70),
        ('Veg Pizza (Slice)', 'fastfood', 90),
    ]
    for name, category, price in sample_items:
        db.session.add(MenuItem(name=name, category=category, price=price))
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_menu_if_empty()


if __name__ == '__main__':
    app.run(debug=True)
