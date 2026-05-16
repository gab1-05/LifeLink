from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("donors", "0003_donorprofile_stats"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="email_notifications",
            field=models.BooleanField(default=True),
        ),
    ]
