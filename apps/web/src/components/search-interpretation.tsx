import { areaBasisDisplay, candidateUsage, USAGE_DISCLAIMER } from "../lib/search-display.ts";
import type { CandidateView, SearchViewModel } from "../lib/search-view.ts";

export function AreaBasisPanel({ model }: { model: SearchViewModel }) {
  const area = model.constraintContext ? areaBasisDisplay(model.constraintContext.areaBasis) : null;
  return (
    <section className="area-basis" aria-labelledby="area-basis-title">
      <h3 id="area-basis-title">Area basis</h3>
      {area ? <>
        <p className="basis-selected">Selected: <strong>{area.selected}</strong></p>
        <dl className="basis-values">
          {[["Basis area", area.basis], ["Declared area", area.declared], ["Geometry area", area.geometry], ["Difference", area.difference]].map(([label, value]) => (
            <div key={label}><dt>{label}</dt><dd>{value}{value !== "Unavailable" ? " m²" : ""}</dd></div>
          ))}
        </dl>
      </> : <p>Context unavailable in legacy Search Result v0.1</p>}
    </section>
  );
}

export function ConstraintUsagePanel({ model, selected }: { model: SearchViewModel; selected?: CandidateView }) {
  const rows = candidateUsage(selected, selected?.constraintCaps ?? model.constraintContext?.constraintCaps);
  return (
    <section className="constraint-usage" aria-labelledby="constraint-usage-title">
      <h3 id="constraint-usage-title">Constraint usage</h3>
      <p className="small">{selected ? `Selected: Rank ${selected.rank}` : "No candidate selected / unavailable"}</p>
      <div className="usage-grid">
        {rows.map((row) => (
          <section className="usage-metric" key={row.label} aria-label={row.label}>
            <h4>{row.label} <span className="small">{row.unit}</span></h4>
            <dl>
              <div><dt>Actual</dt><dd>{row.actual}</dd></div>
              <div><dt>Cap</dt><dd>{row.cap}</dd></div>
              <div><dt>Remaining</dt><dd>{row.remaining}</dd></div>
              <div><dt>Usage %</dt><dd>{row.percentage}</dd></div>
            </dl>
          </section>
        ))}
      </div>
      <p className="usage-disclaimer small">{USAGE_DISCLAIMER}</p>
    </section>
  );
}
