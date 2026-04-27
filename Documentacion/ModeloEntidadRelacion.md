erDiagram
    %% LEYENDA:
    %% || = uno y solo uno
    %% o| = cero o uno
    %% o{ = cero o muchos
    %% |{ = uno o muchos

    USUARIO {
        int id PK
        string username
        string email
        string telefono
        string direccion
        date fecha_nacimiento
        date fecha_registro
        int rol
    }

    CLIENTE {
        int id PK
        int usuario_id FK
    }

    VENDEDOR {
        int id PK
        int usuario_id FK
        date fecha_contratacion
        decimal comision_porcentaje
        string foto_perfil_vendedor
    }

    CATEGORIA_PIEZA {
        int id PK
        string nombre
        string imagen_categoria
        string descripcion
    }

    PIEZA {
        int id PK
        int categoria_id FK
        string nombre
        string referencia
        string version
        string marca
        int anio
        decimal precio_base
        string descripcion
        string imagen
        int stock
        int estado
    }

    IMAGEN_PIEZA {
        int id PK
        int pieza_id FK
        string url_imagen
        string descripcion
    }

    PEDIDO {
        int id PK
        int cliente_id FK
        int vendedor_id FK
        int estado
        date fecha_pedido
        string direccion_envio
        decimal total
    }

    LINEA_PEDIDO {
        int id PK
        int pedido_id FK
        int pieza_id FK
        int cantidad
        decimal precio_unitario
        decimal descuento_aplicado
        decimal subtotal
        int estado
    }

    METODO_PAGO {
        int id PK
        int cliente_id FK
        int tipo_metodo
        boolean es_predeterminado
        date fecha_agregado
    }

    TARJETA {
        int id PK
        int metodo_pago_id FK
        int tipo_tarjeta
        string num_tarjeta_encriptado
        string propietario
        string fecha_caducidad
        string moneda
    }

    CUENTA_BANCARIA {
        int id PK
        int metodo_pago_id FK
        string iban
        string banco
        string moneda
    }

    BILLETERA_DIGITAL {
        int id PK
        int metodo_pago_id FK
        int proveedor
        string email
    }

    PAGO {
        int id PK
        int pedido_id FK
        int metodo_pago_id FK
        int estado
        date fecha_pago
        decimal monto
        string numero_transaccion
    }

    PAGO_PAYPAL {
        int id PK
        int pedido_id FK
        int pago_id FK
        string paypal_order_id
        string paypal_capture_id
        int estado
        decimal monto
        string moneda
        datetime fecha_creacion
        datetime fecha_actualizacion
        json respuesta_paypal
    }

    DEVOLUCION {
        int id PK
        int linea_pedido_id FK
        int cliente_id FK
        int estado
        date fecha_solicitud
        date fecha_aprobacion
        string motivo
        int cantidad_devuelta
        decimal monto_reembolso
    }

    VALORACION {
        int id PK
        int pieza_id FK
        int cliente_id FK
        int puntuacion
        string titulo
        string comentario
        date fecha_valoracion
        boolean aprobado
    }

    LISTA_DESEOS {
        int id PK
        int cliente_id FK
        string nombre
        date fecha_creacion
    }

    LISTA_DESEOS_PIEZA {
        int id PK
        int lista_deseos_id FK
        int pieza_id FK
        date fecha_agregado
    }

    EVENTO_CLIENTE {
        int id PK
        int cliente_id FK
        string nombre_evento
        string sesion_id
        datetime fecha_evento
        json propiedades
    }

    DESCUENTO {
        int id PK
        int tipo
        int estado
        string codigo
        string nombre
        string descripcion
        decimal valor
        date fecha_inicio
        date fecha_fin
        int usos_maximos
        int usos_actuales
    }

    CLIENTE_DESCUENTO {
        int id PK
        int cliente_id FK
        int descuento_id FK
        date fecha_asignado
        int veces_usado
    }

    USUARIO ||--o| CLIENTE : tiene
    USUARIO ||--o| VENDEDOR : tiene

    CATEGORIA_PIEZA ||--o{ PIEZA : clasifica
    PIEZA ||--o{ IMAGEN_PIEZA : tiene

    CLIENTE ||--o{ PEDIDO : realiza
    VENDEDOR ||--o{ PEDIDO : atiende

    PEDIDO ||--o{ LINEA_PEDIDO : contiene
    PIEZA ||--o{ LINEA_PEDIDO : aparece_en

    CLIENTE ||--o{ METODO_PAGO : registra
    METODO_PAGO ||--o| TARJETA : detalle
    METODO_PAGO ||--o| CUENTA_BANCARIA : detalle
    METODO_PAGO ||--o| BILLETERA_DIGITAL : detalle

    PEDIDO ||--o{ PAGO : genera
    METODO_PAGO ||--o{ PAGO : usa

    PEDIDO ||--o{ PAGO_PAYPAL : tiene
    PAGO ||--o| PAGO_PAYPAL : vinculado

    LINEA_PEDIDO ||--o{ DEVOLUCION : origina
    CLIENTE ||--o{ DEVOLUCION : solicita

    PIEZA ||--o{ VALORACION : recibe
    CLIENTE ||--o{ VALORACION : escribe

    CLIENTE ||--o| LISTA_DESEOS : posee
    LISTA_DESEOS ||--o{ LISTA_DESEOS_PIEZA : contiene
    PIEZA ||--o{ LISTA_DESEOS_PIEZA : aparece_en

    CLIENTE ||--o{ EVENTO_CLIENTE : registra

    CLIENTE ||--o{ CLIENTE_DESCUENTO : recibe
    DESCUENTO ||--o{ CLIENTE_DESCUENTO : asigna