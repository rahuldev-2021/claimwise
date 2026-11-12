import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Clock,
  Coins,
  FolderOpen,
  Plus,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { ErrorState, LoadingState } from "../components/ui/StateMessage";
import {
  SubmitClaimIllustration,
  TrackClaimsIllustration,
} from "../features/dealer/DealerActionIllustrations";
import { useDealerClaimStats } from "../hooks/useDealerClaimStats";
import { roleLabel, primaryRole } from "../lib/roles";

const HELP_CARDS = [
  {
    title: "Check the repair story",
    body: "See whether what you fixed matches the customer complaint and your paperwork.",
    icon: ShieldCheck,
    iconBg: "bg-emerald-500/15",
    iconColor: "text-emerald-400",
  },
  {
    title: "Compare your costs",
    body: "See if parts and labour are in line with typical jobs like this one.",
    icon: Coins,
    iconBg: "bg-amber-500/15",
    iconColor: "text-amber-400",
  },
  {
    title: "Talk to the customer",
    body: "Get short talking points you can use at the counter or on the phone.",
    icon: BarChart3,
    iconBg: "bg-blue-500/15",
    iconColor: "text-blue-400",
  },
  {
    title: "Know the next step",
    body: "Understand whether the claim needs more info before it can move forward.",
    icon: Target,
    iconBg: "bg-fuchsia-500/15",
    iconColor: "text-fuchsia-400",
  },
] as const;

export function DealerDashboardPage() {
  const { user } = useAuth();
  const role = primaryRole(user?.roles);
  const statsQuery = useDealerClaimStats();
  const stats = statsQuery.data ?? { total: 0, underReview: 0, actionRequired: 0, submitted: 0 };
  const underReviewTotal = stats.underReview + stats.submitted;

  if (statsQuery.isLoading) {
    return <LoadingState label="Loading dashboard…" />;
  }

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden bg-base">
      <div className="mx-auto flex h-full min-h-0 w-full max-w-[1120px] flex-col gap-3 px-3 py-3 md:gap-4 md:px-5 md:py-4">
        {statsQuery.isError ? (
          <ErrorState message={(statsQuery.error as Error).message} />
        ) : null}

        <section className="relative shrink-0 overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-[#0c1018] via-surface to-[#0a0c10] shadow-composer">
          <div className="pointer-events-none absolute -left-16 top-0 h-full w-1/2 bg-[radial-gradient(ellipse_at_left,rgb(37_99_235_/_0.22),transparent_65%)]" />
          <div className="relative grid items-center gap-4 p-4 md:grid-cols-[minmax(120px,168px)_1fr_minmax(200px,260px)] md:gap-5 md:p-5">
            <div className="hidden overflow-hidden rounded-xl md:block">
              <img
                src="/images/hero-car.png"
                alt=""
                className="aspect-[4/3] w-full object-cover object-center"
                width={168}
                height={126}
              />
            </div>
            <div className="min-w-0 text-center md:text-left">
              <h1 className="mt-1 text-[18px] font-semibold tracking-tight text-text md:text-[20px]">
                Welcome
              </h1> 
              <p className="mx-auto mt-1.5 max-w-md text-[12px] leading-relaxed text-text-muted md:mx-0 md:text-[13px]">
                Submit a new claim or see where your open claims stand in the process.
              </p>
              <p className="mt-1 text-[11px] text-text-faint">
                {user?.org_name ? ` ${user.org_name}` : ""}
              </p>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <HeroStat icon={FolderOpen} value={stats.total} label="My claims" tone="blue" />
              <HeroStat icon={Clock} value={underReviewTotal} label="In review" tone="amber" />
              <HeroStat
                icon={AlertCircle}
                value={stats.actionRequired}
                label="Needs you"
                tone="rose"
              />
            </div>
          </div>
        </section>

        <div className="grid shrink-0 gap-3 lg:grid-cols-2">
          <ActionCard
            icon={Plus}
            iconGlow="from-blue-500/30"
            title="Submit a new claim"
            description="Enter the repair details, attach documents, and run a claim check before it goes to review."
            illustration={<SubmitClaimIllustration className="h-full w-full max-h-[100px]" />}
            action={
              <Link
                to="/claims/new"
                className="inline-flex items-center justify-center gap-1.5 rounded-lg bg-accent px-4 py-2 text-[13px] font-semibold text-accent-fg transition hover:bg-accent-hover"
              >
                Start new claim
                <ArrowRight className="h-4 w-4" />
              </Link>
            }
          />
          <ActionCard
            icon={Clock}
            iconGlow="from-blue-500/25"
            title="Track your claims"
            description="Open any claim to see status, summary, and what might be asked for next."
            illustration={<TrackClaimsIllustration className="h-full w-full max-h-[100px]" />}
            action={
              <Link
                to="/claims"
                className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-border bg-transparent px-4 py-2 text-[13px] font-medium text-text transition hover:bg-surface-hover"
              >
                View my claims
                <ArrowRight className="h-4 w-4" />
              </Link>
            }
          />
        </div>

        <section className="flex min-h-0 flex-1 flex-col">
          <div className="mb-2 flex shrink-0 items-center gap-2">
            <Sparkles className="h-3.5 w-3.5 text-text-faint" aria-hidden />
            <h2 className="text-[13px] font-semibold text-text">What you can do here</h2>
          </div>
          <div className="grid auto-rows-fr gap-2 sm:grid-cols-2 lg:grid-cols-4">
            {HELP_CARDS.map(({ title, body, icon: Icon, iconBg, iconColor }) => (
              <article
                key={title}
                className="rounded-xl border border-border bg-surface p-3 shadow-composer"
              >
                <span
                  className={`mb-2 inline-flex h-8 w-8 items-center justify-center rounded-lg ${iconBg}`}
                >
                  <Icon className={`h-4 w-4 ${iconColor}`} strokeWidth={1.75} />
                </span>
                <p className="text-[12px] font-semibold text-text md:text-[13px]">{title}</p>
                <p className="mt-1 text-[11px] leading-relaxed text-text-faint">{body}</p>
              </article>
            ))}
          </div>
        </section>

        <p className="shrink-0 pb-0.5 text-center text-[10px] text-text-faint">
          Guidance only — a reviewer makes the final decision on every claim.
        </p>
      </div>
    </div>
  );
}

function HeroStat({
  icon: Icon,
  value,
  label,
  tone,
}: {
  icon: typeof FolderOpen;
  value: number;
  label: string;
  tone: "blue" | "amber" | "rose";
}) {
  const iconClass =
    tone === "blue" ? "text-sky-300" : tone === "amber" ? "text-amber-300" : "text-rose-300";
  const ringClass =
    tone === "blue"
      ? "ring-sky-400/30"
      : tone === "amber"
        ? "ring-amber-400/35"
        : "ring-rose-400/35";

  return (
    <div
      className={`rounded-xl border border-white/20 bg-black/35 px-2.5 py-3 text-center shadow-composer ring-1 backdrop-blur-md ${ringClass}`}
    >
      <Icon className={`mx-auto mb-1.5 h-4 w-4 ${iconClass}`} strokeWidth={2} />
      <p className="text-[22px] font-bold tabular-nums leading-none tracking-tight text-white">{value}</p>
      <p className="mt-1.5 text-[10px] font-semibold uppercase tracking-wide text-white/75">{label}</p>
    </div>
  );
}

function ActionCard({
  icon: Icon,
  iconGlow,
  title,
  description,
  illustration,
  action,
}: {
  icon: typeof Plus;
  iconGlow: string;
  title: string;
  description: string;
  illustration: React.ReactNode;
  action: React.ReactNode;
}) {
  return (
    <article className="relative overflow-hidden rounded-2xl border border-border bg-surface shadow-composer">
      <div
        className={`pointer-events-none absolute inset-x-0 top-0 h-24 bg-gradient-to-b ${iconGlow} to-transparent opacity-80`}
      />
      <div className="relative grid gap-3 p-4 md:grid-cols-[1fr_minmax(100px,130px)] md:items-stretch">
        <div className="flex flex-col justify-between">
          <div>
            <div className="flex items-start gap-2.5">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-primary/30 bg-primary/10">
                <Icon className="h-4 w-4 text-primary" strokeWidth={1.75} />
              </span>
              <h2 className="pt-0.5 text-[15px] font-semibold text-text">{title}</h2>
            </div>
            <p className="mt-2 text-[12px] leading-relaxed text-text-muted">{description}</p>
          </div>
          <div className="mt-3">{action}</div>
        </div>
        <div className="hidden items-center justify-center md:flex">{illustration}</div>
      </div>
    </article>
  );
}
