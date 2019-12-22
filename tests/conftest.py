import pytest
from app import create_app, db



@pytest.fixture(scope='module')
def network_engineer():
    return {
        'first_name': 'Сетевой',
        'last_name': 'Инженер',
        'email': 'net_eng@test.com',
        'password': 'cat'
        }


@pytest.fixture(scope='module')
def switch():
    return {
        'manufacturer': 'testmanufacturer',
        'model': 'testmanufacturer_testmodel',
        'port_names': '1,2,3,4,5,6,7,8,9,10',
        'firmware': '1234',
        'template': 'testmanufacturer_testmodel.html'
        }


@pytest.fixture(scope='module')
def mku():
    return {
        'name': 'mku-test',
        'network': '1.1.1.0/24',
        'gateway': '1.1.1.254',
        'mng_vlan': '99'
        }


@pytest.fixture(scope='module')
def test_client():
    app = create_app('testing')
    testing_client = app.test_client(use_cookies=True)
    app_context = app.app_context()
    app_context.push()
    yield testing_client
    app_context.pop()


@pytest.fixture(scope='module')
def test_db():
    # Create the database and the database table
    db.create_all()
    yield db  # this is where the testing happens!
    db.drop_all()
