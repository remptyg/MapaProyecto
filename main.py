from flask import Flask, render_template, request
from dotenv import load_dotenv
import os
import openrouteservice
import json
from geopy.distance import geodesic

# Cargar las variables de entorno desde el archivo .env
# Esto con el fin de no exponer la API y resguardar el codigo en GitHub
load_dotenv()
API_KEY = os.getenv('API_KEY')
client = openrouteservice.Client(API_KEY)

app = Flask(__name__)

# Funcion de openrouteservice para obtener las coordenadas de un lugar
def obtener_coordenadas(nombre_lugar):
    resultado = client.pelias_search(text=nombre_lugar)
    if resultado and resultado['features']:
        return resultado['features'][0]['geometry']['coordinates']
    return None

# Llamado de la funcion route
@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

# Obtencion de la ruta mediante el webrequest POST
@app.route('/ruta', methods=['POST'])
def procesar_ruta():
    origen = request.form['origen']
    destino = request.form['destino']

    coord_origen = obtener_coordenadas(origen)
    coord_destino = obtener_coordenadas(destino)

    if not coord_origen or not coord_destino:
        return render_template('index.html', error="No se encontraron coordenadas para el origen o destino.")
    
    # Comprobacion de distancia limite de la API
    distancia = geodesic((coord_origen[1], coord_origen[0]), (coord_destino[1], coord_destino[0])).meters
    if distancia > 6000000:
        return render_template('index.html', error="La ruta es demasiado larga para calcularse (Maximo 6000).")
    
    # Llamada a la API de OpenRouteService para obtener la ruta en formato GeoJSON
    ruta = client.directions(
        coordinates=[coord_origen, coord_destino],
        profile='driving-car',
        format='geojson'
    )
    segment = ruta['features'][0]['properties']['segments'][0]
    distancia = segment['distance']  # metros
    duracion = segment['duration']  # segundos

    # Calcular el centro del mapa que deberia mostrarse en la ruta usando coordenadas
    lat_centro = (coord_origen[1] + coord_destino[1]) / 2
    lon_centro = (coord_origen[0] + coord_destino[0]) / 2

    # URL ruta de las coordenadas de openrouteservice
    ruta_url = f"https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&route={coord_origen[1]}%2C{coord_origen[0]}%3B{coord_destino[1]}%2C{coord_destino[0]}"

    # Regresamos la ruta (GEOJson) y las coordenadas del centro
    return render_template(
        'index.html',
        ruta_geojson=json.dumps(ruta),
        lat_centro=lat_centro,
        lon_centro=lon_centro,
        origen=origen,
        destino=destino,
        distancia=distancia,
        duracion=duracion,
        ruta_url=ruta_url)

if __name__ == '__main__':
    app.run(debug=True)
