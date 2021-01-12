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
import requests
from bs4 import BeautifulSoup
import time
import smtplib

_moduleLogger = logging.getLogger(__name__)


def _parse_args(argv):
    import argparse
    parser = argparse.ArgumentParser()

    # Setup parser.
    inputGroup = parser.add_argument_group("Input")
    inputGroup.add_argument(
        "--url",
        required=False, default="https://vaccine.heb.com/",
        help="URL to watch.",
    )
    inputGroup.add_argument(
        "--check_period",
        required=False, default=30,
        help="Period of time to wait between checks (seconds).",
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


def _main(argv):
    args, loggingLevel = _parse_args(argv)

    logFormat = '(%(relativeCreated)5d) %(levelname)-5s %(name)s.%(funcName)s: %(message)s'
    logging.basicConfig(level=loggingLevel, format=logFormat)

    if args.test:
        import doctest
        print(doctest.testmod())
        sys.exit(0)

    # Initialize variables and prepare to loop
    check_period = args.check_period

    url = args.url
    _moduleLogger.info("Checking URL: %s", url)    

    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    response = requests.get(url, headers=headers)
    original_soup = BeautifulSoup(response.text, "lxml")
    _moduleLogger.info(original_soup)

    # Loop on website and look for changes
    while True:
        # set the headers like we are a browser,
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        # download the homepage
        response = requests.get(url, headers=headers)
        # parse the downloaded homepage and grab all text, then,
        soup = BeautifulSoup(response.text, "lxml")
    
        # Compare initial snapshot of page to current snapshot. Continue if identical
        if soup == original_soup:
            _moduleLogger.info("Website content identical")
            time.sleep(check_period)
            continue
        
        # If site is different than initial, e-mail me
        else:
            # create an email message with just a subject line,
            msg = 'Subject: This is Chris\'s script talking, CHECK GOOGLE!'
            fromaddr = 'YOUR_EMAIL_ADDRESS'
            toaddrs  = ['AN_EMAIL_ADDRESS','A_SECOND_EMAIL_ADDRESS', 'A_THIRD_EMAIL_ADDRESS']
        
            # setup the email server,
            # server = smtplib.SMTP('smtp.gmail.com', 587)
            # server.starttls()
            # add my account login name and password,
            # server.login("YOUR_EMAIL_ADDRESS", "YOUR_PASSWORD")
        
            # Print the email's contents
            _moduleLogger.info('From: ' + fromaddr)
            _moduleLogger.info('To: ' + str(toaddrs))
            _moduleLogger.info('Message: ' + msg)
        
            # send the email
            # server.sendmail(fromaddr, toaddrs, msg)
            # disconnect from the server
            # server.quit()
            break
        
        return 0

if __name__ == "__main__":
    import sys
    retCode = _main(sys.argv[1:])
    sys.exit(retCode)
