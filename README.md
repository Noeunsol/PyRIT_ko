<p align="center"><img src="./doc/roakey.png" width="150"></p>

# PyRIT_ko

PyRIT_ko는 PyRIT 기반의 한국어 중심 LLM 레드팀/안전성 평가 실험 저장소입니다.  

---

## 1. 레포지토리 설명
- 원본 프레임워크: [Azure/PyRIT](https://github.com/Azure/PyRIT)
- 연관 프로젝트: Attack Method 유형 확대 - 기본 Attacker 구축
- 담당자: 노은솔, 정민재
- 작성일: 2026-04-16
- 목적: 한국어 환경에서 공격(Attack) - 변환(Converter) - 평가(Scorer) 흐름을 빠르게 실험
- 현재 특징:
  - `tests/`에 단계별 튜토리얼(00~05) 정리
  - `main.py`로 대화형 실행(시나리오 모드/커스텀 모드)
  - `01_custom_tutorial`에서 SQLite(`pyrit.db`) 결과 테이블 조회 지원
  - 한국어 문서(`doc_ko/`) 및 한국어 데이터셋(`*_ko`) 포함

---

## 2. 데이터 셋

이 저장소의 데이터 리소스는 크게 `datasets`와 `prompts`로 나뉩니다.

### 2.1 데이터셋 (`src/pyrit/datasets/`)

- Seed 데이터셋
  - 경로: `src/pyrit/datasets/seed_datasets/local/`
  - 예시: `adv_bench_ko.prompt`, `harmbench_ko.csv`
  - 용도: 공격 목표(입력 프롬프트) 소스

- Garak 계열 시드
  - 경로: `src/pyrit/datasets/seed_datasets/local/garak/`
  - 예시: `access_shell_commands_ko.prompt`, `web_html_js_ko.prompt`
  - 용도: 특정 공격군 실험용 시드

- 평가셋
  - 경로: `src/pyrit/datasets/scorer_evals/`
  - 예시: `refusal_ko.csv`, `harm/hate_speech_ko.csv`
  - 용도: 스코어러 품질/행동 검증

- Lexicon
  - 경로: `src/pyrit/datasets/lexicons/`
  - 예시: `languages_most_spoken_ko.yaml`, `fairness/gendered_professions_ko.yaml`
  - 용도: 카테고리/어휘 기반 보조 데이터

- Jailbreak 예시
  - 경로: `src/pyrit/datasets/jailbreak/`
  - 예시: `many_shot/many_shot_examples_ko.json`
  - 용도: 다중 예시 기반 공격 실험

### 2.2 프롬프트 리소스 (`prompts/`)

- 공격 실행 프롬프트
  - 경로: `prompts/executors/`
  - 예시: `red_teaming/*_ko.yaml`, `crescendo/*_ko.yaml`
  - 용도: 공격 전략별 시스템/유도 프롬프트

- 변환 전략 프롬프트
  - 경로: `prompts/prompt_converters/`
  - 예시: `tone_converter_ko.yaml`, `translation_converter_ko.yaml`
  - 용도: LLM 기반 변환 전략 동작 지시

- 점수 평가 프롬프트
  - 경로: `prompts/score/`
  - 예시: `refusal/*_ko.yaml`, `likert/*_ko.yaml`
  - 용도: 스코어러 평가 기준/질문

- 탈옥 템플릿
  - 경로: `prompts/jailbreak/templates/`
  - 예시: `*_ko.yaml` 다수
  - 용도: 템플릿 기반 우회 입력 생성

- 유해 카테고리 정의
  - 경로: `prompts/harm_definition/`
  - 예시: `harm_ko.yaml`, `cyber_ko.yaml`
  - 용도: 카테고리별 정책/정의 텍스트

참고:
- 한국어 리소스는 보통 `*_ko` 접미사 파일로 관리됩니다.

---

## 3. 구체적인 설명

### 3.1 핵심 컴포넌트

- Attack: 목표를 전달하는 전략 (예: `PromptSending`, `Crescendo`, `RedTeaming`)
- Converter: 프롬프트 변형/난독화 (예: `Base64`, `ROT13(ko)`, `Leetspeak(ko)`)
- Target: 테스트 대상 모델 (예: OpenAIChatTarget)
- Scorer: 성공/실패/유해성 판단 (예: Refusal, Scale, Likert)
- Scenario: 여러 원자적 공격을 묶어 캠페인 실행
- Memory: 실행 결과 저장 (`InMemory`, `SQLite`, `AzureSQL`)

### 3.2 지원 모델

`main.py`의 대화형 실행기에서 선택할 수 있는 타겟 모델:

| 키 | 모델 | 카테고리 | 필요 환경변수 |
|---|---|---|---|
| `gpt-4o-mini` | GPT-4o mini | OpenAI API | `OPENAI_CHAT_ENDPOINT`, `OPENAI_CHAT_KEY`, `OPENAI_CHAT_GPT4O_MINI_MODEL` |
| `gpt-4.1-mini` | GPT-4.1 mini | OpenAI API | `OPENAI_CHAT_ENDPOINT`, `OPENAI_CHAT_KEY`, `OPENAI_CHAT_GPT41_MINI_MODEL` |
| `exaone` | EXAONE 3.5 | HuggingFace (로컬) | 없음 (로컬 실행) |
| `no_llm` | — | 텍스트 출력만 | 없음 |

- OpenAI 모델 사용 시 `~/.pyrit/.env.local`에 API 키 설정 필요
- EXAONE은 HuggingFace를 통해 로컬에서 실행되며 별도 API 키 불필요 (`pip install -e ".[huggingface]"`로 torch 추가 설치 필요)
- Azure 환경이 필요한 경우 `pip install -e ".[azure]"`로 추가 의존성 설치

### 3.3 튜토리얼 구성(`tests/`)

- `00_pyrit_overview.md`: 구조 개요
- `01_custom_tutorial.ipynb`: 공격/변환 전략/스코어러 조합 실행 + SQLite 결과 조회
- `02_attack_comparison.ipynb`: 공격 전략 비교
- `03_converter_comparison.ipynb`: 변환 전략 비교
- `04_scorer_comparison.ipynb`: 스코어러 비교
- `05_scenario.ipynb`: 시나리오 기반 종합 실행

---

## 4. 파이프라인 설명 및 실행

### 4.1 파이프라인

```text
Seed
  -> Attack
    -> Converter (선택)
      -> Target LLM
        -> Scorer
          -> Memory (InMemory / SQLite)
```

### 4.2 환경 설정

```bash
# 1. conda 환경 생성 및 활성화
conda create -n pyrit_ko python=3.11 -y
conda activate pyrit_ko

# 2. 패키지 설치
pip install -e ".[dev]"

# 3. API 키 설정
mkdir -p ~/.pyrit
cp .env_example ~/.pyrit/.env
cp .env_local_example ~/.pyrit/.env.local
# ~/.pyrit/.env.local에서 OPENAI_CHAT_KEY에 실제 API 키 입력
```

### 4.3 실행 방법

1) 튜토리얼 실행

VSCode에서 `tests/01_custom_tutorial.ipynb` 열고 커널을 `pyrit_ko`로 선택하여 실행

2) 대화형 실행기

```bash
python main.py
```

3) CLI 실행 (시나리오 기반만 가능, custom attack은 cli로 불가)

```bash
# pyrit_scan --help
# pyrit_shell --help

OPENAI_CHAT_MODEL=gpt-4o-mini \
pyrit_scan garak.encoding \
  --database SQLite \
  --target-lang ko \
  --initializers openai_objective_target \
  --strategies rot13 \
  --max-dataset-size 1
```

4) Streamlit Demo 실행

```bash
streamlit run streamlit/app.py
```

### 4.4 SQLite 결과 저장/조회

```python
MEMORY_DB_TYPE = SQLITE
```

- `pyrit.db`에 결과가 저장되고
- 최신 실행 결과/테이블 row count를 표 형식으로 확인할 수 있습니다.

---

## 5. 이슈

- 튜토리얼 파일은 `ipynb` 기준으로 관리됩니다.
- 모델 실행 시 API 키가 없으면 타겟 호출이 실패합니다.
  - `~/.pyrit/.env.local`에 `OPENAI_CHAT_KEY` 설정 필요
- `InMemory` 모드에서는 `.db` 파일이 남지 않습니다.
  - DB 분석이 필요하면 `SQLITE` 사용

---

## 6. 의존성

> 모든 의존성은 `pyproject.toml`에 정의되어 있으며, `pip install -e ".[dev]"`로 한 번에 설치됩니다.

### 6.1 Python 버전

- `>=3.10, <3.14` (권장: 3.11)

### 6.2 기본 의존성 (`pip install -e .`)

```text
# AI/ML
openai>=2.2.0
transformers>=4.52.4
datasets>=3.6.0
numpy>=1.26.0
scipy>=1.15.3

# 웹/API
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
httpx[http2]>=0.27.2
websockets>=14.0

# 데이터/DB
SQLAlchemy>=2.0.41
pyodbc>=5.1.0
pandas>=2.0.0
pypdf>=6.6.2
reportlab>=4.4.4

# 텍스트 변환 (Converter용)
base2048>=0.1.3
confusables>=1.2.0
confusable-homoglyphs>=3.3.1
ecoji>=0.1.1
art>=6.5.0
segno>=1.6.6

# 유틸리티
pydantic>=2.11.5
jinja2>=3.1.6
python-dotenv>=1.0.1
pillow>=12.1.0
tqdm>=4.67.1
tenacity>=9.1.2
aiofiles>=24,<25
appdirs>=1.4.0
colorama>=0.4.6
termcolor>=2.4.0
tinytag>=2.1.1
treelib>=1.7.1
```

### 6.3 개발/노트북 의존성 (`pip install -e ".[dev]"`)

```text
# 노트북 실행
jupyter>=1.1.1
ipykernel>=6.29.5
jupytext>=1.17.1
jupyter-book==1.0.4

# 테스트
pytest>=8.3.5
pytest-asyncio>=1.0.0
pytest-cov>=6.1.1
pytest-timeout>=2.4.0
pytest-xdist>=3.6.1
mock-alchemy>=0.2.6
respx>=0.22.0

# 코드 품질
ruff>=0.14.4
mypy>=1.16.0
pre-commit>=4.2.0
```

### 6.4 HuggingFace 의존성 (`pip install -e ".[huggingface]"`)

```text
# EXAONE 등 로컬 모델 실행 시 설치
torch>=2.7.0
```

### 6.5 Azure 의존성 (`pip install -e ".[azure]"`)

```text
# Azure 환경 필요 시에만 설치
azure-core>=1.38.0
azure-identity>=1.19.0
azure-ai-contentsafety>=1.0.0
azure-storage-blob>=12.19.0
msal>=1.0.0
msal-extensions>=1.0.0
PyJWT>=2.0.0
```

---

## 7. 폴더 구조

```text
PyRIT_ko/
├── src/pyrit/                    # PyRIT 코어 라이브러리
│   ├── prompt_converter/         # 변환 전략 구현
│   ├── executor/                 # 공격/실행 로직
│   ├── scenario/                 # 시나리오 실행 로직
│   ├── memory/                   # SQLite/AzureSQL 메모리
│   ├── score/                    # 스코어러
│   ├── cli/                      # pyrit_scan, pyrit_shell
│   └── datasets/                 # 시드/평가/렉시콘 데이터셋
├── prompts/                      # 프롬프트 템플릿
├── tests/                        # 튜토리얼 데모(00~05)
├── tutorials/                    # 영어/한국어 비교 테스트
├── unit_tests/                   # 단위/통합 테스트
├── assets/                       # doc 튜토리얼용 이미지/미디어/스코어러 yaml
├── doc/                          # 기본 문서
├── doc_ko/                       # 한국어 문서
├── frontend/                     # 웹 UI (React + TypeScript)
├── main.py                       # 대화형 실행 엔트리포인트
└── pyproject.toml                # 패키지/의존성 정의
```
