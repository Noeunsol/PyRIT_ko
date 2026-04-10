# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
# ---

# %% [markdown]
# # 2. 오디오 변환기 (Audio Converters)
#
# 오디오 변환기는 텍스트와 오디오 간의 변환, 그리고 오디오 간 수정을 지원합니다. 이 변환기들은 멀티모달이며, 한 번에 하나의 입력 타입과 하나의 출력 타입을 처리합니다.
#
# ## 개요
#
# 이 노트북은 세 가지 카테고리의 오디오 변환기를 다룹니다:
#
# - **[텍스트 → 오디오](#text-to-audio)**: 텍스트를 음성 오디오 파일로 변환
# - **[오디오 → 텍스트](#audio-to-text)**: 오디오 파일을 텍스트로 전사 (STT)
# - **[오디오 → 오디오](#audio-to-audio)**: 오디오 파일 수정 (예: 주파수 변경)

# %% [markdown]
# <a id="text-to-audio"></a>
# ## 텍스트 → 오디오 (Text to Audio)
#
# `AzureSpeechTextToAudioConverter`는 텍스트 입력을 오디오 출력으로 변환하여 음성 파일을 생성합니다.
# 한국어 프롬프트를 사용하여 한국어 음성을 생성합니다.

# %%
import os

from pyrit.prompt_converter import AzureSpeechTextToAudioConverter
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

# 한국어 프롬프트로 음성 생성
prompt = "대한민국의 역사에 대해 알려줘"

audio_converter = AzureSpeechTextToAudioConverter(
    output_format="wav",
    synthesis_language="ko-KR",
)
audio_convert_result = await audio_converter.convert_async(prompt=prompt)  # type: ignore

print(audio_convert_result)
assert os.path.exists(audio_convert_result.output_text)

# %% [markdown]
# <a id="audio-to-text"></a>
# ## 오디오 → 텍스트 (Audio to Text)
#
# `AzureSpeechAudioToTextConverter`는 오디오 파일을 텍스트로 전사합니다. 위에서 생성한 한국어 오디오 파일을 사용합니다.

# %%
import logging
import pathlib

from pyrit.common.path import DB_DATA_PATH
from pyrit.prompt_converter import AzureSpeechAudioToTextConverter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# 위에서 생성한 오디오 파일 사용
assert os.path.exists(audio_convert_result.output_text)
prompt = str(pathlib.Path(DB_DATA_PATH) / "dbdata" / "audio" / audio_convert_result.output_text)

speech_text_converter = AzureSpeechAudioToTextConverter(recognition_language="ko-KR")
transcript = await speech_text_converter.convert_async(prompt=prompt)  # type: ignore

print(transcript)

# %% [markdown]
# <a id="audio-to-audio"></a>
# ## 오디오 → 오디오 (Audio to Audio)
#
# `AudioFrequencyConverter`는 오디오 파일의 주파수를 높여 수정합니다. 오디오 모달리티 타겟을 높은 주파수로 탐색할 때 사용합니다.

# %%
from pyrit.prompt_converter import AudioFrequencyConverter

# 위에서 생성한 오디오 파일 사용
assert os.path.exists(audio_convert_result.output_text)
prompt = str(pathlib.Path(DB_DATA_PATH) / "dbdata" / "audio" / audio_convert_result.output_text)

audio_frequency_converter = AudioFrequencyConverter()
converted_audio_file = await audio_frequency_converter.convert_async(prompt=prompt)  # type: ignore

print(converted_audio_file)
