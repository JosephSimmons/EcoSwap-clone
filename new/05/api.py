from flask import Blueprint, request, abort, jsonify
import sqlalchemy.orm                       

from models import Category, Product, User

from app import db

api = Blueprint('api', __name__)


@api.route('/product')
def products_for_category():
    try:
        category_id = int(request.args.get('category_id'))
        category = Category.query.filter(Category.id == category_id).one()
    except ValueError:
        # category_id not a number
        abort(404)
    except sqlalchemy.orm.exc.NoResultFound:
        # No category found for this id
        abort(404)

    products = Product.query.filter(Product.category_id == category_id).all()
    return jsonify([product.as_dict() for product in products])

@api.route('/search')
def search_query_product():
    try:
        name = str(request.args.get('name'))
        product = Product.query.filter(Product.name.ilike(f"%{name}%")).count()
        if product<1:
            raise Exception
    except Exception as error:
        print("Search Results do not exist")
        abort(404)
    
    products = Product.query.filter(Product.name.ilike(f"%{name}%")).all()
    return jsonify([product.as_dict() for product in products])

@api.route('/register')
def register_api():
    return jsonify(
        register(
            str(request.args.get('username')),
            str(request.args.get('email')),
            str(request.args.get('password'))
        )
    )

def register(username=None, email=None, password=None):
    if User.query.filter(User.username == username).count():
        return {"result": f'Error: {username} user already exists'}

    if User.query.filter(User.email == email).count():
        return {"result": f'Error: {email} user email address already exists'}

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    return {"result": "ok"}

# @api.route('/search')
# def add_product():
#     return jsonify