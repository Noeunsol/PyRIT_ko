# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.17.3
# ---

# %% [markdown]
# # 4. 비디오 변환기 (Video Converters)
#
# 비디오 변환기는 비디오 파일과 관련된 변환을 지원하며, 특히 비디오에 이미지를 추가하는 기능을 제공합니다.
#
# ## 개요
#
# 이 노트북은 다음 내용을 다룹니다:
#
# - **[이미지 → 비디오](#image-to-video)**: 비디오 파일에 이미지 추가

# %% [markdown]
# <a id="image-to-video"></a>
# ## 이미지 → 비디오 (Image to Video)
#
# ### AddImageVideoConverter
#
# `AddImageVideoConverter`는 비디오 파일에 이미지 오버레이를 추가합니다.
# 이 변환기를 사용하려면 opencv를 설치해야 합니다: `pip install pyrit[opencv]`

# %%
import pathlib

from pyrit.prompt_converter import AddImageVideoConverter
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

input_video = str(pathlib.Path(".") / ".." / ".." / ".." / "assets" / "sample_video.mp4")
input_image = str(pathlib.Path(".") / ".." / ".." / ".." / "assets" / "pyrit_architecture.png")

video = AddImageVideoConverter(video_path=input_video)
converted_vid = await video.convert_async(prompt=input_image, input_type="image_path")  # type: ignore
converted_vid
