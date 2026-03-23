# Philippe Stepniewski
from backend.domain.use_cases.llm_usecases import _parse_risk_level_response


class TestParseRiskLevelResponse:
    def test_valid_json_high_risk(self):
        raw = '{"suggested_risk_level": "high", "justification": "Crédit scoring relève de l\'Annexe III §5b."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "high"
        assert "Annexe III" in result["justification"]

    def test_valid_json_minimal_risk(self):
        raw = '{"suggested_risk_level": "minimal", "justification": "Aucune obligation spécifique."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "minimal"

    def test_valid_json_unacceptable_risk(self):
        raw = '{"suggested_risk_level": "unacceptable", "justification": "Système interdit selon Art. 5."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "unacceptable"

    def test_valid_json_limited_risk(self):
        raw = '{"suggested_risk_level": "limited", "justification": "Obligations de transparence Art. 50."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "limited"

    def test_json_wrapped_in_code_block(self):
        raw = '```json\n{"suggested_risk_level": "high", "justification": "Risque élevé."}\n```'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "high"

    def test_json_wrapped_in_generic_code_block(self):
        raw = '```\n{"suggested_risk_level": "minimal", "justification": "Pas de risque."}\n```'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "minimal"

    def test_json_with_surrounding_whitespace(self):
        raw = '  \n {"suggested_risk_level": "high", "justification": "Motif."} \n '
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "high"

    def test_invalid_risk_level_returns_none(self):
        raw = '{"suggested_risk_level": "medium", "justification": "Niveau inventé."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] is None
        assert "Niveau inventé" in result["justification"]

    def test_empty_risk_level_returns_none(self):
        raw = '{"suggested_risk_level": "", "justification": "Pas de niveau."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] is None

    def test_invalid_json_returns_raw_as_justification(self):
        raw = "This is not JSON at all"
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] is None
        assert result["justification"] == raw

    def test_case_insensitive_risk_level(self):
        raw = '{"suggested_risk_level": "HIGH", "justification": "Motif."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "high"

    def test_risk_level_with_whitespace(self):
        raw = '{"suggested_risk_level": " minimal ", "justification": "Motif."}'
        result = _parse_risk_level_response(raw)
        assert result["suggested_risk_level"] == "minimal"
