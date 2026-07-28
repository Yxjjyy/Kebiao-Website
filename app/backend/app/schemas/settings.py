from pydantic import BaseModel, ConfigDict, Field


class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    timezone: str
    week_start: int
    currency_symbol: str
    generate_weeks_ahead: int
    default_duration_hours: float
    visible_time_start: str
    visible_time_end: str
    theme: str


class SettingsUpdate(BaseModel):
    currency_symbol: str | None = Field(default=None, max_length=4)
    generate_weeks_ahead: int | None = Field(default=None, ge=1, le=52)
    default_duration_hours: float | None = Field(default=None, gt=0, le=12)
    visible_time_start: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    visible_time_end: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    theme: str | None = Field(default=None, pattern=r"^(auto|light|dark)$")


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    display_name: str
    avatar_color: str


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, max_length=64)
    avatar_color: str | None = Field(default=None, pattern=r"^#[0-9A-Fa-f]{6}$")
