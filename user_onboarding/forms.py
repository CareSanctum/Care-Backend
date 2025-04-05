from django import forms
from .models import IngestionData, CustomUser, UserDevice
from decimal import Decimal


class IngestionDataForm(forms.ModelForm):
    # Custom fields for vitals instead of raw JSON input
    location = forms.CharField(max_length=100, required=True)
    battery_percentage = forms.IntegerField(label='Battery (%)', min_value=0, max_value=100)
    steps = forms.IntegerField(min_value=0)
    sleep = forms.DecimalField(label='Sleep (hours)', min_value=0)
    heart_rate = forms.IntegerField(label='Heart Rate', min_value=0)
    bp_systolic = forms.IntegerField(label='Blood Pressure Systolic', min_value=0)
    bp_diastolic = forms.IntegerField(label='Blood Pressure Diastolic', min_value=0)
    blood_oxygen = forms.DecimalField(label='Blood Oxygen (%)', min_value=0, max_value=100)
    body_temperature = forms.DecimalField(label='Body Temperature (°C)', min_value=30, max_value=100)

    class Meta:
        model = IngestionData
        fields = [
            'user', 'device', 'source', 'status', 'processing_time',
            'location', 'battery_percentage', 'steps', 'sleep', 'heart_rate',
            'bp_systolic', 'bp_diastolic', 'blood_oxygen', 'body_temperature'
        ]

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    
        self.fields['user'].queryset = CustomUser.objects.all()

   
        self.fields['user'].label_from_instance = lambda obj: f"{obj.username}"
        self.fields['device'].label_from_instance = lambda obj: f"{obj.device_code}"

    
        if self.instance and self.instance.pk and self.instance.data:
            data = self.instance.data
            self.fields['location'].initial = data.get("location")
            self.fields['battery_percentage'].initial = data.get("battery_percentage")
            self.fields['steps'].initial = data.get("steps")
            self.fields['sleep'].initial = data.get("sleep")
            self.fields['heart_rate'].initial = data.get("heart_rate")

            bp = data.get("blood_pressure", {})
            self.fields['bp_systolic'].initial = bp.get("systolic")
            self.fields['bp_diastolic'].initial = bp.get("diastolic")

            self.fields['blood_oxygen'].initial = data.get("blood_oxygen")
            self.fields['body_temperature'].initial = data.get("body_temperature")

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        device = cleaned_data.get('device')
        # Set created_by from request
        if self.request and self.request.user.is_authenticated:
            self.instance.created_by = self.request.user

        return cleaned_data

    
    def save(self, commit=True):
    # Populate the JSONField using form inputs
        def to_float(val):
            return float(val) if isinstance(val, Decimal) else val

        self.instance.data = {
            "location": self.cleaned_data['location'],
            "battery_percentage": self.cleaned_data['battery_percentage'],
            "steps": self.cleaned_data['steps'],
            "sleep": to_float(self.cleaned_data['sleep']),
            "heart_rate": self.cleaned_data['heart_rate'],
            "blood_pressure": {
                "systolic": self.cleaned_data['bp_systolic'],
                "diastolic": self.cleaned_data['bp_diastolic'],
            },
            "blood_oxygen": to_float(self.cleaned_data['blood_oxygen']),
            "body_temperature": to_float(self.cleaned_data['body_temperature']),
        }

        return super().save(commit=commit)