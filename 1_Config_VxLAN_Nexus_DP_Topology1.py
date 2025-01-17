from nornir import InitNornir
from nornir_utils.plugins.functions import print_result
from nornir_scrapli.tasks import send_configs
from nornir_jinja2.plugins.tasks import template_file
from nornir_utils.plugins.tasks.data import load_yaml
import os
from rich import print
import ipdb

nr = InitNornir (config_file="Inventory/config.yaml")

# Clearing the Screen
os.system('clear')

'''
this program will configure VxLAN with Data Plane Address Learning (Flood & Learn mechanisum) 
This Program will configure/automate only Spine/Leaf switches, vIOS-RTR will be configured as manually
Prerequisite: VAR Files and J2 templates 

DP Learning is also called Flood  & Learn
DP only support to bridge L2 VNI
DP does not support Inter VNI or Integrated Routing Bridging, for Inter VNI we need Router

Variable Files: load variable from VARS(variable files), VARS are define for each host
'''
def config_device_interfaces_j2_template(task):
    int_cfg_template = task.run (task=template_file, template=f"config_dev_int.j2", path=f"J2_Templates/{task.host.platform}")
    task.host['dev_int_cfg'] = int_cfg_template.result
    dev_int_cfg_rendered = task.host['dev_int_cfg']
    dev_int_config = dev_int_cfg_rendered.splitlines()
    task.run (task=send_configs, configs=dev_int_config)

def config_vxlan_basic_j2_template(task):
    vxlan_basic_cfg_template = task.run (task=template_file, template=f"vxlan_basic.j2", path=f"J2_Templates/{task.host.platform}")
    task.host['dev_vxlan_basic_cfg'] = vxlan_basic_cfg_template.result
    dev_vxlan_basic_cfg_rendered = task.host['dev_vxlan_basic_cfg']
    dev_vxlan_basic_config = dev_vxlan_basic_cfg_rendered.splitlines()
    task.run (task=send_configs, configs=dev_vxlan_basic_config)

def config_ospf_j2_template(task):
    ospf_cfg_template = task.run (task=template_file, template=f"config_dev_ospf.j2", path=f"J2_Templates/{task.host.platform}")
    task.host['dev_ospf_cfg'] = ospf_cfg_template.result
    dev_ospf_cfg_rendered = task.host['dev_ospf_cfg']
    dev_ospf_config = dev_ospf_cfg_rendered.splitlines()
    task.run (task=send_configs, configs=dev_ospf_config)

def config_iBGP_j2_template(task):
    iBGP_cfg_template = task.run (task=template_file, template=f"bgp.j2", path=f"J2_Templates/{task.host.platform}")
    task.host['dev_bgp_cfg'] = iBGP_cfg_template.result
    dev_bgp_cfg_rendered = task.host['dev_bgp_cfg']
    dev_bgp_config = dev_bgp_cfg_rendered.splitlines()
    task.run (task=send_configs, configs=dev_bgp_config)

def config_VxLAN_Nexus_DP (task):
    # First of all we need to load variables (vars) for hosts using load_yaml, 
    
    # it will return yaml data and store in dictionary form and embend into dic key for each specific device 
    dev_data = task.run (task=load_yaml, file=f"./Hosts_VARS/{task.host.platform}/{task.host}.yaml")
    task.host['dev_vars'] = dev_data.result

    # it will return yaml data and store in dictionary form, 
    # These are commond variables for all devices and used to generate commond configurations for all devices
    common_data = task.run (task=load_yaml, file=f"./Hosts_VARS/{task.host.platform}/common_vars.yaml")
    task.host['common_vars'] = common_data.result
    #Now vars are loaded, Lets configure Devices, in our lab we will configuration 

    # Enabled all required featured for VxLAN, Underlay OSPF process, Multicast using j2 template
    # We will also enable Jumbo frame because VxLAN packet is extended with extra headers to avoid fragmentation
    config_vxlan_basic_j2_template(task)

    
    # Interface level configuration (IP add, OSPF, pim etc.using j2 template
    config_device_interfaces_j2_template(task)

    
    # iBGP required TCP/IP reachability to neighbors so we need to configure any IGP
    # OSPF configurations using j2 template for iBGP peer reachability
    #config_ospf_j2_template(task)
    
    # iBGP configuration using j2 template
    #config_iBGP_j2_template(task)
    

results = nr.run (task=config_VxLAN_Nexus_DP)
print_result (results)
#ipdb.set_trace()