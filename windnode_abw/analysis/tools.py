import pandas as pd
from numpy import inf, nan
import papermill as pm
import os
from windnode_abw import __path__ as wn_path
from windnode_abw.tools import config
from windnode_abw.model.region.tools import calc_dsm_cap_up, calc_dsm_cap_down
import multiprocessing as mp


import logging
logger = logging.getLogger('windnode_abw')

INTERNAL_NAMES = {
    "stor_battery_large": "flex_bat_large",
    "stor_battery_small": "flex_bat_small",
    "stor_th_large": "th_cen_storage",
    "stor_th_small": "th_dec_pth_storage",
}

PRINT_NAMES = {
    'bhkw': "Large-scale CHP",
    'bio': "Biogas",
    'gas': "Open-cycle gas turbine",
    'gud': "Combined-cycle gas turbine",
    'hydro': "Hydro",
    'pv_ground': "PV ground-mounted",
    'pv_roof_large': "PV roof top (large)",
    'pv_roof_small': "PV roof top (small)",
    'wind': "Wind",
    "export" : "Export (national grid)",
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
    "pth_ASHP" : "Air source heat pump",
    "pth_ASHP_nostor" : "Air source heat pump, no storage",
    "pth_ASHP_stor" : "Air source heat pump, storage",
    "pth_GSHP" : "Ground source heat pump",
    "pth_GSHP_nostor" :"Ground source heat pump, no storage",
    "pth_GSHP_stor" : "Ground source heat pump, storage",
    "stor_th_large" : "Thermal storage (district heating)",
    "stor_th_small" : "Thermal storage",
    "flex_bat_large" : "Large-scale battery storage",
    "flex_bat_small" : "PV system battery storage",
    "hh" : "Households",
    "ind" : "Industry",
    "rca" : "CTS+agriculture",
    "conventional" : "Conventional",
    "el_hh" : "Electricity households",
    "el_rca" : "Electricity CTS+agriculture",
    "el_ind" : "Electricity industry",
    "th_hh_efh" : "Heat single-family houses",
    "th_hh_mfh" : "Heat apartment buildings",
    "th_rca": "Heat CTS+agriculture",
    "hh_efh" : "Single-family houses",
    "hh_mfh" : "Apartment buildings",
    "ABW-export": "Export (regional)",
    "ABW-import": "Import (regional)"
}

GEN_EL_NAMES = {
    "gud": {
        "params": "pp_natural_gas_cc",
        "params_comm": "comm_natural_gas"},
    "gas": {
        "params": "pp_natural_gas_sc",
        "params_comm": "comm_natural_gas"},
    "bhkw": {
        "params": "pp_bhkw",
        "params_comm": "comm_natural_gas"},
    'hydro': {
        "params": "hydro"},
    'pv_ground': {
        "params": "pv_ground"},
    'pv_roof_large': {
        "params": "pv_roof_large"},
    'pv_roof_small': {
        "params": "pv_roof_small"},
    'wind': {
        "params": "wind"},
    "bio": {
        "params": "bio"},  # plant emissions only, no commodity emissions!
    'import': {
        "params": None,
        "params_comm": "elenergy"}
}

GEN_TH_NAMES = {
    "elenergy": {
        "params": None,
        "params_comm": "elenergy"},
    "fuel_oil": {
        "params": "heating_fuel_oil",
        "params_comm": "comm_fuel_oil"},
    "gas_boiler": {
        "params": "pp_natural_gas_boiler",
        "params_comm": "comm_natural_gas"},
    "gud": {
        "params": "pp_natural_gas_cc",
        "params_comm": "comm_natural_gas"},
    "bhkw": {
        "params": "pp_bhkw",
        "params_comm": "comm_natural_gas"},
    "natural_gas": {
        "params": "heating_natural_gas",
        "params_comm": "comm_natural_gas"},
    "solar": {
        "params": "heating_solar"},
    "wood": {
        "params": "heating_wood",
        "params_comm": "comm_wood"},
    "coal": {
        "params": "heating_coal",
        "params_comm": "comm_coal"},
    "pth": {
        "params": "heating_rod",
        "params_comm": "elenergy"},
    "pth_ASHP": {
        "params": "heating_ashp",
        "params_comm": "elenergy"},
    "pth_GSHP": {
        "params": "heating_gshp",
        "params_comm": "elenergy"},
    "district_heating": {
        "params": "district_heating"
    }
}

UNITS = {
    'Grid losses': 'MWh',
    'Electricity generation': 'MWh',
    'Electricity demand': 'MWh',
    'Electricity demand for heating': 'MWh',
    'Electricity demand total': 'MWh',
    'Heating demand': 'MWh',
    'Electricity imports': 'MWh',
    'Electricity exports': 'MWh',
    'Electricity imports % of demand': '%',
    'Electricity exports % of demand': '%',
    'Balance': 'MWh',
    'Area required pv_roof_small': 'ha',
    'Area required pv_roof_large': 'ha',
    'Area required pv_ground': 'ha',
    'Area required wind': 'ha',
    'CO2 emissions el.': 'tCO2',
    'CO2 emissions th.': 'tCO2',
    'Net DSM activation': 'MWh',
    "Electricity storage losses": "MWh",
    "Heat storage losses": "MWh",
    "Area required rel. PV rooftop": "%",
    "Area required rel. PV rooftop small": "%",
    "Area required rel. PV rooftop large": "%",
    "Area required rel. PV ground (THIS SCENARIO)": "%",
    "Area required rel. PV ground H 0.1-perc agri": "%",
    "Area required rel. PV ground H 1-perc agri": "%",
    "Area required rel. PV ground H 2-perc agri": "%",
    "Area required rel. PV ground HS 0.1-perc agri": "%",
    "Area required rel. PV ground HS 1-perc agri": "%",
    "Area required rel. PV ground HS 2-perc agri": "%",
    "Area required rel. Wind (THIS SCENARIO)": "%",
    "Area required rel. Wind legal SQ (VR/EG)": "%",
    "Area required rel. Wind 1000m w forest 10-perc": "%",
    "Area required rel. Wind 500m wo forest 10-perc": "%",
    "Area required rel. Wind 500m w forest 10-perc": "%",
    "Total costs electricity supply": "EUR",
    "Total costs heat supply": "EUR",
    "LCOE": "EUR/MWh",
    "LCOH": "EUR/MWh",
    "Autarky": "%",
    "Autark hours": "%",
    "Heat Storage Usage Rate": "%",
    "Battery Storage Usage Rate": "%"
    }


def results_to_dataframes(esys, infeasible):
    """Convert result dict to DataFrames for flows and stationary variables.

    Parameters
    ----------
    esys : oemof.solph.EnergySystem
        Energy system including results
    infeasible : :obj:`bool`
        Model was infeasible

    Returns
    -------
    :obj:`dict`
        Results, content:
            :pandas:`pandas.DataFrame`
                DataFrame with flows, node pair as columns.
            :pandas:`pandas.DataFrame`
                DataFrame with stationary variables, (node, var) as columns.
                E.g. DSM measures dsm_up and dsm_do of DSM sink nodes.
            :pandas:`pandas.DataFrame`
                DataFrame with flow parameters, node pair as columns,
                params as index
            :pandas:`pandas.Series`
                Series with node parameters, (node, var) as index,
                labels is excluded
            :pandas:`pandas.Series`
                Investments of a flow, (node, bus) as index,
    """
    # add params to results
    results = {
        'params_flows': pd.DataFrame(
            {(str(from_n), str(to_n)): flow['scalars']
             for (from_n, to_n), flow in esys.results['params'].items()
             if to_n is not None}
        ),
        'params_stat': pd.Series(
            {(str(from_n), row): flow['scalars'].loc[row]
             for (from_n, to_n), flow in esys.results['params'].items()
             if to_n is None
             for row in flow['scalars'].index if row != 'label'}
        )
    }

    # add result vars to results only if there's a solution
    if not infeasible:
        results['flows'] = pd.DataFrame(
            {(str(from_n), str(to_n)): flow['sequences']['flow']
             for (from_n, to_n), flow in esys.results['main'].items()
             if to_n is not None}
        )
        results['vars_stat'] = pd.DataFrame(
            {(str(from_n), col): flow['sequences'][col]
             for (from_n, to_n), flow in esys.results['main'].items()
             if to_n is None
             for col in flow['sequences'].columns}
        )
        results['invest'] = pd.Series(
            {(str(from_n), str(to_n)): flow['scalars']['invest']
             for (from_n, to_n), flow in esys.results['main'].items()
             if not flow['scalars'].empty and "invest" in flow['scalars'].index.values}).rename("invest")

    return results


def aggregate_flows(results_raw):
    """Aggregate result flows and create result dictionary

    Notes
    -----
    * The node prefixes can be found in the Offline-Documentation (section 1.9)

    Parameters
    ----------
    results_raw : :obj:`dict`
        Results
    """

    # aggregations for flows, format:
    # {<TITLE>: {'pattern': <REGEX PATTERN OF NODE NAME>,
    #            'level': 0 for flow input, 1 for flow output}
    # }
    aggregations_flows = {
        'Stromerzeugung nach Technologie': {
            'pattern': 'gen_el_\d+_b\d+_(\w+)',
            'level': 0
        },
        'Strombedarf nach Sektor': {
            # Note for HH: only power demand without DSM is included
            'pattern': 'dem_el_\d+_b\d+_(\w+)',
            'level': 1
        },
        'Strombedarf nach Gemeinde': {
            # Note for HH: only power demand without DSM is included
            'pattern': 'dem_el_(\d+)_b\d+_\w+',
            'level': 1
        },
        'Wärmeerzeugung dezentral nach Technologie': {
            'pattern': 'gen_th_dec_\d+_\w+_(\w+)',
            'level': 0
        },
        'Wärmeerzeugung dezentral nach Sektor': {
            'pattern': 'gen_th_dec_\d+_((?:hh_efh|hh_mfh|rca))_\w+',
            'level': 0
        },
        'Wärmebedarf nach Sektor': {
            'pattern': 'dem_th_(?:dec|cen)_\d+_(\w+)',
            'level': 1
        },
        'Wärmebedarf nach Gemeinde': {
            'pattern': 'dem_th_\w+_(\d+)_\w+',
            'level': 1
        },
        'Wärmeerzeugung Wärmepumpen nach Technologie': {
            'pattern': 'flex_dec_pth_((?:A|G)SHP)_\w+_\d+_\w+',
            'level': 0
        },
        'Wärmeerzeugung Heizstäbe nach Gemeinde': {
            'pattern': 'flex_cen_pth_(\d+)',
            'level': 0
        },
        'Strombedarf Haushalte mit DSM nach Gemeinde': {
            'pattern': 'flex_dsm_(\d+)_b\d+',
            'level': 1
        },
        'Großbatterien: Einspeicherung nach Gemeinde': {
            'pattern': 'flex_bat_large_(\d+)_b\d+',
            'level': 1
        },
        'Großbatterien: Ausspeicherung nach Gemeinde': {
            'pattern': 'flex_bat_large_(\d+)_b\d+',
            'level': 0
        },
        'PV-Batteriespeicher: Einspeicherung nach Gemeinde': {
            'pattern': 'flex_bat_small_(\d+)_b\d+',
            'level': 1
        },
        'PV-Batteriespeicher: Ausspeicherung nach Gemeinde': {
            'pattern': 'flex_bat_small_(\d+)_b\d+',
            'level': 0
        },
        'Stromexport nach Spannungsebene': {
            'pattern': 'excess_el_(\w+)_b\d+',
            'level': 1
        },
        'Stromimport nach Spannungsebene': {
            'pattern': 'shortage_el_(\w+)_b\d+',
            'level': 0
        },
    }

    # aggregations for node variables, format:
    # {<TITLE>: {'pattern': <REGEX PATTERN OF NODE NAME>,
    #            'variable': <VARIABLE NAME>}
    # }
    aggregations_vars = {
        'Lasterhöhung DSM Haushalte nach Gemeinde': {
            'pattern': 'flex_dsm_(\d+)_b\d+',
            'variable': 'dsm_up'
        },
        'Lastreduktion DSM Haushalte nach Gemeinde': {
            'pattern': 'flex_dsm_(\d+)_b\d+',
            'variable': 'dsm_do'
        },
        'Speicherfüllstand Großbatterien nach Gemeinde': {
            'pattern': 'flex_bat_large_(\d+)_b\d+',
            'variable': 'capacity'
        },
        'Speicherfüllstand PV-Batteriespeicher nach Gemeinde': {
            'pattern': 'flex_bat_small_(\d+)_b\d+',
            'variable': 'capacity'
        },
        'Speicherfüllstand dezentrale Wärmespeicher (Wärmepumpen) nach Sektor': {
            'pattern': 'stor_th_dec_pth_\d+_((?:hh_efh|hh_mfh|rca))',
            'variable': 'capacity'
        },
        'Speicherfüllstand dezentrale Wärmespeicher (Wärmepumpen) nach Gemeinde': {
            'pattern': 'stor_th_dec_pth_(\d+)_(?:hh_efh|hh_mfh|rca)',
            'variable': 'capacity'
        },
        'Speicherfüllstand zentrale Wärmespeicher nach Gemeinde': {
            'pattern': 'stor_th_cen_(\d+)',
            'variable': 'capacity'
        },
    }

    results = {}

    # aggregation of flows
    for name, params in aggregations_flows.items():
        results[name] = results_raw['flows'].groupby(
            results_raw['flows'].columns.get_level_values(
                level=params['level']).str.extract(
                params['pattern'],
                expand=False),
            axis=1).agg('sum')

    # aggregation of stationary vars
    for name, params in aggregations_vars.items():
        if params["variable"] in results_raw["vars_stat"].columns.get_level_values(level=1):
            vars_df_filtered = results_raw['vars_stat'].xs(params['variable'],
                                                           level=1,
                                                           axis=1)
            results[name] = vars_df_filtered.groupby(
                vars_df_filtered.columns.get_level_values(level=0).str.extract(
                    params['pattern'],
                    expand=False),
                axis=1).agg('sum')
        else:
            results[name] = pd.DataFrame(
                0,
                index=results['Strombedarf nach Gemeinde'].index,
                columns=results['Strombedarf nach Gemeinde'].columns)

    for key, val in results.items():
        if key.endswith("nach Gemeinde"):
            val.columns= val.columns.astype(int)

    return results


def extract_line_flow(results_raw, region, level_flow_in=0, level_flow_out=1):
    bus_pattern = 'b_el_\w+'
    stubname = "line"
    line_suffix = "(?P<line_id>\d+)_b(?P<bus_from>\d+)_b(?P<bus_to>\d+)"
    line_bus_suffix = "_".join([line_suffix, "(?P<bus>\d+)"])
    line_pattern = "_".join([stubname, line_suffix])

    flows_extract = results_raw.loc[:,
                    results_raw.columns.get_level_values(level_flow_in).str.match(line_pattern)
                    & results_raw.columns.get_level_values(level_flow_out).str.match(bus_pattern)]

    # include bus id into other column level name
    if level_flow_in == 0:
        flows_extract.columns = [i + j.replace("b_el", "") for i, j in flows_extract.columns]
    else:
        flows_extract.columns = [j + i.replace("b_el", "") for i, j in flows_extract.columns]

    # format to long
    flows_extract.index.name = "timestamp"
    flows_extract = flows_extract.reset_index()
    flows_extracted_long = pd.wide_to_long(flows_extract,
                                           stubnames=stubname,
                                           i="timestamp", j="ags_tech", sep="_",
                                           suffix=line_bus_suffix)

    # introduce ags and technology as new index levels
    idx_new = [list(flows_extracted_long.index.get_level_values(0))]
    idx_split = flows_extracted_long.index.get_level_values(1).str.extract(line_bus_suffix)
    [idx_new.append(c[1].tolist()) for c in idx_split.iteritems()]
    flows_extracted_long.index = pd.MultiIndex.from_arrays(
        idx_new,
        names=["timestamp"] + list(idx_split.columns))

    # combine to separate flows on same line into one flow. direction is distinguished by sign:
    # positive: power goes from "from" to "to"; negative: power goes from "to" to "from"
    positive = flows_extracted_long.loc[
                flows_extracted_long.index.get_level_values(3 - level_flow_in)
                == flows_extracted_long.index.get_level_values(4)]
    positive.index = positive.index.droplevel("bus")
    negative = flows_extracted_long.loc[
                flows_extracted_long.index.get_level_values(3 - level_flow_out)
                == flows_extracted_long.index.get_level_values(4)]
    negative.index = negative.index.droplevel("bus")
    line_flows = positive["line"] - negative["line"]

    return line_flows


def extract_line_flow_imex(results_raw, level_flow_in=0, level_flow_out=1):

    stubname = "line"

    bus_pattern = "b_el_(?P<bus>(?:imex|\d+))"
    line_suffix = 'b(?P<non_region_bus>\d+)_b_el_(?P<imex>imex)'

    line_pattern = "_".join([stubname, line_suffix])
    line_bus_suffix = "_".join([line_suffix, bus_pattern])

    flows_extract = results_raw.loc[:,
                    results_raw.columns.get_level_values(level_flow_in).str.match(line_pattern)
                    & results_raw.columns.get_level_values(level_flow_out).str.match(bus_pattern)]

    if level_flow_in == 0:
        flows_extract.columns = [i + "_" + j for i, j in flows_extract.columns]
    else:
        flows_extract.columns = [j + "_" + i for i, j in flows_extract.columns]


    # format to long
    flows_extract.index.name = "timestamp"
    flows_extract = flows_extract.reset_index()
    flows_extracted_long = pd.wide_to_long(flows_extract,
                                           stubnames=stubname,
                                           i="timestamp", j="ags_tech", sep="_",
                                           suffix=line_bus_suffix)

    # introduce ags and technology as new index levels
    idx_new = [list(flows_extracted_long.index.get_level_values(0))]
    idx_split = flows_extracted_long.index.get_level_values(1).str.extract(line_bus_suffix)
    [idx_new.append(c[1].tolist()) for c in idx_split.iteritems()]
    flows_extracted_long.index = pd.MultiIndex.from_arrays(
        idx_new,
        names=["timestamp"] + list(idx_split.columns))

    # combine to separate flows on same line into one flow. direction is distinguished by sign:
    # positive: power goes from "from" to "to"; negative: power goes from "to" to "from"
    index_nlevels = flows_extracted_long.index.nlevels - 1
    positive = flows_extracted_long.loc[
                flows_extracted_long.index.get_level_values(index_nlevels - 1 - level_flow_in)
                == flows_extracted_long.index.get_level_values(index_nlevels)]
    positive.index = positive.index.droplevel("bus")
    negative = flows_extracted_long.loc[
                flows_extracted_long.index.get_level_values(index_nlevels - 1 - level_flow_out)
                == flows_extracted_long.index.get_level_values(index_nlevels)]
    negative.index = negative.index.droplevel("bus")
    line_flows = positive["line"] - negative["line"]
    line_flows.index = line_flows.index.droplevel("imex")

    return line_flows


def extract_flows_timexagsxtech(results_raw, node_pattern, bus_pattern, stubname,
                        level_flow_in=0, level_flow_out=1, unstack_col="technology"):
    """
    Extract flows keeping 3 dimensions: time, ags, tech

    Parameters
    ----------
    results_raw: dict of pd.DataFrame
        Return of :func:`~.results_to_dataframes`
    node_pattern: str
        RegEx pattern matching nodes
    bus_pattern: str
        RegEx pattern matching buses
    stubname: str
        Used in wide-to-long conversion to determine stub of column name that
        is preserved and which must be common across all nodes
    level_flow_in: int, optional
        Level which is treated an going into the flow
    level_flow_out: int, optional
        Level which is treated an going out of the flow

    Returns
    -------
    :class:`pd.DataFrame`
        Extracted and reformatted flows
    """

    # Get an extract of relevant flows
    flows_extract = results_raw.loc[:,
                    results_raw.columns.get_level_values(level_flow_in).str.match("_".join([
                        stubname, node_pattern]))
                    & results_raw.columns.get_level_values(level_flow_out).str.match(bus_pattern)]

    # transform to wide-to-long format while dropping bus column level
    flows_extract = flows_extract.sum(level=level_flow_in, axis=1)
    flows_extract.index.name = "timestamp"
    flows_extract = flows_extract.reset_index()
    flows_extracted_long = pd.wide_to_long(flows_extract, stubnames=stubname, i="timestamp", j="ags_tech", sep="_",
                                           suffix=node_pattern)

    # introduce ags and technology as new index levels
    idx_new = [list(flows_extracted_long.index.get_level_values(0))]
    idx_split = flows_extracted_long.index.get_level_values(1).str.extract(node_pattern)
    [idx_new.append(c[1].tolist()) for c in idx_split.iteritems()]
    flows_extracted_long.index = pd.MultiIndex.from_arrays(
        idx_new,
        names=["timestamp"] + list(idx_split.columns))

    # convert level ags to int
    flows_extracted_long.index = _ags_index2int(flows_extracted_long.index)

    # Sum over buses (aggregation) in one region and unstack technology
    flows_formatted = flows_extracted_long.sum(level=list(range(len(idx_new))))
    if unstack_col:
        flows_formatted = flows_formatted[stubname].unstack(unstack_col, fill_value=0)

    return flows_formatted


def extract_flow_params(flow_params_raw, node_pattern, bus_pattern, stubname,
                        level_flow_in=0, level_flow_out=1, params=None):

    pattern = "_".join([stubname, node_pattern])

    # Get an extract of relevant flows
    params_extract = flow_params_raw.loc[params,
                    flow_params_raw.columns.get_level_values(level_flow_in).str.match(pattern)
                    & flow_params_raw.columns.get_level_values(level_flow_out).str.match(bus_pattern)].astype(float)

    # transform to wide-to-long format while dropping bus column level
    params_extract = params_extract.sum(level=level_flow_in, axis=1).T
    params_extract.index = pd.MultiIndex.from_frame(params_extract.index.str.extract(pattern))
    params_extract = params_extract.sum(level=list(range(params_extract.index.nlevels)))

    # convert level ags to int
    params_extract.index = _ags_index2int(params_extract.index)

    return params_extract


def extract_stat_params(stat_params_raw, node_pattern, stubname, params=None):

    pattern = "_".join([stubname, node_pattern])

    params_extract = stat_params_raw.loc[
        stat_params_raw.index.get_level_values(0).str.match(pattern)]

    # transform to wide-to-long format and create multiindex from pattern groups
    params_extract = params_extract.unstack().droplevel(0, axis=1)
    params_extract.index = pd.MultiIndex.from_frame(
        params_extract.index.get_level_values(0).str.extract(pattern))

    # convert level ags to int
    params_extract.index = _ags_index2int(params_extract.index)

    return params_extract[params]


def extract_invest(vars, node_pattern, bus_pattern):

    # Get an extract of relevant data
    vars_extract = vars.loc[
                    vars.index.get_level_values(0).str.match(node_pattern),
                    vars.index.get_level_values(1).str.match(bus_pattern), :].astype(float)

    # transform to wide-to-long format while dropping bus column level
    vars_extract = vars_extract.max(level=0)
    vars_extract.index = pd.MultiIndex.from_frame(vars_extract.index.str.extract(node_pattern))
    vars_extract = vars_extract.sum(level=list(range(vars_extract.index.nlevels)))

    return vars_extract


def flow_params_agsxtech(results_raw):

    # define extraction pattern
    param_extractor = {
        "Stromerzeugung": {
            "node_pattern": "\w+_(?P<ags>\d+)_?b?\d*?_(?P<technology>\w+)",
            "stubname": "gen",
            "bus_pattern": 'b_el_\d+',
            "params": ["emissions", "nominal_value", "variable_costs"]},
        "Wärmeerzeugung": {
            "node_pattern": "th_(?P<level>\w{3})_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?_(?P<technology>\w+)",
            "stubname": "gen",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',
            "params": ["emissions", "nominal_value", "variable_costs"]},
        "Wärmeerzeugung PtH": {
            "node_pattern": "(?P<level>\w{3})_(?P<technology>\w+)_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "flex",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',
            "params": ["emissions", "nominal_value", "variable_costs"]},
        "Wärmespeicher": {
            "node_pattern": "(?P<level>\w{3})(?:_pth)?_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "stor_th",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',
            "params": ["emissions", "nominal_value", "variable_costs"]},
        "Grid": {
            "node_pattern": "(?P<line_id>\d+)_b(?P<bus_from>\d+)_b(?P<bus_to>\d+)",
            "stubname": "line",
            "bus_pattern": 'b_el_\d+',
            "params": ["emissions", "investment_ep_costs", "investment_existing", "nominal_value", "variable_costs"]}
    }

    params = {}
    for name, patterns in param_extractor.items():
        params[name] = extract_flow_params(results_raw, **patterns)

    return params


def stat_params_agsxtech(results_raw):

    # define extraction pattern
    param_extractor = {
        "Wärmespeicher": {
            "node_pattern": "(?P<level>\w{3})(?:_pth)?_(?P<ags>\d+)(?:_)?(?P<sector>hh_efh|hh_mfh|rca)?",
            "stubname": "stor_th",
            "params": ["nominal_storage_capacity"]}
    }

    params = {}
    results_raw = pd.DataFrame(results_raw)
    for name, patterns in param_extractor.items():
        params[name] = extract_stat_params(results_raw, **patterns)

    return params


def flows_timexagsxtech(results_raw, region):
    """
    Organized, extracted flows with dimensions time (x level) x ags x technology

    Parameters
    ----------
    results_raw: pd.DataFrame
        Flows of results_raw

    Returns
    -------
    dict of DataFrame
        Extracted flows
    """

    # define extraction pattern
    flow_extractor = {
        "Stromerzeugung": {
            "node_pattern": "\w+_(?P<ags>\d+)(?:_b\d+)?_(?P<technology>\w+)",
            "stubname": "gen",
            "bus_pattern": 'b_el_\d+'},
        "Wärmeerzeugung": {
            "node_pattern": "th_(?P<level>\w{3})_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?_(?P<technology>\w+)",
            "stubname": "gen",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',},
        "Wärmeerzeugung PtH": {
            "node_pattern": "(?P<level>\w{3})_(?P<technology>\w+)_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "flex",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?'},
        "Wärmespeicher discharge": {
            "node_pattern": "(?P<level>\w{3})(?:_pth)?_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "stor_th",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',
            "unstack_col": None},
        "Wärmespeicher charge": {
            "node_pattern": "(?P<level>\w{3})(?:_pth)?_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "stor_th",
            "bus_pattern": 'b_th_\w+_\d+(_\w+)?',
            "unstack_col": None,
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Batteriespeicher discharge": {
            "node_pattern": "(?P<level>\w+)_(?P<ags>\d+)_b\d+",
            "stubname": "flex_bat",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": None},
        "Batteriespeicher charge": {
            "node_pattern": "(?P<level>\w+)_(?P<ags>\d+)_b\d+",
            "stubname": "flex_bat",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": None,
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Stromnachfrage": {
            "node_pattern": "(?P<ags>\d+)_b\d+_(?P<sector>\w+)",
            "stubname": "dem_el",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": "sector",
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Wärmenachfrage": {
            "node_pattern": "(?P<level>\w+)_(?P<ags>\d+)_(?P<sector>\w+)",
            "stubname": "dem_th",
            "bus_pattern": 'b_th_(?:dec|cen_out)_\d+',
            "unstack_col": "sector",
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Stromexport": {
            "node_pattern": "(?P<level>\w+)_b(?P<bus>\d+)",
            "stubname": "excess_el",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": "level",
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Stromimport": {
            "node_pattern": "(?P<level>\w+)_b(?P<bus>\d+)",
            "stubname": "shortage_el",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": "level"},
        "Stromnachfrage Heizstab": {
            "node_pattern": "th_(?P<level>\w{3})_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?_(?P<technology>\w+)",
            "stubname": "gen",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": "technology",
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Stromnachfrage PtH": {
            "node_pattern": "(?P<level>\w{3})_(?P<technology>\w+)_(?P<ags>\d+)(?:_hh_efh|_hh_mfh|_rca)?",
            "stubname": "flex",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": "technology",
            "level_flow_in": 1,
            "level_flow_out": 0},
        "Stromnachfrage DSM HH": {
            "node_pattern": "(?P<ags>\d+)_b\d+",
            "stubname": "flex_dsm",
            "bus_pattern": 'b_el_\w+',
            "unstack_col": None,
            "level_flow_in": 1,
            "level_flow_out": 0},
        "GuD Dessau": {
            "node_pattern": "(th_cen_15001000_gud)",
            "stubname": "gen",
            "bus_pattern": 'b_gas',
            "unstack_col": None,
            "level_flow_in": 1,
            "level_flow_out": 0}
    }

    flows = {}
    for name, patterns in flow_extractor.items():
        # HOTFIX: create zero-filled DFs if results cannot be extracted
        # cf. https://github.com/windnode/WindNODE_ABW/pull/40
        try:
            flows[name] = extract_flows_timexagsxtech(results_raw, **patterns)
        except:
            logger.warning(f"Could not extract flows of '{name}' as it's not "
                           f"contained in the scenario results! Creating "
                           f"empty dataframe..")

            # create zero-filled DF for el. storages
            if name in ["Batteriespeicher charge",
                        "Batteriespeicher discharge"]:
                flows[name] = pd.DataFrame(
                    {'flex_bat': 0},
                    index=pd.MultiIndex.from_product(
                        [results_raw.index,
                         ['large', 'small'],
                         region.muns.index], names=['timestamp',
                                                                'level',
                                                                'ags'])
                )

            # create zero-filled DF for th. storages
            elif name in ["Wärmespeicher charge",
                          "Wärmespeicher discharge"]:
                flows[name] = pd.DataFrame(
                    {'stor_th': 0},
                    index=pd.MultiIndex.from_product(
                        [results_raw.index,
                         ['cen', 'dec'],
                         region.muns.index], names=['timestamp',
                                                                'level',
                                                                'ags'])
                )
            # create zero-filled DF for DSM demand
            elif name in ["Stromnachfrage DSM HH"]:
                flows[name] = pd.DataFrame(
                    {'flex_dsm': 0},
                    index=pd.MultiIndex.from_product(
                        [results_raw.index,
                         region.muns.index.astype(str)], names=['timestamp',
                                                                'ags'])
                )

            pass

    # Join Wärmeerzeugung into one DataFrame
    flows["Wärmeerzeugung"] = flows["Wärmeerzeugung"].join(flows["Wärmeerzeugung PtH"])
    flows.pop("Wärmeerzeugung PtH", None)

    # Join th. storage flows into one DF
    for stor in ["Wärmespeicher", "Batteriespeicher"]:
        flows[stor] = flows[stor + " discharge"].join(flows[stor + " charge"],
                                                      lsuffix="discharge",
                                                      rsuffix="charge")
        flows[stor].columns = flows[stor].columns.str.replace(flow_extractor[stor + " charge"]["stubname"], "")
        flows.pop(stor + " discharge")
        flows.pop(stor + " charge")


    # Grid lines
    line_flows_1 = extract_line_flow(results_raw, region)
    line_flows_2 = extract_line_flow(results_raw, region, level_flow_in=1, level_flow_out=0)
    flows["Stromnetz per bus"] = pd.concat(
        [line_flows_1.rename("out"),
         line_flows_2.rename("in")], axis=1)

    # Extract lines connecting ABW region to external, national grid via HV lines
    line_flows_region_1, line_flows_exchange_1 = _rename_external_hv_buses(line_flows_1, region)
    line_flows_region_2, line_flows_exchange_2 = _rename_external_hv_buses(line_flows_2, region)

    flows["Stromnetz"] = pd.concat(
        [line_flows_region_1.rename("out"),
         line_flows_region_2.rename("in")], axis=1)
    flows["Stromnetz exchange"] = pd.concat(
        [line_flows_exchange_1.rename("out"),
         line_flows_exchange_2.rename("in")], axis=1)

    # Extract IMEX lines
    line_flows_imex_1 = extract_line_flow_imex(results_raw)
    line_flows_imex_2 = extract_line_flow_imex(results_raw, level_flow_in=1, level_flow_out=0)

    flows["Stromnetz via external grid"] = pd.concat(
        [line_flows_imex_1.rename("out"),
         line_flows_imex_2.rename("in")], axis=1)
    region_export_imex = flows["Stromnetz via external grid"][flows["Stromnetz via external grid"]["in"] >= 0]["in"].rename("export")
    region_import_imex = flows["Stromnetz via external grid"][flows["Stromnetz via external grid"]["out"] <= 0]["out"].abs().rename("import")
    region_imex = pd.concat([region_export_imex, region_import_imex], axis=1).fillna(0)
    non_region_bus_translation = {_: non_region_bus2ags(_, region) for _ in
                                  region_imex.index.get_level_values("non_region_bus").unique()}
    region_imex = region_imex.rename(index=non_region_bus_translation)
    region_imex.index.set_names("ags", level="non_region_bus", inplace=True)

    # Intra-regional exchange as export (region feeds grid) and import (region gets supplied from grid)
    region_export_in_tmp = flows["Stromnetz"][flows["Stromnetz"]["in"] >= 0].groupby(["timestamp", "ags_from"])["in"].sum()
    region_export_in_tmp.index.set_names("ags", level="ags_from", inplace=True)
    region_export_out_tmp = flows["Stromnetz"][flows["Stromnetz"]["in"] < 0].abs().groupby(["timestamp", "ags_to"])["in"].sum()
    region_export_out_tmp.index.set_names("ags", level="ags_to", inplace=True)
    region_export_tmp = region_export_in_tmp.add(region_export_out_tmp, fill_value=0)

    region_import_in_tmp = flows["Stromnetz"][flows["Stromnetz"]["out"] >= 0].groupby(["timestamp", "ags_to"])[
        "out"].sum()
    region_import_in_tmp.index.set_names("ags", level="ags_to", inplace=True)
    region_import_out_tmp = flows["Stromnetz"][flows["Stromnetz"]["out"] < 0].abs().groupby(["timestamp", "ags_from"])[
        "out"].sum()
    region_import_out_tmp.index.set_names("ags", level="ags_from", inplace=True)
    region_import_tmp = region_import_in_tmp.add(region_import_out_tmp, fill_value=0)

    flows["Intra-regional exchange"] = pd.concat([region_export_tmp, region_import_tmp], axis=1).rename(
        columns={"in": "export", "out": "import"}).fillna(0)
    flows["Intra-regional exchange"] = pd.concat([flows['Intra-regional exchange'], region_imex]).sum(
        level=["timestamp", "ags"])
    flows["Intra-regional exchange"].index = _ags_index2int(flows["Intra-regional exchange"].index)

    # Assign electricity import/export (shortage/excess) to region's ags
    # and merge into Erzeugung/Nachfrage
    for key in ["Stromimport", "Stromexport"]:
        flows[key].rename(index=lambda b: non_region_bus2ags(b, region), level="bus", inplace=True)
        flows[key].rename_axis(index={'bus': 'ags'}, inplace=True)
        flows[key] = flows[key].sum(level=["timestamp", "ags"])
    flows["Stromerzeugung"]["import"] = flows["Stromimport"].sum(axis=1)
    flows["Stromnachfrage"]["export"] = flows["Stromexport"].sum(axis=1)
    flows["Stromerzeugung"] = flows["Stromerzeugung"].fillna(0)
    flows["Stromnachfrage"] = flows["Stromnachfrage"].fillna(0)

    # Electricity demand serving thermal demand
    flows["Stromnachfrage Wärme"] = pd.concat(
        [flows["Stromnachfrage Heizstab"], flows["Stromnachfrage PtH"]],
        axis=1).fillna(0)
    flows.pop("Stromnachfrage Heizstab")
    flows.pop("Stromnachfrage PtH")

    # Add electricity demand by HH with DSM to HH electricity demand
    flows["Stromnachfrage"]["hh"] = flows["Stromnachfrage"]["hh"] + flows["Stromnachfrage DSM HH"]["flex_dsm"]
    flows.pop("Stromnachfrage DSM HH")

    # Add autarky
    flows["Autarky"] = (1 - ((flows['Stromerzeugung']['import'] + flows["Intra-regional exchange"]["import"] +
                              flows["Batteriespeicher"].sum(level=["timestamp", "ags"])["discharge"]).sum(
        level=["timestamp", "ags"])).div(
        (flows['Stromnachfrage'].sum(axis=1) + flows['Stromnachfrage Wärme'].sum(axis=1).sum(
            level=["timestamp", "ags"]) + flows["Intra-regional exchange"]["export"] +
         flows["Batteriespeicher"].sum(level=["timestamp", "ags"])["charge"]).sum(level=["timestamp", "ags"]))) * 100
    flows["Autark hours"] = flows["Autarky"] >= 100

    # Join Dessau GuD data into one DF, need for extraction of variable efficiency,
    # cf. https://github.com/windnode/WindNODE_ABW/issues/33
    flows['GuD Dessau'] = (
        flows['GuD Dessau'].rename(columns={'gen': 'in_gas'}).reset_index(level=1, drop=True).join([
            flows['Stromerzeugung'].xs(
                15001000, level='ags').rename(columns={'gud': 'out_el'})['out_el'],
            flows['Wärmeerzeugung'].xs(
                15001000, level='ags').xs('cen', level='level').rename(columns={'gud': 'out_th'})['out_th']
    ]))

    return flows


def additional_results_txaxt(flow_results, params):

    # Line loadings
    flow_results["Line loading"] = pd.concat([flow_results["Stromnetz"], flow_results["Stromnetz exchange"]]).abs().max(axis=1).div(
        (params["Installed capacity grid"] + params["Newly installed capacity grid"]), axis="index")
    flow_results["Line loading per bus"] = flow_results["Stromnetz per bus"].abs().max(axis=1).div(
        (params["Installed capacity grid per bus"] + params["Newly installed capacity grid per bus"]), axis="index")

    return flow_results


def non_region_bus2ags(bus_id, region):

    bus_id = int(bus_id)

    # Try to translate directly to ags code (only applicable for EHV buses)
    ags = region.buses.loc[bus_id, "ags"]

    # For HV buses, the translation needs the intermediate step via the line
    if pd.isna(ags):
        region_bus = region.lines.loc[region.lines["bus0"] == bus_id, "bus1"]
        if region_bus.empty:
            region_bus = region.lines.loc[region.lines["bus1"] == bus_id, "bus0"]

        ags = region.buses.loc[region_bus, "ags"]

    return int(ags)


def _rename_external_hv_buses(df, region, merged=False):

    def _format_index(df):
        # drop line_id
        df.index = df.index.droplevel("line_id")

        # ...and aggregate to ags level
        df = df.sum(level=df.index.names)
        df.index.set_names(["ags_from", "ags_to"], level=["bus_from", "bus_to"], inplace=True)

        return df.loc[~(df.index.get_level_values("ags_from") == df.index.get_level_values("ags_to"))]

    # Rename all buses with ags code where ags code is available
    bus2ags = {str(k): str(int(v)) for k, v in region.buses["ags"].to_dict().items() if not pd.isna(v)}
    df.rename(index=bus2ags, inplace=True)

    df_from = df.loc[df.index.get_level_values("bus_from").str.len() == 5]
    idx_new_array_base = [
        df_from.index.get_level_values(name) for name in df_from.index.names if name not in ["bus_from", "bus_to"]]
    idx_new_bus_from = ["HV exchange " + str(i) for i in df_from.index.get_level_values("bus_to")]
    idx_new_array = idx_new_array_base + [
        idx_new_bus_from,
        df_from.index.get_level_values("bus_to")]
    df_from.index = pd.MultiIndex.from_arrays(idx_new_array, names=df_from.index.names)

    df_to = df.loc[df.index.get_level_values("bus_to").str.len() == 5]
    idx_new_array_base = [
        df_to.index.get_level_values(name) for name in df_to.index.names if name not in ["bus_from", "bus_to"]]
    idx_new_bus_to = ["HV exchange " + str(i) for i in df_to.index.get_level_values("bus_from")]
    idx_new_array = idx_new_array_base + [
        df_to.index.get_level_values("bus_from"),
        idx_new_bus_to]
    df_to.index = pd.MultiIndex.from_arrays(idx_new_array, names=df_to.index.names)

    df_new = pd.concat(
        [df_from, df_to])

    # Extract lines of regional grid (meaning lines inside region ABW)
    df = df.loc[
        (df.index.get_level_values("bus_from").str.len() != 5)
        & (df.index.get_level_values("bus_to").str.len() != 5)]

    df = _format_index(df)
    df_new = _format_index(df_new)

    if merged:
        df = pd.concat([df, df_new])

        return df, None

    else:
        return df, df_new
    
    
def _ags_index2int(idx):
    """Convert values ags index level ags to int"""
    # idx = pd.MultiIndex.from_arrays(
    #     idx_new,
    #     names=["timestamp"] + list(idx_split.columns))

    # Convert values ags index level ags to int
    new_level_names = []
    new_level_values = []
    for level in idx.levels:
        if level.name == "ags":
            new_level_values.append(idx.get_level_values(level.name).astype(int))
        else:
            new_level_values.append(idx.get_level_values(level.name))
        new_level_names.append(level.name)
    idx = pd.MultiIndex.from_arrays(
        new_level_values,
        names=new_level_names)

    # flows_extracted_long.index = idx

    return idx


def aggregate_parameters(region, results_raw, flows):

    def _extract_tech_params(NAMES):
        gen_keys = [v["params"] for k, v in NAMES.items() if v["params"] is not None]
        df = region.tech_assumptions_scn.loc[gen_keys].rename(
            index={v["params"]: k for k, v in NAMES.items()})
        mapped_commodity = pd.DataFrame.from_dict(
            {k: region.tech_assumptions_scn.loc[v["params_comm"], ["capex", "emissions_var"]].rename(
                {"capex": "opex_var_comm", "emissions_var": "emissions_var_comm"})
                for k, v in NAMES.items() if "params_comm" in v}, orient="index")
        df = df.join(mapped_commodity,
                     how="outer").fillna(0).replace({'sys_eff': {0: 1}})

        return df

    flows_params = flow_params_agsxtech(results_raw["params_flows"])

    params = {}

    # Electricity generators
    params["Parameters el. generators"] = _extract_tech_params(GEN_EL_NAMES)

    # Heat generators
    params["Parameters th. generators"] = _extract_tech_params(GEN_TH_NAMES)

    # overwrite CO2 emission factor of natural_gas incorporating the assumed methane share
    params["Parameters el. generators"].loc[["bhkw", "gud", "gas"], "emissions_var_comm"] = \
        params["Parameters el. generators"].loc[["bhkw", "gud", "gas"], "emissions_var_comm"] * (
                    1 - region.cfg['scn_data']['commodities']['methane_share'])
    params["Parameters th. generators"].loc[["bhkw", "gud", "gas_boiler", "natural_gas"], "emissions_var_comm"] = \
        params["Parameters th. generators"].loc[["bhkw", "gud", "gas_boiler", "natural_gas"], "emissions_var_comm"] * (
                1 - region.cfg['scn_data']['commodities']['methane_share'])

    # overwrite opex_var of natural_gas incorporating the assumed methane share
    params["Parameters el. generators"].loc[["bhkw", "gud", "gas"], "opex_var_comm"] = (
        params["Parameters el. generators"].loc[["bhkw", "gud", "gas"], "opex_var_comm"] * (
                    1 - region.cfg['scn_data']['commodities']['methane_share']) +
        region.tech_assumptions_scn.loc["comm_methane", "capex"] *
        region.cfg['scn_data']['commodities']['methane_share'])
    params["Parameters th. generators"].loc[["bhkw", "gud", "gas_boiler", "natural_gas"], "opex_var_comm"] = (
        params["Parameters th. generators"].loc[["bhkw", "gud", "gas_boiler", "natural_gas"], "opex_var_comm"] * (
                    1 - region.cfg['scn_data']['commodities']['methane_share']) +
        region.tech_assumptions_scn.loc["comm_methane", "capex"] *
        region.cfg['scn_data']['commodities']['methane_share'])

    # overwrite gud efficiencies by one calculated as in model.py
    gud_cfg = region.cfg['scn_data']['generation']['gen_th_cen']['gud_dessau']
    th_eff_max_ex = gud_cfg['efficiency_full_cond'] / (gud_cfg['cb_coeff'] + gud_cfg['cv_coeff'])
    el_eff_max_ex = gud_cfg['cb_coeff'] * th_eff_max_ex
    params["Parameters el. generators"].loc["gud", "sys_eff"] = el_eff_max_ex
    params["Parameters th. generators"].loc["gud", "sys_eff"] = th_eff_max_ex

    # overwrite bhkw efficiencies by one calculated as in model.py
    params["Parameters th. generators"].loc["bhkw", "sys_eff"] = \
        params["Parameters th. generators"].loc["bhkw", "sys_eff"] / \
        region.cfg['scn_data']['generation']['gen_th_cen']['bhkw']['pq_coeff']

    # overwrite emissions_fix in th. parameters for GuD and BHKW to 0
    # we account in the electricity sector for these emissions only
    params["Parameters th. generators"].loc[["gud", "bhkw"], "emissions_fix"] = 0

    # Speicher
    params["Parameters storages"] = region.tech_assumptions_scn[
        region.tech_assumptions_scn.index.str.startswith("stor_")].drop("sys_eff", axis=1)
    params["Parameters storages"].rename(index=INTERNAL_NAMES, inplace=True)

    # add parameters from config file to Speicher Dataframe
    additional_stor_params = {}
    additional_stor_columns = list(region.cfg['scn_data']['storage']['th_dec_pth_storage']["params"].keys())
    for tech in ["th_cen_storage", "th_dec_pth_storage"]:
        additional_stor_params[tech] = [
            region.cfg['scn_data']['storage'][tech]['params'][n] for n in additional_stor_columns]
    for tech in ['flex_bat_large', 'flex_bat_small']:
        additional_stor_params[tech] = [region.cfg['scn_data']['flexopt'][tech]['params'][n]
                                        for n in additional_stor_columns]

    params["Parameters storages"] = params["Parameters storages"].join(pd.DataFrame.from_dict(
        additional_stor_params,
        orient="index",
        columns=additional_stor_columns))

    # Grid parameters
    params["Parameters grid"] = region.tech_assumptions_scn.loc["line", :]

    # installed capacity battery storages
    params["Installierte Kapazität Großbatterien"] = region.batteries_large
    params["Installierte Kapazität PV-Batteriespeicher"] = region.batteries_small

    # Installed discharge(!) power heat storage
    params["Discharge power heat storage"] = flows_params["Wärmespeicher"][
        "nominal_value"].unstack("level").fillna(0).rename(columns={
        "cen": "stor_th_large", "dec": "stor_th_small"})

    # extract static vars from nodes
    stat_params = stat_params_agsxtech(results_raw['params_stat'])

    # Installed capacity heat storage
    params["Installed capacity heat storage"] = stat_params["Wärmespeicher"].astype(float).groupby(
        ['ags', 'level']).sum().unstack("level").droplevel(0, axis=1).rename(
        columns={"cen": "stor_th_large", "dec": "stor_th_small"}).fillna(0)

    # Installed capacity electricity supply
    params["Installed capacity electricity supply"] = \
        region.muns.loc[:, region.muns.columns.str.startswith("gen_capacity")]
    params["Installed capacity electricity supply"].columns = \
        params["Installed capacity electricity supply"].columns.str.replace("gen_capacity_", "")
    params["Installed capacity electricity supply"] = params["Installed capacity electricity supply"].drop(
        ["sewage_landfill_gas", "conventional_large", "conventional_small", "solar_heat"],
        axis=1)

    # Installed capacity from model results (include pre-calculations) gud, bhkw, gas
    capacity_special = flows_params["Stromerzeugung"]["nominal_value"].unstack("technology").fillna(0)[
        ["bhkw", "gas", "gud"]]
    capacity_special.at[15001000, 'gud'] = 60  # manual update of GuD Dessau's nom. el. power
    params["Installed capacity electricity supply"] = \
        params["Installed capacity electricity supply"].join(capacity_special, how="outer").fillna(0)

    # Installed capacity from model results (include pre-calculations) gud, bhkw, gas
    capacity_special = flows_params["Wärmeerzeugung"]["nominal_value"].sum(
        level=["ags", "technology"]).unstack("technology").fillna(0)[
        ["bhkw", "gas_boiler", "gud"]]
    capacity_special_pth = flows_params["Wärmeerzeugung PtH"]["nominal_value"].sum(
        level=["ags", "technology"]).unstack("technology").fillna(0)
    capacity_special_heating = flows['Wärmeerzeugung'].xs(
        "dec", level='level').groupby('ags').max()[
        [col for col in
         ["fuel_oil", "natural_gas", "elenergy", "solar", "wood"]
         if col in flows['Wärmeerzeugung']]
    ]

    params["Installed capacity heat supply"] = pd.concat(
        [capacity_special, capacity_special_pth, capacity_special_heating], axis=1)

    # Rename to ags
    line_capacity = flows_params["Grid"]["investment_existing"]
    params["Installed capacity grid per bus"] = line_capacity.copy()
    params["Installed capacity grid"] = _rename_external_hv_buses(line_capacity, region, merged=True)[0]

    # Newly installed capacity grid
    params["Newly installed capacity grid per bus"] = extract_invest(
        results_raw["invest"],
        "line_(?P<line_id>\d+)_b(?P<bus_from>\d+)_b(?P<bus_to>\d+)",
        'b_el_\d+')
    params["Newly installed capacity grid"] = _rename_external_hv_buses(
        params["Newly installed capacity grid per bus"].copy(),
        region, merged=True)[0]

    # Grid's equivalent periodic costs (EPC)
    params["Line EPC"] = flows_params["Grid"]["investment_ep_costs"]

    return params


def results_agsxlevelxtech(extracted_results, parameters, region):

    def _calculate_co2_emissions(name_part, generation, capacity, params):
        results_tmp = {}
        results_tmp["CO2 emissions {} var".format(name_part)] = ((
            generation * params["emissions_var"]).fillna( 0)) / 1e3

        if "emissions_var_comm" in params and "sys_eff" in params:
            emissions_commodity = (generation * params["emissions_var_comm"] / params["sys_eff"]).fillna(0) / 1e3
            results_tmp["CO2 emissions {} var".format(name_part)] = (
                        results_tmp["CO2 emissions {} var".format(name_part)] + emissions_commodity)
        results_tmp["CO2 emissions {} fix".format(name_part)] = (capacity *
                                                params["emissions_fix"] /
                                                params["lifespan"]
                                                ).fillna(0) / 1e3
        results_tmp["CO2 emissions {} total".format(name_part)] = \
            results_tmp["CO2 emissions {} fix".format(name_part)] + \
            results_tmp["CO2 emissions {} var".format(name_part)]

        return results_tmp

    def _calculate_supply_costs(capacity, generation, params, co2_certificate, annuity=None):
        """
        .. math:
            P_{inst} \cdot (Annuity + opex_{fix}) + E_{gen} * opex_{var} + E_{commodity} * opex_{var,commodity}
        """
        if annuity is None:
            annuity = params["annuity"]

        costs = {}

        costs["Fix costs"] = (capacity * (annuity + params["opex_fix"])).fillna(0)
        costs["Variable costs"] = (generation * params["opex_var"]).fillna(0)

        if "opex_var_comm" in params and "sys_eff" in params:
            costs["CO2 certificate cost"] = (
                    generation * params["emissions_var_comm"] * co2_certificate / params["sys_eff"]).fillna(0)
            costs_commodity = (generation * params["opex_var_comm"] / params["sys_eff"]).fillna(0)
            costs["Variable costs"] = costs["Variable costs"] + costs_commodity

        return costs

    def _get_timesteps(region):
        timestamps = pd.date_range(start=region.cfg['date_from'],
                                   end=region.cfg['date_to'],
                                   freq=region.cfg['freq'])
        steps = len(timestamps)

        return steps

    def _calculate_battery_storage_figures(parameters, battery_storages_muns):
        """"""
        stor_cap_small = parameters['Installierte Kapazität Großbatterien']
        stor_cap_large = parameters['Installierte Kapazität PV-Batteriespeicher']

        battery_storage_figures = pd.concat([stor_cap_small, stor_cap_large], axis=1, keys=['large', 'small'])

        storage = battery_storages_muns
        storage = storage.unstack("level").swaplevel(axis=1)
        storage.index = storage.index.astype(int)

        battery_storage_figures = battery_storage_figures.join(
            storage).sort_index(level=0, axis=1)
        battery_storage_figures = battery_storage_figures.swaplevel(axis=1)
        battery_storage_figures = battery_storage_figures.fillna(0)

        return battery_storage_figures

    def _calculate_heat_storage_figures(parameters, heat_storages_muns):
        """"""
        capacity = parameters['Installed capacity heat storage']
        capacity = capacity.rename(columns={'stor_th_large': 'cen',
            'stor_th_small': 'dec'})
        capacity.index = capacity.index.astype(int)

        power_discharge = parameters['Discharge power heat storage']
        power_discharge = power_discharge.rename(columns={'stor_th_large':'cen', 'stor_th_small':'dec'})

        discharge = heat_storages_muns
        discharge = discharge.discharge.unstack().fillna(0).T
        discharge.index = discharge.index.astype(int)

        # combine
        heat_storage_figures = pd.concat([capacity, power_discharge, discharge],
                                         axis=1, keys=['capacity', 'power_discharge', 'discharge'])
        heat_storage_figures = heat_storage_figures.fillna(0)

        return heat_storage_figures

    def _calculate_storage_ratios(storage_figures, region):
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
        steps = _get_timesteps(region)
        c_rate = storage_figures.power_discharge / storage_figures.capacity
        c_rate[c_rate > 1] = 1 # Issue #127
        max_cycle = 1/2 * steps * c_rate
        max_cycle = max_cycle.fillna(0)

        # relative
        storage_usage_rate = total_cycle / max_cycle * 100
        storage_usage_rate = storage_usage_rate.fillna(0)

        # combine
        storage_ratios = pd.concat([full_load_hours, total_cycle, storage_usage_rate],
                                   axis=1, keys=['Full Discharge Hours', 'Total Cycles', 'Utilization Rate'])
        storage_ratios = storage_ratios.swaplevel(axis=1)

        return storage_ratios

    def _calc_dsm_cap(region, hh_share=True):
        """calculate max dsm potential for each municipality
        Parameters
        ----------
        region : :class:`~.model.Region`
            Region object
        hh_share : bool, int
            share of dsm penetration, if True: scenario share is used
        Return
        ---------
        df_dsm_cap : pd.DataFrame
            max demand increase and decrease potential
        """
        if 0 < hh_share < 1:
            pass
        elif hh_share:
            hh_share = region.cfg['scn_data']['flexopt']['dsm']['params']['hh_share']
        else:
            hh_share = 1

        dsm_cap_up = {ags:calc_dsm_cap_up(region.dsm_ts, ags,
                         mode=region.cfg['scn_data']['flexopt']['dsm']['params']['mode']) for ags in region.muns.index}
        df_dsm_cap_up = pd.DataFrame(dsm_cap_up).loc[region.cfg['date_from']:region.cfg['date_to']]
        df_dsm_cap_up = df_dsm_cap_up * hh_share

        dsm_cap_down = {ags:calc_dsm_cap_down(region.dsm_ts, ags,
                         mode=region.cfg['scn_data']['flexopt']['dsm']['params']['mode']) for ags in region.muns.index}
        df_dsm_cap_down = pd.DataFrame(dsm_cap_down).loc[region.cfg['date_from']:region.cfg['date_to']]
        df_dsm_cap_down = df_dsm_cap_down * hh_share

        df_dsm_cap = pd.concat([df_dsm_cap_up.sum().rename('Demand increase'),
                     df_dsm_cap_down.sum().rename('Demand decrease')], axis=1)

        return df_dsm_cap

    idx = pd.IndexSlice

    results = {}

    co2_certificate_cost = region.tech_assumptions_scn.loc["emission"]["capex"]

    results["Stromerzeugung nach Gemeinde"] = extracted_results["Stromerzeugung"].sum(level="ags")
    results["Stromnachfrage nach Gemeinde"] = extracted_results["Stromnachfrage"].sum(level="ags")
    results["Stromnachfrage Wärme nach Gemeinde"] = extracted_results["Stromnachfrage Wärme"].sum(level="ags")
    results["Wärmeerzeugung nach Gemeinde"] = extracted_results["Wärmeerzeugung"].sum(level=["level", "ags"])
    results["Wärmenachfrage nach Gemeinde"] = extracted_results["Wärmenachfrage"].sum(level=["ags"])
    results["Wärmespeicher nach Gemeinde"] = extracted_results["Wärmespeicher"].sum(level=["level", "ags"])
    results["Batteriespeicher nach Gemeinde"] = extracted_results["Batteriespeicher"].sum(level=["level", "ags"])
    results["Stromnetzleitungen"] = extracted_results["Stromnetz"].sum(level=["ags_from", "ags_to"])
    results["Stromnetzleitungen per bus"] = extracted_results["Stromnetz per bus"].sum(
        level=["line_id", "bus_from", "bus_to"])
    results["Intra-regional exchange"] = extracted_results["Intra-regional exchange"].sum(level=["ags"])
    results["Net DSM activation"] = extracted_results["DSM activation"]["Demand increase"].sum(level="ags")

    # Losses in energy storages
    results["Electricity storage losses"] = (results["Batteriespeicher nach Gemeinde"]["charge"] -
                                             results["Batteriespeicher nach Gemeinde"]["discharge"]).unstack("level").fillna(0)
    results["Electricity storage losses"].columns = ["flex_bat_" + n for n in results["Electricity storage losses"].columns]
    results["Heat storage losses"] = (results["Wärmespeicher nach Gemeinde"]["charge"] -
                                      results["Wärmespeicher nach Gemeinde"]["discharge"]).unstack("level").fillna(
        0).rename(columns={"dec": "stor_th_small", "cen": "stor_th_large"})

    # Area requried by wind and PV
    re_params = region.cfg['scn_data']['generation']['re_potentials']

    if re_params['wec_installed_power'] == 'SQ':
        wind_area = pd.Series(0, index=region.muns.index, name='wind')
    else:
        wind_area = parameters["Installed capacity electricity supply"]["wind"] *\
                    re_params["wec_land_use"] / re_params["wec_nom_power"]
    if re_params['pv_installed_power'] == 'SQ':
        pv_ground_area = pd.Series(0, index=region.muns.index, name='pv_ground')
    else:
        pv_ground_area = parameters["Installed capacity electricity supply"]["pv_ground"] *\
                         re_params["pv_land_use"]

    results["Area required"] = pd.concat([
        parameters["Installed capacity electricity supply"]["pv_roof_small"] * re_params["pv_roof_land_use"],
        parameters["Installed capacity electricity supply"]["pv_roof_large"] * re_params["pv_roof_land_use"],
        pv_ground_area,
        wind_area,
    ], axis=1)

    # === Relative area required by wind and PV ===
    # PV roof
    results["Area required rel."] = pd.DataFrame()
    results["Area required rel."]["PV rooftop small"] = (
            results["Area required"]["pv_roof_small"] /
            region.pot_areas_pv_roof['area_resid_ha'] /
            re_params["pv_roof_resid_usable_area"] * 1e2
    ).fillna(0)
    results["Area required rel."]["PV rooftop large"] = (
            results["Area required"]["pv_roof_large"] /
            region.pot_areas_pv_roof['area_ind_ha'] /
            re_params["pv_roof_ind_usable_area"] * 1e2
    ).fillna(0)

    # PV ground
    results["Area required rel."]["PV ground HS 0.1-perc agri"] = (
            results["Area required"]["pv_ground"] /
            region.pot_areas_pv_scn(
                scenario='HS',
                pv_usable_area_agri_max=2086*0.1
            )['with_agri_restrictions'].groupby('ags_id').agg('sum') * 1e2
    ).replace(inf, 0).fillna(0) \
        if re_params['pv_land_use_scenario'] != 'SQ'\
        else pd.Series(0, index=results["Area required"]["pv_ground"].index)

    # wind
    results["Area required rel."][f"Wind 500m w forest 10-perc"] = (
            results["Area required"]["wind"] /
            (region.pot_areas_wec_scn(scenario='s500f1') * 0.1) * 1e2
    ).replace(inf, 0).fillna(0)
    results["Area required rel."]["Wind legal SQ (VR/EG)"] = (
            results["Area required"]["wind"] /
            region.pot_areas_wec_scn(scenario='SQ') * 1e2
    ).replace(inf, 0).fillna(0) \
        if re_params['wec_installed_power'] != 'SQ' \
        else pd.Series(0, index=results["Area required"]["wind"].index)

    # CO2 emissions electricity
    results_tmp_el = _calculate_co2_emissions(
        "el.",
        results["Stromerzeugung nach Gemeinde"],
        parameters["Installed capacity electricity supply"],
        parameters["Parameters el. generators"]
    )

    # fix el. emissions for GuD Dessau and BHKWs manually,
    # cf. https://github.com/windnode/WindNODE_ABW/issues/33
    results_tmp_el["CO2 emissions el. var"].at[15001000, 'gud'] = (
        (extracted_results["GuD Dessau"]['out_el'].sum() *
         parameters["Parameters el. generators"].at["gud", "emissions_var"]) +
        (extracted_results["GuD Dessau"]['out_el'] /
         (extracted_results["GuD Dessau"]['out_el'] + extracted_results["GuD Dessau"]['out_th']) *
         extracted_results["GuD Dessau"]['in_gas'] *
         parameters["Parameters el. generators"].at["gud", "emissions_var_comm"]
        ).sum()) / 1e3
    bhkw_gas_in = results["Stromerzeugung nach Gemeinde"]["bhkw"] / \
                  parameters["Parameters el. generators"].at["bhkw", "sys_eff"]
    results_tmp_el["CO2 emissions el. var"]["bhkw"] = (
        (results["Stromerzeugung nach Gemeinde"]["bhkw"] *
         parameters["Parameters el. generators"].at["bhkw", "emissions_var"]) +
        (bhkw_gas_in *
         parameters["Parameters el. generators"].at["bhkw", "sys_eff"] / (
         parameters["Parameters el. generators"].at["bhkw", "sys_eff"] +
         parameters["Parameters th. generators"].at["bhkw", "sys_eff"]
         ) *
         parameters["Parameters el. generators"].at["bhkw", "emissions_var_comm"]
    )) / 1e3
    results_tmp_el["CO2 emissions el. total"] = \
        results_tmp_el["CO2 emissions el. fix"] + \
        results_tmp_el["CO2 emissions el. var"]

    results.update(results_tmp_el)

    # CO2 emissions attributed to battery energy storages
    inst_cap_bat_tmp = pd.concat([
        parameters['Installierte Kapazität Großbatterien']["capacity"].rename("flex_bat_large"),
        parameters['Installierte Kapazität PV-Batteriespeicher']["capacity"].rename("flex_bat_small")], axis=1)
    discharge_stor_el_tmp = results['Batteriespeicher nach Gemeinde']["discharge"].unstack("level").rename(
        columns={"large": "flex_bat_large", "small": "flex_bat_small"})
    results_tmp_stor_el = _calculate_co2_emissions(
        "stor el.",
        discharge_stor_el_tmp,
        inst_cap_bat_tmp,
        parameters["Parameters storages"].loc[parameters["Parameters storages"].index.str.startswith("flex_bat"), :])
    results.update(results_tmp_stor_el)

    # CO2 emissions heat
    # Note: costs for the commodity of PtH technologies (pth* and elenergy) is set to zero, because these costs are
    # already included in the electricity generation costs
    params_heat_supply_tmp = parameters["Parameters th. generators"].loc[
        parameters["Parameters th. generators"].index != "district_heating"].copy()
    params_heat_supply_tmp.loc[["elenergy", "pth", "pth_ASHP", "pth_GSHP"], ["opex_var_comm", "emissions_var_comm"]] = 0
    for pth_tech in ["pth_ASHP", "pth_GSHP"]:
        params_heat_supply_tmp.loc[pth_tech + "_stor"] = params_heat_supply_tmp.loc[pth_tech]
        params_heat_supply_tmp.loc[pth_tech + "_nostor"] = params_heat_supply_tmp.loc[pth_tech]
        params_heat_supply_tmp.drop(pth_tech, inplace=True)
    heat_generation = results["Wärmeerzeugung nach Gemeinde"].sum(level="ags")
    results_tmp_th = _calculate_co2_emissions(
        "th.",
        heat_generation,
        parameters["Installed capacity heat supply"],
        params_heat_supply_tmp)

    # fix th. emissions for GuD Dessau and BHKWs manually,
    # cf. https://github.com/windnode/WindNODE_ABW/issues/33
    results_tmp_th["CO2 emissions th. var"].at[15001000, 'gud'] = (
        extracted_results["GuD Dessau"]['out_th'] /
        (extracted_results["GuD Dessau"]['out_el'] + extracted_results["GuD Dessau"]['out_th']) *
        extracted_results["GuD Dessau"]['in_gas'] *
        parameters["Parameters th. generators"].at["gud", "emissions_var_comm"]
    ).sum() / 1e3
    results_tmp_th["CO2 emissions th. var"]["bhkw"] = (
        bhkw_gas_in *
        parameters["Parameters th. generators"].at["bhkw", "sys_eff"] / (
            parameters["Parameters el. generators"].at["bhkw", "sys_eff"] +
            parameters["Parameters th. generators"].at["bhkw", "sys_eff"]
            ) *
        parameters["Parameters th. generators"].at["bhkw", "emissions_var_comm"]
    ) / 1e3
    results_tmp_th["CO2 emissions th. total"] = \
        results_tmp_th["CO2 emissions th. fix"] + \
        results_tmp_th["CO2 emissions th. var"]

    results.update(results_tmp_th)

    # CO2 emissions attributed to heat storages
    discharge_stor_th_tmp = results['Wärmespeicher nach Gemeinde']["discharge"].unstack("level").rename(
        columns={"cen": "stor_th_large", "dec": "stor_th_small"})
    stor_th_parameters = parameters["Parameters storages"].loc[
                         parameters["Parameters storages"].index.str.startswith("th_"), :].rename(
        index={"th_cen_storage": "stor_th_large",
               "th_dec_pth_storage": "stor_th_small"})
    results_tmp_stor_th = _calculate_co2_emissions(
        "stor th.",
        discharge_stor_th_tmp,
        parameters['Installed capacity heat storage'],
        stor_th_parameters)
    results.update(results_tmp_stor_th)

    # CO2 emissions attributed to grid
    line_lengths_tmp = region.lines.set_index("line_id")["length"]
    line_lengths_tmp.index = line_lengths_tmp.index.astype(str)
    line_capacity_length = parameters['Installed capacity grid per bus'].to_frame().join(line_lengths_tmp, on="line_id")
    line_capacity_length = line_capacity_length["investment_existing"] * line_capacity_length["length"]
    results["CO2 emissions grid total"] = _calculate_co2_emissions(
        "grid",
        results["Stromnetzleitungen per bus"]["in"].abs(),
        line_capacity_length,
        parameters["Parameters grid"])["CO2 emissions grid total"]

    line_lengths_new_tmp = region.lines.set_index("line_id")["length"]
    line_lengths_new_tmp.index = line_lengths_new_tmp.index.astype(str)
    line_capacity_length_new = parameters['Newly installed capacity grid per bus'].to_frame("investment_existing").join(
        line_lengths_new_tmp, on="line_id")
    line_capacity_length_new = line_capacity_length_new["investment_existing"] * line_capacity_length_new["length"]
    results["CO2 emissions grid new total"] = _calculate_co2_emissions(
        "grid new",
        results["Stromnetzleitungen per bus"]["in"].abs(),
        line_capacity_length_new,
        parameters["Parameters grid"])["CO2 emissions grid new total"]

    # Calculate supply costs
    # Note: Revenues for exported electricity are considered with negative costs
    costs_el_generation_tmp = _calculate_supply_costs(
        parameters["Installed capacity electricity supply"],
        results["Stromerzeugung nach Gemeinde"],
        parameters["Parameters el. generators"],
        co2_certificate_cost)
    # results["Total costs electricity supply"]
    # Export revenues calculated with constant electricity price of 75 EUR/MWh
    # TODO: if you include it, make sure sum of LCOE calculated in create_highlevel_results() ignore these revenues
    # export_revenues = results["Stromnachfrage nach Gemeinde"]["export"] * -parameters["Parameters el. generators"].loc[
    #     "import", "opex_var_comm"]
    # results["Total costs electricity supply"]["export"] = export_revenues

    # Calculate costs for electricity storages and add to el. supply costs df
    costs_el_storages_tmp = _calculate_supply_costs(
        inst_cap_bat_tmp,
        discharge_stor_el_tmp,
        parameters["Parameters storages"].loc[parameters["Parameters storages"].index.str.startswith("flex_bat"), :],
        co2_certificate_cost)

    # Calculate costs for grid
    results["Total costs lines"] = sum([d for d in _calculate_supply_costs(
        parameters['Installed capacity grid per bus'],
        results["Stromnetzleitungen per bus"]["in"].abs(),
        parameters["Parameters grid"],
        co2_certificate_cost,
        annuity=parameters["Line EPC"]).values()])
    results["Total costs line extensions"] = sum([d for d in _calculate_supply_costs(
        parameters['Newly installed capacity grid per bus'],
        results["Stromnetzleitungen per bus"]["in"].abs(),
        parameters["Parameters grid"],
        co2_certificate_cost,
        annuity=parameters["Line EPC"]).values()])

    # Merge costs data of several el. technologies
    for k in list(costs_el_generation_tmp.keys()):
        results[k + " el."] = pd.concat([c[k] for c in [costs_el_generation_tmp, costs_el_storages_tmp] if k in c], axis=1)
    results["Total costs electricity supply"] = results["Fix costs el."].\
        add(results["Variable costs el."], fill_value=0).\
        add(results["CO2 certificate cost el."], fill_value=0)

    # Calculate heat supply costs
    costs_heat_generation_tmp = _calculate_supply_costs(
        parameters["Installed capacity heat supply"],
        heat_generation,
        params_heat_supply_tmp,
        co2_certificate_cost)

    # Calculate costs for heat storages and add to heat supply costs df
    costs_heat_storages_tmp = _calculate_supply_costs(
        parameters['Installed capacity heat storage'],
        discharge_stor_th_tmp,
        stor_th_parameters,
        co2_certificate_cost)

    # Calculate costs for district heating, capex are multiplied with the peak load
    idx = pd.IndexSlice
    district_heating_dem = extracted_results["Wärmenachfrage"].loc[idx[:, "cen", :], :].sum(axis=1).rename(
        "district_heating")
    costs_heat_dist_heating = _calculate_supply_costs(
        district_heating_dem.max(level="ags"),
        district_heating_dem.sum(level="ags"),
        parameters["Parameters th. generators"].loc["district_heating"],
        co2_certificate_cost)

    # Merge costs data of several heat technologies
    for k in list(costs_heat_generation_tmp.keys()):
        results[k + " th."] = pd.concat([c[k] for c in [costs_heat_generation_tmp,costs_heat_storages_tmp,costs_heat_dist_heating] if k in c], axis=1).fillna(0)
    results["Total costs heat supply"] = results["Fix costs th."].\
        add(results["Variable costs th."], fill_value=0).\
        add(results["CO2 certificate cost th."], fill_value=0)

    # Autarky
    results["Autarky"] = results['Stromerzeugung nach Gemeinde'].drop(columns='import').sum(axis=1).div(
        results['Stromnachfrage nach Gemeinde'].drop(columns='export').sum(axis=1) +
        results['Stromnachfrage Wärme nach Gemeinde'].sum(axis=1)
    ) * 100
    results["Autark hours"] = extracted_results["Autark hours"].mean(level="ags") * 100

    # Battery Storage Figures/Ratios 
    results["Battery Storage Figures"] = _calculate_battery_storage_figures(parameters, results['Batteriespeicher nach Gemeinde'])
    results["Battery Storage Ratios"] = _calculate_storage_ratios(results["Battery Storage Figures"], region)
    results["Heat Storage Figures"] = _calculate_heat_storage_figures(parameters, results['Wärmespeicher nach Gemeinde'])
    results["Heat Storage Ratios"] = _calculate_storage_ratios(results["Heat Storage Figures"], region)

    # DSM Figures
    results["DSM Capacities"] = _calc_dsm_cap(region, hh_share=True)
    # if no DSM Capacities installed utilization rate is 0 as well
    if results["DSM Capacities"].all().sum() == 0:
        results["DSM Utilization Rate"] = results["DSM Capacities"]
    else:
        results["DSM Utilization Rate"] = (extracted_results['DSM activation'].sum(level='ags') / results["DSM Capacities"].values).fillna(0) *1e2

    return results


def results_tech(results_axlxt):
    """Derived results aggregated to entire region for individual technologies considered"""
    results = {}

    el_generation_tmp = {}
    for col in results_axlxt["Stromerzeugung nach Gemeinde"].columns:
        if col not in ["import", "export"]:
            el_generation_tmp[PRINT_NAMES[col]] = results_axlxt["Stromerzeugung nach Gemeinde"][col].sum()
    results["Electricity generation"] = pd.Series(el_generation_tmp)

    results["Heat generation"] = results_axlxt['Wärmeerzeugung nach Gemeinde'].sum().rename(PRINT_NAMES)
    results["CO2 emissions th. total"] = pd.concat([results_axlxt["CO2 emissions th. total"].sum(), results_axlxt["CO2 emissions stor th. total"].sum()]).rename(PRINT_NAMES)
    results["CO2 emissions el. total"] = pd.concat([
        results_axlxt["CO2 emissions el. total"].sum(),
        results_axlxt["CO2 emissions stor el. total"].sum()]).rename(PRINT_NAMES)
    results["CO2 emissions el. total"]["Grid"] = results_axlxt["CO2 emissions grid total"].sum()
    results["CO2 emissions el. total"]["Grid new"] = results_axlxt["CO2 emissions grid new total"].sum()
    results["Total costs electricity supply"] = results_axlxt["Total costs electricity supply"].sum()
    results["Total costs electricity supply"]["Grid"] = results_axlxt["Total costs lines"].sum()
    results["Total costs electricity supply"]["Grid new"] = results_axlxt["Total costs line extensions"].sum()
    results["Total costs heat supply"] = results_axlxt["Total costs heat supply"].sum()

    # Calculate levelized cost of electricity
    results["LCOE"] = results_axlxt["Total costs electricity supply"].sum() / (
                results_axlxt['Stromnachfrage nach Gemeinde'].sum().sum()
                + results_axlxt['Stromnachfrage Wärme nach Gemeinde'].sum().sum())

    # Calculate levelized cost of heat
    results["LCOH"] = results_axlxt["Total costs heat supply"].sum() / results_axlxt['Wärmenachfrage nach Gemeinde'].sum().sum()

    return results


def create_highlevel_results(results_tables, results_t, results_txaxt, region):
    """Aggregate results to scalar values for each scenario"""
    def _get_timesteps(region):
        timestamps = pd.date_range(start=region.cfg['date_from'],
                                   end=region.cfg['date_to'],
                                   freq=region.cfg['freq'])
        steps = len(timestamps)
        return steps

    def _calculate_storage_ratios_total(storage_figures, region):
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
        full_load_hours = storage_figures.discharge.sum().sum() / storage_figures.power_discharge.sum().sum()
        full_load_hours = 0 if full_load_hours == nan else full_load_hours

        # total
        total_cycle = storage_figures.discharge.sum().sum() / storage_figures.capacity.sum().sum()
        total_cycle = 0 if total_cycle == nan else total_cycle

        # max
        steps = _get_timesteps(region)
        c_rate = storage_figures.power_discharge.sum().sum() / storage_figures.capacity.sum().sum()
        c_crate = 1 if c_rate > 1 else c_rate
        #[c_rate > 1] = 1 # Issue #127
        max_cycle = 1/2 * steps * c_rate
        max_cycle = 0 if max_cycle == nan else max_cycle

        # relative
        storage_usage_rate = total_cycle / max_cycle * 100
        storage_usage_rate = 0 if storage_usage_rate == nan else storage_usage_rate

        # combine
        storage_ratios = pd.Series({'Full Discharge Hours':full_load_hours, 'Total Cycles':total_cycle, 'Utilization Rate':storage_usage_rate})

        return storage_ratios

    idx = pd.IndexSlice
    highlevel = {}

    # TODO: Netzverluste af IMEX lines fehlen, müssen aber berücksichtigt werden, da sie bei Stromimport/-export anfallen
    highlevel["Grid losses"] = (results_tables["Stromnetzleitungen"]["in"] - results_tables["Stromnetzleitungen"]["out"]).abs().sum()
    highlevel["Electricity generation"] = results_tables[
        "Stromerzeugung nach Gemeinde"].drop(columns='import').sum().sum()
    highlevel["Electricity demand"] = results_tables[
        "Stromnachfrage nach Gemeinde"].drop(columns='export').sum().sum()
    highlevel["Electricity demand for heating"] = results_tables["Stromnachfrage Wärme nach Gemeinde"].sum().sum()
    highlevel["Electricity demand total"] = highlevel["Electricity demand"] + highlevel["Electricity demand for heating"]
    highlevel["Heating demand"] = results_tables["Wärmenachfrage nach Gemeinde"].sum().sum()
    highlevel["Electricity imports"] = results_tables["Stromerzeugung nach Gemeinde"]["import"].sum()
    highlevel["Electricity exports"] = results_tables["Stromnachfrage nach Gemeinde"]["export"].sum()
    highlevel["Electricity imports % of demand"] = results_tables["Stromerzeugung nach Gemeinde"]["import"].sum() / \
                                           highlevel["Electricity demand total"] * 1e2
    highlevel["Electricity exports % of demand"] = results_tables["Stromnachfrage nach Gemeinde"]["export"].sum() / \
                                           highlevel["Electricity demand total"] * 1e2
    highlevel["Balance"] = highlevel["Electricity imports"] - highlevel["Electricity exports"]
    highlevel["Autarky"] = (highlevel["Electricity generation"] /
                            highlevel["Electricity demand total"] * 100)
    highlevel["Autark hours"] = (
            results_txaxt["Stromerzeugung"].drop(columns='import').sum(axis=1).sum(level="timestamp") >
            (results_txaxt['Stromnachfrage'].drop(columns='export').sum(axis=1).sum(level="timestamp") +
             results_txaxt['Stromnachfrage Wärme'].sum(axis=1).sum(level="timestamp"))
    ).mean() # mean of boolean is intended
    for re in results_tables["Area required"].columns:
        highlevel["Area required " + re] = results_tables["Area required"][re].sum()

    highlevel["CO2 emissions el."] = results_t["CO2 emissions el. total"].sum()
    highlevel["CO2 emissions th."] = results_t["CO2 emissions th. total"].sum()
    highlevel["Net DSM activation"] = results_tables["Net DSM activation"].sum()
    highlevel["Electricity storage losses"] = results_tables["Electricity storage losses"].sum().sum()
    highlevel["Heat storage losses"] = results_tables["Heat storage losses"].sum().sum()

    # === Area required relative to available area ===
    # PV roof
    re_params = region.cfg['scn_data']['generation']['re_potentials']
    highlevel["Area required rel. PV rooftop"] = (
            results_tables["Area required"][["pv_roof_small",
                                             "pv_roof_large"]].sum().sum() /
            ((region.pot_areas_pv_roof['area_resid_ha'].sum() * re_params["pv_roof_resid_usable_area"]) +
             (region.pot_areas_pv_roof['area_ind_ha'].sum() * re_params["pv_roof_ind_usable_area"]))
    ) * 1e2
    highlevel["Area required rel. PV rooftop small"] = (
            results_tables["Area required"]["pv_roof_small"].sum() /
            (region.pot_areas_pv_roof['area_resid_ha'].sum() * re_params["pv_roof_resid_usable_area"])
    ) * 1e2
    highlevel["Area required rel. PV rooftop large"] = (
            results_tables["Area required"]["pv_roof_large"].sum() /
            (region.pot_areas_pv_roof['area_ind_ha'].sum() * re_params["pv_roof_ind_usable_area"])
    ) * 1e2

    # PV ground
    highlevel["Area required rel. PV ground (THIS SCENARIO)"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario=re_params['pv_land_use_scenario'],
                pv_usable_area_agri_max=re_params['pv_usable_area_agri_max']
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    ) if re_params['pv_land_use_scenario'] != 'SQ' else 0
    highlevel[f"Area required rel. PV ground H 0.1-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='H',
                pv_usable_area_agri_max=2086*0.1
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )
    highlevel[f"Area required rel. PV ground H 1-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='H',
                pv_usable_area_agri_max=2086
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )
    highlevel[f"Area required rel. PV ground H 2-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='H',
                pv_usable_area_agri_max=2086*2
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )
    highlevel[f"Area required rel. PV ground HS 0.1-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='HS',
                pv_usable_area_agri_max=2086*0.1
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )
    highlevel[f"Area required rel. PV ground HS 1-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='HS',
                pv_usable_area_agri_max=2086
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )
    highlevel[f"Area required rel. PV ground HS 2-perc agri"] = (
            results_tables["Area required"]["pv_ground"].sum() /
            region.pot_areas_pv_scn(
                scenario='HS',
                pv_usable_area_agri_max=2086*2
            )['with_agri_restrictions'].groupby('ags_id').agg('sum').sum() * 1e2
    )

    # wind
    highlevel["Area required rel. Wind (THIS SCENARIO)"] = (
            results_tables["Area required"]["wind"].sum() /
            (region.pot_areas_wec_scn(
                scenario=re_params['wec_land_use_scenario']
            ).sum() *
             (0.1 if re_params['wec_land_use_scenario'] != 'SQ' else 1)) * 1e2
    )
    highlevel["Area required rel. Wind legal SQ (VR/EG)"] = (
            results_tables["Area required"]["wind"].sum() /
            region.pot_areas_wec_scn(scenario='SQ').sum() * 1e2
    )
    highlevel["Area required rel. Wind 1000m w forest 10-perc"] = (
            results_tables["Area required"]["wind"].sum() /
            (region.pot_areas_wec_scn(scenario='s1000f1').sum() * 0.1) * 1e2
    )
    highlevel["Area required rel. Wind 500m wo forest 10-perc"] = (
            results_tables["Area required"]["wind"].sum() /
            (region.pot_areas_wec_scn(scenario='s500f0').sum() * 0.1) * 1e2
    )
    highlevel["Area required rel. Wind 500m w forest 10-perc"] = (
            results_tables["Area required"]["wind"].sum() /
            (region.pot_areas_wec_scn(scenario='s500f1').sum() * 0.1) * 1e2
    )

    highlevel["Total costs electricity supply"] = results_t["Total costs electricity supply"].sum()
    highlevel["Total costs heat supply"] = results_t["Total costs heat supply"].sum()
    highlevel["LCOE"] = results_t["LCOE"].sum()
    highlevel["LCOH"] = results_t["LCOH"].sum()
    # if Battery Storages consist of empty Dataframe -> 0
    if results_tables['Battery Storage Figures']['capacity'].all().sum() == 0:
        highlevel['Battery Storage Usage Rate'] = 0
    else:
        highlevel['Battery Storage Usage Rate'] = _calculate_storage_ratios_total(results_tables['Battery Storage Figures'], region)['Utilization Rate']
    highlevel['Heat Storage Usage Rate'] = _calculate_storage_ratios_total(results_tables['Heat Storage Figures'], region)['Utilization Rate']

    # add multiindex including units to output
    mindex = [highlevel.keys(),
          [UNITS.get(item, '?') for item in highlevel.keys()]]
    mindex = list(zip(*mindex))
    mindex = pd.MultiIndex.from_tuples(mindex, names=['variable', 'unit'])
    highlevel = pd.Series(highlevel)
    highlevel.index= mindex
    
    return highlevel


def create_scenario_notebook(scenario, run_id,
                             template="scenario_analysis_template.ipynb",
                             output_path=os.path.join(wn_path[0], 'jupy'),
                             kernel_name=None,
                             force_new_results=False):

    # define data and paths
    input_template = os.path.join(wn_path[0], 'jupy', 'templates', template)
    output_name = "scenario_analysis_{scenario}.ipynb".format(scenario=scenario)
    output_notebook = os.path.join(output_path, output_name)

    # execute notebook with specific parameter
    try:
        pm.execute_notebook(input_template, output_notebook,
                            parameters={
                                "scenario": scenario,
                                "run_timestamp": run_id,
                                "force_new_results": force_new_results
                            },
                            request_save_on_cell_execute=True,
                            kernel_name=kernel_name)
    except FileNotFoundError:
        logger.warning(f'Template or output path not found, skipping...')
        return scenario
    except Exception as ex:
        logger.warning(f'Scenario {scenario}: An exception of type {type(ex).__name__} occurred:')
        logger.warning(ex)
        logger.warning(f'Scenario {scenario} skipped...')
        return scenario
    else:
        logger.info(f'Notebook created for scenario: {scenario}...')


def create_multiple_scenario_notebooks(scenarios, run_id,
                                       template="scenario_analysis_template.ipynb",
                                       output_path=os.path.join(wn_path[0], 'jupy'),
                                       num_processes=None,
                                       kernel_name=None,
                                       force_new_results=False):

    if isinstance(scenarios, str):
        scenarios = [scenarios]

    # get list of available scenarios in run id folder
    result_base_path = os.path.join(config.get_data_root_dir(),
                                    config.get('user_dirs',
                                               'results_dir')
                                    )
    avail_scenarios = [file.split('.')[0]
                       for file in os.listdir(os.path.join(result_base_path,
                                                           run_id))
                       if not file.startswith('.')]
    # get list of available scenarios for comparison
    all_scenarios = [file.split('.')[0]
                     for file in os.listdir(os.path.join(wn_path[0],
                                                         'scenarios'))
                     if file.endswith(".scn")]

    if len(all_scenarios) > len(avail_scenarios):
        logger.info(f'Available scenarios ({len(avail_scenarios)}) in run '
                    f'{run_id} differ from the total number of scenarios '
                    f'({len(all_scenarios)}).')

    # create scenario list
    if scenarios == ['all']:
        scenarios = avail_scenarios

    logger.info(f'Creating notebooks for {len(scenarios)} scenarios in {output_path} ...')

    pool = mp.Pool(processes=num_processes)

    errors = None
    for scen in scenarios:
        pool.apply_async(create_scenario_notebook,
                         args=(scen, run_id, template,),
                         kwds={"output_path": output_path,
                               "kernel_name": kernel_name,
                               "force_new_results": force_new_results}
                         )
    pool.close()
    pool.join()

    if errors is not None:
        logger.warning(f'Errors occured during creation of notebooks.')
    else:
        logger.info(f'Notebooks for {len(scenarios)} scenarios created without errors.')


def create_comparative_notebook(scenarios, run_id,
                                template="scenario_analysis_comparative_template.ipynb",
                                output_path=os.path.join(wn_path[0], 'jupy'),
                                kernel_name=None,
                                force_new_results=False):
    """Create comparative jupyter notebook with all scenarios"""

    if isinstance(scenarios, str):
        scenarios = [scenarios]

    # get list of available scenarios in run id folder
    result_base_path = os.path.join(config.get_data_root_dir(),
                                    config.get('user_dirs',
                                               'results_dir')
                                    )
    avail_scenarios = [file.split('.')[0]
                       for file in os.listdir(os.path.join(result_base_path,
                                                           run_id))
                       if not file.startswith('.')]
    # get list of available scenarios for comparison
    all_scenarios = [file.split('.')[0]
                     for file in os.listdir(os.path.join(wn_path[0],
                                                         'scenarios'))
                     if file.endswith(".scn")]

    if len(all_scenarios) > len(avail_scenarios):
        logger.info(f'Available scenarios ({len(avail_scenarios)}) in run '
                    f'{run_id} differ from the total number of scenarios '
                    f'({len(all_scenarios)}).')

    # create scenario list
    if scenarios == ['all']:
        scenarios = avail_scenarios

    logger.info(f'Creating comparative notebook for {len(scenarios)} scenarios in {output_path} ...')

    # define data and paths
    input_template = os.path.join(wn_path[0], 'jupy', 'templates', template)
    output_name = "scenario_analysis_comparative.ipynb"
    output_notebook = os.path.join(output_path, output_name)

    # execute notebook with specific parameters
    try:
        pm.execute_notebook(input_template, output_notebook,
                            parameters={
                                "scenarios": scenarios,
                                "run_timestamp": run_id,
                                "force_new_results": force_new_results
                            },
                            request_save_on_cell_execute=True,
                            kernel_name=kernel_name)
    except FileNotFoundError:
        logger.error(f'Template or output path not found.')
        raise FileNotFoundError
    except Exception as ex:
        logger.error(f'An exception of type {type(ex).__name__} occurred:')
        logger.error(ex)
        raise Exception
    else:
        logger.info(f'Comparative notebook successfully created!')
