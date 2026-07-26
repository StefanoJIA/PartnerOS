from app.models.ai_kb import AIOutput, KbChunk, KbDocument
from app.models.auth import Role, User
from app.models.benchmark_knowledge import (
    BenchmarkBrand,
    BenchmarkDataRights,
    BenchmarkProductCapability,
    BenchmarkSourceReference,
)
from app.models.common import ActivityLog, File, FileAttachment, Note, ObjectTag, OrderResource, Tag
from app.models.crm import Company, Contact, Interaction, Lead, OutreachTemplate, Task
from app.models.enrichment import (
    CompanyEnrichmentRun,
    CompanyEnrichmentSource,
    CompanyEnrichmentSuggestion,
)
from app.models.field_visits import FieldVisitPlan, FieldVisitTarget
from app.models.feedback import FeedbackTicket
from app.models.external_execution import ExternalExecutionAction
from app.models.growth import GrowthCampaign, GrowthCampaignTask, SalesOpportunity
from app.models.market import MarketIntelligenceItem
from app.models.market_response import MarketResponseReview
from app.models.orders import Order, OrderItem, ProductionMilestone, ShippingRecord
from app.models.platform_intelligence import ChannelIntelligenceMetric, PlatformBenchmarkRecord
from app.models.project_request_candidates import ProjectRequestSupplierCandidate
from app.models.partners import ManufacturingPartner, PartnerCapability, PartnerContact
from app.models.products import Product, ProductCategory, ProductDocument, ProductPartnerLink
from app.models.supplier_discovery import SupplierDiscoveryRecord
from app.models.supplier_sample_evaluations import SupplierSampleEvaluation
from app.models.supplier_selection_snapshots import SupplierSelectionSnapshot
from app.models.quality import FactoryAudit, QualityDocument
from app.models.customer_orders import (
    CustomerOrder,
    OrderConfirmation,
    OrderLineItem,
    OrderPartnerSplit,
    OrderProductionMilestone,
    ShipmentPlan,
    ShipmentTrackingEvent,
    SupplierConfirmation,
)
from app.models.customer_quotes import (
    Quote,
    QuoteAdjustment,
    QuoteDeliveryLog,
    QuoteLineItem,
    QuoteLearningRecord,
    QuotePdfExport,
    QuoteTerms,
    QuoteVersion,
)
from app.models.daily_queue import DailyQueueHandlingRecord
from app.models.quote_catalog import (
    FxRate,
    MarginStrategyTier,
    PricingAssumption,
    ProductCatalog,
    ProductCostModel,
    ProductPriceTier,
)
from app.models.commercial_pilot import CategoryCoverageAssessment, CommercialPilotRun, SupplierDevelopmentTask
from app.models.customer_project_requests import CustomerProjectRequest
from app.models.rfq import Quotation, QuotationItem, RFQ, RFQItem, RFQPartnerCandidate
from app.models.samples import Sample, SampleShipment

__all__ = [
    "AIOutput",
    "BenchmarkBrand",
    "BenchmarkDataRights",
    "BenchmarkProductCapability",
    "BenchmarkSourceReference",
    "ChannelIntelligenceMetric",
    "CategoryCoverageAssessment",
    "CommercialPilotRun",
    "ActivityLog",
    "Company",
    "CompanyEnrichmentRun",
    "CompanyEnrichmentSource",
    "CompanyEnrichmentSuggestion",
    "Contact",
    "CustomerProjectRequest",
    "CustomerOrder",
    "DailyQueueHandlingRecord",
    "ExternalExecutionAction",
    "FactoryAudit",
    "FeedbackTicket",
    "FxRate",
    "FieldVisitPlan",
    "FieldVisitTarget",
    "File",
    "FileAttachment",
    "GrowthCampaign",
    "GrowthCampaignTask",
    "Interaction",
    "KbChunk",
    "KbDocument",
    "Lead",
    "ManufacturingPartner",
    "MarginStrategyTier",
    "MarketIntelligenceItem",
    "MarketResponseReview",
    "Note",
    "ObjectTag",
    "OrderResource",
    "Order",
    "OrderConfirmation",
    "OrderItem",
    "OrderLineItem",
    "OrderPartnerSplit",
    "OrderProductionMilestone",
    "OutreachTemplate",
    "PlatformBenchmarkRecord",
    "ProjectRequestSupplierCandidate",
    "PartnerCapability",
    "PartnerContact",
    "ProductionMilestone",
    "Product",
    "ProductCatalog",
    "PricingAssumption",
    "ProductCategory",
    "ProductCostModel",
    "ProductPriceTier",
    "ProductDocument",
    "ProductPartnerLink",
    "QualityDocument",
    "Quote",
    "QuoteAdjustment",
    "QuoteLineItem",
    "QuoteLearningRecord",
    "QuotePdfExport",
    "QuoteDeliveryLog",
    "QuoteTerms",
    "QuoteVersion",
    "Quotation",
    "QuotationItem",
    "RFQ",
    "RFQItem",
    "RFQPartnerCandidate",
    "Role",
    "SupplierDiscoveryRecord",
    "SupplierDevelopmentTask",
    "SupplierSampleEvaluation",
    "SupplierSelectionSnapshot",
    "Sample",
    "SampleShipment",
    "SalesOpportunity",
    "ShippingRecord",
    "ShipmentPlan",
    "ShipmentTrackingEvent",
    "SupplierConfirmation",
    "Tag",
    "Task",
    "User",
]
