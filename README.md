# SISTEMA DE RESERVAS LOUD

# DEFENSA DE EXAMEN

BILLETE A3 DEL EXAMEN

## QUE HICE Y COMO

CAMBIE LAS CONSULTAS, LOS SERVICIOS, MODELOS Y DTO PARA MOSTRAR TODO CORRECTAMENTE.
LO HICE EN LOS ENDPOINTS DE /events Y DE /events/{id}. REALICE CORRECTAMETNE EL PRIMER PUNTO DE OBTENER CURRENT_PRICE, Y TAMBIEN EL SEGUNDO PUNTO PARA OBTENER CURRENT_TIER_ID.

MODIFIQUE SOBRE TODO EL ARCHIVO POSTGRES EN LA FUNCION fetch_events_page Y DEL ARHIVO SERVICIOS Y MODELOS UN POCO PARA QUE HAYA COHERENCIA CON EL MAPEO Y LA RESPUESTA EN LOS MODELOS TIPO DTO, AHI APROVECHE MI LOGICA DE BUSINESS LOGIC QUE TENIA ANTERIORMENTE PARA PONER EL current_price DE MANERA MAS FACIL PORQUE YA HABIA HECHO ESA LOGICA DE NEGOCIO ANTEIERORMENTE (CASI IGUAL). ADEMAS IMPLEMENTE LO DEL EARLY BIRD BEATS GENERAL EN LA MISMA CONSULTA SQL CON LA FUNCION DE AGREGACION MIN.

PARA EL current_tier_id LO QUE HICE FUE APROVECHARME NUEVAMENTE DE LA CONSULTA DE fetch_events_page POR LO QUE AREGUE UNA SUBCONSULTA EXTRA PARA OBTENER EL ID CORRECTAMETNE CON LIMIT 1, Y ORDER BY ASC PORQUE ERA LA MANERA MAS OPTIMIZADA PARA SOLUCIONAR EL PROBLEMA SIN GRAN COMPLEJIDAD.

POR ULTIMO TENIA QUE IMPLEMENTAR EL price-history. QUISE APROVECHARME DE LA CONSULTA QUE TENIA ANTEIRORMENTE DE fetch_event_tiers PARA OBTENER EL TIER Y SUS PRECIOS. PENSE EN HACER UN FOR A ESA CONSULTA (AUNQUE NO ES LO MAS OPTIMO EN RENDIMIENTO) PARA OBTENER LOS PRECIOS BASADO EN EL HORARIO QUE DEFINI. QUE USE EL NOW() Y SUMANDOLE 2 HORAS PARA OBTENER CADA VEZ LA NUEVA RESPUESTA Y ALMACENARLA EN UNA LISTA DE MI MODELO QUE IGUALMENTE CREES PARA PODER SATISFACER EL MAPEO. TAMBIEN CREE UN DTO PARA LA SALIDA API.

## PORQUE LO HICE

LA PRIMERA PARTE DE current-price LO HICE DE ESE MODO DEBIDO A QUE ERA LA MANERA MAS LIMPIA SIGUIENDO PRINCIPIOS DRY (DONT REPEAT YOURSELF) SIN CREAR NUEVAS CONSULTAS YA QUE PODRIA USAR LA MISMA SOLO CON UNAS PEQUENAS MODIFICACIONES. 

LA SEGUNDA PARTE DEL current_tier_id LO REALICE DE ESE MODO DEBIDO A QUE IGUALMETNE ERA LA MANERA MAS OPTIMA, SIGUIENDO PRINCIPIOS DRY, CON POCO CODIGO, ENTENDIBLE Y MANTENIBLE PARA OTROS PROGRAMADORES. PERO SOBRE TODO PORQUE ERA LO MAS RAPIDO

LA TERCERA PARTE FUE EL price-history IMPLEMENTE UNA ESTRUCTURA DE API + SERVICIO + MODELOS + DTO. PERO CREE OTRO SERVICIO Y API PORQUE NO PODIA REUTILIZAR NADA EN EL CODIGO DE ESTE ASPECTO. LO UNICO QUE SI REUTILICE FUE LA CONSULTA PARA LOS tickettypes PORQUE ERA LO MAS OPTIMO, VELOZ, EFICIENTE Y SIGUIENDO PRINCIPIOS DRY. LO HICE DE ESTE MODO PORQUE NECESITABA MOSTRAR EL PRECIO DE CADA 2 HORAS EN LA PANTALLA 18:00 -> 20:00 --> 22:00 Y ASI SUCESIVAMENTE,

## QUE ME FALTO Y COMO LO HUBERA HECHO

 ME FALTO LA PARTE DEL ENDPOINT price-history. TENGO LA ESTRUCTURA PERO TENGO ERRORES DE COMPILACION.

pydantic_core._pydantic_core.ValidationError: 1 validation error for PriceHistoryOut
diccionario (ESTO EN MIS LOGS DE DOCKER)

SIN EMBARGO LO QUE HUBIERA HECHO SERIA PENSAR EN UNA MANEAR MAS OPTIMA Y LIMPIA PARA MANDAR MIS DATOS REQUERIDOS DE LA BASE DE DATOS AL FROTNEND SIN NECESITAR REUTILIZAR UNA FUNCION QUE NO DEBERIA REPETIRSE SU LOGICA.

# DOCUMENTACION

Este documento explica de forma simple el funcionamiento del sistema de reservas LOUD, como ponerlo en marcha, como correr las pruebas de software, el diagrama de interaccion de sus modulos, las decisiones tomadas durante el diseno del backend y las limitaciones o cosas que se harian de otra forma con mas tiempo.

## DIAGRAMA DEL SISTEMA

El trafico exterior entra por Nginx en el puerto 80. Nginx se encarga de rutear las peticiones segun la ruta especificada. Las rutas `/admin` y `/static` se dirigen al servicio de Django. Las rutas que comienzan con `/api/` van directo al backend rapido de FastAPI. La ruta raiz `/` sirve los archivos estaticos del frontend que estan en el contenedor de tickets. Django escribe en Postgres y FastAPI lee de Postgres y cachea las consultas en Redis.

<img width="467" height="647" alt="Image" src="https://github.com/user-attachments/assets/df732ad3-a05b-41a7-9dab-606685f83602" />

<img width="918" height="613" alt="Image" src="https://github.com/user-attachments/assets/bc3ee9b9-fc85-4cae-9525-c4192cdab8ce" />

### Fastapi

<img width="1500" height="882" alt="Image" src="https://github.com/user-attachments/assets/b711324b-a00a-4192-97c5-71e6eb5cca10" />

### Django

<img width="1188" height="807" alt="Image" src="https://github.com/user-attachments/assets/d1a7c461-d861-40c6-b317-9936f1fba548" />

## COMO EJECUTAR EL PROYECTO

Para levantar todo el entorno con un unico comando se debe ejecutar en la terminal `docker compose up --build -d` desde la carpeta raiz del proyecto. Esto creara y levantara los contenedores de Postgres, Redis, Django, FastAPI y Nginx de forma ordenada y con sus respectivos controles de salud.

Para acceder al panel de administracion de Django se debe ingresar a la direccion `http://localhost/admin/` utilizando las credenciales que se encuentran configuradas en el archivo de variables de entorno. El frontend principal estara disponible directamente en la direccion `http://localhost/` en tu navegador.

## COMO CORRER LAS PRUEBAS

Las pruebas de calidad del software estan divididas por servicios para asegurar que cada componente funciona de forma correcta tanto integrada como en conjunto.

Para ejecutar las pruebas del servicio de Django se debe ingresar a la terminal y correr el comando `docker compose exec django python manage.py test` el cual ejecutara las validaciones de forma automatica.

Para ejecutar las pruebas del servicio de FastAPI se debe correr el comando `docker compose exec fastapi pytest` en la terminal.

## DECISIONES DE DISENO

Se decidio desacoplar completamente el funcionamiento de FastAPI de Django a nivel de tiempo de ejecucion en la configuracion de Docker Compose. Esto significa que si el panel de administracion de Django se detiene o falla por cualquier motivo el servicio publico de venta de entradas que corre sobre FastAPI seguira funcionando sin interrupciones consumiendo datos directamente de la base de datos de Postgres y de Redis.

"Graceful Degradation:
En caso de una falla en el servidor de caché (Redis), el servicio seguira funcionando sin cache.

Para las reglas de negocio de precios se implemento una logica basada en ventanas de tiempo. Cada tipo de ticket posee fechas de inicio y fin de validez. El sistema calcula en tiempo real cual es el precio minimo de un evento basandose unicamente en las tarifas activas en ese preciso instante y en caso de que existan varias tarifas validas al mismo tiempo siempre se prioriza la de menor costo para beneficiar al usuario final.

En cuanto a la estrategia de cache en Redis se opto por guardar las respuestas de listados y detalles por un tiempo de trescientos segundos. Para evitar fallas de cache por variaciones de milisegundos en la hora de consulta se redondea el tiempo de la peticion a los diez segundos mas cercanos al generar la llave de cache logrando asi un alto rendimiento y consistencia. 

## COMPROMISOS Y LIMITACIONES

Lo que mas me hizo pensar fue el compromiso del redondeo de la hora de la peticion a diez segundos para la llave de Redis. Esto genera que un cambio de precio o expiracion de ticket tarde hasta diez segundos en verse reflejado en las busquedas de los usuarios pero a cambio reduce la carga de consultas repetitivas en la base de datos Postgres de forma significativa. Se analizo para que tenga un balance entre seguridad y rendimiento.

## MEJORAS PARA EL FUTURO

Con mas tiempo se deberia implementar un sistema de autenticacion en el fastapi, validar UTC a nivel general (actualmente se definio todo en horario bolivia). Implementar de manera mas eficaz el redis. 

## LO QUE ESTOY MAS ORGULLOSO Y MENOS ORGULLOSO

Lo que estoy mas orgulloso es de que aprendi perfectamente a usar nginx en este materia, docker y dockerfiles. Por lo que estoy contento con este aprendizaje y seguramente lo hice bien todo ese proceso en el proyecto. 

Lo que me siento menos orgulloso fue en el hecho de que el frontend aunque no es el objetivo de esta competencia, no soy muy bueno revisando siquiera el codigo para darme cuenta de que apis tiene. Tuve que fijarme muy bien estos detalles. ADEMAS otra cosa que me costo fue el hecho de que no sabia porque no se interpretaba bien los contenedores de python, resulta que era porque las librerias de python usan rust y c y tenia que tener un monton de librerias para correrlas.

## RATE LIMIT IMPLEMENTADO

Con la libreria limiter se agrego un limite DE 100 consultas por minuto para cada usuario para cumplicar con el criterio extra de limites

## Apis Estructura

### /api/v1/events/?page=2&sort=price.

{
  "count": 150,
  "page": 1,
  "results": [
    {
      "id": "c9b0c268-d0ad-48b4-845b-7c37fa9e8dfb",
      "title": "Mega Concierto de Rock",
      "starts_at": "2026-07-10T21:00:00Z",
      "venue": {
        "name": "Teatro Al Aire Libre",
        "city": "La Paz"
      },
      "min_price": 75.50,
      "available": 420,
      "total_capacity": 500
    }
  ]
}

### GET /api/v1/events/search/

{
  "count": 1,
  "page": 1,
  "results": [
    {
      "id": "c9b0c268-d0ad-48b4-845b-7c37fa9e8dfb",
      "title": "Mega Concierto de Rock",
      "starts_at": "2026-07-10T21:00:00Z",
      "venue": {
        "name": "Teatro Al Aire Libre",
        "city": "La Paz"
      },
      "min_price": 75.50,
      "available": 420,
      "total_capacity": 500
    }
  ]
}

### GET /api/v1/events/{event_id}

{
  "id": "c9b0c268-d0ad-48b4-845b-7c37fa9e8dfb",
  "title": "Mega Concierto de Rock",
  "starts_at": "2026-07-10T21:00:00Z",
  "venue": {
    "name": "Teatro Al Aire Libre",
    "city": "La Paz"
  },
  "description": "El festival de rock más grande del año con bandas internacionales invitadas.",
  "min_price": 75.50,
  "available": 420,
  "total_capacity": 500,
  "tiers": [
    {
      "name": "General",
      "price": 75.50,
      "available": 300
    },
    {
      "name": "VIP",
      "price": 250.00,
      "available": 120
    }
  ]
}

### GET /api/v1/healthz 

Sin body


# DEFENSA DE EXAMEN