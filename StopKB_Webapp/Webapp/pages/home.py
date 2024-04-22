import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output

# Charger les nombres à partir des fichiers
with open("../database/variations_number.txt", "r") as file:
    variations_number = file.read().strip()

with open("../database/genes_number.txt", "r") as file:
    genes_number = file.read().strip()

with open("../database/diseases_number.txt", "r") as file:
    diseases_number = file.read().strip()
    
with open("../database/phenotypes_number.txt", "r") as file:
    phenotypes_number = file.read().strip()

layout = dbc.Container(
    [
        html.H1([
            html.Span("StopKB", style={"font-weight": "bold", "font-size": "larger"}),
            ": A comprehensive knowledgebase for nonsense suppression therapies",
        ], style={"text-align": "center", "margin-top": "2%"}),

        dbc.Row(
            dbc.Col(
                [
                    html.H2("Introduction"),
                    html.P("Nonsense variations are responsible in ~12% of rare human genetic diseases and 10% of the variations observed in tumor suppressor genes, such as the TP53 gene involved in more than 50% of cancers. These nonsense variations encode a premature termination codon (PTC) in the sequence of a protein-coding gene. The mRNAs carrying these PTCs are responsible for the production of a truncated protein that is unable to perform its normal function and may have deleterious effects on the cell and the organism. Several nonsense suppression strategies are being studied. For example, therapeutic approaches using small molecules that induce the readthrough of PTCs seems promising. However, existing nonsense suppression therapies have difficulty in combining efficacy and low toxicity. Therefore, new research is needed for a better understanding of the diseases, genes and nonsense variations that are candidates for therapeutic approaches and eventually, for the development of new therapies. We hence propose StopKB, a graph-oriented knowledge base that allows the analysis, evaluation and prioritization of PTCs and diseases to be targeted for a nonsense suppression therapeutic approach. StopKB aggregates a large set of known nonsense variations and associated genes, diseases, and phenotypes from multiple public databases. StopKB data can be explored at different levels of granularity, to query summary statistics or more complex queries regarding the best targets for a nonsense suppression therapeutic approach."),
                    html.Img(src="assets/icons/ribosome.png", style={"width": "200px", "height": "auto", "display": "block", "margin-left": "auto", "margin-right": "auto", "margin-top": "2%"}),
                ],
            ),
            style={"margin-top": "2%"},
        ),

        html.H2("Data sources and content", style={"margin-top": "2%"}),

        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Data sources"),
                            dbc.CardBody(
                                [
                                    html.Div(
                                    [
                                        # Utilisez une boucle pour générer les images
                                        html.A(html.Img(src=f"assets/icons/clinvar.png"), href="https://www.ncbi.nlm.nih.gov/clinvar/"),
                                        html.A(html.Img(src=f"assets/icons/cosmic.png"), href="https://cancer.sanger.ac.uk/cosmic"),
                                        html.A(html.Img(src=f"assets/icons/gnomad.jpg"), href="https://gnomad.broadinstitute.org/"),
                                        html.A(html.Img(src=f"assets/icons/orphanet.png"), href="https://www.orpha.net/consor/cgi-bin/index.php?lng=EN"),
                                        html.A(html.Img(src=f"assets/icons/hpo.png"), href="https://hpo.jax.org/app/"),
                                        html.A(html.Img(src=f"assets/icons/HUGO.png"), href="https://www.genenames.org/"),
                                        html.A(html.Img(src=f"assets/icons/interpro.png"), href="https://www.ebi.ac.uk/interpro/"),
                                        #html.A(html.Img(src=f"../assets/icons/ribosome.png"), href="https://www.ncbi.nlm.nih.gov/clinvar/"),
                                    ],
                                        style={"display": "flex", "justify-content": "center", "align-items": "center", "flex-wrap": "wrap"},
                                    ),
                                    #dbc.Button("Release contents", href="/stopkb/documentation", color="primary", className="ml-auto", style={"float": "right"}),
                                ],
                                style={"height": "100%", "overflow": "auto"},
                            ),
                            dbc.CardFooter(
                                dbc.Button("Release contents", href="/stopkb/documentation", color="primary", className="btn-sm ml-auto", style={"float": "right"}),
                            ),
                        ],
                        style={"height": "100%", "overflow": "auto"},
                    ),
                ),
                dbc.Col(
                    dbc.Card(
                        [
                            dbc.CardHeader("Database content"),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.P(f"{variations_number} nonsense variations", style={"color": "#369BE8", "font-size": "larger", "font-weight": "bold", "margin-bottom": "0.5rem"}),
                                                    html.P(f"{diseases_number} diseases", style={"color": "#2F9682", "font-size": "larger", "font-weight": "bold", "margin-bottom": "0"})
                                                ],
                                                md=6,
                                            ),
                                            dbc.Col(
                                                [
                                                    html.P(f"{genes_number} genes", style={"color": "#F6CF64", "font-size": "larger", "font-weight": "bold", "margin-bottom": "0.5rem"}),
                                                    html.P(f"{phenotypes_number} phenotypes", style={"color": "#F569A6", "font-size": "larger", "font-weight": "bold", "margin-bottom": "0"})
                                                ],
                                                md=6,
                                            ),
                                        ],
                                        align="start",
                                    ),
                                ],
                                style={"height": "100%", "overflow": "auto"},
                            ),
                            dbc.CardFooter(
                                dbc.Button("Release statistics", href="/stopkb/documentation", color="primary", className="btn-sm ml-auto", style={"float": "right"}),
                            ),
                        ],
                        style={"height": "100%", "overflow": "auto"},
                    ),
                ),
            ],
            style={"margin-top": "2%"},
        ),
    ],
    fluid=True,
)