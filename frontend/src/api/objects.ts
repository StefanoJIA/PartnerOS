import { http } from '@/api/http'
import type { ObjectType } from '@/constants/objectType'

export type Paginated<T> = { items: T[]; total: number; page: number; limit: number }

export type Note = {
  id: string
  object_type: string
  object_id: string
  body: string
  created_at: string
}

export type Tag = { id: string; name: string; color: string | null }
export type ObjectTagRow = { object_tag_id: string; tag: Tag }

export type ActivityRow = {
  id: string
  object_type: string
  object_id: string
  action: string
  diff: Record<string, unknown> | null
  actor_id: string | null
  created_at: string
}

export type FileMeta = { id: string; original_filename: string; mime: string | null; size: number }
export type FileAttachmentRow = { id: string; file_id: string; purpose: string | null; file: FileMeta }

export type TaskRow = {
  id: string
  title: string
  status: string
  priority?: string | null
  due_at: string | null
  completed_at: string | null
  assignee_user_id: string | null
  assignee_email?: string | null
  related_object_type?: string | null
  related_object_id?: string | null
  created_at?: string
}

export type InteractionRow = {
  id: string
  related_object_type: string
  related_object_id: string
  interaction_type: string
  channel: string
  interaction_date: string
}

export async function listNotes(ot: ObjectType, oid: string, page = 1, limit = 50) {
  const { data } = await http.get<Paginated<Note>>(`/objects/${ot}/${oid}/notes`, { params: { page, limit } })
  return data
}

export async function createNote(ot: ObjectType, oid: string, body: string) {
  const { data } = await http.post<Note>(`/objects/${ot}/${oid}/notes`, { body })
  return data
}

export async function updateNote(ot: ObjectType, oid: string, noteId: string, body: string) {
  const { data } = await http.put<Note>(`/objects/${ot}/${oid}/notes/${noteId}`, { body })
  return data
}

export async function deleteNote(ot: ObjectType, oid: string, noteId: string) {
  await http.delete(`/objects/${ot}/${oid}/notes/${noteId}`)
}

export async function listObjectTags(ot: ObjectType, oid: string, page = 1, limit = 100) {
  const { data } = await http.get<Paginated<ObjectTagRow>>(`/objects/${ot}/${oid}/tags`, { params: { page, limit } })
  return data
}

export async function attachTag(ot: ObjectType, oid: string, tagId: string) {
  await http.post(`/objects/${ot}/${oid}/tags`, { tag_id: tagId })
}

export async function detachTag(ot: ObjectType, oid: string, tagId: string) {
  await http.delete(`/objects/${ot}/${oid}/tags/${tagId}`)
}

export async function listTags(page = 1, limit = 200) {
  const { data } = await http.get<Paginated<Tag>>('/tags', { params: { page, limit } })
  return data
}

export async function createTag(name: string, color?: string | null) {
  const { data } = await http.post<Tag>('/tags', { name, color: color ?? null })
  return data
}

export async function listActivity(ot: ObjectType, oid: string, page = 1, limit = 50) {
  const { data } = await http.get<Paginated<ActivityRow>>(`/objects/${ot}/${oid}/activity`, { params: { page, limit } })
  return data
}

export async function listObjectFiles(ot: ObjectType, oid: string, page = 1, limit = 50) {
  const { data } = await http.get<Paginated<FileAttachmentRow>>(`/objects/${ot}/${oid}/files`, {
    params: { page, limit },
  })
  return data
}

export async function uploadFile(file: File) {
  const fd = new FormData()
  fd.append('upload', file)
  const { data } = await http.post<FileMeta>('/files/upload', fd)
  return data
}

export async function attachUploadedFile(fileId: string, ot: ObjectType, oid: string, purpose?: string | null) {
  await http.post(`/files/${fileId}/attach`, {
    object_type: ot,
    object_id: oid,
    purpose: purpose ?? null,
  })
}

export async function downloadFileBlob(fileId: string) {
  const res = await http.get<Blob>(`/files/${fileId}/download`, { responseType: 'blob' })
  return res.data
}

export async function listObjectInteractions(ot: ObjectType, oid: string, page = 1, limit = 50) {
  const { data } = await http.get<Paginated<InteractionRow>>(`/objects/${ot}/${oid}/interactions`, {
    params: { page, limit },
  })
  return data
}

export async function createInteraction(payload: {
  related_object_type: ObjectType
  related_object_id: string
  interaction_type: string
  channel: string
  subject?: string | null
  content?: string | null
}) {
  const { data } = await http.post<InteractionRow>('/interactions', payload)
  return data
}

export async function listObjectTasks(ot: ObjectType, oid: string, page = 1, limit = 50, status?: string | null) {
  const { data } = await http.get<Paginated<TaskRow>>(`/objects/${ot}/${oid}/tasks`, {
    params: { page, limit, ...(status ? { status } : {}) },
  })
  return data
}

export async function createTask(payload: {
  title: string
  related_object_type?: ObjectType | null
  related_object_id?: string | null
  assignee_user_id?: string | null
  due_at?: string | null
  status?: string
}) {
  const { data } = await http.post<TaskRow>('/tasks', payload)
  return data
}

export async function completeTask(taskId: string) {
  const { data } = await http.post<TaskRow>(`/tasks/${taskId}/complete`)
  return data
}

export async function spawnTaskFromInteraction(interactionId: string, body: Record<string, unknown> = {}) {
  const { data } = await http.post<TaskRow>(`/interactions/${interactionId}/spawn-task`, body)
  return data
}
