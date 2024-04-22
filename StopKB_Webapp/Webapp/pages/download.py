import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

layout = dbc.Container(
    [
        html.Div(
            html.H1("Download"), 
            style={
                "text-align": "left", 
                "margin-top": "2%", 
                "border-bottom": "5px solid royalblue",
                "display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
            }),
        dbc.Card(
            [
                dbc.CardHeader("StopKB database content", className="card-title"),
                dbc.CardBody(
                    [
                        html.A('StopKB Neo4j backup (dump)', href='assets/stopkb.dump', download='', style={'display': 'block'}),
                        html.A('StopKB flat files', href='assets/flat_database.tar.gz', download='', style={'display': 'block'}),
                        
                    ]
                ),
            ],
            style={"margin-top": "2%"},
        ),
    ],
    fluid=True,
)