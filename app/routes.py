import os
import random

from flask import Blueprint, request, current_app
from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from flask_login import login_required
from werkzeug.utils import secure_filename

from .models import Art
from .transactions import *

main = Blueprint('main', __name__)
root_path = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(root_path, 'static/uploads/arts')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@main.route('/')
def index():
    return render_template('index.html')


@main.route('/')
@main.route('/home')
def home():
    economy = get_economy()
    user_id = current_user.id
    balance = round(db.session.query(User).get(user_id).balance, 2)
    token_price = round(economy.get_token_price(), 4)
    available_tokens = economy.get_max_supply() - economy.get_total_supply()
    arts = Art.query.all()
    return render_template('home.html', arts=arts, balance=balance, token_price=token_price,
                           available_tokens=available_tokens)


art_attributes = {
    'backgrounds': ['Sds', 'Off.png', 'Sds.png'],
    'bodies': ['Sds.png', 'Off.png', 'Sds.png'],
    'eyes': ['Sds.png', 'Off.png', 'Sds.png'],
    'accessories': ['Sds.png', 'Off.png', 'Sds.png']
}


@main.route('/create_art', methods=['GET', 'POST'])
@login_required
def create_art():
    background = random.choice(art_attributes['backgrounds'])
    body = random.choice(art_attributes['bodies'])
    eyes = random.choice(art_attributes['eyes'])
    accessory = random.choice(art_attributes['accessories'])
    art_metadata = f'{background}, {body}, {eyes}, {accessory}'

    if request.method == 'POST':
        background = request.form.get('background')
        body = request.form.get('body')
        eyes = request.form.get('eyes')
        accessory = request.form.get('accessory')
        art_metadata = f'{background}, {body}, {eyes}, {accessory}'

        new_art = Art(
            owner_id=current_user.id,
            image_path=f'{background}_{body}_{eyes}_{accessory}.png',
            art_metadata=art_metadata,
            status='available',
            price=10,
            views=0
        )
        new_art.owner_id = current_user.id
        db.session.add(new_art)
        db.session.commit()
        flash('Your artwork has been saved!', 'success')
        return redirect(url_for('main.home'))

    return render_template('create_art.html', attributes=art_attributes, art_metadata=art_metadata)


@main.route('/buy_art/<int:art_id>', methods=['POST'])
@login_required
def buy_art(art_id):
    art = Art.query.get_or_404(art_id)
    if art.status == 'sold':
        flash('Этот арт уже продан.', 'danger')
        return redirect(url_for('main.marketplace'))

    if current_user.balance < art.price:
        flash('Недостаточно валюты для покупки.', 'danger')
        return redirect(url_for('main.marketplace'))

    current_user.balance -= art.price
    art.status = 'sold'

    art.views += 1
    art_purchase(buyer_id=current_user.id, seller_id=art.owner_id, amount=art.price, art_id=art.id)

    flash('Вы успешно приобрели арт!', 'success')
    return redirect(url_for('main.marketplace'))


# (система кейсов)

@main.route('/buy_case', methods=['GET', 'POST'])
@login_required
def buy_case():
    if current_user.balance < 20:
        flash('Not enough currency to buy a case.', 'danger')
        return redirect(url_for('main.home'))

    case_items = random.choices(
        art_attributes['backgrounds'] + art_attributes['bodies'] + art_attributes['eyes'] + art_attributes[
            'accessories'], k=3)

    current_user.balance -= 20
    db.session.commit()

    flash(f'You have received: {", ".join(case_items)}', 'success')
    return redirect(url_for('main.home'))


@main.route('/art/<int:art_id>')
def view_art(art_id):
    art = Art.query.get_or_404(art_id)
    art.views += 1
    db.session.commit()
    return render_template('art_detail.html', art=art)


@main.route('/edit_art/<int:art_id>', methods=['GET', 'POST'])
@login_required
def edit_art(art_id):
    art = Art.query.get_or_404(art_id)

    if request.method == 'POST':
        art.art_metadata = request.form['metadata']
        art.description = request.form['description']
        art.price = int(request.form['price'])

        file = request.files.get('image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            art.image_path = f'uploads/arts/{filename}'

        db.session.commit()
        flash('Арт успешно обновлён', 'success')
        return redirect(url_for('main.marketplace'))

    return render_template('edit_art.html', art=art)

@main.route('/marketplace')
def marketplace():
    sort_by = request.args.get('sort', 'new')
    query = Art.query.filter_by(status='available')

    if sort_by == 'price':
        arts = query.order_by(Art.price.asc()).all()
    elif sort_by == 'popular':
        arts = query.order_by(Art.views.desc()).all()
    else:
        arts = query.order_by(Art.created_at.desc()).all()

    return render_template('marketplace.html', arts=arts)


@main.route('/give_tokens', methods=['POST'])
@login_required
def give_tokens():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.home'))

    user_id = request.form.get('user_id')
    amount = int(request.form.get('amount'))

    user = User.query.get(user_id)
    if not user:
        flash("Пользователь не найден", 'danger')
        return redirect(url_for('main.admin_panel'))

    user.balance += amount
    db.session.commit()

    flash(f"Пользователю {user.username} выдано {amount} токенов", 'success')
    return redirect(url_for('main.admin_panel'))


@main.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    economy = get_economy()
    if current_user.role != 'admin':
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        emission_amount = int(request.form['emission_amount'])
        if economy.can_mint(emission_amount):
            economy.mint(emission_amount)
            flash(f"Выпущено {emission_amount} токенов", category='success')
            return redirect(url_for('main.admin_panel'))
        else:
            flash(f"Превышен лимит эмиссии", category='danger')
            return redirect(url_for('main.admin_panel'))

    token_price = round(economy.get_token_price(), 4)
    users = User.query.all()
    arts = Art.query.all()
    return render_template('admin_panel.html', users=users, arts=arts, token_price=token_price)


@main.route('/burn_emission', methods=['POST'])
@login_required
def burn_emission():
    burn_amount = float(request.form['burn_amount'])
    user_id = current_user.id
    balance = db.session.query(User).get(user_id).balance
    if balance >= burn_amount:
        burn_tokens(current_user.id, burn_amount)
        flash(f"{burn_amount} RYT было сожжено", category='success')
    else:
        flash(f"Недостаточно RYT для сжигания", category='danger')
    return redirect(url_for('main.home'))

from app.forms import AvatarUploadForm

@main.route('/profile')
@login_required
def profile():
    from flask_login import current_user
    user_arts = Art.query.filter_by(owner_id=current_user.id).all()
    form = AvatarUploadForm()
    return render_template('profile.html', user=current_user, user_arts=user_arts, avatar_form=form)

@main.route('/admin/mint_emission', methods=['POST'])
@login_required
def mint_emission():
    mint_amount = float(request.form['mint_amount'])
    mint_tokens(current_user.id, mint_amount)
    flash(f"{mint_amount} RYT было успешно выпущено", category='success')
    return redirect(url_for('main.admin_panel'))

@main.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    file = request.files.get('avatar')

    if file:
        filename = file.filename
        upload_folder = current_app.config['UPLOAD_FOLDER']

        avatar_dir = os.path.join(upload_folder, 'avatars')
        os.makedirs(avatar_dir, exist_ok=True)

        filepath = os.path.join(avatar_dir, filename)
        file.save(filepath)

        current_user.avatar = f'uploads/avatars/{filename}'
        db.session.commit()

        return redirect(url_for('main.profile'))

    return "No file uploaded", 400

@main.route('/buy_token', methods=['POST'])
@login_required
def buy_token():
    token_amount = float(request.form['token_amount'])
    purchase(current_user.id, token_amount)
    flash(f"{token_amount} RYT было успешно куплено", category='success')
    return redirect(url_for('main.home'))


@main.route('/sell_token', methods=['POST'])
@login_required
def sell_token():
    token_amount = float(request.form['token_amount'])
    user_id = current_user.id
    balance = db.session.query(User).get(user_id).balance
    if balance >= token_amount:
        sell(current_user.id, token_amount)
        flash(f"{token_amount} RYT было успешно продано", category='success')
    else:
        flash(f"Недостаточно RYT для продажи", category='danger')
    return redirect(url_for('main.home'))


@main.route('/RYT', methods=['GET'])
@main.route('/token_stats', methods=['GET'])
@login_required
def token_stats():
    user_id = current_user.id
    economy = get_economy()
    balance = db.session.query(User).get(user_id).balance
    token_price = round(economy.get_token_price(), 4)
    total_supply = economy.get_total_supply()
    circulating_supply = economy.get_circulating_supply()
    max_supply = economy.get_max_supply()
    burned_supply = economy.get_burned_supply()
    market_cap = economy.get_market_cap()
    return render_template('token_stats.html', balance=balance, token_price=token_price,
                           total_supply=total_supply,  circulating_supply=circulating_supply, max_supply=max_supply,
                           burned_supply=burned_supply, market_cap=market_cap)
