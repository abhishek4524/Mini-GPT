/**
 * Determine risk level based on drug and phenotype.
 * Returns: "Normal", "Increased", "Reduced", "Ineffective", etc.
 */
function getRisk(drug, phenotype) {
  const drugLower = drug.toLowerCase();
  const phenLower = phenotype.toLowerCase();

  // Example rules (mock)
  if (drugLower === 'codeine' && phenLower.includes('poor')) return 'Ineffective';
  if (drugLower === 'codeine' && phenLower.includes('ultrarapid')) return 'Increased risk (toxicity)';
  if (drugLower === 'warfarin' && phenLower.includes('poor')) return 'Increased bleeding risk';
  if (drugLower === 'warfarin' && phenLower.includes('low sensitivity')) return 'Reduced efficacy';
  if (drugLower === 'simvastatin' && phenLower.includes('poor')) return 'Increased myopathy risk';
  return 'Normal';
}

module.exports = { getRisk };