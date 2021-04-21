from flask import Flask, render_template, flash, redirect, url_for, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate                   # alembic - database migration tool
from flask_admin import Admin                       # admin
from flask_admin.contrib.sqla import ModelView      # admin
from flask_login import LoginManager, current_user, login_user, logout_user, login_required

from forms import NewCategoryForm, NewProductForm, NewUserForm, PostForm, LoginForm, RemoveProduct, RemoveCategory, RemoveUser, RemovePost

app = Flask(__name__)                                           # init app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../data/ecoswap_database.sqlite'    # connecting to sqlite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False            # set false to stop warnings
app.config['SECRET_KEY'] = 'random string'                      # forms
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'                   # theme of admin pages


db = SQLAlchemy(app)                                            # init db, binding to app

migrate = Migrate(app, db)                                      # alembic
login = LoginManager(app)                                       # Flask-Login needs to know the view function that handles logins
login.login_view = 'login'                                      # 'login' is the function/endpoint for the login view

from models import Category, Product, User, Post
from api import api                                             # api
import json
import api as api_component
app.register_blueprint(api, url_prefix='/api')                  # api

admin = Admin(app, name='Ecoswap', template_mode='bootstrap3')    # admin
admin.add_view(ModelView(Category, db.session))                   # admin
admin.add_view(ModelView(Product, db.session))                    # admin
admin.add_view(ModelView(User, db.session))                       # admin
admin.add_view(ModelView(Post, db.session))                       # admin

## HOMEPAGE FOR APP

@app.route('/')
def index():
    return render_template('index.html')

## ******************* USER LOGIN ********************* ##

@app.route('/login', methods=['POST'])
def login():
    user_arg = request.json.get('user')
    password_arg = request.json.get('password')

    user = User.query.filter_by(username=user_arg).first()
    
    if user is None or not (password_arg == 'correct'):
        return jsonify({'result':'Invalid username or password'})

    if login_user(user):
        return jsonify({'result':'ok'})
    else:
        return jsonify({'result':'failed'})


## ******************* USER REGISTRATION **************** ##

# creating and reading new users for the site
@app.route('/register', methods=['GET', 'POST'])
def newuser():
    form=NewUserForm()
    if not form.validate_on_submit():
        return render_template('new_user.html', form=form)

    username = form.username.data.strip()
    email = form.email.data.strip()
    
    result = api_component.register(username, email, "foo")

    if result["result"] != "ok":
        flash(result["result"])
        return render_template('new_user.html', form=form)
    else:
        flash(f'New user {form.username.data} registered')
        return redirect('/login')
    
    
    

## ******************* DELETING USERS - BACKEND ******************* ##

@app.route('/delete_user', methods=['GET','POST'])
def remove_user():
    form = RemoveUser()

    if (request.method=='GET'):
        return render_template('delete_user.html', users=User.query.all(), form=form)
    else:

        if not form.validate_on_submit():
            return render_template('delete_user.html', form=form)
        
        name = request.form.get("name")                                       # string that the user passes through

        if not User.query.filter(User.username == name).count():
            flash(f'User "{name}" does not exist')
            return render_template('delete_user.html', form=form)

        user = User.query.filter(User.username == name).first()               # finding the matching username

        db.session.delete(user)
        db.session.commit()
        flash(f'User "{name}" deleted')
        return redirect ('/')


## ******************* ACCESSING PRODUCTS - FRONTEND ******************* ##

# list all products available
@app.route('/products')
@login_required
def list_products():
    products_by_category = {
        category: Product.query.filter(Product.category == category)
        for category in Category.query.all()
    }
    return render_template('products.html', categories=Category.query.all(), products_by_category=products_by_category)

# searching for products in a category
@app.route('/nproducts_for_category', methods=['GET','POST'])
def nproducts_for_category():
    if (request.method == 'GET'):
        return render_template('nproducts_for_category.html', categories=Category.query.all())
    else:
        searched_category_id = request.form.get('category_id')
        products = Product.query.filter(Product.category_id == searched_category_id).all()
        return render_template('nproducts_for_category_results.html', products=products, categories=Category.query.all())


## ************ CREATING PRODUCTS, CATEGORIES AND POSTS******* ##

# reading and creating new products in the database
@app.route('/new_product', methods=['GET', 'POST'])
def new_product():
    form = NewProductForm()
    if not form.validate_on_submit():
        return render_template('new_product.html', form=form)

    category = form.category.data.strip()
    name = form.name.data.strip()
    price = int(form.price.data)
    product_des = form.product_des.data.strip()

    if Product.query.filter(Product.name == name).count():
        flash(f'Error: {name} already exists')
        return render_template('new_product.html', form=form)

    prod_cat = Category.query.filter(Category.name == category).first()

    if not Category.query.filter(Category.name == category).count():
        flash(f'Error: {name} needs existing category {category}')
        return render_template('new_product.html', form=form)

    product = Product(category=prod_cat, name=name, product_des=product_des, price=price)
    db.session.add(product)
    db.session.commit()
    flash(f'New product {name} created')
    return redirect('/products')


# reading and creating new categories in the database
@app.route('/new_category', methods=['GET', 'POST'])
def new_category():
    form = NewCategoryForm()
    if not form.validate_on_submit():
        return render_template('new_category.html', form=form)

    name = form.name.data.strip()

    if Category.query.filter(Category.name == name).count():
        flash(f'Error: {name} already exists')
        return render_template('new_category.html', form=form)

    category = Category(name=name)
    db.session.add(category)
    db.session.commit()
    flash(f'New category {name} created')
    return redirect('/products')

# reading and creating new posts in the database
@app.route('/new_post', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if not form.validate_on_submit():
        return render_template('new_post.html', form=form)

    title = form.title.data.strip()
    content=form.content.data.strip()

    if Post.query.filter(Post.title == title).count():
        flash(f'Error: {title} already exists')
        return render_template('new_post.html', form=form)

    post = Post(title=title, content=content)
    db.session.add(post)
    db.session.commit()
    flash(f'New Post {title} created')
    return redirect('/')


## ********** DELETING POSTS, CATEGORIES AND PRODUCT ENTRIES FROM DB ************ ##
#Deleting existing products

@app.route('/delete_product', methods=['GET','POST'])
def remove_product():
    form = RemoveProduct()

    if (request.method == 'GET'):
        return render_template('delete_product.html', products=Product.query.all(),form=form)

    else:
        if not form.validate_on_submit():
            return render_template('delete_product.html', form=form)

        # get prod. name submitted in form
        name = request.form.get("name")
        print(name)

        # querying the database for the same product name
        if not Product.query.filter(Product.name == name).count():
            flash(f'Product "{name}" does not exist')
            return render_template('delete_product.html', form=form)

        prod = Product.query.filter(Product.name == name).one()
        
        # deleting from database
        db.session.delete(prod)
        db.session.commit()
        
        flash(f'Product "{name}" deleted')
        return redirect ('/products')


# Deleting existing categories
@app.route('/delete_category', methods=['GET', 'POST'])
@login_required
def remove_category():
    form = RemoveCategory()

    if (request.method == 'GET'):
        return render_template('delete_category.html', categories=Category.query.all(),form=form)

    else:
        if not form.validate_on_submit():
            return render_template('delete_category.html', form=form)
        
        name = request.form.get("name")                                       # string that the user passes through

        if not Category.query.filter(Category.name == name).count():
            flash(f'Category "{name}" does not exist')
            return render_template('delete_category.html', form=form)

        category = Category.query.filter(Category.name == name).first()       # finding the first thing matching category name

        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{name}" deleted')
        return redirect ('/products')

#Deleting Posts
@app.route('/delete_post', methods=['GET','POST'])
def remove_post():
    form = RemovePost()
    if (request.method == 'GET'):
        return render_template('delete_post.html', posts=Post.query.all(),form=form)

    if not form.validate_on_submit():
        return render_template('delete_post.html', form=form)
    
    title = request.form.get("title")                           # string that the user passes through

    post = Post.query.filter(Post.title == title).first()       # finding the first post/row with matching title

    db.session.delete(post)
    db.session.commit()
    flash(f'Post "{title}" deleted')
    return redirect ('/products')


## ******************* USER LOGOUT **************** ##

# logging out of a session
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


## ******************* SEARCH **************** ##

@app.route('/search', methods=('GET','POST'))
def search():
    if (request.method == 'GET'):
        return render_template ('search.html')
    else:
        searched_product = request.form.get('name')
        products = Product.query.filter(Product.name.ilike(f"%{searched_product}%")).all()
        return jsonify([product.as_dict() for product in products])


## ************* POSTMAN *******************##


#Updating the product
@app.route('/new_product_update', methods=['PUT'])
def update(): 
    
    # FOR READING DATA THROUGH POSTMAN
    # will have to read inputs in JSON
    request_data = request.get_json() 
    
    name_to_update = None
    price_to_update = None
    product_des_to_update = None

    #if the user has submitted all this to be updated
    if request_data:
      if 'name' in request_data:
          name_to_update = request_data['name']

      if 'price' in request_data:
          price_to_update = int(request_data['price'])

      if 'product_des' in request_data:
          product_des_to_update = request_data['product_des']

    result = db.session.query(Product).filter(Product.name == name_to_update).count()
    if result < 1:
        return f"{name_to_update} doesnt exist so update aborted"

    prod = db.session.query(Product).filter(Product.name == name_to_update)
    try:
        prod = prod.update(                                                  # reassignment of updated product
            {
                "name": name_to_update,
                "price": price_to_update,
                "product_des": product_des_to_update
            }, synchronize_session = False
        )
    except Exception as exc:
        return(f"Error: {exc}")

    db.session.commit()
    flash(f'Product {name_to_update} edited')

    return(f'{name_to_update} has been updated')
    # return redirect('/products')


@app.route('/allproducts', methods=['GET'])
def showproducts():
    products = Product.query.all()
    return jsonify([product.as_dict() for product in products])

# @app.route('/users')
# def list_users():
#         for user in User.query.all():
#             print(user)
#         return "users :)"