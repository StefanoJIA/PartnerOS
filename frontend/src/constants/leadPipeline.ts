/** Sales stage pipeline; values match backend LeadStage / `LEAD_STAGES` in statusEnums. */
import { LEAD_STAGES } from './statusEnums'

export const LEAD_PIPELINE_STAGES = LEAD_STAGES

export type LeadPipelineStage = (typeof LEAD_PIPELINE_STAGES)[number]
