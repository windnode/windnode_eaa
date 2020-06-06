import pandas as pd


NAMES = {
    "stor_battery_large": "flex_bat_large",
    "stor_battery_small": "flex_bat_small",
    "stor_th_large": "th_cen_storage",
    "stor_th_small": "th_dec_pth_storage",
}


def results_to_dataframes(esys):
    """Convert result dict to DataFrames for flows and stationary variables.

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
    """
    results = {
        'flows': pd.DataFrame(
            {(str(from_n), str(to_n)): flow['sequences']['flow']
             for (from_n, to_n), flow in esys.results['main'].items()
             if to_n is not None}
        ),
        'vars_stat': pd.DataFrame(
            {(str(from_n), col): flow['sequences'][col]
             for (from_n, to_n), flow in esys.results['main'].items()
             if to_n is None
             for col in flow['sequences'].columns}
        ),
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
            'pattern': 'flex_dec_pth_((?:A|G)SHP)_\d+_\w+',
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

    return results


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

    # Sum over buses (aggregation) in one region and unstack technology
    flows_formatted = flows_extracted_long.sum(level=list(range(len(idx_new))))
    if unstack_col:
        flows_formatted = flows_formatted[stubname].unstack(unstack_col, fill_value=0)

    return flows_formatted


def flows_timexagsxtech(results_raw):
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
            "node_pattern": "\w+_(?P<ags>\d+)_?b?\d+?_(?P<technology>\w+)",
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
    }

    flows = {}
    for name, patterns in flow_extractor.items():
        flows[name] = extract_flows_timexagsxtech(results_raw, **patterns)

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

    return flows


def aggregate_parameters(region):

    params = {}

    # Erzeugungseinheiten
    params["Erzeuger"] = region.tech_assumptions_scn[
        ~region.tech_assumptions_scn.index.str.startswith("stor_")]

    # Speicher
    params["Speicher"] = region.tech_assumptions_scn[
        region.tech_assumptions_scn.index.str.startswith("stor_")].drop("sys_eff", axis=1)
    params["Speicher"].rename(index=NAMES, inplace=True)

    # add parameters from config file to Speicher Dataframe
    additional_stor_params = {}
    additional_stor_columns = list(region.cfg['scn_data']['storage']['th_dec_pth_storage']["params"].keys())
    for tech in ["th_cen_storage", "th_dec_pth_storage"]:
        additional_stor_params[tech] = [
            region.cfg['scn_data']['storage'][tech]['params'][n] for n in additional_stor_columns]
    for tech in ['flex_bat_large', 'flex_bat_small']:
        additional_stor_params[tech] = [region.cfg['scn_data']['flexopt'][tech]['params'][n]
                                        for n in additional_stor_columns]

    params["Speicher"] = params["Speicher"].join(pd.DataFrame.from_dict(
        additional_stor_params,
        orient="index",
        columns=additional_stor_columns))

    # installed capacity battery storages
    params["Installierte Kapazität Großbatterien"] = region.batteries_large
    params["Installierte Kapazität PV-Batteriespeicher"] = region.batteries_small

    return params


def results_tables_ags(aggregated_results, extracted_results, parameters, region):

    results = {}

    results["Energienachfrage nach Gemeinde"] = pd.concat([
        aggregated_results["Strombedarf nach Gemeinde"].sum().rename("Strombedarf"),
        aggregated_results["Wärmebedarf nach Gemeinde"].sum().rename("Wärmebedarf")],
        axis=1)
    results["Stromerzeugung nach Gemeinde"] = extracted_results["Stromerzeugung"].sum(level="ags")
    results["Stromnachfrage nach Gemeinde"] = extracted_results["Stromnachfrage"].sum(level="ags")
    results["Wärmeerzeugung nach Gemeinde"] = extracted_results["Wärmeerzeugung"].sum(level=["level", "ags"])
    results["Wärmenachfrage nach Gemeinde"] = extracted_results["Wärmenachfrage"].sum(level=["level", "ags"])
    results["Wärmespeicher nach Gemeinde"] = extracted_results["Wärmespeicher"].sum(level=["level", "ags"])
    results["Batteriespeicher nach Gemeinde"] = extracted_results["Batteriespeicher"].sum(level=["level", "ags"])

    return results