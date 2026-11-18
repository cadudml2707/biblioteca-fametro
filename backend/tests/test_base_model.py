from django.contrib.auth import get_user_model
from django.db import connection, models
from django.test import TransactionTestCase
from django.utils import timezone

from core.base_model import BaseModel


class BaseModelTests(TransactionTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class ObjetoTeste(BaseModel):
            class Meta:
                app_label = "usuarios"
                db_table = "teste_base_objeto"

        class OutroObjetoTeste(BaseModel):
            class Meta:
                app_label = "usuarios"
                db_table = "teste_base_outro"

        cls.objeto_model = ObjetoTeste
        cls.outro_model = OutroObjetoTeste
        with connection.schema_editor() as schema:
            schema.create_model(ObjetoTeste)
            schema.create_model(OutroObjetoTeste)

    @classmethod
    def tearDownClass(cls):
        try:
            with connection.schema_editor() as schema:
                schema.delete_model(cls.outro_model)
                schema.delete_model(cls.objeto_model)
        finally:
            super().tearDownClass()

    def test_abstract_fields_and_reverse_relations(self):
        self.assertTrue(BaseModel._meta.abstract)
        self.assertNotIn(BaseModel._meta.db_table, connection.introspection.table_names())
        names = {field.name for field in BaseModel._meta.local_fields}
        self.assertEqual(names, {"is_active", "created_at", "created_by", "updated_at", "updated_by"})
        self.assertEqual(self.objeto_model.check(), [])
        self.assertEqual(self.outro_model.check(), [])
        self.assertNotEqual(
            self.objeto_model._meta.get_field("created_by").remote_field.related_name,
            self.outro_model._meta.get_field("created_by").remote_field.related_name,
        )
        self.assertIsInstance(self.objeto_model._meta.pk, models.AutoField)

    def test_audit_fields_and_soft_deactivation(self):
        actor = get_user_model().objects.create(email="responsavel@example.org")
        record = self.objeto_model.objects.create()
        self.assertIsNone(record.created_by)
        self.assertIsNone(record.updated_by)
        self.assertTrue(record.is_active)
        created_at, updated_at = record.created_at, record.updated_at
        self.assertTrue(timezone.is_aware(created_at))
        record.created_by = actor
        record.updated_by = actor
        record.is_active = False
        record.save()
        record.refresh_from_db()
        self.assertEqual(record.created_at, created_at)
        self.assertGreater(record.updated_at, updated_at)
        self.assertEqual(record.created_by, actor)
        self.assertEqual(record.updated_by, actor)
        self.assertFalse(record.is_active)
        actor.delete()
        record.refresh_from_db()
        self.assertIsNone(record.created_by)
        self.assertIsNone(record.updated_by)
