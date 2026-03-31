import http from './http'

// ---------- Types ----------

export interface Category {
  id: string
  display_name: string
  icon: string | null
  sort_order: number
  is_default: boolean
  created_by: string | null
  created_at: string
}

export interface CategoryCreate {
  display_name: string
  icon?: string
  sort_order?: number
}

export interface CategoryUpdate {
  display_name?: string
  icon?: string
  sort_order?: number
}

// ---------- API ----------

export const listCategories = () =>
  http.get<Category[]>('/categories')

export const getCategory = (id: string) =>
  http.get<Category>(`/categories/${id}`)

export const createCategory = (payload: CategoryCreate) =>
  http.post<Category>('/categories', payload)

export const updateCategory = (id: string, payload: CategoryUpdate) =>
  http.put<Category>(`/categories/${id}`, payload)

export const deleteCategory = (id: string) =>
  http.delete(`/categories/${id}`)
