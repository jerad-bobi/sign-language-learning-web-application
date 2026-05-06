from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_remove_account_verification_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='login_streak',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='account',
            name='last_login_date',
            field=models.DateField(blank=True, default=None, null=True),
        ),
    ]
