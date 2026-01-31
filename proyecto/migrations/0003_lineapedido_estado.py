from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proyecto', '0002_categoriapieza_pieza_categoria'),
    ]

    operations = [
        migrations.AddField(
            model_name='lineapedido',
            name='estado',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Entregado'), (2, 'Devuelto')], null=True),
        ),
    ]
