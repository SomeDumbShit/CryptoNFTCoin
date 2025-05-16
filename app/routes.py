import random
from flask import Blueprint, request, current_app, send_file
import os
from app.extensions import db
from .art_generator import combine_layers
from io import BytesIO
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
    balance_usd = round(token_price * balance, 2)
    arts = Art.query.all()
    return render_template('home.html', arts=arts, balance=balance, token_price=token_price,
                           available_tokens=available_tokens, balance_usd=balance_usd)


art_attributes = {
    'backgrounds': ['green', 'purple', 'bamboo'],
    'bodies': ['panda'],
    'eyes': ['angry_eyes', 'star_eyes'],
    'ears': ['black_ears'],
    'mouth': ['cigar', 'joyful', 'singing'],
    'clothes': ['blaze'],
    'hats': ['clown_hat', 'cylinder', 'king', 'purple_hat', 'red_hat'],
    'accessories': ['ring']
}


@main.route('/create_art', methods=['GET', 'POST'])
@login_required
def create_art():
    selected = {
        'background': request.args.get('background', 'green'),
        'body': request.args.get('body', 'panda'),
        'eyes': request.args.get('eyes', 'angry_eyes'),
        'ears': request.args.get('ears', 'black_ears'),
        'mouth': request.args.get('mouth', 'joyful'),
        'clothes': request.args.get('clothes', 'blaze'),
        'hats': request.args.get('hats', 'none'),
        'accessory': request.args.get('accessory', 'none')
    }

    preview_url = None
    if request.args.get('action') == 'preview':
        preview_url = url_for('main.preview_image',
                              background=selected['background'],
                              body=selected['body'],
                              eyes=selected['eyes'],
                              accessory=selected['accessory'],
                              ears=selected['ears'],
                              mouth=selected['mouth'],
                              clothes=selected['clothes'],
                              hats=selected['hats']
                              )
    '''if request.method == 'POST':
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
        return redirect(url_for('main.home'))'''

    return render_template('create_art.html', attributes=art_attributes, selected=selected, preview_url=preview_url)


@main.route('/preview')
def preview_image():
    background = request.args.get('background', 'green')
    body = request.args.get('body', 'panda')
    eyes = request.args.get('eyes', 'angry_eyes')
    accessory = request.args.get('accessory', 'none')
    ears = request.args.get('ears', 'black_ears')
    mouth = request.args.get('mouth', 'joyful')
    clothes = request.args.get('clothes', 'blaze')
    hats = request.args.get('hats', 'none')

    paths = [
        f'static/attributes/background/{background}.png',
        f'static/attributes/body/{body}.png',
        f'static/attributes/eyes/{eyes}.png',
        f'static/attributes/accessory/{accessory}.png',
        f'static/attributes/clothes/{clothes}.png',
        f'static/attributes/hats/{hats}.png',
        f'static/attributes/mouth/{mouth}.png',
        f'static/attributes/ears/{ears}.png'
    ]

    img = combine_layers(paths)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')


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

        # Сохраняем путь относительно /static
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
                           total_supply=total_supply, circulating_supply=circulating_supply, max_supply=max_supply,
                           burned_supply=burned_supply, market_cap=market_cap)
