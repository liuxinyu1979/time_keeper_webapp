from time_management.timekeeperdao import TimeKeeperDao
import pytest
# https://pypi.org/project/pytest-mock/

def test_create_timekeeperdao(app_db):
    test_app, mongo_client, mocker = app_db

    fake_db_exist = True
    mocker.patch('time_management.timekeeperdao.TimeKeeperDao.init_with_db', return_value=fake_db_exist)

    tkd = TimeKeeperDao(mongo_client=mongo_client)
    assert tkd.mongo == mongo_client
    assert tkd.db_exist == fake_db_exist


