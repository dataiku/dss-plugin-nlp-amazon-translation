# -*- coding: utf-8 -*-
import json
from typing import AnyStr
from typing import Dict

import dataiku
from dataiku.customrecipe import get_recipe_config
from dataiku.customrecipe import get_input_names_for_role
from dataiku.customrecipe import get_output_names_for_role

from amazon_translation_api_client import API_EXCEPTIONS, get_client
from amazon_translation_api_formatting import TranslationAPIFormatter
from dkulib.dku_io_utils import set_column_descriptions
from dkulib.parallelizer import DataFrameParallelizer
from plugin_io_utils import ErrorHandlingEnum
from plugin_io_utils import validate_column_input

# ==============================================================================
# SETUP
# ==============================================================================

api_configuration_preset = get_recipe_config().get("api_configuration_preset")
if api_configuration_preset is None or api_configuration_preset == {}:
    raise ValueError("Please specify an API configuration preset")

# Recipe parameters
text_column = get_recipe_config().get("text_column")
target_language = get_recipe_config().get("target_language", "")
source_language = get_recipe_config().get("source_language", "")

# Params for parallelization
column_prefix = "translation_api"
parallel_workers = api_configuration_preset.get("parallel_workers")
error_handling = (
    ErrorHandlingEnum.FAIL if get_recipe_config().get("fail_on_error") else ErrorHandlingEnum.LOG
)

# Params for translation
client = get_client(
    aws_access_key_id=api_configuration_preset.get("aws_access_key_id"),
    aws_secret_access_key=api_configuration_preset.get("aws_secret_access_key"),
    aws_session_token=api_configuration_preset.get("aws_session_token"),
    aws_region_name=api_configuration_preset.get("aws_region_name"),
    max_attempts=api_configuration_preset.get("max_attempts"),
)

# ==============================================================================
# DEFINITIONS
# ==============================================================================

input_dataset = dataiku.Dataset(get_input_names_for_role("input_dataset")[0])
output_dataset = dataiku.Dataset(get_output_names_for_role("output_dataset")[0])
validate_column_input(text_column, [col["name"] for col in input_dataset.read_schema()])
input_df = input_dataset.get_dataframe()


def call_translation_api(
    row: Dict, text_column: AnyStr, target_language: AnyStr, source_language: AnyStr
) -> AnyStr:
    """
    Calls Amazon Translation API. Source & target language are mandatory.
    """
    text = row[text_column]
    if not isinstance(text, str) or str(text).strip() == "":
        return json.dumps({})
    else:
        response = client.translate_text(
            Text=text, TargetLanguageCode=target_language, SourceLanguageCode=source_language
        )
        return json.dumps(response)


formatter = TranslationAPIFormatter(
    input_df=input_df,
    input_column=text_column,
    target_language=target_language,
    source_language=source_language,
    column_prefix=column_prefix,
    error_handling=error_handling,
)

# ==============================================================================
# RUN
# ==============================================================================

df_parallelizer = DataFrameParallelizer(
    function=call_translation_api,
    error_handling=error_handling,
    exceptions_to_catch=API_EXCEPTIONS,
    parallel_workers=parallel_workers,
    batch_size=1,
    output_column_prefix=column_prefix,
)

df = df_parallelizer.run(
    input_df,
    text_column=text_column,
    target_language=target_language,
    source_language=source_language,
)

output_df = formatter.format_df(df)
output_dataset.write_with_schema(output_df)

set_column_descriptions(
    input_dataset=input_dataset,
    output_dataset=output_dataset,
    column_descriptions=formatter.column_description_dict,
)
