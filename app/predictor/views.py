from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render
from .forms import MatchPredictionForm
from .models import MatchPrediction
from .services import PredictionInputError, PredictionServiceError, get_team_choices, predict_match

def prediction_view(request):
    result = None
    try:
        teams = get_team_choices()
    except PredictionServiceError as exc:
        teams = []
        messages.error(request, str(exc))
    form = MatchPredictionForm(request.POST or None, team_choices=teams)
    if request.method == "POST" and form.is_valid():
        try:
            data = form.cleaned_data
            result = predict_match(data["home_team"], data["away_team"], data["match_date"], data["neutral"], data["tournament"])
            probabilities = result["probabilities"]
            MatchPrediction.objects.create(
                home_team=data["home_team"], away_team=data["away_team"], match_date=data["match_date"], neutral=data["neutral"],
                tournament=data["tournament"],
                home_fifa_rank=result["home_rank"], away_fifa_rank=result["away_rank"],
                home_fifa_points=result["home_total_points"], away_fifa_points=result["away_total_points"],
                predicted_result=result["prediction"], home_win_probability=probabilities["home_win"],
                draw_probability=probabilities["draw"], away_win_probability=probabilities["away_win"],
                confidence_level=result["confidence_level"],
                predicted_home_score=result["predicted_home_score"], predicted_away_score=result["predicted_away_score"],
            )
        except (PredictionInputError, PredictionServiceError) as exc:
            messages.error(request, str(exc))
    return render(request, "predictor/predict.html", {"form": form, "result": result})

def history_view(request):
    predictions = MatchPrediction.objects.all()
    team = request.GET.get("team", "").strip()
    result = request.GET.get("result", "")
    confidence = request.GET.get("confidence", "")
    start_date, end_date = request.GET.get("start_date"), request.GET.get("end_date")
    if team: predictions = predictions.filter(Q(home_team__icontains=team) | Q(away_team__icontains=team))
    if result: predictions = predictions.filter(predicted_result=result)
    if confidence: predictions = predictions.filter(confidence_level=confidence)
    if start_date: predictions = predictions.filter(match_date__gte=start_date)
    if end_date: predictions = predictions.filter(match_date__lte=end_date)
    return render(request, "predictor/history.html", {"predictions": predictions[:200]})
