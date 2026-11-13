from django.db import migrations, models


class Migration(migrations.Migration):
    """Issue #68: store which Cognito User Pool vouched for each user."""

    dependencies = [
        ("users", "0002_remove_tag_unique_tag_name_type_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="cognito_issuer",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
