import json
import sys

from azurite.lib.logger import Logger as logger


class Subscription():

    def __init__(self, subproc):
        self.logger = logger.get_logger()
        self.logger.propagate = False
        self.subproc = subproc

    def check_azure_login(self):
        returncode, output = self.subproc.check_azure_login()
        if returncode != 0:
            self.logger.error(f"Unable to authenticate with Azure, run 'az login'.\n{output.strip()}")
            sys.exit(1)

    def check_if_current(self, subscription_name):
        returncode, output = self.subproc.get_current_subscription()
        if returncode != 0:
            self.logger.error(f"Unable to get the current Azure subscription, are you logged in? Run 'az login'.\n{output.strip()}")
            sys.exit(1)
        subscription = json.loads(output)
        if subscription_name == subscription["name"]:
            return True
        return False

    def set_subscription(self, subscription_name):
        if not self.check_if_current(subscription_name):
            self.logger.debug(f"Setting Subscription: {subscription_name}")
            subscriptions = json.loads(self.subproc.list_subscriptions())
            for subscription in subscriptions:
                if subscription['name'] == subscription_name:
                    subscription_id = subscription['id']
                    self.subproc.set_subscription(subscription_id)
                    return
            self.logger.error("SUBSCRIPTION NOT FOUND")
            sys.exit(1)
