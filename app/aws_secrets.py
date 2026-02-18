"""
AWS Secrets Manager integration for TTB Label Verifier.

Fetches UI credentials from AWS Secrets Manager with caching and fallback.
"""

import boto3
import logging
import os
from functools import lru_cache
from typing import Tuple

logger = logging.getLogger(__name__)


@lru_cache(maxsize=128)
def get_secret(secret_name: str) -> str:
    """
    Fetch secret from AWS Secrets Manager (cached).
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        
    Returns:
        Secret value as string
        
    Raises:
        Exception: If secret cannot be fetched and no fallback available
    """
    try:
        # Get region from environment or use default
        region = os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1'))
        client = boto3.client('secretsmanager', region_name=region)
        response = client.get_secret_value(SecretId=secret_name)
        logger.info(f"Successfully fetched secret: {secret_name}")
        return response['SecretString']
    except Exception as e:
        logger.error(f"Failed to fetch secret {secret_name}: {e}")
        
        # Fallback to environment variable (for local development)
        env_var_name = secret_name.replace('-', '_').upper()
        fallback_value = os.getenv(env_var_name)
        
        if fallback_value:
            logger.warning(f"Using environment variable {env_var_name} as fallback for {secret_name}")
            return fallback_value
        
        logger.error(f"No fallback available for secret {secret_name}")
        raise


def get_ui_credentials() -> Tuple[str, str]:
    """
    Get UI username and password from Secrets Manager.
    
    Returns:
        Tuple of (username, password)
        
    Raises:
        Exception: If credentials cannot be fetched
    """
    try:
        username = get_secret('TTB_DEFAULT_USER')
        password = get_secret('TTB_DEFAULT_PASS')
        return username, password
    except Exception as e:
        logger.error(f"Failed to get UI credentials: {e}")
        raise Exception("Unable to load UI credentials from Secrets Manager. Ensure secrets are created and IAM role has permissions.")
