// config.js - Browser compatible version
const API_URL = 'https://maha1326-vastr-fashion-api.hf.space/api/v1';
const API_BASE = API_URL; // Compatibility

const API_ENDPOINTS = {
  products: `${API_URL}/products`,
  brands: `${API_URL}/brands`,
  categories: `${API_URL}/categories`,
  search: `${API_URL}/search`,
  health: `${API_URL}/health`,
};

// Log to verify it's loaded
console.log('✅ Config loaded! API URL:', API_URL);
