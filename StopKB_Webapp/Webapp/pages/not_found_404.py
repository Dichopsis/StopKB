import dash
from dash import html, dcc, callback, Input, Output

layout = html.Div([
    html.Div([
        html.H1("404", style={"font-size": "72px", "margin-bottom": "15px"}),
        html.H2("Page non trouvée", style={"margin-bottom": "25px"}),
    ],
        style={"text-align": "center", "margin-top": "10%"}),
    
    html.Div([
        html.Img(src="/assets/icons/ribosome.png", style={"width": "100%", "max-width": "500px"})
    ],
        style={"text-align": "center"}),
    
    html.Div([
        html.P("Sorry, the page you are looking for does not exist or has been moved.",
               style={"margin-bottom": "35px"}),
        dcc.Link("Back to home page", href="/",
                 style={"text-decoration": "none", "color": "#007BFF", "font-weight": "bold"}),
    ],
        style={"text-align": "center", "margin-bottom": "10%"}),
])