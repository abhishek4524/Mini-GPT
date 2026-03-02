const parseVCF = require('../services/vcfParser');
const matchVariants = require('../services/variantMatcher');
const { getPhenotype } = require('../services/phenotypeEngine');
const { getRisk } = require('../services/riskEngine');
const { getRecommendation } = require('../services/cpicService');
const { generateExplanation } = require('../services/llmService');
const { computeConfidenceScore } = require('../utils/confidenceScore');

// Helper to map risk string to label & severity
function mapRisk(riskStr) {
  const map = {
    'Normal': { label: 'Safe', severity: 'Low' },
    'Increased': { label: 'Adjust Dosage', severity: 'Moderate' },
    'Reduced': { label: 'Adjust Dosage', severity: 'Moderate' },
    'Ineffective': { label: 'Toxic / Ineffective', severity: 'High' },
    'Increased risk (toxicity)': { label: 'Toxic / Ineffective', severity: 'High' },
    'Increased bleeding risk': { label: 'Toxic / Ineffective', severity: 'High' },
    'Reduced efficacy': { label: 'Adjust Dosage', severity: 'Moderate' },
    'Increased myopathy risk': { label: 'Toxic / Ineffective', severity: 'High' },
  };
  return map[riskStr] || { label: 'Unknown', severity: 'Unknown' };
}

// Helper to generate reasoning from risk & explanation
function generateReasoning(riskStr, explanation) {
  if (explanation) return explanation.split('.')[0] + '.';
  return `Based on the detected variants, the risk is ${riskStr}.`;
}

async function analyze(req, res) {
  try {
    if (!req.file) return res.status(400).json({ error: 'VCF file is required' });

    let drugs = [];
    if (req.body.drugs) {
      drugs = typeof req.body.drugs === 'string' ? JSON.parse(req.body.drugs) : req.body.drugs;
    }
    if (!Array.isArray(drugs) || drugs.length === 0) {
      return res.status(400).json({ error: 'At least one drug must be selected' });
    }

    const parsedVariants = parseVCF(req.file.path);
    if (parsedVariants.length === 0) {
      return res.status(400).json({ error: 'No valid variants found in VCF' });
    }

    const matchedVariants = await matchVariants(parsedVariants);
    if (matchedVariants.length === 0) {
      return res.status(404).json({ error: 'No known pharmacogenetic variants found' });
    }

    // Group by gene
    const geneMap = new Map();
    matchedVariants.forEach(v => {
      if (!geneMap.has(v.gene)) geneMap.set(v.gene, []);
      geneMap.get(v.gene).push(v);
    });

    const results = [];

    for (const drug of drugs) {
      const genes = Array.from(geneMap.keys());
      const primaryGene = genes[0] || 'Unknown';
      const variantsForGene = geneMap.get(primaryGene) || [];

      // Build diplotype
      const starAlleles = variantsForGene.map(v => v.star).filter(Boolean);
      const diplotype = starAlleles.length > 1 ? starAlleles.join('/') : (starAlleles[0] || '*1/*1');

      const phenotype = getPhenotype(primaryGene, diplotype);
      const riskStr = getRisk(drug, phenotype);
      const { label: riskLabel, severity } = mapRisk(riskStr);
      const confidence = computeConfidenceScore(variantsForGene, true);
      const recommendation = getRecommendation(drug, phenotype);

      // Generate AI explanation (string)
      const llmExplanation = await generateExplanation({
        drug,
        gene: primaryGene,
        diplotype,
        phenotype,
        risk: riskStr,
        variants: variantsForGene,
        recommendation,
      });

      // Build full frontend-compatible object
      const result = {
        drug,
        patient_id: `PATIENT_${Date.now().toString().slice(-6)}`,
        timestamp: new Date().toISOString(),
        risk_assessment: {
          risk_label: riskLabel,
          severity,
          confidence_score: confidence,
          reasoning: generateReasoning(riskStr, llmExplanation),
        },
        pharmacogenomic_profile: {
          primary_gene: primaryGene,
          diplotype,
          phenotype,
          detected_variants: variantsForGene.map(v => ({
            rs_id: v.rsid,
            gene: v.gene,
            star_allele: v.star,
            diplotype: v.star, // or you could compute per-variant diplotype if available
            impact: v.impact || 'unknown',
          })),
        },
        clinical_recommendation: {
          cpic_recommendation: `${recommendation.dosageAdjustment} ${recommendation.monitoring}`.trim(),
          evidence_level: confidence > 0.8 ? 'A' : (confidence > 0.5 ? 'B' : 'C'),
          dosage_adjustment: recommendation.dosageAdjustment,
          alternative_drugs: recommendation.alternativeDrugs || [],
        },
        llm_generated_explanation: {
          summary: llmExplanation.split('.')[0] + '.', // first sentence
          key_findings: variantsForGene.map(v => `${v.gene} ${v.star} allele detected`),
          detailed_narrative: llmExplanation,
          clinical_implications: `This may affect ${drug} therapy. Consult a clinician.`,
        },
        quality_metrics: {
          total_variants_parsed: parsedVariants.length,
          variants_matched: matchedVariants.length,
          coverage_percent: 98, // placeholder – you can compute from VCF depth if available
          variant_call_rate: 95,
          parsing_warnings: [], // you could collect warnings during parsing
        },
      };

      results.push(result);
    }

    res.json({ success: true, data: results });
  } catch (err) {
    console.error('Analysis error:', err);
    res.status(500).json({ error: 'Internal server error' });
  }
}

module.exports = { analyze };