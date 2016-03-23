import pytest
from app.utils import user_has_permissions
from app.main.views.index import index
from werkzeug.exceptions import Forbidden
from flask import request


def _test_permissions(app_, usr, permissions, service_id, will_succeed, or_=False, admin_override=False):
    with app_.test_request_context() as ctx:
        request.view_args.update({'service_id': service_id})
        with app_.test_client() as client:
            client.login(usr)
            decorator = user_has_permissions(*permissions, or_=or_, admin_override=admin_override)
            decorated_index = decorator(index)
            if will_succeed:
                response = decorated_index()
            else:
                try:
                    response = decorated_index()
                    pytest.fail("Failed to throw a forbidden exception")
                except Forbidden:
                    pass


def test_user_has_permissions_on_endpoint_fail(app_, mocker):
    user = _user_with_permissions()
    mocker.patch('app.user_api_client.get_user', return_value=user)
    _test_permissions(
        app_,
        user,
        ['something'],
        '',
        False)


def test_user_has_permissions_success(app_,
                                      mocker):
    user = _user_with_permissions()
    mocker.patch('app.user_api_client.get_user', return_value=user)
    _test_permissions(
        app_,
        user,
        ['manage_users'],
        '',
        True)


def test_user_has_permissions_or(app_, mocker):
    user = _user_with_permissions()
    mocker.patch('app.user_api_client.get_user', return_value=user)
    _test_permissions(
        app_,
        user,
        ['something', 'manage_users'],
        '',
        True,
        or_=True)


def test_user_has_permissions_multiple(app_,
                                       mocker):
    user = _user_with_permissions()
    mocker.patch('app.user_api_client.get_user', return_value=user)
    _test_permissions(
        app_,
        user,
        ['manage_templates', 'manage_users'],
        '',
        will_succeed=True)


def test_exact_permissions(app_,
                           mocker):
    user = _user_with_permissions()
    mocker.patch('app.user_api_client.get_user', return_value=user)
    _test_permissions(
        app_,
        user,
        ['manage_users', 'manage_templates', 'manage_settings'],
        '',
        True)


def test_platform_admin_user_can_access_page(app_,
                                             platform_admin_user,
                                             mocker):
    mocker.patch('app.user_api_client.get_user', return_value=platform_admin_user)
    _test_permissions(
        app_,
        platform_admin_user,
        [],
        '',
        will_succeed=True,
        admin_override=True)


def test_platform_admin_user_can_not_access_page(app_,
                                                 platform_admin_user,
                                                 mocker):
    mocker.patch('app.user_api_client.get_user', return_value=platform_admin_user)
    _test_permissions(
        app_,
        platform_admin_user,
        [],
        '',
        will_succeed=False,
        admin_override=False)


def _user_with_permissions():
    from app.notify_client.user_api_client import User

    user_data = {'id': 999,
                 'name': 'Test User',
                 'password': 'somepassword',
                 'email_address': 'test@user.gov.uk',
                 'mobile_number': '+4412341234',
                 'state': 'active',
                 'failed_login_count': 0,
                 'permissions': {'': ['manage_users', 'manage_templates', 'manage_settings']},
                 'platform_admin': False
                 }
    user = User(user_data)
    return user
