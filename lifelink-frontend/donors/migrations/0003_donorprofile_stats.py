from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donors", "0002_bloodrequest_created_by"),
    ]

    operations = [
        migrations.AddField(
            model_name="donorprofile",
            name="rating_count",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="donorprofile",
            name="rating_total",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="donorprofile",
            name="total_donations",
            field=models.PositiveIntegerField(default=0),
        ),
    ]
