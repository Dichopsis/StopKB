import dash
import os
from dash import Dash, dcc, html, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
import dash_bio as dashbio
import pandas as pd
import plotly.express as px
from werkzeug.middleware.profiler import ProfilerMiddleware
from pages import home, search, download, documentation, contact, not_found_404

#from dbmanager import DatabaseManager
import neo4j
from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

app = Dash(__name__, url_base_pathname='/stopkb/', external_stylesheets=[dbc.themes.BOOTSTRAP,'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css'])

app.title = "StopKB"

#db_manager = DatabaseManager()
URI = "neo4j://localhost:7687"
AUTH = ("neo4j", os.getenv('NEO4J_PASSWORD'))

with GraphDatabase.driver(URI, auth=AUTH) as driver: 
    driver.verify_connectivity()

# Lire les fichiers et stocker les options au démarrage de l'application
with open("../database/gene_names.txt", "r") as file:
    gene_options = [{"label": line.strip(), "value": line.strip()} for line in file]
with open("../database/disease_names.txt", "r") as file:
    disease_options = [{"label": line.strip(), "value": line.strip()} for line in file]
with open("../database/phenotype_names.txt", "r") as file:
    phenotype_options = [{"label": line.strip(), "value": line.strip()} for line in file]
with open("../database/variant_names.txt", "r") as file:
    variation_options = [{"label": line.strip(), "value": line.strip()} for line in file]

options_dict = {
    "gene": (gene_options, "Enter a gene name"),
    "disease": (disease_options, "Enter a disease name"),
    "phenotype": (phenotype_options, "Enter a phenotype name"),
    "variation": (variation_options, "Enter a variation ID"),
}

StopKB_df = pd.read_csv("assets/StopKB.csv", sep="\t")
StopKB_df.rename(columns={'Merged_Source': 'Source'}, inplace=True)

gene_domains = pd.read_csv("assets/flat_database/gene.csv", sep="\t")

def create_cyto_elements(graph):
    elements = []

    # Add nodes
    for node in graph.nodes:
        elements.append({
            'data': {'id': node.id, 'label': list(node.labels)[0]}
        })

    # Add edges
    for relationship in graph.relationships:
        elements.append({
            'data': {
                'source': relationship.start_node.id,
                'target': relationship.end_node.id,
                'label': type(relationship).__name__
            }
        })

    return elements

navbar = dbc.Navbar(
    [
        html.A(
            dbc.Row(
                [
                    dbc.Col(html.Img(src="assets/icons/graph.png", height="30px")),
                    dbc.Col(dbc.NavbarBrand("StopKB", class_name="ml-2")),
                ],
                align="center",
                #class_name="g-0",
            ),
            href="/stopkb/",
        ),
        dbc.NavbarToggler(id="navbar-toggler"),
        dbc.Collapse(
            dbc.Nav(
                [
                    dbc.NavItem(dbc.NavLink([html.Img(src="assets/icons/home.png", height="20px", className="mx-2"), "Home"], href="/stopkb/")),
                    dbc.NavItem(dbc.NavLink([html.Img(src="assets/icons/search.png", height="20px", className="mx-2"), "Search"], href="/stopkb/search")),
                    dbc.NavItem(dbc.NavLink([html.Img(src="assets/icons/download.png", height="20px", className="mx-2"), "Download"], href="/stopkb/download")),
                    dbc.NavItem(dbc.NavLink([html.Img(src="assets/icons/documentation.png", height="20px", className="mx-2"), "Documentation"], href="/stopkb/documentation")),
                    dbc.NavItem(dbc.NavLink([html.Img(src="assets/icons/contact.png", height="20px", className="mx-2"), "Contact"], href="/stopkb/contact")),
                ],
                class_name="ml-auto",
                navbar=True,
            ),
            id="navbar-collapse",
            navbar=True,
        ),
    ],
    color="dark",
    dark=True,
    fixed="top"
)


app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content', style={"margin-top": "75px"})
])


@app.callback(Output('page-content', 'children'),
              Input('url', 'pathname'))
def display_page(pathname):
    if pathname == '/stopkb/':
        return home.layout
    elif pathname == '/stopkb/search':
        return search.layout
    elif pathname == '/stopkb/download':
        return download.layout
    elif pathname == '/stopkb/documentation':
        return documentation.layout
    elif pathname == '/stopkb/contact':
        return contact.layout
    else:
        return not_found_404.layout


@app.callback(
    Output("navbar-collapse", "is_open"),
    [Input("navbar-toggler", "n_clicks")],
    [State("navbar-collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    [Output("search-dropdown", "options"), Output("search-dropdown", "placeholder"),Output("search-dropdown", "disabled")],
    [Input("category-dropdown", "value")],
)
def update_search_options(category):
        if category == "StopKB":
            return [""], "", True
        else:
            options, placeholder = options_dict.get(category, ([], ""))
            return options, placeholder, False


@app.callback(
    #[Output("search-value", "children"), Output("cytoscape", "elements"), Output("search-results", "children")],
    [Output("loading-output", "children"),
     Output("stored-df","data")],
    [Input("search-button", "n_clicks")],
    [State("category-dropdown", "value"), State("search-dropdown", "value")],
)
def execute_search(n_clicks, category, search_value):
    if n_clicks > 0 and (search_value is not None or category == "StopKB"):
        # Choose the query based on the category
        if category == "StopKB":
            #StopKB_df = driver.execute_query(f"MATCH (v:Variant) RETURN v.HGVSG as HGVSG, v.Merged_Source as Source, v.ClinicalSignificance as ClinicalSignificance, v.pos_stop_prot as pos_stop_prot, v.pos_relative_prot as pos_relative_prot, v.pos_var_cds as pos_var_cds, v.nuc_upstream as nuc_upstream, v.codon_stop as codon_stop, v.nuc_downstream as nuc_downstream, v.exon_localization as exon_localization, v.NMD_sensitivity as NMD_sensitivity, v.AF_ww as AF,v.AF_afr as AF_afr, v.AF_amr as AF_amr, v.AF_asj as AF_asj, v.AF_eas as AF_eas, v.AF_fin as AF_fin, v.AF_nfe as AF_nfe, v.AF_oth as AF_oth, v.Origin as Origin, v.ReviewStatus as ReviewStatus",database_="neo4j",result_transformer_=neo4j.Result.to_df)
            StopKB_preview_df = StopKB_df.iloc[:1000]
            
            
            # nmd_fig_df = StopKB_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
            
            nmd_fig_df = StopKB_df['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = StopKB_df['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([StopKB_df, patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            
            top_genes_df = StopKB_df['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': StopKB_df['symbol'].value_counts().index,
                                       'Number of variations': StopKB_df['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            exploded_diseases = StopKB_df['disease_name'].str.split('; ').explode()
            disease_counts = exploded_diseases.value_counts().head(10)
            
            disease_frequency_df = pd.DataFrame({'disease_name': exploded_diseases.value_counts().index,
                                       'Number of variations': exploded_diseases.value_counts().values})

            # Créer un DataFrame pour le graphique
            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            exploded_phenotypes = StopKB_df['phenotype_name'].str.split('; ').explode()
            phenotype_counts = exploded_phenotypes.value_counts().head(10)
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': exploded_phenotypes.value_counts().index,
                                       'Number of variations': exploded_phenotypes.value_counts().values})

            # Créer un DataFrame pour le graphique
            top_phenotypes_df = phenotype_counts.reset_index()
            top_phenotypes_df.columns = ['Phenotype', 'Count']

            # Créer le graphique à barres
            fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
                        title='Top phenotypes',
                        labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            fig_top_phenotypes.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            
            # fig_top_genes = px.bar(StopKB_df['symbol'].value_counts().iloc[:10], x=StopKB_df['symbol'].value_counts().iloc[:10].index, y=StopKB_df['Symbol'].value_counts().iloc[:10].values,              
            #     title="Top 10 Genes",
            #     labels={'x':'Gene Symbol', 'y':'Count'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            
            return html.Div([
                #html.H2(f"{search_value}", style={"text-align": "center"}),
                html.H2(f"List of nonsense variations in StopKB", style={
                "text-align": "left", 
                #"display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Row(
                            id="filter-row-source",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by Source:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="source-checklist",
                                            options=[
                                                {'label': 'ClinVar', 'value': 'ClinVar'},
                                                {'label': 'gnomAD', 'value': 'gnomAD'},
                                                {'label': 'COSMIC', 'value': 'COSMIC'},
                                            ],
                                            value=['ClinVar', 'gnomAD', 'COSMIC'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-clinical-significance",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by ClinicalSignificance:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="clinical-significance-checklist",
                                            options=[
                                                {"label": "Pathogenic", "value": "Pathogenic"},
                                                {"label": "Likely pathogenic", "value": "Likely pathogenic"},
                                                {"label": "Uncertain significance", "value": "Uncertain significance"},
                                                {"label": "Likely benign", "value": "Likely benign"},
                                                {"label": "Benign", "value": "Benign"}
                                            ],
                                            value=["Pathogenic","Likely pathogenic","Uncertain significance","Likely benign","Benign"],  # Par défaut, toutes les options sont sélectionnées
                                            inline=False
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-stop-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by absolute position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-stop-prot', type='number', placeholder='Start pos', min=0, value = 1, step=1),
                                        dcc.Input(id='end-pos-stop-prot', type='number', placeholder='End pos', min=0, step=1)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-relative-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by relative position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-relative-prot', type='number', placeholder='Start ratio', min=0, max=1, value=0, step=0.01),
                                        dcc.Input(id='end-pos-relative-prot', type='number', placeholder='End ratio', min=0, max=1,value=1, step=0.01)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-stop-codon",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by stop codon:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="stop-codon-checklist",
                                            options=[
                                                {"label": "TGA", "value": "TGA"},
                                                {"label": "TAG", "value": "TAG"},
                                                {"label": "TAA", "value": "TAA"}
                                            ],
                                            value=["TGA", "TAG", "TAA"],
                                            inline=False
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-nmd-sensitivity",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by NMD sensitivity:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="nmd-sensitivity-checklist",
                                            options=[
                                                {'label': 'Sensitive', 'value': 'sensitive'},
                                                {'label': 'Insensitive', 'value': 'insensitive'}
                                            ],
                                            value=['sensitive', 'insensitive'],
                                            inline=False
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-af-worldwide",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by worldwide allele frequency:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-af-worldwide', type='number', placeholder='Min AF', min=0, max=1, step=1e-10),
                                        dcc.Input(id='end-af-worldwide', type='number', placeholder='Max AF', min=0, max=1, step=1e-10)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-overlapping-domain",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by overlapping domain:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="overlapping-domain-checklist",
                                            options=[
                                                {'label': 'Overlapping', 'value': 'overlapping'},
                                                {'label': 'Non-Overlapping', 'value': 'non-overlapping'}
                                            ],
                                            value=['overlapping', 'non-overlapping'],
                                            inline=False
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button("Apply Filter", id="filter-button", color="primary"),
                                width={"size": 6, "offset": 3},
                            ),
                            className="mb-3",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Tabs([
                            dcc.Tab(id='tab-variations',
                                label=f"{StopKB_df['HGVSG'].nunique()} variations",
                                children=[
                                    dcc.Graph(
                                        id='patho-bar-chart',
                                        figure=fig_patho
                                    ),
                                    dcc.Graph(
                                        id='NMD-pie-chart',
                                        figure=fig_nmd
                                    ),
                                ]),
                            dcc.Tab(id='tab-genes',
                                label=f"{StopKB_df['symbol'].nunique()} genes", children=[
                                dcc.Graph(
                                id='top-genes-bar-chart',
                                figure=fig_top_genes
                                ),
                                dash_table.DataTable(
                                        id='table-genes',
                                        data=genes_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(genes_frequency_df[i]) else None} for i in genes_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in genes_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                dcc.Graph(
                                id='needle-plot',
                                style={'display': 'none'}
                                ),
                                html.Button("Download CSV", id="btn_csv_genes"),
                                dcc.Download(id="download-dataframe-csv-genes"),
                            ]),
                            dcc.Tab(id='tab-diseases',
                                label=f"{exploded_diseases.nunique()} diseases", children=[
                                dcc.Graph(
                                id='top-diseases-bar-chart',
                                figure=fig_top_diseases
                                ),
                                dash_table.DataTable(
                                        id='table-diseases',
                                        data=disease_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(disease_frequency_df[i]) else None} for i in disease_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in disease_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                html.Button("Download CSV", id="btn_csv_diseases"),
                                dcc.Download(id="download-dataframe-csv-diseases")
                            ]),
                            dcc.Tab(id='tab-phenotypes',
                                label=f"{exploded_phenotypes.nunique()} phenotypes", children=[
                                dcc.Graph(
                                id='top-phenotypes-bar-chart',
                                figure=fig_top_phenotypes
                                ),
                                dash_table.DataTable(
                                        id='table-phenotypes',
                                        data=phenotype_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(phenotype_frequency_df[i]) else None} for i in phenotype_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in phenotype_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                ),
                                html.Button("Download CSV", id="btn_csv_phenotypes"),
                                dcc.Download(id="download-dataframe-csv-phenotypes")
                            ]),
                            dcc.Tab(label='Table', children=[
                                dash_table.DataTable(
                                    id='table-prefiltered',
                                    data=StopKB_preview_df.drop(columns=['Cytogenetic','RefSeq_nuc','Ensembl_nuc','RefSeq_prot','Ensembl_prot','uniprot_id','prot_length','exon_counts','disorder_id','name','orpha_code','definition','prevalence_geo','hpo_id','hpo_name','comment','definition_x','disease_name','phenotype_name']).to_dict("records"),
                                    columns=[{"name": i, "id": i, 'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(StopKB_preview_df[i]) else None} for i in StopKB_preview_df.drop(columns=['Cytogenetic','RefSeq_nuc','Ensembl_nuc','RefSeq_prot','Ensembl_prot','uniprot_id','prot_length','exon_counts','disorder_id','name','orpha_code','definition','prevalence_geo','hpo_id','hpo_name','comment','definition_x','disease_name','phenotype_name']).columns],
                                    style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'minWidth': 150,
                                    'font-family': 'system-ui',
                                        },
                                    style_cell_conditional=[
                                        {'if': {'column_id': c},
                                        'textAlign': 'center'} for c in StopKB_preview_df.drop(columns=['Cytogenetic','RefSeq_nuc','Ensembl_nuc','RefSeq_prot','Ensembl_prot','uniprot_id','prot_length','exon_counts','disorder_id','name','orpha_code','definition','prevalence_geo','hpo_id','hpo_name','comment','definition_x','disease_name','phenotype_name']).columns],
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(211, 211, 211)'
                                        }
                                    ],
                                    style_header={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'width': 'auto',
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold',
                                        'fontSize': '12px'
                                    },
                                    style_table={'overflowX': 'auto'},
                                    style_as_list_view=True,
                                    filter_action='none',
                                    filter_query='',
                                    sort_action='native',
                                    sort_mode='multi',
                                    page_action='native',
                                    page_current=0,
                                    page_size=20,
                                    fixed_rows={'headers': True},
                                    fixed_columns={'headers': True},
                                    export_format="none",
                                    export_headers="none",
                                ),
                                html.H6("This table is a preview. Please click the button below to download all the data.", style={"font-weight": "bold"}),
                                html.Button("Download CSV", id="btn_csv"),
                                dcc.Download(id="download-dataframe-csv"),
                            ])
                        ])
                    ], width=10),
                ]),
            ]),dash.no_update
            
            
        elif category == "gene":
            gene_df = driver.execute_query(f"MATCH (v:Variant)-[LOCATED_ON]-(g:Gene) WHERE g.Symbol = '{search_value}' RETURN g.Symbol as symbol, g.RefSeq_nuc as RefSeq_nuc, g.Ensembl_nuc as Ensembl_nuc, g.RefSeq_prot as RefSeq_prot, g.Ensembl_prot as Ensembl_prot, g.prot_length as prot_length, g.exon_counts as exon_counts, v.HGVSG as HGVSG, v.Merged_Source as Source, v.ClinicalSignificance as ClinicalSignificance, v.pos_stop_prot as pos_stop_prot, v.pos_relative_prot as pos_relative_prot, v.pos_var_cds as pos_var_cds, v.nuc_upstream as nuc_upstream, v.codon_stop as codon_stop, v.nuc_downstream as nuc_downstream, v.exon_localization as exon_localization, v.NMD_sensitivity as NMD_sensitivity, v.AF_ww as AF,v.AF_afr as AF_afr, v.AF_amr as AF_amr, v.AF_asj as AF_asj, v.AF_eas as AF_eas, v.AF_fin as AF_fin, v.AF_mid as AF_mid, v.AF_nfe as AF_nfe, v.AF_sas as AF_sas, v.AF_remaining as AF_remaining, v.overlapping_domain as overlapping_domain, v.Origin as Origin, v.ReviewStatus as ReviewStatus",database_="neo4j",result_transformer_=neo4j.Result.to_df)
            prot_length = gene_df['prot_length'].iloc[0]
            exon_counts = gene_df['exon_counts'].iloc[0]
            RefSeq_nuc = gene_df['RefSeq_nuc'].iloc[0]
            Ensembl_nuc = gene_df['Ensembl_nuc'].iloc[0]
            RefSeq_prot = gene_df['RefSeq_prot'].iloc[0]
            Ensembl_prot = gene_df['Ensembl_prot'].iloc[0]
            gene_needle_df = pd.merge(gene_df.drop_duplicates(subset=['symbol']), gene_domains, how='left', on='symbol')
            gene_df = gene_df.drop(['prot_length', 'exon_counts', 'RefSeq_nuc', 'Ensembl_nuc', 'RefSeq_prot', 'Ensembl_prot'], axis=1)
            #gene_datatable = create_datatable(gene_df)
            # gene_graph = driver.execute_query(f"MATCH (p:Phenotype)-[r:RECOGNIZABLE_BY]-(d:Disease)-[c:CAUSED_BY]-(g:Gene)-[l:LOCATED_ON]-(v:Variant) WHERE g.Symbol = '{search_value}' RETURN p, r, d, g, l, v",database_="neo4j",result_transformer_=neo4j.Result.graph)
            # gene_cyto = create_cyto_elements(gene_graph)
            
            # nmd_fig_df = gene_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False) 
            

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
            
            # filtered_data = gene_df.dropna(subset=['ClinicalSignificance', 'Source'])

            # # Create a DataFrame for the count of each ClinicalSignificance by Source
            # clinical_significance_counts = filtered_data.groupby(['Source', 'ClinicalSignificance']).size().unstack(fill_value=0)
            # clinical_significance_counts_reset = clinical_significance_counts.reset_index()
            # clinical_significance_counts_melted = clinical_significance_counts_reset.melt(id_vars='Source', 
            #                                                                   var_name='ClinicalSignificance', 
            #                                                                   value_name='Count')

            # # Creating a stacked bar chart using Plotly
            # fig_patho = px.bar(clinical_significance_counts_melted, 
            #     x="ClinicalSignificance", 
            #     y="Count", 
            #     color="Source",
            #     barmode='stack',
            #     labels={'ClinicalSignificance': 'Signification Clinique', 'Source': 'Source des Données', 'Count': 'Nombre de Variantes'})

            # fig_patho.update_layout(title='Répartition des Variantes selon la Classification Clinique et la Source avec Plotly',
            #     xaxis_title='Signification Clinique',
            #     yaxis_title='Nombre de Variantes')
            
            # #top_disease_df =
            
            nmd_fig_df = StopKB_df[StopKB_df['symbol'] == search_value]['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = StopKB_df[StopKB_df['symbol'] == search_value]['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([StopKB_df[StopKB_df['symbol'] == search_value], patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            
            exploded_diseases = StopKB_df[StopKB_df['symbol'] == search_value]['disease_name'].str.split('; ').explode()
            disease_counts = exploded_diseases.value_counts().head(10)

            # Créer un DataFrame pour le graphique
            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            disease_frequency_df = pd.DataFrame({'disease_name': exploded_diseases.value_counts().index,
                                       'Number of variations': exploded_diseases.value_counts().values})
            
            exploded_phenotypes = StopKB_df[StopKB_df['symbol'] == search_value]['phenotype_name'].str.split('; ').explode()
            phenotype_counts = exploded_phenotypes.value_counts().head(10)

            # Créer un DataFrame pour le graphique
            # top_phenotypes_df = phenotype_counts.reset_index()
            # top_phenotypes_df.columns = ['Phenotype', 'Count']

            # # Créer le graphique à barres
            # fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
            #             title='Top phenotypes',
            #             labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            # fig_top_phenotypes.update_layout(font_family="system-ui",
            #                             title_x=0.5,
            #                             xaxis_tickangle=-15,
            #                             xaxis_tickfont_size=12)
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': exploded_phenotypes.value_counts().index,
                                       'Number of variations': exploded_phenotypes.value_counts().values})
            
            domain_data = []
            # Itération sur chaque colonne de domaine dans gene_df
            for col in gene_needle_df.filter(like='domain_'):
                for domain_str in gene_needle_df[col].dropna():
                    # Séparation de la chaîne en prenant en compte le dernier ';' comme séparateur
                    *name_parts, start, end = domain_str.rsplit(';', 2)
                    name = ';'.join(name_parts)  # Reconstruction du nom si nécessaire
                    if len(name) > 20:
                        name = name[:20] + '...'
                    coord = f"{start}-{end}"
                    domain_data.append({'name': name, 'coord': coord})
                    
            mutation_data = {
                'x': gene_df.astype({'pos_stop_prot':'string'})['pos_stop_prot'].tolist(),
                'y': ["1"] * len(gene_df),  
                'mutationGroups': gene_df['ClinicalSignificance'].tolist(),
                'domains': domain_data, 
            }
            
            colors_map = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
                        
            unique_categories = list(dict.fromkeys(mutation_data['mutationGroups']))

            unique_colors = [colors_map.get(category, "default_color") for category in unique_categories]

            
            return html.Div([
                #html.H2(f"{search_value}", style={"text-align": "center"}),
                dbc.Card(
                        [
                            dbc.CardHeader(f"{search_value}", style={"text-align": "center","font-size": "larger", "font-weight": "bold"}),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(html.P(f"Protein length: {prot_length} AA"), md=2),
                                            dbc.Col(html.P(f"Exon count: {exon_counts}"), md=2),
                                            dbc.Col(html.P(f"RefSeq transcript ID: {RefSeq_nuc}"), md=2),
                                            dbc.Col(html.P(f"Ensembl transcript ID: {Ensembl_nuc}"), md=2),
                                            dbc.Col(html.P(f"RefSeq protein ID: {RefSeq_prot}"), md=2),
                                            dbc.Col(html.P(f"Ensembl protein ID: {Ensembl_prot}"), md=2),
                                        ],
                                        align="start",
                                    ),
                                ],
                                style={"height": "100%", "overflow": "auto", "background-color": "rgba(54, 155, 232, 0.3)"},
                            ),
                            dbc.CardFooter(
                                dbc.Button("More infos on GeneCards", href=f"https://www.genecards.org/cgi-bin/carddisp.pl?gene={search_value}", target="_blank", color="primary", className="btn-sm ml-auto", style={"float": "right"}),
                            ),
                        ],
                        style={"margin-bottom": "2%", "overflow": "auto"},
                    ),
                html.H2(f"List of nonsense variations associated to {search_value}", style={
                "text-align": "left", 
                #"display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Row(
                            id="filter-row-source",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by Source:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="source-checklist",
                                            options=[
                                                {'label': 'ClinVar', 'value': 'ClinVar'},
                                                {'label': 'gnomAD', 'value': 'gnomAD'},
                                                {'label': 'COSMIC', 'value': 'COSMIC'},
                                            ],
                                            value=['ClinVar', 'gnomAD', 'COSMIC'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-clinical-significance",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by ClinicalSignificance:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="clinical-significance-checklist",
                                            options=[
                                                {"label": "Pathogenic", "value": "Pathogenic"},
                                                {"label": "Likely pathogenic", "value": "Likely pathogenic"},
                                                {"label": "Uncertain significance", "value": "Uncertain significance"},
                                                {"label": "Likely benign", "value": "Likely benign"},
                                                {"label": "Benign", "value": "Benign"}
                                            ],
                                            value=["Pathogenic","Likely pathogenic","Uncertain significance","Likely benign","Benign"],  # Par défaut, toutes les options sont sélectionnées
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-stop-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by absolute position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-stop-prot', type='number', placeholder='Start pos', min=0, value = 1, step=1),
                                        dcc.Input(id='end-pos-stop-prot', type='number', placeholder='End pos', min=0, step=1)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-relative-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by relative position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-relative-prot', type='number', placeholder='Start ratio', min=0, max=1,value=0, step=0.01),
                                        dcc.Input(id='end-pos-relative-prot', type='number', placeholder='End ratio', min=0, max=1, step=0.01)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-stop-codon",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by stop codon:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="stop-codon-checklist",
                                            options=[
                                                {"label": "TGA", "value": "TGA"},
                                                {"label": "TAG", "value": "TAG"},
                                                {"label": "TAA", "value": "TAA"}
                                            ],
                                            value=["TGA", "TAG", "TAA"],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-nmd-sensitivity",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by NMD sensitivity:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="nmd-sensitivity-checklist",
                                            options=[
                                                {'label': 'Sensitive', 'value': 'sensitive'},
                                                {'label': 'Insensitive', 'value': 'insensitive'}
                                            ],
                                            value=['sensitive', 'insensitive'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-af-worldwide",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by worldwide allele frequency:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-af-worldwide', type='number', placeholder='Min AF', min=0, max=1, step=1e-10),
                                        dcc.Input(id='end-af-worldwide', type='number', placeholder='Max AF', min=0, max=1, step=1e-10)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-overlapping-domain",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by overlapping domain:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="overlapping-domain-checklist",
                                            options=[
                                                {'label': 'Overlapping', 'value': 'overlapping'},
                                                {'label': 'Non-Overlapping', 'value': 'non-overlapping'}
                                            ],
                                            value=['overlapping', 'non-overlapping'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button("Apply Filter", id="filter-button", color="primary"),
                                width={"size": 6, "offset": 3},
                            ),
                            className="mb-3",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Tabs([
                            dcc.Tab(id='tab-variations',
                                label=f"{StopKB_df[StopKB_df['symbol'] == search_value]['HGVSG'].nunique()} variations",
                                children=[
                                    dcc.Graph(
                                        id='patho-bar-chart',
                                        figure=fig_patho
                                    ),
                                    dcc.Graph(
                                        id='NMD-pie-chart',
                                        figure=fig_nmd
                                    ),
                                ]),
                            dcc.Tab(id='tab-genes', label='Protein mapping', children=[
                                dbc.Row(
                                    dbc.Col(
                                        dashbio.NeedlePlot(
                                            id='needle-plot',
                                            mutationData=mutation_data,
                                            needleStyle={
                                                'headSize': 10,
                                                'headColor': unique_colors
                                            },
                                            height=500,
                                        ),
                                        #width=12,
                                        #style={'width': '100%', 'height': '100%'}
                                    ),
                                ),
                                dcc.Graph(
                                    id='top-genes-bar-chart',
                                    style={'display': 'none'}
                                ),
                                dash_table.DataTable(
                                        id='table-genes',
                                        style_table={'display': 'none'}
                                    ),
                            ]),
                            dcc.Tab(id='tab-diseases',
                                label=f"{exploded_diseases.nunique()} diseases",
                                children=[
                                    dcc.Graph(
                                        id='top-diseases-bar-chart',
                                        figure=fig_top_diseases
                                        ),
                                    dash_table.DataTable(
                                        id='table-diseases',
                                        data=disease_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(disease_frequency_df[i]) else None} for i in disease_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in disease_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                    html.Button("Download CSV", id="btn_csv_diseases"),
                                    dcc.Download(id="download-dataframe-csv-diseases"),
                                ]),
                            dcc.Tab(id='tab-phenotypes',
                                label=f"{exploded_phenotypes.nunique()} phenotypes",
                                children=[
                                    dcc.Graph(
                                        id='top-phenotypes-bar-chart',
                                        style={'display': 'none'}
                                    ),
                                    dash_table.DataTable(
                                        id='table-phenotypes',
                                        data=phenotype_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(phenotype_frequency_df[i]) else None} for i in phenotype_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in phenotype_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                    html.Button("Download CSV", id="btn_csv_phenotypes"),
                                    dcc.Download(id="download-dataframe-csv-phenotypes")
                                ]),
                            dcc.Tab(label='Table', children=[
                                dash_table.DataTable(
                                    id='table-prefiltered',
                                    data=gene_df.drop(columns=['symbol']).to_dict("records"),
                                    columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(gene_df.drop(columns=['symbol'])[i]) else None} for i in gene_df.drop(columns=['symbol']).columns],
                                    style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'minWidth': 150,
                                    'font-family': 'system-ui',
                                        },
                                    style_cell_conditional=[
                                        {'if': {'column_id': c},
                                        'textAlign': 'center'} for c in gene_df.drop(columns=['symbol']).columns],
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(211, 211, 211)'
                                        }
                                    ],
                                    style_header={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'width': 'auto',
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold',
                                        'fontSize': '12px'
                                    },
                                    style_table={'overflowX': 'auto'},
                                    style_as_list_view=True,
                                    filter_action='none',
                                    filter_query='',
                                    sort_action='native',
                                    sort_mode='multi',
                                    page_action='native',
                                    page_current=0,
                                    page_size=20,
                                    fixed_rows={'headers': True},
                                    fixed_columns={'headers': True},
                                    export_format="none",
                                    export_headers="none",
                                ),
                                html.Button("Download CSV", id="btn_csv"),
                                dcc.Download(id="download-dataframe-csv"),
                            ])
                        ])
                    ], width=10),
                ]),
                ]),gene_df.to_json(date_format='iso', orient='split')
        
            
        elif category == "disease":
            disease_df = driver.execute_query(f"MATCH (v:Variant)-[LOCATED_ON]-(g:Gene)-[CAUSED_BY]-(d:Disease) WHERE d.disorder_name = '{search_value}' OPTIONAL MATCH (d)-[RECOGNIZABLE_BY]-(p:Phenotype)  RETURN d.disorder_id as disorder_id, d.orpha_code as orpha_code, d.definition as definition, d.prevalence_geo as prevalence_geo, g.Symbol as symbol, v.HGVSG as HGVSG, v.Merged_Source as Source, v.ClinicalSignificance as ClinicalSignificance, v.pos_stop_prot as pos_stop_prot, v.pos_relative_prot as pos_relative_prot, v.pos_var_cds as pos_var_cds, v.nuc_upstream as nuc_upstream, v.codon_stop as codon_stop, v.nuc_downstream as nuc_downstream, v.exon_localization as exon_localization, v.NMD_sensitivity as NMD_sensitivity, v.AF_ww as AF,v.AF_afr as AF_afr, v.AF_amr as AF_amr, v.AF_asj as AF_asj, v.AF_eas as AF_eas, v.AF_fin as AF_fin, v.AF_mid as AF_mid, v.AF_nfe as AF_nfe, v.AF_sas as AF_sas, v.AF_remaining as AF_remaining, v.overlapping_domain as overlapping_domain, v.Origin as Origin, v.ReviewStatus as ReviewStatus, p.hpo_name as hpo_name",database_="neo4j",result_transformer_=neo4j.Result.to_df)
            disorder_id = disease_df['disorder_id'].iloc[0]
            orpha_code = disease_df['orpha_code'].iloc[0]
            definition = disease_df['definition'].iloc[0]
            prevalence_geo = disease_df['prevalence_geo'].iloc[0]
            prevalence_geo_br = prevalence_geo.replace(';', '\n')
            disease_df = disease_df.drop(['disorder_id','orpha_code','definition','prevalence_geo'], axis=1)
            #disease_datatable = create_datatable(disease_df)
            # disease_graph = driver.execute_query(f"MATCH (p:Phenotype)-[r:RECOGNIZABLE_BY]-(d:Disease)-[c:CAUSED_BY]-(g:Gene)-[l:LOCATED_ON]-(v:Variant) WHERE d.name = '{search_value}' RETURN p, r, d, g, l, v",database_="neo4j",result_transformer_=neo4j.Result.graph)
            # disease_cyto = create_cyto_elements(disease_graph)
            
            # nmd_fig_df = disease_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
            
            #nmd_fig_df = StopKB_df[StopKB_df['disease_name'].str.contains(search_value, na=False)]['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df = disease_df.drop_duplicates(subset=['HGVSG'])['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = disease_df.drop_duplicates(subset=['HGVSG'])['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([disease_df.drop_duplicates(subset=['HGVSG']), patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            
            top_genes_df = disease_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': disease_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().index,
                                       'Number of variations': disease_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            #exploded_phenotypes = StopKB_df[StopKB_df['disease_name'].str.contains(search_value)]['phenotype_name'].str.split(';').explode()
            phenotype_counts = disease_df['hpo_name'].value_counts().head(10)
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': disease_df['hpo_name'].value_counts().index,
                                       'Number of variations': disease_df['hpo_name'].value_counts().values})

            # Créer un DataFrame pour le graphique
            # top_phenotypes_df = phenotype_counts.reset_index()
            # top_phenotypes_df.columns = ['Phenotype', 'Count']

            # # Créer le graphique à barres
            # fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
            #             title='Top phenotypes',
            #             labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            # fig_top_phenotypes.update_layout(font_family="system-ui",
            #                             title_x=0.5,
            #                             xaxis_tickangle=-15,
            #                             xaxis_tickfont_size=12)
            
            return html.Div([
                #html.H2(f"{search_value}", style={"text-align": "center"}),
                dbc.Card(
                        [
                            dbc.CardHeader(f"{search_value}", style={"text-align": "center","font-size": "larger", "font-weight": "bold"}),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(html.P(f"Disorder ID: {disorder_id}"), md=2),
                                            dbc.Col(html.P(f"Orpha code: {orpha_code}"), md=2),
                                            dbc.Col(html.P(f"Description: {definition}"), md=6),
                                            #dbc.Col(html.P(f"Prevalence: {prevalence_geo_br}"), md=2),
                                            dbc.Col(dcc.Markdown(f"Prevalence: {prevalence_geo_br}"), md=2),
                                        ],
                                        align="start",
                                    ),
                                ],
                                style={"height": "100%", "overflow": "auto", "background-color": "rgba(54, 155, 232, 0.3)"},
                            ),
                            dbc.CardFooter(
                                dbc.Button("More infos on Orphanet", href=f"https://www.orpha.net/consor/cgi-bin/Disease_Search.php?lng=EN&data_id={disorder_id}", target="_blank", color="primary", className="btn-sm ml-auto", style={"float": "right"}),
                            ),
                        ],
                        style={"margin-bottom": "2%", "overflow": "auto"},
                    ),
                html.H2(f"List of nonsense variations associated to {search_value}", style={
                "text-align": "left", 
                #"display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Row(
                            id="filter-row-source",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by Source:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="source-checklist",
                                            options=[
                                                {'label': 'ClinVar', 'value': 'ClinVar'},
                                                {'label': 'gnomAD', 'value': 'gnomAD'},
                                                {'label': 'COSMIC', 'value': 'COSMIC'},
                                            ],
                                            value=['ClinVar', 'gnomAD', 'COSMIC'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-clinical-significance",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by ClinicalSignificance:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="clinical-significance-checklist",
                                            options=[
                                                {"label": "Pathogenic", "value": "Pathogenic"},
                                                {"label": "Likely pathogenic", "value": "Likely pathogenic"},
                                                {"label": "Uncertain significance", "value": "Uncertain significance"},
                                                {"label": "Likely benign", "value": "Likely benign"},
                                                {"label": "Benign", "value": "Benign"}
                                            ],
                                            value=["Pathogenic","Likely pathogenic","Uncertain significance","Likely benign","Benign"],  # Par défaut, toutes les options sont sélectionnées
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-stop-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by absolute position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-stop-prot', type='number', placeholder='Start pos', min=0, value = 1, step=1),
                                        dcc.Input(id='end-pos-stop-prot', type='number', placeholder='End pos', min=0, step=1)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-relative-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by relative position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-relative-prot', type='number', placeholder='Start ratio', min=0, max=1,value=0, step=0.01),
                                        dcc.Input(id='end-pos-relative-prot', type='number', placeholder='End ratio', min=0, max=1,value=1, step=0.01)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-stop-codon",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by stop codon:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="stop-codon-checklist",
                                            options=[
                                                {"label": "TGA", "value": "TGA"},
                                                {"label": "TAG", "value": "TAG"},
                                                {"label": "TAA", "value": "TAA"}
                                            ],
                                            value=["TGA", "TAG", "TAA"],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-nmd-sensitivity",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by NMD sensitivity:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="nmd-sensitivity-checklist",
                                            options=[
                                                {'label': 'Sensitive', 'value': 'sensitive'},
                                                {'label': 'Insensitive', 'value': 'insensitive'}
                                            ],
                                            value=['sensitive', 'insensitive'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-af-worldwide",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by worldwide allele frequency:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-af-worldwide', type='number', placeholder='Min AF', min=0, max=1, step=1e-10),
                                        dcc.Input(id='end-af-worldwide', type='number', placeholder='Max AF', min=0, max=1, step=1e-10)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-overlapping-domain",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by overlapping domain:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="overlapping-domain-checklist",
                                            options=[
                                                {'label': 'Overlapping', 'value': 'overlapping'},
                                                {'label': 'Non-Overlapping', 'value': 'non-overlapping'}
                                            ],
                                            value=['overlapping', 'non-overlapping'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button("Apply Filter", id="filter-button", color="primary"),
                                width={"size": 6, "offset": 3},
                            ),
                            className="mb-3",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Tabs([
                            dcc.Tab(id='tab-variations',
                                label=f"{disease_df.drop_duplicates(subset=['HGVSG'])['HGVSG'].nunique()} variations",
                                children=[
                                    dcc.Graph(
                                    id='patho-bar-chart',
                                figure=fig_patho
                            ),
                                dcc.Graph(
                                id='NMD-pie-chart',
                                figure=fig_nmd
                            ),
                            ]),
                            dcc.Tab(id='tab-genes',
                                label=f"{disease_df.drop_duplicates(subset=['HGVSG'])['symbol'].nunique()} genes", children=[
                                dcc.Graph(
                                id='top-genes-bar-chart',
                                figure=fig_top_genes
                                ),
                                dash_table.DataTable(
                                        id='table-genes',
                                        data=genes_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(genes_frequency_df[i]) else None} for i in genes_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in genes_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                html.Button("Download CSV", id="btn_csv_genes"),
                                dcc.Download(id="download-dataframe-csv-genes"),
                                dcc.Graph(
                                id='needle-plot',
                                style={'display': 'none'}
                                ),
                                html.Div(id='tab-diseases', style={'display': 'none'}),
                                dcc.Graph(
                                id='top-diseases-bar-chart',
                                style={'display': 'none'}
                                ),
                                dash_table.DataTable(
                                        id='table-diseases',
                                        style_table={'display': 'none'}
                                    ),
                            ]),
                            dcc.Tab(id='tab-phenotypes',
                                label=f"{disease_df['hpo_name'].nunique()} phenotypes",
                                children=[
                                    dcc.Graph(
                                        id='top-phenotypes-bar-chart',
                                        style={'display': 'none'}   
                                    ),
                                    dash_table.DataTable(
                                        id='table-phenotypes',
                                        data=phenotype_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(phenotype_frequency_df[i]) else None} for i in phenotype_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in phenotype_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                    html.Button("Download CSV", id="btn_csv_phenotypes"),
                                    dcc.Download(id="download-dataframe-csv-phenotypes")
                            ]),
                            dcc.Tab(label='Table', children=[
                                dash_table.DataTable(
                                    id='table-prefiltered',
                                    data=disease_df.drop(columns=['hpo_name']).drop_duplicates(subset=['HGVSG']).to_dict("records"),
                                    columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(disease_df.drop(columns=['hpo_name'])[i]) else None} for i in disease_df.drop(columns=['hpo_name']).drop_duplicates(subset=['HGVSG']).columns],
                                    style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'minWidth': 150,
                                    'font-family': 'system-ui',
                                        },
                                    style_cell_conditional=[
                                        {'if': {'column_id': c},
                                        'textAlign': 'center'} for c in disease_df.drop(columns=['hpo_name']).drop_duplicates(subset=['HGVSG']).columns],
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(211, 211, 211)'
                                        }
                                    ],
                                    style_header={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'width': 'auto',
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold',
                                        'fontSize': '12px'
                                    },
                                    style_table={'overflowX': 'auto'},
                                    style_as_list_view=True,
                                    filter_action='none',
                                    filter_query='',
                                    sort_action='native',
                                    sort_mode='multi',
                                    page_action='native',
                                    page_current=0,
                                    page_size=20,
                                    fixed_rows={'headers': True},
                                    fixed_columns={'headers': True},
                                    export_format="none",
                                    export_headers="none",
                                ),
                                html.Button("Download CSV", id="btn_csv"),
                                dcc.Download(id="download-dataframe-csv"),
                            ])
                        ])
                    ], width=10),
                ]),
                ]),disease_df.to_json(date_format='iso', orient='split')
        
        
        elif category == "phenotype":
            phenotype_df = driver.execute_query(f"MATCH (v:Variant)-[LOCATED_ON]-(g:Gene)-[CAUSED_BY]-(d:Disease)-[RECOGNIZABLE_BY]-(p:Phenotype) WHERE p.hpo_name = '{search_value}' RETURN p.hpo_id as hpo_id, p.comment as comment, p.definition as definition, d.disorder_name as disease, g.Symbol as symbol, v.HGVSG as HGVSG, v.Merged_Source as Source, v.ClinicalSignificance as ClinicalSignificance, v.pos_stop_prot as pos_stop_prot, v.pos_relative_prot as pos_relative_prot, v.pos_var_cds as pos_var_cds, v.nuc_upstream as nuc_upstream, v.codon_stop as codon_stop, v.nuc_downstream as nuc_downstream, v.exon_localization as exon_localization, v.NMD_sensitivity as NMD_sensitivity, v.AF_ww as AF,v.AF_afr as AF_afr, v.AF_amr as AF_amr, v.AF_asj as AF_asj, v.AF_eas as AF_eas, v.AF_fin as AF_fin, v.AF_mid as AF_mid, v.AF_nfe as AF_nfe, v.AF_sas as AF_sas, v.AF_remaining as AF_remaining, v.overlapping_domain as overlapping_domain, v.Origin as Origin, v.ReviewStatus as ReviewStatus",database_="neo4j",result_transformer_=neo4j.Result.to_df)
            hpo_id = phenotype_df['hpo_id'].iloc[0]
            comment = phenotype_df['comment'].iloc[0]
            definition = phenotype_df['definition'].iloc[0]
            phenotype_df = phenotype_df.drop(['hpo_id','comment','definition'], axis=1)
            #phenotype_disease_df = phenotype_df[['disease', 'symbol']].drop_duplicates(subset=['disease', 'symbol'])
            #phenotype_variation_df = phenotype_df[['symbol','HGVSG', 'Source', 'ClinicalSignificance', 'pos_stop_prot', 'pos_relative_prot', 'pos_var_cds', 'nuc_upstream', 'codon_stop', 'nuc_downstream', 'exon_localization', 'NMD_sensitivity', 'AF', 'AF_afr', 'AF_amr', 'AF_asj', 'AF_eas', 'AF_fin', 'AF_nfe', 'AF_oth', 'Origin', 'ReviewStatus']].drop_duplicates(subset=['HGVSG'])
            #phenotype_datatable = create_datatable(phenotype_df)
            # phenotype_graph = driver.execute_query(f"MATCH (p:Phenotype)-[r:RECOGNIZABLE_BY]-(d:Disease)-[c:CAUSED_BY]-(g:Gene)-[l:LOCATED_ON]-(v:Variant) WHERE p.HPO_label = '{search_value}' RETURN p, r, d, g, l, v",database_="neo4j",result_transformer_=neo4j.Result.graph)
            # phenotype_cyto = create_cyto_elements(phenotype_graph)
            
            # nmd_fig_df = phenotype_variation_df.groupby(['ClinicalSignificance', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="ClinicalSignificance", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Clinical significance",
            #     labels={'Count':'Count', 'ClinicalSignificance':'ClinicalSignificance'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
            nmd_fig_df = phenotype_df.drop_duplicates(subset=['HGVSG'])['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = phenotype_df.drop_duplicates(subset=['HGVSG'])['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([phenotype_df.drop_duplicates(subset=['HGVSG']), patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            
            top_genes_df = phenotype_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': phenotype_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().index,
                                       'Number of variations': phenotype_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            
            disease_counts = phenotype_df['disease'].value_counts().head(10)

            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']
            
            disease_frequency_df = pd.DataFrame({'disease_name': phenotype_df['disease'].value_counts().index,
                                       'Number of variations': phenotype_df['disease'].value_counts().values})

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)


            return html.Div([
                #html.H2(f"{search_value}", style={"text-align": "center"}),
                dbc.Card(
                        [
                            dbc.CardHeader(f"{search_value}", style={"text-align": "center","font-size": "larger", "font-weight": "bold"}),
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(html.P(f"HPO ID: {hpo_id}"), md=4),
                                            dbc.Col(html.P(f"Definition: {definition}"), md=4),
                                            dbc.Col(html.P(f"Comment: {comment}"), md=4),
                                        ],
                                        align="start",
                                    ),
                                ],
                                style={"height": "100%", "overflow": "auto", "background-color": "rgba(54, 155, 232, 0.3)"},
                            ),
                            dbc.CardFooter(
                                dbc.Button("More infos on HPO", href=f"https://hpo.jax.org/app/browse/term/{hpo_id}", target="_blank", color="primary", className="btn-sm ml-auto", style={"float": "right"}),
                            ),
                        ],
                        style={"margin-bottom": "2%", "overflow": "auto"},
                    ),
                html.H2(f"List of nonsense variations associated to {search_value}", style={
                "text-align": "left", 
                #"display": "inline-block", # Ceci permet au rectangle bleu de s'adapter à la taille du texte
                "padding-bottom": "0px" # Ajustez cette valeur pour changer la distance entre le titre et la bordure
                }),
                html.Hr(),
                dbc.Row([
                    dbc.Col([
                        dbc.Row(
                            id="filter-row-source",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by Source:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="source-checklist",
                                            options=[
                                                {'label': 'ClinVar', 'value': 'ClinVar'},
                                                {'label': 'gnomAD', 'value': 'gnomAD'},
                                                {'label': 'COSMIC', 'value': 'COSMIC'},
                                            ],
                                            value=['ClinVar', 'gnomAD', 'COSMIC'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-clinical-significance",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by ClinicalSignificance:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="clinical-significance-checklist",
                                            options=[
                                                {"label": "Pathogenic", "value": "Pathogenic"},
                                                {"label": "Likely pathogenic", "value": "Likely pathogenic"},
                                                {"label": "Uncertain significance", "value": "Uncertain significance"},
                                                {"label": "Likely benign", "value": "Likely benign"},
                                                {"label": "Benign", "value": "Benign"}
                                            ],
                                            value=["Pathogenic","Likely pathogenic","Uncertain significance","Likely benign","Benign"],  # Par défaut, toutes les options sont sélectionnées
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-stop-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by absolute position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-stop-prot', type='number', placeholder='Start pos', min=0, value = 1, step=1),
                                        dcc.Input(id='end-pos-stop-prot', type='number', placeholder='End pos', min=0, step=1)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-pos-relative-prot",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by relative position of the stop codon in the protein:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-pos-relative-prot', type='number', placeholder='Start ratio', min=0, max=1,value=0, step=0.01),
                                        dcc.Input(id='end-pos-relative-prot', type='number', placeholder='End ratio', min=0, max=1,value=1, step=0.01)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-stop-codon",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by stop codon:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="stop-codon-checklist",
                                            options=[
                                                {"label": "TGA", "value": "TGA"},
                                                {"label": "TAG", "value": "TAG"},
                                                {"label": "TAA", "value": "TAA"}
                                            ],
                                            value=["TGA", "TAG", "TAA"],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-nmd-sensitivity",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by NMD sensitivity:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="nmd-sensitivity-checklist",
                                            options=[
                                                {'label': 'Sensitive', 'value': 'sensitive'},
                                                {'label': 'Insensitive', 'value': 'insensitive'}
                                            ],
                                            value=['sensitive', 'insensitive'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-af-worldwide",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by worldwide allele frequency:", style={"font-weight": "bold"}),
                                        dcc.Input(id='start-af-worldwide', type='number', placeholder='Min AF', min=0, max=1, step=1e-10),
                                        dcc.Input(id='end-af-worldwide', type='number', placeholder='Max AF', min=0, max=1, step=1e-10)
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            id="filter-row-overlapping-domain",
                            children=[
                                dbc.Col(
                                    [
                                        html.Label("Filter by overlapping domain:", style={"font-weight": "bold"}),
                                        dcc.Checklist(
                                            id="overlapping-domain-checklist",
                                            options=[
                                                {'label': 'Overlapping', 'value': 'overlapping'},
                                                {'label': 'Non-Overlapping', 'value': 'non-overlapping'}
                                            ],
                                            value=['overlapping', 'non-overlapping'],
                                            inline=True
                                        ),
                                    ],
                                    md=12
                                ),
                            ],
                            className="g-0",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button("Apply Filter", id="filter-button", color="primary"),
                                width={"size": 6, "offset": 3},
                            ),
                            className="mb-3",
                        ),
                    ], width=2),
                    dbc.Col([
                        dcc.Tabs([
                            dcc.Tab(id='tab-variations',
                                label=f"{phenotype_df.drop_duplicates(subset=['HGVSG'])['HGVSG'].nunique()} variations",
                                children=[
                                dcc.Graph(
                                    id='patho-bar-chart',
                                    figure=fig_patho
                            ),
                                dcc.Graph(
                                    id='NMD-pie-chart',
                                    figure=fig_nmd
                            ),
                            ]),
                            dcc.Tab(id='tab-genes',
                                label=f"{phenotype_df.drop_duplicates(subset=['HGVSG'])['symbol'].nunique()} genes",
                                children=[
                                    dcc.Graph(
                                        id='top-genes-bar-chart',
                                        figure=fig_top_genes
                                    ),
                                    dcc.Graph(
                                        id='needle-plot',
                                        style={'display': 'none'}
                                    ),
                                    dash_table.DataTable(
                                        id='table-genes',
                                        data=genes_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(genes_frequency_df[i]) else None} for i in genes_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in genes_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                    html.Button("Download CSV", id="btn_csv_genes"),
                                    dcc.Download(id="download-dataframe-csv-genes"),
                            ]),
                            dcc.Tab(id='tab-diseases',
                                label=f"{phenotype_df['disease'].nunique()} diseases", children=[
                                dcc.Graph(
                                id='top-diseases-bar-chart',
                                figure=fig_top_diseases
                                ),
                                dash_table.DataTable(
                                        id='table-diseases',
                                        data=disease_frequency_df.to_dict("records"),
                                        columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(disease_frequency_df[i]) else None} for i in disease_frequency_df.columns],
                                        style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'minWidth': 150,
                                        'font-family': 'system-ui',
                                            },
                                        style_cell_conditional=[
                                            {'if': {'column_id': c},
                                            'textAlign': 'center'} for c in disease_frequency_df.columns],
                                        style_data_conditional=[
                                            {
                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(211, 211, 211)'
                                            }
                                        ],
                                        style_header={
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'width': 'auto',
                                            'backgroundColor': 'rgb(230, 230, 230)',
                                            'fontWeight': 'bold',
                                            'fontSize': '12px'
                                        },
                                        style_table={'overflowX': 'auto'},
                                        style_as_list_view=True,
                                        filter_action='none',
                                        filter_query='',
                                        sort_action='native',
                                        sort_mode='multi',
                                        page_action='native',
                                        page_current=0,
                                        page_size=20,
                                        fixed_rows={'headers': True},
                                        fixed_columns={'headers': True},
                                        export_format="none",
                                        export_headers="none",
                                    ),
                                html.Button("Download CSV", id="btn_csv_diseases"),
                                dcc.Download(id="download-dataframe-csv-diseases"),
                                html.Div(id='tab-phenotypes', style={'display': 'none'}),
                                dcc.Graph(
                                id='top-phenotypes-bar-chart',
                                style={'display': 'none'}
                                ),
                                dash_table.DataTable(
                                        id='table-phenotypes',
                                        style_table={'display': 'none'}
                                    ),
                            ]),
                            dcc.Tab(label='Table', children=[
                                dash_table.DataTable(
                                    id='table-prefiltered',
                                    data=phenotype_df.drop(columns=['disease']).drop_duplicates(subset=['HGVSG']).to_dict("records"),
                                    columns=[{"name": i, "id": i,'hideable':True, 'type': 'numeric' if pd.api.types.is_numeric_dtype(phenotype_df.drop(columns=['disease'])[i]) else None} for i in phenotype_df.drop(columns=['disease']).drop_duplicates(subset=['HGVSG']).columns],
                                    style_cell={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                    'minWidth': 150,
                                    'font-family': 'system-ui',
                                        },
                                    style_cell_conditional=[
                                        {'if': {'column_id': c},
                                        'textAlign': 'center'} for c in phenotype_df.drop(columns=['disease']).drop_duplicates(subset=['HGVSG']).columns],
                                    style_data_conditional=[
                                        {
                                            'if': {'row_index': 'odd'},
                                            'backgroundColor': 'rgb(211, 211, 211)'
                                        }
                                    ],
                                    style_header={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'width': 'auto',
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold',
                                        'fontSize': '12px'
                                    },
                                    style_table={'overflowX': 'auto'},
                                    style_as_list_view=True,
                                    filter_action='none',
                                    filter_query='',
                                    sort_action='native',
                                    sort_mode='multi',
                                    page_action='native',
                                    page_current=0,
                                    page_size=20,
                                    fixed_rows={'headers': True},
                                    fixed_columns={'headers': True},
                                    export_format="none",
                                    export_headers="none",
                                ),
                                html.Button("Download CSV", id="btn_csv"),
                                dcc.Download(id="download-dataframe-csv"),
                            ])
                        ])
                    ], width=10),
                ]),
                ]),phenotype_df.to_json(date_format='iso', orient='split')
        
        
        
        # elif category == "variation":
        #     query = f"MATCH (v:Variant)-[LOCATED_ON]-(g:Gene) WHERE v.HGVSG = '{search_value}' RETURN g.Symbol, v.HGVSG as HGVSG"

    #     results = db_manager.run_query(query)

    #     df = pd.DataFrame([dict(record) for record in results])

    #     return dash_table.DataTable(
    #         data=df.to_dict("records"),
    #         columns=[{"name": i, "id": i} for i in df.columns],
    #         style_cell_conditional=[
    #     {'if': {'column_id': c},
    #      'textAlign': 'left'} for c in df.columns],
    # style_data_conditional=[
    #     {
    #         'if': {'row_index': 'odd'},
    #         'backgroundColor': 'rgb(248, 248, 248)'
    #     }
    # ],
    # style_header={
    #     'backgroundColor': 'rgb(230, 230, 230)',
    #     'fontWeight': 'bold'
    # },
    # filter_action='none',
    # sort_action="native",
    # export_format="csv",
    #     )
    else:
        raise dash.exceptions.PreventUpdate
    
@app.callback(
    [Output("table-prefiltered", "data"),
     Output("patho-bar-chart", "figure"),
     Output("NMD-pie-chart", "figure"),
     Output("top-genes-bar-chart", "figure"),
     Output("top-diseases-bar-chart", "figure"),
     Output("top-phenotypes-bar-chart", "figure"),
     Output("needle-plot", "mutationData"),
     Output("needle-plot", "needleStyle"),
     Output("tab-variations", "label"),
     Output("tab-genes", "label"),
     Output("tab-diseases", "label"),
     Output("tab-phenotypes", "label"),
     Output("table-genes", "data"),
     Output("table-diseases", "data"),
     Output("table-phenotypes", "data"),],
    [Input("filter-button", "n_clicks"),
     Input("stored-df", "data")],
    [State("source-checklist", "value"),
     State("clinical-significance-checklist", "value"),
     State("start-pos-stop-prot", "value"),
     State("end-pos-stop-prot", "value"),
     State("start-pos-relative-prot", "value"),
     State("end-pos-relative-prot", "value"),
     State("stop-codon-checklist", "value"),
     State("nmd-sensitivity-checklist", "value"),
     State("start-af-worldwide", "value"),
     State("end-af-worldwide", "value"),
     State("overlapping-domain-checklist", "value"),
     State("category-dropdown", "value"), 
     State("search-dropdown", "value")]
)
def filter_data(n_clicks, data, source_values, clinical_significance_values, start_pos_stop_prot_value, end_pos_stop_prot_value, start_pos_relative_value, end_pos_relative_value, stop_codon_values, nmd_sensitivity_values, start_af_worldwide_value, end_af_worldwide_value, overlapping_domain_values, category, search_value):
    if n_clicks > 0:
        # Choose the query based on the category
        if category == "StopKB":
            #StopKB_df = pd.read_json(data, orient='split')
            # Apply filtering based on Source
            filtered_df = StopKB_df[StopKB_df["Source"].apply(lambda x: any(source in x.split(';') for source in source_values))]
            
            # Apply filtering based on ClinicalSignificance
            filtered_df = filtered_df[filtered_df["ClinicalSignificance"].isin(clinical_significance_values)]

            # Apply filtering based on absolute position of the stop codon in the protein
            if start_pos_stop_prot_value is not None and end_pos_stop_prot_value is not None:
                filtered_df = filtered_df[filtered_df["pos_stop_prot"].between(start_pos_stop_prot_value, end_pos_stop_prot_value)]
            
            # Apply filtering based on relative position of the stop codon in the protein
            if start_pos_relative_value is not None and end_pos_relative_value is not None:
                filtered_df = filtered_df[filtered_df["pos_relative_prot"].between(start_pos_relative_value, end_pos_relative_value)]

            # Apply filtering based on stop codon
            filtered_df = filtered_df[filtered_df["codon_stop"].isin(stop_codon_values)]
            
            # Apply filtering based on NMD sensitivity
            filtered_df = filtered_df[filtered_df["NMD_sensitivity"].isin(nmd_sensitivity_values)]
            
            # Apply filtering based on worldwide allele frequency
            if start_af_worldwide_value is not None and end_af_worldwide_value is not None:
                filtered_df = filtered_df[filtered_df["AF"].between(start_af_worldwide_value, end_af_worldwide_value)]
            
            # Apply filtering based on overlapping_domain   
            if 'overlapping' in overlapping_domain_values and 'non-overlapping' in overlapping_domain_values:
                # No filtering if the two options are selected
                pass
            elif 'overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].notna()]
            elif 'non-overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].isna()]
            
            filtered_preview_df = filtered_df.iloc[:1000]

            # nmd_fig_df = filtered_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
            
            nmd_fig_df = filtered_df['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity', values='Count', 
                 title='Distribution of NMD sensitivity',
                 color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity')
            
            patho_fig_expanded_sources_df = filtered_df['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([StopKB_df, patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            top_genes_df = filtered_df['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': filtered_df['symbol'].value_counts().index,
                                       'Number of variations': filtered_df['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            
            exploded_diseases = filtered_df['disease_name'].str.split('; ').explode()
            disease_counts = exploded_diseases.value_counts().head(10)

            # Créer un DataFrame pour le graphique
            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']
            
            disease_frequency_df = pd.DataFrame({'disease_name': exploded_diseases.value_counts().index,
                                       'Number of variations': exploded_diseases.value_counts().values})

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            exploded_phenotypes = filtered_df['phenotype_name'].str.split('; ').explode()
            phenotype_counts = exploded_phenotypes.value_counts().head(10)

            # Créer un DataFrame pour le graphique
            top_phenotypes_df = phenotype_counts.reset_index()
            top_phenotypes_df.columns = ['Phenotype', 'Count']
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': exploded_phenotypes.value_counts().index,
                                       'Number of variations': exploded_phenotypes.value_counts().values})

            # Créer le graphique à barres
            fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
                        title='Top phenotypes',
                        labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            fig_top_phenotypes.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            tab_variations = f"{filtered_df['HGVSG'].nunique()} variations"
            
            tab_genes = f"{filtered_df['symbol'].nunique()} genes"
            
            tab_diseases = f"{exploded_diseases.nunique()} diseases"
            
            tab_phenotypes = f"{exploded_phenotypes.nunique()} phenotypes"
            
            return filtered_preview_df.to_dict("records"), fig_patho, fig_nmd, fig_top_genes, fig_top_diseases, fig_top_phenotypes, dash.no_update, dash.no_update, tab_variations, tab_genes, tab_diseases, tab_phenotypes, genes_frequency_df.to_dict("records"), disease_frequency_df.to_dict("records"), phenotype_frequency_df.to_dict("records")
        
        elif category == "gene":
            gene_df = pd.read_json(data, orient='split')
            
            # Apply filtering based on Source
            filtered_df = gene_df[gene_df["Source"].apply(lambda x: any(source in x.split(';') for source in source_values))]
            
            # Apply filtering based on ClinicalSignificance
            filtered_df = filtered_df[filtered_df["ClinicalSignificance"].isin(clinical_significance_values)]

            # Apply filtering based on absolute position of the stop codon in the protein
            if start_pos_stop_prot_value is not None and end_pos_stop_prot_value is not None:
                filtered_df = filtered_df[filtered_df["pos_stop_prot"].between(start_pos_stop_prot_value, end_pos_stop_prot_value)]
            
            # Apply filtering based on relative position of the stop codon in the protein
            if start_pos_relative_value is not None and end_pos_relative_value is not None:
                filtered_df = filtered_df[filtered_df["pos_relative_prot"].between(start_pos_relative_value, end_pos_relative_value)]

            # Apply filtering based on stop codon
            filtered_df = filtered_df[filtered_df["codon_stop"].isin(stop_codon_values)]
            
            # Apply filtering based on NMD sensitivity
            filtered_df = filtered_df[filtered_df["NMD_sensitivity"].isin(nmd_sensitivity_values)]
            
            # Apply filtering based on worldwide allele frequency
            if start_af_worldwide_value is not None and end_af_worldwide_value is not None:
                filtered_df = filtered_df[filtered_df["AF"].between(start_af_worldwide_value, end_af_worldwide_value)]
                
            # Apply filtering based on overlapping_domain   
            if 'overlapping' in overlapping_domain_values and 'non-overlapping' in overlapping_domain_values:
                # No filtering if the two options are selected
                pass
            elif 'overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].notna()]
            elif 'non-overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].isna()]
                
            unique_StopKB_df = StopKB_df.drop_duplicates(subset='symbol')
                
            fig_df = pd.merge(filtered_df, unique_StopKB_df[['symbol', 'disease_name', 'phenotype_name']], how='left', on='symbol')
                
            # nmd_fig_df = filtered_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
                        
            nmd_fig_df = fig_df['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = fig_df['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([fig_df, patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            
            exploded_diseases = fig_df['disease_name'].str.split('; ').explode()
            disease_counts = exploded_diseases.value_counts().head(10)
            
            disease_frequency_df = pd.DataFrame({'disease_name': exploded_diseases.value_counts().index,
                                       'Number of variations': exploded_diseases.value_counts().values})

            # Créer un DataFrame pour le graphique
            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            exploded_phenotypes = fig_df['phenotype_name'].str.split('; ').explode()
            phenotype_counts = exploded_phenotypes.value_counts().head(10)
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': exploded_phenotypes.value_counts().index,
                                       'Number of variations': exploded_phenotypes.value_counts().values})

            # Créer un DataFrame pour le graphique
            # top_phenotypes_df = phenotype_counts.reset_index()
            # top_phenotypes_df.columns = ['Phenotype', 'Count']

            # # Créer le graphique à barres
            # fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
            #             title='Top phenotypes',
            #             labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            # fig_top_phenotypes.update_layout(font_family="system-ui",
            #                             title_x=0.5,
            #                             xaxis_tickangle=-15,
            #                             xaxis_tickfont_size=12)
            
            filtered_needle_df = pd.merge(filtered_df.drop_duplicates(subset=['symbol']), gene_domains, how='left', on='symbol')
            
            domain_data = []

            # Itération sur chaque colonne de domaine dans gene_df
            for col in filtered_needle_df.filter(like='domain_'):
                for domain_str in filtered_needle_df[col].dropna():
                    # Séparation de la chaîne en prenant en compte le dernier ';' comme séparateur
                    *name_parts, start, end = domain_str.rsplit(';', 2)
                    name = ';'.join(name_parts)  # Reconstruction du nom si nécessaire
                    if len(name) > 20:
                        name = name[:20] + '...'
                    coord = f"{start}-{end}"
                    domain_data.append({'name': name, 'coord': coord})
                    
            mutation_data = {
                'x': filtered_df.astype({'pos_stop_prot':'string'})['pos_stop_prot'].tolist(),
                'y': ["1"] * len(filtered_df),  
                'mutationGroups': filtered_df['ClinicalSignificance'].tolist(),
                'domains': domain_data, 
            }
            
            colors_map = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
                        
            unique_categories = list(dict.fromkeys(mutation_data['mutationGroups']))

            unique_colors = [colors_map.get(category, "default_color") for category in unique_categories]
            
            needle_style = {
                'headSize': 10,
                'headColor': unique_colors
            }
            
            tab_variations = f"{fig_df['HGVSG'].nunique()} variations"
            
            tab_diseases = f"{exploded_diseases.nunique()} diseases"
            
            tab_phenotypes = f"{exploded_phenotypes.nunique()} phenotypes"
            
            return filtered_df.to_dict("records"), fig_patho, fig_nmd, dash.no_update, fig_top_diseases, dash.no_update, mutation_data, needle_style, tab_variations, dash.no_update, tab_diseases, tab_phenotypes, dash.no_update, disease_frequency_df.to_dict("records"), phenotype_frequency_df.to_dict("records")
        
        elif category == "disease":
            disease_df = pd.read_json(data, orient='split')
            # Apply filtering based on Source
            filtered_df = disease_df[disease_df["Source"].apply(lambda x: any(source in x.split(';') for source in source_values))]
            
            # Apply filtering based on ClinicalSignificance
            filtered_df = filtered_df[filtered_df["ClinicalSignificance"].isin(clinical_significance_values)]

            # Apply filtering based on absolute position of the stop codon in the protein
            if start_pos_stop_prot_value is not None and end_pos_stop_prot_value is not None:
                filtered_df = filtered_df[filtered_df["pos_stop_prot"].between(start_pos_stop_prot_value, end_pos_stop_prot_value)]
            
            # Apply filtering based on relative position of the stop codon in the protein
            if start_pos_relative_value is not None and end_pos_relative_value is not None:
                filtered_df = filtered_df[filtered_df["pos_relative_prot"].between(start_pos_relative_value, end_pos_relative_value)]

            # Apply filtering based on stop codon
            filtered_df = filtered_df[filtered_df["codon_stop"].isin(stop_codon_values)]
            
            # Apply filtering based on NMD sensitivity
            filtered_df = filtered_df[filtered_df["NMD_sensitivity"].isin(nmd_sensitivity_values)]
            
            # Apply filtering based on worldwide allele frequency
            if start_af_worldwide_value is not None and end_af_worldwide_value is not None:
                filtered_df = filtered_df[filtered_df["AF"].between(start_af_worldwide_value, end_af_worldwide_value)]
                
            # Apply filtering based on overlapping_domain   
            if 'overlapping' in overlapping_domain_values and 'non-overlapping' in overlapping_domain_values:
                # No filtering if the two options are selected
                pass
            elif 'overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].notna()]
            elif 'non-overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].isna()]
                
                
            # nmd_fig_df = filtered_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
                        
            nmd_fig_df = filtered_df.drop_duplicates(subset=['HGVSG'])['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = filtered_df.drop_duplicates(subset=['HGVSG'])['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([filtered_df.drop_duplicates(subset=['HGVSG']), patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            top_genes_df = filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().index,
                                       'Number of variations': filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            phenotype_counts = filtered_df['hpo_name'].value_counts().head(10)
            
            phenotype_frequency_df = pd.DataFrame({'phenotype_name': filtered_df['hpo_name'].value_counts().index,
                                       'Number of variations': filtered_df['hpo_name'].value_counts().values})

            # Créer un DataFrame pour le graphique
            # top_phenotypes_df = phenotype_counts.reset_index()
            # top_phenotypes_df.columns = ['Phenotype', 'Count']

            # # Créer le graphique à barres
            # fig_top_phenotypes = px.bar(top_phenotypes_df, x='Phenotype', y='Count', color_discrete_sequence=['#FA0087'],
            #             title='Top phenotypes',
            #             labels={'Phenotype': 'Phenotype', 'Count': 'Number of variations'})
            
            # fig_top_phenotypes.update_layout(font_family="system-ui",
            #                             title_x=0.5,
            #                             xaxis_tickangle=-15,
            #                             xaxis_tickfont_size=12)
            
            tab_variations = f"{filtered_df['HGVSG'].nunique()} variations"
            
            tab_genes = f"{filtered_df['symbol'].nunique()} genes"
            
            tab_phenotypes = f"{filtered_df['hpo_name'].nunique()} phenotypes"
            
            return filtered_df.drop_duplicates(subset=['HGVSG']).to_dict("records"), fig_patho, fig_nmd, fig_top_genes, dash.no_update, dash.no_update, dash.no_update, dash.no_update, tab_variations, tab_genes, dash.no_update, tab_phenotypes, genes_frequency_df.to_dict("records"), dash.no_update, phenotype_frequency_df.to_dict("records")
        
        elif category == "phenotype":
            phenotype_df = pd.read_json(data, orient='split')
            # Apply filtering based on Source
            filtered_df = phenotype_df[phenotype_df["Source"].apply(lambda x: any(source in x.split(';') for source in source_values))]
            
            # Apply filtering based on ClinicalSignificance
            filtered_df = filtered_df[filtered_df["ClinicalSignificance"].isin(clinical_significance_values)]

            # Apply filtering based on absolute position of the stop codon in the protein
            if start_pos_stop_prot_value is not None and end_pos_stop_prot_value is not None:
                filtered_df = filtered_df[filtered_df["pos_stop_prot"].between(start_pos_stop_prot_value, end_pos_stop_prot_value)]
            
            # Apply filtering based on relative position of the stop codon in the protein
            if start_pos_relative_value is not None and end_pos_relative_value is not None:
                filtered_df = filtered_df[filtered_df["pos_relative_prot"].between(start_pos_relative_value, end_pos_relative_value)]

            # Apply filtering based on stop codon
            filtered_df = filtered_df[filtered_df["codon_stop"].isin(stop_codon_values)]
            
            # Apply filtering based on NMD sensitivity
            filtered_df = filtered_df[filtered_df["NMD_sensitivity"].isin(nmd_sensitivity_values)]
            
            # Apply filtering based on worldwide allele frequency
            if start_af_worldwide_value is not None and end_af_worldwide_value is not None:
                filtered_df = filtered_df[filtered_df["AF"].between(start_af_worldwide_value, end_af_worldwide_value)]
                
            # Apply filtering based on overlapping_domain   
            if 'overlapping' in overlapping_domain_values and 'non-overlapping' in overlapping_domain_values:
                # No filtering if the two options are selected
                pass
            elif 'overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].notna()]
            elif 'non-overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].isna()]
                
                
            # nmd_fig_df = filtered_df.groupby(['Source', 'NMD_sensitivity']).size().reset_index(name='counts')
            # nmd_fig_df = nmd_fig_df.sort_values(by=['counts'], ascending=False)

            # fig_nmd = px.bar(nmd_fig_df, x="Source", y="counts", color="NMD_sensitivity",              
            #     title="NMD Sensitivity by Source",
            #     labels={'Count':'Count', 'Source':'Source'},
            #     color_discrete_sequence=px.colors.sequential.Plasma_r)
            # fig_nmd.update_layout(font_family="system-ui", title_x=0.5)
                        
            nmd_fig_df = filtered_df.drop_duplicates(subset=['HGVSG'])['NMD_sensitivity'].value_counts().reset_index()
            nmd_fig_df.columns = ['NMD_sensitivity', 'Count']
            
            pie_colors = ['#F6222E' if sensitivity == 'sensitive' else '#1CBE4F' for sensitivity in nmd_fig_df['NMD_sensitivity']]

            # Créer le graphique Pie Chart pour 'NMD_sensitivity'
            fig_nmd = px.pie(nmd_fig_df, names='NMD_sensitivity',
                values='Count', 
                title='Distribution of NMD sensitivity',
                color_discrete_sequence=pie_colors)

            # Mise à jour de la mise en page
            fig_nmd.update_layout(legend_title='NMD Sensitivity',
                font_family="system-ui",
                title_x=0.5)
            
            
            patho_fig_expanded_sources_df = filtered_df.drop_duplicates(subset=['HGVSG'])['Source'].str.get_dummies(sep=';')

            # Fusion des sources étendues avec le dataframe original
            patho_fig_with_sources_df = pd.concat([filtered_df.drop_duplicates(subset=['HGVSG']), patho_fig_expanded_sources_df], axis=1)

            # Transformation du dataframe en format long pour Plotly
            patho_fig_melted_df = patho_fig_with_sources_df.melt(id_vars='ClinicalSignificance', 
                                            value_vars=patho_fig_expanded_sources_df.columns, 
                                            var_name='Source', value_name='Count')

            # Filtrage des lignes avec un comptage zéro
            patho_fig_melted_df = patho_fig_melted_df[patho_fig_melted_df['Count'] > 0]

            # Regroupement par Source et ClinicalSignificance et somme des comptages
            patho_fig_df = patho_fig_melted_df.groupby(['Source', 'ClinicalSignificance']).sum().reset_index()
            patho_fig_df = patho_fig_df.sort_values(by=['Count'], ascending=False)
            
            # Définition des couleurs spécifiques pour chaque catégorie de Clinical Significance
            colors_patho = {
                'Benign': '#1CBE4F',
                'Likely benign': '#16FF32',
                'Uncertain significance': '#FBE426',
                'Likely pathogenic': '#FEAF16',
                'Pathogenic': '#F6222E'
            }
            # Création du graphique Plotly
            fig_patho = px.bar(patho_fig_df, x='Source', y='Count', color='ClinicalSignificance', 
                        title='Clinical significance by Source',
                        barmode='stack',
                        color_discrete_map=colors_patho)

            # Mise à jour de la mise en page
            fig_patho.update_layout(xaxis_title='Source',
                                    yaxis_title='Number of Variations',
                                    legend_title='Clinical Significance',
                                    font_family="system-ui",
                                    title_x=0.5)
            
            top_genes_df = filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().head(10).reset_index()
            top_genes_df.columns = ['Gene', 'Count']
            
            genes_frequency_df = pd.DataFrame({'symbol': filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().index,
                                       'Number of variations': filtered_df.drop_duplicates(subset=['HGVSG'])['symbol'].value_counts().values})

            # Créer le graphique à barres
            fig_top_genes = px.bar(top_genes_df, x='Gene', y='Count', color_discrete_sequence=['#F6222E'],
                        title='Top genes',
                        labels={'Gene': 'Gene', 'Count': 'Number of Variations'})
            
            fig_top_genes.update_layout(font_family="system-ui",
                                        title_x=0.5)
            
            disease_counts = filtered_df['disease'].value_counts().head(10)

            top_diseases_df = disease_counts.reset_index()
            top_diseases_df.columns = ['Disease', 'Count']
            
            disease_frequency_df = pd.DataFrame({'disease_name': filtered_df['disease'].value_counts().index,
                                       'Number of variations': filtered_df['disease'].value_counts().values})

            # Créer le graphique à barres
            fig_top_diseases = px.bar(top_diseases_df, x='Disease', y='Count', color_discrete_sequence=['#FBE426'],
                        title='Top diseases',
                        labels={'Disease': 'Disease', 'Count': 'Number of variations'})
            
            fig_top_diseases.update_layout(font_family="system-ui",
                                        title_x=0.5,
                                        xaxis_tickangle=-15,
                                        xaxis_tickfont_size=12)
            
            tab_variations = f"{filtered_df['HGVSG'].nunique()} variations"
            
            tab_genes = f"{filtered_df['symbol'].nunique()} genes"
            
            tab_diseases = f"{filtered_df['disease'].nunique()} diseases"

            
            return filtered_df.drop_duplicates(subset=['HGVSG']).to_dict("records"), fig_patho, fig_nmd, fig_top_genes, fig_top_diseases, dash.no_update, dash.no_update, dash.no_update, tab_variations, tab_genes, tab_diseases, dash.no_update, genes_frequency_df.to_dict("records"), disease_frequency_df.to_dict("records"), dash.no_update
        
@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    [State("category-dropdown", "value"),
    State("table-prefiltered", "data"),
    State("source-checklist", "value"),
    State("clinical-significance-checklist", "value"),
    State("start-pos-stop-prot", "value"),
    State("end-pos-stop-prot", "value"),
    State("start-pos-relative-prot", "value"),
    State("end-pos-relative-prot", "value"),
    State("stop-codon-checklist", "value"),
    State("nmd-sensitivity-checklist", "value"),
    State("start-af-worldwide", "value"),
    State("end-af-worldwide", "value"),
    State("overlapping-domain-checklist", "value")],
)
def download_table(n_clicks,category,data, source_values, clinical_significance_values, start_pos_stop_prot_value, end_pos_stop_prot_value, start_pos_relative_value, end_pos_relative_value, stop_codon_values, nmd_sensitivity_values, start_af_worldwide_value, end_af_worldwide_value, overlapping_domain_values):
    if n_clicks > 0:
        if category == "StopKB":
            filtered_df = StopKB_df[StopKB_df["Source"].apply(lambda x: any(source in x.split(';') for source in source_values))]
            
            # Apply filtering based on ClinicalSignificance
            filtered_df = filtered_df[filtered_df["ClinicalSignificance"].isin(clinical_significance_values)]

            # Apply filtering based on absolute position of the stop codon in the protein
            if start_pos_stop_prot_value is not None and end_pos_stop_prot_value is not None:
                filtered_df = filtered_df[filtered_df["pos_stop_prot"].between(start_pos_stop_prot_value, end_pos_stop_prot_value)]
            
            # Apply filtering based on relative position of the stop codon in the protein
            if start_pos_relative_value is not None and end_pos_relative_value is not None:
                filtered_df = filtered_df[filtered_df["pos_relative_prot"].between(start_pos_relative_value, end_pos_relative_value)]

            # Apply filtering based on stop codon
            filtered_df = filtered_df[filtered_df["codon_stop"].isin(stop_codon_values)]
            
            # Apply filtering based on NMD sensitivity
            filtered_df = filtered_df[filtered_df["NMD_sensitivity"].isin(nmd_sensitivity_values)]
            
            # Apply filtering based on worldwide allele frequency
            if start_af_worldwide_value is not None and end_af_worldwide_value is not None:
                filtered_df = filtered_df[filtered_df["AF"].between(start_af_worldwide_value, end_af_worldwide_value)]
            
            # Apply filtering based on overlapping_domain   
            if 'overlapping' in overlapping_domain_values and 'non-overlapping' in overlapping_domain_values:
                # No filtering if the two options are selected
                pass
            elif 'overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].notna()]
            elif 'non-overlapping' in overlapping_domain_values:
                filtered_df = filtered_df[filtered_df['overlapping_domain'].isna()]
                
            return dcc.send_data_frame(filtered_df.drop(columns=['Cytogenetic','RefSeq_nuc','Ensembl_nuc','RefSeq_prot','Ensembl_prot','uniprot_id','prot_length','exon_counts','disorder_id','name','orpha_code','definition','prevalence_geo','hpo_id','hpo_name','comment','definition_x','disease_name','phenotype_name']).to_csv, "data.csv")
        elif category == "gene":
            gene_df = pd.DataFrame(data)
            return dcc.send_data_frame(gene_df.to_csv, "data.csv")
        elif category == "disease":
            disease_df = pd.DataFrame(data)
            return dcc.send_data_frame(disease_df.to_csv, "data.csv")
        elif category == "phenotype":
            phenotype_df = pd.DataFrame(data)
            return dcc.send_data_frame(phenotype_df.to_csv, "data.csv")
        
@app.callback(
    Output("download-dataframe-csv-genes", "data"),
    Input("btn_csv_genes", "n_clicks"),
    [State("category-dropdown", "value"),
    State("table-genes", "data"),]
    )
def download_table_genes(n_clicks,category,data):
    if n_clicks > 0:
            gene_df = pd.DataFrame(data)
            return dcc.send_data_frame(gene_df.to_csv, "data.csv")
        
@app.callback(
    Output("download-dataframe-csv-diseases", "data"),
    Input("btn_csv_diseases", "n_clicks"),
    [State("category-dropdown", "value"),
    State("table-diseases", "data"),]
    )
def download_table_diseases(n_clicks,category,data):
    if n_clicks > 0:
            disease_df = pd.DataFrame(data)
            return dcc.send_data_frame(disease_df.to_csv, "data.csv")
        
@app.callback(
    Output("download-dataframe-csv-phenotypes", "data"),
    Input("btn_csv_phenotypes", "n_clicks"),
    [State("category-dropdown", "value"),
    State("table-phenotypes", "data"),]
    )
def download_table_phenotypes(n_clicks,category,data):
    if n_clicks > 0:
            phenotype_df = pd.DataFrame(data)
            return dcc.send_data_frame(phenotype_df.to_csv, "data.csv")
        

if __name__ == '__main__':
    if os.getenv("PROFILER", None):
        app.server.config["PROFILE"] = True
        app.server.wsgi_app = ProfilerMiddleware(
            app.server.wsgi_app, sort_by=("cumtime", "tottime"), restrictions=[50]
        )
    app.run(debug=False,port=8051,host='0.0.0.0')
