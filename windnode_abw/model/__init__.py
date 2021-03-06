import pickle
import os
import pandas as pd

import logging
logger = logging.getLogger('windnode_abw')

from windnode_abw.tools import config
from windnode_abw.tools.data_io import import_db_data
from windnode_abw.model.region.tools import \
    prepare_feedin_timeseries, prepare_demand_timeseries, \
    prepare_temp_timeseries, preprocess_heating_structure, \
    calc_annuity, distribute_large_battery_capacity, \
    distribute_small_battery_capacity, calc_available_pv_capacity, \
    calc_available_pv_roof_capacity, calc_available_wec_capacity


class Region:
    """Defines the model for ABW region

    Attributes
    ----------
    _name : :obj:`str`
        Name of network
    _cfg : :obj:`dict`
        Run configuration such as timerange, solver, scenario, ...
    _buses : :pandas:`pandas.DataFrame`
        Region's buses
    _lines : :pandas:`pandas.DataFrame`
        Region's lines
    _trafos : :pandas:`pandas.DataFrame`
        Region's transformers
    _subst : :pandas:`pandas.DataFrame`
        Region's substations
    _generators : :pandas:`pandas.DataFrame`
        Region's renewable and conventional generators

    _results_lines : :pandas:`pandas.DataFrame`
        Line loading results

    _demand_ts_init : :pandas:`pandas.DataFrame`
        Original absolute demand (electrical+thermal) timeseries per
        municipality and sector
    _demand_ts : :obj:`dict` of :pandas:`pandas.DataFrame`
        Absolute demand timeseries per demand sector (dict key) and
        municipality (DF column)
    _feedin_ts_init : :pandas:`pandas.DataFrame`
        Original normalized feedin timeseries of renewable and conventional
        generators per municipality and technology/type
    _feedin_ts : :obj:`dict` of :pandas:`pandas.DataFrame`
        Absolute feedin timeseries per technology/type (dict key) and
        municipality (DF column)
    _dsm_ts : :pandas:`pandas.DataFrame`
        DSM timeseries per load band and municipality (MultiIndex columns)
    _temp_ts : :obj:`dict` of :pandas:`pandas.DataFrame`
        Temperature timeseries (air and soil -> dict key) per municipality in
        degree Celsius
    _heating_structure_dec : :pandas:`pandas.DataFrame`
        Decentral heating structure of thermal loads per scenario,
        municipality, sector and energy source
        Unlike the heating structure in DB table
        :class:`WnAbwHeatingStructure <windnode.config.db_models.WnAbwHeatingStructure>`
        which includes district heating,
        the shares of energy sources sum up to 1 per municipality.
    _tech_assumptions : :pandas:`pandas.DataFrame`
        Technical assumptions (costs, lifespan, emissions, system efficiency)
        per technbology and scenario
    """
    def __init__(self, **kwargs):
        self._name = 'ABW region'
        self._cfg = kwargs.get('cfg', None)

        self._muns = kwargs.get('muns', None)
        self._buses = kwargs.get('buses', None)
        self._lines = kwargs.get('lines', None)
        self._trafos = kwargs.get('trafos', None)
        self._subst = kwargs.get('subst', None)
        self._generators = kwargs.get('generators', None)

        self._results_lines = kwargs.get('_results_lines', None)

        self._pot_areas_pv = kwargs.get('pot_areas_pv', None)
        self._pot_areas_pv_roof = kwargs.get('pot_areas_pv_roof', None)
        self._pot_areas_wec = kwargs.get('pot_areas_wec', None)

        # update mun data table using RE potential areas
        self._muns.update(calc_available_pv_capacity(self))
        self._muns.update(calc_available_pv_roof_capacity(self))
        self._muns.update(calc_available_wec_capacity(self))

        self._demography = kwargs.get('demography', None)

        self._demand_ts_init = kwargs.get('demand_ts_init', None)
        self._dsm_ts = kwargs.get('dsm_ts', None)
        self._demand_ts, self._dsm_ts = prepare_demand_timeseries(self)

        self._feedin_ts_init = kwargs.get('feedin_ts_init', None)
        self._feedin_ts = prepare_feedin_timeseries(self)

        self._temp_ts_init = kwargs.get('temp_ts_init', None)
        self._temp_ts = prepare_temp_timeseries(self)

        self._heating_structure_dec,\
        self._dist_heating_share = preprocess_heating_structure(
            cfg=self._cfg,
            heating_structure=kwargs.get('heating_structure', None)
        )

        self._tech_assumptions = calc_annuity(
            cfg=self._cfg,
            tech_assumptions=kwargs.get('tech_assumptions', None)
        )

        self._batteries_large = distribute_large_battery_capacity(self)
        self._batteries_small = distribute_small_battery_capacity(self)

    @property
    def muns(self):
        """Returns region's municipalities"""
        return self._muns

    @property
    def cfg(self):
        """Returns run config"""
        return self._cfg

    @cfg.setter
    def cfg(self, cfg):
        self._cfg = cfg

    @property
    def buses(self):
        """Returns region's buses"""
        return self._buses

    @property
    def lines(self):
        """Returns region's lines"""
        return self._lines

    @property
    def trafos(self):
        """Returns region's transformers"""
        return self._trafos

    @property
    def subst(self):
        """Returns region's substations"""
        return self._subst

    @property
    def generators(self):
        """Returns region's generators (renewable and conventional)"""
        return self._generators

    @property
    def geno_res_grouped(self):
        """Returns grouped region's RES generators

        Data is grouped by HV-MV-substation id and generation type,
        count of generators and sum of nom. capacity is returned.

        Returns
        -------
        :pandas:`pandas.DataFrame`
            Grouped RES generators with MultiIndex
        """
        # access: e.g. df.loc[2303, 'gas']
        # consider to reset index to convert index cols to regular cols
        # ToDo: Revise this method

        return self.geno_res.groupby(['subst_id', 'generation_type'])[
            'capacity'].agg(['sum', 'count'])#.reset_index()

    @property
    def results_lines(self):
        return self._results_lines

    @results_lines.setter
    def results_lines(self, results_lines):
        self._results_lines = results_lines

    @property
    def demand_ts_init(self):
        return self._demand_ts_init

    @property
    def demand_ts(self):
        return self._demand_ts

    def demand_ts_agg_per_mun(self, sectors):
        """Returns demand sum per municipality

        Parameters
        ----------
        sectors : :obj:`list` of :obj:`str`
            Sectors to be included, e.g. ['el_hh', 'el_rca']

        Returns
        -------
        :pandas:`pandas.DataFrame`
            Aggregated demand with muns as columns
        """
        if not all([sec in self._demand_ts.keys() for sec in sectors]):
            raise ValueError('At least 1 sector not found!')

        return pd.DataFrame(
            {ags: sum(self._demand_ts[tech][ags]
                      for tech in sectors)
             for ags in self._muns.index})

    @property
    def feedin_ts_init(self):
        return self._feedin_ts_init

    @feedin_ts_init.setter
    def feedin_ts_init(self, feedin_ts_init):
        self._feedin_ts_init = feedin_ts_init

    @property
    def feedin_ts(self):
        return self._feedin_ts

    def feedin_ts_agg_per_mun(self, techs):
        """Returns feedin sum per municipality

        Parameters
        ----------
        techs : :obj:`list` of :obj:`str`
            Technologies to be included, e.g. ['wind', 'bio']

        Returns
        -------
        :pandas:`pandas.DataFrame`
            Aggregated feedin with muns as columns
        """
        if not all([tech in self._feedin_ts.keys() for tech in techs]):
            raise ValueError('At least 1 technology not found!')

        return pd.DataFrame(
            {ags: sum(self._feedin_ts[tech][ags]
                      for tech in techs)
             for ags in self._muns.index})

    @property
    def dsm_ts(self):
        return self._dsm_ts

    @property
    def temp_ts_init(self):
        return self._temp_ts_init

    @property
    def temp_ts(self):
        return self._temp_ts

    @property
    def heating_structure_dec(self):
        """Return heating structure (relative shares) for all scenarios
        WITHOUT district heating.

        Unlike the heating structure in DB table
        :class:`WnAbwHeatingStructure <windnode.config.db_models.WnAbwHeatingStructure>`
        which includes district heating,
        the shares of energy sources sum up to 1 per municipality.
        """
        return self._heating_structure_dec

    @property
    def heating_structure_dec_scn(self):
        """Return decentral heating structure (relative shares) for year set
        in cfg WITHOUT district heating.

        Unlike the heating structure in DB table
        :class:`WnAbwHeatingStructure <windnode.config.db_models.WnAbwHeatingStructure>`
        which includes district heating,
        the shares of energy sources sum up to 1 per municipality.
        """
        return self._heating_structure_dec.xs(
            self._cfg['scn_data']['general']['year'],
            level='year'
        )

    @property
    def heating_structure_dec_scn_wo_solar(self):
        """Return decentral heating structure (relative shares) for current
        scenario set in cfg WITHOUT district heating and solar.

        The shares of energy sources sum up to 1 per municipality.
        This is needed at creation of decentral sources which cover the
        residual load (load - solar_heat_feedin).
        """

        heating_structure_dec_scn_wo_solar = self.heating_structure_dec_scn.loc[
            self.heating_structure_dec_scn.index.get_level_values(1) != 'solar']

        source_scale_factor = 1 / heating_structure_dec_scn_wo_solar.groupby(
            ['ags_id']).agg('sum')
        return heating_structure_dec_scn_wo_solar * source_scale_factor

    @property
    def dist_heating_share_scn(self):
        """Return district heating share per municipality for year set in
        cfg"""
        return self._dist_heating_share.xs(
            self._cfg['scn_data']['general']['year'],
            level='year'
        )

    @property
    def tech_assumptions(self):
        """Return technical assumptions for all years"""
        return self._tech_assumptions

    @property
    def tech_assumptions_scn(self):
        """Return technical assumptions for year set in cfg"""
        return self._tech_assumptions.xs(
            self._cfg['scn_data']['general']['year'],
            level='year'
        )

    @property
    def batteries_large(self):
        """Return capacity, charging and discharging power of large-scale
        batteries per municipality"""
        return self._batteries_large

    @property
    def batteries_small(self):
        """Return capacity, charging and discharging power of PV batteries
        per municipality"""
        return self._batteries_small

    @property
    def pot_areas_pv_roof(self):
        return self._pot_areas_pv_roof

    @property
    def pot_areas_pv(self):
        return self._pot_areas_pv

    def pot_areas_pv_scn(self, scenario, pv_usable_area_agri_max):
        """Return PV potential areas (with and without restrictions on agricultural
        areas) for given scenario, aggregated by scenario's PV ground area type.

        Returns
        -------
        :obj:`dict` of :pandas:`pandas.DataFrame`
            Potential areas with and without agricultural restrictions.
            Return None for invalid or SQ scenario.
        """
        scn = scenario.lower()
        if scn not in ['hs', 'h']:
            return None

        # --- w/o agri restrictions ---
        pot_areas = {
            'without_agri_restrictions':self._pot_areas_pv[
                self._pot_areas_pv.index.get_level_values(
                    level=1).str.endswith(f'_{scn}')]['area_ha']
        }

        # --- calc agri restrictions ---
        areas = pot_areas['without_agri_restrictions'].copy()
        areas_agri = areas[areas.index.get_level_values(level=1).str.startswith(
            'agri_')]
        # limit area on fields and meadows so that it does not exceed 1 % of the
        # total area of fields and meadows in ABW
        if pv_usable_area_agri_max != 'nolimit':
            if areas_agri.sum() > pv_usable_area_agri_max:
                areas_agri *= pv_usable_area_agri_max / areas_agri.sum()
                areas.update(areas_agri)

        pot_areas['with_agri_restrictions'] = areas

        return pot_areas

    @property
    def pot_areas_wec(self):
        """Return WEC potential areas for of all scenarios

        Notes
        -----
        Scenario SQ contains VR/EG only (real values), other scenarios do not
        incorporate case-by-case decisions and need to be multiplied with
        parameter `wec_usable_area` to get the total usable area.
        """
        return self._pot_areas_wec

    def pot_areas_wec_scn(self, scenario):
        """Return WEC potential areas for given scenario, aggregated by mun.

        Returns
        -------
        :pandas:`pandas.DataFrame`
            Potential areas, return None for invalid WEC scenario.
        """
        scn = scenario.lower()
        if scn not in ['s500f0', 's500f1', 's1000f0', 's1000f1', 'sq']:
            return None
        return self._pot_areas_wec[
            self._pot_areas_wec.index.get_level_values(level=1) ==
                scn]['area_ha'].groupby('ags_id').agg('sum')

    @property
    def demography(self):
        """Return population and employees"""
        return self._demography

    @property
    def demography_scn(self):
        """Return population and employees for year set in cfg"""
        return self._demography.xs(
            self._cfg['scn_data']['general']['year'],
            level='year'
    )

    @property
    def demography_change(self):
        """Return relative change of population and employees for year set in
        cfg since 2017"""
        return self._demography.xs(
            self._cfg['scn_data']['general']['year'],
            level='year') / self._demography.xs(2017,
                                                level='year')

    @classmethod
    def import_data(cls, cfg=None):
        """Import data to Region object"""

        if cfg is None:
            msg = 'Please provide config'
            logger.error(msg)
            raise ValueError(msg)

        # create the region instance
        region = cls(**{**import_db_data(cfg), 'cfg': cfg})

        return region
