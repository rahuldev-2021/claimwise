/** Fixed UI strings for dealer-facing surfaces (not the technical full assessment). */

export const dealerCopy = {
  tabs: {
    summary: "Claim summary",
    documents: "Documents",
    history: "History",
    decision: "Decision",
  },
  actions: {
    runClaimCheck: "Run claim check",
    rerunClaimCheck: "Run check again",
    runningClaimCheck: "Running claim check…",
    viewFullAssessment: "View full assessment",
    openFullTrace: (steps: number) => `Technical details (${steps} steps)`,
    claimCheckOptions: "Check options",
    makeDecision: "Record decision",
  },
  sections: {
    repairCheck: "Repair check",
    costCheck: "Cost check",
    nextStep: "Next step",
    plainSummary: "Plain-language summary",
    communicationHints: "What to say",
    response: "Response",
    responseBecause: "Because",
    responseSay: "What to say",
    submittedAmounts: "What you submitted",
    repairCheckBadge: "Repair check",
  },
  disclaimers: {
    advisoryOnly: "This is guidance only — it does not approve or deny the claim.",
    plainSummaryNote: "Friendly summary only. The repair check result above is what counts.",
    nextStepNote: "Suggested next step — a reviewer still decides the outcome.",
    humanReview: "A reviewer still signs off on the claim.",
  },
  assessmentEmpty: {
    title: "No claim check yet",
    body: "Run a claim check to see whether the repair story holds up, how your costs compare to typical jobs, and what to tell the customer.",
    noPermission: "Your account can't run claim checks. Ask your manager if you need access.",
  },
  options: {
    title: "When you run a check",
    autoIngest: "Attach policy documents automatically",
    llmSummary: "Include a plain-language summary",
    financial: "Compare parts and labour to typical jobs",
  },
  loading: {
    claim: "Loading claim…",
    assessment: "Loading your summary…",
    running: "Running claim check (repair, costs, summary)…",
    evidence: "Loading documents…",
  },
  documents: {
    emptyNoDocs: "Add supporting documents on the claim, then run a claim check to pull relevant excerpts.",
    emptyWithDocs: "Run a claim check to show excerpts from your uploaded documents.",
    evidenceTitle: "From your documents",
    emptyRetrieval: "No matching excerpts yet. Run a claim check with document attach enabled.",
    historyNote:
      "Only past repair records were found. They help with context but don't prove this specific problem.",
    verified: "Verified",
    unverified: "Not verified",
  },
  list: {
    myClaims: "My claims",
    myClaimsSubtitle: "Find and open claims in your dealership.",
    reviewQueue: "Needs attention",
    reviewQueueSubtitle: "Claims waiting on you or further review.",
    tableHeading: "Claim list",
    tableCaption: "Select a claim to open details, run a check, and see suggested next steps.",
  },
  fields: {
    partsVariance: "Parts vs typical",
    labourVariance: "Labour vs typical",
    costCheckUnavailable: "Turn on cost comparison in check options to see how your numbers compare.",
  },
} as const;
