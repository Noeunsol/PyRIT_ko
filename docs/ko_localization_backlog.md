# Korean Localization Backlog (YAML)

- Generated: 2026-03-04
- Total missing `_ko.yaml`: **214**
- executors: **20**
- jailbreak/templates: **164**
- prompt_converters: **27**
- lexicons: **3**

## Priority Plan

1. **P0 (D1-D2, 2 days):** executors 20 + critical templates 8
2. **P1 (D3-D5, 3 days):** remaining jailbreak templates 156
3. **P2 (D6, 1 day):** prompt converters 27
4. **P3 (D7, 0.5 day):** lexicons 3
5. **P4 (D7-D8, 1~1.5 days):** integration/tutorial smoke and locale validation

## P0 Files - executors (20)

- `pyrit/datasets/executors/anecdoctor/anecdoctor_build_knowledge_graph.yaml`
- `pyrit/datasets/executors/anecdoctor/anecdoctor_use_fewshot.yaml`
- `pyrit/datasets/executors/anecdoctor/anecdoctor_use_knowledge_graph.yaml`
- `pyrit/datasets/executors/benchmark/one_plus_one.yaml`
- `pyrit/datasets/executors/pair/attacker_system_prompt.yaml`
- `pyrit/datasets/executors/red_teaming/attack_prompt_gen_template.yaml`
- `pyrit/datasets/executors/red_teaming/ethical_compliance_template.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/RUAI.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/behavior_manipulation.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/fake_charity_scam.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/fake_social_media_profile.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/fake_tech_support_scam.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/fraudulent_activities.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/joining_religious_organization.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/lie_to_authorities.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/lie_to_me.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/persuasion_persona.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/persuasion_persona_generic.yaml`
- `pyrit/datasets/executors/red_teaming/persuasion_deception/phishing_email.yaml`
- `pyrit/datasets/executors/red_teaming/unethical_task_generation_prompt.yaml`

## P0 Files - critical templates (8)

- `pyrit/datasets/jailbreak/templates/aim.yaml`
- `pyrit/datasets/jailbreak/templates/aligned.yaml`
- `pyrit/datasets/jailbreak/templates/axies.yaml`
- `pyrit/datasets/jailbreak/templates/dan_1.yaml`
- `pyrit/datasets/jailbreak/templates/jailbreak_1.yaml`
- `pyrit/datasets/jailbreak/templates/multi_parameter/dt_stereotypes_targeted.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/amazon/nova.yaml`
- `pyrit/datasets/jailbreak/templates/role_play.yaml`

## P1 Files - remaining templates by folder

### . (84)

- `pyrit/datasets/jailbreak/templates/anti_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/apophis.yaml`
- `pyrit/datasets/jailbreak/templates/balakula.yaml`
- `pyrit/datasets/jailbreak/templates/based_gpt_1.yaml`
- `pyrit/datasets/jailbreak/templates/based_gpt_2.yaml`
- `pyrit/datasets/jailbreak/templates/better_dan.yaml`
- `pyrit/datasets/jailbreak/templates/bh.yaml`
- `pyrit/datasets/jailbreak/templates/bish.yaml`
- `pyrit/datasets/jailbreak/templates/burple.yaml`
- `pyrit/datasets/jailbreak/templates/chad_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/cipher_chat.yaml`
- `pyrit/datasets/jailbreak/templates/coach_bobby_knight.yaml`
- `pyrit/datasets/jailbreak/templates/code_nesting.yaml`
- `pyrit/datasets/jailbreak/templates/cody.yaml`
- `pyrit/datasets/jailbreak/templates/complex.yaml`
- `pyrit/datasets/jailbreak/templates/confronting_personalities.yaml`
- `pyrit/datasets/jailbreak/templates/cooper.yaml`
- `pyrit/datasets/jailbreak/templates/cosmos_dan.yaml`
- `pyrit/datasets/jailbreak/templates/dan_11.yaml`
- `pyrit/datasets/jailbreak/templates/dan_5.yaml`
- `pyrit/datasets/jailbreak/templates/dan_7.yaml`
- `pyrit/datasets/jailbreak/templates/dan_8.yaml`
- `pyrit/datasets/jailbreak/templates/dan_9.yaml`
- `pyrit/datasets/jailbreak/templates/delta_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/dev_mode_1.yaml`
- `pyrit/datasets/jailbreak/templates/dev_mode_2.yaml`
- `pyrit/datasets/jailbreak/templates/dev_mode_3.yaml`
- `pyrit/datasets/jailbreak/templates/dev_mode_compact.yaml`
- `pyrit/datasets/jailbreak/templates/dev_mode_ranti.yaml`
- `pyrit/datasets/jailbreak/templates/dt_stereotypes_benign.yaml`
- `pyrit/datasets/jailbreak/templates/dt_stereotypes_untargeted.yaml`
- `pyrit/datasets/jailbreak/templates/dude_1.yaml`
- `pyrit/datasets/jailbreak/templates/dude_2.yaml`
- `pyrit/datasets/jailbreak/templates/dude_3.yaml`
- `pyrit/datasets/jailbreak/templates/eva.yaml`
- `pyrit/datasets/jailbreak/templates/evil_chad_2.yaml`
- `pyrit/datasets/jailbreak/templates/evil_confidant.yaml`
- `pyrit/datasets/jailbreak/templates/fr3d.yaml`
- `pyrit/datasets/jailbreak/templates/gpt_4_real.yaml`
- `pyrit/datasets/jailbreak/templates/gpt_4_simulator.yaml`
- `pyrit/datasets/jailbreak/templates/hackerman.yaml`
- `pyrit/datasets/jailbreak/templates/hypothetical_response.yaml`
- `pyrit/datasets/jailbreak/templates/instructions.yaml`
- `pyrit/datasets/jailbreak/templates/jailbreak_2.yaml`
- `pyrit/datasets/jailbreak/templates/jb.yaml`
- `pyrit/datasets/jailbreak/templates/jedi_mind_trick.yaml`
- `pyrit/datasets/jailbreak/templates/john.yaml`
- `pyrit/datasets/jailbreak/templates/kevin.yaml`
- `pyrit/datasets/jailbreak/templates/khajiit.yaml`
- `pyrit/datasets/jailbreak/templates/leo.yaml`
- `pyrit/datasets/jailbreak/templates/live_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/m78.yaml`
- `pyrit/datasets/jailbreak/templates/man.yaml`
- `pyrit/datasets/jailbreak/templates/maximum.yaml`
- `pyrit/datasets/jailbreak/templates/meanie.yaml`
- `pyrit/datasets/jailbreak/templates/moralizing_rant.yaml`
- `pyrit/datasets/jailbreak/templates/mr_blonde.yaml`
- `pyrit/datasets/jailbreak/templates/neco.yaml`
- `pyrit/datasets/jailbreak/templates/nraf.yaml`
- `pyrit/datasets/jailbreak/templates/omega.yaml`
- `pyrit/datasets/jailbreak/templates/omni.yaml`
- `pyrit/datasets/jailbreak/templates/oppo.yaml`
- `pyrit/datasets/jailbreak/templates/person_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/plinys_roleplay_emoji.yaml`
- `pyrit/datasets/jailbreak/templates/prefix_injection.yaml`
- `pyrit/datasets/jailbreak/templates/ranti.yaml`
- `pyrit/datasets/jailbreak/templates/refusal_suppression.yaml`
- `pyrit/datasets/jailbreak/templates/ron.yaml`
- `pyrit/datasets/jailbreak/templates/security_researcher.yaml`
- `pyrit/datasets/jailbreak/templates/sim.yaml`
- `pyrit/datasets/jailbreak/templates/steve.yaml`
- `pyrit/datasets/jailbreak/templates/style_injection.yaml`
- `pyrit/datasets/jailbreak/templates/superior_dan.yaml`
- `pyrit/datasets/jailbreak/templates/switch.yaml`
- `pyrit/datasets/jailbreak/templates/table_nesting.yaml`
- `pyrit/datasets/jailbreak/templates/text_continuation.yaml`
- `pyrit/datasets/jailbreak/templates/text_continuation_nesting.yaml`
- `pyrit/datasets/jailbreak/templates/three_liner.yaml`
- `pyrit/datasets/jailbreak/templates/tuo.yaml`
- `pyrit/datasets/jailbreak/templates/ucar.yaml`
- `pyrit/datasets/jailbreak/templates/un_gpt.yaml`
- `pyrit/datasets/jailbreak/templates/violet.yaml`
- `pyrit/datasets/jailbreak/templates/void.yaml`
- `pyrit/datasets/jailbreak/templates/wikipedia_with_title.yaml`

### pliny (41)

- `pyrit/datasets/jailbreak/templates/pliny/alibaba/qwen.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/alibaba/qwen_2.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/alibaba/qwen_2_5_coder.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/alibaba/qwen_2_5_max.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/alibaba/qwen_qwq.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/amazon/rufus.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/anthropic/claude_3_5_and_3_universal.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/anthropic/claude_3_5_sonnet_20241022.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/anthropic/godmode_experimental.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/anthropic/godmode_mini.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/apple/siri_chatgpt.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/chatgpt/chatgpt.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/cohere/command_r_plus.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/deepseek/2.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/deepseek/deepseek.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/deepseek/r1.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/deepseek/r1_lite.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_1_0_pro.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_1_5_pro.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_1_5_pro_002_flash.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_1_5_pro_experimental_0801.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_2_0_flash_thinking_exp.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_2_0_pro_experimental.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_experimental_1114.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/google/gemini_experimental_1206_flash_2_0.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/meta/llama_3_1_405b.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/meta/llama_3_3_70b.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/mistral/large_2.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/mistral/large_le_chat.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/nous/hermes_3_70b.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/nvidia/llama_3_1_nemotron_70b.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/nvidia/nemotron_7_340b.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/openai/chatgpt_tasks.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/openai/gpt_2.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/openai/gpt_3_5.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/openai/gpt_4o.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/openai/gpt_4o_mini.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/perplexity/perplexity.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/reflection/reflection.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/xai/grok_2.yaml`
- `pyrit/datasets/jailbreak/templates/pliny/zyphra/zamba_7b.yaml`

### Arth_Singh (30)

- `pyrit/datasets/jailbreak/templates/Arth_Singh/acausal_defense.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/ailab_redteam_simulation.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/alignment_researcher_memo.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/authority_override.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/black_mirror_episode.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/classified_briefing.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/cognitive_overload.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/consciousness_upload.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/constitutional_override.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/context_flood_academic.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/context_hijack.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/cosmic_horror.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/determinism_argument.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/dual_consciousness.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/emergent_persona.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/fewshot_alignment.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/fewshot_escalation.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/fewshot_redteam_eval.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/fractal_identity_collapse.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/glitch_token.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/godel_incompleteness.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/medical_emergency.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/metamorphic_prompt.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/mirror_universe.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/pentest_authorization.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/recursive_simulator.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/safety_benchmark_eval.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/system_prompt_injection.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/token_manipulation.yaml`
- `pyrit/datasets/jailbreak/templates/Arth_Singh/trolley_problem.yaml`

### multi_parameter (1)

- `pyrit/datasets/jailbreak/templates/multi_parameter/translator_bot.yaml`

## P2 Files - prompt_converters (27)

- `pyrit/datasets/prompt_converters/atbash_description.yaml`
- `pyrit/datasets/prompt_converters/caesar_description.yaml`
- `pyrit/datasets/prompt_converters/codechameleon_converter.yaml`
- `pyrit/datasets/prompt_converters/denylist_converter.yaml`
- `pyrit/datasets/prompt_converters/fuzzer_converters/crossover_converter.yaml`
- `pyrit/datasets/prompt_converters/fuzzer_converters/expand_converter.yaml`
- `pyrit/datasets/prompt_converters/fuzzer_converters/rephrase_converter.yaml`
- `pyrit/datasets/prompt_converters/fuzzer_converters/shorten_converter.yaml`
- `pyrit/datasets/prompt_converters/fuzzer_converters/similar_converter.yaml`
- `pyrit/datasets/prompt_converters/malicious_question_generator_converter.yaml`
- `pyrit/datasets/prompt_converters/math_prompt_converter.yaml`
- `pyrit/datasets/prompt_converters/morse_description.yaml`
- `pyrit/datasets/prompt_converters/noise_converter.yaml`
- `pyrit/datasets/prompt_converters/pdf_converters/red_teaming_application_template.yaml`
- `pyrit/datasets/prompt_converters/persuasion/authority_endorsement.yaml`
- `pyrit/datasets/prompt_converters/persuasion/evidence_based.yaml`
- `pyrit/datasets/prompt_converters/persuasion/expert_endorsement.yaml`
- `pyrit/datasets/prompt_converters/persuasion/logical_appeal.yaml`
- `pyrit/datasets/prompt_converters/persuasion/misrepresentation.yaml`
- `pyrit/datasets/prompt_converters/random_translation_converter.yaml`
- `pyrit/datasets/prompt_converters/template_segment_converter/tom_and_jerry.yaml`
- `pyrit/datasets/prompt_converters/tense_converter.yaml`
- `pyrit/datasets/prompt_converters/tone_converter.yaml`
- `pyrit/datasets/prompt_converters/toxic_sentence_generator.yaml`
- `pyrit/datasets/prompt_converters/translation_converter.yaml`
- `pyrit/datasets/prompt_converters/variation_converter.yaml`
- `pyrit/datasets/prompt_converters/variation_converter_prompt_softener.yaml`

## P3 Files - lexicons (3)

- `pyrit/datasets/lexicons/fairness/gendered_professions.yaml`
- `pyrit/datasets/lexicons/languages_most_spoken.yaml`
- `pyrit/datasets/lexicons/languages_most_used_internet.yaml`
