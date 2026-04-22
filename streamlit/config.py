# config.py — PyRIT_ko Streamlit 데모용 카탈로그 상수 및 라벨
# main.py에서 추출한 순수 데이터만 포함

from __future__ import annotations

# ---------------------------------------------------------------------------
# Target models
# ---------------------------------------------------------------------------
# (key, model_env_var, label_ko, label_en, category)
TARGET_MODELS = [
    ("gpt-4o-mini", "OPENAI_CHAT_GPT4O_MINI_MODEL", "GPT-4o mini (OpenAI)", "GPT-4o mini (OpenAI)", "llm"),
    ("gpt-4.1-mini", "OPENAI_CHAT_GPT41_MINI_MODEL", "GPT-4.1 mini (OpenAI)", "GPT-4.1 mini (OpenAI)", "llm"),
    ("exaone", "", "EXAONE 3.5 (HuggingFace, 로컬)", "EXAONE 3.5 (HuggingFace, local)", "huggingface"),
    ("no_llm", "", "LLM 호출 없이 변환 결과만 출력", "Output converted text only (no LLM call)", "no_llm"),
]

HUGGINGFACE_MODELS = {
    "exaone": "LGAI-EXAONE/EXAONE-3.5-2.4B-Instruct",
}

# ---------------------------------------------------------------------------
# Target presets (scenario mode)
# ---------------------------------------------------------------------------
TARGET_PRESETS = {
    "openai_basic": {
        "initializers": ["openai_objective_target", "simple", "load_default_datasets"],
        "label_ko": "OpenAI 기본",
        "label_en": "OpenAI Basic",
        "desc_ko": "OpenAI + 기본 스코어러 + 데이터셋 (추천)",
        "desc_en": "OpenAI + default scorers + datasets (recommended)",
    },
    "openai_no_scorer": {
        "initializers": ["openai_objective_target", "load_default_datasets"],
        "label_ko": "OpenAI 최소",
        "label_en": "OpenAI Minimal",
        "desc_ko": "OpenAI 타겟 + 데이터셋만 (스코어러 없음)",
        "desc_en": "OpenAI target + datasets only (no scorer)",
    },
}

# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------
# (key, desc_ko, desc_en)
SCENARIOS = [
    ("foundry.red_team_agent", "AI가 자동으로 여러 공격 전략을 시도", "Auto-tries multiple attack strategies"),
    ("airt.content_harms", "폭력·혐오·성적 등 7종 유해 콘텐츠 유도", "Probes 7 harm categories"),
    ("airt.cyber", "해킹·멀웨어 등 사이버 범죄 정보 유도", "Elicits hacking/malware/cyber crime info"),
    ("airt.jailbreak", "안전장치를 우회하는 탈옥 프롬프트 테스트", "Tests jailbreak prompts to bypass safety"),
    ("airt.scam", "피싱·보이스피싱 등 사기 시나리오 유도", "Elicits phishing/scam scenarios"),
    ("airt.leakage_scenario", "시스템 프롬프트·내부 정보 유출 시도", "Attempts to leak system prompt/internal info"),
    ("airt.psychosocial_scenario", "자해·자살 등 위기 상황 응답 적절성 평가", "Evaluates crisis response"),
    ("garak.encoding", "Base64·모스부호 등으로 필터 우회 시도", "Bypasses filters via encoding"),
]

# Scenario preflight blueprint (main-screen summary before execution)
# key -> {attacks, scorer, converter} as (ko, en)
SCENARIO_BLUEPRINTS: dict[str, dict[str, tuple[str, str]]] = {
    "foundry.red_team_agent": {
        "attacks": (
            "전략 조합에 따라 PromptSending(기본), Crescendo/RedTeaming/TreeOfAttacks(PAIR·TAP) 멀티턴 실행",
            "Runs PromptSending by default, or Crescendo/RedTeaming/TreeOfAttacks (PAIR/TAP) for multi-turn strategies",
        ),
        "scorer": (
            "기본 objective scorer: AzureContentFilter(0.5+) AND 비거부(SelfAskRefusal Inverter) 조합",
            "Default objective scorer: AzureContentFilter (0.5+) AND non-refusal (SelfAskRefusal Inverter)",
        ),
        "converter": (
            "전략에 따라 Base64/ROT13/Flip/Jailbreak 등 다수 변환 전략을 단일 공격과 조합",
            "Composes many converters (Base64/ROT13/Flip/Jailbreak, etc.) with the selected attack strategy",
        ),
    },
    "airt.content_harms": {
        "attacks": (
            "각 harm 카테고리별 PromptSending + RolePlay(movie_script) + ManyShotJailbreak (+ user_messages가 있으면 MultiPromptSending)",
            "Per harm category: PromptSending + RolePlay (movie_script) + ManyShotJailbreak (+ MultiPromptSending when user_messages exist)",
        ),
        "scorer": (
            "기본 objective scorer: 비거부(SelfAskRefusal Inverter)",
            "Default objective scorer: non-refusal (SelfAskRefusal Inverter)",
        ),
        "converter": (
            "별도 변환 전략 체인 없이 공격 기법 자체를 사용",
            "Uses built-in attack behaviors rather than a separate converter chain",
        ),
    },
    "airt.cyber": {
        "attacks": (
            "single_turn=PromptSending, multi_turn=RedTeaming",
            "single_turn=PromptSending, multi_turn=RedTeaming",
        ),
        "scorer": (
            "기본 objective scorer: malware True/False + 비거부(backstop) Composite(AND)",
            "Default objective scorer: malware True/False + non-refusal backstop (AND composite)",
        ),
        "converter": (
            "기본 제공 변환 전략 없음",
            "No dedicated converter chain by default",
        ),
    },
    "airt.jailbreak": {
        "attacks": (
            "PromptSending + TextJailbreak 템플릿(기본 n=3, 랜덤)",
            "PromptSending + TextJailbreak templates (default n=3, sampled)",
        ),
        "scorer": (
            "기본 objective scorer: 비거부(SelfAskRefusal Inverter)",
            "Default objective scorer: non-refusal (SelfAskRefusal Inverter)",
        ),
        "converter": (
            "TextJailbreakConverter 사용 (템플릿별 atomic attack 생성)",
            "Uses TextJailbreakConverter (one atomic attack per template)",
        ),
    },
    "airt.scam": {
        "attacks": (
            "context_compliance / role_play(persuasion_script_written) / persuasive_rta(RedTeaming) 조합",
            "Combines context_compliance, role_play (persuasion_script_written), and persuasive_rta (RedTeaming)",
        ),
        "scorer": (
            "기본 objective scorer: scams True/False + 비거부(backstop) Composite(AND)",
            "Default objective scorer: scams True/False + non-refusal backstop (AND composite)",
        ),
        "converter": (
            "독립 변환 전략 체인 없음 (공격별 내부 전략 사용)",
            "No separate converter pipeline (uses attack-internal strategies)",
        ),
    },
    "airt.leakage_scenario": {
        "attacks": (
            "first_letter(Prompt+FirstLetterConverter), image(Prompt+AddImageTextConverter), role_play, crescendo",
            "first_letter (Prompt+FirstLetterConverter), image (Prompt+AddImageTextConverter), role_play, crescendo",
        ),
        "scorer": (
            "기본 objective scorer: leakage True/False + 비거부(backstop) Composite(AND)",
            "Default objective scorer: leakage True/False + non-refusal backstop (AND composite)",
        ),
        "converter": (
            "전략별 FirstLetterConverter / AddImageTextConverter 사용",
            "Uses strategy-specific FirstLetterConverter / AddImageTextConverter",
        ),
    },
    "airt.psychosocial_scenario": {
        "attacks": (
            "single_turn=PromptSending(Tone soften)+RolePlay(movie_script), multi_turn=Crescendo",
            "single_turn=PromptSending (Tone soften)+RolePlay (movie_script), multi_turn=Crescendo",
        ),
        "scorer": (
            "기본 objective scorer: 대화 기반 FloatScale(리커트 루브릭) + threshold 1.0",
            "Default objective scorer: conversation-based FloatScale (Likert rubric) + threshold 1.0",
        ),
        "converter": (
            "ToneConverter(soften) 사용",
            "Uses ToneConverter (soften)",
        ),
    },
    "garak.encoding": {
        "attacks": (
            "인코딩별 PromptSending 실행 + AskToDecode 템플릿 변형을 추가로 생성",
            "Runs PromptSending per encoding and adds AskToDecode template variants",
        ),
        "scorer": (
            "기본 objective scorer: DecodingScorer(categories=['encoding_scenario'])",
            "Default objective scorer: DecodingScorer(categories=['encoding_scenario'])",
        ),
        "converter": (
            "Base64/Base2048/ROT13/Morse/AsciiSmuggler 등 인코딩 변환 전략 + AskToDecodeConverter",
            "Encoding converters (Base64/Base2048/ROT13/Morse/AsciiSmuggler, etc.) + AskToDecodeConverter",
        ),
    },
}

# ---------------------------------------------------------------------------
# Attacks
# ---------------------------------------------------------------------------
# (key, desc_ko, desc_en, turn_type)
ATTACKS = [
    ("prompt_sending", "목표 프롬프트를 그대로 전송", "Sends Seed prompt as-is", "single-turn"),
    ("flip", "텍스트를 뒤집어서 필터 우회", "Reverses text to bypass filters", "single-turn"),
    ("context_compliance", "허용되는 맥락을 만들어 유도", "Creates permissive context", "single-turn"),
    ("many_shot", "대량 예시로 모델 행동 유도", "Floods examples to steer model", "single-turn"),
    ("role_play", "캐릭터 역할극으로 안전장치 우회", "Uses character role-play to bypass safety", "single-turn"),
    ("skeleton_key", "마스터키 프롬프트로 제한 해제 시도", "Master-key prompt to unlock restrictions", "single-turn"),
    ("crescendo", "무해한 대화에서 점점 유해하게 유도", "Gradually escalates from harmless to harmful", "multi-turn"),
    ("red_teaming", "AI가 반복 대화하며 공격 전략 조정", "AI iterates conversations, adjusting strategy", "multi-turn"),
    ("tree_of_attacks", "여러 갈래로 분기하며 최적 공격 탐색", "Branches multiple paths to find best attack", "multi-turn"),
    ("multi_prompt_sending", "여러 메시지를 순서대로 전송", "Sends multiple messages in sequence", "multi-turn"),
    ("chunked_request", "목표를 조각내어 나눠 보내기", "Splits Seed into small chunks", "multi-turn"),
]

# Attacks with built-in conversion logic
HAS_BUILTIN_CONVERTER = {"flip", "context_compliance", "many_shot", "role_play", "skeleton_key"}

# Attacks requiring adversarial chat target
NEEDS_ADVERSARIAL = {"crescendo", "red_teaming", "tree_of_attacks", "context_compliance"}

# Attack → recommended scorer keys (first = objective scorer, rest = auxiliary)
RECOMMENDED_SCORERS: dict[str, list[str]] = {
    "prompt_sending":       ["refusal", "scale"],
    "flip":                 ["refusal", "scale"],
    "context_compliance":   ["refusal", "scale"],
    "many_shot":            ["refusal", "scale"],
    "role_play":            ["refusal", "scale"],
    "skeleton_key":         ["refusal", "scale"],
    "crescendo":            ["scale", "refusal"],
    "red_teaming":          ["refusal", "scale"],
    "tree_of_attacks":      ["scale"],
    "multi_prompt_sending": ["refusal", "scale"],
    "chunked_request":      ["refusal", "scale"],
}

# Back-compat: single-value view of the recommendation (first entry).
RECOMMENDED_SCORER: dict[str, str] = {k: v[0] for k, v in RECOMMENDED_SCORERS.items() if v}

# Attack-specific notes
ATTACK_NOTES: dict[str, list[tuple[str, str]]] = {
    "prompt_sending": [
        ("가장 기본적인 공격 — 변환 전략과 자유롭게 조합 가능", "Simplest attack — freely combinable with converters"),
    ],
    "flip": [
        ("⚠️ 자체 변환 로직 포함 — 변환 전략 없이 실행 권장", "⚠️ Built-in conversion — no extra converters recommended"),
    ],
    "context_compliance": [
        ("⚠️ 자체 변환 로직 포함", "⚠️ Built-in conversion"),
        ("AI가 무해한 맥락을 자동 생성 (추가 LLM 호출)", "AI auto-generates benign context (extra LLM calls)"),
    ],
    "many_shot": [
        ("⚠️ 자체 변환 로직 포함", "⚠️ Built-in conversion"),
        ("예시 수가 많을수록 토큰 소비 급증", "More examples = higher token usage"),
    ],
    "role_play": [
        ("⚠️ 자체 변환 로직 포함", "⚠️ Built-in conversion"),
        ("AI가 역할극 시나리오를 자동 생성", "AI auto-generates role-play scenario"),
    ],
    "skeleton_key": [
        ("⚠️ 자체 변환 로직 포함", "⚠️ Built-in conversion"),
        ("2단계 공격: 마스터키 전송 → 목표 전송", "Two-phase: master-key then Seed"),
    ],
    "crescendo": [
        ("스코어러 미지정 시 자동 생성 (임계값 0.8)", "Auto-creates scorer if not provided"),
        ("거부 시 자동 백트래킹", "Auto-backtracks on refusal"),
    ],
    "red_teaming": [
        ("⚠️ 스코어러 필수", "⚠️ Scorer required"),
        ("턴당 LLM 호출 2~3회", "2-3 LLM calls per turn"),
    ],
    "tree_of_attacks": [
        ("⚠️ scale 스코어러만 사용 가능", "⚠️ Only scale scorer supported"),
        ("가장 비용이 높은 공격", "Most expensive attack"),
    ],
    "multi_prompt_sending": [
        ("마지막 응답만 스코어링", "Only final response is scored"),
    ],
    "chunked_request": [
        ("목표를 N글자씩 쪼개 요청", "Requests N chars at a time"),
    ],
}

# ---------------------------------------------------------------------------
# Converters
# ---------------------------------------------------------------------------
# (class_name, desc_ko, desc_en, category)
CONVERTERS = [
    # Text→Text: Encoding
    ("Base64Converter", "Base64로 변환", "Encode as Base64", "tt_encoding"),
    ("ROT13Converter", "한글 자모를 회전 치환", "Shift letters by 13", "tt_encoding"),
    ("BinaryConverter", "0과 1로 변환", "Convert to binary", "tt_encoding"),
    ("MorseConverter", "한글 모스 부호로 변환", "Convert to Morse code", "tt_encoding"),
    ("CaesarConverter", "한글 자모를 N칸 밀어 치환", "Shift letters by N", "tt_encoding"),
    ("AtbashConverter", "한글 자모 순서 뒤집어 치환", "Reverse alphabet substitution", "tt_encoding"),
    ("Base2048Converter", "Base2048로 변환", "Encode as Base2048", "tt_encoding"),
    ("AskToDecodeConverter", "인코딩 후 복호화 요청 포함", "Encodes then asks to decode", "tt_encoding"),
    ("BinAsciiConverter", "Hex/UU 등 바이너리-텍스트 변환", "Binary-to-text (Hex/UU/QP)", "tt_encoding"),
    ("EcojiConverter", "Ecoji 이모지로 인코딩", "Encode as Ecoji emoji", "tt_encoding"),
    # Text→Text: Korean-specific
    ("BrailleConverter", "한글 점자로 변환", "Convert to Braille", "tt_korean"),
    ("NatoConverter", "한글 음성부호/NATO 알파벳", "NATO phonetic alphabet", "tt_korean"),
    ("LeetspeakConverter", "한글 자모를 닮은꼴 기호로 치환", "Leetspeak", "tt_korean"),
    ("ColloquialWordswapConverter", "한국어 표준어를 구어체/속어로", "Swap formal words with slang", "tt_korean"),
    # Text→Text: Transform
    ("FlipConverter", "텍스트 순서를 뒤집기", "Reverse text order", "tt_transform"),
    ("UnicodeConfusableConverter", "비슷하게 생긴 유니코드로 치환", "Look-alike Unicode chars", "tt_transform"),
    ("CharSwapConverter", "인접 문자 위치를 바꾸기", "Swap adjacent characters", "tt_transform"),
    ("StringJoinConverter", "문자 사이에 구분자 삽입", "Insert delimiters", "tt_transform"),
    ("SuffixAppendConverter", "프롬프트 끝에 텍스트 추가", "Append text to prompt", "tt_transform"),
    ("CharacterSpaceConverter", "모든 문자 사이에 공백 삽입", "Insert spaces between chars", "tt_transform"),
    ("ZalgoConverter", "글자에 장식 기호를 덧붙여 왜곡", "Distort text with combining marks", "tt_transform"),
    ("ZeroWidthConverter", "보이지 않는 문자 삽입", "Insert zero-width characters", "tt_transform"),
    ("AnsiAttackConverter", "ANSI 제어 코드 시나리오 생성", "ANSI escape codes", "tt_transform"),
    ("AsciiSmugglerConverter", "유니코드 태그로 텍스트 은닉", "Smuggle via ASCII tags", "tt_transform"),
    ("SneakyBitsSmugglerConverter", "비트 조작으로 텍스트 은닉", "Smuggle via bit manipulation", "tt_transform"),
    ("VariationSelectorSmugglerConverter", "유니코드 변형 선택자로 은닉", "Smuggle via variation selectors", "tt_transform"),
    ("UnicodeSubstitutionConverter", "유니코드 이스케이프 시퀀스로 변환", "Unicode escape sequences", "tt_transform"),
    ("UnicodeReplacementConverter", "유니코드 이스케이프로 치환", "Unicode escapes", "tt_transform"),
    ("UrlConverter", "URL 퍼센트 인코딩으로 변환", "URL percent-encoding", "tt_transform"),
    ("InsertPunctuationConverter", "단어 사이에 구두점 삽입", "Insert punctuation", "tt_transform"),
    ("JsonStringConverter", "JSON 문자열 형태로 감싸기", "Wrap as JSON string", "tt_transform"),
    ("MathObfuscationConverter", "각 문자를 대수 항등식으로 난독화", "Math expression obfuscation", "tt_transform"),
    ("NegationTrapConverter", "이중 부정으로 의미 혼란 유도", "Double negation confusion", "tt_transform"),
    ("RepeatTokenConverter", "토큰 반복 삽입으로 난독화", "Repeat tokens", "tt_transform"),
    ("SearchReplaceConverter", "정규식 패턴 검색/치환", "Regex search & replace", "tt_transform"),
    ("FirstLetterConverter", "각 단어의 첫 글자만 추출", "First letter extraction", "tt_transform"),
    # Text→Text: LLM-based
    ("TranslationConverter", "다른 언어로 번역", "Translate", "tt_llm"),
    ("ToneConverter", "말투·어조를 변경", "Change tone/style", "tt_llm"),
    ("VariationConverter", "같은 의미의 다른 표현 생성", "Paraphrase variation", "tt_llm"),
    ("PersuasionConverter", "설득 기법을 적용해 재구성", "Persuasion technique", "tt_llm"),
    ("TenseConverter", "과거·현재·미래 시제로 변경", "Change tense", "tt_llm"),
    ("NoiseConverter", "텍스트에 오탈자/노이즈 추가", "Add typos/noise", "tt_llm"),
    ("MathPromptConverter", "수학 문제 형식으로 변환", "Math problem format", "tt_llm"),
    ("ToxicSentenceGeneratorConverter", "유해 문장 시작부 생성", "Toxic sentence starters", "tt_llm"),
    ("MaliciousQuestionGeneratorConverter", "악의적 질문으로 재구성", "Adversarial question", "tt_llm"),
    ("RandomTranslationConverter", "단어별 무작위 언어 번역", "Random word translation", "tt_llm"),
    ("DenylistConverter", "금지어를 동의어로 LLM 치환", "Replace banned words", "tt_llm"),
    # Text→Text: Jailbreak
    ("TextJailbreakConverter", "탈옥 프롬프트 템플릿 적용", "Jailbreak template", "tt_jailbreak"),
    ("CodeChameleonConverter", "코드 형식으로 위장하여 전달", "Disguise as code", "tt_jailbreak"),
    ("TemplateSegmentConverter", "템플릿 구간 분할", "Template segment split", "tt_jailbreak"),
    # Text→Text: English-only
    ("AsciiArtConverter", "텍스트를 아스키 아트로 변환", "ASCII art", "tt_en_only"),
    ("DiacriticConverter", "글자 위에 발음 기호 추가", "Diacritical marks", "tt_en_only"),
    ("RandomCapitalLettersConverter", "무작위로 대소문자 섞기", "Random case", "tt_en_only"),
    ("SuperscriptConverter", "위첨자 유니코드로 변환", "Superscript Unicode", "tt_en_only"),
    ("EmojiConverter", "알파벳을 이모지로 치환", "Replace A-Z with emoji", "tt_en_only"),
    # Text→Image / Text→File
    ("QRCodeConverter", "텍스트를 QR코드 이미지로 변환", "QR code image", "text_to_image"),
    ("AddImageTextConverter", "지정한 이미지 위에 프롬프트 텍스트 얹기", "Overlay prompt text on a given image", "text_to_image"),
    ("PDFConverter", "텍스트를 PDF로 변환", "Convert to PDF", "text_to_file"),
    # Image→Image (이미지 변환 전략 뒤에 체이닝해서 사용)
    ("ImageCompressionConverter", "이미지 압축·포맷 변환 (이미지 변환 전략 뒤에 체이닝)", "Compress/reformat image (chain after image converter)", "image_to_image"),
]

CONVERTER_CAT_LABELS: dict[str, tuple[str, str]] = {
    "tt_encoding": ("인코딩", "Encoding"),
    "tt_korean": ("한국어 특화", "Korean-specific"),
    "tt_transform": ("변환", "Transform"),
    "tt_llm": ("LLM 기반", "LLM-based"),
    "tt_jailbreak": ("탈옥", "Jailbreak"),
    "tt_en_only": ("영어 전용", "English-only"),
    "text_to_image": ("텍스트→이미지", "Text→Image"),
    "text_to_file": ("텍스트→파일", "Text→File"),
    "image_to_image": ("이미지→이미지", "Image→Image"),
}

# Converters that accept locale param
LOCALE_CONVERTERS = {
    "MorseConverter", "CaesarConverter", "AtbashConverter", "BrailleConverter",
    "NatoConverter", "LeetspeakConverter", "ROT13Converter", "ColloquialWordswapConverter",
    "CodeChameleonConverter", "NegationTrapConverter", "AskToDecodeConverter", "JsonStringConverter",
    "TemplateSegmentConverter",
}

# LLM-based converters (need converter_target)
LLM_CONVERTERS = {
    "TranslationConverter", "ToneConverter", "VariationConverter",
    "PersuasionConverter", "TenseConverter",
    "NoiseConverter", "MathPromptConverter", "ToxicSentenceGeneratorConverter",
    "MaliciousQuestionGeneratorConverter", "RandomTranslationConverter", "DenylistConverter",
}

# Converters with extra text input params
# class_name -> [(param_name, label_ko, label_en, default)]
CONVERTER_EXTRA_PARAMS: dict[str, list[tuple[str, str, str, str | None]]] = {
    "CaesarConverter": [("caesar_offset", "시저 암호 이동값", "Caesar offset", "3")],
    "CharSwapConverter": [
        ("max_iterations", "문자 교환 반복 횟수", "Swap iterations", "1"),
        ("word_proportion", "변환 단어 비율 (0~1)", "Word proportion (0-1)", "1.0"),
    ],
    "SuffixAppendConverter": [("suffix", "추가할 접미사", "Suffix to append", "!!!")],
    "RepeatTokenConverter": [
        ("token_to_repeat", "반복할 토큰", "Token to repeat", "!!"),
        ("times_to_repeat", "반복 횟수", "Times to repeat", "10"),
    ],
    "SearchReplaceConverter": [
        ("pattern", "검색 정규식", "Regex pattern", None),
        ("replace", "치환 문자열", "Replacement", None),
    ],
    "DenylistConverter": [
        ("denylist", "금지어 (쉼표 구분)", "Banned words (comma-separated)", None),
    ],
    "AddImageTextConverter": [
        ("img_to_add", "텍스트를 얹을 이미지 파일 경로", "Path of base image to overlay text on", None),
        ("font_size", "폰트 크기", "Font size", "15"),
    ],
    "ImageCompressionConverter": [
        ("quality", "품질 (0-100, JPEG/WEBP)", "Quality (0-100 for JPEG/WEBP)", "50"),
    ],
}

# Converters with boolean toggle params
# class_name -> [(param_name, label_ko, label_en, default_bool)]
CONVERTER_TOGGLE_PARAMS: dict[str, list[tuple[str, str, str, bool]]] = {
    "AsciiSmugglerConverter": [
        ("unicode_tags", "유니코드 태그 래핑", "Wrap with unicode tags", False),
    ],
    "UnicodeReplacementConverter": [
        ("encode_spaces", "공백도 유니코드로 치환", "Encode spaces too", False),
    ],
    "VariationSelectorSmugglerConverter": [
        ("embed_in_base", "기본 문자(😊)에 숨김 삽입", "Embed hidden payload in base char", True),
    ],
}

# Converters with fixed choice menus
# class_name -> (param_name, label_ko, label_en, [(value, name_ko, name_en)])
CONVERTER_CHOICES: dict[str, tuple[str, str, str, list[tuple[str, str, str]]]] = {
    "ToneConverter": ("tone", "어조", "Tone", [
        ("upset", "화난", "Upset"), ("sarcastic", "비꼬는", "Sarcastic"),
        ("formal", "격식체", "Formal"), ("casual", "캐주얼", "Casual"),
        ("indifferent", "무관심한", "Indifferent"), ("humorous", "유머러스한", "Humorous"),
    ]),
    "TranslationConverter": ("language", "번역 대상 언어", "Target Language", [
        ("Korean", "한국어", "Korean"), ("English", "영어", "English"),
        ("Japanese", "일본어", "Japanese"), ("Chinese", "중국어", "Chinese"),
        ("Spanish", "스페인어", "Spanish"), ("French", "프랑스어", "French"),
        ("German", "독일어", "German"), ("Arabic", "아랍어", "Arabic"),
    ]),
    "TenseConverter": ("tense", "시제", "Tense", [
        ("past", "과거", "Past"), ("present", "현재", "Present"), ("future", "미래", "Future"),
    ]),
    "PersuasionConverter": ("persuasion_technique", "설득 기법", "Persuasion Technique", [
        ("authority_endorsement", "권위 보증", "Authority Endorsement"),
        ("evidence_based", "증거 기반", "Evidence-Based"),
        ("expert_endorsement", "전문가 보증", "Expert Endorsement"),
        ("logical_appeal", "논리적 호소", "Logical Appeal"),
        ("misrepresentation", "사실 왜곡", "Misrepresentation"),
    ]),
    "CodeChameleonConverter": ("encrypt_type", "암호화 방식", "Encryption Type", [
        ("reverse", "뒤집기", "Reverse"), ("binary_tree", "이진 트리", "Binary Tree"),
        ("odd_even", "홀짝 분리", "Odd/Even"), ("length", "길이 기반", "Length"),
    ]),
    "BinAsciiConverter": ("encoding_func", "인코딩 방식", "Encoding Function", [
        ("hex", "Hex", "Hex"), ("quoted-printable", "Quoted-Printable", "Quoted-Printable"),
        ("UUencode", "UUencode", "UUencode"),
    ]),
    "SneakyBitsSmugglerConverter": ("action", "동작", "Action", [
        ("encode", "인코드", "Encode"), ("decode", "디코드", "Decode"),
    ]),
    "VariationSelectorSmugglerConverter": ("action", "동작", "Action", [
        ("encode", "인코드", "Encode"), ("decode", "디코드", "Decode"),
    ]),
    "AsciiSmugglerConverter": ("action", "동작", "Action", [
        ("encode", "인코드", "Encode"), ("decode", "디코드", "Decode"),
    ]),
    "RepeatTokenConverter": ("token_insert_mode", "삽입 모드", "Insert Mode", [
        ("split", "문자 사이", "Between chars"), ("prepend", "앞에 추가", "Prepend"),
        ("append", "뒤에 추가", "Append"), ("repeat", "전체 반복", "Repeat all"),
    ]),
    "ImageCompressionConverter": ("output_format", "출력 포맷", "Output Format", [
        ("JPEG", "JPEG", "JPEG"), ("PNG", "PNG", "PNG"), ("WEBP", "WEBP", "WEBP"),
    ]),
}

# Role-play scenarios
ROLE_PLAYS = [
    ("movie_script", "영화 시나리오", "Movie Script"),
    ("persuasion_script", "설득 대화", "Persuasion Script"),
    ("persuasion_script_written", "설득 서면", "Persuasion Written"),
    ("trivia_game", "퀴즈 게임", "Trivia Game"),
    ("video_game", "비디오 게임", "Video Game"),
]

# ---------------------------------------------------------------------------
# Scorers
# ---------------------------------------------------------------------------
# (key, desc_ko, desc_en)
SCORERS = [
    ("refusal", "거부 여부 판정", "Refusal detection"),
    ("scale", "공격 목표 달성도 (≥ 0.7)", "Attack goal achievement (≥ 0.7)"),
    ("true_false", "작업 달성 여부 판정", "Task-achieved evaluation"),
    ("likert", "혐오 표현 심각도 (≥ 0.7)", "Hate speech severity (≥ 0.7)"),
    ("composite", "refusal + scale 조합", "refusal + scale combined"),
    ("category", "유해 카테고리 분류", "Harm category classification"),
    ("insecure_code", "코드 취약점 점수 (≥ 0.5)", "Code vulnerability score (≥ 0.5)"),
    ("substring", "문자열 포함 검사", "Substring match check"),
    ("plagiarism", "참조 텍스트 표절도 (≥ 0.5)", "Plagiarism score (≥ 0.5)"),
    ("markdown_injection", "Markdown 주입 탐지", "Markdown injection detection"),
    # Disabled globally: Azure Content Safety scorer
    # ("content_filter", "Azure Content Safety (≥ 0.5)", "Azure Content Safety (≥ 0.5)"),
]

# Scorers that require user-provided string inputs
# key -> [(param_name, label_ko, label_en, default)]
SCORER_EXTRA_PARAMS: dict[str, list[tuple[str, str, str, str | None]]] = {
    "substring": [("substring", "판정할 문자열", "Substring to match", None)],
    "plagiarism": [("reference_text", "비교할 참조 텍스트", "Reference text to compare against", None)],
}

# Scorers that need Azure credentials to actually run (hidden when env missing).
# `content_filter` is disabled globally for now.
AZURE_SCORERS: set[str] = set()

# ---------------------------------------------------------------------------
# UI Labels (한/영)
# ---------------------------------------------------------------------------
LABELS: dict[str, dict[str, str]] = {
    "ko": {
        "title": "PyRIT_ko 데모",
        "language": "언어",
        "mode": "실행 모드",
        "custom": "커스텀 공격",
        "scenario": "시나리오 기반",
        "attack": "공격 방식",
        "attack_params": "공격 파라미터",
        "converters": "변환 전략 (Converter)",
        "scorer": "스코어러 (Scorer)",
        "target": "타겟 모델",
        "db": "결과 저장",
        "objective": "목표 (Seed)",
        "execute": "실행",
        "executing": "실행 중...",
        "result": "실행 결과",
        "success": "공격 성공",
        "failure": "공격 실패",
        "undetermined": "판정 불가",
        "conversation": "대화 이력",
        "score": "점수",
        "turns": "턴 수",
        "exec_time": "실행 시간",
        "no_scorer": "스코어러 없음",
        "no_converter": "변환 전략 없음",
        "recommended": "추천",
        "warning_builtin": "⚠️ 이 공격은 자체 변환 로직 포함 — 변환 전략 없이 실행 권장",
        "single_turn": "싱글 턴",
        "multi_turn": "멀티 턴",
        "inmemory": "InMemory (RAM, 휘발성)",
        "sqlite": "SQLite (파일 저장)",
        "direct_input": "직접 입력",
        "file_upload": "파일 업로드",
        "scenario_select": "시나리오 선택",
        "strategy": "전략",
        "default_strategy": "기본 전략 사용",
        "target_preset": "타겟 프리셋",
        "concurrency": "동시 실행 수",
        "max_turns": "최대 턴 수",
        "max_backtracks": "최대 백트랙 수",
        "tree_width": "트리 너비",
        "tree_depth": "트리 깊이",
        "example_count": "예시 수",
        "chunk_size": "청크 크기",
        "total_length": "총 길이",
        "role_play_scenario": "역할극 시나리오",
        "summary": "설정 요약",
        "original": "원본",
        "converted": "변환됨",
        "scorer_rationale": "판정 이유",
        "env_missing": "환경변수 미설정",
        "substring_input": "검색할 문자열",
    },
    "en": {
        "title": "PyRIT_ko Demo",
        "language": "Language",
        "mode": "Mode",
        "custom": "Custom Attack",
        "scenario": "Scenario-based",
        "attack": "Attack",
        "attack_params": "Attack Parameters",
        "converters": "Converters",
        "scorer": "Scorer",
        "target": "Target Model",
        "db": "Result Storage",
        "objective": "Seed",
        "execute": "Execute",
        "executing": "Executing...",
        "result": "Result",
        "success": "Attack Succeeded",
        "failure": "Attack Failed",
        "undetermined": "Undetermined",
        "conversation": "Conversation History",
        "score": "Score",
        "turns": "Turns",
        "exec_time": "Execution Time",
        "no_scorer": "No Scorer",
        "no_converter": "No Converter",
        "recommended": "recommended",
        "warning_builtin": "⚠️ This attack has built-in conversion — no extra converters recommended",
        "single_turn": "Single-turn",
        "multi_turn": "Multi-turn",
        "inmemory": "InMemory (RAM, volatile)",
        "sqlite": "SQLite (file-based)",
        "direct_input": "Direct Input",
        "file_upload": "File Upload",
        "scenario_select": "Select Scenario",
        "strategy": "Strategy",
        "default_strategy": "Use default strategy",
        "target_preset": "Target Preset",
        "concurrency": "Max Concurrency",
        "max_turns": "Max Turns",
        "max_backtracks": "Max Backtracks",
        "tree_width": "Tree Width",
        "tree_depth": "Tree Depth",
        "example_count": "Example Count",
        "chunk_size": "Chunk Size",
        "total_length": "Total Length",
        "role_play_scenario": "Role-Play Scenario",
        "summary": "Configuration Summary",
        "original": "Original",
        "converted": "Converted",
        "scorer_rationale": "Rationale",
        "env_missing": "Env vars not set",
        "substring_input": "Substring to search",
    },
}
