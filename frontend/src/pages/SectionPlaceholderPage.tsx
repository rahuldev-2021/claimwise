type Props = { title: string; description: string };

export function SectionPlaceholderPage({ title, description }: Props) {
  return (
    <div className="mx-auto max-w-2xl space-y-2 py-8">
      <h1 className="text-[22px] font-semibold tracking-tight text-text">{title}</h1>
      <p className="text-[13px] leading-relaxed text-text-muted">{description}</p>
    </div>
  );
}
