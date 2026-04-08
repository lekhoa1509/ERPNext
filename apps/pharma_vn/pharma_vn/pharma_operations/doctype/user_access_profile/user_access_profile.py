from frappe.model.document import Document

from pharma_vn.access_control.service import refresh_profile_resolution


class UserAccessProfile(Document):
    def validate(self):
        refresh_profile_resolution(self)
