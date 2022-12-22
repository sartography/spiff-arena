"""Script."""
from __future__ import annotations

import importlib
import os
import pkgutil
from abc import abstractmethod
from typing import Any
from typing import Callable

from flask_bpmn.api.api_error import ApiError

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceNotFoundError
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.services.authorization_service import AuthorizationService

# Generally speaking, having some global in a flask app is TERRIBLE.
# This is here, because after loading the application this will never change under
# any known condition, and it is expensive to calculate it everytime.
SCRIPT_SUB_CLASSES = None


class ScriptUnauthorizedForUserError(Exception):
    """ScriptUnauthorizedForUserError."""


class Script:
    """Provides an abstract class that defines how scripts should work, this must be extended in all Script Tasks."""

    @abstractmethod
    def get_description(self) -> str:
        """Get_description."""
        raise ApiError("invalid_script", "This script does not supply a description.")

    @abstractmethod
    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run."""
        raise ApiError(
            "invalid_script",
            "This is an internal error. The script you are trying to execute '%s' "
            % self.__class__.__name__
            + "does not properly implement the run function.",
        )

    @staticmethod
    def requires_privileged_permissions() -> bool:
        """It seems safer to default to True and make safe functions opt in for any user to run them.

        To give access to script for a given user, add a 'create' permission with following target-uri:
            '/can-run-privileged-script/{script_name}'
        """
        return True

    @staticmethod
    def generate_augmented_list(
        script_attributes_context: ScriptAttributesContext,
    ) -> dict[str, Callable]:
        """This makes a dictionary of lambda functions that are closed over the class instance that they represent.

        This is passed into PythonScriptParser as a list of helper functions that are
        available for running.  In general, they maintain the do_task call structure that they had, but
        they always return a value rather than updating the task data.

        We may be able to remove the task for each of these calls if we are not using it other than potentially
        updating the task data.
        """

        def make_closure(
            subclass: type[Script],
            script_attributes_context: ScriptAttributesContext,
        ) -> Callable:
            """Yes - this is black magic.

            Essentially, we want to build a list of all of the submodules (i.e. email, user_data_get, etc)
            and a function that is assocated with them.
            This basically creates an Instance of the class and returns a function that calls do_task
            on the instance of that class.
            the next for x in range, then grabs the name of the module and associates it with the function
            that we created.
            """
            instance = subclass()

            def check_script_permission() -> None:
                """Check_script_permission."""
                if subclass.requires_privileged_permissions():
                    script_function_name = get_script_function_name(subclass)
                    uri = f"/can-run-privileged-script/{script_function_name}"
                    process_instance = ProcessInstanceModel.query.filter_by(
                        id=script_attributes_context.process_instance_id
                    ).first()
                    if process_instance is None:
                        raise ProcessInstanceNotFoundError(
                            f"Could not find a process instance with id '{script_attributes_context.process_instance_id}' "
                            f"when running script '{script_function_name}'"
                        )
                    user = process_instance.process_initiator
                    has_permission = AuthorizationService.user_has_permission(
                        user=user, permission="create", target_uri=uri
                    )
                    if not has_permission:
                        raise ScriptUnauthorizedForUserError(
                            f"User {user.username} does not have access to run privileged script '{script_function_name}'"
                        )

            def run_script_if_allowed(*ar: Any, **kw: Any) -> Any:
                """Run_script_if_allowed."""
                check_script_permission()
                return subclass.run(
                    instance,
                    script_attributes_context,
                    *ar,
                    **kw,
                )

            return run_script_if_allowed

        def get_script_function_name(subclass: type[Script]) -> str:
            """Get_script_function_name."""
            return subclass.__module__.split(".")[-1]

        execlist = {}
        subclasses = Script.get_all_subclasses()
        for x in range(len(subclasses)):
            subclass = subclasses[x]
            execlist[get_script_function_name(subclass)] = make_closure(
                subclass, script_attributes_context=script_attributes_context
            )
        return execlist

    @classmethod
    def get_all_subclasses(cls) -> list[type[Script]]:
        """Get_all_subclasses."""
        # This is expensive to generate, never changes after we load up.
        global SCRIPT_SUB_CLASSES
        if not SCRIPT_SUB_CLASSES:
            SCRIPT_SUB_CLASSES = Script._get_all_subclasses(Script)
        return SCRIPT_SUB_CLASSES

    @staticmethod
    def _get_all_subclasses(script_class: Any) -> list[type[Script]]:
        """_get_all_subclasses."""
        # hackish mess to make sure we have all the modules loaded for the scripts
        pkg_dir = os.path.dirname(__file__)
        for (_module_loader, name, _ispkg) in pkgutil.iter_modules([pkg_dir]):
            importlib.import_module("." + name, __package__)

        """Returns a list of all classes that extend this class."""
        all_subclasses = []

        for subclass in script_class.__subclasses__():
            all_subclasses.append(subclass)
            all_subclasses.extend(Script._get_all_subclasses(subclass))

        return all_subclasses
