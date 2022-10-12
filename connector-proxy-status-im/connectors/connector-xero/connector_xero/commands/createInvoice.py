"""CreateInvoice."""
import json
from datetime import datetime
from datetime import timedelta

from xero_python.accounting import AccountingApi  # type: ignore
from xero_python.accounting import Contact
from xero_python.accounting import Invoice
from xero_python.accounting import Invoices
from xero_python.accounting import LineItem
from xero_python.api_client import ApiClient  # type: ignore
from xero_python.api_client.configuration import Configuration  # type: ignore
from xero_python.api_client.oauth2 import OAuth2Token  # type: ignore
from xero_python.api_client.serializer import serialize  # type: ignore
from xero_python.identity import IdentityApi  # type: ignore

#
# Sample response
#

# {
#     "Invoices": [
#         {
#             "AmountDue": 21.85,
#             "AmountPaid": 0.0,
#             "BrandingThemeID": "324587a9-7eed-46c0-ad64-fa941a1b5b3e",
#             "Contact": {
#                 "Addresses": [
#                     {
#                         "AddressLine1": "79 Madison Ave, Fl 2",
#                         "AddressLine2": "",
#                         "AddressLine3": "",
#                         "AddressLine4": "",
#                         "AddressType": "STREET",
#                         "AttentionTo": "",
#                         "City": "New York",
#                         "Country": "USA",
#                         "PostalCode": "10016",
#                         "Region": "NY"
#                     },
#                     {
#                         "AddressLine1": "Nairn Towers, 901",
#                         "AddressLine2": "120-130 Flinders Street",
#                         "AddressType": "POBOX",
#                         "AttentionTo": "",
#                         "City": "Oaktown",
#                         "Country": "",
#                         "PostalCode": "89012",
#                         "Region": "NY"
#                     }
#                 ],
#                 "BankAccountDetails": "",
#                 "ContactGroups": [
#                     {
#                         "ContactGroupID": "1b979d15-4ad9-42d7-8111-85b990477df0",
#                         "Contacts": [],
#                         "Name": "Training",
#                         "Status": "ACTIVE"
#                     }
#                 ],
#                 "ContactID": "375ac066-85a0-4044-a8be-3159856d5c85",
#                 "ContactPersons": [],
#                 "ContactStatus": "ACTIVE",
#                 "EmailAddress": "info@rexmedia.co",
#                 "FirstName": "",
#                 "HasAttachments": false,
#                 "HasValidationErrors": false,
#                 "IsCustomer": true,
#                 "IsSupplier": false,
#                 "LastName": "",
#                 "Name": "Rex Media Group",
#                 "Phones": [
#                     {
#                         "PhoneAreaCode": "",
#                         "PhoneCountryCode": "",
#                         "PhoneNumber": "",
#                         "PhoneType": "DDI"
#                     },
#                     {
#                         "PhoneAreaCode": "",
#                         "PhoneCountryCode": "",
#                         "PhoneNumber": "",
#                         "PhoneType": "FAX"
#                     },
#                     {
#                         "PhoneAreaCode": "",
#                         "PhoneCountryCode": "",
#                         "PhoneNumber": "",
#                         "PhoneType": "MOBILE"
#                     },
#                     {
#                         "PhoneAreaCode": "201",
#                         "PhoneCountryCode": "",
#                         "PhoneNumber": "5556789",
#                         "PhoneType": "DEFAULT"
#                     }
#                 ],
#                 "PurchasesTrackingCategories": [],
#                 "SalesTrackingCategories": [],
#                 "UpdatedDateUTC": "/Date(1663005822390+0000)/"
#             },
#             "CurrencyCode": "USD",
#             "CurrencyRate": 1.0,
#             "Date": "/Date(1602288000000)/",
#             "DueDate": "/Date(1603843200000)/",
#             "HasAttachments": false,
#             "HasErrors": false,
#             "InvoiceID": "119f7d2e-0598-4dbb-823b-6f6d89823369",
#             "InvoiceNumber": "INV-0074",
#             "IsDiscounted": false,
#             "LineAmountTypes": "Exclusive",
#             "LineItems": [
#                 {
#                     "AccountCode": "400",
#                     "Description": "Foobar",
#                     "LineAmount": 20.0,
#                     "LineItemID": "b3c5b459-2b91-4b00-8c94-b691f54ab464",
#                     "Quantity": 1.0,
#                     "TaxAmount": 1.85,
#                     "TaxType": "OUTPUT",
#                     "Tracking": [],
#                     "UnitAmount": 20.0
#                 }
#             ],
#             "Overpayments": [],
#             "Prepayments": [],
#             "Reference": "Website Design",
#             "SentToContact": false,
#             "Status": "AUTHORISED",
#             "SubTotal": 20.0,
#             "Total": 21.85,
#             "TotalTax": 1.85,
#             "Type": "ACCREC",
#             "UpdatedDateUTC": "/Date(1663261898297+0000)/"
#         }
#     ]
# }


class CreateInvoice:
    """CreateInvoice."""

    def __init__(
        self,
        access_token,
        description: str,
        contact_name: str,
        contact_email: str,
        amount: str,
        # reference: str,
        # created_date: str,
        # due_date: str,
        # account_code: str,
    ):
        """__init__."""
        self.access_token = access_token
        self.description = description
        self.contact_name = contact_name
        self.contact_email = contact_email
        self.amount = amount

    def execute(self, config, task_data):
        """Creates an invoice in xero."""
        client_id = config["XERO_CLIENT_ID"]
        client_secret = config["XERO_CLIENT_SECRET"]

        access_token = json.loads(self.access_token)

        api_client = ApiClient(
            Configuration(
                debug=True,
                oauth2_token=OAuth2Token(
                    client_id=client_id, client_secret=client_secret
                ),
            ),
            pool_threads=1,
        )

        @api_client.oauth2_token_getter
        def obtain_xero_oauth2_token():
            """Obtain_xero_oauth2_token."""
            return access_token

        @api_client.oauth2_token_saver
        def store_xero_oauth2_token(token):
            """Store_xero_oauth2_token."""
            access_token = token  # noqa

        api_instance = AccountingApi(api_client)
        summarize_errors = "True"
        unitdp = 2
        date_value = datetime.now()
        due_date_value = date_value + timedelta(days=7)

        contact = Contact(name=self.contact_name, email_address=self.contact_email)

        line_item = LineItem(
            description=self.description,
            quantity=1.0,
            unit_amount=self.amount,
            account_code="400",
            tracking=[],
        )

        line_items = []
        line_items.append(line_item)

        invoice = Invoice(
            type="ACCREC",
            contact=contact,
            date=date_value,
            due_date=due_date_value,
            line_items=line_items,
            reference="Created by SpiffWorkflow",
            status="AUTHORISED",
        )

        invoices = Invoices(invoices=[invoice])

        try:
            xero_tenant_id = self._get_xero_tenant_id(api_client, access_token)
            created_invoices = api_instance.create_invoices(
                xero_tenant_id, invoices, summarize_errors, unitdp
            )
            response = json.dumps(serialize(created_invoices))
            status = 200
        except Exception as e:
            # TODO better error logging/reporting in debug
            response = f'{{ "error": "{e.reason}" }}'
            status = 500

        return {"response": response, "status": status, "mimetype": "application/json"}

    def _get_xero_tenant_id(self, api_client, token):
        """_get_xero_tenant_id."""
        if not token:
            return None

        identity_api = IdentityApi(api_client)
        for connection in identity_api.get_connections():
            if connection.tenant_type == "ORGANISATION":
                return connection.tenant_id
