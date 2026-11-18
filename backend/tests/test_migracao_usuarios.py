from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase


class MigracaoUsuariosTests(TransactionTestCase):
    def test_migracao_preserva_usuario_da_fase_um(self):
        executor = MigrationExecutor(connection)
        old = [("usuarios", "0001_initial")]
        new = [("usuarios", "0002_usuario_perfil")]
        executor.migrate(old)
        try:
            old_apps = executor.loader.project_state(old).apps
            antigo = old_apps.get_model("usuarios", "Usuario").objects.create(email="Legado@EXAMPLE.org", password="hash-legado")
            executor = MigrationExecutor(connection)
            executor.migrate(new)
            novo = executor.loader.project_state(new).apps.get_model("usuarios", "Usuario").objects.get(pk=antigo.pk)
            self.assertEqual(novo.email, "legado@example.org")
            self.assertEqual(novo.nome, "Legado@EXAMPLE.org")
            self.assertEqual(novo.perfil, 1)
            self.assertEqual(novo.password, "hash-legado")
        finally:
            MigrationExecutor(connection).migrate(MigrationExecutor(connection).loader.graph.leaf_nodes())
