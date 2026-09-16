import type { SearchViewModel } from "../lib/search-view.ts";
import { formatMeasure } from "../lib/search-display.ts";
import { BUILDABLE_DOMAIN_NOTICE, BUILDABLE_DERIVATION_NOTICE, BUILDABLE_LEGAL_NOTICE } from "../lib/spatial-display.ts";

export function BuildableAreaPanel({ model }: { model: SearchViewModel }) {
  if (model.schemaVersion !== "0.5") return null;
  const domain = model.spatialContext.buildableArea;
  return <section className="buildable-area" aria-labelledby="buildable-area-title">
    <h3 id="buildable-area-title">Supplied buildable area</h3>
    <dl className="buildable-facts">
      <div><dt>Area</dt><dd>{formatMeasure(domain.areaM2)} m²</dd></div>
      <div><dt>Source status</dt><dd>{domain.sourceStatus}</dd></div>
      <div><dt>Role</dt><dd>{domain.role}</dd></div>
      <div><dt>Review</dt><dd>{domain.reviewRequired ? "REVIEW REQUIRED" : "No spatial review flag"}</dd></div>
    </dl>
    <p>Candidate footprint is constrained to the supplied domain by Python BVE.</p>
    <p className="small">BCR / FARの面積基準は敷地です。この領域の面積に置き換えません。</p>
    <p className="buildable-disclaimer small">{BUILDABLE_DOMAIN_NOTICE}<br />{BUILDABLE_DERIVATION_NOTICE}<br />{BUILDABLE_LEGAL_NOTICE}</p>
  </section>;
}
