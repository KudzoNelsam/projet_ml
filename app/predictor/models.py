from django.db import models

class MatchPrediction(models.Model):
    RESULT_CHOICES = [("home_win", "Victoire domicile"), ("draw", "Match nul"), ("away_win", "Victoire extérieure")]
    CONFIDENCE_CHOICES = [("low", "Faible"), ("medium", "Moyenne"), ("high", "Élevée")]
    TOURNAMENT_CHOICES = [
        ("FIFA World Cup", "Coupe du monde FIFA"),
        ("FIFA World Cup qualification", "Qualifications Coupe du monde"),
        ("Friendly", "Match amical"),
        ("UEFA Euro", "Championnat d'Europe UEFA"),
        ("UEFA Euro qualification", "Qualifications Euro UEFA"),
        ("African Cup of Nations", "Coupe d'Afrique des nations"),
        ("African Cup of Nations qualification", "Qualifications Coupe d'Afrique"),
        ("Copa América", "Copa América"),
        ("AFC Asian Cup", "Coupe d'Asie AFC"),
        ("AFC Asian Cup qualification", "Qualifications Coupe d'Asie"),
        ("Gold Cup", "Gold Cup CONCACAF"),
        ("Oceania Nations Cup", "Coupe d'Océanie"),
        ("UEFA Nations League", "Ligue des nations UEFA"),
        ("CONCACAF Nations League", "Ligue des nations CONCACAF"),
        ("Confederations Cup", "Coupe des confédérations"),
    ]
    home_team = models.CharField("Équipe à domicile", max_length=100)
    away_team = models.CharField("Équipe à l'extérieur", max_length=100)
    match_date = models.DateField("Date du match")
    neutral = models.BooleanField("Terrain neutre", default=True)
    tournament = models.CharField("Type d'événement", max_length=100, choices=TOURNAMENT_CHOICES, default="FIFA World Cup")
    home_fifa_rank = models.FloatField()
    away_fifa_rank = models.FloatField()
    home_fifa_points = models.FloatField()
    away_fifa_points = models.FloatField()
    predicted_result = models.CharField(max_length=20, choices=RESULT_CHOICES)
    home_win_probability = models.FloatField()
    draw_probability = models.FloatField()
    away_win_probability = models.FloatField()
    confidence_level = models.CharField(max_length=10, choices=CONFIDENCE_CHOICES)
    predicted_home_score = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_away_score = models.PositiveSmallIntegerField(null=True, blank=True)
    predicted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-predicted_at"]

    def __str__(self):
        return f"{self.home_team} - {self.away_team} ({self.match_date})"
