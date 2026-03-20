from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("knowledge_bases", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="knowledgebase",
            name="collection_name",
            field=models.CharField(blank=True, default="", max_length=200),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="rebuild_status",
            field=models.CharField(default="idle", max_length=20),
        ),
        migrations.AddField(
            model_name="knowledgebase",
            name="rebuild_progress",
            field=models.IntegerField(default=0),
        ),
    ]
