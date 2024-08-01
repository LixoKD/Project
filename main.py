import paho.mqtt.client as mqtt
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import pandas as pd
import json
import plotly.graph_objs as go

# MQTT setup
def on_message(client, userdata, message):
    try:
        payload = message.payload.decode('utf-8')  # ใช้ 8 bit หรือ UTF-8 decoding
        print(f"Received message: {payload}")  # Print received message for debugging
        
        # Append message to text file
        with open('mqtt_data.txt', 'a', encoding='utf-8') as f:
            f.write(payload + '\n')
    except Exception as e:
        print(f"Error in on_message: {e}")

# Setup MQTT client
client = mqtt.Client()
client.on_message = on_message

# Connect to MQTT Broker
broker = "broker.hivemq.com"  # Change this to your MQTT broker address
port = 1883
client.connect(broker, port, 60)

# Subscribe to a topic
topic = "sensor/data"
client.subscribe(topic)

# Start the loop
client.loop_start()

# Function to read data from the text file
def read_data_from_file():
    data = {'UPS': [], 'Status': []}
    try:
        with open('mqtt_data.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    json_data = json.loads(line.strip())
                    data['UPS'].append(json_data.get("UPS"))
                    data['Status'].append(json_data.get("Status"))
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from line: {line.strip()}") #เวลามันรับค่ามาจาก mqttแล้วไม่ได้จะทำการprintแสดง
    except FileNotFoundError:
        print("File not found. Make sure the data file exists.")
    return pd.DataFrame(data)

# Initialize the Dash app
app = dash.Dash(__name__)

# Layout of the dashboard 
app.layout = html.Div([
    html.H1("Dashboard UPS", style={
        'textAlign': 'center',
        'color': '#333333',
        'fontFamily': 'Arial',
        'padding': '20px',
        'backgroundColor': '#f9f9f9',
        'margin': '0 auto',
        'width': '90%',
        'maxWidth': '1200px',
        'borderRadius': '8px',
        'border': '1px solid #cccccc'
    }),
    
    html.Div([
        dcc.Graph(id='ups-status-graph', style={
            'height': '70vh',  # Use viewport height for better scaling
            'width': '100%',   # Full width of container
            'border': '1px solid #cccccc',
            'borderRadius': '8px',
            'boxShadow': '0px 0px 5px rgba(0, 0, 0, 0.1)',
            'overflow': 'hidden'  # Hide overflow
        }),
        html.Div(id='summary', style={
            'padding': '20px',
            'backgroundColor': '#ffffff',
            'border': '1px solid #cccccc',
            'borderRadius': '8px',
            'boxShadow': '0px 0px 5px rgba(0, 0, 0, 0.1)',
            'margin': '20px auto 0 auto',
            'width': '90%',
            'maxWidth': '1200px'
        })
    ], style={
        'padding': '20px',
        'backgroundColor': '#ffffff',
        'border': '1px solid #cccccc',
        'borderRadius': '8px',
        'boxShadow': '0px 0px 5px rgba(0, 0, 0, 0.1)',
        'margin': '0 auto',
        'width': '90%',
        'maxWidth': '1200px',
        'overflow': 'hidden'  # Hide overflow
    }),

    dcc.Interval(id='interval-component', interval=5*1000, n_intervals=0)  # อัพเดททุกๆ5วิ
], style={
    'backgroundColor': '#f0f0f0',
    'padding': '20px',
    'fontFamily': 'Arial',
    'border': '1px solid #cccccc',
    'borderRadius': '8px',
    'margin': '0 auto',
    'width': '90%',
    'maxWidth': '1200px',
    'overflow': 'hidden'  # Hide overflow
})

@app.callback(
    [Output('ups-status-graph', 'figure'),
     Output('summary', 'children')],
    [Input('interval-component', 'n_intervals')]
)
def update_graph(n):
    # Generate or fetch data
    df = read_data_from_file()

    # Calculate the summary
    status_counts = df['Status'].value_counts().to_dict()
    ok_count = status_counts.get('OK', 0)
    warning_count = status_counts.get('Warning', 0)
    critical_count = status_counts.get('Critical', 0)

    summary = [
        html.P(f"OK: {ok_count}", style={'color': '#00FF00'}),
        html.P(f"Warning: {warning_count}", style={'color': '#fbc02d'}),
        html.P(f"Critical: {critical_count}", style={'color': '#FF0000'})
    ]

    # สีการแจ้งเตือนต่างๆ
    color_map = {
        'OK': '#00FF00',        # Green for OK
        'Warning': '#fbc02d',   # Yellow for Warning
        'Critical': '#FF0000'   # Red for Critical
    }

    fig = go.Figure()

    # Add bar chart for UPS status
    fig.add_trace(go.Bar(
        x=df['UPS'],
        y=[1] * len(df),  # Dummy value for bar height
        text=df['Status'],
        textposition='auto',
        marker_color=[color_map.get(status, '#cccccc') for status in df['Status']],  # Default to light grey if status not found
        name='UPS Status'
    ))

    fig.update_layout(
        title='UPS Status Overview',
        xaxis=dict(title='UPS', tickangle=-45),
        yaxis=dict(title='Status', tickvals=[]),  # Hide y-axis values
        plot_bgcolor='#ffffff',
        paper_bgcolor='#f9f9f9',
        font=dict(family='Arial', size=14, color='#333333'),
        title_font=dict(size=20, color='#333333'),
        margin=dict(l=30, r=30, t=40, b=30),
        height=600,  # Adjust height if needed
        width=800    # Adjust width if needed
    )

    return fig, summary

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8050)  # Allow access from any IP address
