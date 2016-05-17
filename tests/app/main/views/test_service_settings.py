import pytest
from flask import url_for

import app
from app.utils import email_safe
from tests import validate_route_permission
from bs4 import BeautifulSoup
from unittest.mock import ANY, Mock
from werkzeug.exceptions import InternalServerError


def test_should_show_overview(app_,
                              active_user_with_permissions,
                              mocker,
                              service_one):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            response = client.get(url_for(
                'main.service_settings', service_id=service_one['id']))
        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Service settings' in resp_data
        app.service_api_client.get_service.assert_called_with(service_one['id'])


def test_should_show_service_name(app_,
                                  active_user_with_permissions,
                                  mocker,
                                  service_one):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            response = client.get(url_for(
                'main.service_name_change', service_id=service_one['id']))
        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Change your service name' in resp_data
        app.service_api_client.get_service.assert_called_with(service_one['id'])


def test_should_redirect_after_change_service_name(app_,
                                                   service_one,
                                                   active_user_with_permissions,
                                                   mock_login,
                                                   mock_get_user,
                                                   mock_get_service,
                                                   mock_update_service,
                                                   mock_get_services,
                                                   mock_has_permissions):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions)
            response = client.post(
                url_for('main.service_name_change', service_id=service_one['id']),
                data={'name': "new name"})

        assert response.status_code == 302
        settings_url = url_for(
            'main.service_name_change_confirm', service_id=service_one['id'], _external=True)
        assert settings_url == response.location
        assert mock_get_services.called


def test_switch_service_to_live(app_,
                                service_one,
                                mock_login,
                                mock_get_user,
                                active_user_with_permissions,
                                mock_get_service,
                                mock_update_service,
                                mock_has_permissions):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions)
            response = client.get(
                url_for('main.service_switch_live', service_id=service_one['id']))
        assert response.status_code == 302
        assert response.location == url_for(
            'main.service_settings',
            service_id=service_one['id'], _external=True)
        mock_update_service.assert_called_with(ANY, ANY, ANY, 25000, False, ANY, ANY)


def test_switch_service_to_restricted(app_,
                                      service_one,
                                      mock_login,
                                      mock_get_user,
                                      active_user_with_permissions,
                                      mock_get_live_service,
                                      mock_update_service,
                                      mock_has_permissions):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions)
            response = client.get(
                url_for('main.service_switch_live', service_id=service_one['id']))
        assert response.status_code == 302
        assert response.location == url_for(
            'main.service_settings',
            service_id=service_one['id'], _external=True)
        mock_update_service.assert_called_with(ANY, ANY, ANY, 50, True, ANY, ANY)


def test_should_not_allow_duplicate_names(app_,
                                          active_user_with_permissions,
                                          mocker,
                                          service_one):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            mocker.patch('app.service_api_client.find_all_service_email_from',
                         return_value=['service_one', 'service.two'])
            service_id = service_one['id']
            response = client.post(
                url_for('main.service_name_change', service_id=service_id),
                data={'name': "SErvICE TWO"})

        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'This service name is already in use' in resp_data
        app.service_api_client.find_all_service_email_from.assert_called_once_with()


def test_should_show_service_name_confirmation(app_,
                                               active_user_with_permissions,
                                               mocker,
                                               service_one):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)

            response = client.get(url_for(
                'main.service_name_change_confirm', service_id=service_one['id']))

        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Change your service name' in resp_data
        app.service_api_client.get_service.assert_called_with(service_one['id'])


def test_should_redirect_after_service_name_confirmation(app_,
                                                         active_user_with_permissions,
                                                         service_one,
                                                         mocker,
                                                         mock_update_service,
                                                         mock_verify_password):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            service_id = service_one['id']
            service_new_name = 'New Name'
            with client.session_transaction() as session:
                session['service_name_change'] = service_new_name
            response = client.post(url_for(
                'main.service_name_change_confirm', service_id=service_id))

        assert response.status_code == 302
        settings_url = url_for('main.service_settings', service_id=service_id, _external=True)
        assert settings_url == response.location
        mock_update_service.assert_called_once_with(service_id,
                                                    service_new_name,
                                                    service_one['active'],
                                                    service_one['message_limit'],
                                                    service_one['restricted'],
                                                    service_one['users'],
                                                    email_safe(service_new_name))
        assert mock_verify_password.called


def test_should_raise_duplicate_name_handled(app_,
                                             active_user_with_permissions,
                                             service_one,
                                             mocker,
                                             mock_get_services,
                                             mock_update_service_raise_httperror_duplicate_name,
                                             mock_verify_password,
                                             fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            service_new_name = 'New Name'
            with client.session_transaction() as session:
                session['service_name_change'] = service_new_name
            response = client.post(url_for(
                'main.service_name_change_confirm', service_id=service_one['id']))

        assert response.status_code == 302
        name_change_url = url_for(
            'main.service_name_change', service_id=service_one['id'], _external=True)
        assert name_change_url == response.location
        assert mock_update_service_raise_httperror_duplicate_name.called
        assert mock_verify_password.called


def test_should_show_request_to_go_live(app_,
                                        api_user_active,
                                        mock_get_service,
                                        mock_get_user,
                                        mock_get_user_by_email,
                                        mock_login,
                                        mock_has_permissions,
                                        fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.get(
                url_for('main.service_request_to_go_live', service_id=service_id))
        service = mock_get_service.side_effect(service_id)['data']
        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Request to go live' in resp_data
        assert mock_get_service.called


def test_should_redirect_after_request_to_go_live(
    app_,
    api_user_active,
    mock_get_user,
    mock_get_service,
    mock_has_permissions,
    mocker
):
    mock_post = mocker.patch(
        'app.main.views.feedback.requests.post',
        return_value=Mock(status_code=201))
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.post(
                url_for('main.service_request_to_go_live', service_id='6ce466d0-fd6a-11e5-82f5-e0accb9d11a6'),
                data={'usage': "One million messages"},
                follow_redirects=True
            )
            assert response.status_code == 200
            mock_post.assert_called_with(
                ANY,
                data={
                    'subject': 'Request to go live',
                    'department_id': ANY,
                    'message': 'From Test User <test@user.gov.uk> on behalf of Test Service (http://localhost/services/6ce466d0-fd6a-11e5-82f5-e0accb9d11a6/dashboard)\n\nUsage estimate\n---\n\nOne million messages',  # noqa
                    'person_email': ANY
                },
                headers=ANY
            )

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        flash_banner = page.find('div', class_='banner-default').string.strip()
        h1 = page.find('h1').string.strip()
        assert flash_banner == 'We’ve received your request to go live'
        assert h1 == 'Settings'


def test_log_error_on_request_to_go_live(
    app_,
    api_user_active,
    mock_get_user,
    mock_get_service,
    mock_has_permissions,
    mocker
):
    mock_post = mocker.patch(
        'app.main.views.service_settings.requests.post',
        return_value=Mock(
            status_code=401,
            json=lambda: {
                'error_code': 'invalid_auth',
                'error_message': 'Please provide a valid API key or token'
            }
        )
    )
    with app_.test_request_context():
        mock_logger = mocker.patch.object(app_.logger, 'error')
        with app_.test_client() as client:
            client.login(api_user_active)
            with pytest.raises(InternalServerError):
                resp = client.post(
                    url_for('main.service_request_to_go_live', service_id='6ce466d0-fd6a-11e5-82f5-e0accb9d11a6'),
                    data={'usage': 'blah'}
                )
            mock_logger.assert_called_with(
                "Deskpro create ticket request failed with {} '{}'".format(mock_post().status_code, mock_post().json())
            )


def test_should_show_status_page(app_,
                                 api_user_active,
                                 mock_get_service,
                                 mock_get_user,
                                 mock_get_user_by_email,
                                 mock_login,
                                 mock_has_permissions,
                                 fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.get(url_for(
                'main.service_status_change', service_id=service_id))

        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Suspend API keys' in resp_data
        assert mock_get_service.called


def test_should_show_redirect_after_status_change(app_,
                                                  api_user_active,
                                                  mock_get_service,
                                                  mock_get_user,
                                                  mock_get_user_by_email,
                                                  mock_login,
                                                  mock_has_permissions,
                                                  fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.post(url_for(
                'main.service_status_change', service_id=service_id))

        assert response.status_code == 302
        redirect_url = url_for(
            'main.service_status_change_confirm', service_id=service_id, _external=True)
        assert redirect_url == response.location
        assert mock_get_service.called


def test_should_show_status_confirmation(app_,
                                         api_user_active,
                                         mock_get_service,
                                         mock_get_user,
                                         mock_get_user_by_email,
                                         mock_login,
                                         mock_has_permissions,
                                         fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.get(url_for(
                'main.service_status_change_confirm', service_id=service_id))

        assert response.status_code == 200
        resp_data = response.get_data(as_text=True)
        assert 'Turn off all outgoing notifications' in resp_data
        assert mock_get_service.called


def test_should_redirect_after_status_confirmation(app_,
                                                   api_user_active,
                                                   mock_get_service,
                                                   mock_update_service,
                                                   mock_get_user,
                                                   mock_get_user_by_email,
                                                   mock_login,
                                                   mock_verify_password,
                                                   mock_has_permissions,
                                                   fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.post(url_for(
                'main.service_status_change_confirm', service_id=service_id))

        assert response.status_code == 302
        settings_url = url_for(
            'main.service_settings', service_id=service_id, _external=True)
        assert settings_url == response.location
        assert mock_get_service.called
        assert mock_update_service.called


def test_should_show_delete_page(app_,
                                 api_user_active,
                                 mock_login,
                                 mock_get_service,
                                 mock_get_user,
                                 mock_get_user_by_email,
                                 mock_has_permissions,
                                 fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.get(url_for(
                'main.service_delete', service_id=service_id))

        assert response.status_code == 200
        assert 'Delete this service from GOV.UK Notify' in response.get_data(as_text=True)
        assert mock_get_service.called


def test_should_show_redirect_after_deleting_service(app_,
                                                     api_user_active,
                                                     mock_get_service,
                                                     mock_get_user,
                                                     mock_get_user_by_email,
                                                     mock_login,
                                                     mock_has_permissions,
                                                     fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.post(url_for(
                'main.service_delete', service_id=service_id))

        assert response.status_code == 302
        delete_url = url_for(
            'main.service_delete_confirm', service_id=service_id, _external=True)
        assert delete_url == response.location


def test_should_show_delete_confirmation(app_,
                                         api_user_active,
                                         mock_get_service,
                                         mock_get_user,
                                         mock_get_user_by_email,
                                         mock_login,
                                         mock_has_permissions,
                                         fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.get(url_for(
                'main.service_delete_confirm', service_id=service_id))

        assert response.status_code == 200
        assert 'Delete this service from Notify' in response.get_data(as_text=True)
        assert mock_get_service.called


def test_should_redirect_delete_confirmation(app_,
                                             api_user_active,
                                             mock_get_service,
                                             mock_delete_service,
                                             mock_get_user,
                                             mock_get_user_by_email,
                                             mock_login,
                                             mock_verify_password,
                                             mock_has_permissions,
                                             fake_uuid):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            service_id = fake_uuid
            response = client.post(url_for(
                'main.service_delete_confirm', service_id=service_id))

        assert response.status_code == 302
        choose_url = url_for(
            'main.choose_service', _external=True)
        assert choose_url == response.location
        assert mock_get_service.called
        assert mock_delete_service.called


def test_route_permissions(mocker, app_, api_user_active, service_one):
    routes = [
        'main.service_settings',
        'main.service_name_change',
        'main.service_name_change_confirm',
        'main.service_request_to_go_live',
        'main.service_status_change',
        'main.service_status_change_confirm',
        'main.service_delete',
        'main.service_delete_confirm']
    with app_.test_request_context():
        for route in routes:
            validate_route_permission(
                mocker,
                app_,
                "GET",
                200,
                url_for(route, service_id=service_one['id']),
                ['manage_settings'],
                api_user_active,
                service_one)


def test_route_invalid_permissions(mocker, app_, api_user_active, service_one):
    routes = [
        'main.service_settings',
        'main.service_name_change',
        'main.service_name_change_confirm',
        'main.service_request_to_go_live',
        'main.service_status_change',
        'main.service_status_change_confirm',
        'main.service_delete',
        'main.service_delete_confirm']
    with app_.test_request_context():
        for route in routes:
            validate_route_permission(
                mocker,
                app_,
                "GET",
                403,
                url_for(route, service_id=service_one['id']),
                ['blah'],
                api_user_active,
                service_one)


def test_route_for_platform_admin(mocker, app_, platform_admin_user, service_one):
    routes = [
        'main.service_settings',
        'main.service_name_change',
        'main.service_name_change_confirm',
        'main.service_request_to_go_live',
        'main.service_status_change',
        'main.service_status_change_confirm',
        'main.service_delete',
        'main.service_delete_confirm'
        ]
    with app_.test_request_context():
        for route in routes:
            validate_route_permission(mocker,
                                      app_,
                                      "GET",
                                      200,
                                      url_for(route, service_id=service_one['id']),
                                      [],
                                      platform_admin_user,
                                      service_one)


def test_set_reply_to_email_address(app_,
                                    active_user_with_permissions,
                                    mocker,
                                    mock_update_service,
                                    service_one):
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            data = {"email_address": "test@someservice.gov.uk"}
            response = client.post(url_for('main.service_set_reply_to_email', service_id=service_one['id']),
                                   data=data,
                                   follow_redirects=True)
        assert response.status_code == 200
        mock_update_service.assert_called_with(service_one['id'],
                                               service_one['name'],
                                               service_one['active'],
                                               service_one['message_limit'],
                                               service_one['restricted'],
                                               ANY,
                                               service_one['email_from'],
                                               "test@someservice.gov.uk")


def test_if_reply_to_email_address_set_then_form_populated(app_,
                                                           active_user_with_permissions,
                                                           mocker,
                                                           service_one):

    service_one['reply_to_email_address'] = 'test@service.gov.uk'
    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(active_user_with_permissions, mocker, service_one)
            response = client.get(url_for('main.service_set_reply_to_email', service_id=service_one['id']))

        assert response.status_code == 200
        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        assert page.find(id='email_address')['value'] == 'test@service.gov.uk'
