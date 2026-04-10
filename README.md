<p align="center"><img src="./doc/roakey.png" width="150"></p>

# PyRIT_ko

PyRIT_ko는 PyRIT 기반의 한국어 중심 LLM 레드팀/안전성 평가 실험 저장소입니다.  
이 문서는 현재 저장소 상태를 반영하며, 이후 실험/구조 변경에 따라 계속 업데이트됩니다.

---

## 1. 레포지토리 설명
- 원본 프레임워크: [Azure/PyRIT](https://github.com/Azure/PyRIT)
- 연관 프로젝트: Attack Method 유형 확대 - 기본 Attacker 구축
- 담당자: 노은솔
- 작성일: 2026-04-10
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

- 변환기 프롬프트
  - 경로: `prompts/prompt_converters/`
  - 예시: `tone_converter_ko.yaml`, `translation_converter_ko.yaml`
  - 용도: LLM 기반 변환기 동작 지시

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

### 3.2 튜토리얼 구성(`tests/`)

- `00_pyrit_overview.md`: 구조 개요
- `01_custom_tutorial.ipynb`: 공격/변환기/스코어러 조합 실행 + SQLite 결과 조회
- `02_attack_comparison.ipynb`: 공격 전략 비교
- `03_converter_comparison.ipynb`: 변환기 비교
- `04_scorer_comparison.ipynb`: 스코어러 비교
- `05_scenario_walkthrough.ipynb`: 시나리오 기반 종합 실행

---

## 4. 파이프라인 설명 및 실행

### 4.1 파이프라인

```text
Objective
  -> Attack
    -> Converter (선택)
      -> Target LLM
        -> Scorer
          -> Memory (InMemory / SQLite)
```

### 4.2 설치

```bash
git clone <repo-url>
cd PyRIT_ko
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 4.3 실행 방법

1) 튜토리얼 실행

```bash
jupyter lab
```

권장 시작점:
- `tests/01_custom_tutorial.ipynb`

2) 대화형 실행기

```bash
python main.py
```

3) CLI 엔트리포인트

```bash
pyrit_scan --help
pyrit_shell --help
```

### 4.4 SQLite 결과 저장/조회

`tests/01_custom_tutorial`에서 아래 설정 시:

```python
MEMORY_DB_TYPE = SQLITE
```

- `pyrit.db`에 결과가 저장되고
- 최신 실행 결과/테이블 row count를 표 형식으로 확인할 수 있습니다.

---

## 5. 이슈

- 이 저장소는 튜토리얼/문서/실험 구성이 계속 변경되는 작업 브랜치 성격이 있습니다.
- 튜토리얼 파일은 `ipynb` + `py`(jupytext 페어)로 함께 관리되므로, 수정 시 동기화가 필요합니다.
- 모델 실행 시 API 키가 없으면 타겟 호출이 실패합니다.
  - `OPENAI_API_KEY` 또는 `OPENAI_CHAT_KEY`
- `InMemory` 모드에서는 `.db` 파일이 남지 않습니다.
  - DB 분석이 필요하면 `SQLITE` 사용

---

## 6. Requirements

### 6.1 Python 버전

- `>=3.10, <3.14` (권장: 3.11)

### 6.2 주요 의존성(발췌)

- `openai`, `SQLAlchemy`, `transformers`, `datasets`, `fastapi`, `uvicorn`
- 개발/노트북: `pytest`, `jupyter`, `jupytext`, `ruff`, `mypy`

정확한 전체 목록은 아래를 기준으로 확인:
- `pyproject.toml`

### 6.3 테스트 명령 예시

```bash
.venv/bin/python -m pytest -q unit_tests/unit
```

---

## 7. 폴더 구조

```text
PyRIT_ko/
├── src/pyrit/                    # PyRIT 코어 라이브러리
│   ├── prompt_converter/         # 변환기 구현
│   ├── executor/                 # 공격/실행 로직
│   ├── scenario/                 # 시나리오 실행 로직
│   ├── memory/                   # SQLite/AzureSQL 메모리
│   ├── score/                    # 스코어러
│   ├── cli/                      # pyrit_scan, pyrit_shell
│   └── datasets/                 # 시드/평가/렉시콘 데이터셋
├── prompts/                      # 프롬프트 템플릿
├── tests/                        # 튜토리얼 데모(00~05)
├── doc/                          # 기본 문서
├── doc_ko/                       # 한국어 문서
├── main.py                       # 대화형 실행 엔트리포인트
├── pyproject.toml                # 패키지/의존성 정의
└── Makefile                      # 테스트/빌드 보조 명령
```
