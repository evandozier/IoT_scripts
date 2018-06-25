#!/usr/bin/env python3
'''
ercot_realtime_price.py is a script that will monitor the ercot
    realtime pricing table here: http://www.ercot.com/content/cdr/html/real_time_spp
    and make some decisions off of the value.
    This script monitors the 'LZ_SOUTH' column of that table since that's where my
    cost comes from. Change that as appropriate
    Change the private_webhook_key to whatever your key is to setup the IFTT events.
    I have my webhook triggering my ecobee to go into away mode when the price is high
    and resuming when the price falls back below the threshold.
'''

import logging
import pandas as pd
import time
import requests

_moduleLogger = logging.getLogger(__name__)


def _parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser()

    # Setup parser.
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument(
        "--test_spike", metavar="flag",
        required=False,
        help="Pass script this command to test a spike event and exit.",
    )
    inputGroup.add_argument(
        "--test_normal", metavar="flag",
        required=False,
        help="Pass script this command to test a return to normal event and exit.",
    )
    debugGroup = parser.add_argument_group("Debug")
    debugGroup.add_argument(
        "-v", "--verbose",
        action="count", dest="verbosity", default=0,
        help="Turn on verbose output. (Useful if you really care to see what \
                the tool is doing at all times.)"
    )
    debugGroup.add_argument(
        "-q", "--quiet",
        action="count", dest="quietness", default=0,
        help="Don't print anything to the module logger."
    )
    debugGroup.add_argument(
        "--test",
        action="store_true", default=False,
        help="Run doctests then quit."
    )

    args = parser.parse_args(argv)

    # We want to default to WARNING
    # Quiet should make us only show CRITICAL
    # Verbosity gives us granularity to control past that
    verbosity = 2 + (2 * args.quietness) - args.verbosity
    loggingLevel = {
        0: logging.DEBUG,
        1: logging.INFO,
        2: logging.WARNING,
        3: logging.ERROR,
        4: logging.CRITICAL,
    }.get(verbosity, None)
    if loggingLevel is None:
        parser.error("Unsupported verbosity: %r" % verbosity)

    if args.test:
        return args, loggingLevel

    return args, loggingLevel


class MakerTrigger(object):
  def __init__(self,key,trigger):
    self.key = key
    self.trigger = trigger
    self.maker = "https://maker.ifttt.com/trigger/" + self.trigger + "/with/key/" + self.key
  def alert(self,value1=0,value2=0,value3=0):
    self.value1 = value1
    self.value2 = value2
    self.value3 = value3
    self.json={"value1": self.value1, "value2": self.value2, "value3": self.value3}
    r = requests.post(self.maker, json=self.json)


def _main(argv):
    args, loggingLevel = _parse_args(argv)

    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(level=loggingLevel, format=logFormat)

    if args.test:
        import doctest
        print(doctest.testmod())
        sys.exit(0)

    # Initialize some variables
    previous_price = 0
    price_notify_threshold = 6 # cents per kWh
    notify_flag = False
    private_webhook_key = "<REPLACE_WITH_YOUR_KEY>"
    # Make the 2 IFTTT triggers
    ifttt_price_spike_alert = MakerTrigger(private_webhook_key, "energy_price_spike")
    ifttt_price_normal_alert = MakerTrigger(private_webhook_key, "energy_price_normal")

    # Test spike and exit
    if args.test_spike:
        _moduleLogger.info("Test Spike, notifying IFTTT, exiting")
        ifttt_price_spike_alert.alert("Test Spike")
        return 0

    # Test return to normal and exit
    if args.test_normal:
        _moduleLogger.info("Test Return to Normal, notifying IFTTT, exiting")
        ifttt_price_normal_alert.alert("Test Normal")
        return 0

    # Loop forever running the check
    while(True):
        powergrid_df, = pd.read_html("http://www.ercot.com/content/cdr/html/real_time_spp", header=0)
        # latest_price is in MWh
        latest_price = powergrid_df['LZ_SOUTH'].iloc[-1]
        cents_per_kWh = latest_price / 10

        _moduleLogger.info("Current price is: %f cents per kWh", cents_per_kWh)
        if cents_per_kWh > price_notify_threshold and previous_price != cents_per_kWh:
            # Only notify when the price is above the specified threshold
            _moduleLogger.info("Sending notification to IFTTT")
            ifttt_price_spike_alert.alert(cents_per_kWh)
            notify_flag = True
        elif notify_flag == True and previous_price != cents_per_kWh:
            # Let IFTTT know that the price is back below the threshold
            _moduleLogger.info("Price is back down now to %f cents per kWh. Notifying IFTTT...", cents_per_kWh)
            ifttt_price_normal_alert.alert(cents_per_kWh)
            notify_flag = False
        previous_price = cents_per_kWh
        _moduleLogger.info("Sleeping for 60 seconds")
        time.sleep(60)
    return 0


if __name__ == "__main__":
    import sys
    retCode = _main(sys.argv[1:])
    sys.exit(retCode)
