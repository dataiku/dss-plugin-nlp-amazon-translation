# -*- coding: utf-8 -*-
"""Module with utility functions to call the Google translation API"""

import logging

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError
from botocore.exceptions import ClientError
from botocore.exceptions import NoRegionError

# ==============================================================================
# CONSTANT DEFINITION
# ==============================================================================


API_EXCEPTIONS = (ClientError, BotoCoreError)


# ==============================================================================
# CLASS AND FUNCTION DEFINITION
# ==============================================================================


def get_client(
    aws_access_key_id=None,
    aws_secret_access_key=None,
    aws_session_token=None,
    aws_region_name=None,
    max_attempts=20,
):
    """
    Gets a translation API client from AWS credentials.
    """
    # Try to ascertain credentials from environment
    if aws_access_key_id is None or aws_access_key_id == "":
        logging.info("Attempting to load credentials from environment.")
        try:
            client = boto3.client(
                service_name="translate", config=Config(retries={"max_attempts": max_attempts})
            )
        except NoRegionError as e:
            logging.info(
                "The region could not be loaded from the environment. "
                "If you have specified the region in the environment, "
                "DSS may not be able to access the environemt, "
                "such as in a User Isolation Framework setup. "
                "You may have to specify credentials in the plugin configuration."
            )
            logging.error(e)
            raise
    # Use configured credentials
    else:
        try:
            client = boto3.client(
                service_name="translate",
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                aws_session_token=aws_session_token,
                region_name=aws_region_name,
                config=Config(retries={"max_attempts": max_attempts}),
            )
        except ClientError as e:
            logging.error(e)
            raise

    logging.info("Credentials loaded.")
    return client
