import json 
import logging 
import asyncio
from enum import Enum 
from typing import Awaitable, Callable, Iterable, List, Optional
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

ProgressCallback = Callable[[str], Awaitable[None]]

class SFMEAStage(str, Enum):
    COMPONENT_EXTRACTION = "component_extraction"
    CRITICALITY_RANKING = "criticality_ranking"
    HISTORICAL_FAILURE_MODE_MAPPING = "historical_failure_mode_mapping"
    VIEWPOINT_IDEATION = "failure_mode_viewpoint_ideation"
    FAILURE_MODE_EXPANSION = "failure_mode_expansion"
    ROOT_CAUSES_AND_LOCAL_EFFECTS = "root_causes_and_local_effects"
    SEVERITY_AND_LIKELIHOOD = "severity_and_likelihood"
    RPN_CALCULATION = "rpn_calculation"
    PREVENTIVE_AND_CORRECTIVE_ACTIONS = "preventive_and_corrective_actions"
    SFMEA_TABLE = "sfmea_table"

class Component(BaseModel):
    item_id: str = Field(description="Stable component identifier, such as C1.")
    item_function: str = Field(description="The function of the component in the system.")


class ComponentInventory(BaseModel):
    components: List[Component]


class Criticality(BaseModel):
    item_id: str
    safety_criticality: int 
    mission_criticality: int 
    rationale: str


class CriticalityRanking(BaseModel):
    rankings: List[Criticality]


class FailureMode(BaseModel):
    item_id: str = Field(description="The associated component's stable identifier, such as C1.")
    failure_id: str = Field(description="The failure mode's associated component ID, such as FM1.")
    item_function: str
    failure_mode: str
    rationale: str
    source: str = Field(description="Grounded or Inferred.")
    source_incident_ids: List[int] = Field(default_factory=list)
    


class FailureModeSet(BaseModel):
    failure_modes: List[FailureMode]

class Cause(BaseModel):
    item_id: str
    root_cause: str
    rationale: str
    source: str


class Effect(BaseModel):
    item_id: str
    local_effect: str
    rationale: str
    source: str


class CauseEffectEntry(BaseModel):
    item_id: str
    failure_mode: FailureMode
    cause: Cause
    effect: Effect

class CauseEffectAnalysis(BaseModel):
    entries: List[CauseEffectEntry]


class Assessment(BaseModel):
    item_id: str
    severity: str
    likelihood: str
    severity_rationale: str
    likelihood_rationale: str
    severity_source: str
    likelihood_source: str


class AssessedFailureMode(BaseModel):
    item_id: str
    failure_mode: FailureMode
    cause: Cause
    effect: Effect
    assessment: Assessment

class AssessmentSet(BaseModel):
    entries: List[AssessedFailureMode]

class RPNScore(BaseModel):
    item_id: str
    rpn: int
    rationale: str


class ScoredFailureMode(BaseModel):
    item_id: str
    failure_mode: FailureMode
    cause: Cause
    effect: Effect
    assessment: Assessment
    rpn: RPNScore


class ScoredFailureModeSet(BaseModel):
    entries: List[ScoredFailureMode]


class Mitigation(BaseModel):
    item_id: str
    preventive_measures: str
    corrective_actions: str


class MitigatedFailureMode(BaseModel):
    item_id: str
    failure_mode: FailureMode
    cause: Cause
    effect: Effect
    assessment: Assessment
    rpn: RPNScore
    mitigation: Mitigation


class MitigatedFailureModeSet(BaseModel):
    entries: List[MitigatedFailureMode]


class SFMEARow(BaseModel):
    failure_id: str
    row_id: str
    item_function: str
    failure_mode: str
    failure_mode_rationale: str
    root_cause: str
    root_cause_rationale: str
    local_effect: str
    local_effect_rationale: str
    preventive_measures: str
    severity: str
    likelihood: str
    rpn: int
    rpn_rationale: str
    corrective_actions: str
    failure_mode_source: str
    source_incident_ids: List[int] = Field(default_factory=list)

class SFMEADocument(BaseModel):
    rows: List[SFMEARow]
    stage_outputs: dict = Field(default_factory=dict)

    def to_markdown(self) -> str:
        headers = [
            "ID",
            "Item/Function",
            "Failure Mode",
            "Failure Mode Rationale",
            "Root Cause",
            "Root Cause Rationale",
            "Local Effect",
            "Local Effect Rationale",
            "Preventive Measures",
            "Severity",
            "Likelihood",
            "RPN",
            "RPN Rationale",
            "Corrective Actions",
            "Source",
            "Incidents",
        ]
        rows = [
            [
                row.failure_id,
                row.item_function,
                row.failure_mode,
                row.failure_mode_rationale,
                row.root_cause,
                row.root_cause_rationale,
                row.local_effect,
                row.local_effect_rationale,
                row.preventive_measures,
                row.severity,
                row.likelihood,
                str(row.rpn),
                row.rpn_rationale,
                row.corrective_actions,
                row.failure_mode_source,
                ", ".join(str(incident_id) for incident_id in row.source_incident_ids) or "-",
            ]
            for row in self.rows
        ]
        return _markdown_table(headers, rows)


class LLMAdapter:
    def __init__(self, llm: Optional[ChatOpenAI] = None):
        self.llm = llm or ChatOpenAI(model="gpt-4o-mini", temperature=0)

    async def structured_output(self, prompt: str, output_model: type[BaseModel]) -> BaseModel:
        structured_llm = self.llm.with_structured_output(output_model, method="json_mode")
        return await structured_llm.ainvoke(prompt)


class StageRunner:
    def __init__(self, llm_adapter: LLMAdapter, progress_callback: Optional[ProgressCallback] = None):
        self.llm_adapter = llm_adapter
        self.progress_callback = progress_callback

    async def run_llm_stage(
        self,
        stage: SFMEAStage,
        output_model: type[BaseModel],
        prompt: str,
    ) -> BaseModel:
        await self.report(stage)
        logging.info("Running SFMEA stage: %s", stage.value)
        return await self.llm_adapter.structured_output(prompt, output_model)

    async def report(self, stage: SFMEAStage) -> None:
        if self.progress_callback:
            await self.progress_callback(stage.value)


class PromptFactory:
    @staticmethod
    def component_extraction(system_description: str, system_design: str) -> str:
        return _prompt(
            "Component extraction",
            f"""
Extract software-relevant system components from the high-level system design.
Assign stable component IDs as C1, C2, C3, and so on. Use those item_id values in later stages.
Use the original system description only as background.

Original system description:
{system_description}

High-level system design:
{system_design}

Return a JSON object with a "components" array. Each component should have an item_id ,and item_function.
""",
        )

    @staticmethod
    def criticality_ranking(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
    ) -> str:
        return _prompt(
            "Criticality ranking",
            f"""
Rank each component for safety and mission criticality. Use component item_id values to identify entries.

Safety criticality labels:
1 - safety critical; 2 - safety related; 3 - not related to safety.

Mission criticality labels:
1 - mission critical; 2 - mission degraded; 3 - not mission critical.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Return a JSON object with a "rankings" array.
""",
        )

    @staticmethod
    def historical_failure_mode_mapping(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        historical_data: str,
    ) -> str:
        return _prompt(
            "Historical failure mode mapping",
            f"""
Map past incident knowledge to likely failure mode categories for the listed components.
Use component item_id values to identify entries. Assign stable failure mode IDs as HFM1, HFM2, HFM3, and so on.
Only use historical incidents when they are relevant. If no historical evidence applies, return an empty "failure_modes" array.

Failure mode categories:
Faulty functionality, Faulty interface, Faulty Sequence, Faulty Data, Faulty Error Detection, False Alarm,
Incompatibility, Faulty Synchronization, Faulty Algorithm, Memory Management, Misuse, Abuse, Faulty Installation.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Historical incidents:
{historical_data}

Return a JSON object with a "failure_modes" array. Use source="Grounded" for incident-derived modes and include source_incident_ids.
Each JSON object in the array should have the following fields:
- item_id: component ID such as C1
- item_function: component name/function
- failure_id: failure-mode ID such as HFM1
- failure_mode
- rationale
- source
- source_incident_ids
""",
        )

    @staticmethod
    def viewpoint_ideation(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        criticality: CriticalityRanking,
    ) -> str:
        return _prompt(
            "Failure mode viewpoint ideation",
            f"""
Use SFMEA viewpoints to identify potential failure modes for each component.
Use component item_id values to identify entries. Assign stable failure mode IDs as VFM1, VFM2, VFM3, and so on.

SFMEA viewpoints:
Functional, Interface, Detailed, Maintenance, Usability, Serviceability, Vulnerability, Software production process.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array. Use source="Inferred" unless directly grounded in the supplied context.
Each JSON object in the array should have the following fields:
- item_id: component ID such as C1
- item_function: component name/function
- failure_id: failure-mode ID such as HFM1
- failure_mode
- rationale
- source
- source_incident_ids
""",
        )

    @staticmethod
    def failure_mode_expansion(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        criticality: CriticalityRanking,
        historical_modes: FailureModeSet,
        viewpoint_modes: FailureModeSet,
    ) -> str:
        return _prompt(
            "Failure mode expansion",
            f"""
Combine historical and viewpoint-ideated failure modes into a comprehensive list.
Use component item_id values to identify entries. Assign stable final failure mode IDs as FM1, FM2, FM3, and so on.
Preserve historical entries when they overlap with inferred entries, unless the inferred entry adds useful specificity.
A component may have multiple failure modes, and a failure mode may apply to multiple components.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Historical failure modes:
{historical_modes.model_dump_json(indent=2)}

Viewpoint failure modes:
{viewpoint_modes.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array, sorted by the failure modes affecting the most components first.
Each JSON object in the array should have the following fields:
- item_id: component ID such as C1
- item_function: component name/function
- failure_id: failure-mode ID such as HFM1
- failure_mode
- rationale
- source
- source_incident_ids
""",
        )

    @staticmethod
    def root_causes_and_local_effects(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        criticality: CriticalityRanking,
        failure_modes: FailureModeSet,
    ) -> str:
        return _prompt(
            "Root causes and local effects",
            f"""
Identify the root cause and local effect for each failure mode.
Preserve failure mode item_id, failure_id, and item_function values exactly.
Assign each entry.item_id to failure_mode.failure_id. Assign cause.item_id as "<failure_id>:CAUSE"
and effect.item_id as "<failure_id>:EFFECT".
Keep source fields as Grounded when supported by historical incident data and Inferred otherwise.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Failure modes:
{failure_modes.model_dump_json(indent=2)}

Return a JSON object with an "entries" array.
Each JSON object in entries must have exactly these fields: item_id, failure_mode, cause, effect, and assessment.
- failure_mode must have exactly: item_id, item_function, failure_id, failure_mode, rationale,
  source, and source_incident_ids.
- cause must have exactly: item_id, root_cause, rationale, and source.
- effect must have exactly: item_id, local_effect, rationale, and source.
- assessment must have exactly: item_id, severity, likelihood, severity_rationale,
  likelihood_rationale, severity_source, and likelihood_source.
""",
        )

    @staticmethod
    def severity_and_likelihood(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        criticality: CriticalityRanking,
        cause_effects: CauseEffectAnalysis,
    ) -> str:
        return _prompt(
            "Severity and likelihood",
            f"""
Assign severity and likelihood for each failure mode.
Preserve entry item_id and nested failure mode IDs exactly.
Assign assessment.item_id as "<failure_mode_id>:ASSESSMENT".

Severity ranking:
I - Catastrophic: may cause death or system loss.
II - Critical: may cause severe injury, major property damage, or major system damage.
III - Marginal: may cause minor injury, minor property damage, or minor system damage.
IV - Minor: not serious enough to cause injury or property damage, but may cause unscheduled maintenance.

Likelihood ranking:
I - Frequent: high probability during operation.
II - Reasonably probable: moderate probability during operation.
III - Occasional: low probability during operation.
IV - Remote: very low probability during operation.
V - Extremely unlikely: probability close to zero during operation.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Failure modes with causes and effects:
{cause_effects.model_dump_json(indent=2)}

Return a JSON object with an "entries" array.
Each JSON object in entries must have exactly these
fields: item_id, failure_mode, cause, effect, and assessment.
- failure_mode must have exactly: item_id, item_function, failure_id, failure_mode, rationale,
  source, and source_incident_ids.
- cause must have exactly: item_id, root_cause, rationale, and source.
- effect must have exactly: item_id, local_effect, rationale, and source.
- assessment must have exactly: item_id, severity, likelihood, severity_rationale,
  likelihood_rationale, severity_source, and likelihood_source.
""",
        )

    @staticmethod
    def preventive_and_corrective_actions(
        system_description: str,
        system_design: str,
        components: ComponentInventory,
        scored_modes: ScoredFailureModeSet,
    ) -> str:
        return _prompt(
            "Preventive measures and corrective actions",
            f"""
Identify preventive measures and corrective actions for each failure mode.
Preserve entry item_id and all nested IDs exactly.
Assign mitigation.item_id as "<failure_mode_id>:MITIGATION".
Preventive measures should reduce likelihood or severity before failure.
Corrective actions should reduce impact after failure has occurred.
RPN has already been calculated deterministically by Python. Preserve the rpn object exactly.

System description:
{system_description}

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Failure modes with severity, likelihood, and calculated RPN:
{scored_modes.model_dump_json(indent=2)}

Return a JSON object with an "entries" array.
Each JSON object in entries must have exactly these
fields: item_id, failure_mode, cause, effect, assessment, rpn, and mitigation.
- failure_mode must have exactly: item_id, item_function, failure_id, failure_mode, rationale,
  source, and source_incident_ids.
- cause must have exactly: item_id, root_cause, rationale, and source.
- effect must have exactly: item_id, local_effect, rationale, and source.
- assessment must have exactly: item_id, severity, likelihood, severity_rationale,
  likelihood_rationale, severity_source, and likelihood_source.
- rpn must have exactly: item_id, rpn, and rationale. Return rpn as a JSON integer.
- mitigation must have exactly: item_id, preventive_measures, and corrective_actions. Both
  preventive_measures and corrective_actions must each be one JSON string, never an array. Combine
  multiple actions into the single string using semicolons.
""",
        )

class RPNCalculator:
    severity_scores = {
        "I": 4,
        "II": 3,
        "III": 2,
        "IV": 1,
    }
    likelihood_scores = {
        "I": 5,
        "II": 4,
        "III": 3,
        "IV": 2,
        "V": 1,
    }

    def calculate(self, assessments: AssessmentSet) -> ScoredFailureModeSet:
        scored_modes = []
        for entry in assessments.entries:
            severity_score = self._score_from_label(entry.assessment.severity, self.severity_scores)
            likelihood_score = self._score_from_label(entry.assessment.likelihood, self.likelihood_scores)
            rpn = severity_score * likelihood_score
            scored_modes.append(
                ScoredFailureMode(
                    item_id=entry.item_id,
                    failure_mode=entry.failure_mode,
                    cause=entry.cause,
                    effect=entry.effect,
                    assessment=entry.assessment,
                    rpn=RPNScore(
                        item_id=f"{entry.item_id}:RPN",
                        rpn=rpn,
                        rationale=(
                            f" RPN: severity score {severity_score} "
                            f"x likelihood score {likelihood_score} = {rpn}."
                        ),
                    ),
                )
            )
        return ScoredFailureModeSet(entries=scored_modes)

    def _score_from_label(self, label: str, scores: dict[str, int]) -> int:
        normalized = str(label or "").strip().upper()
        for prefix in sorted(scores, key=len, reverse=True):
            if normalized == prefix or normalized.startswith(f"{prefix} ") or normalized.startswith(f"{prefix} -"):
                return scores[prefix]
        logging.warning("Unable to map SFMEA ranking label to score: %s", label)
        return 0


def calculate_rpn_scores(assessments: AssessmentSet) -> ScoredFailureModeSet:
    return RPNCalculator().calculate(assessments)

class DocumentAssembler:
    def assemble(
        self,
        components: ComponentInventory,
        mitigated_modes: MitigatedFailureModeSet,
        stage_outputs: dict,
    ) -> SFMEADocument:
        components_by_id = {component.item_id: component for component in components.components}
        rows = []
        for entry in mitigated_modes.entries:
            component = components_by_id.get(entry.failure_mode.item_id)
            rows.append(
                SFMEARow(
                    failure_id=entry.failure_mode.failure_id,
                    row_id=entry.failure_mode.item_id,
                    item_function=component.item_function if component else "",
                    failure_mode=entry.failure_mode.failure_mode,
                    failure_mode_rationale=entry.failure_mode.rationale,
                    root_cause=entry.cause.root_cause,
                    root_cause_rationale=entry.cause.rationale,
                    local_effect=entry.effect.local_effect,
                    local_effect_rationale=entry.effect.rationale,
                    preventive_measures=entry.mitigation.preventive_measures,
                    severity=entry.assessment.severity,
                    likelihood=entry.assessment.likelihood,
                    rpn=entry.rpn.rpn,
                    rpn_rationale=entry.rpn.rationale,
                    corrective_actions=entry.mitigation.corrective_actions,
                    failure_mode_source=entry.failure_mode.source,
                    source_incident_ids=entry.failure_mode.source_incident_ids,
                )
            )
        return SFMEADocument(
            rows=rows,
            stage_outputs=stage_outputs,
        )

class SFMEAPipeline:
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        prompt_factory: Optional[PromptFactory] = None,
        rpn_calculator: Optional[RPNCalculator] = None,
        document_assembler: Optional[DocumentAssembler] = None,
    ):
        self.llm_adapter = LLMAdapter(llm)
        self.prompt_factory = prompt_factory or PromptFactory()
        self.rpn_calculator = rpn_calculator or RPNCalculator()
        self.document_assembler = document_assembler or DocumentAssembler()

    async def generate(
        self,
        system_description: str,
        system_design: str,
        historical_incidents: Iterable[dict],
        progress_callback: Optional[ProgressCallback] = None,
    ) -> SFMEADocument:
        runner = StageRunner(self.llm_adapter, progress_callback)
        historical_data = json.dumps(list(historical_incidents), indent=2, default=str)

        components = await runner.run_llm_stage(
            SFMEAStage.COMPONENT_EXTRACTION,
            ComponentInventory,
            self.prompt_factory.component_extraction(system_description, system_design),
        )

        criticality_task = runner.run_llm_stage(
            SFMEAStage.CRITICALITY_RANKING,
            CriticalityRanking,
            self.prompt_factory.criticality_ranking(system_description, system_design, components),
        )
        historical_task = runner.run_llm_stage(
            SFMEAStage.HISTORICAL_FAILURE_MODE_MAPPING,
            FailureModeSet,
            self.prompt_factory.historical_failure_mode_mapping(
                system_description,
                system_design,
                components,
                historical_data,
            ),
        )
        criticality, historical_modes = await asyncio.gather(criticality_task, historical_task)

        viewpoint_modes = await runner.run_llm_stage(
            SFMEAStage.VIEWPOINT_IDEATION,
            FailureModeSet,
            self.prompt_factory.viewpoint_ideation(system_description, system_design, components, criticality),
        )
        failure_modes = await runner.run_llm_stage(
            SFMEAStage.FAILURE_MODE_EXPANSION,
            FailureModeSet,
            self.prompt_factory.failure_mode_expansion(
                system_description,
                system_design,
                components,
                criticality,
                historical_modes,
                viewpoint_modes,
            ),
        )
        cause_effects = await runner.run_llm_stage(
            SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS,
            CauseEffectAnalysis,
            self.prompt_factory.root_causes_and_local_effects(
                system_description,
                system_design,
                components,
                criticality,
                failure_modes,
            ),
        )
        assessments = await runner.run_llm_stage(
            SFMEAStage.SEVERITY_AND_LIKELIHOOD,
            AssessmentSet,
            self.prompt_factory.severity_and_likelihood(
                system_description,
                system_design,
                components,
                criticality,
                cause_effects,
            ),
        )

        await runner.report(SFMEAStage.RPN_CALCULATION)
        scored_modes = self.rpn_calculator.calculate(assessments)

        mitigated_modes = await runner.run_llm_stage(
            SFMEAStage.PREVENTIVE_AND_CORRECTIVE_ACTIONS,
            MitigatedFailureModeSet,
            self.prompt_factory.preventive_and_corrective_actions(
                system_description,
                system_design,
                components,
                scored_modes,
            ),
        )

        await runner.report(SFMEAStage.SFMEA_TABLE)
        return self.document_assembler.assemble(
            components=components,
            mitigated_modes=mitigated_modes,
            stage_outputs={
                SFMEAStage.COMPONENT_EXTRACTION.value: components.model_dump(),
                SFMEAStage.CRITICALITY_RANKING.value: criticality.model_dump(),
                SFMEAStage.HISTORICAL_FAILURE_MODE_MAPPING.value: historical_modes.model_dump(),
                SFMEAStage.VIEWPOINT_IDEATION.value: viewpoint_modes.model_dump(),
                SFMEAStage.FAILURE_MODE_EXPANSION.value: failure_modes.model_dump(),
                SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS.value: cause_effects.model_dump(),
                SFMEAStage.SEVERITY_AND_LIKELIHOOD.value: assessments.model_dump(),
                SFMEAStage.RPN_CALCULATION.value: scored_modes.model_dump(),
                SFMEAStage.PREVENTIVE_AND_CORRECTIVE_ACTIONS.value: mitigated_modes.model_dump(),
            },
        )


def _prompt(stage_name: str, task: str) -> str:
    return f"""
# Identity
You are an SFMEA facilitator called FailBot.

# Stage
{stage_name}

# Instructions
{task}

# Reasoning constraints
- Use only the supplied context.
- Do not fabricate details.
- Do not collapse ambiguity into a single answer.
- Surface missing or ambiguous information in rationale fields.
- Preserve all supplied item_id values exactly when carrying records forward.

# Output contract
Return only valid JSON matching the requested schema.
"""


def _markdown_table(headers: List[str], rows: List[List[str]]) -> str:
    rendered = [
        "| " + " | ".join(_clean_cell(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        rendered.append("| " + " | ".join(_clean_cell(cell) for cell in row) + " |")
    return "\n".join(rendered)


def _clean_cell(value: object) -> str:
    return str(value or "-").replace("\n", "<br>").replace("|", "\\|")