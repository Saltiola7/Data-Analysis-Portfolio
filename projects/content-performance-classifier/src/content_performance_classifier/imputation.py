"""Training-only group-aware numeric imputation."""

from __future__ import annotations

import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

from .contracts import NUMERIC_FEATURES


class TopicMedianImputer(TransformerMixin, BaseEstimator):
    """Fill numeric gaps from training topic medians, then global medians."""

    def fit(self, X: pd.DataFrame, y: object = None) -> TopicMedianImputer:
        frame = X.copy(deep=True)
        self.feature_names_in_ = frame.columns.to_numpy(dtype=object)
        self.global_medians_ = frame.loc[:, NUMERIC_FEATURES].median().to_dict()
        self.topic_medians_ = (
            frame.groupby("topic_family", observed=True)[list(NUMERIC_FEATURES)]
            .median()
            .to_dict(orient="index")
        )
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        frame = X.copy(deep=True)
        for column in NUMERIC_FEATURES:
            topic_values = frame["topic_family"].map(
                {
                    topic: medians[column]
                    for topic, medians in self.topic_medians_.items()
                    if pd.notna(medians[column])
                }
            )
            frame[column] = frame[column].fillna(topic_values).fillna(self.global_medians_[column])
        return frame
