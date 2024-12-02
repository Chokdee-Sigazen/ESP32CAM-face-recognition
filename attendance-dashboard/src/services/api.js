import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8080/api'
});

export const getDashboardData = () => api.get('/dashboard-data');