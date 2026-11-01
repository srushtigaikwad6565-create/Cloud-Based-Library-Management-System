
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Book, Issue

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')


# REGISTER
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or len(password) < 6:
            flash('Enter a username and password of at least 6 characters.')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('register'))

        user = User(
            username=username,
            password=generate_password_hash(password)
        )

        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please login.')
        return redirect(url_for('login'))

    return render_template('register.html')


# LOGIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid username or password!')

    return render_template('login.html')


# DASHBOARD
@app.route('/dashboard')
@login_required
def dashboard():
    total_books = Book.query.count()
    available_books = Book.query.filter_by(available=True).count()
    issued_books = Issue.query.filter_by(
        user_id=current_user.id,
        returned_at=None
    ).count()

    return render_template(
        'dashboard.html',
        total_books=total_books,
        available_books=available_books,
        issued_books=issued_books
    )


# VIEW AND SEARCH BOOKS
@app.route('/books')
@login_required
def books():
    search = request.args.get('search', '').strip()

    query = Book.query

    if search:
        query = query.filter(
            db.or_(
                Book.title.ilike(f'%{search}%'),
                Book.author.ilike(f'%{search}%')
            )
        )

    all_books = query.order_by(Book.id.desc()).all()

    return render_template('books.html', books=all_books)


# ADD BOOK
@app.route('/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()

        if not title or not author:
            flash('Please enter both book title and author.')
            return redirect(url_for('add_book'))

        book = Book(
            title=title,
            author=author,
            available=True
        )

        db.session.add(book)
        db.session.commit()

        flash('Book added successfully!')
        return redirect(url_for('books'))

    return render_template('add_book.html')


# EDIT BOOK
@app.route('/edit_book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = db.get_or_404(Book, book_id)

    if request.method == 'POST':
        title = request.form['title'].strip()
        author = request.form['author'].strip()

        if not title or not author:
            flash('Please enter title and author.')
            return redirect(url_for('edit_book', book_id=book.id))

        book.title = title
        book.author = author

        db.session.commit()

        flash('Book updated successfully!')
        return redirect(url_for('books'))

    return render_template('edit_book.html', book=book)


# DELETE BOOK
@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    book = db.get_or_404(Book, book_id)

    if not book.available:
        flash('Return this book before deleting it.')
    else:
        db.session.delete(book)
        db.session.commit()
        flash('Book deleted successfully!')

    return redirect(url_for('books'))


# ISSUE BOOK
@app.route('/issue_book/<int:book_id>', methods=['POST'])
@login_required
def issue_book(book_id):
    book = db.get_or_404(Book, book_id)

    if not book.available:
        flash('Sorry! This book is already issued.')
        return redirect(url_for('books'))

    issue = Issue(
        book_id=book.id,
        user_id=current_user.id
    )

    book.available = False

    db.session.add(issue)
    db.session.commit()

    flash('Book issued successfully!')
    return redirect(url_for('my_issues'))


# MY ISSUED BOOKS
@app.route('/my_issues')
@login_required
def my_issues():
    records = Issue.query.filter_by(
        user_id=current_user.id
    ).order_by(Issue.issued_at.desc()).all()

    return render_template('my_issues.html', records=records)


# RETURN BOOK
@app.route('/return_book/<int:issue_id>', methods=['POST'])
@login_required
def return_book(issue_id):
    issue = db.get_or_404(Issue, issue_id)

    if issue.user_id != current_user.id:
        flash('You cannot return another user’s book.')
        return redirect(url_for('my_issues'))

    if issue.returned_at is not None:
        flash('This book has already been returned.')
        return redirect(url_for('my_issues'))

    issue.returned_at = db.func.now()
    issue.book.available = True

    db.session.commit()

    flash('Book returned successfully!')
    return redirect(url_for('my_issues'))


# LOGOUT
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out successfully.')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
