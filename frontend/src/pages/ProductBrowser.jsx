import React, { useEffect, useRef, useState } from 'react'
import { fetchProducts, fetchCategories } from '../services/api'
import ProductCard from '../components/ProductCard'
import CategorySelect from '../components/CategorySelect'
import LoadMoreButton from '../components/LoadMoreButton'

const PAGE_LIMIT = 12

export default function ProductBrowser() {
  const [products, setProducts] = useState([])
  const [cursor, setCursor] = useState(null)
  const [snapshot, setSnapshot] = useState(() => {
    try {
      return localStorage.getItem('vectorshelf.snapshot')
    } catch {
      return null
    }
  })
  const [category, setCategory] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [hasMore, setHasMore] = useState(true)
  const [categories, setCategories] = useState([])
  const latestRequestRef = useRef(0)
  // expose raw cursor components optionally for debugging or alternate UI strategies
  const [cursorUpdatedAt, setCursorUpdatedAt] = useState(null)
  const [cursorId, setCursorId] = useState(null)
  const observerRef = useRef()

  // load products; accepts explicit cursor to avoid stale closures
  async function load({ reset = false, cursorArg = null, snapshotArg = snapshot } = {}) {
    setLoading(true)
    setError(null)
    const requestId = ++latestRequestRef.current
    const useCursor = reset ? null : (cursorArg ?? cursor)
    try {
      const data = await fetchProducts({ cursor: useCursor, limit: PAGE_LIMIT, category, snapshot: snapshotArg })

      if (requestId !== latestRequestRef.current) {
        return
      }

      const items = data.items || []
      const nextCursor = data.pagination?.next_cursor ?? null
      const hasNext = Boolean(data.pagination?.has_next)
      const snapshotAt = data.snapshot ?? null

      setProducts((prev) => {
        const merged = reset ? items : [...prev, ...items]
        const uniqueById = Array.from(new Map(merged.map((item) => [item.id, item])).values())
        return uniqueById
      })
      setCursor(nextCursor)
      setHasMore(hasNext)

      // persist snapshot on first load (reset) so UI shows a consistent snapshot
      if (reset && snapshotAt) {
        try {
          localStorage.setItem('vectorshelf.snapshot', snapshotAt)
        } catch {}
        setSnapshot(snapshotAt)
      } else if (!snapshot && snapshotAt) {
        // set snapshot if not present
        setSnapshot(snapshotAt)
      }
    } catch (err) {
      setError(err?.message || 'Failed to load products')
    } finally {
      if (requestId === latestRequestRef.current) {
        setLoading(false)
      }
    }
  }

  // load initial categories and first page
  useEffect(() => {
    let mounted = true
    ;(async () => {
      try {
        const cats = await fetchCategories()
        if (mounted) setCategories(cats)
      } catch (e) {
        // ignore categories error; UI will still work with default select
      }
    })()

    // initial load
    setProducts([])
    setCursor(null)
    setHasMore(true)
    load({ reset: true })

    return () => {
      mounted = false
    }
  }, [])

  // reload when category changes
  useEffect(() => {
    setProducts([])
    setCursor(null)
    setHasMore(true)
    // clear persisted snapshot on category switch to get a new consistent snapshot
    try {
      localStorage.removeItem('vectorshelf.snapshot')
    } catch {}
    setSnapshot(null)
    load({ reset: true, snapshotArg: null })
  }, [category])

  // infinite scroll observer
  useEffect(() => {
    if (!hasMore || loading) return
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) {
        load()
      }
    }, { rootMargin: '200px' })

    const el = observerRef.current
    if (el) observer.observe(el)
    return () => observer.disconnect()
  }, [hasMore, loading, cursor])

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Product Browser</h1>
          <div className="flex items-center gap-4">
            <CategorySelect categories={categories} value={category} onChange={setCategory} />
          </div>
        </header>

        {/* snapshot / info */}
        {snapshot && <div className="text-sm text-gray-500 mb-4">Snapshot: {snapshot}</div>}

        {/* error */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-800 rounded">
            <div className="flex items-center justify-between">
              <div>{error}</div>
              <button onClick={() => load({ reset: true })} className="text-sm text-blue-600">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map((p) => (
            <ProductCard key={p.id ?? p._id ?? p.slug} product={p} />
          ))}

          {loading && Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="p-4">
              <div className="skeleton h-36 mb-4" />
              <div className="skeleton h-4 w-3/4 mb-2" />
              <div className="skeleton h-4 w-1/4" />
            </div>
          ))}
          {!loading && products.length === 0 && !error && (
            <div className="col-span-full p-6 rounded-lg border border-dashed border-gray-300 text-center text-gray-600">
              No products found yet. Try selecting another category or refresh the page.
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center justify-center gap-4">
          <LoadMoreButton
            onClick={() => load()}
            disabled={!hasMore || loading}
            loading={loading}
          />
        </div>

        {/* sentinel for infinite scroll */}
        <div ref={observerRef} style={{ height: 1 }} />
      </div>
    </div>
  )
}
