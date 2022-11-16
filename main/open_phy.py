import os
from google.cloud import storage
import numpy as np
import json


def download_next():
    storage_client = storage.Client(project='spikeline')
    json_path = os.path.join(os.getcwd(), 'sorting_history.json')
    output_bucket = storage_client.get_bucket('spikeline_output')
    output_bucket_folders = np.unique([b[0] for b in [os.path.normpath(blob.name).split(os.path.sep) for blob in
                                                      storage_client.list_blobs('spikeline_output')]])

    if 'sorting_history.json' in output_bucket_folders:
        blob = output_bucket.blob('sorting_history.json')
        blob.download_to_filename(json_path)

    if os.path.exists(json_path):
        with open('sorting_history.json', 'r') as openfile:
            sorting_history = json.load(openfile)
    else:
        sorting_history = {"sorting_complete": [],
                           "curation_complete": [],
                           "exclude": []}
        json_object = json.dumps(sorting_history, indent=4)
        with open(json_path, "w") as outfile:
            outfile.write(json_object)

    print(f'previously curated: {sorting_history["curation_complete"]}')
    to_curate = None
    for folder in output_bucket_folders:
        if folder != 'sorting_history.json' and folder not in sorting_history['curation_complete']:
            to_curate = folder
            break
    if to_curate is not None:
        phy_folder = os.path.join(os.getcwd(), 'phy_export')
        for b in output_bucket.list_blobs(prefix=to_curate):
            b_path = os.path.normpath(b.name).split(os.path.sep)
            b_path = os.path.join(phy_folder, *b_path)
            if not os.path.exists(os.path.dirname(b_path)):
                os.makedirs(os.path.dirname(b_path))
            b.download_to_filename(b_path)
        template_similarity = np.load(os.path.join(phy_folder, 'template_similarty'))
        for i, val in enumerate(template_similarity):
            print(f'unit {i}: similarity {val}')
        open_phy(phy_folder)


def open_phy(save_folder):
    anaconda_prompt_cmd = ' '.join([os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3', 'Scripts', 'activate.bat'),
                                    os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3')])
    folder_path = f'cd /d {save_folder}'
    os.system(
        r"""start "My Spyder Package Installer" /wait cmd /c "%s&%s&%s&%s" """ % (
            anaconda_prompt_cmd, 'conda activate phy2', folder_path, 'phy template-gui params.py'))


if __name__ == '__main__':
    open_phy('C:\github\spikeline\phy_folders\phy_folder_for_ES029_2022-09-15_bot96_1_g0')
