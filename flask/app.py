from flask import Flask, render_template, request, redirect, url_for, jsonify
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import pymysql
from ssh_conn import execute_command_on_vm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'auhue'

def connect():
    try:
        connection = pymysql.connect(
            user='user1',
            # password = 'test',
            # host = '10.120.0.209',
            password = '2ndSemester',
            host = '192.168.1.12',
            port=3306,
            database = 'customer_satisfaction')
        print("connected to database")
        return connection
        
    except pymysql.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        return None
    
def generate_pie_chart(data_dict):
    labels = list(data_dict.keys())
    data = list(data_dict.values())
    colors = ['#4CAF50', '#FFC107', '#F44336']

    fig, ax = plt.subplots()
    wedges, _ = ax.pie(data, labels=None, colors=colors, startangle=90)

    # Display labels on the corner
    legend_labels = [f'{label}: {data_dict[label]}' for label in labels]
    ax.legend(wedges, legend_labels, title='Labels', loc='upper left', bbox_to_anchor=(1, 1))

    ax.axis('equal') 

    image_stream = BytesIO()
    plt.savefig(image_stream, format='png', bbox_inches='tight')
    image_stream.seek(0)
    plt.close()

    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')

    return f"data:image/png;base64, {encoded_image}"

def generate_bar_chart(data_dict):
    labels = list(data_dict.keys())
    data = list(data_dict.values())
    colors = ['#4CAF50', '#FFC107', '#F44336']

    fig, ax = plt.subplots()
    ax.bar(labels, data, color=colors)

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format='png')
    image_stream.seek(0)
    plt.close()

    # Convert the image to base64 for embedding in HTML
    encoded_image = base64.b64encode(image_stream.read()).decode('utf-8')

    return f"data:image/png;base64, {encoded_image}"

def get_statistic(location = None):
    data = {'pleased': 0, 'neutral': 0, 'displeased': 0}
    conn = connect()
    cur = conn.cursor()
    for label in data.keys():
        if location:
            get_amount = f"SELECT COUNT(*) FROM ratings where feedback = '{label}' and location = '{location}';"
        else:
            get_amount = f"SELECT COUNT(*) FROM ratings where feedback = '{label}';"

        cur.execute(get_amount)
        amount = cur.fetchone()[0]
        data[label] = amount
    
    conn.commit()
    conn.close()

    return data

def get_raw_data(amount, location = None):
    conn = connect()
    cur = conn.cursor()

    if location:
        query = f"""SELECT feedback, 
            time, date, location from ratings WHERE location = '{location}' order by date desc,  
            time desc limit {amount};"""
    else:
        query = f"""SELECT feedback, 
            time, date, location from ratings order by date desc,  
            time desc limit {amount};"""
        
    cur.execute(query)
    data = cur.fetchall()
    result = []
    for tup in data:
        temp_dict = {"feedback": tup[0],
                     "time": tup[1],
                     "date": tup[2],
                     "region": tup[3], }
        result.append(temp_dict)

    conn.commit()
    conn.close()


    return result


@app.route('/')
def base():
    return render_template('base.html')


@app.route('/total')
def total():
    data = get_statistic()
    latest_data = get_raw_data(5)

    if sum(data.values()) == 0:
        pie_chart_data = "No data available"
        bar_chart_data = "No data available"
    else:
        pie_chart_data = generate_pie_chart(data)
        bar_chart_data = generate_bar_chart(data)

    return render_template('total.html', 
                           pie_chart_data=pie_chart_data, 
                           bar_chart_data=bar_chart_data, 
                           data=data, 
                           latest_data=latest_data)


@app.route('/per_region')
def per_region():
    locations = ['3A:7F:2E:9C:1', '4A:7F:2E:9C:1']
    data_1 = get_statistic(locations[0])
    data_2 = get_statistic(locations[1])
    latest_data_1 = get_raw_data(5, locations[0])
    latest_data_2 = get_raw_data(5, locations[1])

    if sum(data_1.values()) == 0:
        pie_chart_data_1 = "No data available"
        bar_chart_data_1 = "No data available"
    else:
        pie_chart_data_1 = generate_pie_chart(data_1)
        bar_chart_data_1 = generate_bar_chart(data_1)
        


    if sum(data_2.values()) == 0:
        pie_chart_data_2 = "No data available"
        bar_chart_data_2 = "No data available"
    else:
        pie_chart_data_2 = generate_pie_chart(data_2)
        bar_chart_data_2 = generate_bar_chart(data_2)

    return render_template('per_region.html', 
                           pie_chart_data_1=pie_chart_data_1, 
                           bar_chart_data_1=bar_chart_data_1,
                           pie_chart_data_2 = pie_chart_data_2,
                           bar_chart_data_2 = bar_chart_data_2,
                           data_1 = data_1,
                           data_2 = data_2,
                           latest_data_1 = latest_data_1,
                           latest_data_2 = latest_data_2)


@app.route('/raw_data', methods=['GET', 'POST'])
def raw_data():
    row_count = 1000
    if request.method == 'POST':
        row_count = int(request.form.get('row_count', 1000))

    data = get_raw_data(row_count)
    return render_template('raw_data.html', data=data, row_count=row_count)

def check_credentials(username, password):
    return username == 'admin' and password == 'test'


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        admin_username = request.form['admin_username']
        admin_password = request.form['admin_password']

        if check_credentials(admin_username, admin_password):
            return render_template('admin.html', device_status=get_device_status())
    
    return render_template('login.html')


def get_device_status():
    device_status = {
        'Mqtt_Broker': execute_command_on_vm('Mqtt_Broker'),
        'Mqtt_Sub': execute_command_on_vm('Mqtt_Sub'),
        'Database': execute_command_on_vm('Database'),
    }
    return device_status



@app.route('/admin/toggle', methods=['POST'])
def toggle_device():
    device_status = get_device_status()
    device = request.form.get('device')
    if device == 'Mqtt_Sub':
        temp = device_status[device]
        if temp == 'Off':
            execute_command_on_vm('start')
        elif temp == 'On':
            execute_command_on_vm('stop')

    
    return render_template('admin.html', device_status=get_device_status())




if __name__ == '__main__':
    app.run(debug=True)
