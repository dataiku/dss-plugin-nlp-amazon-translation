# -*- coding: utf-8 -*-
"""Module with classes to format results from the Google Cloud Translation API"""

import logging
import pandas as pd
from typing import AnyStr, Dict

from plugin_io_utils import (
    API_COLUMN_NAMES_DESCRIPTION_DICT,
    ErrorHandlingEnum,
    build_unique_column_names,
    generate_unique,
    safe_json_loads,
    move_api_columns_to_end,
)

LANGUAGE_CODE_LABELS = {
    'af': 'Afrikaans',
    'am': 'Amharic',
    'ar': 'Arabic',
    'az': 'Azerbaijani',
    'bg': 'Bulgarian',
    'bn': 'Bengali',
    'bs': 'Bosnian',
    'ca': 'Catalan',
    'cs': 'Czech',
    'cy': 'Welsh',
    'da': 'Danish',
    'de': 'German',
    'el': 'Greek',
    'en': 'English',
    'es': 'Spanish',
    'es-MX': 'Spanish (Mexico)',
    'et': 'Estonian',
    'fa': 'Persian',
    'fa-AF': 'Dari',
    'fi': 'Finnish',
    'fr': 'French',
    'fr-CA': 'French (Canada)',
    'gu': 'Gujarati',
    'ha': 'Hausa',
    'he': 'Hebrew',
    'hi': 'Hindi',
    'hr': 'Croatian',
    'ht': 'Haitian Creole',
    'hu': 'Hungarian',
    'hy': 'Armenian',
    'id': 'Indonesian',
    'is': 'Icelandic',
    'it': 'Italian',
    'ja': 'Japanese',
    'ka': 'Georgian',
    'kk': 'Kazakh',
    'kn': 'Kannada',
    'ko': 'Korean',
    'lt': 'Lithuanian',
    'lv': 'Latvian',
    'mk': 'Macedonian',
    'ml': 'Malayalam',
    'mn': 'Mongolian',
    'ms': 'Malay',
    'mt': 'Maltese',
    'nl': 'Dutch',
    'no': 'Norwegian',
    'pl': 'Polish',
    'ps': 'Pashto',
    'pt': 'Portuguese',
    'ro': 'Romanian',
    'ru': 'Russian',
    'si': 'Sinhala',
    'sk': 'Slovak',
    'sl': 'Slovenian',
    'so': 'Somali',
    'sq': 'Albanian',
    'sr': 'Serbian',
    'sv': 'Swedish',
    'sw': 'Swahili',
    'ta': 'Tamil',
    'te': 'Telugu',
    'th': 'Thai',
    'tl': 'Tagalog',
    'tr': 'Turkish',
    'uk': 'Ukrainian',
    'ur': 'Urdu',
    'uz': 'Uzbek',
    'vi': 'Vietnamese',
    'zh': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)'
}

# ==============================================================================
# CLASS AND FUNCTION DEFINITION
# ==============================================================================


class GenericAPIFormatter:
    """
    Geric Formatter class for API responses:
    - initialize with generic parameters
    - compute generic column descriptions
    - apply format_row to dataframe
    """

    def __init__(
        self,
        input_df: pd.DataFrame,
        column_prefix: AnyStr = "api",
        error_handling: ErrorHandlingEnum = ErrorHandlingEnum.LOG,
    ):
        self.input_df = input_df
        self.column_prefix = column_prefix
        self.error_handling = error_handling
        self.api_column_names = build_unique_column_names(input_df, column_prefix)
        self.column_description_dict = {
            v: API_COLUMN_NAMES_DESCRIPTION_DICT[k] for k, v in self.api_column_names._asdict().items()
        }

    def format_row(self, row: Dict) -> Dict:
        return row

    def format_df(self, df: pd.DataFrame) -> pd.DataFrame:
        logging.info("Formatting API results...")
        df = df.apply(func=self.format_row, axis=1)
        df = move_api_columns_to_end(df, self.api_column_names, self.error_handling)
        logging.info("Formatting API results: Done.")
        return df


class TranslationAPIFormatter(GenericAPIFormatter):
    """
    Formatter class for translation API responses:
    - make sure response is valid JSON
    """

    def __init__(
        self,
        input_df: pd.DataFrame,
        input_column: AnyStr,
        target_language: AnyStr,
        source_language: AnyStr = None,
        column_prefix: AnyStr = "translation_api",
        error_handling: ErrorHandlingEnum = ErrorHandlingEnum.LOG,
    ):
        super().__init__(input_df, column_prefix, error_handling)
        self.translated_text_column_name = generate_unique(
            f"{input_column}_{target_language.replace('-', '_')}", input_df.columns, prefix=None
        )
        self.detected_language_column_name = generate_unique(f"{input_column}_language", input_df.columns, prefix=None)
        self.source_language = source_language
        self.input_column = input_column
        self.input_df_columns = input_df.columns
        self.target_language = target_language
        self.target_language_label = LANGUAGE_CODE_LABELS[self.target_language]
        self._compute_column_description()

    def _compute_column_description(self):
        self.column_description_dict[
            self.translated_text_column_name
        ] = f"{self.target_language_label} translation of the '{self.input_column}' column by Google Cloud Translation"
        if not self.source_language:
            self.column_description_dict[
                self.detected_language_column_name
            ] = f"Detected language of the '{self.input_column}' column by Google Cloud Translation"

    def format_row(self, row: Dict) -> Dict:
        raw_response = row[self.api_column_names.response]
        response = safe_json_loads(raw_response, self.error_handling)
        if not self.source_language:
            row[self.detected_language_column_name] = LANGUAGE_CODE_LABELS.get(response.get("SourceLanguageCode", ""), "")
        row[self.translated_text_column_name] = response.get("TranslatedText", "")
        return row
