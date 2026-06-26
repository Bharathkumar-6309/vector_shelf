import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL

export const api = axios.create({
  baseURL,
  timeout: 10000
})

// Helper to request products with cursor-based pagination
// Maps FastAPI ProductListResponse to a simpler shape consumed by the UI
export async function fetchProducts({ cursor = null, limit = 12, category = null, snapshot = null } = {}) {
  const params = { limit }
  if (cursor) params.cursor = cursor
  if (snapshot) params.snapshot = snapshot
  if (category) params.category = category

  const resp = await api.get('/products', { params })
  const body = resp.data

  // FastAPI response shape: { snapshot, products, pagination, category }
  return {
    items: body.products || [],
    pagination: body.pagination || {},
    snapshot: body.snapshot || null,
    category: body.category || null
  }
}

export async function fetchCategories() {
  const resp = await api.get('/categories')
  return resp.data?.data || []
}
