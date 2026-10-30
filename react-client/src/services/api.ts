import { fetchApiClient } from './apiClient'
import { mockApiClient } from './mockApi'

// Offline demo is the default. Set VITE_USE_MOCK=false when the backend is available.
export const apiClient = import.meta.env.VITE_USE_MOCK === 'false' ? fetchApiClient : mockApiClient
