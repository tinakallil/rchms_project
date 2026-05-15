                                            
from django import forms
from .models import RepairRequest, MaintenanceUpdate, Dwelling, Community


class RepairRequestForm(forms.ModelForm):
                                                        

    class Meta:
        model = RepairRequest
        fields = ['dwelling', 'title', 'description', 'category', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }


class RepairRequestStatusForm(forms.ModelForm):
                                                                     

    class Meta:
        model = RepairRequest
        fields = ['status', 'assigned_to']


class MaintenanceUpdateForm(forms.ModelForm):
    class Meta:
        model = MaintenanceUpdate
        fields = ['note', 'status_change']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class DwellingForm(forms.ModelForm):
    class Meta:
        model = Dwelling
        fields = ['community', 'address', 'structure_type',
                  'year_built', 'condition_score', 'is_occupied']


class CommunityForm(forms.ModelForm):
    class Meta:
        model = Community
        fields = ['name', 'region', 'latitude', 'longitude', 'population']
