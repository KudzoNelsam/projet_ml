from collections import Counter
from django.db.models import Avg, Count
from django.shortcuts import render
from predictor.models import MatchPrediction

def dashboard_view(request):
    queryset = MatchPrediction.objects.all()
    favorites = Counter()
    for item in queryset.only("home_team", "away_team", "predicted_result"):
        if item.predicted_result == "home_win": favorites[item.home_team] += 1
        elif item.predicted_result == "away_win": favorites[item.away_team] += 1
    context = {
        "total": queryset.count(),
        "home_wins": queryset.filter(predicted_result="home_win").count(),
        "draws": queryset.filter(predicted_result="draw").count(),
        "away_wins": queryset.filter(predicted_result="away_win").count(),
        "averages": queryset.aggregate(home=Avg("home_win_probability"), draw=Avg("draw_probability"), away=Avg("away_win_probability")),
        "favorites": favorites.most_common(5), "latest": queryset[:8],
    }
    return render(request, "dashboard/dashboard.html", context)
