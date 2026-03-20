from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ingestion", "0001_initial"),
    ]

    operations = [
        migrations.DeleteModel(name="EmbeddingJob"),
        migrations.DeleteModel(name="ParseJob"),
    ]
