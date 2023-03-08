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
    recording_preprocessed = get_recording(os.path.dirname(file_path), os.path.basename(file_path), recording_save,
                                           load_new=True)
    sorter_list = ['kilosort3', 'kilosort2_5']
    sorters = run_spike_sorters(recording_preprocessed, sorter_list, run_new=True, keep_mua3=False)
    consensus = sc.compare_multiple_sorters(sorting_list=list(sorters.values()),
                                            name_list=list(sorters.keys()), verbose=False,
                                            delta_time=.2,
                                            match_score=.3,
                                            spiketrain_mode='union')
    consensus = consensus.get_agreement_sorting(minimum_agreement_count=2)

    root = os.path.dirname(os.getcwd())
    # cluster_info = {}
    template_dict = {}
    for sorter in sorters.keys():
        templates = np.load(os.path.join(root, sorter, 'templates.npy'))
        template_dict.update({sorter: templates})
        # channel_positions = np.load(os.path.join(root, sorter, 'channel_positions.npy'))
        # best_channels = np.argmax(np.max(np.abs(templates), axis=1), axis=1)
        # cluster_group = pd.read_csv(os.path.join(root, sorter, 'cluster_group.tsv'), sep='\t')
        # cluster_group['x_loc'] = channel_positions[best_channels][:, 0]
        # cluster_group['y_loc'] = channel_positions[best_channels][:, 1]
        # cluster_info.update({sorter: cluster_group.copy()})

    template = np.concatenate(
        [np.concatenate([template_dict[sorter][:, :, int(unit[sorter])] for sorter in sorters.keys()]) for unit in
         consensus._properties['unit_ids']])

    save_folder = export_for_phy({f'{os.path.basename(file_path)}': consensus}, recording_preprocessed, filter=False)
    np.save(os.path.join(save_folder, 'consensus_templates.npy'), template)


def batch_sort(folder_path):
    sort = True
    curate = False

    sorting_record = get_sorting_record()
    for root, dirs, filenames in walk(folder_path):
        num_files = len(dirs)
        times = []
        for i, name in enumerate(dirs):
            file_path = os.path.join(root, name)
            if name not in sorting_record['exclude']:
                if name not in sorting_record['sorting_complete'] and sort:
                    hdd = psutil.disk_usage('/')
                    if hdd.free / (2 ** 30) < 25:
                        print('under 25GB free, stopping here')
                        break
                    start_time = time.time()
                    run_sort(file_path)
                    sorting_record['sorting_complete'].append(name)
                    sorting_record['sorting_complete'].sort()
                    save_sorting_record(sorting_record)
                    times.append(time.time() - start_time)
                    print(f'Sorting Completed for {name}')
                    print(f'Average processing time: {np.mean(times)}')
                    print(f'{(i + 1)}/{num_files} complete')
                    print('quit now if you want to pause')
                    time.sleep(10)
                if name not in sorting_record['curation_complete'] and curate:
                    project_dir = os.path.dirname(os.getcwd())
                    phy_path = os.path.join(project_dir, 'phy_folders', f'phy_folder_for_{name}')
                    open_phy(phy_path)
                    if os.path.exists(os.path.join(phy_path, 'cluster_info.tsv')):
                        sorting_record['curation_complete'].append(name)
                        sorting_record['curation_complete'].sort()
                        save_sorting_record(sorting_record)
                        print(f'Curation Completed for {name}')
                    # print('quit now if you want to pause')
                    # time.sleep(5)
        save_sorting_record(sorting_record)
        break
    print('done')


def delete_completed():  # Clear space by removing recording saves for sessions already sorted
    project_dir = os.path.dirname(os.getcwd())
    settings = get_sorting_record()
    for name in settings['curation_complete']:
        folder_dir = os.path.join(project_dir, name + '_recording_save')
        if os.path.exists(folder_dir):
            shutil.rmtree(folder_dir)


if __name__ == '__main__':
    path = os.path.join('D:\\', 'Test', 'ES030')
    batch_sort(path)
    # delete_completed()
