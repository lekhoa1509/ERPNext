from pharma_vn.setup.custom_fields import create_custom_fields
from pharma_vn.setup.defaults import create_default_settings
from pharma_vn.setup.taxes import ensure_vietnam_tax_setup
from pharma_vn.setup.workflows import disable_sales_order_workflow
from pharma_vn.access_control.setup import ensure_access_control_defaults
from pharma_vn.hrm.service import ensure_hrm_setup


def after_install():
    after_migrate()


def after_migrate():
    create_custom_fields()
    create_default_settings()
    ensure_vietnam_tax_setup()
    ensure_access_control_defaults()
    disable_sales_order_workflow()
    ensure_hrm_setup()
