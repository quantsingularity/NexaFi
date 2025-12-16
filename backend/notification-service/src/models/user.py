from database.manager import BaseModel


class Notification(BaseModel):
    table_name = "notifications"


class NotificationPreferences(BaseModel):
    table_name = "notification_preferences"


class NotificationTemplate(BaseModel):
    table_name = "notification_templates"
