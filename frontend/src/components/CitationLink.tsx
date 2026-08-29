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
      className="inline-flex items-center justify-center text-[10px] font-bold text-sky-700 bg-sky-100 hover:bg-sky-200 px-1.5 py-0.2 rounded mx-0.5 border border-sky-300 transition-colors cursor-pointer align-super"
    >
      [{citation.citation_index}]
    </button>
  );
};
