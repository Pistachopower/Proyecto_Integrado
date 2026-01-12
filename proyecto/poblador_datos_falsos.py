import random
from faker import Faker
from datetime import datetime, timedelta
#from django.contrib.auth.hashers import  set_password

from proyecto.models import (
    Usuario, Cliente, Vendedor,
    Pieza,
    Pedido, LineaPedido,
    MetodoPago, Tarjeta, CuentaBancaria, BilleteraDigital,
    Pago, Devolucion,
    Valoracion, ListaDeseos, ListaDeseosPieza,
    Descuento, ClienteDescuento
)

fake = Faker("es_ES")


# ============================================================
# TIPOS DE PIEZAS COHERENTES
# ============================================================
TIPOS_PIEZAS = [
    "Caja de cambios",
    "Culata",
    "Kit de airbag",
    "Motor",
    "Turbocompresor",
    "Radiador",
    "Bomba de agua",
    "Alternador",
    "Inyector",
    "Amortiguador",
    "Disco de freno",
    "Batería",
]

# Elegir solo entre 5 y 15 piezas
TIPOS_PIEZAS = random.sample(TIPOS_PIEZAS, random.randint(5, len(TIPOS_PIEZAS)))



# ============================================================
# CREAR USUARIOS
# ============================================================
def crear_usuarios():
    print("Creando usuarios...")

    # Administrador
    admin = Usuario.objects.create(
        username="nelson",
        email="nelson@tienda.com",
        #
        rol=Usuario.ADMINISTRADOR,
        is_superuser=True,
        is_staff=True,
    )
    admin.set_password("nelson")
    admin.save()

    # Empleados / Vendedores
    empleados = []
    import unicodedata
    def limpiar_texto(texto):
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        texto = texto.replace(' ', '').replace("'", "")
        return texto

    for _ in range(5):
        first_name = fake.first_name()
        last_name = fake.last_name()
        first_name_clean = limpiar_texto(first_name.lower())
        last_name_clean = limpiar_texto(last_name.lower())
        username = f"{first_name_clean}.{last_name_clean}"
        email = f"{username}@tienda.com"
        usuario = Usuario.objects.create(
            username=username,
            email=email,
            rol=Usuario.EMPLEADO,
            first_name=first_name,
            last_name=last_name,
            telefono=fake.phone_number(),
            direccion=fake.address(),
            fecha_nacimiento=fake.date_of_birth(minimum_age=20, maximum_age=65),
        )
        usuario.set_password("admin123")
        usuario.save()
        empleados.append(usuario)

    # Clientes
    clientes = []
    for _ in range(20):
        first_name = fake.first_name()
        last_name = fake.last_name()
        first_name_clean = limpiar_texto(first_name.lower())
        last_name_clean = limpiar_texto(last_name.lower())
        username = f"{first_name_clean}.{last_name_clean}"
        email = f"{username}@tienda.com"
        usuario = Usuario.objects.create(
            username=username,
            email=email,
            rol=Usuario.CLIENTE,
            first_name=first_name,
            last_name=last_name,
            telefono=fake.phone_number(),
            direccion=fake.address(),
            fecha_nacimiento=fake.date_of_birth(minimum_age=18, maximum_age=80),
        )
        usuario.set_password("admin123")
        usuario.save()
        clientes.append(usuario)

    return admin, empleados, clientes


# ============================================================
# CREAR CLIENTES Y VENDEDORES
# ============================================================
def crear_clientes_y_vendedores(empleados, clientes):
    print("Creando clientes y vendedores...")

    clientes_creados = []
    vendedores_creados = []

    # Clientes
    for u in clientes:
        c = Cliente.objects.create(usuario=u)
        clientes_creados.append(c)

    # Vendedores
    for u in empleados:
        v = Vendedor.objects.create(
            usuario=u,
            fecha_contratacion=fake.date_between(start_date="-3y", end_date="today"),
            comision_porcentaje=random.randint(1, 10),
        )
        vendedores_creados.append(v)

    return clientes_creados, vendedores_creados


# ============================================================
# CREAR TIENDAS
# ============================================================



# ============================================================
# CREAR PIEZAS
# ============================================================
def crear_piezas():
    print("Creando piezas...")
    piezas = []
    for nombre in TIPOS_PIEZAS:
        pieza = Pieza.objects.create(
            nombre=nombre,
            referencia=f"REF-{fake.unique.random_int(1000, 9999)}",
            version="v" + str(fake.random_int(1, 5)),
            marca=random.choice(["BMW", "Audi", "Ford", "Volkswagen", "Mercedes"]),
            anio=random.randint(2000, 2024),
            estado=fake.random_int(1, 3),  # NUEVO / USADO / REACONDICIONADO
            precio_base=random.randint(50, 1200),
            descripcion=fake.text(),
        )
        piezas.append(pieza)
    return piezas


# ============================================================
# CREAR INVENTARIO
# ============================================================

def poblar_stock_piezas(piezas):
    print("Asignando stock a piezas...")
    for pieza in piezas:
        pieza.stock = random.randint(0, 20)
        pieza.save()


# ============================================================
# CREAR PEDIDOS + LÍNEAS DE PEDIDO
# ============================================================
def crear_pedidos(clientes, vendedores, piezas):
    print("Creando pedidos...")
    pedidos = []

    for _ in range(40):
        cliente = random.choice(clientes)
        vendedor = random.choice(vendedores)

        pedido = Pedido.objects.create(
            cliente=cliente,
            vendedor=vendedor,
            fecha_pedido=fake.date_this_year(),
            direccion_envio=cliente.usuario.direccion,
            estado=random.choice([1, 2, 3, 4, 5]),
            total=0,  # Se actualiza luego
        )

        total = 0

        # Crear 1–5 líneas
        for _ in range(random.randint(1, 5)):
            pieza = random.choice(piezas)
            cantidad = random.randint(1, 3)
            precio = pieza.precio_base
            descuento = random.randint(0, 20)

            subtotal = cantidad * (precio - descuento)

            LineaPedido.objects.create(
                pedido=pedido,
                pieza=pieza,
                cantidad=cantidad,
                precio_unitario=precio,
                descuento_aplicado=descuento,
                subtotal=subtotal,
            )

            total += subtotal

        pedido.total = total
        pedido.save()

        pedidos.append(pedido)

    return pedidos


# ============================================================
# MÉTODOS DE PAGO + TARJETA/CUENTA/BILLETERA
# ============================================================
def crear_metodos_pago(clientes):
    print("Creando métodos de pago...")

    metodos = []

    for c in clientes:
        for _ in range(random.randint(1, 3)):
            metodo = MetodoPago.objects.create(
                cliente=c,
                tipo_metodo=random.choice([1, 2, 3]),
                es_predeterminado=False,
                fecha_agregado=fake.date_this_year(),
            )
            metodos.append(metodo)

            # Crear detalles según tipo
            if metodo.tipo_metodo == 1:
                Tarjeta.objects.create(
                    metodo_pago=metodo,
                    num_tarjeta_encriptado=fake.credit_card_number(),
                    propietario=c.usuario.first_name + " " + c.usuario.last_name,
                    fecha_caducidad=fake.credit_card_expire(),
                    tipo_tarjeta=random.choice([1, 2, 3]),
                    moneda="EUR",
                )
            elif metodo.tipo_metodo == 2:
                CuentaBancaria.objects.create(
                    metodo_pago=metodo,
                    iban=fake.iban(),
                    banco=fake.company(),
                    moneda="EUR",
                )
            else:
                BilleteraDigital.objects.create(
                    metodo_pago=metodo,
                    email=c.usuario.email,
                    proveedor=random.choice([1, 2, 3]),
                )

    return metodos


# ============================================================
# CREAR PAGOS
# ============================================================
def crear_pagos(pedidos, metodos_pago):
    print("Creando pagos...")

    for pedido in pedidos:
        metodo = random.choice(metodos_pago)

        Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo,
            fecha_pago=pedido.fecha_pedido,
            monto=pedido.total,
            estado=random.choice([1, 2, 3]),
            numero_transaccion=fake.uuid4(),
        )


# ============================================================
# DEVOLUCIONES
# ============================================================
def crear_devoluciones(pedidos, clientes):
    print("Creando devoluciones...")

    for _ in range(10):
        linea = random.choice(
            [lp for lp in LineaPedido.objects.all()]
        )
        cliente = linea.pedido.cliente

        Devolucion.objects.create(
            linea_pedido=linea,
            cliente=cliente,
            fecha_solicitud=fake.date_this_year(),
            fecha_aprobacion=None,
            motivo=fake.text(),
            estado=random.choice([1, 2, 3]),
            cantidad_devuelta=random.randint(1, linea.cantidad),
            monto_reembolso=linea.subtotal,
        )


# ============================================================
# VALORACIONES
# ============================================================
def crear_valoraciones(clientes, piezas):
    print("Creando valoraciones...")

    for _ in range(20):
        Valoracion.objects.create(
            pieza=random.choice(piezas),
            cliente=random.choice(clientes),
            puntuacion=random.randint(1, 5),
            titulo=fake.sentence(),
            comentario=fake.text(),
            fecha_valoracion=fake.date_this_year(),
        )


# ============================================================
# LISTA DE DESEOS + ITEMS
# ============================================================
def crear_listas_deseos(clientes, piezas):
    print("Creando listas de deseos...")

    for c in clientes:
        lista = ListaDeseos.objects.create(
            cliente=c,
            nombre="Lista de " + c.usuario.first_name,
            fecha_creacion=fake.date_this_year(),
        )

        for _ in range(random.randint(1, 5)):
            ListaDeseosPieza.objects.create(
                lista_deseos=lista,
                pieza=random.choice(piezas),
                fecha_agregado=fake.date_this_year(),
            )


# ============================================================
# DESCUENTOS + CLIENTE-DESCUENTO
# ============================================================
def crear_descuentos(clientes):
    print("Creando descuentos...")

    descuentos = []

    for _ in range(5):
        d = Descuento.objects.create(
            codigo=f"DSC-{fake.random_int(1000, 9999)}",
            nombre=fake.word().capitalize(),
            descripcion=fake.text(),
            tipo=random.choice([1, 2]),
            valor=random.randint(5, 30),
            fecha_inicio=fake.date_this_year(),
            fecha_fin=datetime.today().date() + timedelta(days=30),
            usos_maximos=100,
            usos_actuales=0,
            estado=random.choice([1, 2]),
        )
        descuentos.append(d)

    # Asignar descuentos a clientes
    for c in clientes:
        d = random.choice(descuentos)
        ClienteDescuento.objects.create(
            cliente=c,
            descuento=d,
            fecha_asignado=fake.date_this_year(),
            veces_usado=random.randint(0, 5),
        )


# ============================================================
# MAIN
# ============================================================

print("========== INICIANDO GENERACIÓN DE DATOS ==========")

admin, empleados, clientes_usuario = crear_usuarios()
clientes, vendedores = crear_clientes_y_vendedores(empleados, clientes_usuario)


piezas = crear_piezas()
poblar_stock_piezas(piezas)
pedidos = crear_pedidos(clientes, vendedores, piezas)

pedidos = crear_pedidos(clientes, vendedores, piezas)

metodos_pago = crear_metodos_pago(clientes)
crear_pagos(pedidos, metodos_pago)

crear_devoluciones(pedidos, clientes)
crear_valoraciones(clientes, piezas)
crear_listas_deseos(clientes, piezas)
crear_descuentos(clientes)

print("========== DATOS GENERADOS CORRECTAMENTE ==========")
