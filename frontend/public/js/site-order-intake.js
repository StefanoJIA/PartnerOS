/** Shared customer-site order intake response handling (demo / non-persisted). */

function handleSiteOrderIntakeResponse(data) {
  if (!data || typeof data !== 'object') {
    return {
      kind: 'error',
      message: 'Unexpected server response.',
    };
  }
  if (
    data.intake_type === 'project_request' ||
    data.status === 'project_request_submitted' ||
    (data.request_reference && data.order_created === false)
  ) {
    return {
      kind: 'project_request',
      message:
        data.message ||
        `项目需求已提交，参考号 ${data.request_reference || '—'}。这不是正式订单确认，运营团队将审核后跟进报价。`,
      requestReference: data.request_reference,
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
