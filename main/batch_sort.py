import os

from open_phy import open_phy
from process_functions import *
import spikeinterface.comparison as sc
from os import walk
import psutil
import shutil

os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')


def run_sort(file_path):
    recording_save = os.path.join('C:\\', 'github', 'spikeline', f'{os.path.basename(file_path)}_recording_save')
    tic = ticker()
    recording_preprocessed = get_recording(os.path.dirname(file_path), os.path.basename(file_path), recording_save,
                                           load_new=True)
    tic = ticker(tic, text='loading recording')
    sorter_list = ['kilosort3', 'kilosort2_5']
    sorters = run_spike_sorters(recording_preprocessed, sorter_list, run_new=True, keep_mua3=False)
    tic = ticker(tic, text='sorting')
    consensus = sc.compare_multiple_sorters(sorting_list=list(sorters.values()),
                                            name_list=list(sorters.keys()), verbose=False,
                                            delta_time=.2,
                                            match_score=.3,
                                            spiketrain_mode='union')
    consensus = consensus.get_agreement_sorting(minimum_agreement_count=2)
    # waveforms = extract_waveforms(consensus, recording_preprocessed)
    # waveforms.run_extract_waveforms()
    # tic = ticker(tic, text='waveforms extracted')
    # metrics_1 = si.compute_quality_metrics(waveforms,
    #                                        metric_names=['snr', 'isi_violation', 'amplitude_cutoff', 'num_spikes',
    #                                                      'firing_rate', 'presence_ratio'])
    # fig, axes = plt.subplots(3, 1)
    # fig.suptitle(os.path.basename(file_path))
    # axes[0].hist(metrics_1['snr'], 50)
    # axes[0].set_ylabel('snr')
    # axes[1].hist(metrics_1['isi_violations_ratio'], 50)
    # axes[1].set_ylabel('isi_violations_ratio')
    # axes[2].hist(metrics_1['amplitude_cutoff'], 50)
    # axes[2].set_ylabel('amplitude_cutoff')
    # plt.show()
    # keep_mask = (metrics_1['num_spikes'] > 300) & \
    #             (metrics_1['isi_violations_ratio'] < 50) & \
    #             (metrics_1['amplitude_cutoff'] < .3)
    # keep_unit_ids = keep_mask[keep_mask].index.values
    # consensus = consensus.select_units(keep_unit_ids)
    tic = ticker(tic, text='metrics calculated')
    export_for_phy({f'{os.path.basename(file_path)}': consensus}, recording_preprocessed, filter=False)
    tic = ticker(tic, text=f'{os.path.basename(file_path)} exported to phy')


def batch_sort(folder_path):
    sort = False
    curate = True
    settings = get_settings()
    for root, dirs, filenames in walk(folder_path):
        num_files = len(dirs)
        times = []
        for i, name in enumerate(dirs[::-1]):
            file_path = os.path.join(root, name)
            if name not in settings['exclude']:
                if name not in settings['sorting_complete'] and sort:
                    hdd = psutil.disk_usage('/')
                    if hdd.free / (2 ** 30) < 25:
                        print('under 25GB free, stopping here')
                        break
                    start_time = time.time()
                    run_sort(file_path)
                    settings['sorting_complete'].append(name)
                    settings['sorting_complete'].sort()
                    save_settings(settings)
                    times.append(time.time() - start_time)
                    print(f'Average processing time: {np.mean(times)}')
                    print(f'{(i + 1)}/{num_files} complete')
                    print('quit now if you want to pause')
                    time.sleep(10)
                if name not in settings['curation_complete'] and curate:
                    project_dir = os.path.dirname(os.getcwd())
                    phy_path = os.path.join(project_dir, 'phy_folders', f'phy_folder_for_{name}')
                    open_phy(phy_path)
                    if os.path.exists(os.path.join(phy_path, 'cluster_info.tsv')):
                        settings['curation_complete'].append(name)
                        settings['curation_complete'].sort()
                        save_settings(settings)
                    # print('quit now if you want to pause')
                    # time.sleep(5)
        save_settings(settings)
        break
    print('done')


def delete_completed():  # Clear space by removing recording saves for sessions already sorted
    project_dir = os.path.dirname(os.getcwd())
    settings = get_settings()
    for name in settings['curation_complete']:
        folder_dir = os.path.join(project_dir, name + '_recording_save')
        if os.path.exists(folder_dir):
            shutil.rmtree(folder_dir)


if __name__ == '__main__':
    # path = os.path.join('C:\\', 'data_drive_overflow')
    # path = os.path.join('D:\\', 'Test', 'ES029')
    # batch_sort(path)
    delete_completed()
