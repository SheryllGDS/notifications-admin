import json
from flask import url_for


def test_should_show_overview_page(
    app_,
    api_user_active,
    mock_login,
    mock_get_service,
    mock_get_users_by_service
):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.get(url_for('main.manage_users', service_id=55555))

        assert 'Manage team' in response.get_data(as_text=True)
        assert response.status_code == 200
        mock_get_users_by_service.assert_called_once_with(service_id='55555')


def test_should_show_page_for_one_user(
    app_,
    api_user_active,
    mock_login,
    mock_get_service
):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.get(url_for('main.edit_user', service_id=55555, user_id=0))

        assert response.status_code == 200


def test_redirect_after_saving_user(
    app_,
    api_user_active,
    mock_login,
    mock_get_service,
    mock_get_users_by_service
):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.post(url_for(
                'main.edit_user', service_id=55555, user_id=0
            ))

        assert response.status_code == 302
        assert response.location == url_for(
            'main.manage_users', service_id=55555, _external=True
        )


def test_should_show_page_for_inviting_user(
    app_,
    api_user_active,
    mock_login,
    mock_get_service
):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.get(url_for('main.invite_user', service_id=55555))

        assert 'Add a new team member' in response.get_data(as_text=True)
        assert response.status_code == 200


def test_invite_user(
    app_,
    service_one,
    api_user_active,
    mock_login,
    mock_get_users_by_service,
    mock_create_invite
):
    from_user = api_user_active.id
    service_id = service_one['id']
    email_address = 'test@example.gov.uk'

    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.post(
                url_for('main.invite_user', service_id=service_id),
                data={'email_address': email_address},
                follow_redirects=True
            )

        assert response.status_code == 200
        assert 'Invite sent to test@example.gov.uk' in response.get_data(as_text=True)
        mock_create_invite.assert_called_with(from_user, service_id, email_address)