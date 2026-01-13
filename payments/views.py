import razorpay
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Payment

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    PLAN_PRICES = {
        'pro_monthly': 14900,  # 149 INR
        'lifetime': 49900      # 499 INR
    }

    def post(self, request):
        plan_type = request.data.get('plan_type')
        
        if not plan_type or plan_type not in self.PLAN_PRICES:
            return Response({'error': 'Invalid or missing plan_type. Choose "pro_monthly" or "lifetime".'}, status=status.HTTP_400_BAD_REQUEST)

        amount_paise = self.PLAN_PRICES[plan_type]
        amount_inr = amount_paise / 100

        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            
            data = {
                'amount': amount_paise,
                'currency': 'INR',
                'payment_capture': '1',  # Auto capture
                'notes': {
                    'plan_type': plan_type,
                    'user_id': request.user.id
                }
            }
            order = client.order.create(data=data)
            
            # Create Payment record
            Payment.objects.create(
                user=request.user,
                razorpay_order_id=order['id'],
                amount=amount_inr,
                plan_type=plan_type,
                status='pending'
            )
            
            return Response({
                'order_id': order['id'],
                'amount': amount_inr,
                'currency': 'INR',
                'key': settings.RAZORPAY_KEY_ID,
                'plan_type': plan_type
            })
        except Exception as e:
            # Log the error for debugging
            print(f"Error in CreateOrderView: {e}") 
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response({'error': 'Missing required parameters'}, status=status.HTTP_400_BAD_REQUEST)

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        try:
            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)

            # Update Payment status
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.razorpay_payment_id = razorpay_payment_id
                payment.razorpay_signature = razorpay_signature
                payment.status = 'success'
                payment.save()
                
                # Upgrade user account
                user = request.user
                if payment.plan_type == 'lifetime':
                    user.user_tier = 'lifetime'
                    user.plan_type = 'lifetime'
                    user.subscription_expiry = None
                elif payment.plan_type == 'pro_monthly':
                    user.user_tier = 'pro'
                    user.plan_type = 'pro_monthly'
                    # If user has existing valid subscription, extend from that date
                    # Otherwise, start from now
                    now = timezone.now()
                    if user.subscription_expiry and user.subscription_expiry > now:
                        # Extend from current expiry (renewal case)
                        user.subscription_expiry = user.subscription_expiry + timezone.timedelta(days=30)
                    else:
                        # New subscription or expired - start from now
                        user.subscription_expiry = now + timezone.timedelta(days=30)
                
                user.save(update_fields=['user_tier', 'plan_type', 'subscription_expiry'])
                
            except Payment.DoesNotExist:
                 return Response({'error': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

            return Response({'status': 'Payment verified successfully'})
        except razorpay.errors.SignatureVerificationError:
            # Update Payment status to failed
            try:
                payment = Payment.objects.get(razorpay_order_id=razorpay_order_id)
                payment.status = 'failed'
                payment.save()
            except Payment.DoesNotExist:
                pass
            return Response({'error': 'Payment verification failed'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
