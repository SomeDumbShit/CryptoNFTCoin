from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from .extensions import db
from .models import User, Art, Transaction
from .economy import get_economy
import random

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/')
@main.route('/home')
def home():
    arts = Art.query.all()
    return render_template('home.html', arts=arts)


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

    transaction = Transaction(
        sender_id=current_user.id,
        recipient_id=art.owner_id,
        amount=art.price,
        art_id=art.id,
        transaction_type='purchase'
    )
    art.views += 1
    db.session.add(transaction)
    db.session.commit()

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

    token_price = economy.get_token_price()
    users = User.query.all()
    arts = Art.query.all()
    return render_template('admin_panel.html', users=users, arts=arts, token_price=token_price)


@main.route('/admin/burn_emission', methods=['POST'])
@login_required
def burn_emission():
    economy = get_economy()
    burn_amount = int(request.form['burn_amount'])
    economy.burn(burn_amount)
    flash(f"{burn_amount} токенов было сожжено", category='success')
    return redirect(url_for('main.admin_panel'))


@main.route('/admin/mint_emission', methods=['POST'])
@login_required
def mint_emission():
    economy = get_economy()
    burn_amount = int(request.form['burn_amount'])
    economy.burn(burn_amount)
    flash(f"{burn_amount} токенов было сожжено", category='success')
    return redirect(url_for('main.admin_panel'))


@main.route('/admin/buy_token', methods=['POST'])
@login_required
def buy_token():
    economy = get_economy()
    burn_amount = int(request.form['burn_amount'])
    economy.burn(burn_amount)
    flash(f"{burn_amount} токенов было сожжено", category='success')
    return redirect(url_for('main.admin_panel'))
