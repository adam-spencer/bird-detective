import argparse
import requests
import pandas as pd
from pathlib import Path
from tqdm import tqdm


def get_api_key(loc: str = 'xenocanto_apikey.txt') -> str:
    with open(loc) as f:
        api_key = f.readline().rstrip()
    return api_key


def handle_multi_birds(args, api_key, bird_col: str = 'scientific_name'
                       ) -> None:
    df = pd.read_csv(args.bird_file)
    for _, bird_name in df[bird_col].items():
        get_one_recording(args, bird_name, api_key)


def get_one_recording(args: argparse.Namespace, bird_name: str, api_key: str
                      ) -> None:
    # Construct API request
    query = f'sp:"{bird_name}" cnt:"{args.country}" q:">{args.quality}"'
    url = ('https://xeno-canto.org/api/3/recordings'
           f'?query={query}&key={api_key}&per_page={args.max_recordings}')
    out_path = Path(args.output_dir) / bird_name.replace(' ', '_')
    out_path.mkdir()

    # Send API request
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check for bad response
        data = response.json()
        num_recordings = data.get('numRecordings', 0)

        if int(num_recordings) > 0:
            print(f'Successfully found {num_recordings} '
                  f'recordings for {bird_name}.')
            print('Downloading...')
            for recording in tqdm(data['recordings']):
                download_link = recording['file']
                recording_id = recording['id']

                audio_response = requests.get(download_link)
                with open(out_path / f'{recording_id}.mp3', 'wb') as f:
                    f.write(audio_response.content)
        else:
            print(f'No recordings found for {bird_name}.')

    except requests.exceptions.RequestException as e:
        print(f'An error occurred with the network request: {e}')
    except KeyError:
        print('Error parsing JSON response.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--bird-name', '-b', nargs='+',
                        help='Scientific name of single bird')
    parser.add_argument('--bird-file', '-f',
                        help='CSV file containing multiple scientific names')
    parser.add_argument('--output-dir', '-o', required=True)
    parser.add_argument('--quality', '-q', default='B',
                        help='Quality greater than [B, C, D, E]')
    parser.add_argument('--country', '-c', default='United Kingdom')
    parser.add_argument('--max-recordings', '-m', default=250, type=int)
    args = parser.parse_args()
    if args.bird_name and args.bird_file:
        raise argparse.ArgumentError(
            'Please only specify either a bird-name or bird-file!')
    # TODO refactor
    api_key = get_api_key()
    if args.bird_name:
        bird_name = ' '.join(args.bird_name)
        get_one_recording(args, bird_name, api_key)
    elif args.bird_file:
        handle_multi_birds(args, api_key)
    else:
        raise argparse.ArgumentError(
            'Please specify either a bird-name or bird-file!')
