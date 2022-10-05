import os
import time
import numpy as np
import spikeinterface.full as si
import spikeinterface.sorters as ss
import spikeinterface.extractors as se
import spikeinterface.comparison as sc
import spikeinterface.widgets as sw
from spikeinterface.exporters import export_to_phy
from shutil import rmtree
import pickle
from dask.diagnostics import ProgressBar
import upsetplot
import matplotlib.pyplot as plt
import pandas as pd

ProgressBar().register()

os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')
os.environ['IRONCLUST_PATH'] = os.path.join('C:\\', 'github', 'ironclust')
os.environ['HDSORT_PATH'] = os.path.join('C:\\', 'github', 'HDsort')
os.environ['WAVECLUS_PATH'] = os.path.join('C:\\', 'github', 'wave_clus')
os.environ['COMBINATO_PATH'] = os.path.join('C:\\', 'github', 'combinato')
os.environ['TEMPDIR'] = os.path.join('D:\\', 'temp')


def ticker(tic=None, text=''):
    t = time.time()
    if tic:
        print(f'Time Elapsed: {t - tic} seconds {text}')
    return t


def reset_folder(name, local=True):
    count = 0
    while True:
        save_folder = name + str(count)
        folder_path = f'./{save_folder}' if local else save_folder
        try:
            if os.path.isdir(folder_path):
                rmtree(folder_path)
            break
        except PermissionError:
            count += 1
    return save_folder


def remove_empty_or_one(sorter):
    units_to_keep = []
    for segment_index in range(sorter.get_num_segments()):
        for unit in sorter.get_unit_ids():
            spikes = sorter.get_unit_spike_train(unit, segment_index=segment_index)
            if spikes.size > 1:
                units_to_keep.append(unit)
    units_to_keep = np.unique(units_to_keep)
    return sorter.select_units(units_to_keep)


def get_recording(recording_folder, recording_name, temp_path, load_new=False):
    recording_path = os.path.join(recording_folder, recording_name, recording_name + '_imec0')
    if load_new or not os.path.isdir(temp_path):
        print(f'Processing recording {recording_name}...')
        recording_preprocessed = process_recording(recording_path, temp_path)
    else:
        print(f'Loading recording from temp_path...')
        recording_preprocessed = si.load_extractor(temp_path)
        # w_ts = sw.plot_timeseries(recording_preprocessed, time_range=(60, 60.1),
        #                           channel_ids=recording_preprocessed.channel_ids[:5])
        # w_ts.ax.set_title('from save')
        # w_ts.plot()
        # plt.show()
    return recording_preprocessed


def process_recording(recording_path, temp_path):
    if not os.path.isdir(recording_path):
        print('path not valid')
        print(recording_path)
        raise Exception
    recording = se.read_spikeglx(recording_path, stream_id='imec0.ap')
    # w_ts = sw.plot_timeseries(recording, time_range=(60, 60.1),
    #                           channel_ids=recording.channel_ids[:5])
    # w_ts.ax.set_title('before processing')
    # w_ts.plot()
    # plt.show()

    recording_cmr = recording
    recording_f = si.bandpass_filter(recording, freq_min=300, freq_max=6000)
    recording_cmr = si.common_reference(recording_f, reference='local', operator='median')
    # w_ts = sw.plot_timeseries(recording_cmr, time_range=(60, 60.1),
    #                           channel_ids=recording_cmr.channel_ids[:5])
    # w_ts.ax.set_title('after processing')
    # w_ts.plot()
    # plt.show()

    if os.path.isdir(temp_path):
        rmtree(temp_path)
    kwargs = {'n_jobs': 8, 'total_memory': '8G'}
    recording_preprocessed = recording_cmr.save(format='binary', folder=temp_path, **kwargs)
    return recording_preprocessed


def run_spike_sorters(recording, sorter_list, run_new=False):
    sorters = {}
    for name in sorter_list:
        try:
            save_path = os.path.join('C:\\', 'github', 'spikeline', name)
            if os.path.isdir(save_path) and not run_new:
                print(f'Loading {name}...')
                sorters.update({name: remove_empty_or_one(si.read_sorter_folder(save_path))})
            else:
                print(f'Running {name}...')
                if os.path.isdir(save_path):
                    rmtree(save_path)
                if name in ['mountainsort4']:
                    sorter_params = {"num_workers": 8}
                else:
                    sorter_params = {}
                sorter = ss.run_sorter(sorter_name=name, recording=recording, output_folder=save_path, verbose=True,
                                       **sorter_params)
                sorters.update({name: remove_empty_or_one(sorter)})
                print(f'{name} succeeded')
        except Exception as e:
            print(f'{name} failed with exception:\n{e}')
    return sorters


def export_for_phy(sorters, recording, tic=time.time(), filter=False):
    save_folders = {}
    current_dir = os.path.dirname(os.getcwd())
    for name, sorter in sorters.items():
        print(f'Extracting waveforms for {name}...')
        waveforms_folder = reset_folder(os.path.join(current_dir, 'waveforms'), local=False)
        waveforms = si.WaveformExtractor.create(recording, sorter, waveforms_folder)
        waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
        waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
        tic = ticker(tic, text='waveforms extracted')
        if filter:
            print(f'Filtering units for {name}...')
            sorter = filter_results(sorter, waveforms)
            tic = ticker(tic, text='units filtered')
            print(f'Extracting waveforms for filtered {name}...')
            waveforms_folder = reset_folder(os.path.join(current_dir, 'waveforms'), local=False)
            waveforms = si.WaveformExtractor.create(recording, sorter, waveforms_folder)
            waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
            waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
            tic = ticker(tic, text='waveforms extracted')
        folder_name = f'phy_folder_for_{name}'
        save_folder = os.path.join(current_dir, folder_name)
        print(f'Exporting waveforms for phy to {folder_name}...')
        sparsity_dict = dict(method="radius", radius_um=50, peak_sign='both')
        export_to_phy(waveforms, save_folder, compute_pc_features=False, compute_amplitudes=False, copy_binary=False,
                      remove_if_exists=True, sparsity_dict=sparsity_dict, max_channels_per_template=None)
        tic = ticker(tic, text='phy export')
        save_folders.update({name: folder_name})
    with open('save_folder_dict', 'wb') as f:
        pickle.dump(save_folders, f, protocol=pickle.HIGHEST_PROTOCOL)
    return save_folders


def filter_results(sorting, waveforms):
    metrics = si.compute_quality_metrics(waveforms, metric_names=['snr', 'isi_violation', 'amplitude_cutoff'])

    keep_mask = (metrics['snr'] > 7.5) & (metrics['isi_violations_rate'] < 0.01)
    print(keep_mask)

    keep_unit_ids = keep_mask[keep_mask].index.values
    print(keep_unit_ids)

    curated_sorting = sorting.select_units(keep_unit_ids)
    return curated_sorting


def visualize_comparison(comp_multi):
    units = comp_multi.units
    units_df = pd.DataFrame.from_dict(units).transpose()
    units_df['sorters'] = [', '.join(list(units_df.loc[i].unit_ids.keys())) for i in range(len(units_df))]
    path = os.path.join('C:\\''github', 'spikeline', 'phy_folder_for_all_sort')
    cluster_info = pd.read_csv(os.path.join(path, 'cluster_info.tsv'), sep='\t')
    cluster_info['sorters'] = units_df['sorters']
    noise = cluster_info[cluster_info.group == 'noise']
    mua = cluster_info[cluster_info.group == 'mua']
    good = cluster_info[cluster_info.group == 'good']
    make_upset(noise, title='noise')
    make_upset(mua, title='mua')
    make_upset(good, title='good')


def make_upset(data, title='Upset Plot'):
    uniques, counts = np.unique([string.split(', ') for string in data.sorters.values], return_counts=True)
    noise_upset = upsetplot.from_memberships(uniques, data=counts)
    upsetplot.plot(noise_upset)
    plt.suptitle(title)
    plt.show()
