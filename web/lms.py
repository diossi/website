import flask
from flask import Flask, redirect, render_template, request, flash, url_for
from flask_login import current_user, login_user, LoginManager, login_required, logout_user
from forms.forms import RegisterForm, LoginForm, ChangePassword
from data import db_session
from data.users import User
from data.items import Item
from data.want_buy_item import WantBuyItem

blueprint = flask.Blueprint(
    'api',
    __name__,
    template_folder='templates'
)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Пожалуйста, войдите для доступа к этой странице."

db_session.global_init("db/blogs.db")


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route("/")
def index():
    db_sess = db_session.create_session()
    items = db_sess.query(Item).filter(Item.is_see == True).limit(3).all()

    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Джинсы'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
    ]

    return render_template("index.html",
                           title='FashionStore - Главная',
                           products=items,
                           categories=categories,
                           current_user=current_user)


@app.route('/category/<int:category_id>')
def category(category_id):
    db_sess = db_session.create_session()

    category_map = {
        1: 'Футболка', 2: 'Штаны', 3: 'Платье', 4: 'Обувь'
    }

    type_wear = category_map.get(category_id, '')
    items = db_sess.query(Item).filter(
        Item.type_wear == type_wear,
        Item.is_see == True
    ).all()

    category_name = {
        1: 'Футболки', 2: 'Штаны', 3: 'Платья', 4: 'Обувь'
    }.get(category_id, 'Категория')

    category_obj = {'id': category_id, 'name': category_name}

    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Штаны'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
    ]

    return render_template("category.html",
                           title=f'{category_name} - FashionStore',
                           products=items,
                           category=category_obj,
                           categories=categories,
                           current_user=current_user)


@app.route('/product/<int:product_id>')
def product(product_id):
    db_sess = db_session.create_session()
    product = db_sess.query(Item).filter(Item.id == product_id, Item.is_see == True).first()

    if not product:
        flash('Товар не найден', 'danger')
        return redirect(url_for('index'))

    similar_products = db_sess.query(Item).filter(
        Item.type_wear == product.type_wear,
        Item.id != product.id,
        Item.is_see == True
    ).limit(4).all()

    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Штаны'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
    ]

    return render_template("product.html",
                           title=f'{product.name} - FashionStore',
                           product=product,
                           similar_products=similar_products,
                           current_user=current_user,
                           categories=categories)


@app.route('/cart')
@login_required
def cart():
    db_sess = db_session.create_session()

    cart_items = db_sess.query(WantBuyItem).filter(WantBuyItem.id_user == current_user.id).all()

    total_price = sum(item.price for item in cart_items)
    total_quantity = len(cart_items)  

    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Штаны'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
    ]

    return render_template('cart.html',
                           cart_items=cart_items,
                           total_price=total_price,
                           total_quantity=total_quantity,
                           categories=categories)

@app.route('/profile')
@login_required
def profile():
    db_sess = db_session.create_session()

    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Штаны'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
    ]

    return render_template("profile.html",
                           title='Профиль - FashionStore',
                           current_user=current_user,
                           categories=categories)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if form.password.data != form.password_again.data:
            flash('Пароли не совпадают', 'danger')
            return render_template('register.html', title='Регистрация', form=form)

        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            flash('Пользователь с таким email уже существует', 'danger')
            return render_template('register.html', title='Регистрация', form=form)

        user = User(
            email=form.email.data
        )
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()

        flash('Регистрация прошла успешно! Теперь вы можете войти.', 'success')
        return redirect('/login')

    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()

        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            flash('Вы успешно вошли!', 'success')

            next_page = request.args.get('next')
            return redirect(next_page or '/')

        flash('Неверный email или пароль', 'danger')

    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect('/')


@app.route('/wantbuyitem/<int:id_item>')
@login_required
def want_buy_item(id_item):
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == id_item).first()

    if item and item.is_see and item.count > 0:
        want_buy_item1 = WantBuyItem(
            id_original_item=item.id,
            name=item.name,
            price=item.price - item.price_down,
            id_user=current_user.id
        )
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.count_want_buy_item += 1
        item.count -= 1
        db_sess.add(want_buy_item1)
        db_sess.commit()
        flash('Товар добавлен в корзину!', 'success')
    elif item.count == 0:
        flash('Товара нет в наличии', 'danger')

    return redirect(request.referrer or url_for('index'))


@app.route('/removewantitem/<int:id_item>')
@login_required
def remove_want_item(id_item):
    
    db_sess = db_session.create_session()
    want_buy_item = db_sess.query(WantBuyItem).filter(
        WantBuyItem.id_original_item == id_item,
        WantBuyItem.id_user == current_user.id
    ).first()
    

    if want_buy_item:
        db_sess.delete(want_buy_item)
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.count_want_buy_item -= 1
        item = db_sess.query(Item).filter(want_buy_item.id_original_item == Item.id).first()
        item.count += 1
        db_sess.commit()
        flash('Товар удален из корзины', 'info')

    return redirect(url_for('cart'))


@app.route('/removeitemfromstorage/<int:id_item>')
@login_required
def remove_item_from_storage(id_item):
    
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == id_item).first()
    
    if item:
        db_sess.delete(item)
        db_sess.commit()
        flash('Товар удален со склада', 'info')

    return redirect(url_for('storage'))


@app.route('/additemtostorage/<int:id_item>')
@login_required
def add_item_to_storage(id_item):
    
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == id_item).first()
    
    if item and current_user.is_admin:
        db_sess.delete(item)
        db_sess.commit()
        flash('Товар удален со склада', 'info')

    return redirect(url_for('storage'))


@app.route('/item_plus/<int:id_item>')
@login_required
def item_plus(id_item):
    
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == id_item).first()
    
    if item and current_user.is_admin:
        item.count += 1
        db_sess.commit()
        flash('Товар добавлен(+1)', 'info')

    return redirect(url_for('storage'))


@app.route('/item_minus/<int:id_item>')
@login_required
def item_minus(id_item):
    
    db_sess = db_session.create_session()
    item = db_sess.query(Item).filter(Item.id == id_item).first()
    
    if item and item.count != 0 and current_user.is_admin:
        item.count -= 1
        db_sess.commit()
        flash('Товар удален(-1)', 'info')

    return redirect(url_for('storage'))



@app.route('/buyitems')
@login_required
def buy_items():
    db_sess = db_session.create_session()
    want_buy_items = db_sess.query(WantBuyItem).filter(
        WantBuyItem.id_user == current_user.id
    ).all()
    for want_buy_item in want_buy_items:
        item_in_store = db_sess.query(Item).filter(
            Item.id == want_buy_item.id_original_item
            ).first()
        db_sess.delete(want_buy_item)
        item_in_store.count_buy += 1
        cur_user = db_sess.query(User).filter(User.id == current_user.id).first()
        cur_user.count_want_buy_item -= 1
        db_sess.commit()
    flash('Вы купили товары!', 'info') 

    return redirect(url_for('cart'))


@app.route("/storage")
@login_required
def storage():
    db_sess = db_session.create_session()
    if current_user.is_admin:
        items = db_sess.query(Item).all()

        categories = [
            {'id': 1, 'name': 'Футболки'},
            {'id': 2, 'name': 'Джинсы'},
            {'id': 3, 'name': 'Платья'},
            {'id': 4, 'name': 'Обувь'}
        ]

        return render_template("storage.html",
                            title='Склад',
                            products=items,
                            categories=categories,
                            current_user=current_user)
    else:
        return render_template("no_permission.html")


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePassword()
    categories = [
        {'id': 1, 'name': 'Футболки'},
        {'id': 2, 'name': 'Штаны'},
        {'id': 3, 'name': 'Платья'},
        {'id': 4, 'name': 'Обувь'}
        ]
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id == current_user.id).first()

        if user and user.check_password(form.current_password.data):
            if form.new_password.data == form.new_password_again.data:
                user.set_password(form.new_password.data)
                db_sess.commit()
                flash('Пароль успешно изменен!', 'success')
                return redirect(url_for('profile'))  
            else:
                flash('Новые пароли не совпадают', 'danger')
        else:
            flash('Неверный текущий пароль', 'danger')

    

    return render_template('change_password.html', title='Изменение пароля', form=form, categories=categories)


if __name__ == '__main__':
    app.register_blueprint(blueprint)
    app.run(debug=True, port=8080, host='127.0.0.1')