import { describe, expect, it } from 'vitest'
import { buildProductBrief, PRODUCT_FOCUS_LABELS } from '@/constants/productFit'

describe('productFit constants', () => {
  it('buildProductBrief includes key fields', () => {
    const brief = buildProductBrief({
      company_name: 'SWC Office Furniture',
      opportunity_level: 'promising',
      project_opportunity_score: 78,
      recommended_product_focus: ['adjustable_desk_frames', 'hosun_lifting_systems'],
      quote_readiness: 'almost_ready',
      missing_quote_info: ['quantity_or_volume', 'project_timeline'],
      recommended_next_product_action: 'Ask for quantity before quote.',
    })
    expect(brief).toContain('SWC Office Furniture')
    expect(brief).toContain('Promising (78)')
    expect(brief).toContain(PRODUCT_FOCUS_LABELS.adjustable_desk_frames)
    expect(brief).toContain('Almost Ready')
  })
})
