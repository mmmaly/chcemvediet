from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_cron', '0003_cronjoblock'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='cronjoblog',
            index_together=set(),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'is_success', 'ran_at_time'], name='django_cron_code_is_succ_idx'),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'start_time', 'ran_at_time'], name='django_cron_code_start_r_idx'),
        ),
        migrations.AddIndex(
            model_name='cronjoblog',
            index=models.Index(fields=['code', 'start_time'], name='django_cron_code_start_idx'),
        ),
    ]
