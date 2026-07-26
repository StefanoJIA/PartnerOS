/**
 * @vitest-environment happy-dom
 */
import { describe, expect, it, vi } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import ElementPlus from 'element-plus'
import ContainerCalcPage from '@/pages/tools/ContainerCalcPage.vue'
import { http } from '@/api/http'

vi.mock('@/api/http', () => ({
  http: {
    post: vi.fn(),
  },
}))

describe('ContainerCalcPage', () => {
  it('calculates pallet positions and renders layer split visualization', async () => {
    vi.mocked(http.post).mockResolvedValue({
      data: {
        summary: {
          total_cbm: 2.88,
          approx_container_load: 0.042,
          pallet_positions: 2,
          physical_pallets: 3,
          blocked_specs: 0,
        },
        plans: [
          {
            label: '主包装箱',
            status: 'ok',
            total_cbm: 2.88,
            cartons_per_layer: 4,
            layers_per_full_pallet: 10,
            cartons_per_full_pallet: 40,
            full_pallet_height_cm: 200,
            full_pallet_layer_segments: [5, 5],
            best_orientation: { orientation: 'normal', along_length: 2, along_width: 2 },
            pallet_positions: 2,
            physical_pallets: 3,
            pallet_units: [
              {
                cartons: 40,
                layers: 10,
                layer_segments: [5, 5],
                divider_pallets: 1,
                gross_height_cm: 200,
                physical_pallets: 2,
              },
              {
                cartons: 20,
                layers: 5,
                layer_segments: [5],
                divider_pallets: 0,
                gross_height_cm: 100,
                physical_pallets: 1,
              },
            ],
            warnings: ['层数超过连续堆叠上限，系统已加入中间托盘分段。'],
          },
        ],
      },
    })

    const wrapper = mount(ContainerCalcPage, { global: { plugins: [ElementPlus] } })
    expect(wrapper.text()).toContain('托盘与装柜计算')
    expect(wrapper.text()).toContain('不会通知承运商')

    const calculateButton = wrapper.findAll('button').find((button) => button.text().includes('计算托盘方案'))
    expect(calculateButton).toBeTruthy()
    await calculateButton!.trigger('click')
    await flushPromises()

    expect(http.post).toHaveBeenCalledWith(
      '/container-calculator/pallet-plan',
      expect.objectContaining({
        pallet_length_cm: 120,
        pallet_width_cm: 100,
        pallet_height_cm: 20,
        max_total_height_cm: 200,
        max_continuous_layers: 8,
      }),
    )
    expect(wrapper.text()).toContain('地面托盘位')
    expect(wrapper.text()).toContain('物理托盘数')
    expect(wrapper.text()).toContain('5')
    expect(wrapper.text()).toContain('中间托盘')
    expect(wrapper.text()).toContain('第 1 托')
  })
})
