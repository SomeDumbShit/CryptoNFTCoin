from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from .extensions import db
from .models import User, Art, Transaction
import random

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/')
@main.route('/home')
def home():
    arts = Art.query.all()  # Получаем все арты
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

    if request.method == 'POST':
        background = request.form.get('background')
        body = request.form.get('body')
        eyes = request.form.get('eyes')
        accessory = request.form.get('accessory')

        new_art = Art(owner_id=current_user.id,
                      image_path=f'{background}_{body}_{eyes}_{accessory}.png',
                      metadata=f'{background}, {body}, {eyes}, {accessory}')
        db.session.add(new_art)
        db.session.commit()
        flash('Your artwork has been saved!', 'success')
        return redirect(url_for('main.home'))

    return render_template('create_art.html', attributes=art_attributes)


@main.route('/buy_art/<int:art_id>', methods=['GET', 'POST'])
@login_required
def buy_art(art_id):
    art = Art.query.get_or_404(art_id)
    if art.status == 'sold':
        flash('This artwork has already been sold.', 'danger')
        return redirect(url_for('main.home'))

    if current_user.balance < 10:
        flash('Not enough currency to purchase this artwork.', 'danger')
        return redirect(url_for('main.home'))

    current_user.balance -= 10  # Стоимость арта
    art.status = 'sold'

    transaction = Transaction(sender_id=current_user.id, recipient_id=art.owner_id,
                              amount=10, art_id=art.id, transaction_type='purchase')
    db.session.add(transaction)
    db.session.commit()

    flash('You have successfully purchased the artwork!', 'success')
    return redirect(url_for('main.home'))


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


@main.route('/admin', methods=['GET'])
@login_required
def admin_panel():
    if current_user.role != 'admin':
        flash('You do not have access to this page.', 'danger')
        return redirect(url_for('main.home'))

    users = User.query.all()
    arts = Art.query.all()
    return render_template('admin_panel.html', users=users, arts=arts)
