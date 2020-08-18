# define and setup logger
from windnode_abw.tools.logger import setup_logger
logger = setup_logger()

# load configs
from windnode_abw.tools import config
config.load_config('config_data.cfg')
config.load_config('config_misc.cfg')

from windnode_abw.analysis import analysis


if __name__ == "__main__":
    # TODO: Nice-to-have: argparse

    # specify what to import (in path ~/.windnode_abw/)
    run_timestamp = '2020-08-14_203324'

    # select multiple scenarios manually or use 'ALL' to analyze all
    # scenarios found in directory
    #scenarios = ['future', 'sq']
    #scenarios = ['ALL']
    scenarios = ['NEP']

    regions_scns, results_scns = analysis(run_timestamp=run_timestamp,
                                          scenarios=scenarios,
                                          force_new_results=True)

    logger.info('===== All done! =====')

