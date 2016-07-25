import copy
from flask import url_for

import pytest
from bs4 import BeautifulSoup
from freezegun import freeze_time

from app.main.views.dashboard import get_dashboard_totals

from tests import validate_route_permission
from tests.conftest import SERVICE_ONE_ID


stub_template_stats = [
    {
        'template': {
            'name': 'Brine Shrimp',
            'template_type': 'sms',
            'id': 1
        },
        'id': '6005e192-4738-4962-beec-ebd982d0b03f',
        'day': '2016-04-06',
        'usage_count': 6,
        'service': '1491b86f-c950-48f5-bed1-2a55df027ecb'
    },
    {
        'template': {
            'name': 'Pickle feet',
            'template_type': 'sms',
            'id': 2
        },
        'id': '0bd529cd-a0fd-43e5-80ee-b95ef6b0d51f',
        'day': '2016-04-06',
        'usage_count': 6,
        'service': '1491b86f-c950-48f5-bed1-2a55df027ecb'
        },
    {
        'template': {
            'name': 'Brine Shrimp',
            'template_type': 'sms',
            'id': 1
        },
        'id': '24531628-ffff-4082-a443-9f6db5af83d9',
        'day': '2016-04-05',
        'usage_count': 7,
        'service': '1491b86f-c950-48f5-bed1-2a55df027ecb'
        },
    {
        'template': {
            'name': 'Pickle feet',
            'template_type': 'sms',
            'id': 2
        },
        'id': '0bd529cd-a0fd-43e5-80ee-b95ef6b0d51f',
        'day': '2016-03-06',
        'usage_count': 200,
        'service': '1491b86f-c950-48f5-bed1-2a55df027ecb'
    },
]


def test_get_started(
    app_,
    mocker,
    api_user_active,
    mock_get_service,
    mock_get_service_templates_when_no_templates_exist,
    mock_get_service_statistics,
    mock_get_aggregate_service_statistics,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
    mock_get_jobs,
    mock_has_permissions,
    mock_get_detailed_service,
    mock_get_usage
):

    mock_template_stats = mocker.patch('app.template_statistics_client.get_template_statistics_for_service',
                                       return_value=copy.deepcopy(stub_template_stats))

    with app_.test_request_context(), app_.test_client() as client:
        client.login(api_user_active)
        response = client.get(url_for('main.service_dashboard', service_id=SERVICE_ONE_ID))

    # mock_get_service_templates_when_no_templates_exist.assert_called_once_with(SERVICE_ONE_ID)
    print(response.get_data(as_text=True))
    assert response.status_code == 200
    assert 'Get started' in response.get_data(as_text=True)


def test_get_started_is_hidden_once_templates_exist(
    app_,
    mocker,
    api_user_active,
    mock_get_service,
    mock_get_service_templates,
    mock_get_service_statistics,
    mock_get_aggregate_service_statistics,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
    mock_get_jobs,
    mock_has_permissions,
    mock_get_detailed_service,
    mock_get_usage
):
    mock_template_stats = mocker.patch('app.template_statistics_client.get_template_statistics_for_service',
                                       return_value=copy.deepcopy(stub_template_stats))
    with app_.test_request_context(), app_.test_client() as client:
        client.login(api_user_active)
        response = client.get(url_for('main.service_dashboard', service_id=SERVICE_ONE_ID))

    # mock_get_service_templates.assert_called_once_with(SERVICE_ONE_ID)
    assert response.status_code == 200
    assert 'Get started' not in response.get_data(as_text=True)


def test_should_show_recent_templates_on_dashboard(app_,
                                                   mocker,
                                                   api_user_active,
                                                   mock_get_service,
                                                   mock_get_service_templates,
                                                   mock_get_aggregate_service_statistics,
                                                   mock_get_user,
                                                   mock_get_user_by_email,
                                                   mock_login,
                                                   mock_get_jobs,
                                                   mock_has_permissions,
                                                   mock_get_detailed_service,
                                                   mock_get_usage):

    mock_template_stats = mocker.patch('app.template_statistics_client.get_template_statistics_for_service',
                                       return_value=copy.deepcopy(stub_template_stats))

    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.get(url_for('main.service_dashboard', service_id=SERVICE_ONE_ID))

        assert response.status_code == 200
        response.get_data(as_text=True)
        mock_template_stats.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        headers = [header.text.strip() for header in page.find_all('h2') + page.find_all('h1')]
        assert 'Test Service' in headers
        assert 'In the last 7 days' in headers

        table_rows = page.find_all('tbody')[0].find_all('tr')

        assert len(table_rows) == 2

        assert 'Pickle feet' in table_rows[0].find_all('th')[0].text
        assert 'Text message template' in table_rows[0].find_all('th')[0].text
        assert '206' in table_rows[0].find_all('td')[0].text

        assert 'Brine Shrimp' in table_rows[1].find_all('th')[0].text
        assert 'Text message template' in table_rows[1].find_all('th')[0].text
        assert '13' in table_rows[1].find_all('td')[0].text


def test_should_show_all_templates_on_template_statistics_page(
    app_,
    mocker,
    api_user_active,
    mock_get_service,
    mock_get_service_templates,
    mock_get_service_statistics,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
    mock_get_jobs,
    mock_has_permissions
):

    mock_template_stats = mocker.patch('app.template_statistics_client.get_template_statistics_for_service',
                                       return_value=copy.deepcopy(stub_template_stats))

    with app_.test_request_context():
        with app_.test_client() as client:
            client.login(api_user_active)
            response = client.get(url_for('main.template_history', service_id=SERVICE_ONE_ID))

        assert response.status_code == 200
        response.get_data(as_text=True)
        mock_template_stats.assert_called_once_with(SERVICE_ONE_ID)

        page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
        table_rows = page.find_all('tbody')[0].find_all('tr')

        assert len(table_rows) == 2

        assert 'Pickle feet' in table_rows[0].find_all('th')[0].text
        assert 'Text message template' in table_rows[0].find_all('th')[0].text
        assert '206' in table_rows[0].find_all('td')[0].text

        assert 'Brine Shrimp' in table_rows[1].find_all('th')[0].text
        assert 'Text message template' in table_rows[1].find_all('th')[0].text
        assert '13' in table_rows[1].find_all('td')[0].text


@freeze_time("2016-01-01 11:09:00.061258")
def test_should_show_recent_jobs_on_dashboard(
    app_,
    mocker,
    api_user_active,
    mock_get_service,
    mock_get_service_templates,
    mock_get_service_statistics,
    mock_get_aggregate_service_statistics,
    mock_get_user,
    mock_get_user_by_email,
    mock_login,
    mock_get_template_statistics,
    mock_get_detailed_service,
    mock_get_jobs,
    mock_has_permissions,
    mock_get_usage
):

    with app_.test_request_context(), app_.test_client() as client:
        client.login(api_user_active)
        response = client.get(url_for('main.service_dashboard', service_id=SERVICE_ONE_ID))

    mock_get_jobs.assert_called_once_with(SERVICE_ONE_ID, limit_days=7)
    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    table_rows = page.find_all('tbody')[1].find_all('tr')

    assert "Test message" not in page.text
    assert len(table_rows) == 4

    for index, filename in enumerate((
        "export 1/1/2016.xls",
        "all email addresses.xlsx",
        "applicants.ods",
        "thisisatest.csv",
    )):
        assert filename in table_rows[index].find_all('th')[0].text
        assert 'Uploaded 1 January at 11:09' in table_rows[index].find_all('th')[0].text
        for column_index, count in enumerate((1, 0, 0)):
            assert table_rows[index].find_all('td')[column_index].text.strip() == str(count)


def _test_dashboard_menu(mocker, app_, usr, service, permissions):
    with app_.test_request_context():
        with app_.test_client() as client:
            usr._permissions[str(service['id'])] = permissions
            mocker.patch('app.user_api_client.check_verify_code', return_value=(True, ''))
            mocker.patch('app.service_api_client.get_services', return_value={'data': [service]})
            mocker.patch('app.user_api_client.get_user', return_value=usr)
            mocker.patch('app.user_api_client.get_user_by_email', return_value=usr)
            mocker.patch('app.service_api_client.get_service', return_value={'data': service})
            mocker.patch('app.statistics_api_client.get_statistics_for_service', return_value={'data': [{}]})
            client.login(usr)
            return client.get(url_for('main.service_dashboard', service_id=service['id']))


def test_menu_send_messages(mocker,
                            app_,
                            api_user_active,
                            service_one,
                            mock_get_service_templates,
                            mock_get_jobs,
                            mock_get_template_statistics,
                            mock_get_detailed_service,
                            mock_get_usage):

    with app_.test_request_context():
        resp = _test_dashboard_menu(
            mocker,
            app_,
            api_user_active,
            service_one,
            ['view_activity', 'send_texts', 'send_emails', 'send_letters'])
        page = resp.get_data(as_text=True)
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='email')in page
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='sms')in page
        assert url_for('main.manage_users', service_id=service_one['id']) in page
        assert url_for('main.documentation') in page

        assert url_for('main.service_settings', service_id=service_one['id']) not in page
        assert url_for('main.api_keys', service_id=service_one['id']) not in page
        assert url_for('main.show_all_services') not in page
        assert url_for('main.view_providers') not in page


def test_menu_manage_service(mocker,
                             app_,
                             api_user_active,
                             service_one,
                             mock_get_service_templates,
                             mock_get_jobs,
                             mock_get_template_statistics,
                             mock_get_detailed_service,
                             mock_get_usage):
    with app_.test_request_context():
        resp = _test_dashboard_menu(
            mocker,
            app_,
            api_user_active,
            service_one,
            ['view_activity', 'manage_users', 'manage_templates', 'manage_settings'])
        page = resp.get_data(as_text=True)
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='email') in page
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='sms') in page
        assert url_for('main.manage_users', service_id=service_one['id']) in page
        assert url_for('main.service_settings', service_id=service_one['id']) in page
        assert url_for('main.documentation') in page

        assert url_for('main.api_keys', service_id=service_one['id']) not in page
        assert url_for('main.show_all_services') not in page


def test_menu_manage_api_keys(mocker,
                              app_,
                              api_user_active,
                              service_one,
                              mock_get_service_templates,
                              mock_get_jobs,
                              mock_get_template_statistics,
                              mock_get_detailed_service,
                              mock_get_usage):
    with app_.test_request_context():
        resp = _test_dashboard_menu(
            mocker,
            app_,
            api_user_active,
            service_one,
            ['view_activity', 'manage_api_keys'])
        page = resp.get_data(as_text=True)
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='email') in page
        assert url_for(
            'main.choose_template',
            service_id=service_one['id'],
            template_type='sms') in page
        assert url_for('main.manage_users', service_id=service_one['id']) in page
        assert url_for('main.service_settings', service_id=service_one['id']) not in page
        assert url_for('main.show_all_services') not in page

        assert url_for('main.api_keys', service_id=service_one['id']) in page


def test_menu_all_services_for_platform_admin_user(mocker,
                                                   app_,
                                                   platform_admin_user,
                                                   service_one,
                                                   mock_get_service_templates,
                                                   mock_get_jobs,
                                                   mock_get_template_statistics,
                                                   mock_get_detailed_service,
                                                   mock_get_usage):
    with app_.test_request_context():
        resp = _test_dashboard_menu(
            mocker,
            app_,
            platform_admin_user,
            service_one,
            [])
        page = resp.get_data(as_text=True)
        assert url_for('main.choose_template', service_id=service_one['id'], template_type='sms') in page
        assert url_for('main.choose_template', service_id=service_one['id'], template_type='email') in page
        assert url_for('main.manage_users', service_id=service_one['id']) in page
        assert url_for('main.service_settings', service_id=service_one['id']) in page
        assert url_for('main.view_notifications', service_id=service_one['id'], message_type='email') in page
        assert url_for('main.view_notifications', service_id=service_one['id'], message_type='sms') in page
        assert url_for('main.api_keys', service_id=service_one['id']) not in page


def test_route_for_service_permissions(mocker,
                                       app_,
                                       api_user_active,
                                       service_one,
                                       mock_get_service,
                                       mock_get_user,
                                       mock_get_service_templates,
                                       mock_get_jobs,
                                       mock_get_service_statistics,
                                       mock_get_template_statistics,
                                       mock_get_detailed_service,
                                       mock_get_usage):
    routes = [
        'main.service_dashboard']
    with app_.test_request_context():
        # Just test that the user is part of the service
        for route in routes:
            validate_route_permission(
                mocker,
                app_,
                "GET",
                200,
                url_for(
                    route,
                    service_id=service_one['id']),
                ['view_activity'],
                api_user_active,
                service_one)


def test_aggregate_template_stats():
    from app.main.views.dashboard import aggregate_usage
    expected = aggregate_usage(copy.deepcopy(stub_template_stats))

    assert len(expected) == 2
    for item in expected:
        if item['template'].id == 1:
            assert item['usage_count'] == 13
        elif item['template'].id == 2:
            assert item['usage_count'] == 206


def test_service_dashboard_updates_gets_dashboard_totals(mocker,
                                                         app_,
                                                         active_user_with_permissions,
                                                         service_one,
                                                         mock_get_user,
                                                         mock_get_service_templates,
                                                         mock_get_template_statistics,
                                                         mock_get_detailed_service,
                                                         mock_get_jobs,
                                                         mock_get_service_statistics,
                                                         mock_get_usage):
    dashboard_totals = mocker.patch('app.main.views.dashboard.get_dashboard_totals', return_value={
        'email': {'requested': 123, 'delivered': 0, 'failed': 0},
        'sms': {'requested': 456, 'delivered': 0, 'failed': 0}
    })

    with app_.test_request_context(), app_.test_client() as client:
        client.login(active_user_with_permissions, mocker, service_one)
        response = client.get(url_for('main.service_dashboard', service_id=SERVICE_ONE_ID))

    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode('utf-8'), 'html.parser')
    numbers = [number.text.strip() for number in page.find_all('div', class_='big-number-number')]
    assert '123' in numbers
    assert '456' in numbers

    table_rows = page.find_all('tbody')[0].find_all('tr')


def test_get_dashboard_totals_adds_percentages():
    stats = {
        'sms': {
            'requested': 3,
            'delivered': 0,
            'failed': 2
        },
        'email': {
            'requested': 0,
            'delivered': 0,
            'failed': 0
        }
    }
    assert get_dashboard_totals(stats)['sms']['failed_percentage'] == '66.7'
    assert get_dashboard_totals(stats)['email']['failed_percentage'] == '0'


@pytest.mark.parametrize(
    'failures,expected', [
        (2, False),
        (3, False),
        (4, True)
    ]
)
def test_get_dashboard_totals_adds_warning(failures, expected):
    stats = {
        'sms': {
            'requested': 100,
            'delivered': 0,
            'failed': failures
        }
    }
    assert get_dashboard_totals(stats)['sms']['show_warning'] == expected
