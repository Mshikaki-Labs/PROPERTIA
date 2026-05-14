from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal

# Create your views here.
from django.shortcuts import render
from django.http import HttpResponse

from .models import Invoice, InvoicePayment
from properties.models import Property
from units.models import Unit
from tenants.models import Tenant
from payments.models import Payment
from PROPATIA.pagination import paginate_queryset

@login_required
def invoice_list(request):
    # Handle Single Invoice Generation
    if request.method == "POST" and 'single_generate' in request.POST:
        try:
            unit_id = request.POST.get('unit')
            due_date_str = request.POST.get('due_date')
            inv_type = request.POST.get('type')
            
            # Validate inputs
            if not unit_id or not due_date_str or not inv_type:
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__user=request.user).order_by('-due_date'),
                    'properties': Property.objects.filter(user=request.user),
                    'units': Unit.objects.filter(property__user=request.user),
                    'error': 'Please fill in all fields'
                })
            
            # Get unit
            unit = Unit.objects.get(id=unit_id, property__user=request.user)
            
            # Convert date string to datetime object
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            
            # Get tenant assigned to this unit
            tenant = unit.get_assigned_tenant()
            
            if not tenant:
                return render(request, 'invoices/invoices_view.html', {
                    'invoices': Invoice.objects.filter(unit__property__user=request.user).order_by('-due_date'),
                    'properties': Property.objects.filter(user=request.user),
                    'units': Unit.objects.filter(property__user=request.user),
                    'error': f'No tenant assigned to unit {unit.name}'
                })
            
            # Create invoice
            Invoice.objects.create(
                user=request.user,
                unit=unit,
                tenant=tenant,
                amount=unit.rent_amount,
                type=inv_type,
                due_date=due_date
            )
            
            return redirect('invoices:invoice_list')
        
        except Unit.DoesNotExist:
            return render(request, 'invoices/invoices_view.html', {
                'invoices': Invoice.objects.filter(unit__property__user=request.user).order_by('-due_date'),
                'properties': Property.objects.filter(user=request.user),
                'units': Unit.objects.filter(property__user=request.user),
                'error': 'Unit not found'
            })
        except Exception as e:
            return render(request, 'invoices/invoices_view.html', {
                'invoices': Invoice.objects.filter(unit__property__user=request.user).order_by('-due_date'),
                'properties': Property.objects.filter(user=request.user),
                'units': Unit.objects.filter(property__user=request.user),
                'error': f'Error creating invoice: {str(e)}'
            })
    
    # Handle Bulk Generation
    if request.method == "POST" and 'bulk_generate' in request.POST:
        prop_id = request.POST.get('property')
        due_date_str = request.POST.get('due_date')
        inv_type = request.POST.get('type')
        
        # Convert date string to datetime object
        due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        
        # Get all units for this property
        units = Unit.objects.filter(property_id=prop_id, property__user=request.user)
        
        for unit in units:
            # Check if unit has an assigned tenant
            tenant = unit.get_assigned_tenant()
            
            if tenant:
                # Create invoice with the unit's rent amount
                Invoice.objects.create(
                    user=request.user,
                    unit=unit,
                    tenant=tenant,
                    amount=unit.rent_amount,  # Use unit's rent amount
                    type=inv_type,
                    due_date=due_date
                )
        
        return redirect('invoices:invoice_list')

    invoices = Invoice.objects.filter(user=request.user).select_related('unit', 'unit__property', 'tenant').order_by('-due_date')
    selected_property = request.GET.get('property', '')
    selected_status = request.GET.get('status', '')

    if selected_property:
        invoices = invoices.filter(unit__property_id=selected_property)
    if selected_status:
        invoices = invoices.filter(status=selected_status)

    pagination = paginate_queryset(request, invoices)

    context = {
        'invoices': pagination['page_obj'],
        'properties': Property.objects.filter(user=request.user),
        'units': Unit.objects.filter(user=request.user),
        'selected_property': selected_property,
        'selected_status': selected_status,
    }
    context.update(pagination)
    return render(request, 'invoices/invoices_view.html', context)


@login_required
@require_POST
def delete_invoices(request):
    """Delete selected invoices."""
    invoice_ids = request.POST.getlist('invoice_ids[]')

    if not invoice_ids:
        return JsonResponse({'success': False, 'message': 'No invoices selected'})

    deleted_count, _ = Invoice.objects.filter(id__in=invoice_ids, user=request.user).delete()
    return JsonResponse({
        'success': True,
        'message': f'Successfully deleted {deleted_count} invoice(s)'
    })


def get_invoice_payments(request):
    """Get available payments for an invoice (AJAX endpoint)"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    invoice_id = request.GET.get('invoice_id')
    
    if not invoice_id:
        return JsonResponse({'success': False, 'message': 'Invoice ID required'})
    
    try:
        invoice = Invoice.objects.get(id=invoice_id)
        
        # Get unclaimed payments for the tenant of this invoice
        available_payments = Payment.objects.filter(
            tenant=invoice.tenant,
            status='unclaimed'
        ).values('id', 'amount', 'balance', 'date', 'code', 'description')
        
        # Calculate invoice balance
        remaining_balance = invoice.get_remaining_balance()
        
        return JsonResponse({
            'success': True,
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number,
            'invoice_amount': float(invoice.amount),
            'amount_paid': float(invoice.get_amount_paid()),
            'remaining_balance': float(remaining_balance),
            'payments': list(available_payments)
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_POST
def attach_payment_to_invoice(request):
    """Attach a payment to an invoice (handles partial payments)"""
    try:
        invoice_id = request.POST.get('invoice_id')
        payment_id = request.POST.get('payment_id')
        amount_to_apply = request.POST.get('amount_applied')
        
        if not all([invoice_id, payment_id, amount_to_apply]):
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        invoice = Invoice.objects.get(id=invoice_id)
        payment = Payment.objects.get(id=payment_id)
        
        # Validate payment belongs to invoice tenant
        if payment.tenant != invoice.tenant:
            return JsonResponse({'success': False, 'message': 'Payment does not match invoice tenant'})
        
        # Validate amount and convert to Decimal
        try:
            amount_applied = Decimal(str(amount_to_apply))
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
        
        if amount_applied <= 0:
            return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})
        
        # Check if payment balance can cover this amount
        if amount_applied > payment.balance:
            return JsonResponse({'success': False, 'message': f'Payment remaining balance KES {payment.balance} is less than requested KES {amount_applied}'})
        
        # Check if invoice attachment already exists
        existing = InvoicePayment.objects.filter(invoice=invoice, payment=payment).first()
        if existing:
            return JsonResponse({'success': False, 'message': 'Payment already attached to this invoice'})
        
        # Create the attachment
        invoice_payment = InvoicePayment.objects.create(
            invoice=invoice,
            payment=payment,
            amount_applied=amount_applied
        )
        
        # Update payment balance (now both are Decimal)
        payment.balance -= amount_applied
        
        # Update payment status to claimed only if balance is 0
        if payment.balance <= 0:
            payment.status = 'claimed'
        
        payment.save()
        
        # Update invoice status
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': f'Payment of KES {amount_applied} attached successfully',
            'remaining_balance': float(invoice.get_remaining_balance()),
            'payment_remaining': float(payment.balance),
            'new_status': invoice.status
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


def get_attached_payments(request):
    """Get all attached payments for an invoice"""
    try:
        invoice_id = request.GET.get('invoice_id')
        
        if not invoice_id:
            return JsonResponse({'success': False, 'message': 'Invoice ID is required'})
        
        invoice = Invoice.objects.get(id=invoice_id)
        attached_payments = InvoicePayment.objects.filter(invoice=invoice).select_related('payment')
        
        payments_list = []
        for ip in attached_payments:
            payments_list.append({
                'invoice_payment_id': ip.id,
                'amount': float(ip.payment.amount),
                'amount_applied': float(ip.amount_applied),
                'date': ip.payment.date.strftime('%Y-%m-%d'),
                'description': ip.payment.description or ''
            })
        
        return JsonResponse({
            'success': True,
            'attached_payments': payments_list
        })
    
    except Invoice.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


def _check_user_permission(user):
    """Check if user is admin or landlord"""
    if user is None or not user.is_authenticated:
        return False
    try:
        from accounts.models import Profile
        profile = Profile.objects.get(user=user)
        return profile.role in ['admin', 'landlord']
    except:
        return False


@require_POST
def update_invoice_payment(request):
    """Update amount applied for an invoice payment"""
    try:
        # Check permission
        if not _check_user_permission(request.user):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        invoice_payment_id = request.POST.get('invoice_payment_id')
        new_amount = request.POST.get('amount_applied')
        
        if not invoice_payment_id or not new_amount:
            return JsonResponse({'success': False, 'message': 'Missing required fields'})
        
        new_amount = Decimal(str(new_amount))
        invoice_payment = InvoicePayment.objects.get(id=invoice_payment_id)
        
        # Calculate the difference
        old_amount = invoice_payment.amount_applied
        difference = new_amount - old_amount
        
        # Check if payment has enough balance
        if difference > 0:
            if invoice_payment.payment.balance < difference:
                return JsonResponse({
                    'success': False, 
                    'message': f'Payment only has KES {invoice_payment.payment.balance} remaining'
                })
        
        # Update invoice payment amount
        invoice_payment.amount_applied = new_amount
        invoice_payment.save()
        
        # Update payment balance
        payment = invoice_payment.payment
        payment.balance -= difference
        
        # Update status
        if payment.balance <= 0:
            payment.status = 'claimed'
        else:
            payment.status = 'unclaimed'
        
        payment.save()
        
        # Update invoice status
        invoice = invoice_payment.invoice
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment amount updated successfully'
        })
    
    except InvoicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})


@require_POST
def remove_invoice_payment(request):
    """Remove an invoice payment attachment"""
    try:
        # Check permission
        if not _check_user_permission(request.user):
            return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
        
        invoice_payment_id = request.POST.get('invoice_payment_id')
        
        if not invoice_payment_id:
            return JsonResponse({'success': False, 'message': 'Invoice payment ID is required'})
        
        invoice_payment = InvoicePayment.objects.get(id=invoice_payment_id)
        
        # Get the amount before deletion
        amount_applied = invoice_payment.amount_applied
        payment = invoice_payment.payment
        invoice = invoice_payment.invoice
        
        # Delete the attachment
        invoice_payment.delete()
        
        # Restore payment balance
        payment.balance += amount_applied
        payment.status = 'unclaimed'
        payment.save()
        
        # Update invoice status
        invoice.update_status()
        
        return JsonResponse({
            'success': True,
            'message': 'Payment removed successfully'
        })
    
    except InvoicePayment.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Invoice payment not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
