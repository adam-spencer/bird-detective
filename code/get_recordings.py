import argparse
import requests
from pathlib import Path
from tqdm import tqdm


def main(args):
    # Construct API request
    bird_name = ' '.join(args.bird_name)
    query = f'sp:"{bird_name}" cnt:"{args.country}" q:{args.quality}'
    with open('xenocanto_apikey.txt') as f:
        api_key = f.readline().rstrip()
    url = ('https://xeno-canto.org/api/3/recordings'
           f'?query={query}&key={api_key}&per_page={args.max_recordings}')

    out_path = Path(args.output_dir) / '_'.join(args.bird_name)
    out_path.mkdir()
    print(out_path)

    # Send API request
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for bad response
        data = response.json()
        num_recordings = data.get('numRecordings', 0)

        if int(num_recordings) > 0:
            print(f'Successfully found {num_recordings} recordings.')
            print('Downloading...')
            for recording in tqdm(data['recordings']):
                download_link = recording['file']
                recording_id = recording['id']

                audio_response = requests.get(download_link)
                with open(out_path / f'{recording_id}.mp3', 'wb') as f:
                    f.write(audio_response.content)
        else:
            print("No recordings found.")

    except requests.exceptions.RequestException as e:
        print(f'An error occurred with the network request: {e}')
    except KeyError:
        print('Error parsing JSON response.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('bird_name', nargs='+')
    parser.add_argument('--output-dir', '-o', required=True)
    parser.add_argument('--quality', '-q', default='A')
    parser.add_argument('--country', '-c', default='United Kingdom')
    parser.add_argument('--max-recordings', '-m', default=250, type=int)
    args = parser.parse_args()
    main(args)
