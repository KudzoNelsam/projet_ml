from django import forms
from .models import MatchPrediction

class MatchPredictionForm(forms.ModelForm):
    class Meta:
        model = MatchPrediction
        fields = ["home_team", "away_team", "tournament", "match_date", "neutral"]
        widgets = {"match_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, team_choices=None, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("", "Sélectionner une équipe")] + list(team_choices or [])
        self.fields["home_team"].widget = forms.Select(choices=choices)
        self.fields["away_team"].widget = forms.Select(choices=choices)
        input_class = "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 shadow-sm outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100"
        for name, field in self.fields.items():
            field.widget.attrs["class"] = input_class
            if name == "neutral":
                field.widget.attrs["class"] = "h-5 w-5 rounded border-slate-300 text-blue-600 focus:ring-blue-500"

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("home_team") == cleaned.get("away_team"):
            raise forms.ValidationError("Les deux équipes doivent être différentes.")
        return cleaned
