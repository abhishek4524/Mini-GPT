/**
 * Return CPIC-based recommendation for a drug and phenotype.
 * This is a mock; you would integrate with a real CPIC API or database.
 */
function getRecommendation(drug, phenotype) {
  const drugLower = drug.toLowerCase();
  const phenLower = phenotype.toLowerCase();

  if (drugLower === 'codeine') {
    if (phenLower.includes('poor')) {
      return {
        dosageAdjustment: 'Avoid codeine. Use alternative non-opioid analgesics.',
        alternativeDrugs: ['Morphine', 'Non-NSAIDs'],
        monitoring: 'Monitor for pain control and adverse effects.',
      };
    }
    if (phenLower.includes('ultrarapid')) {
      return {
        dosageAdjustment: 'Avoid codeine due to risk of morphine toxicity.',
        alternativeDrugs: ['Non-opioid analgesics', 'Tramadol with caution'],
        monitoring: 'Monitor for signs of opioid toxicity.',
      };
    }
    return {
      dosageAdjustment: 'Use label recommended dosage.',
      alternativeDrugs: [],
      monitoring: 'Standard monitoring.',
    };
  }

  if (drugLower === 'warfarin') {
    if (phenLower.includes('poor')) {
      return {
        dosageAdjustment: 'Reduce initial dose. Consider lower maintenance dose.',
        alternativeDrugs: [],
        monitoring: 'Monitor INR frequently.',
      };
    }
    return {
      dosageAdjustment: 'Use standard dosing algorithms.',
      alternativeDrugs: [],
      monitoring: 'Standard INR monitoring.',
    };
  }

  // Default
  return {
    dosageAdjustment: 'No specific adjustment based on genetics.',
    alternativeDrugs: [],
    monitoring: 'Standard monitoring.',
  };
}

module.exports = { getRecommendation };