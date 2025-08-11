from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Transaction, Category
from app.forms import LoginForm, RegisterForm, TransactionForm, CategoryForm
from app.utils import save_receipt_file
import os
from datetime import datetime, timedelta
from sqlalchemy import func, extract

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if user already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'error')
            return render_template('register.html', form=form)
        
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already registered', 'error')
            return render_template('register.html', form=form)
        
        # Create new user
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Create default categories
        default_categories = [
            ('Food & Dining', '#ff6b6b'),
            ('Transportation', '#4ecdc4'),
            ('Shopping', '#45b7d1'),
            ('Entertainment', '#f9ca24'),
            ('Bills & Utilities', '#f0932b'),
            ('Healthcare', '#eb4d4b'),
            ('Salary', '#6c5ce7'),
            ('Other', '#a0a0a0')
        ]
        
        for cat_name, cat_color in default_categories:
            category = Category(name=cat_name, color=cat_color, user_id=user.id)
            db.session.add(category)
        
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    # Get recent transactions
    recent_transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                         .order_by(Transaction.created_at.desc())\
                                         .limit(5).all()
    
    # Calculate monthly stats
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    monthly_income = db.session.query(func.sum(Transaction.amount))\
                              .filter_by(user_id=current_user.id, transaction_type='income')\
                              .filter(extract('month', Transaction.date) == current_month)\
                              .filter(extract('year', Transaction.date) == current_year)\
                              .scalar() or 0
    
    monthly_expenses = db.session.query(func.sum(Transaction.amount))\
                                .filter_by(user_id=current_user.id, transaction_type='expense')\
                                .filter(extract('month', Transaction.date) == current_month)\
                                .filter(extract('year', Transaction.date) == current_year)\
                                .scalar() or 0
    
    # Category-wise expenses for current month
    category_expenses = db.session.query(Category.name, func.sum(Transaction.amount))\
                                 .join(Transaction)\
                                 .filter(Transaction.user_id == current_user.id)\
                                 .filter(Transaction.transaction_type == 'expense')\
                                 .filter(extract('month', Transaction.date) == current_month)\
                                 .filter(extract('year', Transaction.date) == current_year)\
                                 .group_by(Category.name)\
                                 .all()
    
    return render_template('dashboard.html', 
                         recent_transactions=recent_transactions,
                         monthly_income=monthly_income,
                         monthly_expenses=monthly_expenses,
                         category_expenses=category_expenses,
                         total_balance=current_user.get_balance())

@main.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    
    # Populate category choices
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        # Handle file upload
        receipt_filename = None
        if form.receipt.data:
            receipt_filename = save_receipt_file(form.receipt.data, current_user.id)
        
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_type=form.transaction_type.data,
            date=form.date.data,
            category_id=form.category_id.data if form.category_id.data else None,
            receipt_filename=receipt_filename,
            notes=form.notes.data,
            user_id=current_user.id
        )
        
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!', 'success')
        return redirect(url_for('main.transactions'))
    
    return render_template('add_transaction.html', form=form)

@main.route('/transactions')
@login_required
def transactions():
    page = request.args.get('page', 1, type=int)
    transactions = Transaction.query.filter_by(user_id=current_user.id)\
                                  .order_by(Transaction.date.desc())\
                                  .paginate(page=page, per_page=20, error_out=False)
    
    return render_template('transactions.html', transactions=transactions)

@main.route('/edit_transaction/<int:transaction_id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    form = TransactionForm(obj=transaction)
    
    # Populate category choices
    categories = Category.query.filter_by(user_id=current_user.id).all()
    form.category_id.choices = [(c.id, c.name) for c in categories]
    
    if form.validate_on_submit():
        # Handle file upload if new receipt is provided
        if form.receipt.data:
            # Delete old receipt if exists
            if transaction.receipt_filename:
                old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), transaction.receipt_filename)
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
            
            # Save new receipt
            receipt_filename = save_receipt_file(form.receipt.data, current_user.id)
            transaction.receipt_filename = receipt_filename
        
        # Update transaction fields
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.transaction_type = form.transaction_type.data
        transaction.date = form.date.data
        transaction.category_id = form.category_id.data if form.category_id.data else None
        transaction.notes = form.notes.data
        
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.transactions'))
    
    return render_template('edit_transaction.html', form=form, transaction=transaction)

@main.route('/delete_transaction/<int:transaction_id>', methods=['POST'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    # Delete associated receipt file if exists
    if transaction.receipt_filename:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), transaction.receipt_filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete thumbnail if exists
        thumb_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), 'thumbnails', transaction.receipt_filename)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
    
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!', 'success')
    return redirect(url_for('main.transactions'))

@main.route('/download_receipt/<int:transaction_id>')
@login_required
def download_receipt(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    
    if not transaction.receipt_filename:
        flash('No receipt found for this transaction.', 'error')
        return redirect(url_for('main.transactions'))
    
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], str(current_user.id), transaction.receipt_filename)
    
    if not os.path.exists(file_path):
        flash('Receipt file not found.', 'error')
        return redirect(url_for('main.transactions'))
    
    return send_file(file_path, as_attachment=True, download_name=f"receipt_{transaction.description}_{transaction.date}.{transaction.receipt_filename.split('.')[-1]}")

@main.route('/api/transactions')
@login_required
def api_transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).all()
    return jsonify([{
        'id': t.id,
        'amount': t.amount,
        'description': t.description,
        'type': t.transaction_type,
        'date': t.date.isoformat(),
        'category': t.category.name if t.category else None
    } for t in transactions])

@main.route('/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })
