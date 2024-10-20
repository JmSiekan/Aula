from flask import Flask, jsonify, request, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from sqlalchemy import text

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:arkanito@localhost/TurnosAula'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Importar el modelo desde models.py
from models import db, Reserva

# Inicializar SQLAlchemy con la aplicación Flask
db.init_app(app)

# Ruta para renderizar el index.html
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/reservas', methods=['GET'])
def obtener_reservas():
    fecha_str = request.args.get('fecha')
    fecha_reservado = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # Obtener todas las reservas para la fecha seleccionada
    reservas_en_fecha = Reserva.query.filter_by(fecha_reservado=fecha_reservado).all()

    # Crear un conjunto de horas ocupadas
    horas_ocupadas = set()
    for reserva in reservas_en_fecha:
        hora_inicio = datetime.combine(fecha_reservado, datetime.strptime(reserva.hora, '%H:%M').time())
        for i in range(int(reserva.cantidad * 2)):  # Bloquear intervalos de 0.5 horas
            hora_ocupada = (hora_inicio + timedelta(minutes=30 * i)).strftime('%H:%M')
            horas_ocupadas.add(hora_ocupada)

    # Definir todas las horas posibles de 8:00 a 18:00
    todas_las_horas = []
    for i in range(8 * 2, 18 * 2):  # Cada incremento es de 0.5 horas
        hora_str = f'{i // 2:02}:{(i % 2) * 30:02}'
        todas_las_horas.append(hora_str)

    # Filtrar las horas disponibles
    horas_disponibles = [hora for hora in todas_las_horas if hora not in horas_ocupadas]

    # Devolver las horas disponibles como array de strings
    return jsonify(horas_disponibles)



@app.route('/reservas', methods=['GET'])
def obtener_horas_disponibles():
    fecha_str = request.args.get('fecha')
    fecha_reservado = datetime.strptime(fecha_str, '%Y-%m-%d').date()

    # Todas las posibles horas en incrementos de 0.5 horas
    todas_las_horas = ['{:02d}:00'.format(h) if h % 1 == 0 else '{:02d}:30'.format(int(h)) for h in
                       [i * 0.5 for i in range(16)]]

    # Filtrar reservas de la fecha seleccionada
    reservas_en_fecha = Reserva.query.filter_by(fecha_reservado=fecha_reservado).all()

    # Lista de horas ocupadas
    horas_ocupadas = set()

    for reserva in reservas_en_fecha:
        hora_inicio = datetime.combine(fecha_reservado, datetime.strptime(reserva.hora, '%H:%M').time())
        duracion = float(reserva.cantidad)
        for i in range(int(duracion * 2)):  # Multiplicar por 2 porque cada iteración es 0.5 horas
            hora_actual = (hora_inicio + timedelta(minutes=30 * i)).time().strftime('%H:%M')
            horas_ocupadas.add(hora_actual)

    # Calcular horas disponibles
    horas_disponibles = [hora for hora in todas_las_horas if hora not in horas_ocupadas]

    return jsonify(horas_disponibles)


@app.route('/todas_las_reservas', methods=['GET'])
def todas_las_reservas():
    sql = text("""
        SELECT fecha_reservado, hora, profesor
        FROM reserva
        ORDER BY fecha_reservado DESC, hora DESC
    """)
    result = db.session.execute(sql)

    # Formatear la fecha para que no incluya hora ni zona horaria
    reservas = [{'fecha_reservado': row[0].strftime('%d-%b-%Y'), 'hora': row[1], 'profesor': row[2]} for row in result]
    return jsonify(reservas)




@app.route('/reservar', methods=['POST'])
def realizar_reserva():
    data = request.get_json()

    # Fecha seleccionada por el profesor (fecha_reservado)
    fecha_reservado = datetime.strptime(data['fecha'], '%Y-%m-%d').date()

    # Fecha actual (cuando se realiza la reserva)
    fecha_actual = datetime.now().date()

    # Verificar si la fecha seleccionada es anterior a la fecha actual
    if fecha_reservado < fecha_actual:
        return jsonify({'status': 'error', 'message': 'No se pueden hacer reservas en días anteriores'}), 400

    # Hora seleccionada por el profesor
    hora_inicio = data['hora']
    duracion = float(data['duracion'])
    profesor = data['profesor']

    # Convertir hora de inicio a datetime
    hora_inicio_datetime = datetime.combine(fecha_reservado, datetime.strptime(hora_inicio, '%H:%M').time())

    # Calcular todas las horas afectadas por la reserva
    for i in range(int(duracion * 2)):  # 0.5 horas por cada iteración
        hora_actual = hora_inicio_datetime + timedelta(minutes=30 * i)
        hora_str = hora_actual.strftime('%H:%M')

        # Verificar si el bloque de tiempo está disponible
        reservas_en_fecha = Reserva.query.filter_by(fecha_reservado=fecha_reservado, hora=hora_str).all()

        if reservas_en_fecha:
            return jsonify({'status': 'error', 'message': f'Conflicto de horario: el intervalo {hora_str} ya está reservado'}), 400

    # Si no hay conflicto, proceder con la creación de las reservas
    for i in range(int(duracion * 2)):
        hora_actual = hora_inicio_datetime + timedelta(minutes=30 * i)
        hora_str = hora_actual.strftime('%H:%M')

        nueva_reserva = Reserva(
            fecha=fecha_actual,  # Guardar la fecha actual cuando se realiza la reserva
            fecha_reservado=fecha_reservado,  # Guardar la fecha seleccionada por el profesor
            hora=hora_str,  # Guardar la hora específica del bloque de 0.5 horas
            reservado=True,
            profesor=profesor,
            cantidad=0.5  # Guardar cada bloque como 0.5 horas
        )

        db.session.add(nueva_reserva)

    db.session.commit()

    return jsonify({'status': 'success'})




if __name__ == '__main__':
    app.run(debug=True)
