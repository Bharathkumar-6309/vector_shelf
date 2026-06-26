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
  const observerRef = useRef()
  const isFetchingRef = useRef(false) // 🔥 NEW FIX

  // -----------------------------
  // LOAD PRODUCTS
  // -----------------------------
  async function load({ reset = false, cursorArg = null, snapshotArg = snapshot } = {}) {
    if (isFetchingRef.current) return // 🔥 prevent duplicate calls

    isFetchingRef.current = true
    setLoading(true)
    setError(null)

    const requestId = ++latestRequestRef.current
    const useCursor = reset ? null : (cursorArg ?? cursor)

    try {
      const data = await fetchProducts({
        cursor: useCursor,
        limit: PAGE_LIMIT,
        category,
        snapshot: snapshotArg
      })

      if (requestId !== latestRequestRef.current) return

      const items = data.items || []
      const nextCursor = data.pagination?.next_cursor ?? null
      const hasNext = Boolean(data.pagination?.has_next)
      const snapshotAt = data.snapshot ?? null

      setProducts((prev) => {
        const merged = reset ? items : [...prev, ...items]
        const unique = Array.from(new Map(merged.map(i => [i.id, i])).values())
        return unique
      })

      setCursor(nextCursor)
      setHasMore(hasNext)

      if (reset && snapshotAt) {
        localStorage.setItem('vectorshelf.snapshot', snapshotAt)
        setSnapshot(snapshotAt)
      } else if (!snapshot && snapshotAt) {
        setSnapshot(snapshotAt)
      }

    } catch (err) {
      setError(err?.message || 'Failed to load products')
    } finally {
      if (requestId === latestRequestRef.current) {
        setLoading(false)
      }
      isFetchingRef.current = false // 🔥 unlock
    }
  }

  // -----------------------------
  // INITIAL LOAD
  // -----------------------------
  useEffect(() => {
    let mounted = true

    ;(async () => {
      try {
        const cats = await fetchCategories()
        if (mounted) setCategories(cats)
      } catch {}
    })()

    setProducts([])
    setCursor(null)
    setHasMore(true)
    load({ reset: true })

    return () => {
      mounted = false
    }
  }, [])

  // -----------------------------
  // CATEGORY CHANGE
  // -----------------------------
  useEffect(() => {
    setProducts([])
    setCursor(null)
    setHasMore(true)

    localStorage.removeItem('vectorshelf.snapshot')
    setSnapshot(null)

    load({ reset: true, snapshotArg: null })
  }, [category])

  // -----------------------------
  // INFINITE SCROLL (FIXED)
  // -----------------------------
  useEffect(() => {
    const el = observerRef.current
    if (!el) return
    if (!hasMore) return

    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0]

      if (!entry.isIntersecting) return
      if (loading) return
      if (!hasMore) return

      load()
    }, {
      rootMargin: '200px'
    })

    observer.observe(el)

    return () => observer.disconnect()
  }, [hasMore, loading, cursor])

  // -----------------------------
  // UI
  // -----------------------------
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">

        <header className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Product Browser</h1>
          <CategorySelect
            categories={categories}
            value={category}
            onChange={setCategory}
          />
        </header>

        {snapshot && (
          <div className="text-sm text-gray-500 mb-4">
            Snapshot: {snapshot}
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-800 rounded">
            <div className="flex justify-between">
              <span>{error}</span>
              <button onClick={() => load({ reset: true })}>
                Retry
              </button>
            </div>
          </div>
        )}

        {/* GRID */}
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
            <div className="col-span-full p-6 text-center text-gray-600">
              No products found
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-center">
          <LoadMoreButton
            onClick={() => load()}
            disabled={!hasMore || loading}
            loading={loading}
          />
        </div>

        {/* sentinel */}
        <div ref={observerRef} style={{ height: 1 }} />

      </div>
    </div>
  )
}