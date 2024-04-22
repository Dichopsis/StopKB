import dash
from dash import html, dcc, callback, Input, Output
import dash_bootstrap_components as dbc

layout = html.Div([
    dbc.Container([
        html.H1("Contact", style={
                "text-align": "left", 
                "margin-top": "2%", 
                "border-bottom": "5px solid royalblue",
                "display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
        dbc.Row([
            dbc.Col(
                html.Iframe(src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d2639.769388579209!2d7.736326177090977!3d48.57596552053922!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x4796c9b40ade1aa3%3A0x409c7859853f964d!2s1%20Rue%20Eug%C3%A8ne%20Boeckel%2C%2067000%20Strasbourg!5e0!3m2!1sen!2sfr!4v1687611546052!5m2!1sen!2sfr", width="100%", height="100%", style={"border": "0"}),
                md=6
            ),
            dbc.Col([
                html.H3([html.I(className="fas fa-envelope mr-1"), " Email"]),
                html.P([html.A("Nicolas HAAS", href="https://cstb.icube.unistra.fr/index.php/Nicolas_Haas", target="_blank"), ": ni.haas@unistra.fr"], className="text-muted"),
                html.P([html.A("Kirsley CHENNEN", href="https://cstb.icube.unistra.fr/index.php/Kirsley_Chennen", target="_blank"), ": kchennen@unistra.fr"], className="text-muted"),
                html.P([html.A("Julie THOMPSON", href="https://cstb.icube.unistra.fr/index.php/Julie_Thompson", target="_blank"), ": thompson@unistra.fr"], className="text-muted"),
                html.P([html.A("Olivier POCH", href="https://cstb.icube.unistra.fr/index.php/Olivier_Poch", target="_blank"), ": poch@unistra.fr"], className="text-muted"),
                html.H3([html.I(className="fas fa-phone mr-1"), " Phone"]),
                html.P("+33 (0)3 68 85 32 95", className="text-muted"),
                html.H3([html.I(className="fas fa-map-marker-alt mr-1"), " Address"]),
                html.P("Centre de Recherche en Biomédecine de Strasbourg", className="text-muted"),
                html.P("1 rue Eugène Boeckel", className="text-muted"),
                html.P("67000, Strasbourg", className="text-muted"),
                html.P("FRANCE", className="text-muted"),
            ], md=6),
        ]),
    ], style={"margin-top": "5%"}),
])

