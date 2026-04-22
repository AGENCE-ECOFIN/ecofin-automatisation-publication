import React from 'react';

/**
 * @param {object} meta - Réponse API : total, page, page_size, total_pages
 * @param {function} onPageChange - (newPage: number) => void
 */
const Pagination = ({ meta = {}, onPageChange, className = '' }) => {
  const page = meta.page ?? 1;
  const totalPages = meta.total_pages ?? 1;
  const total = meta.total ?? 0;

  if (total === 0) return null;

  return (
    <div
      className={`flex flex-col sm:flex-row items-center justify-between gap-3 py-4 border-t border-gray-200 ${className}`}
    >
      <p className="text-sm text-gray-600">
        <span className="font-medium text-gray-900">{total}</span>
        {' '}résultat{total > 1 ? 's' : ''}
        {totalPages > 1 && (
          <span className="text-gray-500"> · page {page} / {totalPages}</span>
        )}
      </p>
      {totalPages > 1 && (
        <div className="flex items-center gap-2">
          <button
            type="button"
            disabled={page <= 1}
            onClick={() => onPageChange(page - 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Précédent
          </button>
          <span className="text-sm text-gray-700 min-w-[5rem] text-center tabular-nums">
            {page} / {totalPages}
          </span>
          <button
            type="button"
            disabled={page >= totalPages}
            onClick={() => onPageChange(page + 1)}
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
};

export default Pagination;
