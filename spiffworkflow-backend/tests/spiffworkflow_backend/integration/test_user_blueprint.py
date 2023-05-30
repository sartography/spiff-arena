# TODO: fix these tests for new authing system
# """Test User Blueprint."""
# import json
# from typing import Any
#
# from flask.testing import FlaskClient
#
# from spiffworkflow_backend.models.group import GroupModel
# from spiffworkflow_backend.models.user import UserModel
#
#
# def test_acceptance(client: FlaskClient) -> None:
#     """Test_acceptance."""
#     # Create a user U
#     user = create_user(client, "U")
#     # Create a group G
#     group_g = create_group(client, "G")
#     # Assign user U to group G
#     assign_user_to_group(client, user, group_g)
#     # Delete group G
#     delete_group(client, group_g.name)
#     # Create group H
#     group_h = create_group(client, "H")
#     # Assign user U to group H
#     assign_user_to_group(client, user, group_h)
#     # Unassign user U from group H
#     remove_user_from_group(client, user, group_h)
#     # Delete group H
#     delete_group(client, group_h.name)
#     # Delete user U
#     delete_user(client, user.username)
#
#
# def test_user_can_be_created_and_deleted(client: FlaskClient) -> None:
#     """Test_user_can_be_created_and_deleted."""
#     username = "joe"
#     response = client.get(f"/user/{username}")
#     assert response.status_code == 201
#     user = UserModel.query.filter_by(username=username).first()
#     assert user.username == username
#
#     response = client.delete(f"/user/{username}")
#     assert response.status_code == 204
#     user = UserModel.query.filter_by(username=username).first()
#     assert user is None
#
#
# def test_delete_returns_an_error_if_user_is_not_found(client: FlaskClient) -> None:
#     """Test_delete_returns_an_error_if_user_is_not_found."""
#     username = "joe"
#     response = client.delete(f"/user/{username}")
#     assert response.status_code == 400
#
#
# def test_create_returns_an_error_if_user_exists(client: FlaskClient) -> None:
#     """Test_create_returns_an_error_if_user_exists."""
#     username = "joe"
#     response = client.get(f"/user/{username}")
#     assert response.status_code == 201
#     user = UserModel.query.filter_by(username=username).first()
#     assert user.username == username
#
#     response = client.get(f"/user/{username}")
#     assert response.status_code == 409
#
#     response = client.delete(f"/user/{username}")
#     assert response.status_code == 204
#     user = UserModel.query.filter_by(username=username).first()
#     assert user is None
#
#
# def test_group_can_be_created_and_deleted(client: FlaskClient) -> None:
#     """Test_group_can_be_created_and_deleted."""
#     group_name = "administrators"
#     response = client.get(f"/group/{group_name}")
#     assert response.status_code == 201
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group.name == group_name
#
#     response = client.delete(f"/group/{group_name}")
#     assert response.status_code == 204
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group is None
#
#
# def test_delete_returns_an_error_if_group_is_not_found(client: FlaskClient) -> None:
#     """Test_delete_returns_an_error_if_group_is_not_found."""
#     group_name = "administrators"
#     response = client.delete(f"/group/{group_name}")
#     assert response.status_code == 400
#
#
# def test_create_returns_an_error_if_group_exists(client: FlaskClient) -> None:
#     """Test_create_returns_an_error_if_group_exists."""
#     group_name = "administrators"
#     response = client.get(f"/group/{group_name}")
#     assert response.status_code == 201
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group.name == group_name
#
#     response = client.get(f"/group/{group_name}")
#     assert response.status_code == 409
#
#     response = client.delete(f"/group/{group_name}")
#     assert response.status_code == 204
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group is None
#
#
# def test_user_can_be_assigned_to_a_group(client: FlaskClient) -> None:
#     """Test_user_can_be_assigned_to_a_group."""
#     user = create_user(client, "joe")
#     group = create_group(client, "administrators")
#     assign_user_to_group(client, user, group)
#     delete_user(client, user.username)
#     delete_group(client, group.name)
#
#
# def test_user_can_be_removed_from_a_group(client: FlaskClient) -> None:
#     """Test_user_can_be_removed_from_a_group."""
#     user = create_user(client, "joe")
#     group = create_group(client, "administrators")
#     assign_user_to_group(client, user, group)
#     remove_user_from_group(client, user, group)
#     delete_user(client, user.username)
#     delete_group(client, group.name)
#
#
# def create_user(client: FlaskClient, username: str) -> Any:
#     """Create_user."""
#     response = client.get(f"/user/{username}")
#     assert response.status_code == 201
#     user = UserModel.query.filter_by(username=username).first()
#     assert user.username == username
#     return user
#
#
# def delete_user(client: FlaskClient, username: str) -> None:
#     """Delete_user."""
#     response = client.delete(f"/user/{username}")
#     assert response.status_code == 204
#     user = UserModel.query.filter_by(username=username).first()
#     assert user is None
#
#
# def create_group(client: FlaskClient, group_name: str) -> Any:
#     """Create_group."""
#     response = client.get(f"/group/{group_name}")
#     assert response.status_code == 201
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group.name == group_name
#     return group
#
#
# def delete_group(client: FlaskClient, group_name: str) -> None:
#     """Delete_group."""
#     response = client.delete(f"/group/{group_name}")
#     assert response.status_code == 204
#     group = GroupModel.query.filter_by(name=group_name).first()
#     assert group is None
#
#
# def assign_user_to_group(
#     client: FlaskClient, user: UserModel, group: GroupModel
# ) -> None:
#     """Assign_user_to_group."""
#     response = client.post(
#         "/assign_user_to_group",
#         content_type="application/json",
#         data=json.dumps({"user_id": user.id, "group_id": group.id}),
#     )
#     assert response.status_code == 201
#     user = UserModel.query.filter_by(id=user.id).first()
#     assert len(user.user_group_assignments) == 1
#     assert user.user_group_assignments[0].group_id == group.id
#
#
# def remove_user_from_group(
#     client: FlaskClient, user: UserModel, group: GroupModel
# ) -> None:
#     """Remove_user_from_group."""
#     response = client.post(
#         "remove_user_from_group",
#         content_type="application/json",
#         data=json.dumps({"user_id": user.id, "group_id": group.id}),
#     )
#     assert response.status_code == 204
#     user = UserModel.query.filter_by(id=user.id).first()
#     assert len(user.user_group_assignments) == 0
