from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_account_streak'),
    ]

    operations = [
        migrations.CreateModel(
            name='VocabularyFavorite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=100)),
                ('saved_at', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vocabulary_favorites', to='accounts.account')),
            ],
            options={
                'db_table': 'vocabulary_favorite',
                'ordering': ['-saved_at'],
            },
        ),
        migrations.AddConstraint(
            model_name='vocabularyfavorite',
            constraint=models.UniqueConstraint(fields=['account', 'word'], name='unique_vocab_favorite_per_user'),
        ),
        migrations.CreateModel(
            name='PracticeSession',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signs_detected', models.PositiveIntegerField(default=0)),
                ('duration_seconds', models.PositiveIntegerField(default=0)),
                ('session_end', models.DateTimeField(auto_now_add=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='practice_sessions', to='accounts.account')),
            ],
            options={
                'db_table': 'practice_session',
                'ordering': ['-session_end'],
            },
        ),
    ]
