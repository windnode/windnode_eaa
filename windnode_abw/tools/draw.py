import networkx as nx

from matplotlib import rcParams

rcParams['font.family'] = 'sans-serif'
rcParams['font.sans-serif'] = 'Roboto'
rcParams['font.weight'] = 'normal'
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.ticker import ScalarFormatter
import matplotlib.gridspec as gridspec

from matplotlib import cm
from matplotlib.colors import ListedColormap

import numpy as np
import pandas as pd
import geopandas as gpd
import os
import warnings

import seaborn as sns

# set seaborn style
sns.set()

import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go
import plotly.offline as pltly
from plotly.colors import n_colors, unconvert_from_RGB_255
from plotly.subplots import make_subplots

from oemof.outputlib import views
from oemof.graph import create_nx_graph

from windnode_abw.model.region.tools import calc_dsm_cap_up, calc_dsm_cap_down

import logging

logger = logging.getLogger('windnode_abw')

PRINT_NAMES = {
    'bhkw': "Large-scale CHP",
    'bio': "Biogas",
    'demand': 'Demand',
    'district_heating': 'District Heating',
    'gas': "Open-cycle gas turbine",
    'grid': "Grid",
    'Grid': 'Grid',
    'Grid new': 'Grid new',
    'grid new': 'Grid new',
    'gud': "Combined-cycle gas turbine",
    'hydro': "Hydro",
    'pv_ground': "PV ground-mounted",
    "pv_roof": "PV roof",
    'pv_roof_large': "PV roof top (large)",
    'pv_roof_small': "PV roof top (small)",
    'wind': "Wind",
    "export": "Export (national grid)",
    'import': "Import (national grid)",
    "el_heating": "electrical Heating",
    "elenergy": "Direct electric heating",
    "fuel_oil": "Oil heating",
    "gas_boiler": "Gas (district heating)",
    "natural_gas": "Gas heating",
    "solar": "Solar thermal heating",
    "solar_heat": "Solar heating",
    "wood": "Wood heating",
    "coal": "Coal heating",
    "pth": "Power-to-heat (district heating)",
    "pth_ASHP": "Air source heat pump",
    "pth_ASHP_nostor": "Air source heat pump, no storage",
    "pth_ASHP_stor": "Air source heat pump, storage",
    "pth_GSHP": "Ground source heat pump",
    "pth_GSHP_nostor": "Ground source heat pump, no storage",
    "pth_GSHP_stor": "Ground source heat pump, storage",
    "stor_th_large": "Thermal storage (district heating)",
    "stor_th_small": "Thermal storage",
    "flex_bat_large": "Large-scale battery storage",
    "flex_bat_small": "PV system battery storage",
    "hh": "Households",
    "ind": "Industry",
    "rca": "CTS+agriculture",
    "conventional": "Conventional",
    "el_hh": "Electricity households",
    "el_rca": "Electricity CTS+agriculture",
    "el_ind": "Electricity industry",
    "th_hh_efh": "Heat single-family houses",
    "th_hh_mfh": "Heat apartment buildings",
    "th_rca": "Heat CTS+agriculture",
    "hh_efh": "Single-family houses",
    "hh_mfh": "Apartment buildings",
    "ABW-export": "Export (regional)",
    "ABW-import": "Import (regional)",
    "roof": "Area required rel. PV rooftop",
    "H_0.1": "Area required rel. PV ground H 0.1-perc agri",
    "H_1": "Area required rel. PV ground H 1-perc agri",
    "H_2": "Area required rel. PV ground H 2-perc agri",
    "HS_0.1": "Area required rel. PV ground HS 0.1-perc agri",
    "HS_1": "Area required rel. PV ground HS 1-perc agri",
    "HS_2": "Area required rel. PV ground HS 2-perc agri",
    "SQ": "Area required rel. Wind legal SQ (VR/EG)",
    "s1000f1": "Area required rel. Wind 1000m w forest 10-perc",
    "s500f0": "Area required rel. Wind 500m wo forest 10-perc",
    "s500f1": "Area required rel. Wind 500m w forest 10-perc",

}
UNITS = {"relative": "%", "hours": "h", "Utilization Rate": "%", "Total Cycles": "cycles", "Full Discharge Hours": "h",
         "RE": "MWh", "DSM": "MWh", "Import": "MWh", "Lineload": "%"}

# https://developer.mozilla.org/en-US/docs/Web/CSS/color_value
# https://plotly.com/python/builtin-colorscales/
COLORS = {'bio': 'green',
          'district_heating': 'plum',
          'grid': 'grey',
          'grid new': 'darkgrey',
          'Grid': 'grey',
          'Grid new': 'darkgrey',
          'hydro': 'royalblue',
          'pv_ground': 'goldenrod',
          'pv_roof_large': 'gold',
          'pv_roof_small': 'darkorange',
          'wind': 'skyblue',
          'conventional': 'grey',
          'fuel_oil': 'grey',
          'solar_heat': 'peru',
          'solar': 'peru',
          'el_heating': 'red',
          'elenergy': 'red',
          'gud': 'teal',
          'natural_gas': 'teal',
          'bhkw': 'seagreen',
          'gas': 'lightgrey',
          'gas_boiler': 'lightgrey',
          "wood": "maroon",
          "coal": "black",
          'import': 'limegreen',
          'export': 'brown',
          'demand': 'darkgray',
          'rca': 'darkseagreen',
          'hh': 'coral',
          'ind': 'lightslategrey',
          'el_rca': 'gray',
          'el_hh': 'darkmagenta',
          'el_ind': 'darkslategray',
          'th_hh_efh': 'plum',
          'hh_efh': 'plum',
          'th_hh_mfh': 'fuchsia',
          'hh_mfh': 'fuchsia',
          'th_rca': 'crimson',
          'ABW-export': 'mediumpurple',
          'ABW-import': 'mediumorchid',
          "pth": "indianred",
          "pth_ASHP_nostor": "lightpink",
          "pth_ASHP_stor": "lightpink",
          "pth_GSHP_nostor": "lightcoral",
          "pth_GSHP_stor": "lightcoral",
          "flex_bat_large": "sandybrown",
          "flex_bat_small": "burlywood",
          "stor_th_large": "rosybrown",
          "stor_th_small": "indianred",
          }

# Color dict with PRINT_NAMES
COLORS_PRINT = dict()
for key in COLORS.keys():
    COLORS_PRINT[PRINT_NAMES.get(key)] = COLORS[key]


def set_colors(steps=21):
    # RLI Colors
    # CMAP = px.colors.sequential.GnBu_r
    # WindNODE Colors
    colors = n_colors('rgb(0, 200, 200)', 'rgb(255, 100, 0)', steps, colortype='rgb')
    # WindNODE Colormap
    cmap = n_colors((0, 200, 200), (255, 100, 0), 21)
    cmap = [unconvert_from_RGB_255(i) for i in cmap]
    cmap = ListedColormap(cmap)
    return cmap, colors


cmap, colors = set_colors()
colors_r = list(reversed(colors))

def draw_graph(grph, mun_ags=None,
               edge_labels=True, node_color='#AFAFAF',
               edge_color='#CFCFCF', plot=True, node_size=2000,
               with_labels=True, arrows=True, layout='neato',
               node_pos=None, font_size=10):
    """
    Draw a graph (from oemof examples)

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.
    mun_ags : int
        Municipality's AGS. If provided, the graph will contain only nodes from
        this municipality.
    edge_labels : boolean
        Use nominal values of flow as edge label
    node_color : dict or string
        Hex color code oder matplotlib color for each node. If string, all
        colors are the same.

    edge_color : string
        Hex color code oder matplotlib color for edge color.

    plot : boolean
        Show matplotlib plot.

    node_size : integer
        Size of nodes.

    with_labels : boolean
        Draw node labels.

    arrows : boolean
        Draw arrows on directed edges. Works only if an optimization_model has
        been passed.
    layout : string
        networkx graph layout, one of: neato, dot, twopi, circo, fdp, sfdp.
    """
    if type(node_color) is dict:
        node_color = [node_color.get(g, '#AFAFAF') for g in grph.nodes()]

    # set drawing options
    options = {
        'prog': 'dot',
        'with_labels': with_labels,
        'node_color': node_color,
        'edge_color': edge_color,
        'node_size': node_size,
        'arrows': arrows,
        'font_size': font_size
    }

    if mun_ags is not None:
        nodes = [n for n in grph.nodes if str(mun_ags) in n]
        nodes_neighbors = [list(nx.all_neighbors(grph, n))
                           for n in nodes]
        nodes = set(nodes + list(set([n for nlist in nodes_neighbors
                                      for n in nlist])))
        grph = grph.subgraph(nodes)
        grph = nx.relabel_nodes(grph,
                                lambda x: x.replace('_' + str(mun_ags), ''))
        options['node_color'] = [set_node_colors(grph).get(n, '#AFAFAF')
                                 for n in grph.nodes()]
        options['node_size'] = 200
        options['arrowsize'] = 15
        options['with_labels'] = False
        options['font_size'] = 10
        pos = nx.drawing.nx_agraph.graphviz_layout(grph,
                                                   prog='neato',
                                                   args='-Gepsilon=0.0001')
        nx.draw(grph, pos=pos, **options)
        pos = {k: (v[0], v[1] + 10) for k, v in pos.items()}
        nx.draw_networkx_labels(grph, pos=pos, **options)

    else:
        if node_pos is None:
            pos = nx.drawing.nx_agraph.graphviz_layout(grph, prog=layout)
        else:
            pos = node_pos

        nx.draw(grph, pos=pos, **options)
        labels = nx.get_edge_attributes(grph, 'weight')
        nx.draw_networkx_edge_labels(grph, pos=pos, edge_labels=labels)

    # show output
    if plot is True:
        plt.show()


def set_node_colors(grph):
    """Define node colors

    Parameters
    ----------
    grph : networkxGraph
        A graph to draw.

    Returns
    -------
    :obj:`dict`
        Node colors: graph node as key, hex color as val

    Notes
    -----
    Colors made with color brewer (http://colorbrewer2.org)
    """
    colors = {}
    for node in grph.nodes():
        if node[:4] == 'b_el':
            colors[node] = '#bdc9e1'
        elif node[:6] == 'gen_el':
            colors[node] = '#016c59'
        elif node[:6] == 'dem_el':
            colors[node] = '#67a9cf'
        elif node[:9] == 'excess_el':
            colors[node] = '#cccccc'
        elif node[:11] == 'shortage_el':
            colors[node] = '#cccccc'
        elif node[:4] == 'line':
            colors[node] = '#f7f7f7'

        elif node[:8] == 'b_th_dec':
            colors[node] = '#fecc5c'
        elif node[:10] == 'gen_th_dec':
            colors[node] = '#bd0026'
        elif node[:10] == 'dem_th_dec':
            colors[node] = '#fd8d3c'
        elif node[:8] == 'b_th_cen':
            colors[node] = '#d7b5d8'
        elif node[:10] == 'gen_th_cen':
            colors[node] = '#980043'
        elif node[:10] == 'dem_th_cen':
            colors[node] = '#df65b0'

        elif node[:14] == 'flex_bat_large':
            colors[node] = '#08519c'
        elif node[:14] == 'flex_bat_small':
            colors[node] = '#08519c'
        elif node[:12] == 'flex_dec_pth':
            colors[node] = '#ffffb2'
        elif node[:12] == 'flex_cen_pth':
            colors[node] = '#ffffb2'
        elif node[:8] == 'flex_dsm':
            colors[node] = '#3c6ecf'

    return colors


def debug_plot_results(esys, region):
    """Plots results of simulation

    Parameters
    ----------
    esys : oemof.solph.EnergySystem
        Energy system including results
    region : :class:`~.model.Region`
        Region object
    """

    logger.info('Plotting results...')

    results = esys.results['main']
    # om_flows = esys.results['om_flows']

    imex_bus_results = views.node(results, 'b_th_dec_15001000_hh_efh')
    imex_bus_results_flows = imex_bus_results['sequences']

    # print some sums for import/export bus
    print(imex_bus_results_flows.sum())
    print(imex_bus_results_flows.info())

    # some example plots for bus_el
    ax = imex_bus_results_flows.sum(axis=0).plot(kind='barh')
    ax.set_title('Sums for optimization period')
    ax.set_xlabel('Energy (MWh)')
    ax.set_ylabel('Flow')
    plt.tight_layout()
    plt.show()

    imex_bus_results_flows.plot(kind='line', drawstyle='steps-post')
    plt.show()

    ax = imex_bus_results_flows.plot(kind='bar', stacked=True, linewidth=0, width=1)
    ax.set_title('Sums for optimization period')
    ax.legend(loc='upper right', bbox_to_anchor=(1, 1))
    ax.set_xlabel('Energy (MWh)')
    ax.set_ylabel('Flow')
    plt.tight_layout()

    dates = imex_bus_results_flows.index
    tick_distance = int(len(dates) / 7) - 1
    ax.set_xticks(range(0, len(dates), tick_distance), minor=False)
    ax.set_xticklabels(
        [item.strftime('%d-%m-%Y') for item in dates.tolist()[0::tick_distance]],
        rotation=90, minor=False)
    plt.show()


def sample_plots(region, results):
    ##############
    # PLOT: Grid #
    ##############
    fig, axs = plt.subplots(1, 2)
    de = gpd.read_file(os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        'data',
        'DEU_adm0.shp')).to_crs("EPSG:3035")
    de.plot(ax=axs[0], color='white', edgecolor='#aaaaaa')

    gdf_region = gpd.GeoDataFrame(region.muns, geometry='geom')
    gdf_region['centroid'] = gdf_region['geom'].centroid

    gdf_region.plot(ax=axs[0])

    gdf_region.plot(ax=axs[1], color='white', edgecolor='#aaaaaa')
    for idx, row in gdf_region.iterrows():
        axs[1].annotate(s=row['gen'],
                        xy=(row['geom'].centroid.x, row['geom'].centroid.y),
                        ha='center',
                        va='center',
                        color='#555555',
                        size=8)
    gdf_lines = gpd.GeoDataFrame(region.lines, geometry='geom')
    gdf_lines.plot(ax=axs[1], color='#88aaaa', linewidth=1.5, alpha=1)
    gdf_buses = gpd.GeoDataFrame(region.buses, geometry='geom')
    gdf_buses.plot(ax=axs[1], color='#338888', markersize=6, alpha=1)

    for p in [0, 1]:
        axs[p].set_yticklabels([])
        axs[p].set_xticklabels([])

    axs[0].set_title('Region ABW in Deutschland',
                     fontsize=16,
                     fontweight='normal')
    axs[1].set_title('Region ABW mit Hochspannungsnetz',
                     fontsize=16,
                     fontweight='normal')

    plt.show()

    #######################
    # PLOT: RE capacities #
    #######################
    fig, axs = plt.subplots(2, 2)
    gdf_region = gpd.GeoDataFrame(region.muns, geometry='geom')
    gdf_region['gen_capacity_pv_roof'] = gdf_region['gen_capacity_pv_roof_small'] + \
                                         gdf_region['gen_capacity_pv_roof_large']
    gdf_region.plot(column='gen_capacity_wind', ax=axs[0, 0], legend=True, cmap='viridis')

    axs[0, 0].set_title('Wind')
    gdf_region.plot(column='gen_capacity_pv_ground', ax=axs[0, 1], legend=True, cmap='viridis')
    axs[0, 1].set_title('Photovoltaik FF-Anlagen')
    gdf_region.plot(column='gen_capacity_pv_roof', ax=axs[1, 0], legend=True, cmap='viridis')
    axs[1, 0].set_title('Photovoltaik Aufdachanlagen')
    gdf_region.plot(column='gen_capacity_bio', ax=axs[1, 1], legend=True, cmap='viridis')
    axs[1, 1].set_title('Bioenergie')
    # plt.axis('off')
    for x, y in zip([0, 0, 1, 1], [0, 1, 0, 1]):
        axs[x, y].set_yticklabels([])
        axs[x, y].set_xticklabels([])
        # for idx, row in gdf_region.iterrows():
        #     axs[x, y].annotate(s=row['gen'],
        #                        xy=(row['geom'].centroid.x, row['geom'].centroid.y),
        #                        ha='center',
        #                        va='center',
        #                        color='#ffffff',
        #                        size=8)
    fig.suptitle('Installierte Leistung Erneuerbare Energie in Megawatt',
                 fontsize=16,
                 fontweight='normal')
    plt.show()

    ###########################
    # PLOT: RE feedin stacked #
    ###########################
    time_start = 2000
    timesteps = 240
    techs = {'hydro': 'Laufwasser',
             'bio': 'Bioenergie',
             'wind': 'Windenergie',
             'pv_ground': 'Photovoltaik (Freifläche)',
             'pv_roof_small': 'Photovoltaik (Aufdach <30 kW)',
             'pv_roof_large': 'Photovoltaik (Aufdach >30 kW)',
             }
    sectors = {'el_ind': 'Industrie',
               'el_rca': 'GHD',
               'el_hh': 'Haushalte'
               }
    fig, ax = plt.subplots()
    feedin = pd.DataFrame({v: region.feedin_ts[k].sum(axis=1)
                           for k, v in techs.items()}).iloc[
             time_start:time_start + timesteps]
    demand = pd.DataFrame({v: region.demand_ts[k].sum(axis=1)
                           for k, v in sectors.items()}).iloc[
             time_start:time_start + timesteps]

    residual_load = demand.sum(axis=1) - feedin.sum(axis=1)

    (-feedin).plot.area(ax=ax, cmap='viridis')
    demand.plot.area(ax=ax, cmap='copper')
    residual_load.plot(ax=ax, style='r--', label='Residuallast')
    ax.set_title('Strom: Last- und EE-Erzeugungszeitreihen, Residuallast',
                 fontsize=16,
                 fontweight='normal')
    ax.set_xlabel('Zeit', fontsize=12)
    ax.set_ylabel('MW', fontsize=12)
    ax.set_ylim(round(min(-feedin.sum(axis=1)) / 100 - 1) * 100,
                round(max(demand.sum(axis=1)) / 100 + 1) * 100)
    plt.legend()
    plt.show()

    #############################
    # PLOT: Dec. th. generation #
    #############################
    timesteps = 96
    fig, ax = plt.subplots()
    th_generation = results['Wärmeerzeugung dezentral nach Technologie'].merge(
        results['Wärmeerzeugung Wärmepumpen nach Technologie'], left_index=True, right_index=True).iloc[0:0 + timesteps]

    th_generation.plot.area(ax=ax, cmap='viridis')  # BrBG
    ax.set_title('Wärmeerzeugung dezentral nach Technologie',
                 fontsize=16,
                 fontweight='normal')
    ax.set_xlabel('Zeit', fontsize=12)
    ax.set_ylabel('MW', fontsize=12)
    ax.set_ylim(0)
    plt.legend()
    plt.show()


def plot_grid(region, lines=False, buses=False):
    """plot ABW Region, optional with powerlines and buses"""
    with sns.axes_style("white"):
        fig, ax = plt.subplots(figsize=(20, 10))

        gdf_region = gpd.GeoDataFrame(region.muns, geometry='geom')

        # gdf_region.plot(ax=ax, color='white', edgecolor='#aaaaaa')
        gdf_region.plot(ax=ax, color=cmap(1), edgecolor='white', alpha=1)

        for idx, row in gdf_region.iterrows():
            ax.annotate(s=row['gen'],
                        xy=(row['geom'].centroid.x, row['geom'].centroid.y),
                        ha='center',
                        va='bottom',
                        color='black',
                        size=14)

        gdf_region['centroid'] = gdf_region['geom'].centroid
        gdf_centroid = gpd.GeoDataFrame(gdf_region, geometry='centroid')
        gdf_centroid.plot(ax=ax, color=cmap(20), markersize=30, alpha=1)
        if lines:
            gdf_lines = gpd.GeoDataFrame(region.lines, geometry='geom')
            gdf_lines.plot(ax=ax, color='#88aaaa', linewidth=1.5, alpha=1)
        if buses:
            gdf_buses = gpd.GeoDataFrame(region.buses, geometry='geom')
            gdf_buses.plot(ax=ax, color='#338888', markersize=6, alpha=1)

        ax.set_yticklabels([])
        ax.set_xticklabels([])

        ax.set_title('Region Anhalt-Bitterfeld-Wittenberg',
                     fontsize=16,
                     fontweight='normal')
        sns.despine(ax=ax, top=True, bottom=True, left=True, right=True)
        plt.show()


# one geoplot to fit in subplots
def plot_geoplot(name, data, region, ax, unit=None, cmap=None, vmin=None, vmax=None):
    """plot geoplot from pd.Series
    Parameters
    ----------
    name : str
        title of plot
    data : pd.Series
        data to plot
    region : :class:`~.model.Region`
        Region object
    ax : matplotlib.axes
        coordinate system
    unit : str
        label of colorbar
    """
    # Rli Colormap
    # cmap = cm.GnBu_r(np.linspace(0,1,40))
    # cmap = ListedColormap(cmap[:32,:-1])
    # WindNODE Colormap
    # cmap = n_colors((0, 200, 200), (255, 100, 0), 21)
    # cmap = [unconvert_from_RGB_255(i) for i in cmap]
    # cmap = ListedColormap(cmap)

    gdf_region = gpd.GeoDataFrame(region.muns.loc[:, ['gen', 'geom']],
                                  geometry='geom')
    gdf_region = gdf_region.join(data,
                                 how='inner')

    # size the colorbar to plot
    divider = make_axes_locatable(ax)
    cax = divider.append_axes("right", size="5%", pad=0.05)

    #
    gdf_region.plot(column=data.values,
                    ax=ax,
                    legend=True,
                    cmap=cmap,
                    cax=cax,
                    legend_kwds={'label': unit},
                    vmin=vmin,
                    vmax=vmax,
                    )

    # Set title, remove ticks/grid
    ax.set_title(name)
    ax.set_yticklabels([])
    ax.set_xticklabels([])
    ax.grid(False)

# ######################
# single scenario notebook
# ######################


def plot_snd_total(region, df_supply, df_demand):
    """plot barplot of yearly total supply and demand per ags
    Parameters
    ----------
    region : :class:`~.model.Region`
        Region object
    df_supply : pd.DataFrame
        yearly total per ags
    df_demand : pd.DataFrame
        yearly total per ags
    """
    fig = go.Figure()
    for tech, data in df_supply.iteritems():
        fig.add_trace(go.Bar(x=region.muns['gen'],
                             y=data / 1e3,
                             name=PRINT_NAMES[tech],
                             marker_color=COLORS[tech]))

    for tech, data in df_demand.iteritems():
        fig.add_trace(go.Bar(x=region.muns['gen'],
                             y=-data / 1e3,
                             name=PRINT_NAMES[tech],
                             marker_color=COLORS[tech],
                             visible='legendonly'))

    fig.update_traces(hovertemplate='%{fullData.name}<br>' +
                                    '%{y:.1f} GWh <br>' +
                                    '<extra></extra>', )
    fig.update_layout(
        title='Power Supply and Demand',
        legend_title="Technology/Sector",
        barmode='relative',
        height=600,
        xaxis={'categoryorder': 'category ascending'},
        xaxis_tickfont_size=14,
        yaxis=dict(title='GWh',
                   titlefont_size=16,
                   tickfont_size=14),
        autosize=True)
    fig.show()


def plot_split_hbar(data, limit, ax, title=None, unit=None):
    """plot 2 horizontal barplot with data splitted at limit
    Parameters
    ----------
    data : pd.Series
        indexed values to plot
    limit : int/float
        threshold to split barplot at
    ax : matplotlib.axes
        coordinate system
    title : str
        title describing data
    unit : str
        xlabel: unit of data
    """
    # split data
    data_left = data[data < limit]
    data_right = data[data >= limit]

    ax.set_title(title)
    # split subplot
    inner = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=ax, wspace=0.35, hspace=0.2)

    # left plot
    ax1 = plt.subplot(inner[0])
    data_left.plot(kind='barh', ax=ax1)  # , color=colors_hight(df_data_left.values, 'winter'))
    ax1.set_ylabel('AGS')
    ax1.set_xlabel(unit)
    ax1.set_xlim([0, limit])
    ax1.set_title(title, loc='left', fontsize=12)

    # right plot
    ax2 = plt.subplot(inner[1])
    data_right.plot(kind='barh', ax=ax2)  # color=colors_hight(df_data_right.values, 'winter'))
    ax2.set_ylabel(None)
    ax2.set_xlabel(unit)
    ax2.set_title(title, loc='left', fontsize=12)


def plot_timeseries(results_scn, kind='Power', **kwargs):
    """plot generation and demand timeseries of either 'electrical' or 'thermal' components
    Parameters
    ----------
    results_scn : dict
        scenario result
    kind : str
        'Power' or 'Thermal'
    *ags : str/int
        ags number or 'ABW' for whole region
    """
    # start = kwargs.get('start', region.cfg['date_from'])
    # end = kwargs.get('end', region.cfg['date_to'])
    ags = kwargs.get('ags', 'ABW')

    # remove if ags in multiindex is converted to int
    ags = str(ags)

    if kind == 'Power':
        df_feedin = results_scn['flows_txaxt']['Stromerzeugung']
        df_demand = results_scn['flows_txaxt']['Stromnachfrage']

        if ags == 'ABW':
            df_feedin = df_feedin.sum(level=0)  # .loc[start:end,:]
            df_demand = df_demand.sum(level=0)  # .loc[start:end,:]
            df_demand = df_demand.join(
                results_scn['flows_txaxt']['Stromnachfrage Wärme'].sum(level=2).sum(axis=1).rename('el_heating'))

        else:
            # add intra regional exchange
            df_feedin = df_feedin.join(results_scn['flows_txaxt']['Intra-regional exchange']['import'].rename(
                'ABW-import'))  # .loc[(slice(None), ags)])
            df_demand = df_demand.join(results_scn['flows_txaxt']['Intra-regional exchange']['export'].rename(
                'ABW-export'))  # .loc[(slice(None), ags)])

            df_feedin = df_feedin.loc[(slice(None), ags), :].sum(level=0)  # .loc[start:end,:]
            df_demand = df_demand.loc[(slice(None), ags), :].sum(level=0)
            el_heating = results_scn['flows_txaxt']['Stromnachfrage Wärme'].loc[(slice(None), slice(None), ags), :].sum(
                level='timestamp')
            df_demand['el_heating'] = el_heating.sum(axis=1)

    elif kind == 'Thermal':
        df_feedin = results_scn['flows_txaxt']['Wärmeerzeugung']
        df_demand = results_scn['flows_txaxt']['Wärmenachfrage']

        if ags == 'ABW':
            df_feedin = df_feedin.sum(level=0)  # .loc[start:end,:]
            df_demand = df_demand.sum(level=0)  # .loc[start:end,:]
        else:
            df_feedin = df_feedin.loc[(slice(None), ags), :].sum(level=0)  # .loc[start:end,:]
            df_demand = df_demand.loc[(slice(None), ags), :].sum(level=0)
    # else:
    #    raise ValueError("Enter either 'el' or 'th'") 

    # what is conventional
    # df_residual_load = df_demand.sum(axis=1) - df_feedin.drop(columns=['conventional']).sum(axis=1)

    fig = go.Figure()

    for tech, data in df_feedin.iteritems():
        fig.add_trace(go.Scatter(x=data.index,
                                 y=data.values,
                                 name=PRINT_NAMES[tech],
                                 fill='tonexty',
                                 mode='none',
                                 fillcolor=COLORS[tech],
                                 stackgroup='one'))

    for tech, data in df_demand.iteritems():
        fig.add_trace(go.Scatter(x=data.index,
                                 y=(-data.values),
                                 name=PRINT_NAMES[tech],
                                 fill='tonexty',
                                 mode='none',
                                 fillcolor=COLORS[tech],
                                 stackgroup='two'))

    fig.update_xaxes(
        title='Zoom',
        showspikes=True,
        rangeslider_visible=True,
        rangeselector=dict(
            buttons=list([
                dict(count=6, label="6m", step="month", stepmode="backward"),
                dict(count=1, label="1m", step="month", stepmode="backward"),
                dict(count=14, label="2w", step="day", stepmode="backward"),
                dict(count=7, label="1w", step="day", stepmode="backward"),
                dict(count=3, label="3d", step="day", stepmode="backward"),
                # dict(step="all")
            ])
        )
    )

    fig.update_layout(
        title=f'{kind} Generation and Demand of {ags}',
        legend_title="Technology/Sector",
        height=700,
        # xaxis={'categoryorder':'category ascending'},
        xaxis_tickfont_size=14,
        yaxis=dict(
            title='MW',
            titlefont_size=16,
            tickfont_size=14),
        autosize=True,
    )
    fig.update_traces(hovertemplate='%{x}<br>' +
                                    '%{fullData.name} <br>' +
                                    'Power: %{y:.0f} MW <br>' +
                                    '<extra></extra>', )  #
    fig.show()


def get_timesteps(region):
    timestamps = pd.date_range(start=region.cfg['date_from'],
                               end=region.cfg['date_to'],
                               freq=region.cfg['freq'])
    steps = len(timestamps)
    return steps


def get_storage_ratios(storage_figures, region):
    """calculate storage ratios for heat or electricity
    Parameters
    ----------
    storage_figures : pd.DataFrame
        DF including: discharge, capacity, power_discharge
    
    Return
    ---------
    storage_ratios : pd.DataFrame
        'Full Load Hours', 'Total Cycles', 'Storage Usage Rate'
    """
    # full load hours
    full_load_hours = storage_figures.discharge / storage_figures.power_discharge
    full_load_hours = full_load_hours.fillna(0)

    # total 
    total_cycle = storage_figures.discharge / storage_figures.capacity
    total_cycle = total_cycle.fillna(0)

    # max
    steps = get_timesteps(region)
    c_rate = storage_figures.power_discharge / storage_figures.capacity
    c_rate[c_rate > 1] = 1
    max_cycle = 1 / 2 * steps * c_rate
    max_cycle = max_cycle.fillna(0)

    # relative
    storage_usage_rate = total_cycle / max_cycle * 100
    storage_usage_rate = storage_usage_rate.fillna(0)

    # combine
    storage_ratios = pd.concat([full_load_hours, total_cycle, storage_usage_rate], axis=1,
                               keys=['Full Discharge Hours', 'Total Cycles', 'Utilization Rate'])
    storage_ratios = storage_ratios.swaplevel(axis=1)

    return storage_ratios


def plot_storage_ratios(storage_ratios, region, title):
    """plot storage ratios of either heat or electricity
    Parameters
    ----------
    storage_ratios : pd.DataFrame
        including 'Full Discharge Hours', 'Total Cycles', 'Utilization Rate'
    region : 
        region
    title : str
        title of the figures
    """
    stor_colors = {'Full Discharge Hours': colors[0],
                   'Total Cycles': colors[10],
                   'Utilization Rate': colors[20],
                   'ABW': 'crimson'}
    sub_titles = storage_ratios.columns.get_level_values(level=0).unique()
    rows = storage_ratios.sum(level=0, axis=1)
    subplot_size = (rows != 0).sum() / (rows != 0).sum().sum()
    subplot_size = subplot_size.replace(np.inf, 0)
    subplot_size = subplot_size.where(subplot_size <= 0.8, 0.8)
    subplot_size = subplot_size.where(subplot_size >= 0.2, 0.2)

    fig = make_subplots(rows=1, cols=2,
                        horizontal_spacing=0.2,
                        column_widths=list(subplot_size),
                        # column_widths=[0.2, 0.8],
                        subplot_titles=(sub_titles[0], sub_titles[1]),
                        specs=[[{"secondary_y": True}, {"secondary_y": True}]])

    for subplot, (stor, df_stor) in enumerate(storage_ratios.groupby(level=0, axis=1)):

        for ratio, df in df_stor[stor].items():

            secondary_y = True if ratio == 'Utilization Rate' else False
            visible = 'legendonly' if ratio == 'Full Discharge Hours' else True

            df = df[df != 0].dropna()
            ags = df.index
            df = df.rename(index=region.muns.gen.to_dict())
            hovertemplate = f'{ratio}: ' + '%{y:.2f}' + f' {UNITS[ratio]}'

            # municipalities
            fig.add_trace(
                go.Bar(x=df.index,
                       y=df.values,
                       orientation='v',
                       name=ratio,
                       legendgroup=ratio,
                       marker_color=stor_colors[ratio],
                       offsetgroup=ratio,
                       showlegend=bool(subplot),
                       visible=visible,
                       hovertemplate=hovertemplate),
                row=1, col=subplot + 1,
                secondary_y=secondary_y)

            # --- ABW ---
            if ratio == 'Total Cycles':
                fig.add_trace(
                    go.Scatter(x=df.index,
                               y=len(df)*[df.mean()],
                               orientation='v',
                               name='ABW',
                               legendgroup="ABW",
                               mode='lines',
                               line=dict(dash='dash'),
                               marker_color=stor_colors['ABW'],
                               showlegend=bool(subplot),
                               visible='legendonly',
                               hovertemplate=hovertemplate, ),
                    row=1, col=subplot + 1,
                    secondary_y=False)

                # === Layout ===
    fig.update_layout(title=title,
                      autosize=True,
                      hovermode="x unified",
                      legend=dict(traceorder='normal',
                                  orientation="h",
                                  yanchor="bottom",
                                  y=1.05,
                                  xanchor="right",
                                  x=1))

    fig.update_yaxes(title_text="Full Cycles/Discharge Hours", row=1, col=1, anchor="x", secondary_y=False)
    fig.update_yaxes(title_text="Full Cycles/Discharge Hours", row=1, col=2, anchor="x2", secondary_y=False)
    fig.update_yaxes(title_text="Utilization Rate %", row=1, col=1, anchor="x", secondary_y=True)
    fig.update_yaxes(title_text="Utilization Rate %", row=1, col=2, anchor="x2", secondary_y=True)
    fig.update_xaxes(type='category', tickangle=45)
    fig.show()


def plot_key_scenario_results(results_scns, scenarios, cmap_name='WindNODE', scenario_order=None):

    if cmap_name == 'WindNODE':
        cmap_dot_plot = n_colors((0, 200, 200), (255, 100, 0), len(scenarios))
        cmap_dot_plot = [unconvert_from_RGB_255(i) for i in cmap_dot_plot]
    else:
        cmap_dot_plot = sns.color_palette(cmap_name, len(scenarios))
    return_data = {}

    plots = {
        1: {'highlevel_results': [('Total costs electricity supply', 'EUR'),
                                  ('Total costs heat supply', 'EUR'),
                                  ('LCOE', 'EUR/MWh'),
                                  ('LCOH', 'EUR/MWh'),
                                  ('CO2 emissions el.', 'tCO2'),
                                  ('CO2 emissions th.', 'tCO2'),
                                  ('Electricity generation', 'MWh')],
            'results_axlxt': [],
            'col_order': ['Scenario', 'Total Costs [bnEUR]', 'LCOE [EUR/MWh]',
                          'LCOH [EUR/MWh]', 'Specific Emissions [g/kWh]'],
            'title': 'Costs and Emissions'
            },
        2: {'highlevel_results': [('Area required rel. Wind legal SQ (VR/EG)', '%'),
                                  ('Area required rel. PV ground H 0.1-perc agri', '%'),
                                  ('Electricity exports', 'MWh')],
            'results_axlxt': [('Intra-regional exchange', 'export', 'MWh')],
            'col_order': ['Scenario', 'RES Area Wind (VR/EG) [%]',
                          'RES Area PV ground [%]',
                          'Intra-reg. Exchange [TWh]',
                          'El. Exports [TWh]'],
            'title': 'Land Use and Energy Balance'
            },
        3: {'highlevel_results': [('Autarky', '%'), ('Net DSM activation', 'MWh'), ('Battery Storage Usage Rate', '%'),
                                  ('Heat Storage Usage Rate', '%')],
            'results_axlxt': [('DSM Capacities', 'Demand decrease', 'MWh')],
            'col_order': ['Scenario', 'Autarky [%]', 'El. Storage Use [%]',
                          'Heat Storage Use [%]', 'DSM Utilization Rate [%]'],
            'title': 'Flexibility Commitment'
            }
    }

    for no, params in plots.items():

        #####################################
        # get and process highlevel_results #
        #####################################
        data_hl = pd.DataFrame(
            ({f'{name} [{unit}]': results_scns[scn]['highlevel_results'][(name, unit)]
              for name, unit in params['highlevel_results']}
             for scn in scenarios),
            index=scenarios
        )

        if no == 1:
            data_hl['Total Costs [bnEUR]'] = (data_hl['Total costs electricity supply [EUR]'] +
                                              data_hl['Total costs heat supply [EUR]']) / 1e9
            data_hl['Emissions [MtCO2]'] = (data_hl['CO2 emissions el. [tCO2]'] +
                                            data_hl['CO2 emissions th. [tCO2]']) / 1e6
            data_hl['Specific Emissions [g/kWh]'] = data_hl['Emissions [MtCO2]'] / data_hl[
                'Electricity generation [MWh]'] * 1e9

            data_hl.drop(columns=['Total costs electricity supply [EUR]',
                                  'Total costs heat supply [EUR]',
                                  'CO2 emissions el. [tCO2]',
                                  'CO2 emissions th. [tCO2]',
                                  'Emissions [MtCO2]'],
                         inplace=True)
        elif no == 2:
            data_hl['Electricity exports [TWh]'] = data_hl['Electricity exports [MWh]'] / 1e6
            data_hl.drop(columns=['Electricity exports [MWh]'], inplace=True)

            col_mapping = {
                'Area required rel. Wind legal SQ (VR/EG) [%]': 'RES Area Wind (VR/EG) [%]',
                'Area required rel. PV ground H 0.1-perc agri [%]': 'RES Area PV ground [%]',
                'Electricity exports [TWh]': 'El. Exports [TWh]'
            }
            data_hl.rename(columns=col_mapping, inplace=True)
        elif no == 3:
            col_mapping = {"Battery Storage Usage Rate [%]": "El. Storage Use [%]",
                           "Heat Storage Usage Rate [%]": "Heat Storage Use [%]"}
            data_hl.rename(columns=col_mapping, inplace=True)

        #################################
        # get and process results_axlxt #
        #################################
        data_axlxt = pd.DataFrame(
            ({f'{name} [{unit}]': results_scns[scn]['results_axlxt'][name][col].sum(axis=0)
              for name, col, unit in params['results_axlxt']}
             for scn in scenarios),
            index=scenarios
        )
        if no == 1:
            data = data_hl
        if no == 2:
            data_axlxt['Intra-regional exchange [TWh]'] = data_axlxt['Intra-regional exchange [MWh]'] / 1e6
            data_axlxt.drop(columns=['Intra-regional exchange [MWh]'], inplace=True)

            col_mapping = {
                'Intra-regional exchange [TWh]': 'Intra-reg. Exchange [TWh]'
            }
            data_axlxt.rename(columns=col_mapping, inplace=True)
            data = pd.concat([data_hl, data_axlxt], axis=1)
        if no == 3:
            data_axlxt['DSM Utilization Rate [%]'] = data_hl['Net DSM activation [MWh]'] / data_axlxt[
                'DSM Capacities [MWh]'] * 1e2
            data_axlxt['DSM Utilization Rate [%]'] = data_axlxt['DSM Utilization Rate [%]'].fillna(0)
            data_axlxt.drop(columns=['DSM Capacities [MWh]'], inplace=True)
            data_hl.drop(columns=['Net DSM activation [MWh]'], inplace=True)
            data = pd.concat([data_hl, data_axlxt], axis=1)

        # # sort all plots by total costs
        # if no == 1:
        #     # data.sort_values(by='LCOE [EUR/MWh]', inplace=True)
        #     data.sort_values(by='Total Costs [bnEUR]', inplace=True)
        #     sort_order = data.index
        # else:
        #     data = data.reindex(sort_order)
        #
        # data = data.reset_index().rename(columns={'index': 'Scenario'})
        #
        if set(scenario_order) != set(scenarios):
            warnings.warn("scenario_order is not complete. Falling back to original order!")
            scenario_order = scenarios
        else:
            data = data.loc[scenario_order]
        data = data.reset_index().rename(columns={'index': 'Scenario'})

        # # reorder columns
        data = data[params['col_order']]

        g = sns.PairGrid(data,
                         x_vars=data.columns[1:], y_vars=['Scenario'],
                         height=10, aspect=.25)

        plt.subplots_adjust(top=0.9)
        # plt.suptitle(f'Key Results {no}/{len(plots.keys())}: {params["title"]}',
        plt.suptitle(f'Key Results {no}/{len(plots.keys())}',
                     size=20,
                     horizontalalignment='left')

        # Draw a dot plot using the stripplot function
        g.map(sns.stripplot, size=10, orient="h",
              palette=cmap_dot_plot,
              linewidth=1, edgecolor="w")

        # Set 2nd title for columns (top)
        titles = list(data.columns[1:])

        for ax, title in zip(g.axes.flat, titles):
            # Set a different title for each axes
            ax.set(title=title)

            # Make the grid horizontal instead of vertical
            ax.xaxis.grid(False)
            ax.yaxis.grid(True)

        sns.despine(left=True, bottom=True)

        return_data[no] = data

    return return_data


def calc_dsm_cap(region, hh_share=True):
    """calculate max dsm potential for each municipality
    Parameters
    ----------
    region : :class:`~.model.Region`
        Region object
    hh_share : bool, int
        share of dsm penetration, if True: scenario share is used
    Return
    ---------
    df_dsm_cap_up : pd.DataFrame
        max demand increase potential
    df_dsm_cap_down : pd.DataFrame
        max demand decrease potential
    """
    if 0 < hh_share < 1:
        pass
    elif hh_share:
        hh_share = region.cfg['scn_data']['flexopt']['dsm']['params']['hh_share']
    else:
        hh_share = 1

    dsm_cap_up = {ags: calc_dsm_cap_up(region.dsm_ts, ags,
                                       mode=region.cfg['scn_data']['flexopt']['dsm']['params']['mode']) for ags in
                  region.muns.index}
    df_dsm_cap_up = pd.DataFrame(dsm_cap_up).loc[region.cfg['date_from']:region.cfg['date_to']]
    df_dsm_cap_up = df_dsm_cap_up * hh_share

    dsm_cap_down = {ags: calc_dsm_cap_down(region.dsm_ts, ags,
                                           mode=region.cfg['scn_data']['flexopt']['dsm']['params']['mode']) for ags in
                    region.muns.index}
    df_dsm_cap_down = pd.DataFrame(dsm_cap_down).loc[region.cfg['date_from']:region.cfg['date_to']]
    df_dsm_cap_down = df_dsm_cap_down * hh_share

    return df_dsm_cap_up, df_dsm_cap_down


def get_emissions_sb_formated(results):
    """format emissions dataframe for sunburst"""
    data_el = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions el. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions el. var'].sum(axis=0),
    }).rename(index=PRINT_NAMES).reset_index().rename(columns={'index': 'technology'})
    data_el['sector'] = 'Power'

    data_th = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions th. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions th. var'].sum(axis=0),
    }).rename(index=PRINT_NAMES).reset_index().rename(columns={'index': 'technology'})
    data_th['sector'] = 'Heat'

    data_stor_el = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions stor el. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions stor el. var'].sum(axis=0),
    }).rename(index=PRINT_NAMES)
    data_stor_el.index.name = None
    data_stor_el = data_stor_el.reset_index().rename(columns={'index': 'technology'})
    data_stor_el['sector'] = 'Power'

    data_stor_th = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions stor th. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions stor th. var'].sum(axis=0),
    }).rename(index=PRINT_NAMES)
    data_stor_th.index.name = None
    data_stor_th = data_stor_th.reset_index().rename(columns={'index': 'technology'})
    data_stor_th['sector'] = 'Heat'

    data_grid = pd.DataFrame(columns=data_el.columns)
    data_grid.loc[0, 'fix'] = results['results_axlxt']['CO2 emissions grid total'].sum(axis=0) + \
                              results['results_axlxt']['CO2 emissions grid new total'].sum(axis=0)
    data_grid.loc[0, 'var'] = 0
    data_grid.loc[0, 'technology'] = 'Grid'
    data_grid.loc[0, 'sector'] = 'Grid'

    data = pd.concat([data_el, data_th, data_stor_el, data_stor_th, data_grid],
                     axis=0)

    data_fix = data.copy()
    data_var = data.copy()
    data_fix = data_fix.drop(columns=['var']).rename(columns={'fix': 'emissions'})
    data_fix['type'] = 'fix'
    data_var = data_var.drop(columns=['fix']).rename(columns={'var': 'emissions'})
    data_var['type'] = 'var'

    df_data = pd.concat([data_fix, data_var]).reset_index(drop=True)

    return df_data


def get_emissions_type_formatted(results):
    """format emissions dataframe per type for barplot"""
    # Electricity
    data_el = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions el. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions el. var'].sum(axis=0),
    })
    # Storage el
    data_stor_el = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions stor el. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions stor el. var'].sum(axis=0),
    })
    data_el = data_el.append(data_stor_el)
    # Grid
    data_el.loc['Grid', 'fix'] = results['results_axlxt']['CO2 emissions grid total'].sum(axis=0) + \
                                 results['results_axlxt']['CO2 emissions grid new total'].sum(axis=0)

    # Heat
    data_th = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions th. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions th. var'].sum(axis=0),
    })
    # Storage th
    data_stor_th = pd.DataFrame({
        'fix': results['results_axlxt']['CO2 emissions stor th. fix'].sum(axis=0),
        'var': results['results_axlxt']['CO2 emissions stor th. var'].sum(axis=0),
    })
    data_th = data_th.append(data_stor_th)

    # concat
    df_data = pd.concat([data_el, data_th, ], axis=1,
                        keys=['Electricity Supply', 'Heat Supply'], sort=True)

    df_data = df_data.fillna(0)
    # df_data = df_data[(df_data!=0).any(axis=1)]
    df_data = df_data.rename(index=PRINT_NAMES)

    return df_data

# ##########################
# ## multi scenario notebooks
# ##########################


scenario_order = ['StatusQuo',
                  'NEP_RE-',
                  'NEP_RE-_DSM',
                  'NEP_RE-_DSM+',
                  'NEP_RE-_BAT',
                  'NEP_RE-_BAT+',
                  'NEP_RE-_PTH',
                  'NEP_RE-_PTH+',
                  'NEP_RE-_DSM_BAT_PTH',
                  'NEP_RE-_DSM+_BAT+_PTH+',
                  'NEP_RE-_AUT80_DSM_BAT_PTH',
                  'NEP_RE-_AUT80_DSM+_BAT+_PTH+',
                  'NEP_RE-_AUT90_DSM_BAT_PTH',
                  'NEP_RE-_AUT90_DSM+_BAT+_PTH+',
                  'NEP',
                  'NEP_DSM_BAT_PTH',
                  'NEP_AUT90_DSM_BAT_PTH',
                  'NEP_DSM+_BAT+_PTH+',
                  'NEP_WIND+_DSM_BAT_PTH',
                  'NEP_WIND+_DSM+_BAT+_PTH+',
                  'NEP_PV+_DSM_BAT_PTH',
                  'NEP_PV+_DSM+_BAT+_PTH+',
                  'NEP_RE++_DSM_BAT_PTH',
                  'ISE_RE-',
                  'ISE_RE-_DSM',
                  'ISE_RE-_DSM+',
                  'ISE_RE-_BAT',
                  'ISE_RE-_BAT+',
                  'ISE_RE-_PTH',
                  'ISE_RE-_PTH+',
                  'ISE_RE-_DSM_BAT_PTH',
                  'ISE_RE-_DSM+_BAT+_PTH+',
                  'ISE_RE-_AUT80_DSM_BAT_PTH',
                  'ISE_RE-_AUT80_DSM+_BAT+_PTH+',
                  'ISE_RE-_AUT90_DSM++_BAT++_PTH++',
                  'ISE',
                  'ISE_DSM_BAT_PTH',
                  'ISE_DSM+_BAT+_PTH+',
                  'ISE_RE++_DSM_BAT_PTH']


def power_pot_land_use(regions_scns, scenarios):
    """draw bar chart to decribe the power potential restricted by land use scenarios"""
    # get potential areas per land use scenario
    pv_ground = pd.Series({f'{sc}_{faktor}': regions_scns['ISE'].pot_areas_pv_scn(
        scenario=sc, pv_usable_area_agri_max=2086 * faktor)['with_agri_restrictions'].sum()
                           for sc in ['HS', 'H'] for faktor in [0.1, 1, 2]})
    wind = pd.Series({sc: regions_scns['ISE'].pot_areas_wec_scn(
        scenario=sc).sum() * faktor for sc, faktor in zip(['SQ', 's1000f1', 's500f0', 's500f1'],
                                                          [1, 0.1, 0.1, 0.1])})
    pv_roof_tmp = regions_scns['ISE'].pot_areas_pv_roof.sum(axis=0)
    re_pot_config = regions_scns['ISE'].cfg['scn_data']['generation']['re_potentials']
    pv_roof = pd.Series(
        {'roof': pv_roof_tmp['area_resid_ha'] * re_pot_config['pv_roof_resid_usable_area'] +
                 pv_roof_tmp['area_ind_ha'] * re_pot_config['pv_roof_ind_usable_area']}
    )

    df_pot_area = pd.concat([pv_ground, pv_roof, wind], keys=['pv_ground', 'pv_roof', 'wind'])

    # Land use
    df_area = pd.DataFrame({scn: regions_scns[scn].cfg['scn_data']['generation']['re_potentials']
                            for scn in scenarios}).T
    df_land_use = pd.concat([
        df_area['pv_roof_land_use'],  # ha/Mwp
        df_area['pv_land_use'].rename('pv_ground_land_use'),  # ha/MWp
        (df_area['wec_land_use'] / df_area['wec_nom_power']).rename('wind_land_use')],  # ha /MW
        axis=1)

    highlight_dict = {
        'wind': {'Wind legal SQ \(VR/EG\)': '<b>Wind legal SQ (VR/EG)</b>'},
        'pv_ground': {'PV ground HS 0.1-perc agri': '<b>PV ground HS 0.1-perc agri</b>'},
        'pv_roof': {'PV rooftop': '<b>PV rooftop</b>'}
    }
    PRINT_NAMES_WO_REL = {k: v.replace('Area required rel. ', '') for k, v in PRINT_NAMES.items()}
    CMAP = {'wind': colors[0], 'pv_ground': colors[20], 'pv_roof': colors[10]}

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # potential Capacity
    for i, (tech, df) in enumerate(df_pot_area.groupby(level=0)):
        data = df.loc[tech] / df_land_use.loc['ISE', tech + '_land_use']
        data = data.rename(index=PRINT_NAMES_WO_REL)
        data.index = data.index.str.replace(list(highlight_dict[tech].keys())[0],
                                            list(highlight_dict[tech].values())[0])

        fig.add_trace(
            go.Bar(x=data.index,
                   y=data / 1e3,
                   orientation='v',
                   name=PRINT_NAMES_WO_REL[tech],
                   marker_color=CMAP[tech],
                   legendgroup=tech,
                   opacity=1,
                   offsetgroup=1,
                   hovertemplate='%{y:.1f} GW'))

        data = df.loc[tech] / df.loc[(tech, ['HS_0.1', 'roof', 'SQ'])].values * 100
        data = data.rename(index=PRINT_NAMES_WO_REL)
        data.index = data.index.str.replace(list(highlight_dict[tech].keys())[0],
                                            list(highlight_dict[tech].values())[0])

        fig.add_trace(
            go.Bar(x=data.index,
                   y=data,
                   orientation='v',
                   name='rel. to legal SQ',
                   marker_color='grey',
                   legendgroup=tech,
                   showlegend=True,
                   opacity=0.4,
                   offsetgroup=2,
                   hovertemplate='%{y:.1f} %'),
            secondary_y=True)

    fig.update_layout(title_text='RES Power Potential in Land Use Scenarios',
                      autosize=True,
                      barmode='group',
                      hovermode="x unified")

    fig.update_yaxes(title="GW", showspikes=True, secondary_y=False)
    fig.update_yaxes(title="%", showspikes=True, secondary_y=True)
    # fig.write_image("RES_power_potential_vs_Landuse_scenarios.png", format="png", scale=2, width=1080)
    fig.show()


def power_pot_scenarios(regions_scns, scenarios):
    """draw bar chart to decribe the power potential restricted by land use scenarios"""
    # define reference scenarios
    ref_scenarios = {
        'NEP 2035': {
            'RE-': 'NEP_RE-',
            'RE': 'NEP',
            'WIND+': 'NEP_WIND+_DSM_BAT_PTH',
            'PV+': 'NEP_PV+_DSM_BAT_PTH',
            'RE++': 'NEP_RE++_DSM_BAT_PTH'
        },
        'ISE 2050': {
            'RE-': 'ISE_RE-',
            'RE': 'ISE',
            'RE++': 'ISE_RE++_DSM_BAT_PTH'
        }
    }

    # Land use
    df_area = pd.DataFrame({scn: regions_scns[scn].cfg['scn_data']['generation']['re_potentials']
                            for scn in scenarios}).T
    df_land_use = pd.concat([
        df_area['pv_roof_land_use'],  # ha/Mwp
        df_area['pv_land_use'].rename('pv_ground_land_use'),  # ha/MWp
        (df_area['wec_land_use'] / df_area['wec_nom_power']).rename('wind_land_use')],  # ha /MW
        axis=1)

    # get capacity data
    re_caps=pd.concat([pd.DataFrame({
        'wind': [regions_scns[scn].muns['gen_capacity_wind'].sum()
                 for scn in ref_scenarios[year].values()],
        'pv_ground': [regions_scns[scn].muns['gen_capacity_pv_ground'].sum()
                      for scn in ref_scenarios[year].values()],
        'pv_roof': [(regions_scns[scn].muns['gen_capacity_pv_roof_small'].sum() +
                     regions_scns[scn].muns['gen_capacity_pv_roof_large'].sum())
                    for scn in ref_scenarios[year].values()]
    }, index=ref_scenarios[year].keys()) for year in ref_scenarios.keys()], keys=ref_scenarios.keys(), names=['year', 'scenario'])


    # get rel area data
    re_areas=pd.concat([pd.DataFrame({
        'wind': [regions_scns[scn].muns['gen_capacity_wind'].sum() *
                 df_land_use.loc[scn]['wind_land_use']
                 for scn in ref_scenarios[year].values()],
        'pv_ground': [regions_scns[scn].muns['gen_capacity_pv_ground'].sum() *
                      df_land_use.loc[scn]['pv_ground_land_use']
                      for scn in ref_scenarios[year].values()],
        'pv_roof': [(regions_scns[scn].muns['gen_capacity_pv_roof_small'].sum() + regions_scns[scn].muns['gen_capacity_pv_roof_large'].sum()) *
                    df_land_use.loc[scn]['pv_roof_land_use']
                    for scn in ref_scenarios[year].values()]
    }, index=ref_scenarios[year].keys()) for year in ref_scenarios.keys()], keys=ref_scenarios.keys(), names=['year', 'scenario'])

    # # merge WIND+ and PV+ and reorder
    # re_caps.loc[('NEP 2035', 'RE+'), :] = re_caps.loc[('NEP 2035', ('WIND+', 'PV+')),:].max()
    # re_caps.drop([('NEP 2035', 'WIND+'), ('NEP 2035', 'PV+')], inplace=True)
    #
    # re_areas.loc[('NEP 2035', 'RE+'), :] = re_areas.loc[('NEP 2035', ('WIND+', 'PV+')),:].max()
    # re_areas.drop([('NEP 2035', 'WIND+'), ('NEP 2035', 'PV+')], inplace=True)

    # order = [('NEP 2035', 'RE-'), ('NEP 2035', 'RE'), ('NEP 2035', 'RE+'), ('NEP 2035', 'RE++'),
    #          ('ISE 2050', 'RE-'), ('ISE 2050', 'RE'), ('ISE 2050', 'RE++')]

    order = [('NEP 2035', 'RE-'), ('NEP 2035', 'RE'), ('NEP 2035', 'WIND+'), ('NEP 2035', 'PV+'),
             ('NEP 2035', 'RE++'), ('ISE 2050', 'RE-'), ('ISE 2050', 'RE'), ('ISE 2050', 'RE++')]

    re_areas = re_areas.reindex(index=order)
    re_caps = re_caps.reindex(index=order)

    re_areas_ref = re_areas.copy()
    re_areas_ref['pv_roof'] = re_areas.loc['NEP 2035', 'RE++']['pv_roof'] # use pv roof pot. from RE++ as ref.

    # create rel. numbers
    re_areas_rel = pd.concat({'NEP 2035': re_areas.loc['NEP 2035'].div(re_areas_ref.loc['NEP 2035', 'RE-'])*100,
                              'ISE 2050': re_areas.loc['ISE 2050'].div(re_areas_ref.loc['ISE 2050', 'RE-'])*100})
    PRINT_NAMES_WO_REL = {k: v.replace('Area required rel. ', '') for k, v in PRINT_NAMES.items()}

    CMAP = {'wind': colors[0], 'pv_ground': colors[20], 'pv_roof': colors[10]}

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    xlabels = [list(re_areas_rel.index.get_level_values(1)),
               list(re_areas_rel.index.get_level_values(0)),
               re_areas_rel.index]

    for i, tech in enumerate(re_areas_rel.columns):
        fig.add_trace(go.Bar(y=re_caps[tech] / 1000,
                             x=xlabels,
                             name=PRINT_NAMES_WO_REL[tech],
                             marker_color=CMAP[tech],
                             showlegend=True,
                             legendgroup=tech,
                             orientation='v',
                             hovertemplate='%{y:.1f} GW'), )
        fig.add_trace(go.Bar(y=re_areas_rel[tech],
                             x=xlabels,
                             name='rel. to legal SQ',
                             marker_color='black',
                             showlegend=True,
                             width=0.07,
                             legendgroup=tech,
                             orientation='v',
                             hovertemplate='%{y:.1f} %',
                             opacity=0.5, ),
                      secondary_y=True)

    fig.update_layout(yaxis=dict(
                          titlefont_size=16,
                          tickfont_size=12),
                      title_text='RES Power Potential in RE Scenarios',
                      autosize=True,
                      barmode='group',
                      hovermode="x unified",)

    fig.update_yaxes(title="GW", showspikes=True, dtick=1, secondary_y=False)
    fig.update_yaxes(title="%", showspikes=True, dtick=100, secondary_y=True)
    #fig.write_image("RES_power_potential_vs_REx_scenarios.png", format="png", scale=2, width=1080)
    fig.show()