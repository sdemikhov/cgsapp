from flask import (current_app, render_template, redirect, url_for,
                   flash, request, session)
from flask_login import login_required
from wtforms import StringField, SubmitField
from wtforms.validators import IPAddress
import netmiko
import yaml
from concurrent.futures import ThreadPoolExecutor
from itertools import repeat


from . import make_intf
from .. decorators import permission_required
from ..models import Permission
from .forms import MakeIntfForm1, MakeIntfForm2


def send_config_commands(device, commands):
    with netmiko.ConnectHandler(**device) as ssh:
        result = ssh.send_config_set(commands)
        return result


@make_intf.route('/', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.BRAS)
def index():
    intf_type = session.get('intf_type')

    with open('interfaces_info.yaml') as f:
        interfaces = yaml.safe_load(f)

    if not intf_type:
        make_int_choices = [
            (interface, interface)
            for interface in interfaces
            ]
        form1 = MakeIntfForm1(make_int_choices)
        if form1.validate_on_submit():
            session['intf_type'] = form1.intf_type.data
            return redirect(url_for('make_intf.index'))
        return render_template('make_intf/index.html', form=form1)
    else:
        form2 = MakeIntfForm2()

        if not "{ip}" in interfaces[intf_type]['conf']:
            del form2.ip
        if form2.reset.data:
            del session['intf_type']
            return redirect(url_for('make_intf.index'))
        if form2.validate_on_submit():
            params = {'lag': form2.lag.data,
                      'outer_vlan': form2.outer_vlan.data,
                      'inner_vlan': form2.inner_vlan.data,
                      'description': form2.description.data}
            if form2.ip:
                params['ip'] = form2.ip.data
            commands = interfaces[session['intf_type']]['conf'].format(
                **params
                ).split('\n')
            devices = [{'device_type': interfaces[session['intf_type']]['device_type'], 
                        'host': host, 
                        'username': current_app.config['NETMIKO_USER'],
                        'password': current_app.config['NETMIKO_PASS']}
                for host in interfaces[session['intf_type']]['lag'][form2.lag.data]]
            with ThreadPoolExecutor(
                max_workers=len(interfaces[session['intf_type']]['lag'][form2.lag.data])
                ) as ex:
                f = ex.map(send_config_commands,
                                devices,
                                repeat(commands))
                result = [(device['host'], output)
                           for device, output in zip(devices, f)]
                del session['intf_type']
                return render_template('make_intf/index.html', result=result)
        return render_template('make_intf/index.html', form=form2)
