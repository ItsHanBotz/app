import os
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
import json
import io
import pytz
import matplotlib.pyplot as plt
from io import BytesIO
from github import Github

app = FastAPI()

repository_url = "https://github.com/ItsHanBotz/data"
data_file_path = "data.json"
timezone = 'Asia/Jakarta'

def get_repo():
    github_token = os.getenv("GITHUB_TOKEN")
    g = Github(github_token)
    return g.get_repo(repository_url)

def load_data():
    repo = get_repo()
    try:
        content = repo.get_contents(data_file_path)
        data = json.loads(content.decoded_content)
        if 'dates' in data and isinstance(data['dates'][0], str):
            data['dates'] = [datetime.strptime(date, '%y-%m-%d\n%H:%M').replace(tzinfo=pytz.utc).astimezone(pytz.timezone(timezone)) for date in data['dates']]
        return data
    except Exception as e:
        return {'dates': [], 'values': []}

def save_data(data):
    repo = get_repo()
    data['dates'] = [date.strftime('%y-%m-%d\n%H:%M') for date in data['dates']]
    data_str = json.dumps(data, indent=2)
    repo.update_file(data_file_path, "Update data.json", data_str, content.sha)

def generate_line_chart(data):
    fig, ax = plt.subplots(figsize=(10, 6))

    data_subset = {'dates': data['dates'][-10:], 'values': data['values'][-10:]}

    colors = ['b', 'g', 'r']

    for i, color in enumerate(colors):
        values_at_index = [values[i] for values in data_subset['values']]
        ax.plot(data_subset['dates'], values_at_index, marker='o', linestyle='-', color=color, label=f'Data {i+1}')

    ax.set_xlabel('Year ' + str(datetime.now().year))
    ax.set_ylabel('Value')
    ax.set_title('HanBotz')
    ax.legend(['Pengguna', 'Pesan diterima', 'Perintah digunakan'], loc='upper left')

    ax.set_xticks(data_subset['dates'])
    current_max_value = max(max(data_subset['values'], default=0))
    current_ylim = max(current_max_value + 150, 4000)
    ax.set_ylim(0, current_ylim)

    ax.set_xticklabels(data_subset['dates'], rotation=45, ha='right')

    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)

    image_stream = BytesIO()
    fig.savefig(image_stream, format='png')
    image_stream.seek(0)

    plt.close(fig)

    return image_stream

@app.get('/update_data', response_class=StreamingResponse)
async def update_data_api(number1: int = Query(...), number2: int = Query(...), number3: int = Query(...)):
    try:
        numbers = [number1, number2, number3]

        existing_data = load_data()

        if 'dates' not in existing_data:
            existing_data['dates'] = []
        if 'values' not in existing_data:
            existing_data['values'] = []

        current_date = datetime.now(pytz.timezone(timezone))
        values = numbers
        existing_data['dates'].append(current_date)
        existing_data['values'].append(values)

        current_max_value = max(max(existing_data['values'], default=0))
        current_ylim = max(current_max_value + 150, 4000)

        save_data(existing_data)

        chart_data = generate_line_chart(existing_data)

        return StreamingResponse(content=chart_data, media_type="image/png")

    except Exception as e:
        return {'error': str(e)}
