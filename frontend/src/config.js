// Configuration for API URL based on environment
// In development, this will be empty (using relative path via Vite proxy)
// In production, this should be set to the backend URL (e.g., https://your-backend.onrender.com)
export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
