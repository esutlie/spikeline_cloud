import os
import json
import glob
import psutil
import traceback
import subprocess
import numpy as np
import logging as log
from sys import platform
from shutil import rmtree

from sklearn.preprocessing import normalize
import spikeinterface.full as si
import spikeinterface.sorters as ss
import spikeinterface.extractors as se
import spikeinterface.comparison as sc
from spikeinterface.exporters import export_to_phy

os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')


def sort_session(data_path):
    n_jobs = -1

    kilosort3_folder = os.path.join(os.getcwd(), 'kilosort3')
    kilosort2_5_folder = os.path.join(os.getcwd(), 'kilosort2_5')
    waveforms_folder = os.path.join(os.getcwd(), 'waveforms')
    consensus_folder = os.path.join(os.getcwd(), 'consensus')
    phy_folder = os.path.join(os.getcwd(), 'phy_export')
    recording_save = os.path.join(os.getcwd(), 'recording_save')

    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')

    folder_name = data_path.split(os.sep)[-1]
    recording_name = folder_name + '_imec0'
    recording_path = os.path.join(data_path, recording_name)
    log.info(f'specified recording save path: {recording_path}')

    recording = se.read_spikeglx(recording_path, stream_id='imec0.ap')
    log.info(f'read spikeGLX')

    recording_cmr = recording
    recording_f = si.bandpass_filter(recording, freq_min=300, freq_max=6000)
    recording_cmr = si.common_reference(recording_f, reference='local', operator='median',
                                        local_radius=(30, 200))
    kwargs = {'n_jobs': n_jobs, 'total_memory': '8G'}
    log.info(f'applying filters...')
    recording = recording_cmr.save(format='binary', folder=recording_save, **kwargs)
    log.info(f'filters applied')
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')

    sorter_params = {"keep_good_only": True}
    log.info(f'starting kilosort3...')
    ss.Kilosort3Sorter.set_kilosort3_path(os.path.join('C:\\', 'github', 'Kilosort'))
    ss.Kilosort2_5Sorter.set_kilosort2_5_path(os.path.join('C:\\', 'github', 'Kilosort2_5'))
    ks3_sorter = ss.run_sorter(sorter_name='kilosort3', recording=recording, output_folder=kilosort3_folder,
                               verbose=False, **sorter_params)
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')
    sorter_params = {"keep_good_only": False}
    log.info(f'starting kilosort2_5...')
    ks2_5_sorter = ss.run_sorter(sorter_name='kilosort2_5', recording=recording,
                                 output_folder=kilosort2_5_folder,
                                 verbose=False, **sorter_params)
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')

    log.info(f'starting consensus...')
    consensus = sc.compare_multiple_sorters(sorting_list=[ks3_sorter, ks2_5_sorter],
                                            name_list=['kilosort3', 'kilosort2_5'], verbose=False,
                                            delta_time=.2,
                                            match_score=.3,
                                            spiketrain_mode='union')
    consensus = consensus.get_agreement_sorting(minimum_agreement_count=2)

    kilosort3_templates = np.load(os.path.join(kilosort3_folder, 'templates.npy'))
    kilosort2_5_templates = np.load(os.path.join(kilosort2_5_folder, 'templates.npy'))

    template_similarty = np.array([np.sum(
        (normalize(np.max(abs(kilosort3_templates[int(unit['kilosort3']), :, :]), axis=0, keepdims=True)) -
         normalize(np.max(abs(kilosort2_5_templates[int(unit['kilosort2_5']), :, :]), axis=0,
                          keepdims=True))) ** 2) for unit in consensus._properties['unit_ids']]) / 2

    consensus = consensus.select_units(consensus.unit_ids[np.where(template_similarty < .9)[0]])
    log.info(f'trimmed with template matching')
    consensus = consensus.save(folder=consensus_folder)

    waveforms = si.WaveformExtractor.create(recording, consensus, waveforms_folder)
    waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
    waveforms.run_extract_waveforms(n_jobs=n_jobs, chunk_size=30000)
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')

    sparsity_dict = dict(method="radius", radius_um=50, peak_sign='both')
    log.info(f'got waveforms')
    log.info(f'starting phy export')
    job_kwargs = {'n_jobs': n_jobs, 'total_memory': '8G'}
    export_to_phy(waveforms, phy_folder, compute_pc_features=True, compute_amplitudes=True, copy_binary=True,
                  remove_if_exists=True, sparsity_dict=sparsity_dict, max_channels_per_template=None,
                  **job_kwargs)
    log.info(f'finished phy export')
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')

    log.info(f'removing intermediate data folders')
    rmtree(kilosort3_folder)
    rmtree(kilosort2_5_folder)
    rmtree(waveforms_folder)
    rmtree(consensus_folder)
    rmtree(recording_save)
    hdd = psutil.disk_usage('/')
    log.info(f'remaining disk: {hdd.free / (2 ** 30)} GiB')


def open_phy(save_folder=os.path.join('C:\\', 'github', 'spikeline', 'main', 'phy_export')):
    anaconda_prompt_cmd = ' '.join([os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3', 'Scripts', 'activate.bat'),
                                    os.path.join('C:\\', 'Users', 'Elissa', 'Anaconda3')])
    folder_path = f'cd /d {save_folder}'
    os.system(
        r"""start "My Spyder Package Installer" /wait cmd /c "%s&%s&%s&%s" """ % (
            anaconda_prompt_cmd, 'conda activate phy2', folder_path, 'phy template-gui params.py'))


if __name__ == '__main__':
    file_path = os.path.join('D:\\', 'Test', 'ES031', 'ES031_2022-12-20_bot170_1_g0')
    # sort_session(file_path)
    open_phy()
