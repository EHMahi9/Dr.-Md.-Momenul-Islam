import React from 'react';
import { CitationReference } from '../types';

interface CitationLinkProps {
  citation: CitationReference;
  onClick?: (chunkId: string) => void;
}

export const CitationLink: React.FC<CitationLinkProps> = ({ citation, onClick }) => {
  return (
    <button
      type="button"
      onClick={() => onClick?.(citation.chunk_id)}
      title={`${citation.source_title} (${citation.chunk_id}): "${citation.excerpt_snippet}"`}
      className="inline-flex items-center justify-center text-[10px] font-semibold text-teal-800 bg-teal-50 hover:bg-teal-100 px-1.5 py-0.5 rounded mx-0.5 border border-teal-200 transition-colors cursor-pointer align-super"
    >
      [{citation.citation_index}]
    </button>
  );
};
