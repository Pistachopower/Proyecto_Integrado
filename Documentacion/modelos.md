```mermaid
erDiagram

    Usuario ||--|| Cliente : "1 a 1"
    Usuario ||--|| Vendedor : "1 a 1"

    CategoriaPieza ||--o{ Pieza : "1 a N"
    Pieza ||--o{ ImagenPieza : "1 a N"

    Cliente ||--o{ Pedido : "1 a N"
    Vendedor ||--o{ Pedido : "1 a N"

    Pedido ||--o{ LineaPedido : "1 a N"
    Pieza ||--o{ LineaPedido : "1 a N"

    Cliente ||--o{ MetodoPago : "1 a N"
    MetodoPago ||--|| Tarjeta : "1 a 1"
    MetodoPago ||--|| CuentaBancaria : "1 a 1"
    MetodoPago ||--|| BilleteraDigital : "1 a 1"

    Pedido ||--o{ Pago : "1 a N"
    MetodoPago ||--o{ Pago : "1 a N"

    LineaPedido ||--o{ Devolucion : "1 a N"
    Cliente ||--o{ Devolucion : "1 a N"

    Pieza ||--o{ Valoracion : "1 a N"
    Cliente ||--o{ Valoracion : "1 a N"

    Cliente ||--|| ListaDeseos : "1 a 1"
    ListaDeseos ||--o{ ListaDeseosPieza : "1 a N"
    Pieza ||--o{ ListaDeseosPieza : "1 a N"

    Cliente ||--o{ ClienteDescuento : "1 a N"
    Descuento ||--o{ ClienteDescuento : "1 a N"
