from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from itertools import repeat

from app import db
from . import make_conf
from .. decorators import permission_required
from ..models import (Permission, MKUInfo, SwitchModel, 
                      StorageForMakeConfig, PCV, MandatoryVlan)
from .forms import MakeConfigForm1, MakeConfigForm2, MakeConfigForm3
from ..common_functions import convert_to_list, make_choices


def merge_vlans(vlans):
    result = [str(vlan) for vlan in sorted(set(vlans))]
    return ','.join(result)


@make_conf.route('/switch', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.SW_n_AP)
def switch():
    storage = StorageForMakeConfig.query.filter_by(
        user_id=current_user.id
        ).first()

    if storage is None:
        mku_info_choices = make_choices(MKUInfo, 'name', 'name')
        switch_models_choices = make_choices(SwitchModel, 'model',
                                             'manufacturer')
        form1 = MakeConfigForm1(switch_models_choices, mku_info_choices)
        if form1.validate_on_submit():
            db.session.add(StorageForMakeConfig(
                           user_id=current_user.id,
                           mku_info_id=form1.mku_name.data,
                           switch_model_id=form1.sw_model.data,
                           step='configure_client_ports'
                           ))
            db.session.commit()
            return redirect(url_for('make_conf.switch'))
        return render_template('make_conf/switch.html', form1=form1)
    elif storage.step == 'configure_client_ports':
        form2 = MakeConfigForm2(PCV.generate_groups())
        if form2.reset_2.data:
            db.session.delete(storage)
            db.session.commit()
            return redirect(url_for('make_conf.switch'))
        if form2.validate_on_submit():
            storage.hostname = form2.hostname.data
            if form2.vlan_character.data == 'PCV':
                storage.PCV_group = form2.PCV_group.data
            elif form2.vlan_character.data == 'single_vlan':
                storage.pppoe_single_vlan = form2.pppoe_single_vlan.data
            storage.vlan_character = form2.vlan_character.data
            storage.ipaddress = form2.ipaddress.data
            storage.gateway = form2.gateway.data
            storage.netmask = form2.netmask.data
            storage.mng_vlan = form2.mng_vlan.data
            storage.client_ports = form2.client_ports.data
            storage.step='configure_switches_ports'
            db.session.add(storage)
            db.session.commit()
            return redirect(url_for('make_conf.switch'))
        mku = MKUInfo.query.get(storage.mku_info_id)
        form2.gateway.data = mku.gateway
        form2.netmask.data = mku.netmask
        form2.mng_vlan.data  = mku.mng_vlan
        return render_template('make_conf/switch.html', form2=form2)
    elif storage.step == 'configure_switches_ports':
        form3 = MakeConfigForm3()
        if form3.reset_3.data:
            db.session.delete(storage)
            db.session.commit()
            return redirect(url_for('make_conf.switch'))
        if form3.validate_on_submit():
            sw_model = SwitchModel.query.get(storage.switch_model_id)

            port_names = convert_to_list(sw_model.port_names)
            client_ports = [
                int(port)
                for port in sorted(
                    set(convert_to_list(storage.client_ports)),
                    key=(lambda x:int(x))
                    )
                ]
            switches_ports = convert_to_list(form3.switches_ports.data)
            switches_vlans = convert_to_list(
                form3.switches_ports_vlans.data
                )
            uplink = form3.switches_ports_uplink.data

            data = storage.as_dict()
            data['uplink_port'] = port_names[int(uplink) - 1]
            data['switches_ports_vlans'] = [
                vlan
                for vlan in sorted(
                    switches_vlans,
                    key=(lambda x:int(x))
                    )
                ]
            data['switches_port_names'] = [
                port_names[int(port) - 1]
                for port in switches_ports
                ]
            if storage.vlan_character == 'PCV':
                client_vlans = storage.pcv_by_client_ports
            elif storage.vlan_character == 'single_vlan':
                client_vlans = repeat(storage.pppoe_single_vlan)
            data['client_port_names_with_vlans'] = {
                port_names[port - 1]: vlan
                for port, vlan in zip(client_ports, client_vlans)
                }

            url = ('make_conf/switches_configuration/' + \
                sw_model.manufacturer + '/' + sw_model.model + '.html')
                
            db.session.delete(storage)
            db.session.commit()
            return render_template(url, data=data)
        if storage.vlan_character == 'PCV':
            client_vlans = storage.pcv_by_client_ports
        elif storage.vlan_character == 'single_vlan':
            client_vlans = [storage.pppoe_single_vlan]
        form3.switches_ports_vlans.data = merge_vlans(
            client_vlans + MandatoryVlan.get_all() + [storage.mng_vlan]
            )
        return render_template('make_conf/switch.html' ,form3=form3)
