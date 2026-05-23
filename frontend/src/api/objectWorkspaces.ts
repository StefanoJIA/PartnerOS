import { http } from '@/api/http'

export async function fetchCompanyWorkspace(companyId: string) {
  const { data } = await http.get<Record<string, unknown>>(`/companies/${companyId}/workspace`)
  return data
}

export async function fetchContactWorkspace(contactId: string) {
  const { data } = await http.get<Record<string, unknown>>(`/contacts/${contactId}/workspace`)
  return data
}

export async function fetchPartnerWorkspace(partnerId: string) {
  const { data } = await http.get<Record<string, unknown>>(`/manufacturing-partners/${partnerId}/workspace`)
  return data
}

export async function fetchProductWorkspace(productId: string) {
  const { data } = await http.get<Record<string, unknown>>(`/products/${productId}/workspace`)
  return data
}
