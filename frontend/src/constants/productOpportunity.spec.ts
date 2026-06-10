/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it } from 'vitest'
import {
  COMMON_QUOTE_QUESTIONS,
  filterProductOpportunityRows,
  mapBoardRow,
  productFilterQueryPath,
} from '@/constants/productOpportunity'

describe('productOpportunity constants', () => {
  const rows = [
    mapBoardRow({
      lead_id: '1',
      company_name: 'Lift Co',
      project_opportunity_score: 85,
      opportunity_level: 'high_opportunity',
      project_type: 'dealer_supply',
      quote_readiness: 'ready',
      sample_readiness: 'ready',
      recommended_product_focus: ['hosun_lifting_systems'],
      missing_quote_info: [],
    }),
    mapBoardRow({
      lead_id: '2',
      company_name: 'Project Co',
      project_opportunity_score: 65,
      opportunity_level: 'promising',
      project_type: 'project_based',
      quote_readiness: 'almost_ready',
      sample_readiness: 'needs_specs',
      recommended_product_focus: ['project_supply'],
      missing_quote_info: ['quantity_or_volume', 'project_timeline'],
    }),
  ]

  it('filters quote ready', () => {
    const filtered = filterProductOpportunityRows(rows, 'quote_ready')
    expect(filtered).toHaveLength(1)
    expect(filtered[0].companyName).toBe('Lift Co')
  })

  it('filters lifting system fit', () => {
    const filtered = filterProductOpportunityRows(rows, 'lifting_system_fit')
    expect(filtered).toHaveLength(1)
  })

  it('filters missing quantity', () => {
    const filtered = filterProductOpportunityRows(rows, 'missing_quantity')
    expect(filtered[0].companyName).toBe('Project Co')
  })

  it('builds dashboard link path', () => {
    expect(productFilterQueryPath('quote_ready')).toContain('productFilter=quote_ready')
  })

  it('common questions text is non-empty', () => {
    expect(COMMON_QUOTE_QUESTIONS).toContain('数量或体量')
  })
})
