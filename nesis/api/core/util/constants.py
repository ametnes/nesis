import re

DEFAULT_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DEFAULT_DATE_FORMAT = "%Y-%m-%d"

DATETIME_FILTER_FORMAT = "%Y%m%d%H%M%S"

DATE_FILTER_FORMAT = "%Y%m%d"

TRANSACTION_UNIT_CREDIT = "usd/100000"

TRANSACTION_UNIT_DEBIT = "usd/100000/hour"

USD_TO_TRANSACTION_UNIT = 100000

USD_TO_CENTS_UNIT = 100

CACHE_SEPARATOR = "--"

UNIQUE_CONSTRAINT_STR = "unique constraint"

BEARER_PREFIX = "Bearer"

BASIC_PREFIX = "Basic"

UUID_PATTERN = re.compile(r"^[\da-fA-F]{8}-([\da-fA-F]{4}-){3}[\da-fA-F]{12}$")

DEFAULT_SAMBA_PORT = 445


class TOKEN_AUTH:
    AMETNES_GWT = "__agwt_key__"


class RESOURCE_STATUS:
    INIT = "INIT"
    READY = "READY"
    DELETED = "DELETED"
    TERMINATED = "TERMINATED"
    ERROR = "ERROR"


class TRANSACTION_DESC:
    SIGNUP_CREDIT = "SIGNUP_CREDIT"
    MANUAL_PAYMENT = "MANUAL_PAYMENT"
    AUTOMATIC_PAYMENT = "AUTOMATIC_PAYMENT"
    RESOURCE_USAGE_CHARGE = "RESOURCE_USAGE_CHARGE"


transaction_desc_summary_hr_map = {
    TRANSACTION_DESC.SIGNUP_CREDIT: "Payment",
    TRANSACTION_DESC.MANUAL_PAYMENT: "Payment",
    TRANSACTION_DESC.AUTOMATIC_PAYMENT: "Payment",
    TRANSACTION_DESC.RESOURCE_USAGE_CHARGE: "Resource Usage Charge",
}


class TRANSACTION_LIST_TYPE:
    DEFAULT = "default"
    SUMMARY = "summary"


class TRANSACTION_SUMMARY_TYPE:
    DAILY = "daily"
    MONTHLY = "monthly"


class INVOICE_STATUS:
    PENDING = "PENDING"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    ALREADY_PAID = "ALREADY_PAID"
    PAID = "PAID"


class CACHE_KEYS_NAME:
    PRODUCT = "/keys/product"
    PROJECT = "/keys/project"
    LOCATION = "/keys/location"
    ACCOUNT_LOCATION = "/keys/account_location"
    USER = "/keys/user"


class ACCOUNT_STATUS:
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELINQUENT = "delinquent"
    EXPIRED = "expired"


class ACCOUNT_PLAN:
    FREEMIUM = "freemium"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class SORT_ORDER:
    ASC = "asc"
    DESC = "desc"


class PAYMENT_TYPE:
    MANUAL_PAYMENT = "MANUAL_PAYMENT"
    AUTOMATIC_PAYMENT = "AUTOMATIC_PAYMENT"


class PAYMENT_STATUS:
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class COMMENT_TYPE:
    DELETE_ACCOUNT = "DELETE_ACCOUNT"


class USER_TYPE:
    SYSTEM = "system"
    DEFAULT = "default"
