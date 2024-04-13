from django.shortcuts import render
from django.http import JsonResponse
import requests
from datetime import datetime
import uuid
import json

class WaafiPayIntegrationView(View):
    #below are the API access credentials
    base_url = "https://api.waafipay.com/asm"
    merchant_uid = "MARCHANT_UID"
    api_user_id = "API_USER_ID"
    api_key = "API_PASSWORD"


    #This code assumes you have a Django project set up and a transaction_form.html template in your templates directory

    def show_transaction_form(self, request):
        return render(request, 'transaction_form.html')

    #Pre-authorization also known as an authorization hold is a practice by which the WaafiPay API allows you to place a hold on an amount approved as part of a transaction. 
    #The WaafiPay essentially holds that part of the customer's balance in reserve for a while until you clear the transaction.
    def preauthorize_transaction(self, request):
        if request.method == 'POST':
            account_no = request.POST.get('account_no')
            amount = request.POST.get('amount')
            invoice_id = request.POST.get('invoice_id')
            #You can add any other request data from the form as required

            # Prepare request data
            request_data = {
                "schemaVersion": "1.0",
                "requestId": str(uuid.uuid4()),  # Unique request ID
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "channelName": "WEB",
                "serviceName": "API_PREAUTHORIZE",
                "serviceParams": {
                    "merchantUid": self.merchant_uid,
                    "apiUserId": self.api_user_id,
                    "apiKey": self.api_key,
                    "paymentMethod": "MWALLET_ACCOUNT",
                    "payerInfo": {
                        "accountNo": account_no
                    },
                    "transactionInfo": {
                        "referenceId": str(uuid.uuid4()),  # Unique reference ID
                        "invoiceId": invoice_id,
                        "amount": "{:.2f}".format(float(amount)),
                        "currency": "USD",
                        "description": "test"
                    }
                }
            }

            # Send request to WaafiPay API
            response = requests.post(self.base_url, json=request_data)

            # Handle response
            response_data = response.json()
            if response_data['responseCode'] == '2001':
                if response_data['params']['state'] == 'APPROVED':
                    # Payment is approved, commit the transaction
                    self.commit_transaction(response_data['requestId'], response_data['timestamp'], response_data['params']['transactionId'], response_data['params']['referenceId'])
                else:
                    # Handle other states if needed
                    pass
            else:
                #If the customer's account balance is not sufficient or the customer rejects the payment or even he losses the connection
                # Transaction failed, handle the error
                error_response = {
                    'message': response_data['responseMsg'],
                    'error_code': response_data['errorCode'],
                    'order_id': response_data['params']['orderId'] if 'orderId' in response_data['params'] else None,
                    'description': response_data['params']['description'] if 'description' in response_data['params'] else None,
                }
                return JsonResponse(error_response, status=400)

            # Return the response
            return JsonResponse(response_data)
        
    #If you sent your payment PreAuthorize and then commit it the payment is fully 
    #PreAuthorized and following things will heppen:
    # 1. Commits the original transaction done by PreAuthorize service.
    #  2. Deducts funds from customer account including charges  

    def commit_transaction(self, request_id, timestamp, transaction_id, reference_id):
        # Prepare request data
        request_data = {
            "schemaVersion": "1.0",
            "requestId": str(uuid.uuid4()),  # Unique request ID
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "channelName": "WEB",
            "serviceName": "API_PREAUTHORIZE_COMMIT",
            "serviceParams": {
                "merchantUid": self.merchant_uid,
                "apiUserId": self.api_user_id,
                "apiKey": self.api_key,
                "transactionId": transaction_id,
                "description": "Commited",
                "referenceId": reference_id
            }
        }

        # Send request to WaafiPay API
        response = requests.post(self.base_url, json=request_data)

        # Handle response
        response_data = response.json()
        if response_data['responseCode'] == '2001':
            # Transaction is successfully committed
            # Update your application accordingly including any database updates
            pass
        else:
            # Transaction commit failed, handle the error
            # You can log the error or return an appropriate response
            pass

        # Return the response
        return JsonResponse(response_data)

    #If you sent your payment PreAuthorize and then commit it and you want to cancel the
    #payment this request would be cancel it and the following things happen:
    # 1. Cancels the original transaction done by PreAuthorize service
    # 2. Returns the funds to customer account
    def cancel_transaction(self, transaction_id):
        # Prepare request data
        request_data = {
            "schemaVersion": "1.0",
            "requestId": str(uuid.uuid4()),  # Unique request ID
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "channelName": "WEB",
            "serviceName": "API_PREAUTHORIZE_CANCEL",
            "serviceParams": {
                "merchantUid": self.merchant_uid,
                "apiUserId": self.api_user_id,
                "apiKey": self.api_key,
                "transactionId": transaction_id,
                "description": "Cancel Transaction",
                "referenceId": str(uuid.uuid4())  # Unique reference ID
            }
        }

        # Send request to WaafiPay API
        response = requests.post(self.base_url, json=request_data)

        # Handle response
        response_data = response.json()
        if response_data['responseCode'] == '2001':
            # Transaction is successfully cancelled
            # Update your application accordingly including any database updates
            pass
        else:
            # Transaction cancellation failed, handle the error
            # You can log the error or return an appropriate response
            pass

        # Return the response
        return JsonResponse(response_data)
