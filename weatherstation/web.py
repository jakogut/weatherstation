from flask import Flask

app = Flask(__name__)

env_data = {}

@app.route('/')
def display_conditions():
    formatter = '''
        <pre>
            Temperature: {temp} \t Humidity: {humd}
            \tPressure: {press}\tUV Index: {uv}
        </pre>
    '''
    
    return formatter.format(
        temp=env_data.get('temp', 'not available'),
        humd=env_data.get('humd', 'not available'),
        press=env_data.get('press', 'not available'),
        uv=env_data.get('uv', 'not available')
    )
