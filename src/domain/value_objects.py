from pydantic import BaseModel, Field, field_validator


class HotnessScore(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    unexpectedness: float = Field(default=0.0, ge=0.0, le=1.0)
    materiality: float = Field(default=0.0, ge=0.0, le=1.0)
    velocity: float = Field(default=0.0, ge=0.0, le=1.0)
    breadth: float = Field(default=0.0, ge=0.0, le=1.0)
    credibility: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("HotnessScore must be between 0 and 1")
        return v


class SourceReputation(BaseModel):
    source_name: str
    reputation_score: float = Field(ge=0.0, le=1.0)
    trust_level: str = Field(default="unknown")
    verification_count: int = Field(default=0)

    @field_validator("trust_level")
    @classmethod
    def validate_trust_level(cls, v: str) -> str:
        allowed = ["high", "medium", "low", "unknown"]
        if v not in allowed:
            raise ValueError(f"trust_level must be one of {allowed}")
        return v

