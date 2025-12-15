// Your Hugging Face Backend URL
const API_BASE = 'https://maha1326-vastr-fashion-api.hf.space/api/v1';
const API_URL = API_BASE; // Alias for compatibility

// API Endpoints
const API_ENDPOINTS = {
  products: `${API_BASE}/products`,
  brands: `${API_BASE}/brands`,
  categories: `${API_BASE}/categories`,
  search: `${API_BASE}/search`,
  health: `${API_BASE}/health`,
};

// Log configuration for debugging
console.log('API Configuration loaded:', {
  API_BASE,
  API_ENDPOINTS
});
