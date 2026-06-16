## Entidades principales y relaciones

- `Usuario` (extiende `AbstractUser`)
  - Campos: rol, email, telefono, direccion, fecha_nacimiento, fecha_registro
  - Relaciones:
    - 1:1 -> `Cliente` (OneToOneField, on_delete=CASCADE, related_name='cliente')
    - 1:1 -> `Vendedor` (OneToOneField, on_delete=CASCADE, related_name='vendedor')

- `Cliente`
  - Relacionado directamente a `Usuario` (ver arriba)
  - Relaciones:
    - 1:N -> `Pedido` (ForeignKey, on_delete=CASCADE, related_name='pedidos_cliente')
    - 1:N -> `MetodoPago` (ForeignKey, on_delete=CASCADE, related_name='metodos_pago')
    - 1:1 -> `ListaDeseos` (OneToOneField, on_delete=CASCADE, related_name='lista_deseos')
    - 1:N -> `Valoracion`, `Devolucion`, `ClienteDescuento`, `EventoCliente` (para este último: on_delete=SET_NULL)

- `Pedido`
  - Pertenece a `Cliente` (CASCADE)
  - Relacionado a `Vendedor` (CASCADE, nullable)
  - 1:N -> `LineaPedido` (CASCADE)
  - 1:N -> `Pago` (CASCADE)
  - 1:N -> `PagoPayPal` (CASCADE)

- `LineaPedido`
  - Pertenece a `Pedido` (CASCADE)
  - Referencia `Pieza` (CASCADE)

- `MetodoPago` (Tarjeta / Cuenta / Billetera)
  - Pertenece a `Cliente` (CASCADE)
  - 1:1 -> `Tarjeta`, `CuentaBancaria`, `BilleteraDigital` (CASCADE)
  - `Pago.metodo_pago` puede apuntar a `MetodoPago` (FK, CASCADE, nullable)

- `Pago` y `PagoPayPal`
  - `Pago` pertenece a `Pedido` (CASCADE)
  - `PagoPayPal.pago` es OneToOne con `Pago` pero usa `SET_NULL` (puede quedar null si se elimina el `Pago`)

- `EventoCliente`
  - FK a `Cliente` con `on_delete=SET_NULL` (diseñado para preservar histórico): potencial fuente de registros "huérfanos" si se elimina `Cliente` sin limpiar.

- `ListaDeseos` y `ListaDeseosPieza`
  - `ListaDeseos` es 1:1 con `Cliente` (CASCADE)
  - `ListaDeseosPieza` referencia `ListaDeseos` y `Pieza` (CASCADE)

- `Descuento` y `ClienteDescuento`
  - `ClienteDescuento` es intermedia (FK a Cliente y Descuento) con CASCADE

## Comportamiento frente a borrados — riesgos y decisiones

- Mayoría de relaciones usan `CASCADE`, lo que facilita limpiar todo eliminando `Cliente` o `Usuario`.
- Excepciones clave:
  - `EventoCliente.cliente` usa `SET_NULL`: si borras `Cliente` tendrás eventos con `cliente=NULL`.
  - `PagoPayPal.pago` usa `SET_NULL`: puede quedar el registro PayPal sin referencia al `Pago` local.
- Otras dependencias externas: tablas de tokens JWT (`outstandingtoken`, `blacklistedtoken`) referencian `usuario`; deben eliminarse antes de borrar el `Usuario`.