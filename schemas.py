from enum import Enum
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field

class TestCategory(str, Enum):
    HAPPY_PATH = "HAPPY_PATH"
    BOUNDARY = "BOUNDARY"
    SECURITY_ADVERSARIAL = "SECURITY_ADVERSARIAL"

class TestCase(BaseModel):
    test_id: str = Field(description="Unique ID, e.g., TEST-USER-POST-01")
    endpoint: str = Field(description="Endpoint path, e.g., /users")
    method: str = Field(description="HTTP method in uppercase")
    category: TestCategory
    headers: Dict[str, str] = Field(default_factory=dict)
    query_params: Dict[str, Any] = Field(default_factory=dict)
    body: Optional[Dict[str, Any]] = None
    expected_status_codes: List[int] = Field(description="List of valid HTTP status codes")
    description: str = Field(description="Purpose of the test case")

class EndpointTestSuite(BaseModel):
    endpoint: str
    method: str
    test_cases: List[TestCase]