import paramiko

def create_ssh_client(host_addr, user, password):
    host = host_addr
    port = 22
    user = user
    password = password

    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(host, port=port, username=user, password=password)
    return client

def find_pid_by_name(process_name, ssh_client):
    command = f"pgrep -f {process_name}"
    stdin, stdout, stderr = ssh_client.exec_command(command)
    pid = stdout.read().decode().strip().split()
    return pid


def check_database_status(ssh_client):
    command = 'ps aux | grep mysql'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    process_list = stdout.read().decode()
    if 'mysqld' in process_list:
        return 'On'
    else:
        return 'Off'

def check_mqtt_sub_status(ssh_client):
    command = 'ps aux | grep mqtt_sub.py'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    process_list = stdout.read().decode()
    if 'python3 mqtt_sub.py' in process_list:
        return "On"
    else:
        return "Off"

def check_mqtt_broker_status(ssh_client):
    command = 'ps aux | grep mosquitto'
    stdin, stdout, stderr = ssh_client.exec_command(command)
    process_list = stdout.read().decode()
    if '/mosquitto/mosquitto.conf' in process_list:
        return 'On'
    else:
        return 'Off'


def start_mqtt_subscriber(ssh_client):
    try:
        cmd = 'python3 mqtt_sub.py'
        stdin, stdout, stderr = ssh_client.exec_command(cmd)
    
        print("MQTT subscriber script started.")
    finally:
        ssh_client.close()

def stop_mqtt_subscriber(ssh_client):
    pid_list = find_pid_by_name('mqtt_sub.py', ssh_client)
    for i in pid_list:
        ssh_client.exec_command(f"kill {i}")
    print('stoped mqtt')

def execute_command_on_vm(cmd):
    # host_list = {'Mqtt_Sub'   : ['10.120.0.49', 'test', 'test'],
    #              'start'      : ['10.120.0.49', 'test', 'test'],
    #              'stop'       : ['10.120.0.49', 'test', 'test'],
    #              'Mqtt_Broker': ['10.120.0.23', 'test', 'test'],
    #              'Database'   : ['10.120.0.209', 'test', 'test']
    #             }

    host_list = {'Mqtt_Sub'  : ['192.168.1.12', 'test', 'test'],
                'start'      : ['192.168.1.12', 'test', 'test'],
                'stop'       : ['192.168.1.12', 'test', 'test'],
                'Mqtt_Broker': ['172.17.185.145', 'solo', 'test'],
                'Database'   : ['192.168.1.12', 'test', 'test']
            }
    
    client = create_ssh_client(host_list[cmd][0], host_list[cmd][1], host_list[cmd][2])
    if cmd == 'start':
        start_mqtt_subscriber(client)
    elif cmd == 'stop':
        stop_mqtt_subscriber(client)
    elif cmd == 'Database':
        return check_database_status(client)
    elif cmd == 'Mqtt_Sub':
        return check_mqtt_sub_status(client)
    elif cmd == 'Mqtt_Broker':
        return check_mqtt_broker_status(client)

    
    



    

