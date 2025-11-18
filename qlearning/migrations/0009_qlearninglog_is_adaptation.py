from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('qlearning', '0008_remove_qlearningactionlog_user_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='qlearninglog',
            name='is_adaptation',
            field=models.BooleanField(default=False, help_text='Whether this log entry represents an adaptation event'),
        ),
    ]
