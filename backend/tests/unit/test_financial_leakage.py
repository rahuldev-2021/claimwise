from app.modules.financial_validation.config.loader import load_financial_config


def test_submitted_costs_not_training_features():
    bundle = load_financial_config("config/financial")
    training_cols = set(bundle.feature_mapping.training_columns().keys())  # feature ids
    forbidden = set(bundle.data_dictionary.leakage_forbidden_columns)
    assert not training_cols.intersection(forbidden)
