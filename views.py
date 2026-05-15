   
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .decorators import role_required
from .forms import (
    RepairRequestForm,
    RepairRequestStatusForm,
    MaintenanceUpdateForm,
)
from .models import (
    RepairRequest, Notification, Community, Dwelling, Role,
)

logger = logging.getLogger('housing')

                                                                           
@login_required
def dashboard(request):
                                              
    user = request.user
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None

    base_qs = RepairRequest.objects.select_related('dwelling__community')

    if user.is_superuser or role == Role.ADMIN:
        visible = base_qs.all()
    elif role == Role.HOUSING_OFFICER and profile and profile.community:
        visible = base_qs.filter(dwelling__community=profile.community)
    elif role == Role.MAINTENANCE_SUPERVISOR:
        visible = base_qs.filter(
            Q(assigned_to=user)
            | Q(status__in=[RepairRequest.Status.OPEN, RepairRequest.Status.ASSIGNED])
        )
    elif role == Role.COMMUNITY_MANAGER and profile and profile.community:
        visible = base_qs.filter(dwelling__community=profile.community)
    elif role == Role.TENANT:
        visible = base_qs.filter(raised_by=user)
    else:
        visible = base_qs.none()

    stats = visible.aggregate(
        total=Count('pk'),
        open=Count('pk', filter=Q(status=RepairRequest.Status.OPEN)),
        in_progress=Count('pk', filter=Q(status=RepairRequest.Status.IN_PROGRESS)),
        completed=Count('pk', filter=Q(status=RepairRequest.Status.COMPLETED)),
        urgent=Count('pk', filter=Q(priority=RepairRequest.Priority.URGENT)),
    )

    context = {
        'role': role,
        'stats': stats,
        'recent_requests': visible.order_by('-created_at')[:8],
        'communities_count': Community.objects.count(),
        'dwellings_count': Dwelling.objects.count(),
    }
    return render(request, 'housing/dashboard.html', context)


                                                                             
                    
                                                                             
@login_required
def repair_request_list(request):
                                              
    user = request.user
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None
    qs = RepairRequest.objects.select_related('dwelling__community', 'raised_by')

    if user.is_superuser or role == Role.ADMIN:
        pass
    elif role == Role.HOUSING_OFFICER and profile and profile.community:
        qs = qs.filter(dwelling__community=profile.community)
    elif role == Role.MAINTENANCE_SUPERVISOR:
        qs = qs.all()
    elif role == Role.COMMUNITY_MANAGER and profile and profile.community:
        qs = qs.filter(dwelling__community=profile.community)
    elif role == Role.TENANT:
        qs = qs.filter(raised_by=user)
    else:
        qs = qs.none()

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    return render(request, 'housing/repair_request_list.html', {
        'repair_requests': qs.order_by('-created_at'),
        'status_choices': RepairRequest.Status.choices,
        'active_status': status_filter or '',
    })


@login_required
def repair_request_detail(request, pk):
                                                                    
    rr = get_object_or_404(
        RepairRequest.objects.select_related('dwelling__community', 'raised_by', 'assigned_to'),
        pk=pk,
    )
    _check_can_view(request.user, rr)
    update_form = MaintenanceUpdateForm()
    return render(request, 'housing/repair_request_detail.html', {
        'rr': rr,
        'updates': rr.updates.select_related('author').all(),
        'update_form': update_form,
    })


@login_required
def repair_request_create(request):
                 
    if request.method == 'POST':
        form = RepairRequestForm(request.POST)
        if form.is_valid():
            with transaction.atomic():                                                     
                rr = form.save(commit=False)
                rr.raised_by = request.user
                rr.save()
                                                                                  
                                                                                     
                logger.info('CREATE repair id=%s by user=%s', rr.pk, request.user.username)
            messages.success(request, f'Repair request #{rr.pk} created.')
            return redirect('repair_request_detail', pk=rr.pk)
    else:
        form = RepairRequestForm()
    return render(request, 'housing/repair_request_form.html',
                  {'form': form, 'action': 'Create'})


@login_required
def repair_request_update(request, pk):
                                                                                  
    rr = get_object_or_404(RepairRequest, pk=pk)
    _check_can_edit(request.user, rr)

    profile = getattr(request.user, 'profile', None)
    role = profile.role if profile else None
    StaffEdit = role in {Role.ADMIN, Role.HOUSING_OFFICER, Role.MAINTENANCE_SUPERVISOR}
    FormCls = RepairRequestStatusForm if StaffEdit else RepairRequestForm

    if request.method == 'POST':
        form = FormCls(request.POST, instance=rr)
        if form.is_valid():
            with transaction.atomic():
                previous_status = rr.status
                obj = form.save()
                if obj.status == RepairRequest.Status.COMPLETED and previous_status != RepairRequest.Status.COMPLETED:
                    obj.completed_at = timezone.now()
                    obj.save(update_fields=['completed_at'])
                logger.info('UPDATE repair id=%s status=%s by user=%s',
                            obj.pk, obj.status, request.user.username)
            messages.success(request, 'Repair request updated.')
            return redirect('repair_request_detail', pk=rr.pk)
    else:
        form = FormCls(instance=rr)

    return render(request, 'housing/repair_request_form.html',
                  {'form': form, 'action': 'Update', 'rr': rr})


@login_required
def repair_request_delete(request, pk):
                                                                         
    rr = get_object_or_404(RepairRequest, pk=pk)
    user = request.user
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None

    is_admin = user.is_superuser or role == Role.ADMIN
    is_owner_open = (rr.raised_by_id == user.id
                     and rr.status == RepairRequest.Status.OPEN)
    if not (is_admin or is_owner_open):
        messages.error(request, 'You cannot delete this repair request.')
        return redirect('repair_request_detail', pk=rr.pk)

    if request.method == 'POST':
        logger.info('DELETE repair id=%s by user=%s', rr.pk, user.username)
        rr.delete()
        messages.success(request, 'Repair request deleted.')
        return redirect('repair_request_list')
    return render(request, 'housing/repair_request_confirm_delete.html', {'rr': rr})


@login_required
def repair_request_add_update(request, pk):
                                                   
    rr = get_object_or_404(RepairRequest, pk=pk)
    _check_can_edit(request.user, rr)
    if request.method == 'POST':
        form = MaintenanceUpdateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                update = form.save(commit=False)
                update.repair_request = rr
                update.author = request.user
                update.save()
                if update.status_change:
                    rr.status = update.status_change
                    if update.status_change == RepairRequest.Status.COMPLETED:
                        rr.completed_at = timezone.now()
                    rr.save()
                logger.info('UPDATE repair id=%s note added by %s',
                            rr.pk, request.user.username)
            messages.success(request, 'Update added.')
    return redirect('repair_request_detail', pk=rr.pk)


                                                                             
               
                                                                             
@login_required
def notifications(request):
    qs = request.user.notifications.all()
                                                        
    qs.filter(is_read=False).update(is_read=True)
    return render(request, 'housing/notifications.html', {'notifications': qs})


                                                                             
         
                                                                             
@role_required(Role.ADMIN, Role.COMMUNITY_MANAGER)
def community_report(request, pk):
       
    community = get_object_or_404(Community, pk=pk)
    dwellings = community.dwellings.all()
    repairs = RepairRequest.objects.filter(dwelling__community=community)
    summary = {
        'total_dwellings': dwellings.count(),
        'occupied_dwellings': dwellings.filter(is_occupied=True).count(),
        'total_repairs': repairs.count(),
        'open_repairs': repairs.filter(status=RepairRequest.Status.OPEN).count(),
        'urgent_repairs': repairs.filter(priority=RepairRequest.Priority.URGENT).count(),
    }
    return render(request, 'housing/community_report.html', {
        'community': community,
        'summary': summary,
    })


                                                                             
                             
                                                                             
def _check_can_view(user, rr):
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None
    if user.is_superuser or role in {Role.ADMIN, Role.MAINTENANCE_SUPERVISOR}:
        return
    if role in {Role.HOUSING_OFFICER, Role.COMMUNITY_MANAGER}:
        if profile and profile.community_id == rr.dwelling.community_id:
            return
    if role == Role.TENANT and rr.raised_by_id == user.id:
        return
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied('Not allowed to view this repair request.')


def _check_can_edit(user, rr):
    profile = getattr(user, 'profile', None)
    role = profile.role if profile else None
    if user.is_superuser or role in {Role.ADMIN, Role.MAINTENANCE_SUPERVISOR, Role.HOUSING_OFFICER}:
        return
    if role == Role.TENANT and rr.raised_by_id == user.id and rr.status == RepairRequest.Status.OPEN:
        return
    from django.core.exceptions import PermissionDenied
    raise PermissionDenied('Not allowed to edit this repair request.')
