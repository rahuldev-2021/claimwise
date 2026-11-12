import type { ClaimAssessmentResponse } from "../api/types/assessment";
import type { ClaimInput } from "../api/types/claim";
import {
  buildPipelineSteps,
  deriveTraceStats,
} from "../features/assessment/trace/assessmentTraceModel";
import { recommendationLabel, technicalStatusLabel } from "./statusLabels";

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatMoney(value: string | number | undefined): string {
  if (value === undefined || value === "") return "—";
  const n = typeof value === "number" ? value : Number(value);
  if (Number.isNaN(n)) return String(value);
  return `$${n.toFixed(2)}`;
}

function formatGeneratedAt(iso?: string): string {
  if (!iso) return new Date().toLocaleString();
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString();
}

export function buildAssessmentReportHtml(
  claim: ClaimInput,
  assessment: ClaimAssessmentResponse,
): string {
  const stats = deriveTraceStats(assessment);
  const steps = buildPipelineSteps(assessment);
  const rec = assessment.recommendation;
  const tv = assessment.technical_validation;
  const fin = rec.financial_validation;
  const vehicle = claim.vehicle;

  const stepRows = steps
    .map(
      (s, i) => `
    <tr>
      <td>${i + 1}</td>
      <td><strong>${escapeHtml(s.title)}</strong></td>
      <td>${escapeHtml(s.pills.join(", ") || "—")}</td>
      <td>${escapeHtml(s.summary)}</td>
    </tr>
    ${s.detail ? `<tr><td></td><td colspan="3" class="detail">${escapeHtml(s.detail)}</td></tr>` : ""}`,
    )
    .join("");

  const reasons = rec.recommendation_reasons
    .map((r) => `<li>${escapeHtml(r)}</li>`)
    .join("");

  const rules = rec.triggered_business_rules.map((r) => escapeHtml(r)).join(", ") || "—";

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>CLAIMWISE Assessment — ${escapeHtml(claim.claim_id)}</title>
  <style>
    body { font-family: Calibri, Arial, sans-serif; font-size: 11pt; color: #111; line-height: 1.45; margin: 24px 32px; }
    h1 { font-size: 18pt; margin: 0 0 4px; color: #0f172a; }
    h2 { font-size: 13pt; margin: 20px 0 8px; border-bottom: 1px solid #cbd5e1; padding-bottom: 4px; }
    .meta { color: #475569; font-size: 10pt; margin-bottom: 16px; }
    table { width: 100%; border-collapse: collapse; margin: 8px 0 16px; }
    th, td { border: 1px solid #cbd5e1; padding: 6px 8px; vertical-align: top; text-align: left; }
    th { background: #f1f5f9; font-weight: 600; }
    td.detail { font-size: 10pt; color: #334155; background: #f8fafc; }
    dl { display: grid; grid-template-columns: 140px 1fr; gap: 4px 12px; margin: 0; }
    dt { font-weight: 600; color: #475569; }
    dd { margin: 0; }
    ul { margin: 6px 0; padding-left: 20px; }
    .footer { margin-top: 28px; font-size: 9pt; color: #64748b; border-top: 1px solid #e2e8f0; padding-top: 10px; }
    @media print {
      body { margin: 12mm; }
      h2 { page-break-after: avoid; }
      tr { page-break-inside: avoid; }
    }
  </style>
</head>
<body>
  <h1>CLAIMWISE — Assessment report</h1>
  <p class="meta">
    Claim ${escapeHtml(claim.claim_id)} · Assessment ${escapeHtml(stats.assessmentId)} ·
    Generated ${escapeHtml(formatGeneratedAt(stats.generatedAt))} ·
    Duration ${Math.round(stats.durationMs)} ms
  </p>

  <h2>Claim summary</h2>
  <dl>
    <dt>Vehicle</dt><dd>${escapeHtml(String(vehicle.model_year))} ${escapeHtml(vehicle.make)} ${escapeHtml(vehicle.model)}</dd>
    <dt>VIN</dt><dd>${escapeHtml(vehicle.vin ?? "—")}</dd>
    <dt>Repair category</dt><dd>${escapeHtml(claim.recommended_repair.repair_category)}</dd>
    <dt>Parts / labour</dt><dd>${formatMoney(claim.submitted_parts_cost)} / ${escapeHtml(String(claim.submitted_labour_hours))} h</dd>
    <dt>Complaint</dt><dd>${escapeHtml(claim.customer_complaint)}</dd>
    <dt>Diagnosis</dt><dd>${escapeHtml(claim.technician_diagnosis)}</dd>
    <dt>Recommended repair</dt><dd>${escapeHtml(claim.recommended_repair.recommended_action)}</dd>
  </dl>

  <h2>Overall recommendation</h2>
  <p><strong>${escapeHtml(recommendationLabel(rec.overall_recommendation))}</strong>
    ${rec.human_review_required ? " (human review required)" : ""}</p>
  <p>Technical: ${escapeHtml(technicalStatusLabel(tv.technical_status))} ·
     Financial: ${escapeHtml(stats.financialStatus)} · LLM: ${escapeHtml(stats.llmStatus)}</p>
  ${fin ? `<p>Financial model status: ${escapeHtml(fin.financial_status)} — ${escapeHtml(fin.explanation ?? "")}</p>` : ""}
  <p><strong>Reasons</strong></p>
  <ul>${reasons || "<li>—</li>"}</ul>
  <p><strong>Triggered business rules:</strong> ${rules}</p>

  <h2>Pipeline steps</h2>
  <table>
    <thead>
      <tr><th>#</th><th>Step</th><th>Status</th><th>Summary</th></tr>
    </thead>
    <tbody>${stepRows}</tbody>
  </table>

  ${assessment.llm_contextual_assessment?.assessment.summary ? `<h2>LLM advisory summary</h2><p>${escapeHtml(assessment.llm_contextual_assessment.assessment.summary)}</p>` : ""}

  <p class="footer">
    Advisory output only — not an approval or rejection. Reviewer decision required.
    CLAIMWISE assessment export.
  </p>
</body>
</html>`;
}

function sanitizeFilename(claimId: string): string {
  return claimId.replace(/[^\w.-]+/g, "_");
}

export function downloadAssessmentReportDoc(claim: ClaimInput, assessment: ClaimAssessmentResponse): void {
  const html = buildAssessmentReportHtml(claim, assessment);
  const blob = new Blob(["\ufeff", html], {
    type: "application/msword;charset=utf-8",
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `CLAIMWISE-${sanitizeFilename(claim.claim_id)}-assessment.doc`;
  a.click();
  URL.revokeObjectURL(url);
}

/** Opens print dialog; user can choose &quot;Save as PDF&quot;. */
export function printAssessmentReportPdf(claim: ClaimInput, assessment: ClaimAssessmentResponse): void {
  const html = buildAssessmentReportHtml(claim, assessment);
  const win = window.open("", "_blank", "noopener,noreferrer");
  if (!win) {
    window.alert("Allow pop-ups to export PDF, or use Download Word (.doc) instead.");
    return;
  }
  win.document.open();
  win.document.write(html);
  win.document.close();
  win.focus();
  const trigger = () => {
    win.print();
  };
  if (win.document.readyState === "complete") {
    setTimeout(trigger, 250);
  } else {
    win.addEventListener("load", () => setTimeout(trigger, 250));
  }
}
