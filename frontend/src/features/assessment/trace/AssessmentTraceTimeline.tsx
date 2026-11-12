import {
  CheckCircle2,
  Circle,
  Eye,
  FileSearch,
  Loader2,
  Scale,
  ScrollText,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import { useMemo, useState } from "react";
import type { ClaimAssessmentResponse } from "../../../api/types/assessment";
import type { ClaimInput } from "../../../api/types/claim";
import { Badge } from "../../../components/ui/Badge";
import { OverviewSection } from "../OverviewSection";
import { NlpSection } from "../NlpSection";
import { TechnicalSection } from "../TechnicalSection";
import { LlmRecommendationSection } from "../LlmRecommendationSection";
import { FinancialValidationSection } from "../../financial/FinancialValidationSection";
import { EvidenceSection } from "../EvidenceSection";
import {
  AssessmentTextPreviewModal,
  type TextPreviewSection,
} from "./AssessmentTextPreviewModal";
import {
  buildPipelineSteps,
  deriveTraceStats,
  type AssessmentPipelineStep,
  type StepTone,
} from "./assessmentTraceModel";
import { recommendationLabel, recommendationTone, technicalStatusTone } from "../../../lib/statusLabels";

type TraceTab = "overview" | "context" | "nlp" | "evidence" | "pipeline" | "technical" | "decision";

const TABS: { id: TraceTab; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "context", label: "Claim context" },
  { id: "nlp", label: "NLP" },
  { id: "evidence", label: "Evidence" },
  { id: "pipeline", label: "Pipeline steps" },
  { id: "technical", label: "Technical" },
  { id: "decision", label: "Decision" },
];

function contentWidth(expanded: boolean, cap = "max-w-4xl") {
  return expanded ? "w-full" : `mx-auto w-full ${cap}`;
}

const stepNodeClass: Record<StepTone, string> = {
  ok: "border-status-ok bg-status-ok/15 text-status-ok",
  warn: "border-status-warn bg-status-warn/10 text-status-warn",
  err: "border-status-err bg-status-err/10 text-status-err",
  mute: "border-border bg-surface-raised text-text-faint",
  accent: "border-accent bg-accent-muted text-accent",
};

function PreviewButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="inline-flex items-center gap-1 rounded-md border border-border bg-surface px-2 py-1 text-[10px] font-medium text-text-muted hover:bg-surface-hover hover:text-text"
    >
      <Eye className="h-3 w-3" />
      Preview
    </button>
  );
}

function PipelineStepCard({
  step,
  index,
  expanded,
  onPreview,
}: {
  step: AssessmentPipelineStep;
  index: number;
  expanded: boolean;
  onPreview: (sections: TextPreviewSection[], title: string) => void;
}) {
  const nodeClass = step.isFinal
    ? "border-status-ok bg-status-ok/15 text-status-ok"
    : stepNodeClass[step.tone];

  return (
    <div className={`grid gap-3 ${expanded ? "grid-cols-[72px_minmax(0,1fr)]" : "grid-cols-[40px_minmax(0,1fr)]"}`}>
      <div className="flex flex-col items-center">
        <div
          className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold ${nodeClass}`}
        >
          {step.isFinal ? <CheckCircle2 className="h-4 w-4" /> : index + 1}
        </div>
        <div className="mt-1 w-px flex-1 bg-border" />
      </div>
      <div className="mb-4 rounded-lg border border-border bg-surface-raised/40 p-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h3 className="text-[13px] font-semibold text-text">{step.title}</h3>
          <div className="flex flex-wrap items-center gap-1.5">
            {step.pills.map((pill) => (
              <span
                key={pill}
                className="rounded bg-surface px-1.5 py-0.5 text-[10px] font-medium text-text-muted ring-1 ring-border"
              >
                {pill}
              </span>
            ))}
            <PreviewButton
              onClick={() =>
                onPreview(
                  [
                    { id: "summary", label: "Summary", content: step.summary },
                    ...(step.detail ? [{ id: "detail", label: "Detail", content: step.detail }] : []),
                  ],
                  step.title,
                )
              }
            />
          </div>
        </div>
        <p className="mt-2 text-[12px] leading-relaxed text-text-muted line-clamp-4">{step.summary}</p>
        {step.detail && step.id === "rag" ? (
          <p className="mt-2 rounded border border-emerald-500/20 bg-emerald-500/5 px-2 py-1.5 text-[11px] text-emerald-700 dark:text-emerald-300">
            {step.detail}
          </p>
        ) : null}
        {step.detail && step.id !== "rag" ? (
          <p className="mt-2 text-[11px] text-text-muted">{step.detail}</p>
        ) : null}
      </div>
    </div>
  );
}

function FlowDiagram({ steps }: { steps: AssessmentPipelineStep[] }) {
  return (
    <ol className="flex flex-wrap items-center gap-2">
      {steps.map((step, i) => (
        <li key={step.id} className="flex items-center gap-2">
          <span
            className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${
              step.isFinal ? "border-status-ok bg-status-ok/15 text-status-ok" : stepNodeClass[step.tone]
            }`}
          >
            {step.title.replace(" validation", "").replace(" extraction", "")}
          </span>
          {i < steps.length - 1 ? <span className="text-text-faint">→</span> : null}
        </li>
      ))}
    </ol>
  );
}

type PreviewState = { title: string; sections: TextPreviewSection[] } | null;

export function AssessmentTraceTimeline({
  claim,
  assessment,
  loading = false,
  expanded = false,
}: {
  claim: ClaimInput;
  assessment: ClaimAssessmentResponse | null;
  loading?: boolean;
  expanded?: boolean;
}) {
  const [tab, setTab] = useState<TraceTab>("overview");
  const [preview, setPreview] = useState<PreviewState>(null);

  const steps = useMemo(() => (assessment ? buildPipelineSteps(assessment) : []), [assessment]);
  const stats = useMemo(() => (assessment ? deriveTraceStats(assessment) : null), [assessment]);

  if (loading) {
    return (
      <div className={`flex flex-col items-center justify-center gap-3 py-20 ${contentWidth(expanded)}`}>
        <Loader2 className="h-8 w-8 animate-spin text-accent" aria-hidden />
        <p className="text-center text-[13px] text-text-muted">
          Running assessment pipeline—NLP, RAG, technical validation, and recommendation…
        </p>
      </div>
    );
  }

  if (!assessment) {
    return (
      <div className={`flex flex-col items-center gap-2 py-20 text-text-faint ${contentWidth(expanded)}`}>
        <Circle className="h-8 w-8" aria-hidden />
        <p className="text-[13px]">No assessment trace yet. Run assessment on the claim.</p>
      </div>
    );
  }

  const tv = assessment.technical_validation;
  const rec = assessment.recommendation;
  const llmSummary =
    assessment.llm_contextual_assessment?.assessment.summary ??
    rec.llm_advisory_summary ??
    rec.recommendation_reasons[0];

  return (
    <>
      <div className="sticky top-0 z-10 border-b border-border bg-surface/95 backdrop-blur">
        <div className={`flex gap-1 overflow-x-auto px-4 py-2 scrollbar-thin sm:px-6 ${expanded ? "lg:px-10" : ""}`}>
          {TABS.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`shrink-0 rounded-md px-3 py-1.5 text-[12px] font-medium transition ${
                tab === t.id ? "bg-accent-muted text-accent" : "text-text-muted hover:bg-surface-hover"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className={`space-y-4 py-4 ${expanded ? "px-6 lg:px-10 xl:px-12" : "px-4 sm:px-6"}`}>
        {tab === "overview" ? (
          <div className={contentWidth(expanded, "max-w-5xl")}>
            <div
              className={`mb-4 grid gap-3 ${expanded ? "sm:grid-cols-3 lg:grid-cols-6" : "sm:grid-cols-2 lg:grid-cols-3"}`}
            >
              {[
                { label: "Duration", value: `${stats?.durationMs.toLocaleString() ?? "—"} ms` },
                { label: "Passages", value: String(stats?.passageCount ?? 0) },
                { label: "Technical", value: stats?.technicalStatus ?? "—" },
                { label: "Financial", value: stats?.financialStatus ?? "—" },
                { label: "LLM", value: stats?.llmStatus ?? "—" },
                { label: "Assessment ID", value: stats?.assessmentId?.slice(0, 8) ?? "—" },
              ].map((item) => (
                <div key={item.label} className="rounded-lg border border-border bg-surface-raised/50 px-3 py-2">
                  <p className="text-[10px] font-semibold uppercase tracking-wide text-text-faint">{item.label}</p>
                  <p className="mt-1 text-[18px] font-semibold tabular-nums text-text">{item.value}</p>
                </div>
              ))}
            </div>

            <div className="mb-4 rounded-lg border border-border bg-surface-raised/30 p-3">
              <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-text-faint">Pipeline flow</p>
              <FlowDiagram steps={steps} />
            </div>

            <div className="rounded-lg border border-status-ok/30 bg-status-ok/5 p-4">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-status-ok" />
                <p className="text-[10px] font-semibold uppercase tracking-wide text-status-ok">Final recommendation</p>
                <Badge tone={recommendationTone(rec.overall_recommendation)}>
                  {recommendationLabel(rec.overall_recommendation)}
                </Badge>
              </div>
              <p className="text-[14px] leading-relaxed text-text">{llmSummary}</p>
              <p className="mt-2 text-[11px] text-text-faint">
                Advisory narrative shown for context. Technical status{" "}
                <Badge tone={technicalStatusTone(tv.technical_status)}>
                  {stats?.technicalStatus}
                </Badge>{" "}
                remains authoritative.
              </p>
            </div>
          </div>
        ) : null}

        {tab === "context" ? (
          <div className={contentWidth(expanded)}>
            <OverviewSection claim={claim} />
          </div>
        ) : null}

        {tab === "nlp" ? (
          <div className={contentWidth(expanded, "max-w-5xl")}>
            <NlpSection assessment={assessment} />
          </div>
        ) : null}

        {tab === "evidence" ? (
          <div className={contentWidth(expanded, "max-w-5xl")}>
            <div className="mb-3 flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <FileSearch className="h-4 w-4" />
              <p className="text-[11px] font-semibold uppercase tracking-wider">RAG evidence</p>
            </div>
            <EvidenceSection assessment={assessment} />
          </div>
        ) : null}

        {tab === "pipeline" ? (
          <div className={contentWidth(expanded, "max-w-4xl")}>
            <div className="mb-3 flex items-center gap-2">
              <ScrollText className="h-4 w-4 text-accent" />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">
                Pipeline steps ({steps.length})
              </p>
            </div>
            {steps.map((step, index) => (
              <PipelineStepCard
                key={step.id}
                step={step}
                index={index}
                expanded={expanded}
                onPreview={(sections, title) => setPreview({ title, sections })}
              />
            ))}
          </div>
        ) : null}

        {tab === "technical" ? (
          <div className={contentWidth(expanded, "max-w-5xl")}>
            <div className="mb-3 flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
              <ShieldCheck className="h-4 w-4" />
              <p className="text-[11px] font-semibold uppercase tracking-wider">Technical validation</p>
            </div>
            <TechnicalSection assessment={assessment} />
          </div>
        ) : null}

        {tab === "decision" ? (
          <div className={contentWidth(expanded, "max-w-5xl")}>
            <div className="mb-4 grid gap-3 lg:grid-cols-2">
              <div className="rounded-lg border border-violet-500/25 bg-violet-500/5 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-violet-400" />
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-violet-300">LLM execution</p>
                </div>
                <dl className="space-y-1 text-[12px] text-text-muted">
                  <div className="flex justify-between gap-2">
                    <dt>Status</dt>
                    <dd className="font-medium text-text">{assessment.llm_execution.status}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Model</dt>
                    <dd className="text-text">{assessment.llm_execution.actual_model ?? "—"}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Latency</dt>
                    <dd className="tabular-nums text-text">
                      {assessment.llm_execution.latency_ms != null
                        ? `${assessment.llm_execution.latency_ms} ms`
                        : "—"}
                    </dd>
                  </div>
                </dl>
              </div>
              <div className="rounded-lg border border-border bg-surface-raised/40 p-3">
                <div className="mb-2 flex items-center gap-2">
                  <Workflow className="h-4 w-4 text-accent" />
                  <p className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">Execution</p>
                </div>
                <dl className="space-y-1 text-[12px] text-text-muted">
                  <div className="flex justify-between gap-2">
                    <dt>RAG mode</dt>
                    <dd>{assessment.execution_metadata.rag_mode ?? "—"}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Generated</dt>
                    <dd>{assessment.execution_metadata.generated_at ?? "—"}</dd>
                  </div>
                  <div className="flex justify-between gap-2">
                    <dt>Duration</dt>
                    <dd className="tabular-nums">{assessment.execution_metadata.duration_ms} ms</dd>
                  </div>
                </dl>
              </div>
            </div>
            <div className="mb-4 flex items-center gap-2">
              <Scale className="h-4 w-4 text-brand" />
              <p className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">Financial & workflow</p>
            </div>
            <div className="space-y-4">
              <FinancialValidationSection
                claim={claim}
                financial={rec.financial_validation}
                assessmentStatus={String(rec.financial_assessment_status)}
              />
              <LlmRecommendationSection assessment={assessment} />
            </div>
          </div>
        ) : null}
      </div>

      <AssessmentTextPreviewModal
        open={preview != null}
        title={preview?.title ?? ""}
        sections={preview?.sections ?? []}
        onClose={() => setPreview(null)}
      />
    </>
  );
}
