import logging
logger = logging.getLogger('windnode_abw')

import pandas as pd
from pandas import compat
import networkx as nx
import matplotlib.pyplot as plt

import oemof.solph as solph


def remove_isolates():
    raise NotImplementedError
    # logging.info('Removing orphan buses')
    # # get all buses
    # buses = [obj for obj in Regions.entities if isinstance(obj, Bus)]
    # for bus in buses:
    #     if len(bus.inputs) > 0 or len(bus.outputs) > 0:
    #         logging.debug('Bus {0} has connections.'.format(bus.type))
    #     else:
    #         logging.debug('Bus {0} has no connections and will be deleted.'.format(
    #             bus.type))
    #         Regions.entities.remove(bus)
    #
    # for i in esys.nodes[0].inputs.keys():
    #     print(i.label)


def reduce_to_regions(bus_data,
                      line_data):
    """Reduce/sum existing transport capacities to capacities between region pairs

    Parameters
    ----------
    bus_data
    line_data

    Returns
    -------

    """

    def _to_dict_dropna(data):
        return dict((k, v.dropna().to_dict()) for k, v in compat.iteritems(data))

    # convert nominal cap. to numeric
    line_data['s_nom'] = pd.to_numeric(line_data['s_nom'])

    bus_data_nogeom = bus_data[['bus_id', 'hvmv_subst_id']]

    # bus data needs bus_id as index
    bus_data_nogeom.set_index('bus_id', inplace=True)

    # join HV-MV substation ids from buses on lines
    line_data = line_data.join(bus_data_nogeom, on='bus0')
    line_data.rename(columns={'hvmv_subst_id': 'hvmv_subst_id0'}, inplace=True)
    line_data = line_data.join(bus_data_nogeom, on='bus1')
    line_data.rename(columns={'hvmv_subst_id': 'hvmv_subst_id1'}, inplace=True)

    # remove lines which are fully located in one region (MVGD)
    line_data = line_data[line_data['hvmv_subst_id0'] != line_data['hvmv_subst_id1']]

    # swap substation ids if not ascending to allow grouping
    cond = line_data['hvmv_subst_id0'] > line_data['hvmv_subst_id1']
    line_data.loc[cond, ['hvmv_subst_id0',
                         'hvmv_subst_id1']] = \
        line_data.loc[cond, ['hvmv_subst_id1', 'hvmv_subst_id0']].values

    line_data.sort_values(by='hvmv_subst_id0', inplace=True)

    # group by substation ids and sum up capacities
    line_data_grouped = line_data.groupby(
        ['hvmv_subst_id0', 'hvmv_subst_id1']).sum().reset_index()
    line_data_grouped.drop(['bus0', 'bus1', 'line_id'], axis=1, inplace=True)

    line_data_grouped.rename(columns={'s_nom': 'capacity'}, inplace=True)

    # OLD:
    # line_data_grouped = line_data.groupby(
    #     ['hvmv_subst_id0', 'hvmv_subst_id1'])['s_nom'].sum()
    # # flatten and transpose
    # line_data_grouped = line_data_grouped.unstack().transpose()
    # line_data_dict = _to_dict_dropna(line_data_grouped)

    return line_data_grouped


def region_graph(subst_data,
                 line_data,
                 rm_isolates=False,
                 draw=False):
    """Create graph representation of grid from substation and line data

    Parameters
    ----------
    subst_data
    line_data
    rm_isolates
    draw

    Returns
    -------
    networkx.Graph
        Graph representation of grid
    """

    def _find_main_graph(graph):
        """Remove isolated grids (subgraphs) of grid/graph

        Parameters
        ----------
        graph : networkx.Graph

        Returns
        -------
        networkx.Graph
        """

        subgraphs = {len(sg.nodes()): sg for sg in nx.connected_component_subgraphs(graph)}

        if len(subgraphs) > 1:
            logger.warning('Region consists of {g_cnt} separate (unconnected) grids with node counts '
                           '{n_cnt}. The grid with max. node count is used, the others are dropped.'
                           .format(g_cnt=str(len(subgraphs)),
                                   n_cnt=str(list(subgraphs.keys()))
                                   )
                           )

            # use subgraph with max. count of nodes
            subgraph_used = subgraphs[max(list(subgraphs.keys()))]
            #subgraphs_dropped = [sg for n_cnt, sg in subgraphs.iteritems() if n_cnt != max(list(subgraphs.keys()))]

            return subgraph_used

    # create graph
    graph = nx.Graph()
    npos = {}
    elabels = {}

    for idx, row in line_data.iterrows():
        source = row['hvmv_subst_id0']
        geom = subst_data.loc[source]['geom']
        npos[source] = (geom.x, geom.y)

        target = row['hvmv_subst_id1']
        geom = subst_data.loc[target]['geom']
        npos[target] = (geom.x, geom.y)

        elabels[(source, target)] = str(int(row['capacity']))
        graph.add_edge(source, target)

    # remove isolated grids (graphs)
    if rm_isolates:
        graph = _find_main_graph(graph=graph)

    # draw graph
    if draw:
        plt.figure()
        nx.draw_networkx(graph, pos=npos, with_labels=True, font_size=8)
        nx.draw_networkx_edge_labels(graph, pos=npos, edge_labels=elabels, font_size=8)
        plt.show()

    return graph


def grid_graph(region,
               draw=False):
    """Create graph representation of grid from substation and line data from Region object

    Parameters
    ----------
    region : :class:`~.model.Region`
    draw : :obj:`bool`
        If true, graph is plotted

    Returns
    -------
    networkx.Graph
        Graph representation of grid
    """

    # create graph
    graph = nx.Graph()
    npos = {}
    elabels = {}
    nodes_color = []

    for idx, row in region.lines.iterrows():
        source = row['bus0']
        geom = region.buses.loc[source]['geom']
        npos[source] = (geom.x, geom.y)

        target = row['bus1']
        geom = region.buses.loc[target]['geom']
        npos[target] = (geom.x, geom.y)

        elabels[(source, target)] = str(int(row['s_nom']))
        graph.add_edge(source, target)

    for bus in graph.nodes():
        if bus in list(region.subst['bus_id']):
            color = (0.7, 0.7, 1)
        else:
            color = (0.8, 0.8, 0.8)

        # mark buses which are connected to im- and export
        if (not region.buses.loc[bus]['region_bus'] or
            bus in (list(region.trafos['bus0']) + list(region.trafos['bus1']))
            ):
            color = (1, 0.7, 0.7)

        nodes_color.append(color)

    # draw graph
    if draw:
        plt.figure()
        nx.draw_networkx(graph, pos=npos, node_color=nodes_color, with_labels=True, font_size=6)
        nx.draw_networkx_edge_labels(graph, pos=npos, edge_labels=elabels, font_size=8)
        plt.title('Gridmap')
        plt.xlabel('lon')
        plt.ylabel('lat')
        plt.show()

    return graph


def calc_line_loading(esys, region):
    """Calculates relative loading of esys' lines

    Parameters
    ----------
    esys : oemof.solph.EnergySystem
        Energy system including results

    Returns
    -------
    :obj:`dict`
        Line loading of format (node_from, node_to): relative mean line loading
    :obj:`dict`
        Line loading of format (node_from, node_to): relative max, line loading
    """

    results = esys.results['main']
    om_flows = dict(esys.results['om_flows'])

    line_loading_mean = {
        (from_n, to_n): float(flow['sequences'].mean()) / om_flows[(from_n, to_n)].nominal_value
        for (from_n, to_n), flow in results.items()
        if isinstance(from_n, solph.custom.Link)
    }

    line_loading_mean2 = {}
    for (from_n, to_n), flow in results.items():
        if isinstance(from_n, solph.custom.Link):
            line_loading_mean2[(from_n, to_n)] =\
                float(flow['sequences'].mean()) / om_flows[(from_n, to_n)].nominal_value

            if float(flow['sequences'].mean()) != float(flow['sequences'].max()):
                print((from_n, to_n))

    line_loading_max = {
        (from_n, to_n): float(flow['sequences'].max()) / om_flows[(from_n, to_n)].nominal_value
        for (from_n, to_n), flow in results.items()
        if isinstance(from_n, solph.custom.Link)
    }

    results_lines = region.lines[['line_id', 'bus0', 'bus1']].copy()
    results_lines['loading_mean'] = 0.
    results_lines['loading_max'] = 0.

    # calc max. of 2 loadings (both directions) and save in DF
    for line in results_lines.itertuples():
        link = esys.groups['line_{line_id}_b{b0}_b{b1}'.format(
                    line_id=str(line.line_id),
                    b0=str(line.bus0),
                    b1=str(line.bus1)
                )]
        results_lines.at[line.Index, 'loading_mean'] = max([line_loading_mean[(from_n, to_n)]
                                                     for (from_n, to_n), loading in line_loading_mean.items()
                                                     if from_n == link])
        results_lines.at[line.Index, 'loading_max'] = max([line_loading_max[(from_n, to_n)]
                                                    for (from_n, to_n), loading in line_loading_max.items()
                                                    if from_n == link])
    # region.results_lines = results_lines.sort_values('loading_max')
    region.results_lines = results_lines

    # # Alternative version with oemof objs (working):
    # # create DF with custom cols (node1, node 2, flow) from simulation result dict
    # flows_results = pd.Series(results).rename_axis(['node1', 'node2']).reset_index(name='flow_res')
    # flows_results.set_index(['node1', 'node2'], inplace=True)
    # flows_obj = pd.Series(dict(om_flows)).rename_axis(['node1', 'node2']).reset_index(name='flow_obj')
    # flows_obj.set_index(['node1', 'node2'], inplace=True)
    # flows = pd.concat([flows_obj, flows_results], axis=1).reset_index()
    #
    # # get esys' lines (Link instances)
    # lines = [node for node in esys.nodes if isinstance(node, solph.custom.Link)]
    # # get flows of lines (filtering of column node1 should be sufficient since Link always creates 2 Transformers)
    # flows_links = flows[flows['node1'].isin(lines)]
    #
    # for idx, row in flows_links.iterrows():
    #     obj = row['flow_obj']
    #     seq = row['flow_res']['sequences']
    #     if obj.nominal_value:
    #         flows_links.at[idx, 'loading_mean'] = float(seq.mean()) / obj.nominal_value
    #         flows_links.at[idx, 'loading_max'] = float(seq.max()) / obj.nominal_value
    #     else:
    #         flows_links.at[idx, 'loading_mean'] = 0.
    #         flows_links.at[idx, 'loading_max'] = 0.
    # flows_links.sort_values('loading_max')

    return


def prepare_feedin_timeseries(region):
    """Calculate feedin timeseries per technology for entire region

    Parameters
    ----------
    region : :class:`~.model.Region`

    Returns
    -------
    :obj:`dict` of :pandas:`pandas.DataFrame`
        Absolute feedin timeseries per technology (dict key) and municipality
        (DF column)

    ToDo: Allow for different scenarios
    """

    # needed columns from scenario's mun data for feedin
    cols = ['gen_capacity_wind',
            'gen_capacity_pv_ground',
            'gen_capacity_pv_roof_small',
            'gen_capacity_pv_roof_large',
            'gen_capacity_hydro',
            'gen_capacity_bio',
            'gen_capacity_sewage_landfill_gas',
            'gen_capacity_conventional_large',
            'gen_capacity_conventional_small']

    # mapping for capacity columns to timeseries columns
    # if repowering scenario present, use wind_fs time series
    tech_mapping = {
        'gen_capacity_wind': 'wind_sq',
            # ToDo: Include future scenario by using wind_fs
            #  as soon as they are defined and implemented:
            #'wind_sq' if reg_params['repowering_scn'] == 0 else 'wind_fs',
        'gen_capacity_pv_ground': 'pv_ground',
        'gen_capacity_hydro': 'hydro',
    }

    # prepare capacities (for relative timeseries only)
    cap_per_mun = region.muns[cols].rename(columns=tech_mapping)
    cap_per_mun['pv_roof'] = \
        cap_per_mun['gen_capacity_pv_roof_small'] + \
        cap_per_mun['gen_capacity_pv_roof_large']
    cap_per_mun['bio'] = \
        cap_per_mun['gen_capacity_bio'] + \
        cap_per_mun['gen_capacity_sewage_landfill_gas']
    cap_per_mun['conventional'] = \
        cap_per_mun['gen_capacity_conventional_large'] + \
        cap_per_mun['gen_capacity_conventional_small']
    cap_per_mun.drop(columns=['gen_capacity_pv_roof_small',
                                 'gen_capacity_pv_roof_large',
                                 'gen_capacity_bio',
                                 'gen_capacity_sewage_landfill_gas',
                                 'gen_capacity_conventional_large',
                                 'gen_capacity_conventional_small'],
                        inplace=True)

    # calculate capacity(mun)-weighted aggregated feedin timeseries for entire region:
    # 1) process relative TS
    feedin_agg = {}
    for tech in list(cap_per_mun.loc[:,
                     cap_per_mun.columns != 'conventional'].columns):
        feedin_agg[tech] = region.feedin_ts_init[tech] * cap_per_mun[tech]

    # 2) process absolute TS (conventional plants)
    # do not use capacities as the full load hours of the plants differ - use
    # ratio of currently set power values and those from status quo scenario
    conv_cap_per_mun = \
        cap_per_mun['conventional'] /\
        region.muns[['gen_capacity_conventional_large',
                  'gen_capacity_conventional_small']].sum(axis=1)
    feedin_agg['conventional'] = region.feedin_ts_init['conventional'] * conv_cap_per_mun

    # if repowering scenario present, rename wind_fs time series to wind
    feedin_agg['wind'] = feedin_agg.pop('wind_sq')

    # ToDo: Include future scenario by using wind_fs
    #  as soon as they are defined and implemented:
    # if reg_params['repowering_scn'] == 0:
    #     feedin_agg['wind'] = feedin_agg.pop('wind_sq')
    # else:
    #     feedin_agg['wind'] = feedin_agg.pop('wind_fs')

    return feedin_agg


def prepare_demand_timeseries(region):
    """Calculate demand timeseries per sector

    Parameters
    ----------
    region : :class:`~.model.Region`

    Returns
    -------
    :obj:`dict` of :pandas:`pandas.DataFrame`
        Absolute demand timeseries per demand sector (dict key) and
        municipality (DF column)

    ToDo: Allow for different scenarios
    """
    demand_ts = {}
    demand_types = region.demand_ts_init.columns.get_level_values(0).unique()
    for dt in demand_types:
        demand_ts[dt] = region.demand_ts_init[dt]

    return demand_ts
