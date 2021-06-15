# -*- coding: utf-8 -*-
"""Module with utility functions to call the Google translation API"""

import json
import logging

import boto3
from botocore.exceptions import ClientError
from botocore.exceptions import BotoCoreError
from botocore.config import Config

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
            max_attempts=20
            ):
    """
    Get a translate API client from the AWS credentials.
    """
    # Try to ascertain credentials from environment
    if aws_access_key_id is None or aws_access_key_id == "":
        return boto3.client(service_name='translate')
    
    try:
        client = boto3.client(
            service_name='translate', 
            aws_access_key_id=aws_access_key_id, 
            aws_secret_access_key=aws_secret_access_key, 
            aws_session_token=aws_session_token, 
            region_name=aws_region_name, 
            config=Config(retries={'max_attempts': max_attempts})
        )
    except ClientError as e:
        logging.error(e)
        raise

    logging.info("Credentials loaded")
    return client
