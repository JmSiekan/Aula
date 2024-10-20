from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Modelo de la base de datos
class Reserva(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date)  # Fecha en la que se realiza la reserva
    fecha_reservado = db.Column(db.Date)  # Fecha para la cual se hace la reserva
    hora = db.Column(db.String(5))
    profesor = db.Column(db.String(100))
    reservado = db.Column(db.Boolean)
    cantidad = db.Column(db.Float)

