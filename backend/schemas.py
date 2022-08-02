from datetime import datetime

from pydantic import BaseModel, Field


class DoneClockRequest(BaseModel):
    """
    DoneClock请求体

    参数来自 https://docs.hamibot.com/reference/hamibot#env
    """

    app_env: str
    user_id: str
    robot_id: str
    script_id: str
    timestamp: str  # "2021-02-03 04:05:06"
    direction: str  # "in" / "out"


class UserInfo(BaseModel):
    class Config:
        pass

    token: str
    user_id: str = Field(alias="userId")
    username: str = ""
    email: str = ""
    avatar_url: str = Field(alias="avatarUrl", default="")
    name: str = ""
    balance: int = 0
    role: str = "user"
    plan: str = "free"
    referral_code: str = Field(alias="referralCode", default="ctfa")
    referral_count: int = Field(alias="referralCount", default=0)


class RobotInfo(BaseModel):
    id: str = Field(alias="_id")
    user_id: str = Field(alias="userId", default="")
    online: bool = True
    version: str = ""
    brand: str = ""
    model: str = ""
    app_version_code: int = 0
    name: str = ""


class ScriptInfo(BaseModel):
    id: str = Field(alias="_id")
    user_id: str = Field(alias="userId", default="")
    name: str
    obfuscate: bool = False
    use_message: bool = Field(alias="useMessage", default=False)
    updated_at: datetime = Field(alias="updatedAt", default_factory=datetime)
    listing_slug: str = Field(alias="listingSlug", default="")
    configuration: dict = {}
    files: list = []


class InstallationInfo(BaseModel):
    id: str = Field(alias="_id")
    user_id: str = Field(alias="userId", default="")
    configuration: dict = {}
    plan: dict = {}
    has_update: bool = Field(alias="hasUpdate", default=False)
    settings: dict = {"autoUpdate": False, "autoRenew": False}
    slug: str = ""
    name: str = ""
    version: str = ""
    icon: str = ""
    use_for_task: bool = Field(alias="useForTask", default=False)
