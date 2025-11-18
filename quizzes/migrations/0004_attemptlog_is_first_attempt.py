from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('quizzes', '0003_remove_choice_question_remove_quiz_created_by_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='attemptlog',
            name='is_first_attempt',
            field=models.BooleanField(default=True, help_text='Whether this is the first attempt at this question'),
        ),
    ]
