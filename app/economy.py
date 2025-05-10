from .extensions import db
from .models import Economy


def get_economy():
    return WrappedEconomy()


class WrappedEconomy(Economy):
    def __init__(self):
        if db.session.query(Economy).count() == 0:
            db.session.add(Economy())
            db.session.commit()
        self.economy = db.session.query(Economy).first()
        self.update_price()

    def update_price(self):
        base_price = self.economy.base_price
        circulating_supply = self.economy.circulating_supply
        growth_factor = self.economy.growth_factor
        max_supply = self.economy.max_supply

        price = base_price + (circulating_supply / max_supply) * growth_factor
        self.economy.market_cap = price * circulating_supply
        self.economy.price = price
        db.session.commit()

    def get_token_price(self):
        return self.economy.price

    def get_market_cap(self):
        return self.economy.market_cap

    def get_max_supply(self):
        return self.economy.max_supply

    def get_total_supply(self):
        return self.economy.total_supply

    def get_circulating_supply(self):
        return self.economy.circulating_supply

    def get_burned_supply(self):
        return self.economy.burned

    def mint(self, amount):
        self.economy.max_supply += amount
        db.session.commit()
        self.update_price()

    def buy(self, amount):
        self.economy.total_supply += amount
        self.economy.circulating_supply = self.economy.total_supply - self.economy.burned
        db.session.commit()
        self.update_price()

    def sell(self, amount):
        self.economy.total_supply -= amount
        self.economy.circulating_supply = self.economy.total_supply - self.economy.burned
        db.session.commit()
        self.update_price()

    def burn(self, amount):
        self.economy.circulating_supply -= amount
        self.economy.burned += amount
        db.session.commit()
        self.update_price()
