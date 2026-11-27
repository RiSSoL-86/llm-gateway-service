from pydantic import BaseModel, ConfigDict


class PermissiveModel(BaseModel):
    """A model that keeps unknown fields instead of dropping them."""

    model_config = ConfigDict(extra="allow")
