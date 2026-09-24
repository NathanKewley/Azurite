import sys
import argparse
from argparse import RawTextHelpFormatter

from nitra.lib.logger import Logger as logger
from nitra.lib.orchestrator import Orchestrator

logger = logger.get_logger()
orchestrator = Orchestrator()


def _parse_args():
    parser = argparse.ArgumentParser(prog='nitra', formatter_class=RawTextHelpFormatter, 
    description="""nitra Usage:
        - deploy: deploy a single configuration
        - deploy-resource-group: deploy all config in a specific resource group
        - deploy-subscription: deploy all config in a specific subscription
        - deploy-account: deploy all config in the account / nitra project
        - destroy: destroy a single configuration
        - destroy-resource-group: destroy all config in a specific resource group
        - destroy-subscription: destroy all config in a specific subscription
        - destroy-account: destroy all config in the account / nitra project
        see GitHub for more details: https://github.com/NathanKewley/nitra """)
    parser.add_argument('operation', nargs=1, help=argparse.SUPPRESS, choices=[ "deploy", "deploy-resource-group", "deploy-subscription", "deploy-account", "destroy", "destroy-resource-group", "destroy-subscription", "destroy-account"], metavar="operation")
    parser.add_argument('suboperation', nargs='?', default=None, help=argparse.SUPPRESS)
    args = parser.parse_args()
    args.operation[0] = args.operation[0].replace("-", "_")
    return args

def nitra():
    args = _parse_args()
    logger.debug(args)
    try:
        # Fail before any hooks or deployments run if the Azure login is missing or expired
        orchestrator.subscription.check_azure_login()
        if args.suboperation is None:
            getattr(orchestrator, f"{args.operation[0]}")()
        else:
            getattr(orchestrator, f"{args.operation[0]}")(args.suboperation)
    except Exception as e:
        logger.error(e, exc_info=True)
        sys.exit(1)
