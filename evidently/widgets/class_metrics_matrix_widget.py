#!/usr/bin/env python
# coding: utf-8

import json
from typing import Optional

import pandas as pd

import plotly.figure_factory as ff

from evidently import ColumnMapping
from evidently.analyzers.classification_performance_analyzer import ClassificationPerformanceAnalyzer
from evidently.model.widget import BaseWidgetInfo
from evidently.widgets.widget import Widget


class ClassMetricsMatrixWidget(Widget):
    def __init__(self, title: str, dataset: str = 'reference'):
        super().__init__(title)
        self.dataset = dataset  # reference or current

    def analyzers(self):
        return [ClassificationPerformanceAnalyzer]

    def calculate(self,
                  reference_data: pd.DataFrame,
                  current_data: Optional[pd.DataFrame],
                  column_mapping: ColumnMapping,
                  analyzers_results) -> Optional[BaseWidgetInfo]:

        results = analyzers_results[ClassificationPerformanceAnalyzer]

        if results['utility_columns']['target'] is None or results['utility_columns']['prediction'] is None:
            if self.dataset == 'reference':
                raise ValueError(f"Widget [{self.title}] requires 'target' and 'prediction' columns.")
            return None
        if self.dataset not in results['metrics'].keys():
            if self.dataset == 'reference':
                raise ValueError(f"Widget [{self.title}] required 'reference' results from"
                                 f" {ClassificationPerformanceAnalyzer.__name__} but no data found")
            return None
        # plot support bar
        metrics_matrix = results['metrics'][self.dataset]['metrics_matrix']
        metrics_frame = pd.DataFrame(metrics_matrix)

        z = metrics_frame.iloc[:-1, :-3].values

        x = results['target_names'] if results['target_names'] else metrics_frame.columns.tolist()[:-3]

        y = ['precision', 'recall', 'f1-score']

        # change each element of z to type string for annotations
        z_text = [[str(round(y, 3)) for y in x] for x in z]

        # set up figure
        fig = ff.create_annotated_heatmap(z, x=x, y=y, annotation_text=z_text, colorscale='bluered', showscale=True)
        fig.update_layout(
            xaxis_title="Class",
            yaxis_title="Metric")

        metrics_matrix_json = json.loads(fig.to_json())

        return BaseWidgetInfo(
            title=self.title,
            type="big_graph",
            size=1 if current_data is not None else 2,
            params={
                "data": metrics_matrix_json['data'],
                "layout": metrics_matrix_json['layout']
            },
        )
