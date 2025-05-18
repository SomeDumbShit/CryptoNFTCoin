import os
import random
from io import BytesIO

from flask import Blueprint, request, current_app, send_file
from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from flask_login import login_required
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.utils import secure_filename

from .art_generator import combine_layers
from .models import Quest, UserQuest
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
    balance_usd = round(token_price * balance, 2)
    arts = Art.query.all()
    return render_template('home.html', arts=arts, balance=balance, token_price=token_price,
                           balance_usd=balance_usd)


art_attributes = {
    'background': ['green', 'purple', 'bamboo'],
    'body': ['panda'],
    'eyes': ['angry_eyes', 'star_eyes'],
    'ears': ['black_ears'],
    'mouth': ['cigar', 'joyful', 'singing'],
    'clothes': ['none', 'blaze'],
    'hats': ['none', 'clown_hat', 'cylinder', 'king', 'purple_hat', 'red_hat'],
    'accessory': ['none', 'ring']
}


@main.route('/create_art', methods=['GET', 'POST'])
@login_required
def create_art():
    selected = {
        'background': request.form.get('background', 'green'),
        'body': request.form.get('body', 'panda'),
        'eyes': request.form.get('eyes', 'angry_eyes'),
        'ears': request.form.get('ears', 'black_ears'),
        'mouth': request.form.get('mouth', 'joyful'),
        'clothes': request.form.get('clothes', 'none'),
        'hats': request.form.get('hats', 'none'),
        'accessory': request.form.get('accessory', 'none')
    }

    user = db.session.query(User).get(current_user.id)
    attributes = user.attributes or {}
    default_attributes = ['green', 'panda', 'angry_eyes', 'black_ears', 'joyful', 'blaze', 'none']

    preview_url = url_for('main.preview_image', **selected)

    if request.method == 'POST' and request.form.get('action') == 'save':
        art_price = request.form.get('price')
        art_metadata = request.form.get('Name_of_the_art')

        if not art_price or not art_metadata:
            flash('Заполните все поля', 'danger')
        else:
            for attr_type, attr_value in selected.items():
                if attr_value not in default_attributes:
                    if attr_type in attributes and attr_value in attributes[attr_type]:
                        attributes[attr_type].remove(attr_value)
            user.attributes = attributes
            flag_modified(user, "attributes")
            db.session.commit()


            paths = [
                f'app/static/attributes/background/{selected["background"]}.png',
                f'app/static/attributes/body/{selected["body"]}.png',
                f'app/static/attributes/eyes/{selected["eyes"]}.png',
                f'app/static/attributes/ears/{selected["ears"]}.png',
                f'app/static/attributes/clothes/{selected["clothes"]}.png',
                f'app/static/attributes/mouth/{selected["mouth"]}.png',
                f'app/static/attributes/hats/{selected["hats"]}.png',
                f'app/static/attributes/accessories/{selected["accessory"]}.png'
            ]

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            filename = f"{'_'.join(selected.values())}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            img = combine_layers(paths)
            img.save(filepath)

            new_art = Art(
                owner_id=current_user.id,
                artist_id=current_user.id,
                image_path=f'uploads/arts/{filename}',
                art_metadata=art_metadata,
                status='awaiting moderation',
                moderation_status='pending',
                price=art_price,
                views=0
            )
            db.session.add(new_art)

            quest = Quest.query.filter_by(description="Create your first NFT").first()
            if not quest:
                quest = Quest(description="Create your first NFT", reward=50, condition="create_art")
                db.session.add(quest)
                db.session.commit()

            user_quest = UserQuest.query.filter_by(user_id=current_user.id, quest_id=quest.id).first()
            if not user_quest:
                reward_user(current_user.id, quest.reward)
                db.session.add(UserQuest(user_id=current_user.id, quest_id=quest.id, status='completed'))
                flash(f'🎉 Quest completed! You earned {quest.reward} RYT!', 'success')

            db.session.commit()
            flash('Your artwork has been saved!', 'success')
            return redirect(url_for('main.home'))

    for attr_type in attributes:
        attributes[attr_type] = list(dict.fromkeys(attributes[attr_type]))

    return render_template('create_art.html',
                           attributes=attributes,
                           selected=selected,
                           preview_url=preview_url)



@main.route('/challenge')
@login_required
def challenge():
    quest = Quest.query.filter_by(description="Create your first NFT").first()

    # Проверяем, выполнил ли пользователь квест
    quest_completed = False
    if quest:
        quest_completed = UserQuest.query.filter_by(
            user_id=current_user.id,
            quest_id=quest.id,
            status='completed'
        ).first() is not None

    return render_template(
        'quests.html',
        quest_completed=quest_completed,
        quest_reward=quest.reward if quest else 50
    )


@main.route('/preview')
def preview_image():
    background = request.args.get('background', 'green')
    body = request.args.get('body', 'panda')
    eyes = request.args.get('eyes', 'angry_eyes')
    accessory = request.args.get('accessory', 'none')
    ears = request.args.get('ears', 'black_ears')
    mouth = request.args.get('mouth', 'joyful')
    clothes = request.args.get('clothes', 'none')
    hats = request.args.get('hats', 'none')

    paths = [
        f'app/static/attributes/background/{background}.png',
        f'app/static/attributes/body/{body}.png',
        f'app/static/attributes/eyes/{eyes}.png',
        f'app/static/attributes/ears/{ears}.png',
        f'app/static/attributes/clothes/{clothes}.png',
        f'app/static/attributes/mouth/{mouth}.png',
        f'app/static/attributes/hats/{hats}.png',
        f'app/static/attributes/accessories/{accessory}.png'
    ]

    img = combine_layers(paths)
    img_io = BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')



@main.route('/buy/<int:art_id>', methods=['POST'])
@login_required
def buy_art(art_id):
    art = Art.query.get_or_404(art_id)

    if current_user.balance < art.price:
        flash("Недостаточно средств", "danger")
        return redirect(url_for('main.marketplace'))

    art.status = 'sold'
    art.views += 1
    art_purchase(buyer_id=current_user.id, seller_id=art.owner_id, amount=art.price, art_id=art.id)
    buyer = current_user
    seller = art.owner
    artist = art.artist
    
    price = art.price
    fee_artist = int(price * 0.1)//1
    seller_income = price - fee_artist
    
    buyer.balance -= price
    seller.balance += seller_income
    
    if artist and artist.id != seller.id:
        artist.balance += fee_artist
    
    art.owner = buyer
    art.status = 'sold'
    
    tx = Transaction(
        sender_id=buyer.id,
        recipient_id=seller.id,
        amount=price,
        transaction_fee=fee_artist,
        art_id=art.id,
        transaction_type="purchase"
        )

    db.session.add(tx)
    db.session.commit()

    flash("Покупка завершена", "success")
    return redirect(url_for('main.marketplace'))



# (система кейсов)

@main.route('/buy_case', methods=['GET', 'POST'])
@login_required
def buy_case():
    if request.method == 'POST':
        if current_user.balance < 20:
            flash('Недостаточно средств для покупки кейса.', 'danger')
            return redirect(url_for('main.buy_case'))

        case_items = random.choices(sum(list(art_attributes.values()), []), k=3)
        buy_case_tx(current_user.id, 20, ', '.join(case_items))

        user = db.session.query(User).get(current_user.id)
        attributes = user.attributes
        db.session.commit()
        default_attributes = ['green', 'panda', 'angry_eyes', 'black_ears', 'joyful', 'blaze', 'none']
        for attribute in case_items:
            for attribute_type in attributes.keys():
                if attribute not in default_attributes and attribute in art_attributes[attribute_type]:
                    attributes[attribute_type].append(attribute)
        user.attributes = attributes
        db.session.commit()
        flash(f'Вы получили: {", ".join(case_items)}', 'success')
        return redirect(url_for('main.buy_case'))

    return render_template('buy_case.html')



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
    elif sort_by == 'rarity':
        rarity_order = {'legendary': 0, 'rare': 1, 'common': 2}
        arts = sorted(query.all(), key=lambda a: rarity_order.get(a.rarity, 3))
    else:
        arts = query.order_by(Art.created_at.desc()).all()

    return render_template('marketplace.html', arts=arts)


@main.route("/admin/moderation", methods=["GET", "POST"])
@login_required
def moderate_arts():
    if current_user.role != "admin":
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('main.home'))

    if request.method == "POST":
        id = request.form.get("id")
        action = request.form.get("action")
        rarity = request.form.get("rarity")

        art = Art.query.get(id)
        if not art:
            flash("Артефакт не найден.", "danger")
            return redirect(url_for("main.moderate_arts"))

        if action == "approve":
            art.moderation_status = "approved"
            art.rarity = rarity
            art.status = 'available'
        elif action == "reject":
            art.status = 'rejected'
            art.moderation_status = "rejected"
        db.session.commit()
        flash("Статус обновлён", "success")
        return redirect(url_for("main.moderate_arts"))

    pending_arts = Art.query.filter_by(moderation_status="pending").all()
    return render_template("moderate.html", arts=pending_arts)



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

    reward_user(user_id=user.id, amount=amount)
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
