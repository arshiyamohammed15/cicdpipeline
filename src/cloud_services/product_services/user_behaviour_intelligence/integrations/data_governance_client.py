"""
Data Governance & Privacy (EPC-2) Integration Client for UBI Module (EPC-9).

What: Client for retention policies and data deletion
Why: Integrate with Data Governance per PRD FR-8
Reads/Writes: Data Governance API calls
Contracts: Data Governance PRD, UBI PRD FR-8
Risks: Data Governance unavailability, deletion failures
"""

import logging
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..dependencies import MockM22DataGovernance
from ..main import get_data_governance_instance

logger = logging.getLogger(__name__)


class DataGovernanceClient:
    """
    Data Governance client for retention policies and data deletion.

    Per UBI PRD FR-8:
    - Retention policy query: GET /privacy/v1/retention/policies
    - Data deletion callback: POST /privacy/v1/retention/delete
    - Privacy classification: POST /privacy/v1/classification
    """

    def __init__(self, base_url: Optional[str] = None, timeout_seconds: float = 5.0):
        """
        Initialize Data Governance client.

        Args:
            base_url: Data Governance service base URL (None for mock)
            timeout_seconds: Request timeout
        """
        self.base_url = base_url
        self.timeout = timeout_seconds
        self.use_mock = base_url is None
        
        if self.use_mock:
            self.data_governance = get_data_governance_instance()
        else:
            self.data_governance = None

    async def get_retention_policies(self, tenant_id: str) -> List[Dict[str, Any]]:
        """
        Get retention policies for tenant.

        Args:
            tenant_id: Tenant identifier

        Returns:
            List of retention policy dictionaries
        """
        if self.use_mock:
            return await self.data_governance.get_retention_policies(tenant_id)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.base_url}/privacy/v1/retention/policies",
                    params={"tenant_id": tenant_id}
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error getting retention policies: {e}")
            return []

    async def delete_data(
        self,
        tenant_id: str,
        time_range: Dict[str, str]
    ) -> bool:
        """
        Delete data for tenant within time range.

        Args:
            tenant_id: Tenant identifier
            time_range: Time range dictionary with 'from' and 'to' ISO 8601 timestamps

        Returns:
            True if deletion successful, False otherwise
        """
        if self.use_mock:
            return await self.data_governance.delete_data(tenant_id, time_range)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/privacy/v1/retention/delete",
                    params={"tenant_id": tenant_id},
                    json=time_range
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Error deleting data: {e}")
            return False

    async def classify_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify data for privacy.

        Args:
            data: Data dictionary to classify

        Returns:
            Classification result with privacy tags
        """
        if self.use_mock:
            return await self.data_governance.classify_data(data)
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/privacy/v1/classification",
                    json=data
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Error classifying data: {e}")
            return {"classification_level": "internal", "privacy_tags": []}

