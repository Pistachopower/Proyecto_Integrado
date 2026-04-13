from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0009_alter_pedido_vendedor'),
    ]

    operations = [
        migrations.CreateModel(
            name='EventoCliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre_evento', models.CharField(choices=[('producto_visto', 'Producto visto'), ('busqueda_realizada', 'Busqueda realizada'), ('agregado_carrito', 'Agregado al carrito'), ('compra_completada', 'Compra completada')], max_length=50)),
                ('sesion_id', models.CharField(blank=True, max_length=100, null=True)),
                ('fecha_evento', models.DateTimeField(auto_now_add=True)),
                ('propiedades', models.JSONField(default=dict)),
                ('cliente', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='eventos_cliente', to='proyecto.cliente')),
            ],
            options={
                'db_table': 'evento_cliente',
            },
        ),
        migrations.AddIndex(
            model_name='eventocliente',
            index=models.Index(fields=['nombre_evento'], name='evento_clie_nombre__2aa007_idx'),
        ),
        migrations.AddIndex(
            model_name='eventocliente',
            index=models.Index(fields=['fecha_evento'], name='evento_clie_fecha_e_9c11dc_idx'),
        ),
        migrations.AddIndex(
            model_name='eventocliente',
            index=models.Index(fields=['cliente'], name='evento_clie_cliente_2c9fb0_idx'),
        ),
    ]
