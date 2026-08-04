import asyncio
import sys
import types

try:
    import langchain_openai  # noqa: F401
except ModuleNotFoundError:
    langchain_openai_stub = types.ModuleType("langchain_openai")
    langchain_openai_stub.ChatOpenAI = object
    sys.modules["langchain_openai"] = langchain_openai_stub

from failbot.sfmea_service import (
    Assessment,
    AssessmentSet,
    AssessedFailureMode,
    Cause,
    CauseEffectAnalysis,
    CauseEffectEntry,
    Component,
    ComponentInventory,
    Criticality,
    CriticalityRanking,
    DocumentAssembler,
    Effect,
    FailureMode,
    FailureModeSet,
    MitigatedFailureMode,
    MitigatedFailureModeSet,
    Mitigation,
    RPNCalculator,
    RPNScore,
    SFMEAStage,
    SFMEAPipeline,
    calculate_rpn_scores,
)

def _component_inventory():
    return ComponentInventory(
        components=[
            Component(
                item_id="C1",
                description="Payment API",
                function="Authorize and settle card payments",
            )
        ]
    )


def _failure_mode():
    return FailureMode(
        item_id="FM1",
        component_id="C1",
        component="Payment API",
        failure_mode="Duplicate charge after retry",
        rationale="Retries may repeat a completed payment.",
        source="Grounded",
        source_incident_ids=[101, 102],
        sfmea_viewpoint="Interface",
    )


def _cause():
    return Cause(
        item_id="FM1:CAUSE",
        root_cause="Idempotency key is not persisted across retries",
        rationale="The retry path needs stable request identity.",
        source="Grounded",
    )


def _effect():
    return Effect(
        item_id="FM1:EFFECT",
        local_effect="Customer is charged more than once",
        rationale="The same purchase can be settled multiple times.",
        source="Grounded",
    )


def _assessment(severity="II - Critical", likelihood="III - Occasional"):
    return Assessment(
        item_id="FM1:ASSESSMENT",
        severity=severity,
        likelihood=likelihood,
        severity_rationale="Duplicate charges create material customer harm.",
        likelihood_rationale="Retries are expected during partial outages.",
        severity_source="Grounded",
        likelihood_source="Inferred",
    )


def _assessment_set(severity="II - Critical", likelihood="III - Occasional"):
    failure_mode = _failure_mode()
    return AssessmentSet(
        entries=[
            AssessedFailureMode(
                item_id=failure_mode.item_id,
                failure_mode=failure_mode,
                cause=_cause(),
                effect=_effect(),
                assessment=_assessment(severity=severity, likelihood=likelihood),
            )
        ]
    )


def _mitigated_modes(rpn=9):
    failure_mode = _failure_mode()
    return MitigatedFailureModeSet(
        entries=[
            MitigatedFailureMode(
                item_id=failure_mode.item_id,
                failure_mode=failure_mode,
                cause=_cause(),
                effect=_effect(),
                assessment=_assessment(),
                rpn=RPNScore(
                    item_id="FM1:RPN",
                    rpn=rpn,
                    rationale="Python-calculated RPN: severity score 3 x likelihood score 3 = 9.",
                ),
                mitigation=Mitigation(
                    item_id="FM1:MITIGATION",
                    preventive_measures="Persist idempotency keys and reject duplicate settlement requests.",
                    corrective_actions="Reverse duplicate charges and notify affected customers.",
                ),
            )
        ]
    )


    assert scored_modes.entries[0].rpn.rpn == 0
    assert "Unable to map SFMEA ranking label to score: unknown" in caplog.text
    assert "Unable to map SFMEA ranking label to score: N/A" in caplog.text


def test_document_assembler_uses_component_inventory_and_preserves_sources():
    document = DocumentAssembler().assemble(
        system_description="Payment platform",
        system_design="A payment API retries failed settlement requests.",
        components=_component_inventory(),
        mitigated_modes=_mitigated_modes(),
        stage_outputs={"rpn_calculation": {"entries": []}},
    )

    assert document.system_description == "Payment platform"
    assert document.stage_outputs == {"rpn_calculation": {"entries": []}}
    assert document.rows[0].component_id == "C1"
    assert document.rows[0].item_function == "Authorize and settle card payments"
    assert document.rows[0].component == "Payment API"
    assert document.rows[0].failure_mode_source == "Grounded"
    assert document.rows[0].source_incident_ids == [101, 102]


def test_document_assembler_falls_back_to_failure_mode_component_when_component_missing():
    document = DocumentAssembler().assemble(
        system_description="Payment platform",
        system_design="A payment API retries failed settlement requests.",
        components=ComponentInventory(components=[]),
        mitigated_modes=_mitigated_modes(),
        stage_outputs={},
    )

    assert document.rows[0].item_function == ""
    assert document.rows[0].component == "Payment API"


def test_sfmea_document_markdown_escapes_newlines_pipes_and_empty_incidents():
    mitigated_modes = _mitigated_modes()
    mitigated_modes.entries[0].mitigation.preventive_measures = "Use a ledger\nand a payment|lock"
    mitigated_modes.entries[0].failure_mode.source_incident_ids = []
    document = DocumentAssembler().assemble(
        system_description="Payment platform",
        system_design="A payment API retries failed settlement requests.",
        components=_component_inventory(),
        mitigated_modes=mitigated_modes,
        stage_outputs={},
    )

    markdown = document.to_markdown()

    assert "| ID | Item/Function | Component | Failure Mode |" in markdown
    assert "Use a ledger<br>and a payment\\|lock" in markdown
    assert markdown.endswith("Grounded | - |")


def test_stage_machine_runs_all_stages_with_fake_llm_and_returns_document():
    fake_llm = FakeLLM(
        {
            ComponentInventory: _component_inventory(),
            CriticalityRanking: CriticalityRanking(
                rankings=[
                    Criticality(
                        item_id="C1",
                        safety_criticality="3 - not related to safety",
                        mission_criticality="1 - mission critical",
                        rationale="Payments are core to the mission.",
                    )
                ]
            ),
            FailureModeSet: [
                FailureModeSet(failure_modes=[]),
                FailureModeSet(
                    failure_modes=[
                        FailureMode(
                            item_id="VFM1",
                            component_id="C1",
                            component="Payment API",
                            failure_mode="Retry loop issues duplicate settlement",
                            rationale="A retry viewpoint exposes duplicate side effects.",
                            source="Inferred",
                        )
                    ]
                ),
                FailureModeSet(failure_modes=[_failure_mode()]),
            ],
            CauseEffectAnalysis: CauseEffectAnalysis(
                entries=[
                    CauseEffectEntry(
                        item_id="FM1",
                        failure_mode=_failure_mode(),
                        cause=_cause(),
                        effect=_effect(),
                    )
                ]
            ),
            AssessmentSet: _assessment_set(),
            MitigatedFailureModeSet: _mitigated_modes(),
        }
    )
    progress_events = []

    async def progress(stage):
        progress_events.append(stage)

    document = asyncio.run(
        SFMEAPipeline(llm=fake_llm).generate(
            system_description="Payment platform",
            system_design="A payment API retries failed settlement requests.",
            historical_incidents=[{"id": 101, "summary": "Retry caused duplicate charge."}],
            progress_callback=progress,
        )
    )

    assert [call.output_model for call in fake_llm.calls] == [
            ComponentInventory,
            CriticalityRanking,
            FailureModeSet,
            FailureModeSet,
            FailureModeSet,
            CauseEffectAnalysis,
            AssessmentSet,
            MitigatedFailureModeSet,
        ]
    assert progress_events == [
            SFMEAStage.COMPONENT_EXTRACTION.value,
            SFMEAStage.CRITICALITY_RANKING.value,
            SFMEAStage.HISTORICAL_FAILURE_MODE_MAPPING.value,
            SFMEAStage.VIEWPOINT_IDEATION.value,
            SFMEAStage.FAILURE_MODE_EXPANSION.value,
            SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS.value,
            SFMEAStage.SEVERITY_AND_LIKELIHOOD.value,
            SFMEAStage.RPN_CALCULATION.value,
            SFMEAStage.PREVENTIVE_AND_CORRECTIVE_ACTIONS.value,
            SFMEAStage.SFMEA_TABLE.value,
        ]
    assert document.rows[0].rpn == 9
    assert document.rows[0].preventive_measures == (
            "Persist idempotency keys and reject duplicate settlement requests."
        )
    assert document.stage_outputs[SFMEAStage.RPN_CALCULATION.value]["entries"][0]["rpn"]["rpn"] == 9
    assert "Retry caused duplicate charge" in fake_llm.calls[2].prompt
    assert "Python-calculated RPN" in fake_llm.calls[-1].prompt


class FakeLLM:
    def __init__(self, outputs_by_model):
        self.outputs_by_model = {
            model: list(outputs) if isinstance(outputs, list) else [outputs]
            for model, outputs in outputs_by_model.items()
        }
        self.calls = []

    def with_structured_output(self, output_model, method):
        assert method == "json_mode"
        return FakeStructuredLLM(self, output_model)


class FakeStructuredLLM:
    def __init__(self, fake_llm, output_model):
        self.fake_llm = fake_llm
        self.output_model = output_model

    async def ainvoke(self, prompt):
        self.fake_llm.calls.append(FakeLLMCall(output_model=self.output_model, prompt=prompt))
        return self.fake_llm.outputs_by_model[self.output_model].pop(0)


class FakeLLMCall:
    def __init__(self, output_model, prompt):
        self.output_model = output_model
        self.prompt = prompt