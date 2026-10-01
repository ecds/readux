"""Elasticsearch signal processor scoped to indexed models only.

django_elasticsearch_dsl's CelerySignalProcessor (and the RealTimeSignalProcessor
it's built on) connects post_save/post_delete globally -- with no `sender=` --
so it dispatches two Celery tasks (registry_update_task,
registry_update_related_task) for every single model save anywhere in the
project, not just the handful that are actually registered with the
Elasticsearch document registry. The overwhelming majority of those are
no-ops: registry.update()/update_related() just early-return once the task
is already running and discovers the model isn't registered. But each one
still costs a real Celery enqueue, a worker dequeue, an apps.get_model()
lookup and a DB re-fetch before it can discover there's nothing to do --
constant background load proportional to unrelated site traffic (sessions,
CMS pages, tags, ...), not to anything actually searchable.

Connecting per-model instead means Django's own signal dispatcher skips
calling the handler at all for anything not actually indexed -- it isn't a
Python-level filter added after the fact, it's Django not invoking the
receiver in the first place for a non-matching sender.

m2m_changed is intentionally left connected globally (no sender=): its
sender is the auto-generated *through* model for a ManyToManyField, not
either side of the relation, so there's no direct model class to connect it
to without separately resolving each indexed model's M2M through-models.
M2M change volume is low compared to routine saves, and getting that
resolution wrong would silently drop reindexing on a real field change
(e.g. Manifest.collections) -- not a trade worth making for this.
"""
from django.db.models.signals import post_save, post_delete, pre_delete
from django_elasticsearch_dsl.registries import registry
from django_elasticsearch_dsl.signals import CelerySignalProcessor


class ScopedCelerySignalProcessor(CelerySignalProcessor):
    """CelerySignalProcessor, connected only to models that are actually
    registered (directly or via a Document's related_models) with the
    Elasticsearch document registry."""

    def _indexed_models(self):
        return set(registry._models) | set(registry._related_models)

    def setup(self):
        for model in self._indexed_models():
            post_save.connect(self.handle_save, sender=model)
            post_delete.connect(self.handle_delete, sender=model)
            pre_delete.connect(self.handle_pre_delete, sender=model)
        from django.db.models.signals import m2m_changed
        m2m_changed.connect(self.handle_m2m_changed)

    def teardown(self):
        for model in self._indexed_models():
            post_save.disconnect(self.handle_save, sender=model)
            post_delete.disconnect(self.handle_delete, sender=model)
            pre_delete.disconnect(self.handle_pre_delete, sender=model)
        from django.db.models.signals import m2m_changed
        m2m_changed.disconnect(self.handle_m2m_changed)
