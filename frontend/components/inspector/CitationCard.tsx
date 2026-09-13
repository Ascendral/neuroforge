'use client';

import type { NeuronResponse } from '@/lib/types';

interface CitationCardProps {
  neuron: NeuronResponse;
}

// Anti-theater: every link below points to a resolvable canonical URL for
// real upstream identifiers (NeuroMorpho, doi.org, pubmed.ncbi.nlm.nih.gov).
// We never fabricate DOIs or PMIDs.

export function CitationCard({ neuron }: CitationCardProps) {
  const hasRefs = neuron.reference_doi.length > 0 || neuron.reference_pmid.length > 0;

  return (
    <section aria-label="Citations" className="space-y-3">
      <h3 className="kicker">Source</h3>
      <dl className="space-y-1.5 text-[13px]">
        <div className="flex gap-2">
          <dt className="w-20 text-white/40">archive</dt>
          <dd className="text-white">{neuron.archive}</dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-20 text-white/40">neuron</dt>
          <dd>
            <a
              className="text-white underline-offset-2 hover:underline"
              href={neuron.source_url}
              target="_blank"
              rel="noreferrer"
            >
              {neuron.neuron_name} (#{neuron.neuron_id})
            </a>
          </dd>
        </div>
        <div className="flex gap-2">
          <dt className="w-20 text-white/40">swc</dt>
          <dd>
            <a
              className="break-all text-white/70 underline-offset-4 hover:underline"
              href={neuron.swc_url}
              target="_blank"
              rel="noreferrer"
            >
              {neuron.swc_url.replace('https://neuromorpho.org', '')}
            </a>
          </dd>
        </div>
      </dl>

      {hasRefs && (
        <div className="space-y-2">
          <h3 className="kicker">References</h3>
          {neuron.reference_doi.length > 0 && (
            <ul className="space-y-1.5 text-[13px]">
              {neuron.reference_doi.map((doi) => (
                <li key={doi} className="flex gap-2">
                  <span className="w-12 text-white/40">doi</span>
                  <a
                    className="break-all text-white underline-offset-2 hover:underline"
                    href={`https://doi.org/${doi}`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {doi}
                  </a>
                </li>
              ))}
            </ul>
          )}
          {neuron.reference_pmid.length > 0 && (
            <ul className="space-y-1.5 text-[13px]">
              {neuron.reference_pmid.map((pmid) => (
                <li key={pmid} className="flex gap-2">
                  <span className="w-12 text-white/40">pmid</span>
                  <a
                    className="text-white/80 underline-offset-2 hover:underline"
                    href={`https://pubmed.ncbi.nlm.nih.gov/${pmid}/`}
                    target="_blank"
                    rel="noreferrer"
                  >
                    {pmid}
                  </a>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {!hasRefs && (
        <p className="text-xs text-white/40">
          No publication references available for this neuron in the upstream record.
        </p>
      )}
    </section>
  );
}
