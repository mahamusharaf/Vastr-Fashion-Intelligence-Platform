// config.js
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'https://maha1326-vastr-fashion-api.hf.space/api/v1';

export const API_ENDPOINTS = {
  products: `${API_URL}/products`,
  brands: `${API_URL}/brands`,
  categories: `${API_URL}/categories`,
  search: `${API_URL}/search`,
  health: `${API_URL}/health`,
  // Add other endpoints as needed
};

export default API_URL;
