interface PagePlaceholderProps {
  title: string;
  description: string;
  bullets?: string[];
}

export function PagePlaceholder({ title, description, bullets }: PagePlaceholderProps): JSX.Element {
  return (
    <div className="space-y-6">
      <section className="card">
        <h2 className="text-base font-semibold text-white">{title}</h2>
        <p className="mt-1 text-sm text-slate-400">{description}</p>
      </section>
      {bullets && bullets.length > 0 && (
        <section className="card">
          <h3 className="text-sm font-semibold text-slate-200">Planned capabilities</h3>
          <ul className="mt-3 list-inside list-disc space-y-1 text-sm text-slate-300">
            {bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

export default PagePlaceholder;
