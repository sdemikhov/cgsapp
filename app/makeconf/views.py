from flask import render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app import db
from . import make_conf
from .. decorators import permission_required
from ..models import (Permission, MKUInfo, SwitchModel, 
                      StorageForMakeConfig, PCV, MandatoryVlan)
from .forms import MakeConfigForm1, MakeConfigForm2, MakeConfigForm3
from ..common_functions import convert_to_list


def check_params(storage, params):
    for param in params:
        if not getattr(storage, param):
            return False
    return True


def generate_data_for_template(storage):
    result = {}
    need_convert = ['switches_ports_vlans',
                    'client_ports',
                    'switches_ports']
    for key, value in storage.__dict__.items():
        if not key.startswith('_') and 'id' not in key:
            if key in need_convert:
               value = convert_to_list(value)
            result[key] = value
    return result


@make_conf.route('/switch', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.SW_n_AP)
def switch():

    storage = StorageForMakeConfig.query.filter_by(
        user_id=current_user.id
        ).first()

    if storage is not None:
        if storage.step == 2:
            form3 = MakeConfigForm3()
            if form3.reset_3.data:
                db.session.delete(storage)
                db.session.commit()
                return redirect(url_for('make_conf.switch'))
            if form3.validate_on_submit() and form3.submit3.data:                
                storage.switches_ports = form3.switches_ports.data
                storage.switches_ports_vlans = form3.switches_ports_vlans.data
                storage.switches_ports_uplink = form3.switches_ports_uplink.data
                
                sw_model=SwitchModel.query.get(storage.switch_model_id)
                data = generate_data_for_template(storage)
                if storage.PCV_group:
                    data['pcv_vlans'] = PCV.get_pcv_group(storage.PCV_group)
                data['port_names'] = convert_to_list(
                    sw_model.port_names
                    )
                url = ('make_conf/switches_configuration/' + \
                    sw_model.manufacturer + '/' + \
                    sw_model.template)
                db.session.delete(storage)
                db.session.commit()
                return render_template(url, data=data)
            if storage.vlan_character == 'PCV':
                pcv_vlans = [str(vlan)
                    for vlan in PCV.get_pcv_group(storage.PCV_group)
                    ]
                form3.switches_ports_vlans.data = (
                    f'{storage.mng_vlan},{MandatoryVlan.ur_pppoe}'
                    f',{",".join(pcv_vlans)}'
                    f',{MandatoryVlan.multicast}'
                    )
            elif storage.vlan_character == 'single_vlan':
                form3.switches_ports_vlans.data = (
                    f'{storage.mng_vlan},{MandatoryVlan.ur_pppoe}'
                    f',{storage.pppoe_single_vlan}'
                    f',{MandatoryVlan.multicast}'
                    )
            return render_template('make_conf/switch.html' ,form3=form3)
        elif storage.step == 1:
            form2 = MakeConfigForm2(PCV.generate_groups())
            if form2.reset_2.data:
                db.session.delete(storage)
                db.session.commit()
                return redirect(url_for('make_conf.switch'))
            if form2.validate_on_submit() and form2.submit2.data:
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
                storage.step=2
                db.session.add(storage)
                db.session.commit()
                return redirect(url_for('make_conf.switch'))
            mku = MKUInfo.query.get(storage.mku_info_id)
            form2.gateway.data = mku.gateway
            form2.netmask.data = mku.netmask
            form2.mng_vlan.data  = mku.mng_vlan
            
            return render_template('make_conf/switch.html', form2=form2)

    mku_info_choices = [
        (mku_info.id, mku_info.name )
        for mku_info in MKUInfo.query.order_by(MKUInfo.name).all()
        ]
    switch_models_choices = [
        (sw_model.id, sw_model.model)
        for sw_model in (
            SwitchModel.query.order_by(SwitchModel.manufacturer)
            )
        ]
    form1 = MakeConfigForm1(switch_models_choices, mku_info_choices)
    
    if form1.validate_on_submit() and form1.submit1.data:
        db.session.add(StorageForMakeConfig(
                               user_id=current_user.id,
                               mku_info_id=form1.mku_name.data,
                               switch_model_id=form1.sw_model.data,
                               step=1
                               ))
        db.session.commit()
        return redirect(url_for('make_conf.switch'))
    return render_template('make_conf/switch.html' ,form1=form1)
