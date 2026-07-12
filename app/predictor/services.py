import gettext
from functools import lru_cache
from math import exp, factorial

import joblib
import pandas as pd
import pycountry
from django.conf import settings


TEAM_NAME_MAPPING = {
    "Brunei": "Brunei Darussalam", "Cape Verde": "Cabo Verde",
    "China": "China PR", "Curaçao": "Curacao",
    "Czech Republic": "Czechia", "DR Congo": "Congo DR",
    "Gambia": "The Gambia", "Iran": "IR Iran",
    "Ivory Coast": "Côte d'Ivoire", "Kyrgyzstan": "Kyrgyz Republic",
    "North Korea": "Korea DPR", "South Korea": "Korea Republic",
    "Saint Kitts and Nevis": "St Kitts and Nevis", "Saint Lucia": "St Lucia",
    "Saint Vincent and the Grenadines": "St Vincent and the Grenadines",
    "São Tomé and Príncipe": "Sao Tome and Principe",
    "Taiwan": "Chinese Taipei", "United States": "USA",
    "United States Virgin Islands": "US Virgin Islands",
}

SPECIAL_TEAM_LABELS = {
    "England": "Angleterre", "Scotland": "Écosse", "Wales": "Pays de Galles",
    "Northern Ireland": "Irlande du Nord", "South Korea": "Corée du Sud",
    "North Korea": "Corée du Nord", "Ivory Coast": "Côte d’Ivoire",
    "DR Congo": "RD Congo", "Cape Verde": "Cap-Vert",
    "United States": "États-Unis", "Taiwan": "Taïwan",
}


class PredictionInputError(ValueError):
    """Erreur de données compréhensible dans le formulaire."""


class PredictionServiceError(RuntimeError):
    """Erreur de chargement ou d'exécution des pipelines."""


class MatchPredictionService:
    """Construit les features puis exécute les pipelines sauvegardées."""

    def __init__(self):
        required = [
            settings.ML_MODEL_PATH, settings.SCORE_MODEL_PATH,
            settings.MATCH_RESULTS_PATH, settings.FIFA_RANKING_PATH,
        ]
        missing = [str(path) for path in required if not path.exists()]
        if missing:
            raise PredictionServiceError("Fichier requis absent : " + ", ".join(missing))
        self.matches = pd.read_csv(
            settings.MATCH_RESULTS_PATH, parse_dates=["date"]
        ).dropna(subset=["home_score", "away_score"])
        self.ranking = pd.read_csv(
            settings.FIFA_RANKING_PATH, parse_dates=["rank_date"]
        ).sort_values("rank_date")
        self.bundle = joblib.load(settings.ML_MODEL_PATH)
        self.score_bundle = joblib.load(settings.SCORE_MODEL_PATH)
        self.model = self.bundle["model"]

    @property
    def available_teams(self):
        return sorted(set(self.matches["home_team"]) | set(self.matches["away_team"]))

    @property
    def available_ranked_teams(self):
        recent_limit = self.ranking["rank_date"].max() - pd.Timedelta(days=730)
        ranked_names = set(self.ranking.loc[
            (self.ranking["rank_date"] >= recent_limit) & self.ranking["rank"].notna(),
            "country_full",
        ])
        return sorted(team for team in self.available_teams if TEAM_NAME_MAPPING.get(team, team) in ranked_names)

    def _recent_form(self, team, match_date):
        home = self.matches.loc[
            (self.matches["home_team"] == team) & (self.matches["date"] < match_date),
            ["date", "home_score", "away_score"],
        ].rename(columns={"home_score": "goals_for", "away_score": "goals_against"})
        away = self.matches.loc[
            (self.matches["away_team"] == team) & (self.matches["date"] < match_date),
            ["date", "home_score", "away_score"],
        ].rename(columns={"away_score": "goals_for", "home_score": "goals_against"})
        recent = pd.concat([home, away]).sort_values("date").tail(5)
        if recent.empty:
            raise PredictionInputError(f"Aucun match antérieur disponible pour {team}.")
        wins = int((recent["goals_for"] > recent["goals_against"]).sum())
        draws = int((recent["goals_for"] == recent["goals_against"]).sum())
        losses = int((recent["goals_for"] < recent["goals_against"]).sum())
        return {
            "recent_matches_count": len(recent), "recent_wins": wins,
            "recent_draws": draws, "recent_losses": losses,
            "avg_goals_for": recent["goals_for"].mean(),
            "avg_goals_against": recent["goals_against"].mean(),
            "recent_form_points": 3 * wins + draws,
        }

    def _fifa_state(self, team, match_date):
        ranking_name = TEAM_NAME_MAPPING.get(team, team)
        history = self.ranking.loc[
            (self.ranking["country_full"] == ranking_name)
            & (self.ranking["rank_date"] <= match_date)
        ]
        if history.empty:
            raise PredictionInputError(f"Aucun classement FIFA disponible pour {team} avant cette date.")
        row = history.iloc[-1]
        if pd.isna(row["rank"]):
            raise PredictionInputError(f"{team} ne possède pas de rang FIFA exploitable à cette date.")
        return {
            "rank": row["rank"], "total_points": row["total_points"],
            "rank_change": row["rank_change"], "confederation": row["confederation"],
            "ranking_age_days": (match_date - row["rank_date"]).days,
            "rank_date": row["rank_date"],
        }

    def build_features(self, home_team, away_team, match_date, neutral=True, tournament="FIFA World Cup"):
        match_date = pd.Timestamp(match_date).normalize()
        if home_team == away_team:
            raise PredictionInputError("Les deux équipes doivent être différentes.")
        unknown = {home_team, away_team} - set(self.available_teams)
        if unknown:
            raise PredictionInputError(f"Équipe inconnue : {', '.join(sorted(unknown))}.")
        home_form, away_form = self._recent_form(home_team, match_date), self._recent_form(away_team, match_date)
        home_fifa, away_fifa = self._fifa_state(home_team, match_date), self._fifa_state(away_team, match_date)
        values = {f"home_{key}": value for key, value in home_form.items()}
        values.update({f"away_{key}": value for key, value in away_form.items()})
        for side, state in [("home", home_fifa), ("away", away_fifa)]:
            for key in ["rank", "total_points", "rank_change", "confederation", "ranking_age_days"]:
                values[f"{side}_{key}"] = state[key]
        for name in ["recent_wins", "recent_draws", "recent_losses", "avg_goals_for", "avg_goals_against", "recent_form_points"]:
            values[f"{name}_diff"] = values[f"home_{name}"] - values[f"away_{name}"]
        values["rank_diff"] = values["away_rank"] - values["home_rank"]
        values["total_points_diff"] = values["home_total_points"] - values["away_total_points"]
        values.update({"tournament": tournament, "neutral": bool(neutral)})
        features = pd.DataFrame([values]).reindex(columns=self.bundle["feature_columns"])
        missing_features = [column for column in features if column not in values]
        if missing_features:
            raise PredictionInputError("Features impossibles à construire : " + ", ".join(missing_features))
        return features, home_fifa["rank_date"], away_fifa["rank_date"]

    @staticmethod
    def _encode(features, bundle):
        """Reproduit l'encodage get_dummies + scaling manuel fait dans le notebook d'entraînement."""
        encoded = pd.get_dummies(features, columns=bundle["onehot_features"])
        encoded["neutral"] = encoded["neutral"].astype(int)
        encoded = encoded.reindex(columns=bundle["encoded_columns"], fill_value=0)
        if bundle.get("scaler_mean") is not None:
            mean = pd.Series(bundle["scaler_mean"])
            std = pd.Series(bundle["scaler_std"])
            encoded[bundle["numeric_features"]] = (encoded[bundle["numeric_features"]] - mean) / std
        return encoded

    def predict(self, home_team, away_team, match_date, neutral=True, tournament="FIFA World Cup"):
        features, home_rank_date, away_rank_date = self.build_features(home_team, away_team, match_date, neutral, tournament)
        encoded_features = self._encode(features, self.bundle)
        probabilities = self.model.predict_proba(encoded_features)[0]
        mapping = self.bundle["class_mapping"]
        probability_by_result = {
            mapping[int(label)]: float(probability)
            for label, probability in zip(self.model.classes_, probabilities)
        }
        predicted_result = mapping[int(self.model.predict(encoded_features)[0])]
        score_features = self._encode(features, self.score_bundle)
        expected_home = max(0.0, float(self.score_bundle["home_model"].predict(score_features)[0]))
        expected_away = max(0.0, float(self.score_bundle["away_model"].predict(score_features)[0]))
        possible_scores = []
        for home_goals in range(9):
            for away_goals in range(9):
                compatible = ((predicted_result == "home_win" and home_goals > away_goals)
                              or (predicted_result == "draw" and home_goals == away_goals)
                              or (predicted_result == "away_win" and home_goals < away_goals))
                if compatible:
                    probability = (exp(-expected_home) * expected_home ** home_goals / factorial(home_goals)
                                   * exp(-expected_away) * expected_away ** away_goals / factorial(away_goals))
                    possible_scores.append((probability, home_goals, away_goals))
        _, predicted_home_score, predicted_away_score = max(possible_scores)
        ranking_end = self.ranking["rank_date"].max()
        warning = "Estimation statistique, pas une certitude sportive."
        if pd.Timestamp(match_date) > ranking_end:
            warning += f" Le dernier classement disponible date du {ranking_end.strftime('%Y-%m-%d')}."
        return {
            "prediction": predicted_result, "probabilities": probability_by_result,
            "home_rank_date": home_rank_date.strftime("%Y-%m-%d"),
            "away_rank_date": away_rank_date.strftime("%Y-%m-%d"),
            "home_rank": float(features.iloc[0]["home_rank"]), "away_rank": float(features.iloc[0]["away_rank"]),
            "home_total_points": float(features.iloc[0]["home_total_points"]),
            "away_total_points": float(features.iloc[0]["away_total_points"]),
            "predicted_home_score": predicted_home_score, "predicted_away_score": predicted_away_score,
            "expected_home_goals": expected_home, "expected_away_goals": expected_away,
            "warning": warning,
        }


def french_team_label(team):
    if team in SPECIAL_TEAM_LABELS:
        return SPECIAL_TEAM_LABELS[team]
    try:
        country = pycountry.countries.lookup(team)
        translator = gettext.translation("iso3166-1", pycountry.LOCALES_DIR, languages=["fr"], fallback=True)
        return translator.gettext(country.name)
    except LookupError:
        return team


@lru_cache(maxsize=1)
def get_service():
    try:
        return MatchPredictionService()
    except PredictionServiceError:
        raise
    except Exception as exc:
        raise PredictionServiceError(f"Impossible de charger le modèle : {exc}") from exc


def get_team_choices():
    return sorted(
        ((team, french_team_label(team)) for team in get_service().available_ranked_teams),
        key=lambda item: item[1],
    )


def predict_match(home_team, away_team, match_date, neutral, tournament):
    try:
        result = get_service().predict(home_team, away_team, match_date, neutral, tournament)
    except PredictionInputError:
        raise
    except Exception as exc:
        raise PredictionServiceError(f"Erreur pendant la prédiction : {exc}") from exc
    maximum = max(result["probabilities"].values())
    result["confidence_level"] = "high" if maximum >= .70 else "medium" if maximum >= .55 else "low"
    result["confidence_label"] = {"high": "Élevée", "medium": "Moyenne", "low": "Faible"}[result["confidence_level"]]
    result["home_team_label"], result["away_team_label"] = french_team_label(home_team), french_team_label(away_team)
    result["predicted_winner_label"] = {
        "home_win": result["home_team_label"], "draw": "Match nul", "away_win": result["away_team_label"],
    }[result["prediction"]]
    return result
