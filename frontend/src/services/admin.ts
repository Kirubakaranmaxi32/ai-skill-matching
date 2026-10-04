import { apiClient } from './api';
import {
  AdminOverviewResponse,
  AdminStudentStats,
  AdminProjectStats,
  AdminProgressStats,
  AdminFeedbackStats,
  AdminAiMatchingStats,
  AdminSystemStats,
  AdminStatusResponse,
} from '../types/admin';

export const checkAdminStatus = async (): Promise<AdminStatusResponse> => {
  const response = await apiClient.get<AdminStatusResponse>('/admin/status');
  return response.data;
};

export const getAdminOverview = async (): Promise<AdminOverviewResponse> => {
  const response = await apiClient.get<AdminOverviewResponse>('/admin/overview');
  return response.data;
};

export const getAdminStudentStats = async (): Promise<AdminStudentStats> => {
  const response = await apiClient.get<AdminStudentStats>('/admin/students');
  return response.data;
};

export const getAdminProjectStats = async (): Promise<AdminProjectStats> => {
  const response = await apiClient.get<AdminProjectStats>('/admin/projects');
  return response.data;
};

export const getAdminProgressStats = async (): Promise<AdminProgressStats> => {
  const response = await apiClient.get<AdminProgressStats>('/admin/progress');
  return response.data;
};

export const getAdminFeedbackStats = async (): Promise<AdminFeedbackStats> => {
  const response = await apiClient.get<AdminFeedbackStats>('/admin/feedback');
  return response.data;
};

export const getAdminAiMatchingStats = async (): Promise<AdminAiMatchingStats> => {
  const response = await apiClient.get<AdminAiMatchingStats>('/admin/ai-matching');
  return response.data;
};

export const getAdminSystemStats = async (): Promise<AdminSystemStats> => {
  const response = await apiClient.get<AdminSystemStats>('/admin/system');
  return response.data;
};
