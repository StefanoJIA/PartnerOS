/** Shared customer-site order intake response handling (demo / non-persisted). */

function handleSiteOrderIntakeResponse(data) {
  if (!data || typeof data !== 'object') {
    return {
      kind: 'error',
      message: 'Unexpected server response.',
    };
  }
  if (data.order_created === false || data.status === 'draft_intake_not_persisted' || !data.order_number) {
    return {
      kind: 'demo_intake',
      message:
        data.message ||
        '演示/意向提交已收到，尚未写入正式订单。请通过报价确认后再由运营创建订单。',
    };
  }
  return {
    kind: 'success',
    message: `Order created successfully! Order Number: ${data.order_number}`,
    orderNumber: data.order_number,
  };
}
