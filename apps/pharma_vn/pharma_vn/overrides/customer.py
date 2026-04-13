from erpnext.selling.doctype.customer.customer import Customer

from pharma_vn.customer_naming import apply_customer_naming, ensure_unique_customer_identity


class PharmaVNCustomer(Customer):
    def autoname(self):
        apply_customer_naming(self)

    def validate(self):
        super().validate()
        ensure_unique_customer_identity(self)
