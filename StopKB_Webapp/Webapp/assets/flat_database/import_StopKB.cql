// Create indexes for import and search peroformance
CREATE INDEX variant_hgvsg FOR (v:Variant) ON (v.HGVSG);
CREATE INDEX phenotype_hpo_id FOR (p:Phenotype) ON (p.hpo_id);
CREATE INDEX disease_disorder_name FOR (d:Disease) ON (d.disorder_name);
CREATE INDEX gene_symbol FOR (g:Gene) ON (g.Symbol);

// import disease
LOAD CSV WITH HEADERS FROM 'file:///disease.csv' AS row FIELDTERMINATOR ','
WITH row.disorder_id AS disorder_id, row.name AS disorder_name,
row.orpha_code AS orpha_code, row.definition AS definition,
row.prevalence_geo AS prevalence_geo
MERGE (d:Disease {disorder_id: disorder_id})
  SET d.disorder_id = disorder_id, d.disorder_name = disorder_name, d.orpha_code = orpha_code,
  d.definition = definition, d.prevalence_geo = prevalence_geo
RETURN count(d);

// import gene
LOAD CSV WITH HEADERS FROM 'file:///gene.csv' AS row FIELDTERMINATOR '\t'
WITH row.symbol AS Symbol, row.Cytogenetic AS Cytogenetic, row.RefSeq_nuc AS RefSeq_nuc,
row.Ensembl_nuc AS Ensembl_nuc, row.RefSeq_prot AS RefSeq_prot,
row.Ensembl_prot AS Ensembl_prot, row.prot_length AS prot_length, toInteger(row.exon_counts) AS exon_counts
MERGE (g:Gene {Symbol: Symbol})
  SET g.Symbol = Symbol, g.Cytogenetic = Cytogenetic, g.RefSeq_nuc = RefSeq_nuc,
  g.Ensembl_nuc = Ensembl_nuc, g.RefSeq_prot = RefSeq_prot, g.Ensembl_prot = Ensembl_prot,
  g.prot_length = prot_length, g.exon_counts = exon_counts
RETURN count(g);

// import phenotype
LOAD CSV WITH HEADERS FROM 'file:///phenotype.csv' AS row FIELDTERMINATOR '\t'
WITH row.hpo_id AS hpo_id, row.hpo_name AS hpo_name, row.comment AS comment, row.definition_x AS definition
MERGE (p:Phenotype {hpo_id: hpo_id})
  SET p.hpo_id = hpo_id, p.hpo_name = hpo_name, p.comment = comment, p.definition = definition
RETURN count(p);

// import variant
LOAD CSV WITH HEADERS FROM 'file:///variant.csv' AS row FIELDTERMINATOR '\t'
WITH row.HGVSG AS HGVSG, row.Merged_Source AS Merged_Source, row.Name AS Name, row.ClinicalSignificance AS ClinicalSignificance,
row.Origin AS Origin, row.ReviewStatus AS ReviewStatus, toInteger(row.pos_stop_prot) AS pos_stop_prot, toFloat(row.pos_relative_prot) AS pos_relative_prot,
toInteger(row.pos_var_cds) AS pos_var_cds, row.nuc_upstream AS nuc_upstream, row.codon_stop AS codon_stop, row.nuc_downstream AS nuc_downstream,
toInteger(row.exon_localization) AS exon_localization, row.NMD_sensitivity AS NMD_sensitivity, toFloat(row.AF) AS AF_ww,
toFloat(row.AF_afr) AS AF_afr, toFloat(row.AF_amr) AS AF_amr, toFloat(row.AF_asj) AS AF_asj, toFloat(row.AF_eas) AS AF_eas,
toFloat(row.AF_fin) AS AF_fin, toFloat(row.AF_mid) AS AF_mid, toFloat(row.AF_nfe) AS AF_nfe, toFloat(row.AF_remaining) AS AF_remaining, toFloat(row.AF_sas) AS AF_sas, row.overlapping_domain AS overlapping_domain
MERGE (v:Variant {HGVSG: HGVSG})
  SET v.HGVSG = HGVSG, v.Merged_Source = Merged_Source, v.Name = Name, v.ClinicalSignificance = ClinicalSignificance,
  v.Origin = Origin, v.ReviewStatus = ReviewStatus,
  v.pos_stop_prot = pos_stop_prot, v.pos_relative_prot = pos_relative_prot,
  v.pos_var_cds = pos_var_cds, v.nuc_upstream = nuc_upstream, v.codon_stop = codon_stop, v.nuc_downstream = nuc_downstream,
  v.exon_localization = exon_localization, v.NMD_sensitivity = NMD_sensitivity,
  v.AF_ww = AF_ww, v.AF_afr = AF_afr, v.AF_amr = AF_amr, v.AF_asj = AF_asj, v.AF_eas = AF_eas,
  v.AF_fin = AF_fin, v.AF_mid = AF_mid, v.AF_nfe = AF_nfe, v.AF_remaining = AF_remaining, v.AF_sas = AF_sas, v.overlapping_domain = overlapping_domain
RETURN count(v);

// link disease_gene
LOAD CSV WITH HEADERS FROM 'file:///disease_gene.csv' AS row FIELDTERMINATOR '\t'
WITH row.disorder_id AS disorder_id, row.symbol AS Symbol
MATCH (d:Disease {disorder_id: disorder_id})
MATCH (g:Gene {Symbol: Symbol})
MERGE (d)-[rel:CAUSED_BY]->(g)
RETURN count(rel);

// link disease_phenotype
LOAD CSV WITH HEADERS FROM 'file:///disease_phenotype.csv' AS row FIELDTERMINATOR '\t'
WITH row.disorder_id AS disorder_id, row.hpo_id AS hpo_id
MATCH (d:Disease {disorder_id: disorder_id})
MATCH (p:Phenotype {hpo_id: hpo_id})
MERGE (d)-[rel:RECOGNIZABLE_BY]->(p)
RETURN count(rel);

// link variant_gene
LOAD CSV WITH HEADERS FROM 'file:///variant_gene.csv' AS row FIELDTERMINATOR '\t'
WITH row.HGVSG AS HGVSG, row.symbol AS Symbol
MATCH (v:Variant {HGVSG: HGVSG})
MATCH (g:Gene {Symbol: Symbol})
MERGE (v)-[rel:LOCATED_ON]->(g)
RETURN count(rel);

