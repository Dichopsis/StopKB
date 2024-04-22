import dash
from dash import html, dcc, callback, Input, Output, dash_table
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import pandas as pd

# Charger les options pour le menu déroulant depuis un fichier
with open("../database/gene_names.txt", "r") as file:
    gene_options = [{"label": line.strip(), "value": line.strip()} for line in file]

# Définir la mise en page de l'app Dash
layout = dbc.Container(
    [
        html.H1("Search", style={
                "text-align": "left", 
                "margin-top": "2%", 
                "border-bottom": "5px solid royalblue",
                "display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
        dbc.Row(
            [
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="category-dropdown",
                            options=[
                                {"label": "StopKB", "value": "StopKB"},
                                {"label": "Gene", "value": "gene"},
                                {"label": "Disease", "value": "disease"},
                                {"label": "Phenotype", "value": "phenotype"},
                                #{"label": "Variation", "value": "variation"},
                            ],
                            value="StopKB",  # valeur par défaut
                            style={"width": "100%", "margin": "auto"},
                            #className="ms-auto" # décale vers la droite
                        ),
                    ],
                    md=6,
                    className="p-0 ms-auto", 
                ),
                dbc.Col(
                    [
                        dcc.Dropdown(
                            id="search-dropdown",
                            options=[],  # options par défaut
                            placeholder="StopKB",  # placeholder par défaut
                            style={"width": "100%"},
                            searchable=True,
                        ),
                    ],
                    md=6,
                    className="p-0",
                ),
            ],
            align="center",
            justify="center",
            style={"margin-top": "2%"},
            className="g-0",  # Retire l'espace entre les colonnes
        ),
        dbc.Row(
            dbc.Button("Search", id="search-button", color="primary", className="mr-1", n_clicks=0, style={"width": "200px", "margin": "auto"}),
            justify="center",
            style={"margin-top": "2%"},
        ),
        dcc.Store(id='stored-df'),
        dcc.Loading(
            id="loading",
            type="circle",
            children=[
                dbc.Row(
                    id="loading-output",
                    justify="center",
                    style={"margin-top": "2%"},
                ),
            ]
        )
    ],
    fluid=True,
)