from app.models.ai_kb import AIOutput, KbChunk, KbDocument
from app.models.auth import Role, User
from app.models.common import ActivityLog, File, FileAttachment, Note, ObjectTag, Tag
from app.models.crm import Company, Contact, Interaction, Lead, OutreachTemplate, Task
from app.models.enrichment import (
    CompanyEnrichmentRun,
    CompanyEnrichmentSource,
    CompanyEnrichmentSuggestion,
)
from app.models.field_visits import FieldVisitPlan, FieldVisitTarget
from app.models.market import MarketIntelligenceItem
from app.models.orders import Order, OrderItem, ProductionMilestone, ShippingRecord
from app.models.partners import ManufacturingPartner, PartnerCapability, PartnerContact
from app.models.products import Product, ProductCategory, ProductDocument, ProductPartnerLink
from app.models.quality import FactoryAudit, QualityDocument
from app.models.customer_quotes import (
    Quote,
    QuoteAdjustment,
    QuoteLineItem,
    QuotePdfExport,
    QuoteTerms,
    QuoteVersion,
)
from app.models.quote_catalog import (
    FxRate,
    MarginStrategyTier,
    ProductCatalog,
    ProductCostModel,
    ProductPriceTier,
)
from app.models.rfq import Quotation, QuotationItem, RFQ, RFQItem, RFQPartnerCandidate
from app.models.samples import Sample, SampleShipment

__all__ = [
    "AIOutput",
    "ActivityLog",
    "Company",
    "CompanyEnrichmentRun",
    "CompanyEnrichmentSource",
    "CompanyEnrichmentSuggestion",
    "Contact",
    "FactoryAudit",
    "FxRate",
    "FieldVisitPlan",
    "FieldVisitTarget",
    "File",
    "FileAttachment",
    "Interaction",
    "KbChunk",
    "KbDocument",
    "Lead",
    "ManufacturingPartner",
    "MarginStrategyTier",
    "MarketIntelligenceItem",
    "Note",
    "ObjectTag",
    "Order",
    "OrderItem",
    "OutreachTemplate",
    "PartnerCapability",
    "PartnerContact",
    "ProductionMilestone",
    "Product",
    "ProductCatalog",
    "ProductCategory",
    "ProductCostModel",
    "ProductPriceTier",
    "ProductDocument",
    "ProductPartnerLink",
    "QualityDocument",
    "Quote",
    "QuoteAdjustment",
    "QuoteLineItem",
    "QuotePdfExport",
    "QuoteTerms",
    "QuoteVersion",
    "Quotation",
    "QuotationItem",
    "RFQ",
    "RFQItem",
    "RFQPartnerCandidate",
    "Role",
    "Sample",
    "SampleShipment",
    "ShippingRecord",
    "Tag",
    "Task",
    "User",
]
