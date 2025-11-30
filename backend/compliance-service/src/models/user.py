from ..shared.database.manager import BaseModel


class KYCVerification(BaseModel):
    table_name = "kyc_verifications"


class AMLCheck(BaseModel):
    table_name = "aml_checks"


class SanctionsScreening(BaseModel):
    table_name = "sanctions_screening"


class ComplianceReport(BaseModel):
    table_name = "compliance_reports"
