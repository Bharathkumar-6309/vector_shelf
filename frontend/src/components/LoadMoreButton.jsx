import React from 'react'

export default function LoadMoreButton({ onClick, disabled, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
    >
      {loading ? 'Loading...' : 'Load More'}
    </button>
  )
}
