import numpy as np
import os
import pandas as pd


def visualize():
    path = os.path.join('C:\\''github', 'spikeline', 'phy_folder_for_all_sort')
    spike_times = np.load(os.path.join(path, 'spike_times.npy'))
    channel_groups = np.load(os.path.join(path, 'channel_groups.npy'))
    channel_map = np.load(os.path.join(path, 'channel_map.npy'))
    channel_map_si = np.load(os.path.join(path, 'channel_map_si.npy'))
    channel_positions = np.load(os.path.join(path, 'channel_positions.npy'))
    spike_clusters = np.load(os.path.join(path, 'spike_clusters.npy'))
    template_ind = np.load(os.path.join(path, 'template_ind.npy'))
    templates = np.load(os.path.join(path, 'templates.npy'))
    cluster_channel_group = pd.read_csv(os.path.join(path, 'cluster_channel_group.tsv'), sep='\t')
    cluster_group = pd.read_csv(os.path.join(path, 'cluster_group.tsv'), sep='\t')
    cluster_info = pd.read_csv(os.path.join(path, 'cluster_info.tsv'), sep='\t')
    cluster_si_unit_id = pd.read_csv(os.path.join(path, 'cluster_si_unit_id.tsv'), sep='\t')
    cluster_si_unit_ids = pd.read_csv(os.path.join(path, 'cluster_si_unit_ids.tsv'), sep='\t')
    pass

def cross_correlegrams(sorter):
    pass

if __name__ == '__main__':
    visualize()
