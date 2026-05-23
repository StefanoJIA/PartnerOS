/**
 * @vitest-environment happy-dom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import CompanyEnrichmentPanel from './CompanyEnrichmentPanel.vue'
import * as enrichmentApi from '@/api/companyEnrichment'

vi.mock('@/api/companyEnrichment', () => ({
  createEnrichmentRun: vi.fn(),
  listEnrichmentRuns: vi.fn(),
  getEnrichmentRunDetail: vi.fn(),
  reviewEnrichmentSuggestion: vi.fn(),
  batchReviewEnrichment: vi.fn(),
  applyEnrichmentSuggestion: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(enrichmentApi.listEnrichmentRuns).mockResolvedValue({ items: [], total: 0 })
})

function summary(partial: Partial<enrichmentApi.EnrichmentRunSummary> = {}): enrichmentApi.EnrichmentRunSummary {
  return {
    id: 'run-1',
    company_id: 'c1',
    status: 'completed',
    source_scope: 'website_mvp_v1',
    max_pages: 10,
    pages_fetched: 3,
    pending_suggestion_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    ...partial,
  }
}

describe('CompanyEnrichmentPanel', () => {
  it('shows hint when company has no website', async () => {
    const w = mount(CompanyEnrichmentPanel, {
      props: { companyId: 'c1', website: null },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    expect(w.text()).toContain('该公司无网站 URL')
    expect(enrichmentApi.createEnrichmentRun).not.toHaveBeenCalled()
  })

  it('starts enrichment run when clicking primary action', async () => {
    vi.mocked(enrichmentApi.createEnrichmentRun).mockResolvedValue(summary({ status: 'pending' }))
    vi.mocked(enrichmentApi.listEnrichmentRuns).mockResolvedValue({
      items: [summary({ status: 'running' })],
      total: 1,
    })

    const w = mount(CompanyEnrichmentPanel, {
      props: { companyId: 'c1', website: 'https://example.com' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    await w.get('button').trigger('click')
    await flushPromises()
    expect(enrichmentApi.createEnrichmentRun).toHaveBeenCalledWith('c1')
  })

  it('opens review drawer and loads run detail', async () => {
    vi.mocked(enrichmentApi.listEnrichmentRuns).mockResolvedValue({
      items: [summary({ pending_suggestion_count: 2 })],
      total: 1,
    })
    vi.mocked(enrichmentApi.getEnrichmentRunDetail).mockResolvedValue({
      run: summary(),
      sources: [
        {
          id: 's1',
          url: 'https://example.com/about',
          page_type: 'about',
          fetch_status: 'ok',
        },
      ],
      suggestions: [
        {
          id: 'g1',
          enrichment_run_id: 'run-1',
          suggestion_type: 'tag',
          suggested_value: 'height_adjustable_desk',
          review_status: 'pending',
        },
      ],
    })

    const w = mount(CompanyEnrichmentPanel, {
      props: { companyId: 'c1', website: 'https://example.com' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    const reviewBtn = w.findAll('button').find((b) => b.text().includes('审阅建议与证据'))
    expect(reviewBtn).toBeTruthy()
    await reviewBtn!.trigger('click')
    await flushPromises()
    expect(enrichmentApi.getEnrichmentRunDetail).toHaveBeenCalledWith('run-1')
    expect(w.text()).toContain('height_adjustable_desk')
  })

  it('accepts a pending suggestion from the drawer', async () => {
    vi.mocked(enrichmentApi.listEnrichmentRuns).mockResolvedValue({
      items: [summary()],
      total: 1,
    })
    vi.mocked(enrichmentApi.getEnrichmentRunDetail)
      .mockResolvedValueOnce({
        run: summary(),
        sources: [],
        suggestions: [
          {
            id: 'g1',
            enrichment_run_id: 'run-1',
            suggestion_type: 'tag',
            suggested_value: 'lifting_column_interest',
            review_status: 'pending',
          },
        ],
      })
      .mockResolvedValueOnce({
        run: summary(),
        sources: [],
        suggestions: [
          {
            id: 'g1',
            enrichment_run_id: 'run-1',
            suggestion_type: 'tag',
            suggested_value: 'lifting_column_interest',
            review_status: 'accepted',
          },
        ],
      })
    vi.mocked(enrichmentApi.reviewEnrichmentSuggestion).mockResolvedValue({
      id: 'g1',
      enrichment_run_id: 'run-1',
      suggestion_type: 'tag',
      suggested_value: 'lifting_column_interest',
      review_status: 'accepted',
    })

    const w = mount(CompanyEnrichmentPanel, {
      props: { companyId: 'c1', website: 'https://example.com' },
      global: { plugins: [ElementPlus] },
    })
    await flushPromises()
    await w.findAll('button').find((b) => b.text().includes('审阅建议与证据'))!.trigger('click')
    await flushPromises()
    const accept = w.findAll('button').find((b) => b.text() === '接受')
    expect(accept).toBeTruthy()
    await accept!.trigger('click')
    await flushPromises()
    expect(enrichmentApi.reviewEnrichmentSuggestion).toHaveBeenCalledWith('g1', { review_status: 'accepted' })
  })
})
