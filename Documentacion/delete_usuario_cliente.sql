-- Borra un usuario cliente y todos sus registros asociados.
-- Cambia v_user_id por el ID real antes de ejecutarlo.

DO $$
DECLARE
    v_user_id bigint := 58;
    v_cliente_id bigint;
BEGIN
    SELECT id
    INTO v_cliente_id
    FROM proyecto_cliente
    WHERE usuario_id = v_user_id;

    IF v_cliente_id IS NULL THEN
        DELETE FROM proyecto_usuario
        WHERE id = v_user_id;
        RETURN;
    END IF;

    DELETE FROM evento_cliente
    WHERE cliente_id = v_cliente_id;

    IF to_regclass('public.proyecto_clientedescuento') IS NOT NULL THEN
        DELETE FROM proyecto_clientedescuento
        WHERE cliente_id = v_cliente_id;
    END IF;

    DELETE FROM proyecto_listadeseospieza
    WHERE lista_deseos_id IN (
        SELECT id
        FROM proyecto_listadeseos
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_listadeseos
    WHERE cliente_id = v_cliente_id;

    DELETE FROM proyecto_devolucion
    WHERE cliente_id = v_cliente_id;

    DELETE FROM proyecto_valoracion
    WHERE cliente_id = v_cliente_id;

    DELETE FROM proyecto_pagopaypal
    WHERE pedido_id IN (
        SELECT id
        FROM proyecto_pedido
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_pago
    WHERE pedido_id IN (
        SELECT id
        FROM proyecto_pedido
        WHERE cliente_id = v_cliente_id
    )
    OR metodo_pago_id IN (
        SELECT id
        FROM proyecto_metodopago
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_tarjeta
    WHERE metodo_pago_id IN (
        SELECT id
        FROM proyecto_metodopago
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_cuentabancaria
    WHERE metodo_pago_id IN (
        SELECT id
        FROM proyecto_metodopago
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_billeteradigital
    WHERE metodo_pago_id IN (
        SELECT id
        FROM proyecto_metodopago
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_metodopago
    WHERE cliente_id = v_cliente_id;

    DELETE FROM proyecto_lineapedido
    WHERE pedido_id IN (
        SELECT id
        FROM proyecto_pedido
        WHERE cliente_id = v_cliente_id
    );

    DELETE FROM proyecto_pedido
    WHERE cliente_id = v_cliente_id;

    DELETE FROM proyecto_cliente
    WHERE id = v_cliente_id;

    DELETE FROM token_blacklist_blacklistedtoken
    WHERE token_id IN (
        SELECT id
        FROM token_blacklist_outstandingtoken
        WHERE user_id = v_user_id
    );

    DELETE FROM token_blacklist_outstandingtoken
    WHERE user_id = v_user_id;

    DELETE FROM proyecto_usuario
    WHERE id = v_user_id;
END $$;
