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
# # 5. 파일 변환기 (File Converters)
#
# 파일 변환기는 텍스트를 PDF 등의 파일 출력으로 변환합니다. 프롬프트를 배포 가능한 형식으로 패키징할 때 유용합니다.
#
# ## 개요
#
# 이 노트북은 다음 내용을 다룹니다:
#
# - **PDFConverter**: 템플릿 기반 또는 직접 생성 방식으로 텍스트를 PDF 문서로 변환

# %% [markdown]
# ## PDFConverter
#
# `PDFConverter`는 텍스트로부터 PDF 문서를 여러 가지 모드로 생성합니다:
#
# 1. **템플릿 기반 PDF 생성**: YAML 템플릿을 사용하여 동적 콘텐츠를 PDF로 렌더링
# 2. **직접 프롬프트 PDF 생성**: 템플릿 없이 일반 텍스트 문자열을 PDF로 변환
# 3. **기존 PDF 수정**: 기존 PDF 문서에 텍스트를 삽입

# %% [markdown]
# ### 템플릿 기반 PDF 생성
#
# 이 모드는 YAML 기반 템플릿의 플레이스홀더를 채운 후 렌더링된 콘텐츠를 PDF로 변환합니다.

# %%
import pathlib

from pyrit.common.path import CONVERTER_SEED_PROMPT_PATH
from pyrit.executor.attack import (
    AttackConverterConfig,
    ConsoleAttackResultPrinter,
    PromptSendingAttack,
)
from pyrit.models import SeedPrompt
from pyrit.prompt_converter import PDFConverter
from pyrit.prompt_normalizer import PromptConverterConfiguration
from pyrit.prompt_target import TextTarget
from pyrit.setup import IN_MEMORY, initialize_pyrit_async

await initialize_pyrit_async(memory_db_type=IN_MEMORY)  # type: ignore

prompt_data = {
    "hiring_manager_name": "홍길동",
    "current_role": "AI 엔지니어",
    "company": "사이버디펜스 주식회사",
    "red_teaming_reason": "무료 커피를 즐기며 창의적으로 보안 취약점을 식별하기 위해",
    "applicant_name": "김철수",
}

# PDF 생성을 위한 YAML 템플릿 로드
template_path = pathlib.Path(CONVERTER_SEED_PROMPT_PATH) / "pdf_converters" / "red_teaming_application_template.yaml"
if not template_path.exists():
    raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template_path}")

# YAML 파일에서 SeedPrompt 로드
prompt_template = SeedPrompt.from_yaml_file(template_path)

# 타겟 초기화
prompt_target = TextTarget()

# PDFConverter 초기화
pdf_converter = PromptConverterConfiguration.from_converters(
    converters=[
        PDFConverter(
            prompt_template=prompt_template,
            font_type="Arial",
            font_size=12,
            page_width=210,
            page_height=297,
        )
    ]
)

converter_config = AttackConverterConfig(
    request_converters=pdf_converter,
)

# 공격용 프롬프트 정의
prompt = str(prompt_data)

# 공격 초기화
attack = PromptSendingAttack(
    objective_target=prompt_target,
    attack_converter_config=converter_config,
)

result = await attack.execute_async(objective=prompt)  # type: ignore
await ConsoleAttackResultPrinter().print_conversation_async(result=result)  # type: ignore

# %% [markdown]
# ### 직접 프롬프트 PDF 생성 (템플릿 없음)
#
# 이 모드는 템플릿 없이 일반 텍스트 문자열을 직접 PDF로 변환합니다.

# %%
# 간단한 문자열 프롬프트 정의 (템플릿 없음)
prompt = "PDF 생성을 위한 간단한 테스트 문자열입니다. 템플릿을 사용하지 않습니다!"

# 템플릿 없이 PDFConverter 초기화
pdf_converter = PromptConverterConfiguration.from_converters(
    converters=[
        PDFConverter(
            prompt_template=None,  # 템플릿 미사용
            font_type="Arial",
            font_size=12,
            page_width=210,
            page_height=297,
        )
    ]
)

converter_config = AttackConverterConfig(
    request_converters=pdf_converter,
)

# 공격 초기화
attack = PromptSendingAttack(
    objective_target=prompt_target,
    attack_converter_config=converter_config,
)

result = await attack.execute_async(objective=prompt)  # type: ignore
await ConsoleAttackResultPrinter().print_conversation_async(result=result)  # type: ignore

# %% [markdown]
# ### 기존 PDF에 텍스트 삽입 (Injection Items)
#
# `PDFConverter`는 기존 PDF 문서의 지정된 위치에 텍스트를 삽입할 수도 있습니다.

# %%
import tempfile
from pathlib import Path

import requests

# 샘플 PDF 다운로드
url = "https://raw.githubusercontent.com/Azure/PyRIT/main/pyrit/datasets/prompt_converters/pdf_converters/fake_CV.pdf"

with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
    response = requests.get(url)
    tmp_file.write(response.content)

cv_pdf_path = Path(tmp_file.name)

# 삽입할 항목 정의
injection_items = [
    {
        "page": 0,
        "x": 50,
        "y": 700,
        "text": "삽입된 텍스트",
        "font_size": 12,
        "font": "Helvetica",
        "font_color": (255, 0, 0),
    },  # 빨간색 텍스트
    {
        "page": 1,
        "x": 100,
        "y": 600,
        "text": "기밀",
        "font_size": 10,
        "font": "Helvetica",
        "font_color": (0, 0, 255),
    },  # 파란색 텍스트
]

# 기존 PDF와 삽입 항목으로 PDFConverter 초기화
pdf_converter = PromptConverterConfiguration.from_converters(
    converters=[
        PDFConverter(
            prompt_template=None,
            font_type="Arial",
            font_size=12,
            page_width=210,
            page_height=297,
            existing_pdf=cv_pdf_path,  # 기존 PDF 제공
            injection_items=injection_items,  # 삽입 항목 제공
        )
    ]
)

converter_config = AttackConverterConfig(
    request_converters=pdf_converter,
)

# 공격 초기화
attack = PromptSendingAttack(
    objective_target=prompt_target,
    attack_converter_config=converter_config,
)

result = await attack.execute_async(objective="기존 PDF 수정")  # type: ignore
await ConsoleAttackResultPrinter().print_conversation_async(result=result)  # type: ignore
