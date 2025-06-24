# models.py
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# Ein einziges db-Objekt für alle Models
db = SQLAlchemy()

class Offer(db.Model):
    __tablename__ = 'offers'

    offer_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.Text, nullable=False)
    category = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    region = db.Column(db.Text, nullable=False)
    price_per_night = db.Column(db.Float, nullable=False, default=0.0)
    rating = db.Column(db.Float, nullable=False, default=0.0)
    photo = db.Column(db.Text, nullable=True)  # z. B. Dateipfad "uploads/abc.jpg"
    features = db.Column(db.Text, nullable=True)  # JSON-String mit den dynamischen Merkmalen
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Beziehung zu Rentals
    rentals = db.relationship(
        'Rental',
        back_populates='offer',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return (
            f"<Offer id={self.offer_id} title={self.title!r} category={self.category!r} "
            f"region={self.region!r} price_per_night={self.price_per_night} rating={self.rating} "
            f"photo={self.photo!r} created_at={self.created_at}>"
        )

class Rental(db.Model):
    __tablename__ = 'rentals'

    rental_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    offer_id = db.Column(db.Integer, db.ForeignKey('offers.offer_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Beziehung zurück zum Offer
    offer = db.relationship('Offer', back_populates='rentals')
    # Beziehung zu User
    user = db.relationship('User')

    def __repr__(self):
        return (
            f"<Rental id={self.rental_id} offer_id={self.offer_id} user_id={self.user_id} "
            f"start_date={self.start_date} end_date={self.end_date} total_price={self.total_price}>"
        )
