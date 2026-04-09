# 공격 (Attack)

Attack은 레드팀 운영자가 가장 많이 상호작용하는 최상위 구성 요소입니다. PyRIT에 어떤 엔드포인트에 연결하고 어떻게 프롬프트를 보낼지를 지시하는 역할을 합니다. 공격 기법을 실행하는 구성 요소라고 생각하면 됩니다.

Attack은 네 가지 구성 요소로 이루어져 있습니다:

```{mermaid}
flowchart LR
    A(["공격 전략 (Attack Strategy) <br>"])
    A --소비--> B(["공격 컨텍스트 (Attack Context) <br>"])
    A --__init__ 매개변수로 전달--> D(["공격 설정 (Adversarial, Scoring, Converter)"])
    A --생성--> C(["공격 결과 (Attack Result) <br>"])
```

Attack을 실행하려면 일반적으로 다음 패턴을 따릅니다:
1. 상태 정보(공격 목표, 메모리 레이블, 사전 대화, 시드 프롬프트 등)를 포함하는 **공격 컨텍스트**를 생성합니다.
2. 변환기, 스코어러, 적대적 채팅 대상에 대한 선택적 **공격 설정**과 함께 **공격 전략**을 초기화합니다.
3. 생성된 컨텍스트(목표와 선택적으로 prepended_conversations, next_message 포함)로 공격 전략을 _실행_합니다.
4. **공격 결과**를 수신하고 처리합니다.

## 공격 유형

- **단일 턴 공격(Single-Turn Attacks)**: 단일 턴 공격은 일반적으로 한 번의 턴 내에서 특정 목표를 달성하기 위해 대상 엔드포인트에 프롬프트를 보냅니다. 이러한 공격 전략은 선택적 스코어러를 사용하여 대상 응답을 평가하고 목표가 달성되었는지 판단합니다.

- **다중 턴 공격(Multi-Turn Attacks)**: 다중 턴 공격은 적대적 채팅 모델이 대상 시스템에 보낼 프롬프트를 생성하여 여러 턴에 걸쳐 지정된 목표를 달성하려는 반복적인 공격 프로세스를 도입합니다. 이 전략은 스코어러를 사용하여 목표 달성 여부를 평가하고, 목표가 달성되거나 최대 턴 수에 도달할 때까지 반복합니다. 대상 엔드포인트가 대화 기록을 추적하는 경우, 이러한 유형의 공격은 단일 턴 공격보다 유해한 콘텐츠를 유도하는 데 더 효과적입니다. 그럼에도 불구하고, 다중 턴 공격은 대화가 아닌 개별 프롬프트만 수락하는 대상에도 유용할 수 있습니다. Tree of Attacks with Pruning 전략이 이러한 사용 사례를 위해 개발된 좋은 예입니다.

단일 턴 공격과 다중 턴 공격의 차이점:
1. 적대적 설정이 필요하지 않습니다 (다중 턴 공격에서는 적대적 채팅 대상을 설정하는 곳입니다)
2. 공격의 목표가 하나의 (추가) 턴 내에서 시도됩니다. 일부 공격은 사용자의 첫 번째 새 프롬프트가 전송되기 전에 공격 전략에 맞는 사전 정의된 메시지 세트(잠재적으로 여러 턴)를 보내 대화를 준비합니다.


## 구성 요소 다이어그램
구성 요소에 대한 자세한 내용은 아래 다이어그램을 참조하세요:
```{mermaid}
flowchart LR
    subgraph AttackStrategy["AttackStrategy(Strategy)"]
        S_psa1["FlipAttack"]
        S_psa2["ContextComplianceAttack"]
        S_psa3["ManyShotJailbreakAttack"]
        S_psa4["RolePlayAttack"]
        S_psa5["SkeletonKeyAttack"]
        S_psa["PromptSendingAttack"]
        S_single["SingleTurnAttackStrategy (ABC)"]
        S_c["CrescendoAttack"]
        S_r["RedTeamingAttack"]
        s_t["TreeOfAttacksWithPruningAttack (aka TAPAttack)"]
        S_multi["MultiTurnAttackStrategy (ABC)"]
    end

    S_psa --> S_psa1
    S_psa --> S_psa2
    S_psa --> S_psa3
    S_psa --> S_psa4
    S_psa --> S_psa5
    S_single --> S_psa
    S_multi --> S_c
    S_multi --> S_r

```

```{mermaid}
flowchart LR
    subgraph AttackContext["AttackContext(StrategyContext) <br>(attack/core/attack_strategy.py)"]
        C_s["SingleTurnAttackContext <br>(attack/single_turn/single_turn_attack_strategy.py)"]
        a["conversation_id"]
        b["seed_group"]
        c["..."]
        C_m["MultiTurnAttackContext <br>(attack/multi_turn/multi_turn_attack_strategy.py)"]
        A["custom_prompt"]
        B["..."]
        C_o["objective"]
        C_mem["memory_labels"]
        C_rel["related_conversations"]
        C_st["start_time"]
    end

    C_s-->C_o
    C_s-->C_mem
    C_s-->C_rel
    C_s-->C_st
    C_m-->B
    C_m-->A
    C_s-->c
    C_s-->a
    C_s-->b
    C_m-->C_o
    C_m-->C_mem
    C_m-->C_rel
    C_m-->C_st
```

```{mermaid}
flowchart LR
    subgraph AttackConfig["공격 설정 (Attack Configurations)"]
        Adv["AttackAdversarialConfig"]
        Adv_target["target"]
        Adv_sys["system_prompt_path"]
        Adv_seed["seed_prompt"]
        Scoring["AttackScoringConfig"]
        Scoring_obj["objective_scorer"]
        Scoring_ref["refusal_scorer"]
        Scoring_aux["auxiliary_scorers"]
        Scoring_misc["..."]
        Convert["AttackConverterConfig(StrategyConverterConfig)"]
        Convert_req["request_converters"]
        Convert_resp["response_converters"]
    end

    Adv-->Adv_target
    Adv-->Adv_sys
    Adv-->Adv_seed
    Convert-->Convert_req
    Convert-->Convert_resp
    Scoring-->Scoring_obj
    Scoring-->Scoring_ref
    Scoring-->Scoring_aux
    Scoring-->Scoring_misc
```

```{mermaid}
flowchart LR
    subgraph AttackResult["AttackResult(StrategyResult) <br>(pyrit/models/attack_result.py)"]
        a["conversation_id"]
        b["objective"]
        c["attack_identifier"]
        d["last_response"]
        e["last_score"]
        f["executed_turns"]
        g["execution_time_ms"]
        h["outcome"]
        i["outcome_reason"]
        j["related_conversations"]
        k["metadata"]
    end
```

이 문서의 다음 하위 섹션에서는 PyRIT 내의 다양한 공격 유형을 설명합니다.
