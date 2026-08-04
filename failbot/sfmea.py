import json 
import logging 
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
    description: str = Field(description="Component name or short description.")
    function: str = Field(default="", description="Known function of the component.")
    assumptions_or_gaps: List[str] = Field(default_factory=list)

class ComponentList(BaseModel):
    components: List[Component]

class CriticalComponent(Component):
    safety_criticality: str
    mission_criticality: str
    criticality_rationale: str

class CriticalityRanking(BaseModel):
    components: List[CriticalComponent]

class FailureModeSeed(BaseModel):
    component: str
    failure_mode: str
    rationale: str
    source: str = Field(description="Grounded or Inferred.")
    source_incident_ids: List[int] = Field(default_factory=list)

class FailureModeSeeds(BaseModel):
    failure_modes: List[FailureModeSeed]

class FailureModeCandidate(FailureModeSeed):
    sfmea_viewpoint: str = Field(
        description="Functional, Interface, Detailed, Maintenance, Usability, Serviceability, Vulnerability, or Software production process."
    )
    safety_criticality: str
    mission_criticality: str

class FailureModeCandidates(BaseModel):
    failure_modes: List[FailureModeCandidate]

class ExpandedFailureMode(FailureModeCandidate):
    expanded_failure_mode: str

class ExpandedFailureModes(BaseModel):
    failure_modes: List[ExpandedFailureMode]

class CauseEffectFailureMode(ExpandedFailureMode):
    root_cause: str
    root_cause_rationale: str
    root_cause_source: str
    local_effect: str
    local_effect_rationale: str
    local_effect_source: str

class CauseEffectFailureModes(BaseModel):
    failure_modes: List[CauseEffectFailureMode]

class SeverityLikelihoodFailureMode(CauseEffectFailureMode):
    severity: str
    likelihood: str
    severity_rationale: str
    likelihood_rationale: str
    severity_source: str
    likelihood_source: str

class SeverityLikelihoodFailureModes(BaseModel):
    failure_modes: List[SeverityLikelihoodFailureMode]

class ScoredFailureMode(SeverityLikelihoodFailureMode):
    rpn: int
    rpn_rationale: str

class ScoredFailureModes(BaseModel):
    failure_modes: List[ScoredFailureMode]

class MitigatedFailureMode(ScoredFailureMode):
    preventive_measures: str
    corrective_actions: str

class MitigatedFailureModes(BaseModel):
    failure_modes: List[MitigatedFailureMode]

class SFMEARow(BaseModel):
    item_function: str
    component: str
    failure_mode: str
    root_cause: str
    local_effect: str
    preventive_measures: str
    severity: str
    likelihood: str
    rpn: int
    rpn_rationale: str
    corrective_actions: str
    failure_mode_source: str
    source_incident_ids: List[int] = Field(default_factory=list)

class SFMEADocument:
        source_incident_ids: List[int] = Field(default_factory=list)

class FailureModeSeeds(BaseModel):
    failure_modes: List[FailureModeSeed]

class FailureModeCandidate(FailureModeSeed):
    sfmea_viewpoint: str = Field(
        description="Functional, Interface, Detailed, Maintenance, Usability, Serviceability, Vulnerability, or Software production process."
    )
    safety_criticality: str
    mission_criticality: str

class FailureModeCandidates(BaseModel):
    failure_modes: List[FailureModeCandidate]

class ExpandedFailureMode(FailureModeCandidate):
    expanded_failure_mode: str

class ExpandedFailureModes(BaseModel):
    failure_modes: List[ExpandedFailureMode]

class CauseEffectFailureMode(ExpandedFailureMode):
    root_cause: str
    root_cause_rationale: str
    root_cause_source: str
    local_effect: str
    local_effect_rationale: str
    local_effect_source: str

class CauseEffectFailureModes(BaseModel):
    failure_modes: List[CauseEffectFailureMode]

class SeverityLikelihoodFailureMode(CauseEffectFailureMode):
    severity: str
    likelihood: str
    severity_rationale: str
    likelihood_rationale: str
    severity_source: str
    likelihood_source: str

class SeverityLikelihoodFailureModes(BaseModel):
    failure_modes: List[SeverityLikelihoodFailureMode]

class ScoredFailureMode(SeverityLikelihoodFailureMode):
    rpn: int
    rpn_rationale: str

class ScoredFailureModes(BaseModel):
    failure_modes: List[ScoredFailureMode]

class MitigatedFailureMode(ScoredFailureMode):
    preventive_measures: str
    corrective_actions: str

class MitigatedFailureModes(BaseModel):
    failure_modes: List[MitigatedFailureMode]

class SFMEARow(BaseModel):
    item_function: str
    component: str
    failure_mode: str
    root_cause: str
    local_effect: str
    preventive_measures: str
    severity: str
    likelihood: str
    rpn: int
    rpn_rationale: str
    corrective_actions: str
    failure_mode_source: str
    source_incident_ids: List[int] = Field(default_factory=list)

class SFMEADocument(BaseModel):
    system_description: str
    system_design: str
    rows: List[SFMEARow]
    stage_outputs: dict = Field(default_factory=dict)

    def to_markdown(self) -> str:
        headers = [
            "Item/Function",
            "Component",
            "Failure Mode",
            "Root Cause",
            "Local Effect",
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
                row.item_function,
                row.component,
                row.failure_mode,
                row.root_cause,
                row.local_effect,
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


class SFMEATable(BaseModel):
    rows: List[SFMEARow]


class SFMEAPipeline:
    def __init__(self, llm):
        self.llm = llm
        
    async def generate(self,
    system_description:str,
    system_design: str, 
    historical_incidents:Iterable[dict], 
    progress_callback: Optional[ProgressCallback] = None,
    ) -> SFMEADocument:
    historical_data = json.dumps(list(historical_incidents), indent=2, default=str)

    components = await self._run_stage(
        SFMEAStage.COMPONENT_EXTRACTION,
        ComponentList,
        _component_extraction_prompt(system_description, system_design),
        progress_callback,
    )

    criticality = await self._run_stage(
        SFMEAStage.CRITICALITY_RANKING,
        CriticalityRanking,
        _criticality_prompt(components),
        progress_callback,
    )

    historical_modes = await self._run_stage(
        SFMEAStage.HISTORICAL_FAILURE_MODE_MAPPING,
        FailureModeSeeds,
        _historical_failure_mode_prompt(system_design, components, historical_data),
        progress_callback,
    )

    viewpoint_modes = await self._run_stage(
        SFMEAStage.VIEWPOINT_IDEATION,
        FailureModeCandidates,
        _viewpoint_ideation_prompt(criticality),
        progress_callback,
    )

    expanded_modes = await self._run_stage(
        SFMEAStage.FAILURE_MODE_EXPANSION,
        ExpandedFailureModes,
        _failure_mode_expansion_prompt(criticality, historical_modes, viewpoint_modes),
        progress_callback,
    )

    cause_effect_modes = await self._run_stage(
        SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS,
        CauseEffectFailureModes,
        _cause_effect_prompt(expanded_modes),
        progress_callback,
    )

    severity_likelihood = await self._run_stage(
        SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS,
        SeverityLikelihoodFailureModes,
        _severity_likelihood_prompt(cause_effect_modes),
        progress_callback,
    )


    scored_modes = await self._calculate_rpn(severity_likelihood, progress_callback)

    mitigated_modes = await self._run_stage(
        SFMEAStage.PREVENTIVE_AND_CORRECTIVE_ACTIONS,
        MitigatedFailureModes,
        _mitigation_prompt(scored_modes),
        progress_callback,
    )

    table = await self._run_stage(
        SFMEAStage.SFMEA_TABLE,
        SFMEATable,
        _sfmea_table_prompt(system_description, system_design, mitigated_modes),
        progress_callback,
    )

    table = _apply_calculated_rpn(table, mitigated_modes)

    return SFMEADocument(
        system_description=system_description,
        system_design=system_design,
        rows = table.rows,
        stage_output = {
            SFMEAStage.COMPONENT_EXTRACTION.value: components.model_dump(),
            SFMEAStage.CRITICALITY_RANKING.value: criticality.model_dump(),
            SFMEAStage.HISTORICAL_FAILURE_MODE_MAPPING.value: historical_modes.model_dump(),
            SFMEAStage.VIEWPOINT_IDEATION.value: viewpoint_modes.model_dump(),
            SFMEAStage.FAILURE_MODE_EXPANSION.value: expanded_modes.model_dump(),
            SFMEAStage.ROOT_CAUSES_AND_LOCAL_EFFECTS.value: cause_effect_modes.model_dump(),
            SFMEAStage.SEVERITY_AND_LIKELIHOOD.value: severity_likelihood.model_dump(),
            SFMEAStage.RPN_CALCULATION.value: scored_modes.model_dump(),
            SFMEAStage.PREVENTIVE_AND_CORRECTIVE_ACTIONS.value: mitigated_modes.model_dump(),

        },
    )

    async def _run_stage(self, stage: SFMEAStage, output_model: type[BaseModel], prompt, progress_callback:Optional[ProgressCallback]) -> BaseModal:
        if progress_callback:
            await progress_callback(stage.value)
        logging.info("Running SFMEA stage: %s", stage.value)
        structured_llm = self.llm.with_structured_output(output_model, method="json_mode")
        return await structured_llm.ainvoke(prompt)

    async def _calculate_rpn_stage(self, severity_likelihood: SeverityLikelihoodFailureModes, progress_callback:Optional[ProgressCallback]) -> ScoredFailureModes:
        if progress_callback:
            await progress_callback(SFMEAStage.RPN_CALCULATION.value)
        logging.info("Running SFMEA stage: %s", SFMEAStage.RPN_CALCULATION.value)
        return calculate_rpn_scores(severity_likelihood)

def _component_extraction_prompt(system_description: str, system_design: str) -> str:
    return _prompt(
        "Component extraction",
        f"""
Extract a listing of software-relevant system components from the high-level system design.
Use the original system description only as background.

Original system description:
{system_description}

High-level system design:
{system_design}

Return a JSON object with a "components" array. Do not fabricate missing parts. If a component's function is unclear,
include the uncertainty in "assumptions_or_gaps".
""",
    )


def _criticality_prompt(components: ComponentList) -> str:
    return _prompt(
        "Criticality ranking",
        f"""
Rank each component for safety and mission criticality.

Safety criticality labels:
1 - safety critical; 2 - safety related; 3 - not related to safety.

Mission criticality labels:
1 - mission critical; 2 - mission degraded; 3 - not mission critical.

Components:
{components.model_dump_json(indent=2)}

Return a JSON object with a "components" array.
""",
    )


def _historical_failure_mode_prompt(system_design: str, components: ComponentList, historical_data: str) -> str:
    return _prompt(
        "Historical failure mode mapping",
        f"""
Map past incident knowledge to likely failure mode categories for the listed components.
Only use historical incidents when they are relevant. If no historical evidence applies, return an empty "failure_modes" array.

Failure mode categories:
Faulty functionality, Faulty interface, Faulty Sequence, Faulty Data, Faulty Error Detection, False Alarm,
Incompatibility, Faulty Synchronization, Faulty Algorithm, Memory Management, Misuse, Abuse, Faulty Installation.

High-level system design:
{system_design}

Components:
{components.model_dump_json(indent=2)}

Historical incidents:
{historical_data}

Return a JSON object with a "failure_modes" array. Use source="Grounded" for incident-derived modes and include source_incident_ids.
""",
    )

def _viewpoint_ideation_prompt(criticality: CriticalityRanking) -> str:
    return _prompt(
        "Failure mode viewpoint ideation",
        f"""
Use SFMEA viewpoints to identify potential failure modes for each component.

SFMEA viewpoints:
Functional, Interface, Detailed, Maintenance, Usability, Serviceability, Vulnerability, Software production process.

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array. Use source="Inferred" unless directly grounded in the given ranking.
""",
    )


def _failure_mode_expansion_prompt(
    criticality: CriticalityRanking,
    historical_modes: FailureModeSeeds,
    viewpoint_modes: FailureModeCandidates,
) -> str:
    return _prompt(
        "Failure mode expansion",
        f"""
Combine historical and viewpoint-ideated failure modes into a comprehensive list.
Preserve historical entries when they overlap with inferred entries, unless the inferred entry adds useful specificity.
A component may have multiple failure modes, and a failure mode may apply to multiple components.

Criticality ranking:
{criticality.model_dump_json(indent=2)}

Historical failure modes:
{historical_modes.model_dump_json(indent=2)}

Viewpoint failure modes:
{viewpoint_modes.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array, sorted by the failure modes affecting the most components first.
""",
    )

def _cause_effect_prompt(expanded_modes: ExpandedFailureModes) -> str:
    return _prompt(
        "Root causes and local effects",
        f"""
Identify the root cause and local effect for each expanded failure mode.
Keep source fields as Grounded when supported by historical incident data and Inferred otherwise.

Expanded failure modes:
{expanded_modes.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array.
""",
    )


def _severity_likelihood_prompt(cause_effect_modes: CauseEffectFailureModes) -> str:
    return _prompt(
        "Severity and likelihood",
        f"""
Assign severity and likelihood for each failure mode.

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

Failure modes with causes and effects:
{cause_effect_modes.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array.
""",
    )


def calculate_rpn_scores(severity_likelihood: SeverityLikelihoodFailureModes) -> ScoredFailureModes:
    scored_modes = []
    for failure_mode in severity_likelihood.failure_modes:
        severity_score = _score_from_label(
            failure_mode.severity,
            {
                "I": 4,
                "II": 3,
                "III": 2,
                "IV": 1,
            },
        )
        likelihood_score = _score_from_label(
            failure_mode.likelihood,
            {
                "I": 5,
                "II": 4,
                "III": 3,
                "IV": 2,
                "V": 1,
            },
        )
        rpn = severity_score * likelihood_score
        rpn_rationale = (
            f"Python-calculated RPN: severity score {severity_score} "
            f"x likelihood score {likelihood_score} = {rpn}."
        )
        scored_modes.append(
            ScoredFailureMode(
                **failure_mode.model_dump(),
                rpn=rpn,
                rpn_rationale=rpn_rationale,
            )
        )
    return ScoredFailureModes(failure_modes=scored_modes)


def _score_from_label(label: str, scores: dict[str, int]) -> int:
    normalized = str(label or "").strip().upper()
    for prefix in sorted(scores, key=len, reverse=True):
        if normalized == prefix or normalized.startswith(f"{prefix} ") or normalized.startswith(f"{prefix} -"):
            return scores[prefix]
    logging.warning("Unable to map SFMEA ranking label to score: %s", label)
    return 0


def _mitigation_prompt(scored_modes: ScoredFailureModes) -> str:
    return _prompt(
        "Preventive measures and corrective actions",
        f"""
Identify preventive measures and corrective actions for each failure mode.
Preventive measures should reduce likelihood or severity before failure.
Corrective actions should reduce impact after failure has occurred.
RPN has already been calculated deterministically by Python. Preserve the rpn and rpn_rationale fields exactly.

Failure modes with severity, likelihood, and calculated RPN:
{scored_modes.model_dump_json(indent=2)}

Return a JSON object with a "failure_modes" array.
""",
    )


def _sfmea_table_prompt(system_description: str, system_design: str, mitigated_modes: MitigatedFailureModes) -> str:
    return _prompt(
        "SFMEA table",
        f"""
Generate the final Software FMEA table from the staged analysis.
RPN has already been calculated deterministically by Python. Copy the supplied rpn and rpn_rationale values exactly.
Do not recalculate, reinterpret, or replace RPN values.

System description:
{system_description}

High-level system design:
{system_design}

Mitigated failure modes:
{mitigated_modes.model_dump_json(indent=2)}

Return a JSON object with a "rows" array.
""",
    )

def _apply_calculated_rpn(table: SFMEATable, mitigated_modes: MitigatedFailureModes) -> SFMEATable:
    scored_by_key = {}
    for failure_mode in mitigated_modes.failure_modes:
        for failure_mode_name in {failure_mode.failure_mode, failure_mode.expanded_failure_mode}:
            scored_by_key[_failure_mode_key(failure_mode.component, failure_mode_name)] = failure_mode

    rows = []
    for index, row in enumerate(table.rows):
        scored_mode = scored_by_key.get(_failure_mode_key(row.component, row.failure_mode))
        if scored_mode is None and index < len(mitigated_modes.failure_modes):
            scored_mode = mitigated_modes.failure_modes[index]
        if scored_mode is None:
            rows.append(row)
            continue
        rows.append(
            row.model_copy(
                update={
                    "rpn": scored_mode.rpn,
                    "rpn_rationale": scored_mode.rpn_rationale,
                }
            )
        )
    return SFMEATable(rows=rows)


def _failure_mode_key(component: str, failure_mode: str) -> tuple[str, str]:
    return (_normalize_key(component), _normalize_key(failure_mode))


def _normalize_key(value: str) -> str:
    return " ".join(str(value or "").lower().split())


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