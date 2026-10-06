import { client } from './client'
import type { DocumentContent, FileItem } from '@/types/api'

export const filesApi = {
  /** q 非空时后端跨目录全库搜（文件名或解析正文） */
  list(params: { parentId?: string; q?: string } = {}) {
    return client.get<FileItem[]>('/files', { params: { parent_id: params.parentId, q: params.q } })
  },
  upload(file: File, parentId?: string) {
    const fd = new FormData()
    fd.append('file', file)
    // 大文件上传 + 服务端解析耗时长，单独放宽超时
    return client.post<FileItem>('/files', fd, { params: { parent_id: parentId }, timeout: 300000 })
  },
  createFolder(name: string, parentId?: string) {
    return client.post<FileItem>('/files/folder', { name, parent_id: parentId })
  },
  remove(id: string) {
    return client.delete(`/files/${id}`)
  },
  download(id: string) {
    return client.get(`/files/${id}/download`, { responseType: 'blob' })
  },
}

export const documentsApi = {
  content(docId: string) {
    return client.get<DocumentContent>(`/documents/${docId}/content`)
  },
  reparse(docId: string) {
    return client.post(`/documents/${docId}/reparse`)
  },
}
