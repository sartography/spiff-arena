from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService
from tests.base_test import BaseTest
from tests.data.providers.bootstrap_provider import BootstrapProvider


class TestBootstrap(BaseTest):
    def test_bootstrap(self, app_context, mock_process_model_get_all, mock_process_model_get):
        """Test that we can run the bootstrap script without a running server."""

        with app_context.app.app_context():
            provider = BootstrapProvider()
            UserService.add_user(provider.get_user())
            for group in provider.get_groups():
                UserService.add_group(group)
            for file in provider.get_files():
                ProcessModelService.add_process_model_file(file)

            from spiffworkflow_backend.bin.bootstrap import main

            main()

            user = UserModel.query.filter_by(username="bootstrap_user").first()
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "bootstrap_user")
