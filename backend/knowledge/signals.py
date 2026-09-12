from django.db.models.signals import pre_delete
from django.dispatch import receiver

from knowledge.models import Document


@receiver(pre_delete, sender=Document)
def delete_document_file(sender, instance, **kwargs):
    if instance.file:
        instance.file.delete(save=False)
