from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
import re


class HouseListing(BaseModel):
    address: str = Field(description="The full street address of the property")
    price: str = Field(description="The listed sale price of the home, e.g., '$450,000'")
    beds: Optional[int] = Field(None, description="Number of bedrooms")
    baths: Optional[float] = Field(None, description="Number of bathrooms")
    sqft: Optional[int] = Field(None, description="Square footage of the home")
    url: str = Field(description="The direct Zillow URL for the property")

    @field_validator("price")
    @classmethod
    def filter_price_ceilings(cls, value: str) -> str:
        """
        RPA Guardrail: Hard-enforces a maximum price cap of $500,000.
        Strips out currency formatting characters and drops any luxury outliers.
        """
        # Strip out '$', ',' and any trailing whitespace
        clean_numeric_string = re.sub(r'[^\d]', '', value)

        if clean_numeric_string:
            numeric_price = int(clean_numeric_string)
            # Fail validation if the property hits or exceeds our $500k budget ceiling
            if numeric_price >= 500000:
                raise ValueError(f"Property price {value} meets or exceeds the strict $500,000 maximum cap constraint.")

        return value


class ZillowDataPayload(BaseModel):
    listings: List[HouseListing]