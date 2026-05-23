import { http } from '@/api/http'
import type { Paginated } from '@/api/objects'

export type TaskDto = {
  id: string
  title: string
  description: string | null
  status: string
  priority: string | null
  due_at: string | null
  completed_at: string | null
  assignee_user_id: string | null
  assignee_email: string | null
  related_object_type: string | null
  related_object_id: string | null
  created_at: string
}

export type TaskStats = {
  due_today: number
  overdue: number
  this_week: number
  open_tasks: number
  completed_tasks: number
}

export type UserBrief = { id: string; email: string; full_name: string }

export async function fetchTaskStats() {
  const { data } = await http.get<TaskStats>('/tasks/summary')
  return data
}

export async function fetchTasks(params: Record<string, unknown>) {
  const { data } = await http.get<Paginated<TaskDto>>('/tasks', { params })
  return data
}

export async function getTask(id: string) {
  const { data } = await http.get<TaskDto>(`/tasks/${id}`)
  return data
}

export async function createTask(body: Record<string, unknown>) {
  const { data } = await http.post<TaskDto>('/tasks', body)
  return data
}

export async function updateTask(id: string, body: Record<string, unknown>) {
  const { data } = await http.put<TaskDto>(`/tasks/${id}`, body)
  return data
}

export async function completeTask(id: string) {
  const { data } = await http.post<TaskDto>(`/tasks/${id}/complete`)
  return data
}

export async function listUsersBrief(page = 1, limit = 200) {
  const { data } = await http.get<Paginated<UserBrief>>('/users', { params: { page, limit } })
  return data
}
