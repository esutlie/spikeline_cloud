import os
import time

import matplotlib.pyplot as plt
from open_phy import open_phy
from process_functions import *
import spikeinterface.comparison as sc
from remove_duplicate_spikes import remove_dup
import spikeinterface.widgets as sw
import pandas as pd
import seaborn as sns
import itertools
from itertools import product
import datetime
from extract_waveforms import extract_waveforms

os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')
os.environ['IRONCLUST_PATH'] = os.path.join('C:\\', 'github', 'ironclust')


def test_loop(sorter_list):
    os.environ['KILOSORT3_PATH'] = os.path.join('C:\\', 'github', 'Kilosort')
    os.environ['KILOSORT2_5_PATH'] = os.path.join('C:\\', 'github', 'Kilosort2_5')
    os.environ['IRONCLUST_PATH'] = os.path.join('C:\\', 'github', 'ironclust')
    # Get the recording
    current_dir = os.path.dirname(os.getcwd())
    recording_folder = os.path.join('D:\\', 'Test', 'ES029')
    recording_name = 'ES029_2022-09-14_bot72_0_g0'
    recording_save = os.path.join('C:\\', 'github', 'spikeline', 'recording_save')
    tic = ticker()
    recording_preprocessed = get_recording(recording_folder, recording_name, recording_save, load_new=False)
    tic = ticker(tic, text='loaded recording')

    path = os.path.join('C:\\', 'github', 'spikeline', 'gt_sorter')  # ES029_2022-09-14_bot72_0_g0
    gt_sorter = se.PhySortingExtractor.load_from_folder(path)
    columns = ['run_name', 'num_true', 'num_tested', 'num_well_detected', 'percent_overlap', 'percent_true',
               'percent_found']

    sorter_combos = [list(itertools.combinations(sorter_list, length + 1)) for length in range(len(sorter_list))]
    sorter_combos = [item for sublist in sorter_combos for item in sublist]
    sorter_combos = sorter_combos[::-1]

    variable_dict = {
        'kilosort3_mua': [True, False],
        'kilosort2_5_mua': [True, False],
        'isi_violations_ratio': [3],
        'amplitude_cutoff': [.3],
        'snr': [20],
        'match_score': [.3],
        'delta_time': [.2],
        'spiketrain_mode': ['union'],
        'sorter_combos': sorter_combos
    }
    keys = list(variable_dict.keys())
    sets = [dict(zip(keys, values)) for values in product(*variable_dict.values())]
    num_sets = len(sets)
    results_df = pd.DataFrame(columns=columns)
    params_df = pd.DataFrame(columns=keys[:-1])
    start_time = time.time()
    sorter_runs = {}
    tic = time.time()
    for sorter in sorter_list:
        if sorter == 'kilosort2_5':
            for keep_mua2_5 in variable_dict['kilosort2_5_mua']:
                sorter_runs.update(
                    run_spike_sorters(recording_preprocessed, [sorter], run_new=False, keep_mua2_5=keep_mua2_5))
        elif sorter == 'kilosort3':
            for keep_mua3 in variable_dict['kilosort3_mua']:
                sorter_runs.update(
                    run_spike_sorters(recording_preprocessed, [sorter], run_new=False, keep_mua3=keep_mua3))
        else:
            sorter_runs.update(run_spike_sorters(recording_preprocessed, [sorter], run_new=False))
    i = 0
    for sorter_combo in variable_dict['sorter_combos']:
        param_set = {sorter_name: sorter_name in sorter_combo for sorter_name in sorter_list}
        param_sets = []
        sorters_list = []
        if 'kilosort3' in sorter_combo:
            for keep_mua3 in variable_dict['kilosort3_mua']:
                if 'kilosort2_5' in sorter_combo:
                    for keep_mua2_5 in variable_dict['kilosort2_5_mua']:
                        sorters = run_spike_sorters(recording_preprocessed, sorter_combo, run_new=False,
                                                    keep_mua3=keep_mua3, keep_mua2_5=keep_mua2_5)
                        sorters_list.append(sorters)
                        param_sets.append({**param_set, 'kilosort3_mua': keep_mua3, 'kilosort2_5_mua': keep_mua2_5})
                else:
                    sorters = run_spike_sorters(recording_preprocessed, sorter_combo, run_new=False,
                                                keep_mua3=keep_mua3)
                    sorters_list.append(sorters)
                    param_sets.append({**param_set, 'kilosort3_mua': keep_mua3, 'kilosort2_5_mua': 'nan'})
        else:
            if 'kilosort2_5' in sorter_combo:
                for keep_mua2_5 in variable_dict['kilosort2_5_mua']:
                    sorters = run_spike_sorters(recording_preprocessed, sorter_combo, run_new=False,
                                                keep_mua2_5=keep_mua2_5)
                    sorters_list.append(sorters)
                    param_sets.append({**param_set, 'kilosort3_mua': 'nan', 'kilosort2_5_mua': keep_mua2_5})
            else:
                sorters = run_spike_sorters(recording_preprocessed, sorter_combo, run_new=False)
                sorters_list.append(sorters)
                param_sets.append({**param_set, 'kilosort3_mua': 'nan', 'kilosort2_5_mua': 'nan'})
        tic = ticker(tic, text='sorting')
        for sorts, param_set1 in zip(sorters_list, param_sets):
            num_sorters = len(sorts)
            test_sorts = []
            waveforms_list = []
            param_sets1 = []
            if num_sorters > 1:
                for delta_time in variable_dict['delta_time']:
                    for match_score in variable_dict['match_score']:
                        for spiketrain_mode in variable_dict['spiketrain_mode']:
                            test_sort = sc.compare_multiple_sorters(sorting_list=list(sorts.values()),
                                                                    name_list=list(sorts.keys()), verbose=False,
                                                                    delta_time=delta_time,
                                                                    match_score=match_score,
                                                                    spiketrain_mode=spiketrain_mode)
                            test_sort = test_sort.get_agreement_sorting(minimum_agreement_count=num_sorters)
                            test_sorts.append(test_sort)
                            waveforms_list.append(extract_waveforms(test_sort, recording_preprocessed))
                            param_sets1.append({**param_set1, 'delta_time': delta_time, 'match_score': match_score,
                                                'spiketrain_mode': spiketrain_mode})
            else:
                test_sorts.append(list(sorts.values())[0])
                waveforms_list.append(extract_waveforms(test_sorts[0], recording_preprocessed))
                param_sets1.append({**param_set1, 'delta_time': 'nan', 'match_score': 'nan',
                                    'spiketrain_mode': 'nan'})
            tic = ticker(tic, text='test_sorts generated')
            for test_sort, waveforms, param_set2 in zip(test_sorts, waveforms_list, param_sets1):
                print('computing metrics...')
                tic = time.time()
                waveforms.run_extract_waveforms()
                metrics_1 = si.compute_quality_metrics(waveforms,
                                                       metric_names=['snr', 'isi_violation', 'amplitude_cutoff'])
                tic = ticker(tic, text='metrics computed')

                for snr in variable_dict['snr']:
                    for isi_violations_ratio in variable_dict['isi_violations_ratio']:
                        for amplitude_cutoff in variable_dict['amplitude_cutoff']:
                            keep_mask = (metrics_1['snr'] < snr) & \
                                        (metrics_1['isi_violations_ratio'] < isi_violations_ratio) & \
                                        (metrics_1['amplitude_cutoff'] < amplitude_cutoff)

                            keep_unit_ids = keep_mask[keep_mask].index.values
                            curated_sorting = test_sort.select_units(keep_unit_ids)
                            results = test_performance(gt_sorter, curated_sorting, i)
                            results_df = pd.concat((results_df, results))
                            params = {**param_set2, 'snr': snr, 'isi_violations_ratio': isi_violations_ratio,
                                      'amplitude_cutoff': amplitude_cutoff}
                            params = pd.DataFrame.from_dict({key: [value] for (key, value) in params.items()})
                            params_df = pd.concat((params_df, params))
                            i += 1
                            total_time = time.time() - start_time
                            time_remaining = total_time / i * (num_sets - i)
                            print(f'{i}/{num_sets} complete in {str(datetime.timedelta(seconds=total_time))}')
                            print(f'Estimated time remaining: {str(datetime.timedelta(seconds=time_remaining))}')
                intermediate = pd.concat((results_df, params_df), axis=1)
                intermediate.sort_values('percent_overlap', inplace=True, ascending=False)
                if len(intermediate) > 10:
                    print(intermediate[:10].to_markdown())
                else:
                    print(intermediate.to_markdown())
    results_df = pd.concat((results_df, params_df), axis=1)
    path = os.path.join(os.path.dirname(os.getcwd()), 'results_df')
    results_df.to_pickle(path)


def test_performance(gt_sorter, test_sorter, name):
    columns = ['run_name', 'num_true', 'num_tested', 'num_well_detected', 'percent_overlap', 'percent_true',
               'percent_found']
    gt_comp = sc.compare_sorter_to_ground_truth(gt_sorter, test_sorter, gt_name='ground_truth', tested_name=name,
                                                compute_labels=False, verbose=True, exhaustive_gt=True)
    num_true = len(gt_comp.event_counts1)
    num_tested = len(gt_comp.event_counts2)
    num_well_detected = len(gt_comp.get_well_detected_units(well_detected_score=0.75))
    percent_overlap = num_well_detected / (num_true + num_tested - num_well_detected)
    percent_true = num_well_detected / num_tested  # percent of found units that arent true
    percent_found = num_well_detected / num_true  # percent of units we didnt find
    data = np.array([[name, num_true, num_tested, num_well_detected, percent_overlap, percent_true, percent_found]])
    return pd.DataFrame(data=data, columns=columns)


def metrics(recording, sorter, gt_comp, tic=time.time()):
    current_dir = os.path.dirname(os.getcwd())

    print(f'Extracting waveforms for metrics...')
    waveforms_folder = reset_folder(os.path.join(current_dir, 'waveforms'), local=False)
    waveforms = si.WaveformExtractor.create(recording, sorter, waveforms_folder)
    waveforms.set_params(ms_before=3., ms_after=4., max_spikes_per_unit=500)
    waveforms.run_extract_waveforms(n_jobs=-1, chunk_size=30000)
    tic = ticker(tic, text='waveforms extracted')

    print(f'Calculating metrics...')
    metrics = si.compute_quality_metrics(waveforms, metric_names=['snr', 'isi_violation', 'amplitude_cutoff'])
    tic = ticker(tic, text='metrics calculated')

    good_units = gt_comp.get_well_detected_units(well_detected_score=0.75)
    metrics['unit_type'] = metrics.index.isin(good_units)
    sns.histplot(data=metrics, x='isi_violations_ratio', hue="unit_type", multiple="stack", binwidth=1)
    plt.title('isi_violations_ratio')
    plt.ylim([0, 40])
    plt.xlim([0, 15])
    plt.show()
    # histplots(metrics)
    print('test')


def histplots(metrics_df):
    for c in metrics_df.columns:
        if c != 'unit_type':
            sns.histplot(data=metrics_df, x=c, hue="unit_type", multiple="stack", bins=100)
            plt.title(c)
            plt.ylim([0, 20])
            plt.show()


if __name__ == '__main__':
    sorter_list = ['kilosort2_5', 'kilosort3']
    test_loop(sorter_list)
