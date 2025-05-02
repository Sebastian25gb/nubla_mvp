import axios from 'axios';

const API_URL = 'http://localhost:8000';

export const getTenants = async () => {
  const response = await axios.get(`${API_URL}/tenants`);
  return response.data;
};

export const getLogs = async (tenant = null) => {
  const url = tenant ? `${API_URL}/logs?tenant=${tenant}` : `${API_URL}/logs`;
  const response = await axios.get(url);
  return response.data;
};

export const getStats = async () => {
  const response = await axios.get(`${API_URL}/stats`);
  return response.data;
};