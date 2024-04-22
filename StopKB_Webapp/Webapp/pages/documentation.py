import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback, Input, Output
import pandas as pd
import plotly.express as px

df_variants = pd.read_csv("assets/flat_database/variant.csv", sep="\t")

# grouped_df = df_variants.groupby(['Merged_Source', 'NMD_sensitivity']).size().reset_index(name='counts')

# grouped_df = grouped_df.sort_values(by=['counts'], ascending=False)

# fig_nmd = px.bar(grouped_df, x="Merged_Source", y="counts", color="NMD_sensitivity",
#              title="NMD Sensitivity by Source",
#              labels={'Count':'Count', 'Source':'Source'},
#              color_discrete_sequence=px.colors.sequential.Plasma_r)

layout = dbc.Container(
    [
       html.Div(
            html.H1("Documentation"), 
            style={
                "text-align": "left", 
                "margin-top": "2%", 
                "border-bottom": "5px solid royalblue",
                "display": "inline-block",
                "padding-bottom": "0px"
            }),
       html.H2(
            "What is StopKB ?", 
            style={"margin-top": "2%", "text-align": "left"}
        ),
       html.Hr(),
       html.P(
            """StopKB is a graph-oriented approach that is designed to assist in the analysis, evaluation, and prioritization of nonsense mutations and diseases targeted for nonsense suppression therapy. This involves integrating features like the notion of nonsense-mediated mRNA decay for each nonsense variation. Moreover, StopKB incorporates the genome and nucleotide context of each nonsense variation, an important factor impacting the efficiency of readthrough therapies, as well as other nonsense suppression therapeutic strategies. StopKB incorporates a broad range of nonsense mutations detected not only in healthy individuals, but also in patients suffering from rare genetic diseases and cancers. StopKB should be of interest to researchers from divergent fields ranging from genetics to cancer and pharmacology for example.""", 
            style={"margin-top": "1%", "text-align": "left"}
        ),
       html.H2(
            "Release contents", 
            style={"margin-top": "2%", "text-align": "left"}
        ),
       html.Hr(),
       html.P(
            "StopKB Data release: 2024-04-18 - Neo4j v4.4.3", 
            style={"margin-top": "1%", "text-align": "left"}
        ),
       dbc.Table(
           [
               html.Thead(
                   html.Tr([
                       html.Th("Source"), 
                       html.Th("Description"), 
                       html.Th("Release"), 
                       html.Th("Last import")
                    ])
               ),
               html.Tbody(
                   [
                       html.Tr([
                           html.Td("Clinvar"),
                           html.Td("Clinically Relevant Variations"),
                           html.Td("Latest"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("COSMIC"),
                           html.Td("Catalogue of somatic mutations in cancer"),
                           html.Td("v99"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("gnomAD"),
                           html.Td("Genome Aggregation Database"),
                           html.Td("4.0.0"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("HPO"),
                           html.Td("Human Phenotype Ontology"),
                           html.Td("v2024-02-08"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("Orphanet"),
                           html.Td("Portal for rare diseases and orphan drugs"),
                           html.Td("Latest"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("InterPro"),
                           html.Td("Protein families, domains and functional sites"),
                           html.Td("Latest"),
                           html.Td("2024-04-18")
                       ]),
                       html.Tr([
                           html.Td("HGNC"),
                           html.Td("HUGO Gene Nomenclature Committee"),
                           html.Td("Latest"),
                           html.Td("2024-04-18")
                       ]),
                   ]
               ),
           ],
           bordered=True,
           hover=True,
           responsive=True,
           striped=True,
       ),
       html.H2(
            "Release statistics", 
            style={"margin-top": "2%", "text-align": "left"}
        ),
       html.Hr(),
       html.P(
            "Statistics concerning StopKB v2024-04-18:", 
            style={"margin-top": "1%", "text-align": "left"}
        ),
       html.Img(src='assets/icons/venn.png', style={'width': '50%', 'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto'}),
    #    dcc.Graph(
    #         id='NMD-documentation-bar-chart',
    #         figure=fig_nmd
    #     ),
       html.H2(
            "Understanding the data", 
            style={"margin-top": "2%", "text-align": "left"}
        ),
       html.Hr(),
       dbc.Table(
           [
               html.Thead(
                   html.Tr([
                       html.Th("Node"), 
                       html.Th("Property"), 
                       html.Th("Description")
                    ])
               ),
               html.Tbody(
                   [
                       html.Tr([
                           html.Td("Variant", rowSpan=25),
                           html.Td("HGVSG"),
                           html.Td("Unique identifier for a variant (Human Genome Variation Society genomic syntax (3' shifted))")
                       ]),
                       html.Tr([
                           html.Td("Name"),
                           html.Td("ClinVar's preferred name for the record")
                       ]),
                       html.Tr([
                           html.Td("ClinicalSignificance"),
                           html.Td("Value of clinical significance calculated for this variant (ACMG recommendations)")
                       ]),
                       html.Tr([
                           html.Td("Merged_Source"),
                           html.Td("Source of the variant")
                       ]),
                       html.Tr([
                           html.Td("Origin"),
                           html.Td("List of all allelic origins for this variant")
                       ]),
                       html.Tr([
                           html.Td("ReviewStatus"),
                           html.Td("Highest review status for reporting this measure")
                       ]),
                       html.Tr([
                           html.Td("pos_stop_prot"),
                           html.Td("Position of the premature termination/stop codon in the protein sequence")
                       ]),
                       html.Tr([
                           html.Td("pos_relative_prot"),
                           html.Td("Relative position of the premature termination codon in the protein sequence")
                       ]),
                       html.Tr([
                           html.Td("pos_var_cds"),
                           html.Td("Position of the nonsense variation in the coding DNA sequence (CDS)")
                       ]),
                       html.Tr([
                           html.Td("nuc_upstream"),
                           html.Td("The 3 nucleotides upstream of the premature termination codon (5' sided)")
                       ]),
                       html.Tr([
                           html.Td("codon_stop"),
                           html.Td("Identity of the premature termination codon")
                       ]),
                       html.Tr([
                           html.Td("nuc_downstream"),
                           html.Td("The 3 nucleotides downstream of the premature termination codon (3' sided)")
                       ]),
                       html.Tr([
                           html.Td("exon_localization"),
                           html.Td("In which exon is localized the variant")
                       ]),
                       html.Tr([
                           html.Td("NMD_sensitivity"),
                           html.Td("Nonsense-mediated mRNA decay (NMD) sensitivity of the variant")
                       ]),
                       html.Tr([
                           html.Td("AF_ww"),
                           html.Td("Allele Frequency in worldwide population")
                       ]),
                       html.Tr([
                           html.Td("AF_afr"),
                           html.Td("Allele Frequency in african population")
                       ]),
                       html.Tr([
                           html.Td("AF_amr"),
                           html.Td("Allele Frequency in admixed american population")
                       ]),
                       html.Tr([
                           html.Td("AF_asj"),
                           html.Td("Allele Frequency in ashkenazi jewish population")
                       ]),
                       html.Tr([
                           html.Td("AF_eas"),
                           html.Td("Allele Frequency in east asian population")
                       ]),
                       html.Tr([
                           html.Td("AF_fin"),
                           html.Td("Allele Frequency in finnish population")
                       ]),
                       html.Tr([
                           html.Td("AF_mid"),
                           html.Td("Allele Frequency in middle eastern population")
                       ]),
                       html.Tr([
                           html.Td("AF_nfe"),
                           html.Td("Allele Frequency in non-finnish European population")
                       ]),
                       html.Tr([
                           html.Td("AF_sas"),
                           html.Td("Allele Frequency in south asian population")
                       ]),
                       html.Tr([
                           html.Td("AF_remaining"),
                           html.Td("Allele Frequency in remaining population")
                       ]),
                       html.Tr([
                           html.Td("overlapping_domain"),
                           html.Td("In which domain is localized the variant")
                       ]),
                       #Gene
                       html.Tr([
                           html.Td("Gene", rowSpan=8),
                           html.Td("Symbol"),
                           html.Td("Gene symbol")
                       ]),
                       html.Tr([
                           html.Td("Cytogenetic"),
                           html.Td("International System for Human Cytogenomic Nomenclature (ISCN) cytogenetic location")
                       ]),
                       html.Tr([
                           html.Td("RefSeq_nuc"),
                           html.Td("RefSeq identifier for corresponding canonical transcript")
                       ]),
                       html.Tr([
                           html.Td("Ensembl_nuc"),
                           html.Td("Ensembl identifier for corresponding canonical transcript")
                       ]),
                       html.Tr([
                           html.Td("RefSeq_prot"),
                           html.Td("RefSeq identifier for corresponding canonical protein")
                       ]),
                       html.Tr([
                           html.Td("Ensembl_prot"),
                           html.Td("Ensembl identifier for corresponding canonical protein")
                       ]),
                       html.Tr([
                           html.Td("prot_length"),
                           html.Td("Canonical protein length")
                       ]),
                       html.Tr([
                           html.Td("exon_counts"),
                           html.Td("Number of exons in the canonical transcript")
                       ]),
                       #Disease
                       html.Tr([
                           html.Td("Disease", rowSpan=5),
                           html.Td("Disorder_id"),
                           html.Td("Unique disease identifier from Orphanet")
                       ]),
                       html.Tr([
                           html.Td("Disorder_name"),
                           html.Td("Disorder name")
                       ]),
                       html.Tr([
                           html.Td("orpha_code"),
                           html.Td("Unique identifier to link with Orphanet")
                       ]),
                       html.Tr([
                           html.Td("definition"),
                           html.Td("Detailed description of the disease")
                       ]),
                       html.Tr([
                           html.Td("prevalence_geo"),
                           html.Td("Number of cases of the disease in a population")
                       ]),
                       #Phenotype
                       html.Tr([
                           html.Td("Phenotype", rowSpan=4),
                           html.Td("hpo_id"),
                           html.Td("Unique phenotype identifier from HPO")
                       ]),
                       html.Tr([
                           html.Td("hpo_name"),
                           html.Td("Phenotype name")
                       ]),
                       html.Tr([
                           html.Td("comment"),
                           html.Td("Description of the phenotype")
                       ]),
                       html.Tr([
                           html.Td("definition"),
                           html.Td("ORCID identifier of the author of the phenotype definition")
                       ]),
                   ]
               ),
           ],
           bordered=True,
           hover=True,
           responsive=True,
           striped=True,
       )
    ],
    fluid=True,
)