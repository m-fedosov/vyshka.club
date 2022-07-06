# Generated by Django 3.2.5 on 2021-09-29 21:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0022_auto_20210911_0827'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalpost',
            name='comment_template',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='comment_template',
            field=models.TextField(null=True),
        ),
        migrations.AlterField(
            model_name='historicalpost',
            name='type',
            field=models.CharField(choices=[('post', 'Текст'), ('intro', '#intro'), ('link', 'Студентам'), ('question', 'Вопрос'), ('pain', 'Боль'), ('idea', 'Идея'), ('project', 'Проект'), ('event', 'Событие'), ('referral', 'Рефералка'), ('battle', 'Батл'), ('weekly_digest', 'Журнал Клуба'), ('guide', 'Адаптация'), ('thread', 'Флуд')], db_index=True, default='post', max_length=32),
        ),
        migrations.AlterField(
            model_name='post',
            name='type',
            field=models.CharField(choices=[('post', 'Текст'), ('intro', '#intro'), ('link', 'Студентам'), ('question', 'Вопрос'), ('pain', 'Боль'), ('idea', 'Идея'), ('project', 'Проект'), ('event', 'Событие'), ('referral', 'Рефералка'), ('battle', 'Батл'), ('weekly_digest', 'Журнал Клуба'), ('guide', 'Адаптация'), ('thread', 'Флуд')], db_index=True, default='post', max_length=32),
        ),
    ]
