import json

from azurite.lib.logger import Logger as logger


class Subscription():

    def __init__(self, subproc):
        self.logger = logger.get_logger()
        self.logger.propagate = False
        self.subproc = subproc

    def check_if_current(self, subscription_name):
        if subscription_name in self.subproc.get_current_subscription():
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
            exit()
