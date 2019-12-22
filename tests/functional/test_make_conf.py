from app.models import (User, Role, SwitchModel, MKUInfo,
                        MandatoryVlan, PCV)
from app.makeconf.forms import (MakeConfigForm1, MakeConfigForm2, 
                                 MakeConfigForm3)
import ipaddress


def test_make_conf_page(test_client, test_db, network_engineer,
                        switch, mku):
    user = User(**network_engineer)
    Role.insert_roles()
    role = Role.query.filter_by(name='Network_engineer').first()
    user.role = role

    switch_model = SwitchModel(**switch)
    mku_info = MKUInfo(**mku)

    test_db.session.add_all([user, switch_model, mku_info])
    test_db.session.commit()

    pcv_test_group = 10
    pcv_vlans = [
        str(vlan) 
        for vlan in PCV.get_pcv_group(pcv_test_group)
        ]
    all_vlans = f'{mku_info.mng_vlan},{MandatoryVlan.ur_pppoe},{",".join(pcv_vlans)},{MandatoryVlan.multicast}'
    port_names = switch_model.port_names.split(',')
    result = {
        'hostname': 'pushkina,200',
        'ipaddress': str(next(ipaddress.IPv4Network(mku_info.network).hosts())),
        'netmask': mku_info.netmask,
        'gateway': mku_info.gateway, 
        'mng_vlan': mku_info.mng_vlan,
        'client_ports': f'{port_names[0]}-{port_names[-2]}',
        'pppoe_single_vlan': '',
        'switches_ports_uplink': f'{port_names[-1]}',
        'switches_ports': f'{port_names[-2]}-{port_names[-1]}', 
        'switches_ports_vlans': all_vlans,
        }

    response = test_client.get('/make_conf/switch')
    assert response.status_code == 302, (
        'получилось зайти без авторизации'
        )

    test_client.post('/auth/login', data={
        'email': network_engineer['email'],
        'password': network_engineer['password']
        })

    response = test_client.get('/make_conf/switch')
    assert response.status_code == 200, (
        'не удалось зайти на страницу после авторизации'
        )
    assert 'Шаг 1' in response.get_data(as_text=True), (
        'не отрисовано поле "Шаг 1" на странице'
        )
    assert switch_model.model in response.get_data(as_text=True), (
        f'Нет модели коммутатора {switch_model.model} на странице'
        )
    assert mku_info.name in response.get_data(as_text=True), (
        f'Нет мку {mku_info.name} на странице'
        )

    response = test_client.post('/make_conf/switch', data={
            'sw_model': switch_model.id,
            'mku_name': mku_info.id,
            'submit1': 'Следующий шаг'
        }, follow_redirects=True)
    assert 'Шаг 2' in response.get_data(as_text=True), (
            f'не отрисовано поле "Шаг 2" на странице'
            )
    assert mku_info.netmask in response.get_data(as_text=True), (
            f'Нет маски подсети {mku_info.netmask} соответствующей МКУ'
            )
    assert mku_info.gateway in response.get_data(as_text=True), (
            f'Нет шлюза по умолчанию {mku_info.gateway} соответствующей МКУ'
            )
    assert str(mku_info.mng_vlan) in response.get_data(as_text=True), (
            f'Нет влана управления {mku_info.mng_vlan} соответствующей МКУ'
            )

    response = test_client.post('/make_conf/switch', data={
        'hostname': result['hostname'],
        'ipaddress': result['ipaddress'],
        'netmask': result['netmask'],
        'gateway': result['gateway'], 
        'mng_vlan': result['mng_vlan'],
        'client_ports': result['client_ports'],
        'vlan_character': 'PCV',
        'PCV_group': str(pcv_test_group),
        'pppoe_single_vlan': '',
        'submit2': 'Следующий шаг'
        },  follow_redirects=True)
    assert 'Шаг 3' in response.get_data(as_text=True), (
            f'не отрисовано поле "Шаг 3" на странице'
        )
    assert all_vlans in response.get_data(as_text=True), (
            'Нет всех выбранных вланов на странице'
        )

    response = test_client.post('/make_conf/switch', data={
        'switches_ports_uplink': result['switches_ports_uplink'],
        'switches_ports': result['switches_ports'], 
        'switches_ports_vlans': result['switches_ports_vlans'],
        'submit3': 'Сгенерировать конфиг'
        }, follow_redirects=True)
    print(response.get_data(as_text=True))
    assert 'конфиг для коммутатора' in response.get_data(as_text=True), (
        f'не отрисовано поле "конфиг для коммутатора" на странице'
        )
    # 
    # for key, value in result.items():
    #     assert f'{key}:{value}' in response.get_data(as_text=True), (
    #     f'в итоговый конфиг не попали значения {key}:{value}'
    #     )
