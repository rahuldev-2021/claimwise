import { ArrowLeft } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { createClaim } from "../api/services";
import { ApiError } from "../api/client";
import { Button } from "../components/ui/Button";
import {
  EMPTY_NEW_CLAIM,
  generateRepairOrder,
  type NewClaimFormData,
} from "../data/sampleNewClaim";
import {
  EVALUATION_SCENARIOS,
  getEvaluationScenario,
  type EvaluationScenarioId,
} from "../data/evaluationClaimScenarios";

const fieldClass = "ui-input mt-0.5 w-full py-1.5";

function Field({
  label,
  required,
  children,
  className = "",
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <label className={`block ${className}`}>
      <span className="text-[11px] font-medium text-text-faint">
        {label}
        {required ? <span className="text-status-err"> *</span> : null}
      </span>
      {children}
    </label>
  );
}

export function ClaimSubmitPage() {
  const [searchParams] = useSearchParams();
  const scenarioParam = searchParams.get("scenario");
  const [activeScenario, setActiveScenario] = useState<EvaluationScenarioId | null>(null);
  const [form, setForm] = useState<NewClaimFormData>(() => ({
    ...EMPTY_NEW_CLAIM,
    repair_order: generateRepairOrder(),
  }));
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [files, setFiles] = useState<File[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const applyScenario = (id: EvaluationScenarioId | "") => {
    if (!id) {
      setActiveScenario(null);
      setForm({
        ...EMPTY_NEW_CLAIM,
        repair_order: generateRepairOrder(),
      });
      setSubmitError(null);
      return;
    }
    const scenario = getEvaluationScenario(id);
    if (!scenario) return;
    setActiveScenario(id);
    setForm({
      ...scenario.form,
      repair_order: generateRepairOrder(),
    });
    setSubmitError(null);
  };

  useEffect(() => {
    const fromUrl = getEvaluationScenario(scenarioParam);
    if (fromUrl) {
      applyScenario(fromUrl.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- load once from URL
  }, [scenarioParam]);

  const submitMutation = useMutation({
    mutationFn: () =>
      createClaim(
        {
          repair_order: form.repair_order,
          vin: form.vin.trim() || null,
          year: form.year,
          make: form.make,
          model: form.model,
          category: form.category,
          customer_complaint: form.complaint,
          technician_diagnosis: form.technician_diagnosis,
          recommended_repair: form.repair,
          parts_cost: form.parts_cost,
          labour_hours: form.labour_hours,
          currency: "USD",
          mileage: form.mileage.trim() || undefined,
          engine_type: form.engine_type.trim() || undefined,
        },
        files,
      ),
    onSuccess: (claim) => {
      void qc.invalidateQueries({ queryKey: ["claims"] });
      navigate(`/claims/${claim.claim_id}`, { state: { autoAssess: true } });
    },
    onError: (err: unknown) => {
      const message = err instanceof ApiError ? err.message : "Submit failed";
      setSubmitError(message);
    },
  });

  const set =
    (key: keyof NewClaimFormData) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
      setForm((prev) => ({ ...prev, [key]: e.target.value }));
      setSubmitError(null);
      setActiveScenario(null);
    };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    submitMutation.mutate();
  };

  return (
    <div className="w-full space-y-4">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
        <div className="min-w-0">
          <h1 className="text-[18px] font-semibold tracking-tight text-text">New claim</h1>
          <p className="text-[12px] text-text-muted">
            We assign a reference number — you enter the vehicle, what the customer reported, and what you repaired.
          </p>
        </div>
        <Link
          to="/"
          className="inline-flex items-center gap-1 text-[12px] font-medium text-text-muted transition hover:text-text"
        >
          <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.75} />
          Home
        </Link>
      </header>

      {submitError ? (
        <p className="rounded-lg border border-status-err/40 bg-status-err/10 px-3 py-2 text-[12px] text-text">
          {submitError}
        </p>
      ) : null}
      <form
        className="rounded-xl border border-border bg-surface shadow-composer"
        onSubmit={onSubmit}
      >
        <div className="grid gap-4 p-4 lg:grid-cols-2 lg:gap-x-6 lg:p-5">
          <section className="space-y-3">
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">
              Claim & vehicle
            </h2>
            <Field label="Claim Request">
              <select
                className={fieldClass}
                value={activeScenario ?? ""}
                onChange={(e) => applyScenario(e.target.value as EvaluationScenarioId | "")}
              >
                <option value="">Custom claim</option>
                {EVALUATION_SCENARIOS.map((scenario) => (
                  <option key={scenario.id} value={scenario.id}>
                    {scenario.title}
                  </option>
                ))}
              </select>
            </Field>
            <div className="block">
              <span className="text-[11px] font-medium text-text-faint">Repair order</span>
              <p
                className="ui-input mt-0.5 w-full cursor-default border-dashed bg-base-deep/50 py-1.5 font-mono text-[13px] text-text"
                aria-readonly
              >
                {form.repair_order}
              </p>
              <p className="mt-0.5 text-[10px] text-text-faint">
                Auto-generated reference (your DMS RO can be linked when integrations are enabled).
              </p>
            </div>
            <Field label="VIN">
              <input
                className={fieldClass}
                name="vin"
                value={form.vin}
                onChange={set("vin")}
                placeholder="Optional — 17-character VIN"
                maxLength={17}
              />
            </Field>
            <div className="grid grid-cols-3 gap-2">
              <Field label="Year" required>
                <input
                  className={fieldClass}
                  name="year"
                  required
                  inputMode="numeric"
                  value={form.year}
                  onChange={set("year")}
                  placeholder="2024"
                />
              </Field>
              <Field label="Make" required>
                <input
                  className={fieldClass}
                  name="make"
                  required
                  value={form.make}
                  onChange={set("make")}
                  placeholder="Ford"
                />
              </Field>
              <Field label="Model" required>
                <input
                  className={fieldClass}
                  name="model"
                  required
                  value={form.model}
                  onChange={set("model")}
                  placeholder="F-150"
                />
              </Field>
            </div>
            <Field label="Repair category" required>
              <select
                className={fieldClass}
                name="category"
                required
                value={form.category}
                onChange={set("category")}
              >
                <option value="ENGINE">Engine</option>
                <option value="TRANSMISSION">Transmission</option>
                <option value="BRAKING">Braking</option>
                <option value="ELECTRICAL">Electrical</option>
                <option value="OTHER">Other</option>
              </select>
            </Field>
            <div className="grid gap-3 sm:grid-cols-2">
              <Field label="Parts cost (USD)" required>
                <input
                  className={fieldClass}
                  name="parts_cost"
                  required
                  inputMode="decimal"
                  value={form.parts_cost}
                  onChange={set("parts_cost")}
                  placeholder="0.00"
                />
              </Field>
              <Field label="Labour hours (hr)" required>
                <input
                  className={fieldClass}
                  name="labour_hours"
                  required
                  inputMode="decimal"
                  value={form.labour_hours}
                  onChange={set("labour_hours")}
                  placeholder="0"
                />
              </Field>
            </div>
          </section>

          <section className="flex min-h-0 flex-col gap-3">
            <h2 className="text-[11px] font-semibold uppercase tracking-wider text-text-faint">
              Complaint & repair
            </h2>
            <Field label="Customer complaint" required className="flex min-h-0 flex-col">
              <textarea
                className={`${fieldClass} min-h-[72px] resize-y sm:min-h-[88px]`}
                name="complaint"
                required
                rows={3}
                value={form.complaint}
                onChange={set("complaint")}
                placeholder="What the customer reported…"
              />
            </Field>
            <Field label="Technician diagnosis" required className="flex min-h-0 flex-col">
              <textarea
                className={`${fieldClass} min-h-[72px] resize-y sm:min-h-[88px]`}
                name="technician_diagnosis"
                required
                rows={3}
                value={form.technician_diagnosis}
                onChange={set("technician_diagnosis")}
                placeholder="Your findings from inspection / road test (not the customer complaint)…"
              />
            </Field>
            <Field label="Recommended repair" required>
              <textarea
                className={`${fieldClass} min-h-[64px] resize-y`}
                name="repair"
                required
                rows={2}
                value={form.repair}
                onChange={set("repair")}
                placeholder="Claim repair requested…"
              />
            </Field>
            <Field label="Documents (optional)">
              <input
                type="file"
                multiple
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
                className="mt-0.5 block w-full text-[11px] text-text-muted file:mr-2 file:rounded-md file:border-0 file:bg-surface-hover file:px-2.5 file:py-1.5 file:text-[11px] file:text-text"
              />
            </Field>
          </section>
        </div>

        <div className="flex flex-wrap items-center justify-end gap-2 border-t border-border bg-base-deep/30 px-4 py-2.5">
          <Link to="/claims">
            <Button type="button" variant="secondary" className="py-1.5">
              Cancel
            </Button>
          </Link>
          <Button type="submit" className="py-1.5" disabled={submitMutation.isPending}>
            {submitMutation.isPending ? "Submitting…" : "Submit claim"}
          </Button>
        </div>
      </form>
    </div>
  );
}
