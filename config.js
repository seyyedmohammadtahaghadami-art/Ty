const saved = localStorage.getItem('typo_api_base');
export const API_BASE_URL = saved || (location.protocol === 'http:' || location.protocol === 'https:' ? location.origin : '');
export function setApiBase(value){ if(value) localStorage.setItem('typo_api_base', value.replace(/\/$/,'')); else localStorage.removeItem('typo_api_base'); }
