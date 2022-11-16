import os
import json
import glob
import traceback
import numpy as np
from sys import platform
from shutil import rmtree
from google.cloud import storage
from sklearn.preprocessing import normalize

import spikeinterface.full as si
import spikeinterface.sorters as ss
import spikeinterface.extractors as se
import spikeinterface.comparison as sc
from spikeinterface.exporters import export_to_phy


# # os.system('gsutil cp -r gs://my data /src/local_data')

def cloud_sort():
    if platform == "linux" or platform == "linux2":
        docker_image = True
    else:
        docker_image = None

    storage_client = storage.Client(project='spikeline')

    json_path = os.path.join(os.getcwd(), 'sorting_history.json')
    input_bucket = storage_client.get_bucket('spikeline_input')
    output_bucket = storage_client.get_bucket('spikeline_output')
    archive_bucket = storage_client.get_bucket('spikeline_archive')
    input_bucket_folders = np.unique([b[0] for b in [os.path.normpath(blob.name).split(os.path.sep) for blob in
                                     storage_client.list_blobs('spikeline_input')]])

    if 'sorting_history.json' in input_bucket_folders:
        blob = input_bucket.blob('sorting_history.json')
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

    print(f'previously sorted: {sorting_history["sorting_complete"]}')

    for folder in input_bucket_folders:
        if folder != 'sorting_history.json' and folder not in sorting_history['sorting_complete']:
            print(f'{folder} not previously sorted. Beginning sort.')
            data_path = os.path.join(os.getcwd(), 'data')
            kilosort3_folder = os.path.join(os.getcwd(), 'kilosort3')
            kilosort2_5_folder = os.path.join(os.getcwd(), 'kilosort2_5')
            waveforms_folder = os.path.join(os.getcwd(), 'waveforms')
            phy_folder = os.path.join(os.getcwd(), 'phy_export')
            recording_save = os.path.join(os.getcwd(), 'recording_save')

            for b in input_bucket.list_blobs(prefix=folder):
                b_path = os.path.normpath(b.name).split(os.path.sep)
                b_path = os.path.join(data_path, *b_path)
                if not os.path.exists(os.path.dirname(b_path)):
                    os.makedirs(os.path.dirname(b_path))
                b.download_to_filename(b_path)

            recording_path = os.path.join(data_path, folder, folder + '_imec0')
            recording = se.read_spikeglx(recording_path, stream_id='imec0.ap')

            recording_cmr = recording
            recording_f = si.bandpass_filter(recording, freq_min=300, freq_max=6000)
            recording_cmr = si.common_reference(recording_f, reference='local', operator='median',
                                                local_radius=(30, 200))
            kwargs = {'n_jobs': 8, 'total_memory': '8G'}
            recording = recording_cmr.save(format='binary', folder=recording_save, **kwargs)

            sorter_params = {"keep_good_only": True}
            # ks3_sorter = si.read_sorter_folder(kilosort3_folder)
            ks3_sorter = ss.run_sorter(sorter_name='kilosort3', recording=recording, output_folder=kilosort3_folder,
                                       verbose=False, docker_image=docker_image, **sorter_params)
            sorter_params = {"keep_good_only": False}
            # ks2_5_sorter = si.read_sorter_folder(kilosort2_5_folder)
            ks2_5_sorter = ss.run_sorter(sorter_name='kilosort2_5', recording=recording,
                                         output_folder=kilosort2_5_folder,
                                         verbose=False, docker_image=docker_image, **sorter_params)

            consensus = sc.compare_multiple_sorters(sorting_list=[ks3_sorter, ks2_5_sorter],
                                                    name_list=['kilosort3', 'kilosort2_5'], verbose=False,
                                                    delta_time=.2,
                                                    match_score=.3,
                                                    spiketrain_mode='union')
            consensus = consensus.get_agreement_sorting(minimum_agreement_count=2)

            if os.path.isdir(waveforms_folder):
                rmtree(waveforms_folder)
            waveforms = si.WaveformExtractor.create(recording, consensus, waveforms_folder)
            waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
            waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
            sparsity_dict = dict(method="radius", radius_um=50, peak_sign='both')

            kilosort3_templates = np.load(os.path.join(kilosort3_folder, 'templates.npy'))
            kilosort2_5_templates = np.load(os.path.join(kilosort2_5_folder, 'templates.npy'))

            template_similarty = np.array([np.sum(
                (normalize(np.max(abs(kilosort3_templates[int(unit['kilosort3']), :, :]), axis=0, keepdims=True)) -
                 normalize(np.max(abs(kilosort2_5_templates[int(unit['kilosort2_5']), :, :]), axis=0,
                                  keepdims=True))) ** 2) for unit in consensus._properties['unit_ids']]) / 2

            job_kwargs = {'n_jobs': 8, 'total_memory': '8G'}
            try:
                export_to_phy(waveforms, phy_folder, compute_pc_features=True, compute_amplitudes=True, copy_binary=True,
                              remove_if_exists=True, sparsity_dict=sparsity_dict, max_channels_per_template=None,
                              **job_kwargs)
            except Exception:
                traceback.print_exc()
                export_to_phy(waveforms, phy_folder, compute_pc_features=True, compute_amplitudes=False,
                              copy_binary=True,
                              remove_if_exists=True, sparsity_dict=sparsity_dict, max_channels_per_template=None,
                              **job_kwargs)
            np.save(os.path.join(phy_folder, 'template_similarty'), template_similarty)

            rel_paths = glob.glob(phy_folder + '/**', recursive=True)
            for local_file in rel_paths:
                if os.path.isfile(local_file):
                    local_path_parts = local_file.split(os.sep)
                    remote_path = f'{folder}/{"/".join(local_path_parts[local_path_parts.index("phy_export"):])}'
                    blob = output_bucket.blob(remote_path)
                    blob.upload_from_filename(local_file)

            archive_bucket_blobs = [blob.name for blob in archive_bucket.list_blobs()]
            for b in input_bucket.list_blobs(prefix=folder):
                if b.name not in archive_bucket_blobs:
                    src_blob = input_bucket.get_blob(b.name)
                    dst_blob = archive_bucket.blob(b.name)
                    rewrite_token = ''
                    print(f'starting upload: {b.name}')
                    while rewrite_token is not None:
                        rewrite_token, bytes_rewritten, bytes_to_rewrite = dst_blob.rewrite(
                            src_blob, token=rewrite_token)
                        print(f'Progress so far: {bytes_rewritten}/{bytes_to_rewrite} bytes.')

            sorting_history['sorting_complete'].append(folder)
            sorting_history['sorting_complete'].sort()
            json_object = json.dumps(sorting_history, indent=4)
            with open(json_path, "w") as outfile:
                outfile.write(json_object)
            blob = input_bucket.blob('sorting_history.json')
            blob.upload_from_filename(json_path)

            rmtree(data_path)
            rmtree(kilosort3_folder)
            rmtree(kilosort2_5_folder)
            rmtree(waveforms_folder)
            rmtree(recording_save)



def get_bucket_folders(storage_client, bucket):
    return np.unique([b[0] for b in [os.path.normpath(blob.name).split(os.path.sep) for blob in
                                     storage_client.list_blobs(bucket)]])


if __name__ == '__main__':
    cloud_sort()

"""
in terminal at containing folder i ran this:

gcloud builds submit --pack image=gcr.io/spikeline/test-sort

which builds the container.

then i ran this:

gcloud beta run jobs create job-testsort \
    --image gcr.io/spikeline/test-sort \
    --tasks 1 \
    --set-env-vars FOLDER_NAME="ES029_2022-09-14_bot72_0_g0" \
    --max-retries 5 \
    --region us-central1

which creates the job.

Next i ran this to run the job:

gcloud beta run jobs execute job-testsort
"""
