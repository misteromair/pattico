from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super_secret_gold_key' # Change for production
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///profumi.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- DATABASE MODELS ---
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200), nullable=False)

class Analytics(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    clicks = db.Column(db.Integer, default=0)
    add_to_carts = db.Column(db.Integer, default=0)
    sales = db.Column(db.Integer, default=0)
    employee_logins = db.Column(db.Integer, default=0)

# --- AUTHENTICATION DECORATOR ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'employee_logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTES ---
@app.route('/')
def index():
    # Track page clicks
    stats = Analytics.query.first()
    stats.clicks += 1
    db.session.commit()
    
    products = Product.query.all()
    return render_template('index.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Track add to carts
    stats = Analytics.query.first()
    stats.add_to_carts += 1
    db.session.commit()

    if 'cart' not in session:
        session['cart'] = []
    
    session['cart'].append(product_id)
    session.modified = True
    flash('Profumo added to cart!', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_item_ids = session.get('cart', [])
    products = []
    total = 0
    for pid in cart_item_ids:
        product = Product.query.get(pid)
        if product:
            products.append(product)
            total += product.price
    return render_template('cart.html', products=products, total=total)

@app.route('/checkout', methods=['POST'])
def checkout():
    cart_items = session.get('cart', [])
    if cart_items:
        stats = Analytics.query.first()
        stats.sales += len(cart_items) # Count each item as a sale, or +1 for the order
        db.session.commit()
        session['cart'] = [] # Empty cart
        flash('Purchase successful! Thank you.', 'success')
    return redirect(url_for('index'))

@app.route('/employee/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        # Simple auth for prototype
        if password == 'gold123': 
            session['employee_logged_in'] = True
            stats = Analytics.query.first()
            stats.employee_logins += 1
            db.session.commit()
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials', 'error')
    return render_template('login.html')

@app.route('/employee/logout')
def logout():
    session.pop('employee_logged_in', None)
    return redirect(url_for('index'))

@app.route('/employee/dashboard')
@login_required
def dashboard():
    stats = Analytics.query.first()
    return render_template('dashboard.html', stats=stats)

# --- INITIALIZATION ---
def setup_database():
    with app.app_context():
        db.create_all()
        # Create initial analytics row
        if not Analytics.query.first():
            db.session.add(Analytics())
        # Add sample products
        if not Product.query.first():
            products = [
                Product(name="Oud Magnifique", price=120.00, description="Deep woody notes with a touch of vanilla."),
                Product(name="Notte Nera", price=95.00, description="Fresh bergamot fading into dark leather."),
                Product(name="Venezia D'Oro", price=150.00, description="A luxurious blend of amber and spices.")
            ]
            db.session.bulk_save_objects(products)
        db.session.commit()

if __name__ == '__main__':
    setup_database()
    app.run(debug=True)
